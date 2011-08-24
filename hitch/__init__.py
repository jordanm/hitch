import logging
from threading import local

from django.conf import settings

request_local_context = local()
request_local_context.request = None

settings.CONFIGURE_LOGGING()