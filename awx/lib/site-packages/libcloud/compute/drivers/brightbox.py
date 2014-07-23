# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Brightbox Driver
"""

from libcloud.utils.py3 import httplib
from libcloud.utils.py3 import b

from libcloud.common.brightbox import BrightboxConnection
from libcloud.compute.types import Provider, NodeState
from libcloud.compute.base import NodeDriver
from libcloud.compute.base import Node, NodeImage, NodeSize, NodeLocation

import base64


API_VERSION = '1.0'


def _extract(d, keys):
    return dict((k, d[k]) for k in keys if k in d and d[k] is not None)


class BrightboxNodeDriver(NodeDriver):
    """
    Brightbox node driver
    """

    connectionCls = BrightboxConnection

    type = Provider.BRIGHTBOX
    name = 'Brightbox'
    website = 'http://www.brightbox.co.uk/'

    NODE_STATE_MAP = {'creating': NodeState.PENDING,
                      'active': NodeState.RUNNING,
                      'inactive': NodeState.UNKNOWN,
                      'deleting': NodeState.UNKNOWN,
                      'deleted': NodeState.TERMINATED,
                      'failed': NodeState.UNKNOWN,
                      'unavailable': NodeState.UNKNOWN}

    def __init__(self, key, secret=None, secure=True, host=None, port=None,
                 api_version=API_VERSION, **kwargs):
        super(BrightboxNodeDriver, self).__init__(key=key, secret=secret,
                                                  secure=secure,
                                                  host=host, port=port,
                                                  api_version=api_version,
                                                  **kwargs)

    def _to_node(self, data):
        extra_data = _extract(data, ['fqdn', 'user_data', 'status',
                                     'interfaces', 'snapshots',
                                     'server_groups', 'hostname',
                                     'started_at', 'created_at',
                                     'deleted_at'])
        extra_data['zone'] = self._to_location(data['zone'])

        ipv6_addresses = [interface['ipv6_address'] for interface
                          in data['interfaces'] if 'ipv6_address' in interface]

        private_ips = [interface['ipv4_address']
                       for interface in data['interfaces']
                       if 'ipv4_address' in interface]

        public_ips = [cloud_ip['public_ip'] for cloud_ip in data['cloud_ips']]
        public_ips += ipv6_addresses

        return Node(
            id=data['id'],
            name=data['name'],
            state=self.NODE_STATE_MAP[data['status']],
            private_ips=private_ips,
            public_ips=public_ips,
            driver=self.connection.driver,
            size=self._to_size(data['server_type']),
            image=self._to_image(data['image']),
            extra=extra_data
        )

    def _to_image(self, data):
        extra_data = _extract(data, ['arch', 'compatibility_mode',
                                     'created_at', 'description',
                                     'disk_size', 'min_ram', 'official',
                                     'owner', 'public', 'source',
                                     'source_type', 'status', 'username',
                                     'virtual_size', 'licence_name'])

        if data.get('ancestor', None):
            extra_data['ancestor'] = self._to_image(data['ancestor'])

        return NodeImage(
            id=data['id'],
            name=data['name'],
            driver=self,
            extra=extra_data
        )

    def _to_size(self, data):
        return NodeSize(
            id=data['id'],
            name=data['name'],
            ram=data['ram'],
            disk=data['disk_size'],
            bandwidth=0,
            price=0,
            driver=self
        )

    def _to_location(self, data):
        if data:
            return NodeLocation(
                id=data['id'],
                name=data['handle'],
                country='GB',
                driver=self
            )
        else:
            return None

    def _post(self, path, data={}):
        headers = {'Content-Type': 'application/json'}
        return self.connection.request(path, data=data, headers=headers,
                                       method='POST')

    def _put(self, path, data={}):
        headers = {'Content-Type': 'application/json'}
        return self.connection.request(path, data=data, headers=headers,
                                       method='PUT')

    def create_node(self, **kwargs):
        """Create a new Brightbox node

        Reference: https://api.gb1.brightbox.com/1.0/#server_create_server

        @inherits: :class:`NodeDriver.create_node`

        :keyword    ex_userdata: User data
        :type       ex_userdata: ``str``

        :keyword    ex_servergroup: Name or list of server group ids to
                                    add server to
        :type       ex_servergroup: ``str`` or ``list`` of ``str``
        """
        data = {
            'name': kwargs['name'],
            'server_type': kwargs['size'].id,
            'image': kwargs['image'].id,
        }

        if 'ex_userdata' in kwargs:
            data['user_data'] = base64.b64encode(b(kwargs['ex_userdata'])) \
                                      .decode('ascii')

        if 'location' in kwargs:
            data['zone'] = kwargs['location'].id

        if 'ex_servergroup' in kwargs:
            if not isinstance(kwargs['ex_servergroup'], list):
                kwargs['ex_servergroup'] = [kwargs['ex_servergroup']]
            data['server_groups'] = kwargs['ex_servergroup']

        data = self._post('/%s/servers' % self.api_version, data).object
        return self._to_node(data)

    def destroy_node(self, node):
        response = self.connection.request(
            '/%s/servers/%s' % (self.api_version, node.id),
            method='DELETE')
        return response.status == httplib.ACCEPTED

    def list_nodes(self):
        data = self.connection.request('/%s/servers' % self.api_version).object
        return list(map(self._to_node, data))

    def list_images(self, location=None):
        data = self.connection.request('/%s/images' % self.api_version).object
        return list(map(self._to_image, data))

    def list_sizes(self):
        data = self.connection.request('/%s/server_types' % self.api_version) \
                              .object
        return list(map(self._to_size, data))

    def list_locations(self):
        data = self.connection.request('/%s/zones' % self.api_version).object
        return list(map(self._to_location, data))

    def ex_list_cloud_ips(self):
        """
        List Cloud IPs

        @note: This is an API extension for use on Brightbox

        :rtype: ``list`` of ``dict``
        """
        return self.connection.request('/%s/cloud_ips' % self.api_version) \
                              .object

    def ex_create_cloud_ip(self, reverse_dns=None):
        """
        Requests a new cloud IP address for the account

        @note: This is an API extension for use on Brightbox

        :param      reverse_dns: Reverse DNS hostname
        :type       reverse_dns: ``str``

        :rtype: ``dict``
        """
        params = {}

        if reverse_dns:
            params['reverse_dns'] = reverse_dns

        return self._post('/%s/cloud_ips' % self.api_version, params).object

    def ex_update_cloud_ip(self, cloud_ip_id, reverse_dns):
        """
        Update some details of the cloud IP address

        @note: This is an API extension for use on Brightbox

        :param  cloud_ip_id: The id of the cloud ip.
        :type   cloud_ip_id: ``str``

        :param      reverse_dns: Reverse DNS hostname
        :type       reverse_dns: ``str``

        :rtype: ``dict``
        """
        response = self._put('/%s/cloud_ips/%s' % (self.api_version,
                                                   cloud_ip_id),
                             {'reverse_dns': reverse_dns})
        return response.status == httplib.OK

    def ex_map_cloud_ip(self, cloud_ip_id, interface_id):
        """
        Maps (or points) a cloud IP address at a server's interface
        or a load balancer to allow them to respond to public requests

        @note: This is an API extension for use on Brightbox

        :param  cloud_ip_id: The id of the cloud ip.
        :type   cloud_ip_id: ``str``

        :param  interface_id: The Interface ID or LoadBalancer ID to
                              which this Cloud IP should be mapped to
        :type   interface_id: ``str``

        :return: True if the mapping was successful.
        :rtype: ``bool``
        """
        response = self._post('/%s/cloud_ips/%s/map' % (self.api_version,
                                                        cloud_ip_id),
                              {'destination': interface_id})
        return response.status == httplib.ACCEPTED

    def ex_unmap_cloud_ip(self, cloud_ip_id):
        """
        Unmaps a cloud IP address from its current destination making
        it available to remap. This remains in the account's pool
        of addresses

        @note: This is an API extension for use on Brightbox

        :param  cloud_ip_id: The id of the cloud ip.
        :type   cloud_ip_id: ``str``

        :return: True if the unmap was successful.
        :rtype: ``bool``
        """
        response = self._post('/%s/cloud_ips/%s/unmap' % (self.api_version,
                                                          cloud_ip_id))
        return response.status == httplib.ACCEPTED

    def ex_destroy_cloud_ip(self, cloud_ip_id):
        """
        Release the cloud IP address from the account's ownership

        @note: This is an API extension for use on Brightbox

        :param  cloud_ip_id: The id of the cloud ip.
        :type   cloud_ip_id: ``str``

        :return: True if the unmap was successful.
        :rtype: ``bool``
        """
        response = self.connection.request(
            '/%s/cloud_ips/%s' % (self.api_version,
                                  cloud_ip_id),
            method='DELETE')
        return response.status == httplib.OK
