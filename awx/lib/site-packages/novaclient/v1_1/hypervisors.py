# Copyright 2012 OpenStack Foundation
# All Rights Reserved.
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

"""
Hypervisors interface (1.1 extension).
"""

from six.moves.urllib import parse

from novaclient import base


class Hypervisor(base.Resource):
    NAME_ATTR = 'hypervisor_hostname'

    def __repr__(self):
        return "<Hypervisor: %s>" % self.id


class HypervisorManager(base.ManagerWithFind):
    resource_class = Hypervisor

    def list(self, detailed=True):
        """
        Get a list of hypervisors.
        """
        detail = ""
        if detailed:
            detail = "/detail"
        return self._list('/os-hypervisors%s' % detail, 'hypervisors')

    def search(self, hypervisor_match, servers=False):
        """
        Get a list of matching hypervisors.

        :param servers: If True, server information is also retrieved.
        """
        target = 'servers' if servers else 'search'
        url = ('/os-hypervisors/%s/%s' %
               (parse.quote(hypervisor_match, safe=''), target))
        return self._list(url, 'hypervisors')

    def get(self, hypervisor):
        """
        Get a specific hypervisor.
        """
        return self._get("/os-hypervisors/%s" % base.getid(hypervisor),
                         "hypervisor")

    def uptime(self, hypervisor):
        """
        Get the uptime for a specific hypervisor.
        """
        return self._get("/os-hypervisors/%s/uptime" % base.getid(hypervisor),
                         "hypervisor")

    def statistics(self):
        """
        Get hypervisor statistics over all compute nodes.
        """
        return self._get("/os-hypervisors/statistics", "hypervisor_statistics")
