# (c) 2013, AnsibleWorks
#
# This file is part of Ansible Commander
#
# Ansible Commander is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible Commander is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible Commander.  If not, see <http://www.gnu.org/licenses/>.

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

# users service
views_UsersList                   = views.UsersList.as_view()
views_UsersDetail                 = views.UsersDetail.as_view()
views_UsersMeList                 = views.UsersMeList.as_view()

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

    # users service
    url(r'^api/v1/users/$',                                    views_UsersList),
    url(r'^api/v1/users/(?P<pk>[0-9]+)/$',                     views_UsersDetail),
    url(r'^api/v1/me/$',                                       views_UsersMeList),

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
