import logging
from collections import defaultdict
from os.path import exists, join
from re import compile

from hitch.support.util import uniqid

log = logging.getLogger(__name__)

class StylesheetBuilder(object):
    Filters = {'post': [], 'property': []}
    
    def __init__(self, preprocessor, searchpath, minified=True):
        self.minified = minified
        self.preprocessor = preprocessor
        self.searchpath = searchpath
        
    def build(self, sources, context, files=None, preprocess_only=False):
        files = files or {}
        rules = defaultdict(dict)
        for basepath in reversed(self.searchpath):
            for source in sources:
                path = join(basepath, source)
                if path in files:
                    template = self.preprocessor.create_template(files[path])
                else:
                    template = self.preprocessor.get_template(path)
                if template:
                    template = self.preprocessor.preprocess_template(template, context)
                    self._merge_css(rules, template)
        if self.minified:
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
            for key, value in sorted(properties.iteritems()):
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
                properties = {}
                for pair in definition.split(';'):
                    try:
                        key, value = pair.split(':')
                    except ValueError:
                        log.warn('ignoring invalid css property %r' % pair)
                    else:
                        key, value = key.strip(), value.strip()
                        for filter in self.Filters['property']:
                            key, value = filter(key, value)
                        properties[key] = value
                for selector in css[offset:opening].strip().split(','):
                    rules[selector.strip()].update(properties)
            offset = closing + 1
            
    def _minify_css(self, rules):
        combined = defaultdict(list)
        for selector, properties in rules.iteritems():
            definition = []
            for key, value in sorted(properties.iteritems()):
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
    def _filter_background_gradients(key, value):
        if key == 'background-image' and 'gradient' in value:
            return '%s|%s|' % (key, uniqid()), value
        else:
            return key, value
        
    @filter('post')
    def _filter_background_gradients_post(css):
        return re.sub(r'[|][0-9a-f]{32}[|]', '', css)