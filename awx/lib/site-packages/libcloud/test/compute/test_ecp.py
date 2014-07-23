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

from libcloud.compute.drivers.ecp import ECPNodeDriver
from libcloud.compute.types import NodeState

from libcloud.test import MockHttp
from libcloud.test.compute import TestCaseMixin
from libcloud.test.file_fixtures import ComputeFileFixtures

from libcloud.test.secrets import ECP_PARAMS


class ECPTests(unittest.TestCase, TestCaseMixin):

    def setUp(self):
        ECPNodeDriver.connectionCls.conn_classes = (None,
                                                    ECPMockHttp)
        self.driver = ECPNodeDriver(*ECP_PARAMS)

    def test_list_nodes(self):
        nodes = self.driver.list_nodes()
        self.assertEqual(len(nodes), 2)
        node = nodes[0]
        self.assertEqual(node.id, '1')
        self.assertEqual(node.name, 'dummy-1')
        self.assertEqual(node.public_ips[0], "42.78.124.75")
        self.assertEqual(node.state, NodeState.RUNNING)

    def test_list_sizes(self):
        sizes = self.driver.list_sizes()
        self.assertEqual(len(sizes), 3)
        size = sizes[0]
        self.assertEqual(size.id, '1')
        self.assertEqual(size.ram, 512)
        self.assertEqual(size.disk, 0)
        self.assertEqual(size.bandwidth, 0)
        self.assertEqual(size.price, 0)

    def test_list_images(self):
        images = self.driver.list_images()
        self.assertEqual(len(images), 2)
        self.assertEqual(
            images[0].name, "centos54: AUTO import from /opt/enomalism2/repo/5d407a68-c76c-11de-86e5-000475cb7577.xvm2")
        self.assertEqual(images[0].id, "1")

        name = "centos54 two: AUTO import from /opt/enomalism2/repo/5d407a68-c76c-11de-86e5-000475cb7577.xvm2"
        self.assertEqual(images[1].name, name)
        self.assertEqual(images[1].id, "2")

    def test_reboot_node(self):
        # Raises exception on failure
        node = self.driver.list_nodes()[0]
        self.driver.reboot_node(node)

    def test_destroy_node(self):
        # Raises exception on failure
        node = self.driver.list_nodes()[0]
        self.driver.destroy_node(node)

    def test_create_node(self):
        # Raises exception on failure
        size = self.driver.list_sizes()[0]
        image = self.driver.list_images()[0]
        node = self.driver.create_node(
            name="api.ivan.net.nz", image=image, size=size)
        self.assertEqual(node.name, "api.ivan.net.nz")
        self.assertEqual(node.id, "1234")


class ECPMockHttp(MockHttp):

    fixtures = ComputeFileFixtures('ecp')

    def _modules_hosting(self, method, url, body, headers):
        headers = {}
        headers['set-cookie'] = 'vcloud-token=testtoken'
        body = 'Anything'
        return (httplib.OK, body, headers, httplib.responses[httplib.OK])

    def _rest_hosting_vm_1(self, method, url, body, headers):
        if method == 'GET':
            body = self.fixtures.load('vm_1_get.json')
        if method == 'POST':
            if body.find('delete', 0):
                body = self.fixtures.load('vm_1_action_delete.json')
            if body.find('stop', 0):
                body = self.fixtures.load('vm_1_action_stop.json')
            if body.find('start', 0):
                body = self.fixtures.load('vm_1_action_start.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _rest_hosting_vm(self, method, url, body, headers):
        if method == 'PUT':
            body = self.fixtures.load('vm_put.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _rest_hosting_vm_list(self, method, url, body, headers):
        body = self.fixtures.load('vm_list.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _rest_hosting_htemplate_list(self, method, url, body, headers):
        body = self.fixtures.load('htemplate_list.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _rest_hosting_network_list(self, method, url, body, headers):
        body = self.fixtures.load('network_list.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _rest_hosting_ptemplate_list(self, method, url, body, headers):
        body = self.fixtures.load('ptemplate_list.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])


if __name__ == '__main__':
    sys.exit(unittest.main())
