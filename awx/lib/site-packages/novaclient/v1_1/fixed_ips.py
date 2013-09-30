# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 IBM Corp.
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
Fixed IPs interface.
"""

from novaclient import base


class FixedIP(base.Resource):
    def __repr__(self):
        return "<FixedIP: %s>" % self.address


class FixedIPsManager(base.Manager):
    resource_class = FixedIP

    def get(self, fixed_ip):
        """
        Show information for a Fixed IP

        :param fixed_ip: Fixed IP address to get info for
        """
        return self._get('/os-fixed-ips/%s' % base.getid(fixed_ip),
                         "fixed_ip")

    def reserve(self, fixed_ip):
        """Reserve a Fixed IP

        :param fixed_ip: Fixed IP address to reserve
        """
        body = {"reserve": None}
        self.api.client.post('/os-fixed-ips/%s/action' % base.getid(fixed_ip),
                             body=body)

    def unreserve(self, fixed_ip):
        """Unreserve a Fixed IP

        :param fixed_ip: Fixed IP address to unreserve
        """
        body = {"unreserve": None}
        self.api.client.post('/os-fixed-ips/%s/action' % base.getid(fixed_ip),
                             body=body)
