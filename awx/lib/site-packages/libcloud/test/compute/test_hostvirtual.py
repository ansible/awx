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
import sys
import unittest

from libcloud.utils.py3 import httplib

from libcloud.compute.drivers.hostvirtual import HostVirtualNodeDriver
from libcloud.compute.types import NodeState
from libcloud.compute.base import NodeAuthPassword
from libcloud.test import MockHttp
from libcloud.test.file_fixtures import ComputeFileFixtures
from libcloud.test.secrets import HOSTVIRTUAL_PARAMS


class HostVirtualTest(unittest.TestCase):

    def setUp(self):
        HostVirtualNodeDriver.connectionCls.conn_classes = (
            None, HostVirtualMockHttp)
        self.driver = HostVirtualNodeDriver(*HOSTVIRTUAL_PARAMS)

    def test_list_nodes(self):
        nodes = self.driver.list_nodes()
        self.assertEqual(len(nodes), 4)
        self.assertEqual(len(nodes[0].public_ips), 1)
        self.assertEqual(len(nodes[1].public_ips), 1)
        self.assertEqual(len(nodes[0].private_ips), 0)
        self.assertEqual(len(nodes[1].private_ips), 0)
        self.assertTrue('208.111.39.118' in nodes[1].public_ips)
        self.assertTrue('208.111.45.250' in nodes[0].public_ips)
        self.assertEqual(nodes[3].state, NodeState.RUNNING)
        self.assertEqual(nodes[1].state, NodeState.TERMINATED)

    def test_list_sizes(self):
        sizes = self.driver.list_sizes()
        self.assertEqual(len(sizes), 14)
        self.assertEqual(sizes[0].id, '31')
        self.assertEqual(sizes[4].id, '71')
        self.assertEqual(sizes[2].ram, '512MB')
        self.assertEqual(sizes[2].disk, '20GB')
        self.assertEqual(sizes[3].bandwidth, '600GB')
        self.assertEqual(sizes[1].price, '15.00')

    def test_list_images(self):
        images = self.driver.list_images()
        self.assertEqual(len(images), 8)
        self.assertEqual(images[0].id, '1739')
        self.assertEqual(images[0].name, 'Gentoo 2012 (0619) i386')

    def test_list_locations(self):
        locations = self.driver.list_locations()
        self.assertEqual(locations[0].id, '3')
        self.assertEqual(locations[0].name, 'SJC - San Jose, CA')
        self.assertEqual(locations[1].id, '13')
        self.assertEqual(locations[1].name, 'IAD2- Reston, VA')

    def test_reboot_node(self):
        node = self.driver.list_nodes()[0]
        self.assertTrue(self.driver.reboot_node(node))

    def test_ex_get_node(self):
        node = self.driver.ex_get_node(node_id='62291')
        self.assertEqual(node.id, '62291')
        self.assertEqual(node.name, 'server1.vr-cluster.org')
        self.assertEqual(node.state, NodeState.TERMINATED)
        self.assertTrue('208.111.45.250' in node.public_ips)

    def test_ex_stop_node(self):
        node = self.driver.list_nodes()[0]
        self.assertTrue(self.driver.ex_stop_node(node))

    def test_ex_start_node(self):
        node = self.driver.list_nodes()[0]
        self.assertTrue(self.driver.ex_start_node(node))

    def test_destroy_node(self):
        node = self.driver.list_nodes()[0]
        self.assertTrue(self.driver.destroy_node(node))

    def test_ex_delete_node(self):
        node = self.driver.list_nodes()[0]
        self.assertTrue(self.driver.ex_delete_node(node))

    def test_create_node(self):
        auth = NodeAuthPassword('vr!@#hosted#@!')
        size = self.driver.list_sizes()[0]
        image = self.driver.list_images()[0]
        node = self.driver.create_node(
            name='test.com',
            image=image,
            size=size,
            auth=auth
        )
        self.assertEqual('62291', node.id)
        self.assertEqual('server1.vr-cluster.org', node.name)

    def test_ex_provision_node(self):
        node = self.driver.list_nodes()[0]
        auth = NodeAuthPassword('vr!@#hosted#@!')
        self.assertTrue(self.driver.ex_provision_node(
            node=node,
            auth=auth
        ))

    def test_create_node_in_location(self):
        auth = NodeAuthPassword('vr!@#hosted#@!')
        size = self.driver.list_sizes()[0]
        image = self.driver.list_images()[0]
        location = self.driver.list_locations()[1]
        node = self.driver.create_node(
            name='test.com',
            image=image,
            size=size,
            auth=auth,
            location=location
        )
        self.assertEqual('62291', node.id)
        self.assertEqual('server1.vr-cluster.org', node.name)


class HostVirtualMockHttp(MockHttp):
    fixtures = ComputeFileFixtures('hostvirtual')

    def _cloud_servers(self, method, url, body, headers):
        body = self.fixtures.load('list_nodes.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _cloud_server(self, method, url, body, headers):
        body = self.fixtures.load('get_node.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _cloud_sizes(self, method, url, body, headers):
        body = self.fixtures.load('list_sizes.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _cloud_images(self, method, url, body, headers):
        body = self.fixtures.load('list_images.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _cloud_locations(self, method, url, body, headers):
        body = self.fixtures.load('list_locations.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _cloud_cancel(self, method, url, body, headers):
        body = self.fixtures.load('node_destroy.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _cloud_server_reboot(self, method, url, body, headers):
        body = self.fixtures.load('node_reboot.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _cloud_server_shutdown(self, method, url, body, headers):
        body = self.fixtures.load('node_stop.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _cloud_server_start(self, method, url, body, headers):
        body = self.fixtures.load('node_start.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _cloud_buy(self, method, url, body, headers):
        body = self.fixtures.load('create_node.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _cloud_server_build(self, method, url, body, headers):
        body = self.fixtures.load('create_node.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _cloud_server_delete(self, method, url, body, headers):
        body = self.fixtures.load('node_destroy.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

if __name__ == '__main__':
    sys.exit(unittest.main())

# vim:autoindent tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python
