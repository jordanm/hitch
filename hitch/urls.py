from django.conf import settings
from django.conf.urls.defaults import include, patterns, url
from django.contrib import admin
from django.contrib.auth.models import User, Group

from hitch.core.views import Views
from hitch.support.util import static_serve_url

#handler404 = ''
#handler500 = '' 

admin.autodiscover()
admin.site.unregister(User)
admin.site.unregister(Group)

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
)
urlpatterns += Views.urlpatterns

if getattr(settings, 'DEVELOPING', False):
    urlpatterns += patterns('',
        static_serve_url(settings.STATIC_URL, settings.STATIC_ROOT),
        static_serve_url(settings.MEDIA_URL, settings.MEDIA_ROOT),
    )