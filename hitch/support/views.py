import logging
from collections import defaultdict
from functools import wraps
from json import dumps

from django.conf import settings
from django.conf.urls.defaults import patterns, url
from django.contrib.messages import DEFAULT_TAGS, add_message
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.utils.http import urlquote

from hitch.support.templates import render_template

HTTPS_SCHEME = getattr(settings, 'HTTPS_SCHEME', 'https')
MESSAGE_TAGS = dict([tuple(reversed(item)) for item in DEFAULT_TAGS.items()])

log = logging.getLogger(__name__)

def viewable(name, path, **params):
    params.update(name=name, path=path, viewable=True)
    params['ajax_only'] = params.get('ajax_only', False)
    params['authenticated'] = params.get('authenticated', False)
    params['secured'] = (params.get('secured', False) and HTTPS_SCHEME == 'https')
    
    def wrapper(view):
        view.__dict__.update(params)
        return view
    return wrapper

class Response(object):
    def __init__(self, request, view):
        self.context = {'request': request, 'view': view}
        self.cookies = []
        self.data = {}
        self.messages = []
        self.request = request
        self.view = view
        
    def authorize(self, permission):
        account = self.request.account
        if not (account and account.superuser):
            raise PermissionDenied()
        
    def collect(self, form):
        self.data.update(field_errors={}, form_errors=[])
        if isinstance(form.errors, list):
            for subform in form.forms:
                self._collect_errors(subform)
        else:
            self._collect_errors(form)
        return self
        
    def error(self, error='unknown-error', **params):
        self.data['error'] = error
        if params:
            self.data.update(params)
        return self
    
    def ignore(self, url='/'):
        if self.request.is_ajax():
            return HttpResponseBadRequest()
        else:
            return HttpResponseRedirect(url)
    
    def json(self, **params):
        data = self.data
        if params:
            data.update(params)
            
        data['messages'] = [{'text': msg[0], 'tag': msg[1]} for msg in self.messages]
        return self._apply_cookies(HttpResponse(dumps(data), mimetype='application/json'))

    def message(self, text, tag='info'):
        self.messages.append((text, tag))
        return self
    
    def redirect(self, url='/'):
        self._apply_messages()
        return self._apply_cookies(HttpResponseRedirect(url))
    
    def render(self, template, context=None, response=None, mimetype='text/html', **params):
        self._apply_messages() 
        template_context = self.context
        if context:
            template_context.update(context)
        if params:
            template_context.update(params)
            
        response = response or HttpResponse(mimetype=mimetype)
        response.content = render_template(template, template_context)
        return self._apply_cookies(response)

    def set_cookie(self, *args, **params):
        self.cookies.append((args, params))
        return self
    
    def update(self, *args, **params):
        self.context.update(*args, **params)
    
    def _apply_cookies(self, response):
        for args, params in self.cookies:
            response.set_cookie(*args, **params)
        return response
    
    def _apply_messages(self):
        for text, tag in self.messages:
            add_message(self.request, MESSAGE_TAGS.get(tag, 20), text)
            
    def _collect_errors(self, form):
        prefix = ('%s-' % form.prefix if form.prefix else '')
        for field in form:
            if field.name in form.errors:
                errors = self.data['field_errors'][prefix + field.name] = []
                for error in form.errors[field.name]:
                    errors.append(unicode(error))
        
        form_errors = form.errors.get('__all__')
        if isinstance(form_errors, (list, tuple)):
            self.data['form_errors'].extend(form_errors)
        elif form_errors:
            self.data['form_errors'].append(form_errors)
    
class ViewSetMeta(type):
    def __init__(cls, name, bases, namespace):
        super(ViewSetMeta, cls).__init__(name, bases, namespace)
        views = {}
        for key, value in namespace.iteritems():
            try:
                viewable = value.viewable
                if viewable:
                    views[key] = value
            except (AttributeError, TypeError):
                pass
        if views:
            cls.declared_views = views
            cls.declared_viewsets.add(cls)
            
    @property
    def urlpatterns(cls):
        urls = []
        for viewset in cls.declared_viewsets:
            if issubclass(viewset, cls):
                for name, view in viewset.declared_views.iteritems():
                    urls.append(url(view.path, viewset(name), name=view.name))
        
        urls.sort(cmp=cls._sort_url_patterns)
        return patterns('', *urls)
    
    @staticmethod
    def _sort_url_patterns(left, right):
        return cmp(len(left.regex.pattern), len(right.regex.pattern))
    
class ViewSet(object):
    __metaclass__ = ViewSetMeta
    declared_viewsets = set()
    
    def __init__(self, view):
        self._view = view
        
    def __call__(self, request, *args, **params):
        request.view = getattr(self, self._view)
        if request.view.ajax_only and not request.is_ajax():
            log.debug('rejecting non-ajax request to ajax only view')
            return HttpResponseBadRequest()
        if request.view.secured and not request.is_secure():
            if request.is_ajax():
                log.debug('rejecting unsecured ajax request to secured view') 
                return HttpResponseBadRequest()
            else:
                log.debug('redirecting unsecured request to secured view')
                return HttpResponseRedirect('https://%s%s' % (request.META['HTTP_HOST'], request.get_full_path()))
        if request.view.authenticated and not request.account:
            if request.is_ajax():
                log.debug('rejecting unauthenticated ajax request to authenticated view')
                return HttpResponseBadRequest()
            else:
                log.debug('redirecting unauthenticated request to authenticated view')
                return HttpResponseRedirect('%s://%s%s?next=%s' % (HTTPS_SCHEME, request.META['HTTP_HOST'],
                    reverse('account-login'), urlquote(request.get_full_path())))
            
        response = Response(request, self)
        try:
            return request.view(request, response, *args, **params)
        except PermissionDenied:
            log.debug('rejecting request due to insufficient permissions')
            return response.ignore()