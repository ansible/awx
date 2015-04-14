# Copyright 2013 OpenStack Foundation
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

""" V3 API versions of the Hosts interface.

Inherits from the 1.1 code because a lot of the functionality is shared.
"""

from novaclient.v1_1 import hosts


Host = hosts.Host


class HostManager(hosts.HostManager):
    def update(self, host, values):
        """Update status or maintenance mode for the host."""
        body = dict(host=values)
        return self._update("/os-hosts/%s" % host, body, response_key='host')

    def host_action(self, host, action):
        """Perform an action on a host."""
        url = '/os-hosts/{0}/{1}'.format(host, action)
        return self._get(url, response_key='host')

    def list(self, zone=None, service=None):
        """List cloud hosts."""

        filters = []
        if zone:
            filters.append('zone=%s' % zone)
        if service:
            filters.append('service=%s' % service)

        if filters:
            url = '/os-hosts?%s' % '&'.join(filters)
        else:
            url = '/os-hosts'

        return self._list(url, "hosts")
