# Copyright 2002-2009, Distributed Systems Architecture Group, Universidad
# Complutense de Madrid (dsa-research.org)
#
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
OpenNebula.org test suite.
"""

__docformat__ = 'epytext'

import unittest
import sys

from libcloud.utils.py3 import httplib

from libcloud.compute.base import Node, NodeImage, NodeSize, NodeState
from libcloud.compute.drivers.opennebula import OpenNebulaNodeDriver
from libcloud.compute.drivers.opennebula import OpenNebulaNetwork
from libcloud.compute.drivers.opennebula import OpenNebulaResponse
from libcloud.compute.drivers.opennebula import OpenNebulaNodeSize
from libcloud.compute.drivers.opennebula import ACTION

from libcloud.test.file_fixtures import ComputeFileFixtures
from libcloud.common.types import InvalidCredsError
from libcloud.test import MockResponse, MockHttp
from libcloud.test.compute import TestCaseMixin

from libcloud.test.secrets import OPENNEBULA_PARAMS


class OpenNebulaCaseMixin(TestCaseMixin):

    def test_reboot_node_response(self):
        pass


class OpenNebula_ResponseTests(unittest.TestCase):
    XML = """<?xml version="1.0" encoding="UTF-8"?><root/>"""

    def test_unauthorized_response(self):
        http_response = MockResponse(httplib.UNAUTHORIZED,
                                     OpenNebula_ResponseTests.XML,
                                     headers={'content-type':
                                              'application/xml'})
        try:
            OpenNebulaResponse(http_response, None).parse_body()
        except InvalidCredsError:
            exceptionType = sys.exc_info()[0]
            self.assertEqual(exceptionType, type(InvalidCredsError()))


class OpenNebula_1_4_Tests(unittest.TestCase, OpenNebulaCaseMixin):

    """
    OpenNebula.org test suite for OpenNebula v1.4.
    """

    def setUp(self):
        """
        Setup test environment.
        """
        OpenNebulaNodeDriver.connectionCls.conn_classes = (
            OpenNebula_1_4_MockHttp, OpenNebula_1_4_MockHttp)
        self.driver = OpenNebulaNodeDriver(*OPENNEBULA_PARAMS + ('1.4',))

    def test_create_node(self):
        """
        Test create_node functionality.
        """
        image = NodeImage(id=5, name='Ubuntu 9.04 LAMP', driver=self.driver)
        size = NodeSize(id=1, name='small', ram=None, disk=None,
                        bandwidth=None, price=None, driver=self.driver)
        networks = list()
        networks.append(OpenNebulaNetwork(id=5, name='Network 5',
                        address='192.168.0.0', size=256, driver=self.driver))
        networks.append(OpenNebulaNetwork(id=15, name='Network 15',
                        address='192.168.1.0', size=256, driver=self.driver))

        node = self.driver.create_node(name='Compute 5', image=image,
                                       size=size, networks=networks)

        self.assertEqual(node.id, '5')
        self.assertEqual(node.name, 'Compute 5')
        self.assertEqual(node.state,
                         OpenNebulaNodeDriver.NODE_STATE_MAP['ACTIVE'])
        self.assertEqual(node.public_ips[0].name, None)
        self.assertEqual(node.public_ips[0].id, '5')
        self.assertEqual(node.public_ips[0].address, '192.168.0.1')
        self.assertEqual(node.public_ips[0].size, 1)
        self.assertEqual(node.public_ips[1].name, None)
        self.assertEqual(node.public_ips[1].id, '15')
        self.assertEqual(node.public_ips[1].address, '192.168.1.1')
        self.assertEqual(node.public_ips[1].size, 1)
        self.assertEqual(node.private_ips, [])
        self.assertEqual(node.image.id, '5')
        self.assertEqual(node.image.extra['dev'], 'sda1')

    def test_destroy_node(self):
        """
        Test destroy_node functionality.
        """
        node = Node(5, None, None, None, None, self.driver)
        ret = self.driver.destroy_node(node)
        self.assertTrue(ret)

    def test_list_nodes(self):
        """
        Test list_nodes functionality.
        """
        nodes = self.driver.list_nodes()

        self.assertEqual(len(nodes), 3)
        node = nodes[0]
        self.assertEqual(node.id, '5')
        self.assertEqual(node.name, 'Compute 5')
        self.assertEqual(node.state,
                         OpenNebulaNodeDriver.NODE_STATE_MAP['ACTIVE'])
        self.assertEqual(node.public_ips[0].id, '5')
        self.assertEqual(node.public_ips[0].name, None)
        self.assertEqual(node.public_ips[0].address, '192.168.0.1')
        self.assertEqual(node.public_ips[0].size, 1)
        self.assertEqual(node.public_ips[1].id, '15')
        self.assertEqual(node.public_ips[1].name, None)
        self.assertEqual(node.public_ips[1].address, '192.168.1.1')
        self.assertEqual(node.public_ips[1].size, 1)
        self.assertEqual(node.private_ips, [])
        self.assertEqual(node.image.id, '5')
        self.assertEqual(node.image.extra['dev'], 'sda1')
        node = nodes[1]
        self.assertEqual(node.id, '15')
        self.assertEqual(node.name, 'Compute 15')
        self.assertEqual(node.state,
                         OpenNebulaNodeDriver.NODE_STATE_MAP['ACTIVE'])
        self.assertEqual(node.public_ips[0].id, '5')
        self.assertEqual(node.public_ips[0].name, None)
        self.assertEqual(node.public_ips[0].address, '192.168.0.2')
        self.assertEqual(node.public_ips[0].size, 1)
        self.assertEqual(node.public_ips[1].id, '15')
        self.assertEqual(node.public_ips[1].name, None)
        self.assertEqual(node.public_ips[1].address, '192.168.1.2')
        self.assertEqual(node.public_ips[1].size, 1)
        self.assertEqual(node.private_ips, [])
        self.assertEqual(node.image.id, '15')
        self.assertEqual(node.image.extra['dev'], 'sda1')
        node = nodes[2]
        self.assertEqual(node.id, '25')
        self.assertEqual(node.name, 'Compute 25')
        self.assertEqual(node.state,
                         NodeState.UNKNOWN)
        self.assertEqual(node.public_ips[0].id, '5')
        self.assertEqual(node.public_ips[0].name, None)
        self.assertEqual(node.public_ips[0].address, '192.168.0.3')
        self.assertEqual(node.public_ips[0].size, 1)
        self.assertEqual(node.public_ips[1].id, '15')
        self.assertEqual(node.public_ips[1].name, None)
        self.assertEqual(node.public_ips[1].address, '192.168.1.3')
        self.assertEqual(node.public_ips[1].size, 1)
        self.assertEqual(node.private_ips, [])
        self.assertEqual(node.image, None)

    def test_list_images(self):
        """
        Test list_images functionality.
        """
        images = self.driver.list_images()

        self.assertEqual(len(images), 2)
        image = images[0]
        self.assertEqual(image.id, '5')
        self.assertEqual(image.name, 'Ubuntu 9.04 LAMP')
        self.assertEqual(image.extra['size'], '2048')
        self.assertEqual(image.extra['url'],
                         'file:///images/ubuntu/jaunty.img')
        image = images[1]
        self.assertEqual(image.id, '15')
        self.assertEqual(image.name, 'Ubuntu 9.04 LAMP')
        self.assertEqual(image.extra['size'], '2048')
        self.assertEqual(image.extra['url'],
                         'file:///images/ubuntu/jaunty.img')

    def test_list_sizes(self):
        """
        Test list_sizes functionality.
        """
        sizes = self.driver.list_sizes()

        self.assertEqual(len(sizes), 3)
        size = sizes[0]
        self.assertEqual(size.id, '1')
        self.assertEqual(size.name, 'small')
        self.assertEqual(size.ram, None)
        self.assertEqual(size.disk, None)
        self.assertEqual(size.bandwidth, None)
        self.assertEqual(size.price, None)
        size = sizes[1]
        self.assertEqual(size.id, '2')
        self.assertEqual(size.name, 'medium')
        self.assertEqual(size.ram, None)
        self.assertEqual(size.disk, None)
        self.assertEqual(size.bandwidth, None)
        self.assertEqual(size.price, None)
        size = sizes[2]
        self.assertEqual(size.id, '3')
        self.assertEqual(size.name, 'large')
        self.assertEqual(size.ram, None)
        self.assertEqual(size.disk, None)
        self.assertEqual(size.bandwidth, None)
        self.assertEqual(size.price, None)

    def test_list_locations(self):
        """
        Test list_locations functionality.
        """
        locations = self.driver.list_locations()

        self.assertEqual(len(locations), 1)
        location = locations[0]
        self.assertEqual(location.id, '0')
        self.assertEqual(location.name, '')
        self.assertEqual(location.country, '')

    def test_ex_list_networks(self):
        """
        Test ex_list_networks functionality.
        """
        networks = self.driver.ex_list_networks()

        self.assertEqual(len(networks), 2)
        network = networks[0]
        self.assertEqual(network.id, '5')
        self.assertEqual(network.name, 'Network 5')
        self.assertEqual(network.address, '192.168.0.0')
        self.assertEqual(network.size, '256')
        network = networks[1]
        self.assertEqual(network.id, '15')
        self.assertEqual(network.name, 'Network 15')
        self.assertEqual(network.address, '192.168.1.0')
        self.assertEqual(network.size, '256')

    def test_ex_node_action(self):
        """
        Test ex_node_action functionality.
        """
        node = Node(5, None, None, None, None, self.driver)
        ret = self.driver.ex_node_action(node, ACTION.STOP)
        self.assertTrue(ret)


class OpenNebula_2_0_Tests(unittest.TestCase, OpenNebulaCaseMixin):

    """
    OpenNebula.org test suite for OpenNebula v2.0 through v2.2.
    """

    def setUp(self):
        """
        Setup test environment.
        """
        OpenNebulaNodeDriver.connectionCls.conn_classes = (
            OpenNebula_2_0_MockHttp, OpenNebula_2_0_MockHttp)
        self.driver = OpenNebulaNodeDriver(*OPENNEBULA_PARAMS + ('2.0',))

    def test_create_node(self):
        """
        Test create_node functionality.
        """
        image = NodeImage(id=5, name='Ubuntu 9.04 LAMP', driver=self.driver)
        size = OpenNebulaNodeSize(id=1, name='small', ram=1024, cpu=1,
                                  disk=None, bandwidth=None, price=None,
                                  driver=self.driver)
        networks = list()
        networks.append(OpenNebulaNetwork(id=5, name='Network 5',
                        address='192.168.0.0', size=256, driver=self.driver))
        networks.append(OpenNebulaNetwork(id=15, name='Network 15',
                        address='192.168.1.0', size=256, driver=self.driver))
        context = {'hostname': 'compute-5'}

        node = self.driver.create_node(name='Compute 5', image=image,
                                       size=size, networks=networks,
                                       context=context)

        self.assertEqual(node.id, '5')
        self.assertEqual(node.name, 'Compute 5')
        self.assertEqual(node.state,
                         OpenNebulaNodeDriver.NODE_STATE_MAP['ACTIVE'])
        self.assertEqual(node.public_ips[0].id, '5')
        self.assertEqual(node.public_ips[0].name, 'Network 5')
        self.assertEqual(node.public_ips[0].address, '192.168.0.1')
        self.assertEqual(node.public_ips[0].size, 1)
        self.assertEqual(node.public_ips[0].extra['mac'], '02:00:c0:a8:00:01')
        self.assertEqual(node.public_ips[1].id, '15')
        self.assertEqual(node.public_ips[1].name, 'Network 15')
        self.assertEqual(node.public_ips[1].address, '192.168.1.1')
        self.assertEqual(node.public_ips[1].size, 1)
        self.assertEqual(node.public_ips[1].extra['mac'], '02:00:c0:a8:01:01')
        self.assertEqual(node.private_ips, [])
        self.assertTrue(len([s for s in self.driver.list_sizes()
                        if s.id == node.size.id]) == 1)
        self.assertEqual(node.image.id, '5')
        self.assertEqual(node.image.name, 'Ubuntu 9.04 LAMP')
        self.assertEqual(node.image.extra['type'], 'DISK')
        self.assertEqual(node.image.extra['target'], 'hda')
        context = node.extra['context']
        self.assertEqual(context['hostname'], 'compute-5')

    def test_destroy_node(self):
        """
        Test destroy_node functionality.
        """
        node = Node(5, None, None, None, None, self.driver)
        ret = self.driver.destroy_node(node)
        self.assertTrue(ret)

    def test_list_nodes(self):
        """
        Test list_nodes functionality.
        """
        nodes = self.driver.list_nodes()

        self.assertEqual(len(nodes), 3)
        node = nodes[0]
        self.assertEqual(node.id, '5')
        self.assertEqual(node.name, 'Compute 5')
        self.assertEqual(node.state,
                         OpenNebulaNodeDriver.NODE_STATE_MAP['ACTIVE'])
        self.assertEqual(node.public_ips[0].id, '5')
        self.assertEqual(node.public_ips[0].name, 'Network 5')
        self.assertEqual(node.public_ips[0].address, '192.168.0.1')
        self.assertEqual(node.public_ips[0].size, 1)
        self.assertEqual(node.public_ips[0].extra['mac'], '02:00:c0:a8:00:01')
        self.assertEqual(node.public_ips[1].id, '15')
        self.assertEqual(node.public_ips[1].name, 'Network 15')
        self.assertEqual(node.public_ips[1].address, '192.168.1.1')
        self.assertEqual(node.public_ips[1].size, 1)
        self.assertEqual(node.public_ips[1].extra['mac'], '02:00:c0:a8:01:01')
        self.assertEqual(node.private_ips, [])
        self.assertTrue(len([size for size in self.driver.list_sizes()
                        if size.id == node.size.id]) == 1)
        self.assertEqual(node.size.id, '1')
        self.assertEqual(node.size.name, 'small')
        self.assertEqual(node.size.ram, 1024)
        self.assertTrue(node.size.cpu is None or isinstance(node.size.cpu,
                                                            int))
        self.assertTrue(node.size.vcpu is None or isinstance(node.size.vcpu,
                                                             int))
        self.assertEqual(node.size.cpu, 1)
        self.assertEqual(node.size.vcpu, None)
        self.assertEqual(node.size.disk, None)
        self.assertEqual(node.size.bandwidth, None)
        self.assertEqual(node.size.price, None)
        self.assertTrue(len([image for image in self.driver.list_images()
                        if image.id == node.image.id]) == 1)
        self.assertEqual(node.image.id, '5')
        self.assertEqual(node.image.name, 'Ubuntu 9.04 LAMP')
        self.assertEqual(node.image.extra['type'], 'DISK')
        self.assertEqual(node.image.extra['target'], 'hda')
        context = node.extra['context']
        self.assertEqual(context['hostname'], 'compute-5')
        node = nodes[1]
        self.assertEqual(node.id, '15')
        self.assertEqual(node.name, 'Compute 15')
        self.assertEqual(node.state,
                         OpenNebulaNodeDriver.NODE_STATE_MAP['ACTIVE'])
        self.assertEqual(node.public_ips[0].id, '5')
        self.assertEqual(node.public_ips[0].name, 'Network 5')
        self.assertEqual(node.public_ips[0].address, '192.168.0.2')
        self.assertEqual(node.public_ips[0].size, 1)
        self.assertEqual(node.public_ips[0].extra['mac'], '02:00:c0:a8:00:02')
        self.assertEqual(node.public_ips[1].id, '15')
        self.assertEqual(node.public_ips[1].name, 'Network 15')
        self.assertEqual(node.public_ips[1].address, '192.168.1.2')
        self.assertEqual(node.public_ips[1].size, 1)
        self.assertEqual(node.public_ips[1].extra['mac'], '02:00:c0:a8:01:02')
        self.assertEqual(node.private_ips, [])
        self.assertTrue(len([size for size in self.driver.list_sizes()
                        if size.id == node.size.id]) == 1)
        self.assertEqual(node.size.id, '1')
        self.assertEqual(node.size.name, 'small')
        self.assertEqual(node.size.ram, 1024)
        self.assertTrue(node.size.cpu is None or isinstance(node.size.cpu,
                                                            int))
        self.assertTrue(node.size.vcpu is None or isinstance(node.size.vcpu,
                                                             int))
        self.assertEqual(node.size.cpu, 1)
        self.assertEqual(node.size.vcpu, None)
        self.assertEqual(node.size.disk, None)
        self.assertEqual(node.size.bandwidth, None)
        self.assertEqual(node.size.price, None)
        self.assertTrue(len([image for image in self.driver.list_images()
                        if image.id == node.image.id]) == 1)
        self.assertEqual(node.image.id, '15')
        self.assertEqual(node.image.name, 'Ubuntu 9.04 LAMP')
        self.assertEqual(node.image.extra['type'], 'DISK')
        self.assertEqual(node.image.extra['target'], 'hda')
        context = node.extra['context']
        self.assertEqual(context['hostname'], 'compute-15')
        node = nodes[2]
        self.assertEqual(node.id, '25')
        self.assertEqual(node.name, 'Compute 25')
        self.assertEqual(node.state,
                         NodeState.UNKNOWN)
        self.assertEqual(node.public_ips[0].id, '5')
        self.assertEqual(node.public_ips[0].name, 'Network 5')
        self.assertEqual(node.public_ips[0].address, '192.168.0.3')
        self.assertEqual(node.public_ips[0].size, 1)
        self.assertEqual(node.public_ips[0].extra['mac'], '02:00:c0:a8:00:03')
        self.assertEqual(node.public_ips[1].id, '15')
        self.assertEqual(node.public_ips[1].name, 'Network 15')
        self.assertEqual(node.public_ips[1].address, '192.168.1.3')
        self.assertEqual(node.public_ips[1].size, 1)
        self.assertEqual(node.public_ips[1].extra['mac'], '02:00:c0:a8:01:03')
        self.assertEqual(node.private_ips, [])
        self.assertEqual(node.size, None)
        self.assertEqual(node.image, None)
        context = node.extra['context']
        self.assertEqual(context, {})

    def test_list_images(self):
        """
        Test list_images functionality.
        """
        images = self.driver.list_images()

        self.assertEqual(len(images), 2)
        image = images[0]
        self.assertEqual(image.id, '5')
        self.assertEqual(image.name, 'Ubuntu 9.04 LAMP')
        self.assertEqual(image.extra['description'],
                         'Ubuntu 9.04 LAMP Description')
        self.assertEqual(image.extra['type'], 'OS')
        self.assertEqual(image.extra['size'], '2048')
        image = images[1]
        self.assertEqual(image.id, '15')
        self.assertEqual(image.name, 'Ubuntu 9.04 LAMP')
        self.assertEqual(image.extra['description'],
                         'Ubuntu 9.04 LAMP Description')
        self.assertEqual(image.extra['type'], 'OS')
        self.assertEqual(image.extra['size'], '2048')

    def test_list_sizes(self):
        """
        Test list_sizes functionality.
        """
        sizes = self.driver.list_sizes()

        self.assertEqual(len(sizes), 4)
        size = sizes[0]
        self.assertEqual(size.id, '1')
        self.assertEqual(size.name, 'small')
        self.assertEqual(size.ram, 1024)
        self.assertTrue(size.cpu is None or isinstance(size.cpu, int))
        self.assertTrue(size.vcpu is None or isinstance(size.vcpu, int))
        self.assertEqual(size.cpu, 1)
        self.assertEqual(size.vcpu, None)
        self.assertEqual(size.disk, None)
        self.assertEqual(size.bandwidth, None)
        self.assertEqual(size.price, None)
        size = sizes[1]
        self.assertEqual(size.id, '2')
        self.assertEqual(size.name, 'medium')
        self.assertEqual(size.ram, 4096)
        self.assertTrue(size.cpu is None or isinstance(size.cpu, int))
        self.assertTrue(size.vcpu is None or isinstance(size.vcpu, int))
        self.assertEqual(size.cpu, 4)
        self.assertEqual(size.vcpu, None)
        self.assertEqual(size.disk, None)
        self.assertEqual(size.bandwidth, None)
        self.assertEqual(size.price, None)
        size = sizes[2]
        self.assertEqual(size.id, '3')
        self.assertEqual(size.name, 'large')
        self.assertEqual(size.ram, 8192)
        self.assertTrue(size.cpu is None or isinstance(size.cpu, int))
        self.assertTrue(size.vcpu is None or isinstance(size.vcpu, int))
        self.assertEqual(size.cpu, 8)
        self.assertEqual(size.vcpu, None)
        self.assertEqual(size.disk, None)
        self.assertEqual(size.bandwidth, None)
        self.assertEqual(size.price, None)
        size = sizes[3]
        self.assertEqual(size.id, '4')
        self.assertEqual(size.name, 'custom')
        self.assertEqual(size.ram, 0)
        self.assertEqual(size.cpu, 0)
        self.assertEqual(size.vcpu, None)
        self.assertEqual(size.disk, None)
        self.assertEqual(size.bandwidth, None)
        self.assertEqual(size.price, None)

    def test_list_locations(self):
        """
        Test list_locations functionality.
        """
        locations = self.driver.list_locations()

        self.assertEqual(len(locations), 1)
        location = locations[0]
        self.assertEqual(location.id, '0')
        self.assertEqual(location.name, '')
        self.assertEqual(location.country, '')

    def test_ex_list_networks(self):
        """
        Test ex_list_networks functionality.
        """
        networks = self.driver.ex_list_networks()

        self.assertEqual(len(networks), 2)
        network = networks[0]
        self.assertEqual(network.id, '5')
        self.assertEqual(network.name, 'Network 5')
        self.assertEqual(network.address, '192.168.0.0')
        self.assertEqual(network.size, '256')
        network = networks[1]
        self.assertEqual(network.id, '15')
        self.assertEqual(network.name, 'Network 15')
        self.assertEqual(network.address, '192.168.1.0')
        self.assertEqual(network.size, '256')


class OpenNebula_3_0_Tests(unittest.TestCase, OpenNebulaCaseMixin):

    """
    OpenNebula.org test suite for OpenNebula v3.0.
    """

    def setUp(self):
        """
        Setup test environment.
        """
        OpenNebulaNodeDriver.connectionCls.conn_classes = (
            OpenNebula_3_0_MockHttp, OpenNebula_3_0_MockHttp)
        self.driver = OpenNebulaNodeDriver(*OPENNEBULA_PARAMS + ('3.0',))

    def test_ex_list_networks(self):
        """
        Test ex_list_networks functionality.
        """
        networks = self.driver.ex_list_networks()

        self.assertEqual(len(networks), 2)
        network = networks[0]
        self.assertEqual(network.id, '5')
        self.assertEqual(network.name, 'Network 5')
        self.assertEqual(network.address, '192.168.0.0')
        self.assertEqual(network.size, '256')
        self.assertEqual(network.extra['public'], 'YES')
        network = networks[1]
        self.assertEqual(network.id, '15')
        self.assertEqual(network.name, 'Network 15')
        self.assertEqual(network.address, '192.168.1.0')
        self.assertEqual(network.size, '256')
        self.assertEqual(network.extra['public'], 'NO')

    def test_ex_node_set_save_name(self):
        """
        Test ex_node_action functionality.
        """
        image = NodeImage(id=5, name='Ubuntu 9.04 LAMP', driver=self.driver)
        node = Node(5, None, None, None, None, self.driver, image=image)
        ret = self.driver.ex_node_set_save_name(node, 'test')
        self.assertTrue(ret)


class OpenNebula_3_2_Tests(unittest.TestCase, OpenNebulaCaseMixin):

    """
    OpenNebula.org test suite for OpenNebula v3.2.
    """

    def setUp(self):
        """
        Setup test environment.
        """
        OpenNebulaNodeDriver.connectionCls.conn_classes = (
            OpenNebula_3_2_MockHttp, OpenNebula_3_2_MockHttp)
        self.driver = OpenNebulaNodeDriver(*OPENNEBULA_PARAMS + ('3.2',))

    def test_reboot_node(self):
        """
        Test reboot_node functionality.
        """
        image = NodeImage(id=5, name='Ubuntu 9.04 LAMP', driver=self.driver)
        node = Node(5, None, None, None, None, self.driver, image=image)
        ret = self.driver.reboot_node(node)
        self.assertTrue(ret)

    def test_list_sizes(self):
        """
        Test ex_list_networks functionality.
        """
        sizes = self.driver.list_sizes()

        self.assertEqual(len(sizes), 3)
        size = sizes[0]
        self.assertEqual(size.id, '1')
        self.assertEqual(size.name, 'small')
        self.assertEqual(size.ram, 1024)
        self.assertTrue(size.cpu is None or isinstance(size.cpu, float))
        self.assertTrue(size.vcpu is None or isinstance(size.vcpu, int))
        self.assertEqual(size.cpu, 1)
        self.assertEqual(size.vcpu, None)
        self.assertEqual(size.disk, None)
        self.assertEqual(size.bandwidth, None)
        self.assertEqual(size.price, None)
        size = sizes[1]
        self.assertEqual(size.id, '2')
        self.assertEqual(size.name, 'medium')
        self.assertEqual(size.ram, 4096)
        self.assertTrue(size.cpu is None or isinstance(size.cpu, float))
        self.assertTrue(size.vcpu is None or isinstance(size.vcpu, int))
        self.assertEqual(size.cpu, 4)
        self.assertEqual(size.vcpu, None)
        self.assertEqual(size.disk, None)
        self.assertEqual(size.bandwidth, None)
        self.assertEqual(size.price, None)
        size = sizes[2]
        self.assertEqual(size.id, '3')
        self.assertEqual(size.name, 'large')
        self.assertEqual(size.ram, 8192)
        self.assertTrue(size.cpu is None or isinstance(size.cpu, float))
        self.assertTrue(size.vcpu is None or isinstance(size.vcpu, int))
        self.assertEqual(size.cpu, 8)
        self.assertEqual(size.vcpu, None)
        self.assertEqual(size.disk, None)
        self.assertEqual(size.bandwidth, None)
        self.assertEqual(size.price, None)


class OpenNebula_3_6_Tests(unittest.TestCase, OpenNebulaCaseMixin):

    """
    OpenNebula.org test suite for OpenNebula v3.6.
    """

    def setUp(self):
        """
        Setup test environment.
        """
        OpenNebulaNodeDriver.connectionCls.conn_classes = (
            OpenNebula_3_6_MockHttp, OpenNebula_3_6_MockHttp)
        self.driver = OpenNebulaNodeDriver(*OPENNEBULA_PARAMS + ('3.6',))

    def test_create_volume(self):
        new_volume = self.driver.create_volume(1000, 'test-volume')

        self.assertEqual(new_volume.id, '5')
        self.assertEqual(new_volume.size, 1000)
        self.assertEqual(new_volume.name, 'test-volume')

    def test_destroy_volume(self):
        images = self.driver.list_images()

        self.assertEqual(len(images), 2)
        image = images[0]

        ret = self.driver.destroy_volume(image)
        self.assertTrue(ret)

    def test_attach_volume(self):
        nodes = self.driver.list_nodes()
        node = nodes[0]

        images = self.driver.list_images()
        image = images[0]

        ret = self.driver.attach_volume(node, image, 'sda')
        self.assertTrue(ret)

    def test_detach_volume(self):
        images = self.driver.list_images()
        image = images[1]

        ret = self.driver.detach_volume(image)
        self.assertTrue(ret)

        nodes = self.driver.list_nodes()
        # node with only a single associated image
        node = nodes[1]

        ret = self.driver.detach_volume(node.image)
        self.assertFalse(ret)

    def test_list_volumes(self):
        volumes = self.driver.list_volumes()

        self.assertEqual(len(volumes), 2)

        volume = volumes[0]
        self.assertEqual(volume.id, '5')
        self.assertEqual(volume.size, 2048)
        self.assertEqual(volume.name, 'Ubuntu 9.04 LAMP')

        volume = volumes[1]
        self.assertEqual(volume.id, '15')
        self.assertEqual(volume.size, 1024)
        self.assertEqual(volume.name, 'Debian Sid')


class OpenNebula_3_8_Tests(unittest.TestCase, OpenNebulaCaseMixin):

    """
    OpenNebula.org test suite for OpenNebula v3.8.
    """

    def setUp(self):
        """
        Setup test environment.
        """
        OpenNebulaNodeDriver.connectionCls.conn_classes = (
            OpenNebula_3_8_MockHttp, OpenNebula_3_8_MockHttp)
        self.driver = OpenNebulaNodeDriver(*OPENNEBULA_PARAMS + ('3.8',))

    def test_list_sizes(self):
        """
        Test ex_list_networks functionality.
        """
        sizes = self.driver.list_sizes()

        self.assertEqual(len(sizes), 3)
        size = sizes[0]
        self.assertEqual(size.id, '1')
        self.assertEqual(size.name, 'small')
        self.assertEqual(size.ram, 1024)
        self.assertEqual(size.cpu, 1)
        self.assertEqual(size.vcpu, None)
        self.assertEqual(size.disk, None)
        self.assertEqual(size.bandwidth, None)
        self.assertEqual(size.price, None)

        size = sizes[1]
        self.assertEqual(size.id, '2')
        self.assertEqual(size.name, 'medium')
        self.assertEqual(size.ram, 4096)
        self.assertEqual(size.cpu, 4)
        self.assertEqual(size.vcpu, None)
        self.assertEqual(size.disk, None)
        self.assertEqual(size.bandwidth, None)
        self.assertEqual(size.price, None)

        size = sizes[2]
        self.assertEqual(size.id, '3')
        self.assertEqual(size.name, 'large')
        self.assertEqual(size.ram, 8192)
        self.assertEqual(size.cpu, 8)
        self.assertEqual(size.vcpu, None)
        self.assertEqual(size.disk, None)
        self.assertEqual(size.bandwidth, None)
        self.assertEqual(size.price, None)


class OpenNebula_1_4_MockHttp(MockHttp):

    """
    Mock HTTP server for testing v1.4 of the OpenNebula.org compute driver.
    """

    fixtures = ComputeFileFixtures('opennebula_1_4')

    def _compute(self, method, url, body, headers):
        """
        Compute pool resources.
        """
        if method == 'GET':
            body = self.fixtures.load('computes.xml')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        if method == 'POST':
            body = self.fixtures.load('compute_5.xml')
            return (httplib.CREATED, body, {},
                    httplib.responses[httplib.CREATED])

    def _storage(self, method, url, body, headers):
        """
        Storage pool resources.
        """
        if method == 'GET':
            body = self.fixtures.load('storage.xml')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        if method == 'POST':
            body = self.fixtures.load('disk_5.xml')
            return (httplib.CREATED, body, {},
                    httplib.responses[httplib.CREATED])

    def _network(self, method, url, body, headers):
        """
        Network pool resources.
        """
        if method == 'GET':
            body = self.fixtures.load('networks.xml')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        if method == 'POST':
            body = self.fixtures.load('network_5.xml')
            return (httplib.CREATED, body, {},
                    httplib.responses[httplib.CREATED])

    def _compute_5(self, method, url, body, headers):
        """
        Compute entry resource.
        """
        if method == 'GET':
            body = self.fixtures.load('compute_5.xml')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        if method == 'PUT':
            body = ""
            return (httplib.ACCEPTED, body, {},
                    httplib.responses[httplib.ACCEPTED])

        if method == 'DELETE':
            body = ""
            return (httplib.OK, body, {},
                    httplib.responses[httplib.OK])

    def _compute_15(self, method, url, body, headers):
        """
        Compute entry resource.
        """
        if method == 'GET':
            body = self.fixtures.load('compute_15.xml')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        if method == 'PUT':
            body = ""
            return (httplib.ACCEPTED, body, {},
                    httplib.responses[httplib.ACCEPTED])

        if method == 'DELETE':
            body = ""
            return (httplib.OK, body, {},
                    httplib.responses[httplib.OK])

    def _compute_25(self, method, url, body, headers):
        """
        Compute entry resource.
        """
        if method == 'GET':
            body = self.fixtures.load('compute_25.xml')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        if method == 'PUT':
            body = ""
            return (httplib.ACCEPTED, body, {},
                    httplib.responses[httplib.ACCEPTED])

        if method == 'DELETE':
            body = ""
            return (httplib.OK, body, {},
                    httplib.responses[httplib.OK])

    def _storage_5(self, method, url, body, headers):
        """
        Storage entry resource.
        """
        if method == 'GET':
            body = self.fixtures.load('disk_5.xml')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        if method == 'DELETE':
            body = ""
            return (httplib.OK, body, {},
                    httplib.responses[httplib.OK])

    def _storage_15(self, method, url, body, headers):
        """
        Storage entry resource.
        """
        if method == 'GET':
            body = self.fixtures.load('disk_15.xml')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        if method == 'DELETE':
            body = ""
            return (httplib.OK, body, {},
                    httplib.responses[httplib.OK])

    def _network_5(self, method, url, body, headers):
        """
        Network entry resource.
        """
        if method == 'GET':
            body = self.fixtures.load('network_5.xml')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        if method == 'DELETE':
            body = ""
            return (httplib.OK, body, {},
                    httplib.responses[httplib.OK])

    def _network_15(self, method, url, body, headers):
        """
        Network entry resource.
        """
        if method == 'GET':
            body = self.fixtures.load('network_15.xml')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        if method == 'DELETE':
            body = ""
            return (httplib.OK, body, {},
                    httplib.responses[httplib.OK])


class OpenNebula_2_0_MockHttp(MockHttp):

    """
    Mock HTTP server for testing v2.0 through v3.2 of the OpenNebula.org
    compute driver.
    """

    fixtures = ComputeFileFixtures('opennebula_2_0')

    def _compute(self, method, url, body, headers):
        """
        Compute pool resources.
        """
        if method == 'GET':
            body = self.fixtures.load('compute_collection.xml')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        if method == 'POST':
            body = self.fixtures.load('compute_5.xml')
            return (httplib.CREATED, body, {},
                    httplib.responses[httplib.CREATED])

    def _storage(self, method, url, body, headers):
        """
        Storage pool resources.
        """
        if method == 'GET':
            body = self.fixtures.load('storage_collection.xml')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        if method == 'POST':
            body = self.fixtures.load('storage_5.xml')
            return (httplib.CREATED, body, {},
                    httplib.responses[httplib.CREATED])

    def _network(self, method, url, body, headers):
        """
        Network pool resources.
        """
        if method == 'GET':
            body = self.fixtures.load('network_collection.xml')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        if method == 'POST':
            body = self.fixtures.load('network_5.xml')
            return (httplib.CREATED, body, {},
                    httplib.responses[httplib.CREATED])

    def _compute_5(self, method, url, body, headers):
        """
        Compute entry resource.
        """
        if method == 'GET':
            body = self.fixtures.load('compute_5.xml')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        if method == 'PUT':
            body = ""
            return (httplib.ACCEPTED, body, {},
                    httplib.responses[httplib.ACCEPTED])

        if method == 'DELETE':
            body = ""
            return (httplib.NO_CONTENT, body, {},
                    httplib.responses[httplib.NO_CONTENT])

    def _compute_15(self, method, url, body, headers):
        """
        Compute entry resource.
        """
        if method == 'GET':
            body = self.fixtures.load('compute_15.xml')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        if method == 'PUT':
            body = ""
            return (httplib.ACCEPTED, body, {},
                    httplib.responses[httplib.ACCEPTED])

        if method == 'DELETE':
            body = ""
            return (httplib.NO_CONTENT, body, {},
                    httplib.responses[httplib.NO_CONTENT])

    def _compute_25(self, method, url, body, headers):
        """
        Compute entry resource.
        """
        if method == 'GET':
            body = self.fixtures.load('compute_25.xml')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        if method == 'PUT':
            body = ""
            return (httplib.ACCEPTED, body, {},
                    httplib.responses[httplib.ACCEPTED])

        if method == 'DELETE':
            body = ""
            return (httplib.NO_CONTENT, body, {},
                    httplib.responses[httplib.NO_CONTENT])

    def _storage_5(self, method, url, body, headers):
        """
        Storage entry resource.
        """
        if method == 'GET':
            body = self.fixtures.load('storage_5.xml')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        if method == 'DELETE':
            body = ""
            return (httplib.NO_CONTENT, body, {},
                    httplib.responses[httplib.NO_CONTENT])

    def _storage_15(self, method, url, body, headers):
        """
        Storage entry resource.
        """
        if method == 'GET':
            body = self.fixtures.load('storage_15.xml')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        if method == 'DELETE':
            body = ""
            return (httplib.NO_CONTENT, body, {},
                    httplib.responses[httplib.NO_CONTENT])

    def _network_5(self, method, url, body, headers):
        """
        Network entry resource.
        """
        if method == 'GET':
            body = self.fixtures.load('network_5.xml')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        if method == 'DELETE':
            body = ""
            return (httplib.NO_CONTENT, body, {},
                    httplib.responses[httplib.NO_CONTENT])

    def _network_15(self, method, url, body, headers):
        """
        Network entry resource.
        """
        if method == 'GET':
            body = self.fixtures.load('network_15.xml')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        if method == 'DELETE':
            body = ""
            return (httplib.NO_CONTENT, body, {},
                    httplib.responses[httplib.NO_CONTENT])


class OpenNebula_3_0_MockHttp(OpenNebula_2_0_MockHttp):

    """
    Mock HTTP server for testing v3.0 of the OpenNebula.org compute driver.
    """

    fixtures_3_0 = ComputeFileFixtures('opennebula_3_0')

    def _network(self, method, url, body, headers):
        """
        Network pool resources.
        """
        if method == 'GET':
            body = self.fixtures_3_0.load('network_collection.xml')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        if method == 'POST':
            body = self.fixtures.load('network_5.xml')
            return (httplib.CREATED, body, {},
                    httplib.responses[httplib.CREATED])

    def _network_5(self, method, url, body, headers):
        """
        Network entry resource.
        """
        if method == 'GET':
            body = self.fixtures_3_0.load('network_5.xml')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        if method == 'DELETE':
            body = ""
            return (httplib.NO_CONTENT, body, {},
                    httplib.responses[httplib.NO_CONTENT])

    def _network_15(self, method, url, body, headers):
        """
        Network entry resource.
        """
        if method == 'GET':
            body = self.fixtures_3_0.load('network_15.xml')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        if method == 'DELETE':
            body = ""
            return (httplib.NO_CONTENT, body, {},
                    httplib.responses[httplib.NO_CONTENT])


class OpenNebula_3_2_MockHttp(OpenNebula_3_0_MockHttp):

    """
    Mock HTTP server for testing v3.2 of the OpenNebula.org compute driver.
    """

    fixtures_3_2 = ComputeFileFixtures('opennebula_3_2')

    def _compute_5(self, method, url, body, headers):
        """
        Compute entry resource.
        """
        if method == 'GET':
            body = self.fixtures.load('compute_5.xml')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        if method == 'PUT':
            body = ""
            return (httplib.ACCEPTED, body, {},
                    httplib.responses[httplib.ACCEPTED])

        if method == 'DELETE':
            body = ""
            return (httplib.NO_CONTENT, body, {},
                    httplib.responses[httplib.NO_CONTENT])

    def _instance_type(self, method, url, body, headers):
        """
        Instance type pool.
        """
        if method == 'GET':
            body = self.fixtures_3_2.load('instance_type_collection.xml')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])


class OpenNebula_3_6_MockHttp(OpenNebula_3_2_MockHttp):

    """
    Mock HTTP server for testing v3.6 of the OpenNebula.org compute driver.
    """

    fixtures_3_6 = ComputeFileFixtures('opennebula_3_6')

    def _storage(self, method, url, body, headers):
        if method == 'GET':
            body = self.fixtures.load('storage_collection.xml')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        if method == 'POST':
            body = self.fixtures_3_6.load('storage_5.xml')
            return (httplib.CREATED, body, {},
                    httplib.responses[httplib.CREATED])

    def _compute_5(self, method, url, body, headers):
        if method == 'GET':
            body = self.fixtures_3_6.load('compute_5.xml')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        if method == 'PUT':
            body = ""
            return (httplib.ACCEPTED, body, {},
                    httplib.responses[httplib.ACCEPTED])

        if method == 'DELETE':
            body = ""
            return (httplib.NO_CONTENT, body, {},
                    httplib.responses[httplib.NO_CONTENT])

    def _compute_5_action(self, method, url, body, headers):
        body = self.fixtures_3_6.load('compute_5.xml')
        if method == 'POST':
            return (httplib.ACCEPTED, body, {},
                    httplib.responses[httplib.ACCEPTED])

        if method == 'GET':
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _compute_15(self, method, url, body, headers):
        if method == 'GET':
            body = self.fixtures_3_6.load('compute_15.xml')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        if method == 'PUT':
            body = ""
            return (httplib.ACCEPTED, body, {},
                    httplib.responses[httplib.ACCEPTED])

        if method == 'DELETE':
            body = ""
            return (httplib.NO_CONTENT, body, {},
                    httplib.responses[httplib.NO_CONTENT])

    def _storage_10(self, method, url, body, headers):
        """
        Storage entry resource.
        """
        if method == 'GET':
            body = self.fixtures_3_6.load('disk_10.xml')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _storage_15(self, method, url, body, headers):
        """
        Storage entry resource.
        """
        if method == 'GET':
            body = self.fixtures_3_6.load('disk_15.xml')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])


class OpenNebula_3_8_MockHttp(OpenNebula_3_2_MockHttp):

    """
    Mock HTTP server for testing v3.8 of the OpenNebula.org compute driver.
    """

    fixtures_3_8 = ComputeFileFixtures('opennebula_3_8')

    def _instance_type(self, method, url, body, headers):
        """
        Instance type pool.
        """
        if method == 'GET':
            body = self.fixtures_3_8.load('instance_type_collection.xml')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _instance_type_small(self, method, url, body, headers):
        """
        Small instance type.
        """
        if method == 'GET':
            body = self.fixtures_3_8.load('instance_type_small.xml')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _instance_type_medium(self, method, url, body, headers):
        """
        Medium instance type pool.
        """
        if method == 'GET':
            body = self.fixtures_3_8.load('instance_type_medium.xml')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _instance_type_large(self, method, url, body, headers):
        """
        Large instance type pool.
        """
        if method == 'GET':
            body = self.fixtures_3_8.load('instance_type_large.xml')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

if __name__ == '__main__':
    sys.exit(unittest.main())
