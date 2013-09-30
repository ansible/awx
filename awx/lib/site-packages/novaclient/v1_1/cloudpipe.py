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

"""Cloudpipe interface."""

from novaclient import base


class Cloudpipe(base.Resource):
    """A cloudpipe instance is a VPN attached to a proejct's VLAN."""

    def __repr__(self):
        return "<Cloudpipe: %s>" % self.project_id

    def delete(self):
        self.manager.delete(self)


class CloudpipeManager(base.ManagerWithFind):
    resource_class = Cloudpipe

    def create(self, project):
        """
        Launch a cloudpipe instance.

        :param project: name of the project for the cloudpipe
        """
        body = {'cloudpipe': {'project_id': project}}
        return self._create('/os-cloudpipe', body, 'instance_id',
                return_raw=True)

    def list(self):
        """
        Get a list of cloudpipe instances.
        """
        return self._list('/os-cloudpipe', 'cloudpipes')

    def update(self, address, port):
        """
        Update VPN address and port for all networks associated
        with the project defined by authentication

        :param address: IP address
        :param port: Port number
        """

        body = {'configure_project': {'vpn_ip': address,
                                      'vpn_port': port}}
        self._update("/os-cloudpipe/configure-project", body)
