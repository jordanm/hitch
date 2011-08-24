from datetime import datetime
from logging import Formatter

from hitch import request_local_context

class ContextualLoggingMiddleware(object):
    def process_request(self, request):
        request_local_context.request_signature = '%s %s %s %s' % (
            request.ip,
            request.META.get('HTTP_HOST', 'unknown-domain'),
            request.path,
            request.account.email if request.account else 'anonymous')

class ContextualFormatter(Formatter):
    def format(self, record):
        record.request_signature = getattr(request_local_context, 'request_signature', '- - - -')
        record.timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')
        return Formatter.format(self, record)

DefaultFormatter = ContextualFormatter('%(timestamp)s %(name)s %(levelname)s %(request_signature)s %(message)s')