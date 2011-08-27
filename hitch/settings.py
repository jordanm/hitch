import logging
from os import path

root = path.dirname(path.abspath(__file__))
FILESYSTEM_ROOT = root

DEBUG = False
TEMPLATE_DEBUG = DEBUG
DEVELOPING = False

ADMINS = ()
MANAGERS = ADMINS

DATABASES = {}
ROOT_URLCONF = 'hitch.urls'

TIME_ZONE = 'America/Chicago'
LANGUAGE_CODE = 'en-us'
USE_I18N = True
USE_L10N = True

HTTPS_SCHEME = 'http'
SITE_ID = 1
SECRET_KEY = '8agre=s-lropumj*x(zlzs$ehtkeptkth@ip!o&7bu7)f1zdtc'

PLOGIN_COOKIE_MAXAGE = (86400 * 365 * 2)
PLOGIN_COOKIE_NAME = 'plogin'

MEDIA_ROOT = path.join(root, 'media')
MEDIA_URL = '/media/'
ADMIN_MEDIA_PREFIX = '/admin_media/'

STATIC_ROOT = path.join(root, 'static')
STATIC_URL = '/static/'
STATICFILES_DIRS = ()
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

TEMPLATE_SEARCHPATH = path.join(root, 'templates')

TEMPLATE_LOADERS = ()
TEMPLATE_DIRS = ()

MIDDLEWARE_CLASSES = (
    'hitch.support.middleware.RequestMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    #'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'hitch.core.account.middleware.AuthenticationMiddleware',
    'hitch.support.logs.ContextualLoggingMiddleware',
    'hitch.support.logs.RequestLoggingMiddleware',
    'hitch.support.middleware.UncaughtExceptionMiddleware',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.admin',
    'hitch.core',
    'south',
)

MODELS_IGNORED_WHEN_DELETED = (
    'django.contrib.auth.models.Message',
    'hitch.core.account.models.PasswordReset',
    'hitch.core.account.models.PersistentLogin',
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

def CONFIGURE_LOGGING(log):
    from hitch.support.logs import DefaultFormatter
    log.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setFormatter(DefaultFormatter)
    log.addHandler(handler)

try:
    from settings_local import *
except ImportError:
    pass