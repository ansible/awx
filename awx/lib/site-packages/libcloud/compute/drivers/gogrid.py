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
GoGrid driver
"""
import time
import hashlib
import copy

from libcloud.utils.py3 import b

from libcloud.common.types import InvalidCredsError, LibcloudError
from libcloud.common.gogrid import GoGridConnection, BaseGoGridDriver
from libcloud.compute.providers import Provider
from libcloud.compute.types import NodeState
from libcloud.compute.base import Node, NodeDriver
from libcloud.compute.base import NodeSize, NodeImage, NodeLocation

STATE = {
    "Starting": NodeState.PENDING,
    "On": NodeState.RUNNING,
    "On/Saving": NodeState.RUNNING,
    "Off": NodeState.PENDING,
    "Restarting": NodeState.REBOOTING,
    "Saving": NodeState.PENDING,
    "Restoring": NodeState.PENDING,
}

GOGRID_INSTANCE_TYPES = {
    '512MB': {'id': '512MB',
              'name': '512MB',
              'ram': 512,
              'disk': 30,
              'bandwidth': None},
    '1GB': {'id': '1GB',
            'name': '1GB',
            'ram': 1024,
            'disk': 60,
            'bandwidth': None},
    '2GB': {'id': '2GB',
            'name': '2GB',
            'ram': 2048,
            'disk': 120,
            'bandwidth': None},
    '4GB': {'id': '4GB',
            'name': '4GB',
            'ram': 4096,
            'disk': 240,
            'bandwidth': None},
    '8GB': {'id': '8GB',
            'name': '8GB',
            'ram': 8192,
            'disk': 480,
            'bandwidth': None},
    '16GB': {'id': '16GB',
             'name': '16GB',
             'ram': 16384,
             'disk': 960,
             'bandwidth': None},
    '24GB': {'id': '24GB',
             'name': '24GB',
             'ram': 24576,
             'disk': 960,
             'bandwidth': None},
}


class GoGridNode(Node):
    # Generating uuid based on public ip to get around missing id on
    # create_node in gogrid api
    #
    # Used public ip since it is not mutable and specified at create time,
    # so uuid of node should not change after add is completed
    def get_uuid(self):
        return hashlib.sha1(
            b("%s:%s" % (self.public_ips, self.driver.type))
        ).hexdigest()


class GoGridNodeDriver(BaseGoGridDriver, NodeDriver):
    """
    GoGrid node driver
    """

    connectionCls = GoGridConnection
    type = Provider.GOGRID
    api_name = 'gogrid'
    name = 'GoGrid'
    website = 'http://www.gogrid.com/'
    features = {"create_node": ["generates_password"]}

    _instance_types = GOGRID_INSTANCE_TYPES

    def __init__(self, *args, **kwargs):
        """
        @inherits: :class:`NodeDriver.__init__`
        """
        super(GoGridNodeDriver, self).__init__(*args, **kwargs)

    def _get_state(self, element):
        try:
            return STATE[element['state']['name']]
        except:
            pass
        return NodeState.UNKNOWN

    def _get_ip(self, element):
        return element.get('ip').get('ip')

    def _get_id(self, element):
        return element.get('id')

    def _to_node(self, element, password=None):
        state = self._get_state(element)
        ip = self._get_ip(element)
        id = self._get_id(element)
        n = GoGridNode(id=id,
                       name=element['name'],
                       state=state,
                       public_ips=[ip],
                       private_ips=[],
                       extra={'ram': element.get('ram').get('name'),
                              'description': element.get('description', '')},
                       driver=self.connection.driver)
        if password:
            n.extra['password'] = password

        return n

    def _to_image(self, element):
        n = NodeImage(id=element['id'],
                      name=element['friendlyName'],
                      driver=self.connection.driver)
        return n

    def _to_images(self, object):
        return [self._to_image(el)
                for el in object['list']]

    def _to_location(self, element):
        location = NodeLocation(id=element['id'],
                                name=element['name'],
                                country="US",
                                driver=self.connection.driver)
        return location

    def _to_locations(self, object):
        return [self._to_location(el)
                for el in object['list']]

    def list_images(self, location=None):
        params = {}
        if location is not None:
            params["datacenter"] = location.id
        images = self._to_images(
            self.connection.request('/api/grid/image/list', params).object)
        return images

    def list_nodes(self):
        """
        @inherits: :class:`NodeDriver.list_nodes`
        :rtype: ``list`` of :class:`GoGridNode`
        """
        passwords_map = {}

        res = self._server_list()
        try:
            for password in self._password_list()['list']:
                try:
                    passwords_map[password['server']['id']] = \
                        password['password']
                except KeyError:
                    pass
        except InvalidCredsError:
            # some gogrid API keys don't have permission to access the
            # password list.
            pass

        return [self._to_node(el, passwords_map.get(el.get('id')))
                for el in res['list']]

    def reboot_node(self, node):
        """
        @inherits: :class:`NodeDriver.reboot_node`
        :type node: :class:`GoGridNode`
        """
        id = node.id
        power = 'restart'
        res = self._server_power(id, power)
        if not res.success():
            raise Exception(res.parse_error())
        return True

    def destroy_node(self, node):
        """
        @inherits: :class:`NodeDriver.reboot_node`
        :type node: :class:`GoGridNode`
        """
        id = node.id
        res = self._server_delete(id)
        if not res.success():
            raise Exception(res.parse_error())
        return True

    def _server_list(self):
        return self.connection.request('/api/grid/server/list').object

    def _password_list(self):
        return self.connection.request('/api/support/password/list').object

    def _server_power(self, id, power):
        # power in ['start', 'stop', 'restart']
        params = {'id': id, 'power': power}
        return self.connection.request("/api/grid/server/power", params,
                                       method='POST')

    def _server_delete(self, id):
        params = {'id': id}
        return self.connection.request("/api/grid/server/delete", params,
                                       method='POST')

    def _get_first_ip(self, location=None):
        ips = self.ex_list_ips(public=True, assigned=False, location=location)
        try:
            return ips[0].ip
        except IndexError:
            raise LibcloudError('No public unassigned IPs left',
                                GoGridNodeDriver)

    def list_sizes(self, location=None):
        sizes = []
        for key, values in self._instance_types.items():
            attributes = copy.deepcopy(values)
            attributes.update({'price': self._get_size_price(size_id=key)})
            sizes.append(NodeSize(driver=self.connection.driver, **attributes))

        return sizes

    def list_locations(self):
        locations = self._to_locations(
            self.connection.request('/api/common/lookup/list',
                                    params={'lookup': 'ip.datacenter'}).object)
        return locations

    def ex_create_node_nowait(self, **kwargs):
        """Don't block until GoGrid allocates id for a node
        but return right away with id == None.

        The existence of this method is explained by the fact
        that GoGrid assigns id to a node only few minutes after
        creation.


        :keyword    name:   String with a name for this new node (required)
        :type       name:   ``str``

        :keyword    size:   The size of resources allocated to this node .
                            (required)
        :type       size:   :class:`NodeSize`

        :keyword    image:  OS Image to boot on node. (required)
        :type       image:  :class:`NodeImage`

        :keyword    ex_description: Description of a Node
        :type       ex_description: ``str``

        :keyword    ex_ip: Public IP address to use for a Node. If not
            specified, first available IP address will be picked
        :type       ex_ip: ``str``

        :rtype: :class:`GoGridNode`
        """
        name = kwargs['name']
        image = kwargs['image']
        size = kwargs['size']
        try:
            ip = kwargs['ex_ip']
        except KeyError:
            ip = self._get_first_ip(kwargs.get('location'))

        params = {'name': name,
                  'image': image.id,
                  'description': kwargs.get('ex_description', ''),
                  'server.ram': size.id,
                  'ip': ip}

        object = self.connection.request('/api/grid/server/add',
                                         params=params, method='POST').object
        node = self._to_node(object['list'][0])

        return node

    def create_node(self, **kwargs):
        """Create a new GoGird node

        @inherits: :class:`NodeDriver.create_node`

        :keyword    ex_description: Description of a Node
        :type       ex_description: ``str``

        :keyword    ex_ip: Public IP address to use for a Node. If not
                    specified, first available IP address will be picked
        :type       ex_ip: ``str``

        :rtype: :class:`GoGridNode`
        """
        node = self.ex_create_node_nowait(**kwargs)

        timeout = 60 * 20
        waittime = 0
        interval = 2 * 60

        while node.id is None and waittime < timeout:
            nodes = self.list_nodes()

            for i in nodes:
                if i.public_ips[0] == node.public_ips[0] and i.id is not None:
                    return i

            waittime += interval
            time.sleep(interval)

        if id is None:
            raise Exception(
                "Wasn't able to wait for id allocation for the node %s"
                % str(node))

        return node

    def ex_save_image(self, node, name):
        """Create an image for node.

        Please refer to GoGrid documentation to get info
        how prepare a node for image creation:

        http://wiki.gogrid.com/wiki/index.php/MyGSI

        :keyword    node: node to use as a base for image
        :type       node: :class:`GoGridNode`

        :keyword    name: name for new image
        :type       name: ``str``

        :rtype: :class:`NodeImage`
        """
        params = {'server': node.id,
                  'friendlyName': name}
        object = self.connection.request('/api/grid/image/save', params=params,
                                         method='POST').object

        return self._to_images(object)[0]

    def ex_edit_node(self, **kwargs):
        """Change attributes of a node.

        :keyword    node: node to be edited (required)
        :type       node: :class:`GoGridNode`

        :keyword    size: new size of a node (required)
        :type       size: :class:`NodeSize`

        :keyword    ex_description: new description of a node
        :type       ex_description: ``str``

        :rtype: :class:`Node`
        """
        node = kwargs['node']
        size = kwargs['size']

        params = {'id': node.id,
                  'server.ram': size.id}

        if 'ex_description' in kwargs:
            params['description'] = kwargs['ex_description']

        object = self.connection.request('/api/grid/server/edit',
                                         params=params).object

        return self._to_node(object['list'][0])

    def ex_edit_image(self, **kwargs):
        """Edit metadata of a server image.

        :keyword    image: image to be edited (required)
        :type       image: :class:`NodeImage`

        :keyword    public: should be the image public (required)
        :type       public: ``bool``

        :keyword    ex_description: description of the image (optional)
        :type       ex_description: ``str``

        :keyword    name: name of the image
        :type       name: ``str``

        :rtype: :class:`NodeImage`
        """

        image = kwargs['image']
        public = kwargs['public']

        params = {'id': image.id,
                  'isPublic': str(public).lower()}

        if 'ex_description' in kwargs:
            params['description'] = kwargs['ex_description']

        if 'name' in kwargs:
            params['friendlyName'] = kwargs['name']

        object = self.connection.request('/api/grid/image/edit',
                                         params=params).object

        return self._to_image(object['list'][0])

    def ex_list_ips(self, **kwargs):
        """Return list of IP addresses assigned to
        the account.

        :keyword    public: set to True to list only
                    public IPs or False to list only
                    private IPs. Set to None or not specify
                    at all not to filter by type
        :type       public: ``bool``

        :keyword    assigned: set to True to list only addresses
                    assigned to servers, False to list unassigned
                    addresses and set to None or don't set at all
                    not no filter by state
        :type       assigned: ``bool``

        :keyword    location: filter IP addresses by location
        :type       location: :class:`NodeLocation`

        :rtype: ``list`` of :class:`GoGridIpAddress`
        """

        params = {}

        if "public" in kwargs and kwargs["public"] is not None:
            params["ip.type"] = {True: "Public",
                                 False: "Private"}[kwargs["public"]]
        if "assigned" in kwargs and kwargs["assigned"] is not None:
            params["ip.state"] = {True: "Assigned",
                                  False: "Unassigned"}[kwargs["assigned"]]
        if "location" in kwargs and kwargs['location'] is not None:
            params['datacenter'] = kwargs['location'].id

        ips = self._to_ips(
            self.connection.request('/api/grid/ip/list',
                                    params=params).object)
        return ips
