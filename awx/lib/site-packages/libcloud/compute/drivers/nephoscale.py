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
NephoScale Cloud driver (http://www.nephoscale.com)
API documentation: http://docs.nephoscale.com
Created by Markos Gogoulos (https://mist.io)
"""

import base64
import sys
import time
import os
import binascii

from libcloud.utils.py3 import httplib
from libcloud.utils.py3 import b
from libcloud.utils.py3 import urlencode

from libcloud.compute.providers import Provider
from libcloud.common.base import JsonResponse, ConnectionUserAndKey
from libcloud.compute.types import (NodeState, InvalidCredsError,
                                    LibcloudError)
from libcloud.compute.base import (Node, NodeDriver, NodeImage, NodeSize,
                                   NodeLocation)
from libcloud.utils.networking import is_private_subnet

API_HOST = 'api.nephoscale.com'

NODE_STATE_MAP = {
    'on': NodeState.RUNNING,
    'off': NodeState.UNKNOWN,
    'unknown': NodeState.UNKNOWN,
}

VALID_RESPONSE_CODES = [httplib.OK, httplib.ACCEPTED, httplib.CREATED,
                        httplib.NO_CONTENT]

# used in create_node and specifies how many times to get the list of nodes and
# check if the newly created node is there. This is because when a request is
# sent to create a node, NephoScale replies with the job id, and not the node
# itself thus we don't have the ip addresses, that are required in deploy_node
CONNECT_ATTEMPTS = 10


class NodeKey(object):
    def __init__(self, id, name, public_key=None, key_group=None,
                 password=None):
        self.id = id
        self.name = name
        self.key_group = key_group
        self.password = password
        self.public_key = public_key

    def __repr__(self):
        return (('<NodeKey: id=%s, name=%s>') %
                (self.id, self.name))


class NephoscaleResponse(JsonResponse):
    """
    Nephoscale API Response
    """

    def parse_error(self):
        if self.status == httplib.UNAUTHORIZED:
            raise InvalidCredsError('Authorization Failed')
        if self.status == httplib.NOT_FOUND:
            raise Exception("The resource you are looking for is not found.")

        return self.body

    def success(self):
        return self.status in VALID_RESPONSE_CODES


class NephoscaleConnection(ConnectionUserAndKey):
    """
    Nephoscale connection class.
    Authenticates to the API through Basic Authentication
    with username/password
    """
    host = API_HOST
    responseCls = NephoscaleResponse

    allow_insecure = False

    def add_default_headers(self, headers):
        """
        Add parameters that are necessary for every request
        """
        user_b64 = base64.b64encode(b('%s:%s' % (self.user_id, self.key)))
        headers['Authorization'] = 'Basic %s' % (user_b64.decode('utf-8'))
        return headers


class NephoscaleNodeDriver(NodeDriver):
    """
    Nephoscale node driver class.

    >>> from libcloud.compute.providers import get_driver
    >>> driver = get_driver('nephoscale')
    >>> conn = driver('nepho_user','nepho_password')
    >>> conn.list_nodes()
    """

    type = Provider.NEPHOSCALE
    api_name = 'nephoscale'
    name = 'NephoScale'
    website = 'http://www.nephoscale.com'
    connectionCls = NephoscaleConnection
    features = {'create_node': ['ssh_key']}

    def list_locations(self):
        """
        List available zones for deployment

        :rtype: ``list`` of :class:`NodeLocation`
        """
        result = self.connection.request('/datacenter/zone/').object
        locations = []
        for value in result.get('data', []):
            location = NodeLocation(id=value.get('id'),
                                    name=value.get('name'),
                                    country='US',
                                    driver=self)
            locations.append(location)
        return locations

    def list_images(self):
        """
        List available images for deployment

        :rtype: ``list`` of :class:`NodeImage`
        """
        result = self.connection.request('/image/server/').object
        images = []
        for value in result.get('data', []):
            extra = {'architecture': value.get('architecture'),
                     'disks': value.get('disks'),
                     'billable_type': value.get('billable_type'),
                     'pcpus': value.get('pcpus'),
                     'cores': value.get('cores'),
                     'uri': value.get('uri'),
                     'storage': value.get('storage'),
                     }
            image = NodeImage(id=value.get('id'),
                              name=value.get('friendly_name'),
                              driver=self,
                              extra=extra)
            images.append(image)
        return images

    def list_sizes(self):
        """
        List available sizes containing prices

        :rtype: ``list`` of :class:`NodeSize`
        """
        result = self.connection.request('/server/type/cloud/').object
        sizes = []
        for value in result.get('data', []):
            value_id = value.get('id')
            size = NodeSize(id=value_id,
                            name=value.get('friendly_name'),
                            ram=value.get('ram'),
                            disk=value.get('storage'),
                            bandwidth=None,
                            price=self._get_size_price(size_id=str(value_id)),
                            driver=self)
            sizes.append(size)

        return sorted(sizes, key=lambda k: k.price)

    def list_nodes(self):
        """
        List available nodes

        :rtype: ``list`` of :class:`Node`
        """
        result = self.connection.request('/server/cloud/').object
        nodes = [self._to_node(value) for value in result.get('data', [])]
        return nodes

    def rename_node(self, node, name, hostname=None):
        """rename a cloud server, optionally specify hostname too"""
        data = {'name': name}
        if hostname:
            data['hostname'] = hostname
        params = urlencode(data)
        result = self.connection.request('/server/cloud/%s/' % node.id,
                                         data=params, method='PUT').object
        return result.get('response') in VALID_RESPONSE_CODES

    def reboot_node(self, node):
        """reboot a running node"""
        result = self.connection.request('/server/cloud/%s/initiator/restart/'
                                         % node.id, method='POST').object
        return result.get('response') in VALID_RESPONSE_CODES

    def ex_start_node(self, node):
        """start a stopped node"""
        result = self.connection.request('/server/cloud/%s/initiator/start/'
                                         % node.id, method='POST').object
        return result.get('response') in VALID_RESPONSE_CODES

    def ex_stop_node(self, node):
        """stop a running node"""
        result = self.connection.request('/server/cloud/%s/initiator/stop/'
                                         % node.id, method='POST').object
        return result.get('response') in VALID_RESPONSE_CODES

    def destroy_node(self, node):
        """destroy a node"""
        result = self.connection.request('/server/cloud/%s/' % node.id,
                                         method='DELETE').object
        return result.get('response') in VALID_RESPONSE_CODES

    def ex_list_keypairs(self, ssh=False, password=False, key_group=None):
        """
        List available console and server keys
        There are two types of keys for NephoScale, ssh and password keys.
        If run without arguments, lists all keys. Otherwise list only
        ssh keys, or only password keys.
        Password keys with key_group 4 are console keys. When a server
        is created, it has two keys, one password or ssh key, and
        one password console key.

        :keyword ssh: if specified, show ssh keys only (optional)
        :type    ssh: ``bool``

        :keyword password: if specified, show password keys only (optional)
        :type    password: ``bool``

        :keyword key_group: if specified, show keys with this key_group only
                            eg key_group=4 for console password keys (optional)
        :type    key_group: ``int``

        :rtype: ``list`` of :class:`NodeKey`
        """
        if (ssh and password):
            raise LibcloudError('You can only supply ssh or password. To \
get all keys call with no arguments')
        if ssh:
            result = self.connection.request('/key/sshrsa/').object
        elif password:
            result = self.connection.request('/key/password/').object
        else:
            result = self.connection.request('/key/').object
        keys = [self._to_key(value) for value in result.get('data', [])]

        if key_group:
            keys = [key for key in keys if
                    key.key_group == key_group]
        return keys

    def ex_create_keypair(self, name, public_key=None, password=None,
                          key_group=None):
        """Creates a key, ssh or password, for server or console
           The group for the key (key_group) is 1 for Server and 4 for Console
           Returns the id of the created key
        """
        if public_key:
            if not key_group:
                key_group = 1
            data = {
                'name': name,
                'public_key': public_key,
                'key_group': key_group

            }
            params = urlencode(data)
            result = self.connection.request('/key/sshrsa/', data=params,
                                             method='POST').object
        else:
            if not key_group:
                key_group = 4
            if not password:
                password = self.random_password()
                data = {
                    'name': name,
                    'password': password,
                    'key_group': key_group
                }
            params = urlencode(data)
            result = self.connection.request('/key/password/', data=params,
                                             method='POST').object
        return result.get('data', {}).get('id', '')

    def ex_delete_keypair(self, key_id, ssh=False):
        """Delete an ssh key or password given it's id
        """
        if ssh:
            result = self.connection.request('/key/sshrsa/%s/' % key_id,
                                             method='DELETE').object
        else:
            result = self.connection.request('/key/password/%s/' % key_id,
                                             method='DELETE').object
        return result.get('response') in VALID_RESPONSE_CODES

    def create_node(self, name, size, image, server_key=None,
                    console_key=None, zone=None, **kwargs):
        """Creates the node, and sets the ssh key, console key
        NephoScale will respond with a 200-200 response after sending a valid
        request. If nowait=True is specified in the args, we then ask a few
        times until the server is created and assigned a public IP address,
        so that deploy_node can be run

        >>> from libcloud.compute.providers import get_driver
        >>> driver = get_driver('nephoscale')
        >>> conn = driver('nepho_user','nepho_password')
        >>> conn.list_nodes()
        >>> name = 'staging-server'
        >>> size = conn.list_sizes()[0]
        <NodeSize: id=27, ...name=CS025 - 0.25GB, 10GB, ...>
        >>> image = conn.list_images()[9]
        <NodeImage: id=49, name=Linux Ubuntu Server 10.04 LTS 64-bit, ...>
        >>> server_keys = conn.ex_list_keypairs(key_group=1)[0]
        <NodeKey: id=71211, name=markos>
        >>> server_key = conn.ex_list_keypairs(key_group=1)[0].id
        70867
        >>> console_keys = conn.ex_list_keypairs(key_group=4)[0]
        <NodeKey: id=71213, name=mistio28434>
        >>> console_key = conn.ex_list_keypairs(key_group=4)[0].id
        70907
        >>> node = conn.create_node(name=name, size=size, image=image, \
                console_key=console_key, server_key=server_key)

        We can also create an ssh key, plus a console key and
        deploy node with them
        >>> server_key = conn.ex_create_keypair(name, public_key='123')
        71211
        >>> console_key = conn.ex_create_keypair(name, key_group=4)
        71213

        We can increase the number of connect attempts to wait until
        the node is created, so that deploy_node has ip address to
        deploy the script
        We can also specify the location
        >>> location = conn.list_locations()[0]
        >>> node = conn.create_node(name=name,
            ...                     size=size,
            ...                     image=image,
            ...                     console_key=console_key,
            ...                     server_key=server_key,
            ...                     connect_attempts=10,
            ...                     nowait=True,
            ...                     zone=location.id)
        """
        hostname = kwargs.get('hostname', name)
        service_type = size.id
        image = image.id
        connect_attempts = int(kwargs.get('connect_attempts',
                               CONNECT_ATTEMPTS))

        data = {'name': name,
                'hostname': hostname,
                'service_type': service_type,
                'image': image,
                'server_key': server_key,
                'console_key': console_key,
                'zone': zone
                }

        params = urlencode(data)
        try:
            node = self.connection.request('/server/cloud/', data=params,
                                           method='POST')
        except Exception:
            e = sys.exc_info()[1]
            raise Exception("Failed to create node %s" % e)
        node = Node(id='', name=name, state=NodeState.UNKNOWN, public_ips=[],
                    private_ips=[], driver=self)

        nowait = kwargs.get('ex_wait', False)
        if not nowait:
            return node
        else:
            # try to get the created node public ips, for use in deploy_node
            # At this point we don't have the id of the newly created Node,
            # so search name in nodes
            created_node = False
            while connect_attempts > 0:
                nodes = self.list_nodes()
                created_node = [c_node for c_node in nodes if
                                c_node.name == name]
                if created_node:
                    return created_node[0]
                else:
                    time.sleep(60)
                    connect_attempts = connect_attempts - 1
            return node

    def _to_node(self, data):
        """Convert node in Node instances
        """

        state = NODE_STATE_MAP.get(data.get('power_status'), '4')
        public_ips = []
        private_ips = []
        ip_addresses = data.get('ipaddresses', '')
        # E.g. "ipaddresses": "198.120.14.6, 10.132.60.1"
        if ip_addresses:
            for ip in ip_addresses.split(','):
                ip = ip.replace(' ', '')
                if is_private_subnet(ip):
                    private_ips.append(ip)
                else:
                    public_ips.append(ip)
        extra = {
            'zone_data': data.get('zone'),
            'zone': data.get('zone', {}).get('name'),
            'image': data.get('image', {}).get('friendly_name'),
            'create_time': data.get('create_time'),
            'network_ports': data.get('network_ports'),
            'is_console_enabled': data.get('is_console_enabled'),
            'service_type': data.get('service_type', {}).get('friendly_name'),
            'hostname': data.get('hostname')
        }

        node = Node(id=data.get('id'), name=data.get('name'), state=state,
                    public_ips=public_ips, private_ips=private_ips,
                    driver=self, extra=extra)
        return node

    def _to_key(self, data):
        return NodeKey(id=data.get('id'),
                       name=data.get('name'),
                       password=data.get('password'),
                       key_group=data.get('key_group'),
                       public_key=data.get('public_key'))

    def random_password(self, size=8):
        value = os.urandom(size)
        password = binascii.hexlify(value).decode('ascii')
        return password[:size]
