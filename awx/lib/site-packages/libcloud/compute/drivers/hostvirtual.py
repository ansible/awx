# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
libcloud driver for the Host Virtual Inc. (VR) API
Home page http://www.vr.org/
"""

import time

try:
    import simplejson as json
except ImportError:
    import json

from libcloud.common.hostvirtual import HostVirtualResponse
from libcloud.common.hostvirtual import HostVirtualConnection
from libcloud.common.hostvirtual import HostVirtualException
from libcloud.compute.providers import Provider
from libcloud.compute.types import NodeState
from libcloud.compute.base import Node, NodeDriver
from libcloud.compute.base import NodeImage, NodeSize, NodeLocation
from libcloud.compute.base import NodeAuthSSHKey, NodeAuthPassword

API_ROOT = ''

NODE_STATE_MAP = {
    'BUILDING': NodeState.PENDING,
    'PENDING': NodeState.PENDING,
    'RUNNING': NodeState.RUNNING,  # server is powered up
    'STOPPING': NodeState.REBOOTING,
    'REBOOTING': NodeState.REBOOTING,
    'STARTING': NodeState.REBOOTING,
    'TERMINATED': NodeState.TERMINATED,  # server is powered down
    'STOPPED': NodeState.STOPPED
}

DEFAULT_NODE_LOCATION_ID = 4


class HostVirtualComputeResponse(HostVirtualResponse):
    pass


class HostVirtualComputeConnection(HostVirtualConnection):
    responseCls = HostVirtualComputeResponse


class HostVirtualNodeDriver(NodeDriver):
    type = Provider.HOSTVIRTUAL
    name = 'HostVirtual'
    website = 'http://www.vr.org'
    connectionCls = HostVirtualComputeConnection
    features = {'create_node': ['ssh_key', 'password']}

    def __init__(self, key, secure=True, host=None, port=None):
        self.location = None
        super(HostVirtualNodeDriver, self).__init__(key=key, secure=secure,
                                                    host=host, port=port)

    def _to_node(self, data):
        state = NODE_STATE_MAP[data['status']]
        public_ips = []
        private_ips = []
        extra = {}

        if 'plan_id' in data:
            extra['size'] = data['plan_id']
        if 'os_id' in data:
            extra['image'] = data['os_id']
        if 'location_id' in data:
            extra['location'] = data['location_id']
        if 'ip' in data:
            public_ips.append(data['ip'])

        node = Node(id=data['mbpkgid'], name=data['fqdn'], state=state,
                    public_ips=public_ips, private_ips=private_ips,
                    driver=self.connection.driver, extra=extra)
        return node

    def list_locations(self):
        result = self.connection.request(API_ROOT + '/cloud/locations/').object
        locations = []
        for dc in result:
            locations.append(NodeLocation(
                dc["id"],
                dc["name"],
                dc["name"].split(',')[1].replace(" ", ""),  # country
                self))
        return locations

    def list_sizes(self, location=None):
        params = {}
        if location:
            params = {'location': location.id}
        result = self.connection.request(
            API_ROOT + '/cloud/sizes/',
            data=json.dumps(params)).object
        sizes = []
        for size in result:
            n = NodeSize(id=size['plan_id'],
                         name=size['plan'],
                         ram=size['ram'],
                         disk=size['disk'],
                         bandwidth=size['transfer'],
                         price=size['price'],
                         driver=self.connection.driver)
            sizes.append(n)
        return sizes

    def list_images(self):
        result = self.connection.request(API_ROOT + '/cloud/images/').object
        images = []
        for image in result:
            i = NodeImage(id=image["id"],
                          name=image["os"],
                          driver=self.connection.driver,
                          extra=image)
            del i.extra['id']
            del i.extra['os']
            images.append(i)
        return images

    def list_nodes(self):
        result = self.connection.request(API_ROOT + '/cloud/servers/').object
        nodes = []
        for value in result:
            node = self._to_node(value)
            nodes.append(node)
        return nodes

    def _wait_for_node(self, node_id, timeout=30, interval=5.0):
        """
        :param node_id: ID of the node to wait for.
        :type node_id: ``int``

        :param timeout: Timeout (in seconds).
        :type timeout: ``int``

        :param interval: How long to wait (in seconds) between each attempt.
        :type interval: ``float``
        """
        # poll until we get a node
        for i in range(0, timeout, int(interval)):
            try:
                node = self.ex_get_node(node_id)
                return node
            except HostVirtualException:
                time.sleep(interval)

        raise HostVirtualException(412, 'Timedout on getting node details')

    def create_node(self, **kwargs):
        dc = None

        size = kwargs['size']
        image = kwargs['image']

        auth = self._get_and_check_auth(kwargs.get('auth'))

        params = {'plan': size.name}

        dc = DEFAULT_NODE_LOCATION_ID
        if 'location' in kwargs:
            dc = kwargs['location'].id

        # simply order a package first
        result = self.connection.request(API_ROOT + '/cloud/buy/',
                                         data=json.dumps(params),
                                         method='POST').object

        # create a stub node
        stub_node = self._to_node({
            'mbpkgid': result['id'],
            'status': 'PENDING',
            'fqdn': kwargs['name'],
            'plan_id': size.id,
            'os_id': image.id,
            'location_id': dc
        })

        # provisioning a server using the stub node
        self.ex_provision_node(node=stub_node, auth=auth)
        node = self._wait_for_node(stub_node.id)

        if getattr(auth, 'generated', False):
            node.extra['password'] = auth.password

        return node

    def reboot_node(self, node):
        params = {'force': 0, 'mbpkgid': node.id}
        result = self.connection.request(
            API_ROOT + '/cloud/server/reboot',
            data=json.dumps(params),
            method='POST').object

        return bool(result)

    def destroy_node(self, node):
        params = {
            'mbpkgid': node.id,
            # 'reason': 'Submitted through Libcloud API'
        }

        result = self.connection.request(
            API_ROOT + '/cloud/cancel', data=json.dumps(params),
            method='POST').object

        return bool(result)

    def ex_get_node(self, node_id):
        """
        Get a single node.

        :param      node_id: id of the node that we need the node object for
        :type       node_id: ``str``

        :rtype: :class:`Node`
        """

        params = {'mbpkgid': node_id}
        result = self.connection.request(
            API_ROOT + '/cloud/server', params=params).object
        node = self._to_node(result)
        return node

    def ex_stop_node(self, node):
        """
        Stop a node.

        :param      node: Node which should be used
        :type       node: :class:`Node`

        :rtype: ``bool``
        """
        params = {'force': 0, 'mbpkgid': node.id}
        result = self.connection.request(
            API_ROOT + '/cloud/server/shutdown',
            data=json.dumps(params),
            method='POST').object

        return bool(result)

    def ex_start_node(self, node):
        """
        Start a node.

        :param      node: Node which should be used
        :type       node: :class:`Node`

        :rtype: ``bool``
        """
        params = {'mbpkgid': node.id}
        result = self.connection.request(
            API_ROOT + '/cloud/server/start',
            data=json.dumps(params),
            method='POST').object

        return bool(result)

    def ex_provision_node(self, **kwargs):
        """
        Provision a server on a VR package and get it booted

        :keyword node: node which should be used
        :type    node: :class:`Node`

        :keyword image: The distribution to deploy on your server (mandatory)
        :type    image: :class:`NodeImage`

        :keyword auth: an SSH key or root password (mandatory)
        :type    auth: :class:`NodeAuthSSHKey` or :class:`NodeAuthPassword`

        :keyword location: which datacenter to create the server in
        :type    location: :class:`NodeLocation`

        :return: Node representing the newly built server
        :rtype: :class:`Node`
        """

        node = kwargs['node']

        if 'image' in kwargs:
            image = kwargs['image']
        else:
            image = node.extra['image']

        params = {
            'mbpkgid': node.id,
            'image': image,
            'fqdn': node.name,
            'location': node.extra['location'],
        }

        auth = kwargs['auth']

        ssh_key = None
        password = None
        if isinstance(auth, NodeAuthSSHKey):
            ssh_key = auth.pubkey
            params['ssh_key'] = ssh_key
        elif isinstance(auth, NodeAuthPassword):
            password = auth.password
            params['password'] = password

        if not ssh_key and not password:
            raise HostVirtualException(500, "Need SSH key or Root password")

        result = self.connection.request(API_ROOT + '/cloud/server/build',
                                         data=json.dumps(params),
                                         method='POST').object
        return bool(result)

    def ex_delete_node(self, node):
        """
        Delete a node.

        :param      node: Node which should be used
        :type       node: :class:`Node`

        :rtype: ``bool``
        """

        params = {'mbpkgid': node.id}
        result = self.connection.request(
            API_ROOT + '/cloud/server/delete', data=json.dumps(params),
            method='POST').object

        return bool(result)
