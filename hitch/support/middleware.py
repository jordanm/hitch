import logging

from django.http import Http404

from hitch import request_local_context
from hitch.support.util import format_mapped_data

log = logging.getLogger('hitch')

class RequestMiddleware(object):
    def process_request(self, request):
        request_local_context.request = request
        
        chain = request.META.get('HTTP_X_FORWARDED_FOR')
        if chain:
            request.ip = chain.split(',')[0].strip()
        else:
            request.ip = request.META.get('REMOTE_ADDR')
            
        request.posting = (request.method == 'POST')
        request.scheme = ('https' if request.META.get('HTTPS') in ('on', '1') else 'http')

class UncaughtExceptionMiddleware(object):
    def process_exception(self, request, exception):
        if isinstance(exception, Http404):
            return
        
        lines = ['uncaught %s: %s' % (type(exception).__name__, str(exception))]
        lines.append('url: %s%s' % (request.META['HTTP_HOST'], request.get_full_path()))
        if request.GET:
            lines.append('get: %s' % format_mapped_data(request.GET))
        elif request.POST:
            lines.append('post: %s' % format_mapped_data(request.POST))
        log.exception('\n'.join(lines))