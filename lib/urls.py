from django.conf import settings
from django.conf.urls import *
import lib.main.views as views

urlpatterns = patterns('',
    url(r'', include('lib.web.urls')),
    url(r'^api/v1/organizations/$',                 views.OrganizationsList.as_view()),
    url(r'^api/v1/organizations/(?P<pk>[0-9]+)/$',  views.OrganizationsDetail.as_view()),
)

if 'django.contrib.admin' in settings.INSTALLED_APPS:
    from django.contrib import admin
    admin.autodiscover()
    urlpatterns += patterns('',
        url(r'^admin/', include(admin.site.urls)),
    )
