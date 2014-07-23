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
libcloud driver for the Blue Box Blocks API

This driver implements all libcloud functionality for the Blue Box Blocks API.

Blue Box home page            http://bluebox.net
Blue Box API documentation    https://boxpanel.bluebox
.net/public/the_vault/index.php/Blocks_API
"""

import copy
import base64

from libcloud.utils.py3 import urlencode
from libcloud.utils.py3 import b

from libcloud.common.base import JsonResponse, ConnectionUserAndKey
from libcloud.compute.providers import Provider
from libcloud.compute.types import NodeState, InvalidCredsError
from libcloud.compute.base import Node, NodeDriver
from libcloud.compute.base import NodeSize, NodeImage, NodeLocation
from libcloud.compute.base import NodeAuthPassword, NodeAuthSSHKey

# Current end point for Blue Box API.
BLUEBOX_API_HOST = "boxpanel.bluebox.net"

# The API doesn't currently expose all of the required values for libcloud,
# so we simply list what's available right now, along with all of the various
# attributes that are needed by libcloud.
BLUEBOX_INSTANCE_TYPES = {
    '1gb': {
        'id': '94fd37a7-2606-47f7-84d5-9000deda52ae',
        'name': 'Block 1GB Virtual Server',
        'ram': 1024,
        'disk': 20,
        'cpu': 0.5
    },
    '2gb': {
        'id': 'b412f354-5056-4bf0-a42f-6ddd998aa092',
        'name': 'Block 2GB Virtual Server',
        'ram': 2048,
        'disk': 25,
        'cpu': 1
    },
    '4gb': {
        'id': '0cd183d3-0287-4b1a-8288-b3ea8302ed58',
        'name': 'Block 4GB Virtual Server',
        'ram': 4096,
        'disk': 50,
        'cpu': 2
    },
    '8gb': {
        'id': 'b9b87a5b-2885-4a2e-b434-44a163ca6251',
        'name': 'Block 8GB Virtual Server',
        'ram': 8192,
        'disk': 100,
        'cpu': 4
    }
}

RAM_PER_CPU = 2048

NODE_STATE_MAP = {'queued': NodeState.PENDING,
                  'building': NodeState.PENDING,
                  'running': NodeState.RUNNING,
                  'error': NodeState.TERMINATED,
                  'unknown': NodeState.UNKNOWN}


class BlueboxResponse(JsonResponse):
    def parse_error(self):
        if int(self.status) == 401:
            if not self.body:
                raise InvalidCredsError(str(self.status) + ': ' + self.error)
            else:
                raise InvalidCredsError(self.body)
        return self.body


class BlueboxNodeSize(NodeSize):
    def __init__(self, id, name, cpu, ram, disk, price, driver):
        self.id = id
        self.name = name
        self.cpu = cpu
        self.ram = ram
        self.disk = disk
        self.price = price
        self.driver = driver

    def __repr__(self):
        return ((
                '<NodeSize: id=%s, name=%s, cpu=%s, ram=%s, disk=%s, '
                'price=%s, driver=%s ...>')
                % (self.id, self.name, self.cpu, self.ram, self.disk,
                   self.price, self.driver.name))


class BlueboxConnection(ConnectionUserAndKey):
    """
    Connection class for the Bluebox driver
    """

    host = BLUEBOX_API_HOST
    secure = True
    responseCls = BlueboxResponse

    allow_insecure = False

    def add_default_headers(self, headers):
        user_b64 = base64.b64encode(b('%s:%s' % (self.user_id, self.key)))
        headers['Authorization'] = 'Basic %s' % (user_b64)
        return headers


class BlueboxNodeDriver(NodeDriver):
    """
    Bluebox Blocks node driver
    """

    connectionCls = BlueboxConnection
    type = Provider.BLUEBOX
    api_name = 'bluebox'
    name = 'Bluebox Blocks'
    website = 'http://bluebox.net'
    features = {'create_node': ['ssh_key', 'password']}

    def list_nodes(self):
        result = self.connection.request('/api/blocks.json')
        return [self._to_node(i) for i in result.object]

    def list_sizes(self, location=None):
        sizes = []
        for key, values in list(BLUEBOX_INSTANCE_TYPES.items()):
            attributes = copy.deepcopy(values)
            attributes.update({'price': self._get_size_price(size_id=key)})
            sizes.append(BlueboxNodeSize(driver=self.connection.driver,
                                         **attributes))

        return sizes

    def list_images(self, location=None):
        result = self.connection.request('/api/block_templates.json')
        images = []
        for image in result.object:
            images.extend([self._to_image(image)])

        return images

    def create_node(self, **kwargs):
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        size = kwargs["size"]

        name = kwargs['name']
        image = kwargs['image']
        size = kwargs['size']

        auth = self._get_and_check_auth(kwargs.get('auth'))

        data = {
            'hostname': name,
            'product': size.id,
            'template': image.id
        }

        ssh = None
        password = None

        if isinstance(auth, NodeAuthSSHKey):
            ssh = auth.pubkey
            data.update(ssh_public_key=ssh)
        elif isinstance(auth, NodeAuthPassword):
            password = auth.password
            data.update(password=password)

        if "ex_username" in kwargs:
            data.update(username=kwargs["ex_username"])

        if not ssh and not password:
            raise Exception("SSH public key or password required.")

        params = urlencode(data)
        result = self.connection.request('/api/blocks.json', headers=headers,
                                         data=params, method='POST')
        node = self._to_node(result.object)

        if getattr(auth, "generated", False):
            node.extra['password'] = auth.password

        return node

    def destroy_node(self, node):
        url = '/api/blocks/%s.json' % (node.id)
        result = self.connection.request(url, method='DELETE')

        return result.status == 200

    def list_locations(self):
        return [NodeLocation(0, "Blue Box Seattle US", 'US', self)]

    def reboot_node(self, node):
        url = '/api/blocks/%s/reboot.json' % (node.id)
        result = self.connection.request(url, method="PUT")
        return result.status == 200

    def _to_node(self, vm):
        state = NODE_STATE_MAP[vm.get('status', NodeState.UNKNOWN)]
        n = Node(id=vm['id'],
                 name=vm['hostname'],
                 state=state,
                 public_ips=[ip['address'] for ip in vm['ips']],
                 private_ips=[],
                 extra={'storage': vm['storage'], 'cpu': vm['cpu']},
                 driver=self.connection.driver)
        return n

    def _to_image(self, image):
        image = NodeImage(id=image['id'],
                          name=image['description'],
                          driver=self.connection.driver)
        return image
