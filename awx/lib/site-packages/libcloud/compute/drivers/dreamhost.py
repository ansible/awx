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
DreamHost Driver
"""

import copy

from libcloud.common.base import ConnectionKey, JsonResponse
from libcloud.common.types import InvalidCredsError
from libcloud.compute.base import Node, NodeDriver, NodeSize
from libcloud.compute.base import NodeImage
from libcloud.compute.types import Provider, NodeState

# DreamHost Private Servers can be resized on the fly, but Libcloud doesn't
# currently support extensions to its interface, so we'll put some basic sizes
# in for node creation.

DH_PS_SIZES = {
    'minimum': {
        'id': 'minimum',
        'name': 'Minimum DH PS size',
        'ram': 300,
        'disk': None,
        'bandwidth': None
    },
    'maximum': {
        'id': 'maximum',
        'name': 'Maximum DH PS size',
        'ram': 4000,
        'disk': None,
        'bandwidth': None
    },
    'default': {
        'id': 'default',
        'name': 'Default DH PS size',
        'ram': 2300,
        'disk': None,
        'bandwidth': None
    },
    'low': {
        'id': 'low',
        'name': 'DH PS with 1GB RAM',
        'ram': 1000,
        'disk': None,
        'bandwidth': None
    },
    'high': {
        'id': 'high',
        'name': 'DH PS with 3GB RAM',
        'ram': 3000,
        'disk': None,
        'bandwidth': None
    },
}


class DreamhostAPIException(Exception):
    def __str__(self):
        return self.args[0]

    def __repr__(self):
        return "<DreamhostException '%s'>" % (self.args[0])


class DreamhostResponse(JsonResponse):
    """
    Response class for DreamHost PS
    """

    def parse_body(self):
        resp = super(DreamhostResponse, self).parse_body()
        if resp['result'] != 'success':
            raise Exception(self._api_parse_error(resp))
        return resp['data']

    def parse_error(self):
        raise Exception

    def _api_parse_error(self, response):
        if 'data' in response:
            if response['data'] == 'invalid_api_key':
                raise InvalidCredsError(
                    "Oops!  You've entered an invalid API key")
            else:
                raise DreamhostAPIException(response['data'])
        else:
            raise DreamhostAPIException("Unknown problem: %s" % (self.body))


class DreamhostConnection(ConnectionKey):
    """
    Connection class to connect to DreamHost's API servers
    """

    host = 'api.dreamhost.com'
    responseCls = DreamhostResponse
    format = 'json'

    def add_default_params(self, params):
        """
        Add key and format parameters to the request.  Eventually should add
        unique_id to prevent re-execution of a single request.
        """
        params['key'] = self.key
        params['format'] = self.format
        # params['unique_id'] = generate_unique_id()
        return params


class DreamhostNodeDriver(NodeDriver):
    """
    Node Driver for DreamHost PS
    """
    type = Provider.DREAMHOST
    api_name = 'dreamhost'
    name = "Dreamhost"
    website = 'http://dreamhost.com/'
    connectionCls = DreamhostConnection

    _sizes = DH_PS_SIZES

    def create_node(self, **kwargs):
        """Create a new Dreamhost node

        @inherits: :class:`NodeDriver.create_node`

        :keyword    ex_movedata: Copy all your existing users to this new PS
        :type       ex_movedata: ``str``
        """
        size = kwargs['size'].ram
        params = {
            'cmd': 'dreamhost_ps-add_ps',
            'movedata': kwargs.get('movedata', 'no'),
            'type': kwargs['image'].name,
            'size': size
        }
        data = self.connection.request('/', params).object
        return Node(
            id=data['added_web'],
            name=data['added_web'],
            state=NodeState.PENDING,
            public_ips=[],
            private_ips=[],
            driver=self.connection.driver,
            extra={
                'type': kwargs['image'].name
            }
        )

    def destroy_node(self, node):
        params = {
            'cmd': 'dreamhost_ps-remove_ps',
            'ps': node.id
        }
        try:
            return self.connection.request('/', params).success()
        except DreamhostAPIException:
            return False

    def reboot_node(self, node):
        params = {
            'cmd': 'dreamhost_ps-reboot',
            'ps': node.id
        }
        try:
            return self.connection.request('/', params).success()
        except DreamhostAPIException:
            return False

    def list_nodes(self, **kwargs):
        data = self.connection.request(
            '/', {'cmd': 'dreamhost_ps-list_ps'}).object
        return [self._to_node(n) for n in data]

    def list_images(self, **kwargs):
        data = self.connection.request(
            '/', {'cmd': 'dreamhost_ps-list_images'}).object
        images = []
        for img in data:
            images.append(NodeImage(
                id=img['image'],
                name=img['image'],
                driver=self.connection.driver
            ))
        return images

    def list_sizes(self, **kwargs):
        sizes = []
        for key, values in self._sizes.items():
            attributes = copy.deepcopy(values)
            attributes.update({'price': self._get_size_price(size_id=key)})
            sizes.append(NodeSize(driver=self.connection.driver, **attributes))

        return sizes

    def list_locations(self, **kwargs):
        raise NotImplementedError(
            'You cannot select a location for '
            'DreamHost Private Servers at this time.')

    def _resize_node(self, node, size):
        if (size < 300 or size > 4000):
            return False

        params = {
            'cmd': 'dreamhost_ps-set_size',
            'ps': node.id,
            'size': size
        }
        try:
            return self.connection.request('/', params).success()
        except DreamhostAPIException:
            return False

    def _to_node(self, data):
        """
        Convert the data from a DreamhostResponse object into a Node
        """
        return Node(
            id=data['ps'],
            name=data['ps'],
            state=NodeState.UNKNOWN,
            public_ips=[data['ip']],
            private_ips=[],
            driver=self.connection.driver,
            extra={
                'current_size': data['memory_mb'],
                'account_id': data['account_id'],
                'type': data['type']})
