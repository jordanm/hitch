import json
import logging
from datetime import datetime
from decimal import Decimal

from django.conf import settings
from django.core.urlresolvers import NoReverseMatch, reverse
from django.http import HttpResponse, HttpResponseServerError
from django.template.defaultfilters import escapejs
from django.utils.http import urlquote
import jinja2
from jinja2 import contextfunction
from jinja2.filters import urlize

from hitch.support.util import pluralize as _pluralize

log = logging.getLogger(__name__)

TEMPLATE_SEARCHPATH = settings.TEMPLATE_SEARCHPATH

STANDARD_FILTERS = [escapejs, repr]
STANDARD_EXTENSIONS = ['jinja2.ext.loopcontrols', 'jinja2.ext.with_']
STANDARD_GLOBALS = [str, zip]

class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        else:
            return super(JsonEncoder, self).default(obj)

json_encoder = JsonEncoder()

class TemplateEnvironment(jinja2.Environment):
    def __init__(self, **params):
        extensions = list(params.get('extensions', []))
        for extension in STANDARD_EXTENSIONS:
            if extension not in extensions:
                extensions.append(extension)
        
        params['extensions'] = extensions
        super(TemplateEnvironment, self).__init__(**params)
        
        self._populate_environment(self.filters, STANDARD_FILTERS)
        self._populate_environment(self.globals, STANDARD_GLOBALS)
    
    def filter(self, function):
        self.filters[function.__name__] = function
        return function
    
    def function(self, function):
        self.globals[function.__name__] = function
        return function
    
    @classmethod
    def instrument_for_testing(cls, revert=False):
        if revert:
            try:
                original = cls._original_render_template
            except AttributeError:
                return
            cls.render_template = original
            del cls._original_render_template
            return
        if hasattr(cls, '_original_render_template'):
            return
        
        cls._original_render_template = cls.render_template
        def instrumented(self, template, context=None):
            template_rendered.send(sender=self, template=template, context=context or {})
            return cls._original_render_template(self, template, context)
        cls.render_template = instrumented        
        
    def render_template(self, template, context=None, **params):
        context = context or {}
        if params:
            context.update(params)
        
        try:
            return self.get_template(template).render(context)
        except jinja2.TemplateError as exception:
            if 'source' in exception.__dict__:
                del exception.__dict__['source']
            raise

    def test(self, function):
        self.tests[function.__name__] = function
        return function
    
    def _populate_environment(self, collection, additions):
        for addition in additions:
            if isinstance(addition, tuple):
                collection[addition[0]] = addition[1]
            else:
                collection[addition.__name__] = addition

environment = TemplateEnvironment(loader=jinja2.FileSystemLoader(TEMPLATE_SEARCHPATH))
render_template = environment.render_template

@environment.filter
def json(value):
    return json_encoder.encode(value)

@environment.filter
def pluralize(value, number=2, alternative=None):
    if not isinstance(number, int):
        number = (len(number) if number else 0)
    if alternative:
        return (alternative if number != 1 else value)
    else:
        return (_pluralize(value) if number != 1 else value)

@environment.filter
def typename(value):
    return type(value).__name__

@environment.function
@contextfunction
def url(context, view=None, url=None, absolute=False, domain=None, query=None,
    secure=False, silent=False, urlconf=None, request=None, **params):
    
    if view:
        try:
            url = reverse(view, urlconf=urlconf, kwargs=params)
        except NoReverseMatch:
            if silent:
                return ''
            else:
                raise
    if absolute:
        pass
    if query:
        query = ('&'.join(query) if isinstance(query, (list, tuple)) else query)
        url = '%s?%s' % (url, query)
    return url 

@environment.filter
def urlencode(value):
    return urlquote(value)