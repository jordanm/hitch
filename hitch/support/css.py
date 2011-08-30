import logging
import re
from collections import defaultdict, OrderedDict
from os.path import exists, join
from re import compile

from django.conf import settings

from hitch.support.util import uniqid

CSS_URL = settings.CSS_URL
CSS_TARGETS = settings.CSS_TARGETS
FILESYSTEM_ROOT = settings.FILESYSTEM_ROOT

log = logging.getLogger(__name__)

def _uniquify_key(key):
    return '%s|%s|' % (key, uniqid())

class StylesheetBuilder(object):
    Filters = {'post': [], 'property': []}
    
    def build(self, files, minified=False):
        rules = defaultdict(OrderedDict)
        for filepath in files:
            with open(filepath) as openfile:
                self._merge_css(rules, openfile.read())
        
        if minified:
            css = self._minify_css(rules)
        else:
            css = self._format_css(rules)
            
        for filter in self.Filters['post']:
            css = filter(css)
        return css
    
    def _format_css(self, rules):
        css = []
        for selector, properties in rules.iteritems():
            definition = []
            for key, value in properties.iteritems():
                definition.append('  %s: %s;' % (key, value))
            else:
                css.append('%s {\n%s\n}' % (selector, '\n'.join(definition)))
        else:
            return '\n'.join(css)
        
    def _merge_css(self, rules, css):
        css = re.sub(r'[\n\t]', ' ', css)
        css = re.sub(r'[ ]{2,}', ' ', css)
        css = re.sub(r'[/][*][^*]*[*][/]', '', css)
        css = css.replace('( ', '(').replace(' )', ')')
        
        offset = 0
        while True:
            try:
                opening = css.index('{', offset)
                closing = css.index('}', opening)
            except ValueError:
                break
            definition = css[opening + 1:closing].strip(' ;')
            if definition:
                selectors = css[offset:opening].strip()
                properties = OrderedDict()
                for pair in definition.split(';'):
                    try:
                        key, value = pair.split(':')
                    except ValueError:
                        log.warn('ignoring invalid css property %r' % pair)
                    else:
                        key, value = key.strip(), value.strip()
                        for filter in self.Filters['property']:
                            key, value = filter(selectors, key, value)
                        properties[key] = value
                for selector in selectors.split(','):
                    rules[selector.strip()].update(properties)
            offset = closing + 1
            
    def _minify_css(self, rules):
        combined = defaultdict(list)
        for selector, properties in rules.iteritems():
            definition = []
            for key, value in properties.iteritems():
                definition.append('%s:%s' % (key, value))
            else:
                combined[';'.join(definition)].append(selector)
        
        css = []
        for definition, selectors in combined.iteritems():
            css.append('%s{%s}' % (','.join(selectors), definition))
        else:
            return ''.join(css)
            
    def filter(stage, filters=Filters):
        def decorator(method):
            filters[stage].append(method)
            return method
        return decorator
    
    @filter('property')
    def _filter_background_gradients(selectors, key, value):
        if key == 'background-image' and 'gradient' in value:
            return _uniquify_key(key), value
        else:
            return key, value
        
    @filter('property')
    def _filter_font_face_src(selectors, key, value):
        if selectors == '@font-face' and key == 'src':
            return _uniquify_key(key), value
        else:
            return key, value
        
    @filter('post')
    def _filter_uniquified_keys(css):
        return re.sub(r'[|][0-9a-f]{32}[|]', '', css)
    
def build_css_targets(targets=None, minified=False, stdout=False):
    builder = StylesheetBuilder() 
    for target in targets or CSS_TARGETS.keys():
        files = [join(FILESYSTEM_ROOT, CSS_URL[1:], filename) for filename in CSS_TARGETS[target]]
        css = builder.build(files, minified)
        if stdout:
            print css
        else:
            with open(join(FILESYSTEM_ROOT, CSS_URL[1:], '%s.css' % target), 'w+') as openfile:
                openfile.write(css)