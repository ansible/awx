from django.conf import settings
from django.conf.urls import *
import lib.main.views as views

# organizations service
views_OrganizationsList           = views.OrganizationsList.as_view()
views_OrganizationsDetail         = views.OrganizationsDetail.as_view()
views_OrganizationsAuditTrailList = views.OrganizationsAuditTrailList.as_view()
views_OrganizationsUsersList      = views.OrganizationsUsersList.as_view()
views_OrganizationsAdminsList     = views.OrganizationsAdminsList.as_view()
views_OrganizationsProjectsList   = views.OrganizationsProjectsList.as_view()
views_OrganizationsTagsList       = views.OrganizationsTagsList.as_view()

# FIXME: add entries for all of these:
    
# projects service
views_ProjectsDetail              = views.OrganizationsDetail.as_view()

# audit trail service
# team service
# inventory service
# group service
# host service
# inventory variable service
# log data services
# events services
# jobs services
# tags service
views_TagsDetail              = views.TagsDetail.as_view()


urlpatterns = patterns('',
    # organizations service
    url(r'^api/v1/organizations/$',                            views_OrganizationsList),
    url(r'^api/v1/organizations/(?P<pk>[0-9]+)/$',             views_OrganizationsDetail),
    url(r'^api/v1/organizations/(?P<pk>[0-9]+)/audit_trail/$', views_OrganizationsAuditTrailList),
    url(r'^api/v1/organizations/(?P<pk>[0-9]+)/users/$',       views_OrganizationsUsersList),
    url(r'^api/v1/organizations/(?P<pk>[0-9]+)/admins/$',      views_OrganizationsAdminsList),
    url(r'^api/v1/organizations/(?P<pk>[0-9]+)/projects/$',    views_OrganizationsProjectsList),
    url(r'^api/v1/organizations/(?P<pk>[0-9]+)/tags/$',        views_OrganizationsTagsList),

    # FIXME: implement:

    # users service

    # projects service
    url(r'^api/v1/projects/(?P<pk>[0-9]+)/$',                  views_ProjectsDetail),
    
    # audit trail service

    # team service

    # inventory service

    # group service

    # host service

    # inventory variable service

    # log data services

    # events services

    # jobs services

    # tags service
    url(r'^api/v1/tags/(?P<pk>[0-9]+)/$',                  views_TagsDetail),

)

if 'django.contrib.admin' in settings.INSTALLED_APPS:
    from django.contrib import admin
    admin.autodiscover()
    urlpatterns += patterns('',
        url(r'^admin/', include(admin.site.urls)),
    )
