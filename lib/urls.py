# Copyright (c) 2013 AnsibleWorks, Inc.
#
# This file is part of Ansible Commander.
#
# Ansible Commander is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# Ansible Commander is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible Commander. If not, see <http://www.gnu.org/licenses/>.

from django.conf import settings
from django.conf.urls import *

urlpatterns = patterns('',
    url(r'', include('lib.ui.urls', namespace='ui', app_name='ui')),
    url(r'^api/', include('lib.main.urls', namespace='main', app_name='main')),
)

if 'django.contrib.admin' in settings.INSTALLED_APPS:
    from django.contrib import admin
    admin.autodiscover()
    urlpatterns += patterns('',
        url(r'^admin/', include(admin.site.urls)),
    )
