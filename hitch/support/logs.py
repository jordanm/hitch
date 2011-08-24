import logging
from datetime import datetime

from django.conf import settings

from hitch import request_local_context
from hitch.support.util import format_mapped_data

STATIC_URL_PREFIXES = (settings.STATIC_URL, settings.MEDIA_URL)

log = logging.getLogger('hitch')

class ContextualLoggingMiddleware(object):
    def process_request(self, request):
        account = getattr(request, 'account')
        request_local_context.request_signature = '%s %s %s %s %s %s' % (
            getattr(request, 'ip', '-'),
            getattr(request, 'method', '-'),
            request.META.get('HTTP_HOST', '-'),
            getattr(request, 'path', '-'),
            account.email if account else 'anonymous',
            'ajax' if request.is_ajax() else '-')

class ContextualFormatter(logging.Formatter):
    def format(self, record):
        record.request_signature = getattr(request_local_context, 'request_signature', '- - - - - -')
        record.timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')
        return logging.Formatter.format(self, record)

DefaultFormatter = ContextualFormatter('%(timestamp)s %(name)s %(levelname)s %(request_signature)s %(message)s')

class RequestLoggingMiddleware(object):
    def process_request(self, request):
        path = request.get_full_path()
        for prefix in STATIC_URL_PREFIXES:
            if path.startswith(prefix):
                return

        lines = ['REQUEST']
        if request.GET:
            lines.append('GET: %s' % format_mapped_data(request.GET))
        elif request.POST:
            lines.append('POST: %s' % format_mapped_data(request.POST))
        log.debug('\n'.join(lines))