from django.conf import settings
from django.conf.urls import *

urlpatterns = patterns('',
    # Example:
    # (r'^foo/', include('lib.foo.urls')),
)

if 'django.contrib.admin' in settings.INSTALLED_APPS:
    from django.contrib import admin
    admin.autodiscover()
    urlpatterns += patterns('',
        url(r'^admin/', include(admin.site.urls)),
    )
