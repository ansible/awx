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
Dummy Driver

@note: This driver is out of date
"""
import uuid
import socket
import struct

from libcloud.common.base import ConnectionKey
from libcloud.compute.base import NodeImage, NodeSize, Node
from libcloud.compute.base import NodeDriver, NodeLocation
from libcloud.compute.base import KeyPair
from libcloud.compute.types import Provider, NodeState


class DummyConnection(ConnectionKey):
    """
    Dummy connection class
    """

    def connect(self, host=None, port=None):
        pass


class DummyNodeDriver(NodeDriver):
    """
    Dummy node driver

    This is a fake driver which appears to always create or destroy
    nodes successfully.

    >>> from libcloud.compute.drivers.dummy import DummyNodeDriver
    >>> driver = DummyNodeDriver(0)
    >>> node=driver.create_node()
    >>> node.public_ips[0]
    '127.0.0.3'
    >>> node.name
    'dummy-3'

    If the credentials you give convert to an integer then the next
    node to be created will be one higher.

    Each time you create a node you will get a different IP address.

    >>> driver = DummyNodeDriver(22)
    >>> node=driver.create_node()
    >>> node.name
    'dummy-23'

    """

    name = "Dummy Node Provider"
    website = 'http://example.com'
    type = Provider.DUMMY

    def __init__(self, creds):
        """
        :param  creds: Credentials
        :type   creds: ``str``

        :rtype: ``None``
        """
        self.creds = creds
        try:
            num = int(creds)
        except ValueError:
            num = None
        if num:
            self.nl = []
            startip = _ip_to_int('127.0.0.1')
            for i in range(num):
                ip = _int_to_ip(startip + i)
                self.nl.append(
                    Node(id=i,
                         name='dummy-%d' % (i),
                         state=NodeState.RUNNING,
                         public_ips=[ip],
                         private_ips=[],
                         driver=self,
                         extra={'foo': 'bar'})
                )
        else:
            self.nl = [
                Node(id=1,
                     name='dummy-1',
                     state=NodeState.RUNNING,
                     public_ips=['127.0.0.1'],
                     private_ips=[],
                     driver=self,
                     extra={'foo': 'bar'}),
                Node(id=2,
                     name='dummy-2',
                     state=NodeState.RUNNING,
                     public_ips=['127.0.0.1'],
                     private_ips=[],
                     driver=self,
                     extra={'foo': 'bar'}),
            ]
        self.connection = DummyConnection(self.creds)

    def get_uuid(self, unique_field=None):
        """

        :param  unique_field: Unique field
        :type   unique_field: ``bool``
        :rtype: :class:`UUID`
        """
        return str(uuid.uuid4())

    def list_nodes(self):
        """
        List the nodes known to a particular driver;
        There are two default nodes created at the beginning

        >>> from libcloud.compute.drivers.dummy import DummyNodeDriver
        >>> driver = DummyNodeDriver(0)
        >>> node_list=driver.list_nodes()
        >>> sorted([node.name for node in node_list ])
        ['dummy-1', 'dummy-2']

        each item in the list returned is a node object from which you
        can carry out any node actions you wish

        >>> node_list[0].reboot()
        True

        As more nodes are added, list_nodes will return them

        >>> node=driver.create_node()
        >>> node.size.id
        's1'
        >>> node.image.id
        'i2'
        >>> sorted([n.name for n in driver.list_nodes()])
        ['dummy-1', 'dummy-2', 'dummy-3']

        @inherits: :class:`NodeDriver.list_nodes`
        """
        return self.nl

    def reboot_node(self, node):
        """
        Sets the node state to rebooting; in this dummy driver always
        returns True as if the reboot had been successful.

        >>> from libcloud.compute.drivers.dummy import DummyNodeDriver
        >>> driver = DummyNodeDriver(0)
        >>> node=driver.create_node()
        >>> from libcloud.compute.types import NodeState
        >>> node.state == NodeState.RUNNING
        True
        >>> node.state == NodeState.REBOOTING
        False
        >>> driver.reboot_node(node)
        True
        >>> node.state == NodeState.REBOOTING
        True

        Please note, dummy nodes never recover from the reboot.

        @inherits: :class:`NodeDriver.reboot_node`
        """

        node.state = NodeState.REBOOTING
        return True

    def destroy_node(self, node):
        """
        Sets the node state to terminated and removes it from the node list

        >>> from libcloud.compute.drivers.dummy import DummyNodeDriver
        >>> driver = DummyNodeDriver(0)
        >>> from libcloud.compute.types import NodeState
        >>> node = [node for node in driver.list_nodes() if
        ...         node.name == 'dummy-1'][0]
        >>> node.state == NodeState.RUNNING
        True
        >>> driver.destroy_node(node)
        True
        >>> node.state == NodeState.RUNNING
        False
        >>> [n for n in driver.list_nodes() if n.name == 'dummy-1']
        []

        @inherits: :class:`NodeDriver.destroy_node`
        """

        node.state = NodeState.TERMINATED
        self.nl.remove(node)
        return True

    def list_images(self, location=None):
        """
        Returns a list of images as a cloud provider might have

        >>> from libcloud.compute.drivers.dummy import DummyNodeDriver
        >>> driver = DummyNodeDriver(0)
        >>> sorted([image.name for image in driver.list_images()])
        ['Slackware 4', 'Ubuntu 9.04', 'Ubuntu 9.10']

        @inherits: :class:`NodeDriver.list_images`
        """
        return [
            NodeImage(id=1, name="Ubuntu 9.10", driver=self),
            NodeImage(id=2, name="Ubuntu 9.04", driver=self),
            NodeImage(id=3, name="Slackware 4", driver=self),
        ]

    def list_sizes(self, location=None):
        """
        Returns a list of node sizes as a cloud provider might have

        >>> from libcloud.compute.drivers.dummy import DummyNodeDriver
        >>> driver = DummyNodeDriver(0)
        >>> sorted([size.ram for size in driver.list_sizes()])
        [128, 512, 4096, 8192]

        @inherits: :class:`NodeDriver.list_images`
        """

        return [
            NodeSize(id=1,
                     name="Small",
                     ram=128,
                     disk=4,
                     bandwidth=500,
                     price=4,
                     driver=self),
            NodeSize(id=2,
                     name="Medium",
                     ram=512,
                     disk=16,
                     bandwidth=1500,
                     price=8,
                     driver=self),
            NodeSize(id=3,
                     name="Big",
                     ram=4096,
                     disk=32,
                     bandwidth=2500,
                     price=32,
                     driver=self),
            NodeSize(id=4,
                     name="XXL Big",
                     ram=4096 * 2,
                     disk=32 * 4,
                     bandwidth=2500 * 3,
                     price=32 * 2,
                     driver=self),
        ]

    def list_locations(self):
        """
        Returns a list of locations of nodes

        >>> from libcloud.compute.drivers.dummy import DummyNodeDriver
        >>> driver = DummyNodeDriver(0)
        >>> sorted([loc.name + " in " + loc.country for loc in
        ...         driver.list_locations()])
        ['Island Datacenter in FJ', 'London Loft in GB', "Paul's Room in US"]

        @inherits: :class:`NodeDriver.list_locations`
        """
        return [
            NodeLocation(id=1,
                         name="Paul's Room",
                         country='US',
                         driver=self),
            NodeLocation(id=2,
                         name="London Loft",
                         country='GB',
                         driver=self),
            NodeLocation(id=3,
                         name="Island Datacenter",
                         country='FJ',
                         driver=self),
        ]

    def create_node(self, **kwargs):
        """
        Creates a dummy node; the node id is equal to the number of
        nodes in the node list

        >>> from libcloud.compute.drivers.dummy import DummyNodeDriver
        >>> driver = DummyNodeDriver(0)
        >>> sorted([node.name for node in driver.list_nodes()])
        ['dummy-1', 'dummy-2']
        >>> nodeA = driver.create_node()
        >>> sorted([node.name for node in driver.list_nodes()])
        ['dummy-1', 'dummy-2', 'dummy-3']
        >>> driver.create_node().name
        'dummy-4'
        >>> driver.destroy_node(nodeA)
        True
        >>> sorted([node.name for node in driver.list_nodes()])
        ['dummy-1', 'dummy-2', 'dummy-4']

        @inherits: :class:`NodeDriver.create_node`
        """
        l = len(self.nl) + 1
        n = Node(id=l,
                 name='dummy-%d' % l,
                 state=NodeState.RUNNING,
                 public_ips=['127.0.0.%d' % l],
                 private_ips=[],
                 driver=self,
                 size=NodeSize(id='s1', name='foo', ram=2048,
                               disk=160, bandwidth=None, price=0.0,
                               driver=self),
                 image=NodeImage(id='i2', name='image', driver=self),
                 extra={'foo': 'bar'})
        self.nl.append(n)
        return n

    def import_key_pair_from_string(self, name, key_material):
        key_pair = KeyPair(name=name,
                           public_key=key_material,
                           fingerprint='fingerprint',
                           private_key='private_key',
                           driver=self)
        return key_pair


def _ip_to_int(ip):
    return socket.htonl(struct.unpack('I', socket.inet_aton(ip))[0])


def _int_to_ip(ip):
    return socket.inet_ntoa(struct.pack('I', socket.ntohl(ip)))

if __name__ == "__main__":
    import doctest

    doctest.testmod()
