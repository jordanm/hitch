import logging
from threading import local

from django.conf import settings
from django.contrib.auth import models
from django.contrib.auth.management import create_superuser
from django.core.serializers import serialize
from django.db.models.signals import pre_delete, post_syncdb

from hitch.support.util import identify_instance, receives_signals

log = logging.getLogger(__name__)

# disconnect the create_superuser management command from the syncdb management command

post_syncdb.disconnect(create_superuser, sender=models,
    dispatch_uid='django.contrib.auth.management.create_superuser')

# declare a thread local to store the current request, so that the request doesn't have
# to be explicitly passed around during the request pipeline, which isn't always possible
# (see hitch.support.middleware.RequestMiddleware)

request_local_context = local()
request_local_context.request = None

#@receives_signals(pre_delete)
def _log_database_deletes(sender, **params):
    instance = params['instance']
    identity = identify_instance(instance)
    if identity.startswith('hitch.') and identity not in settings.MODELS_IGNORED_WHEN_DELETED:
        structure = serialize('json', [instance], indent=2)
        log.info('deleted %s: %s\n%s' % (identity, str(instance), structure))

# configure logging for the entire application using a configuration function defined
# in the settings module; doing it here will ensure that logging is only configured
# once, since the settings module can potentially be evaluated multiple times

settings.CONFIGURE_LOGGING(log)