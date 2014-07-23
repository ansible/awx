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

from libcloud.compute.base import Node, NodeSize, NodeImage, NodeLocation
from libcloud.compute.drivers.voxel import VoxelNodeDriver as Voxel
from libcloud.compute.types import InvalidCredsError

from libcloud.test import MockHttp
from libcloud.test.file_fixtures import ComputeFileFixtures

from libcloud.test.secrets import VOXEL_PARAMS


class VoxelTest(unittest.TestCase):

    def setUp(self):

        Voxel.connectionCls.conn_classes = (None, VoxelMockHttp)
        VoxelMockHttp.type = None
        self.driver = Voxel(*VOXEL_PARAMS)

    def test_auth_failed(self):
        VoxelMockHttp.type = 'UNAUTHORIZED'
        try:
            self.driver.list_nodes()
        except Exception:
            e = sys.exc_info()[1]
            self.assertTrue(isinstance(e, InvalidCredsError))
        else:
            self.fail('test should have thrown')

    def test_response_failure(self):
        VoxelMockHttp.type = 'FAILURE'

        try:
            self.driver.list_nodes()
        except Exception:
            pass
        else:
            self.fail('Invalid response, but exception was not thrown')

    def test_list_nodes(self):
        VoxelMockHttp.type = 'LIST_NODES'
        nodes = self.driver.list_nodes()

        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].name, 'www.voxel.net')

    def test_list_sizes(self):
        sizes = self.driver.list_sizes()

        self.assertEqual(len(sizes), 13)

    def test_list_images(self):
        VoxelMockHttp.type = 'LIST_IMAGES'
        images = self.driver.list_images()

        self.assertEqual(len(images), 1)

    def test_list_locations(self):
        VoxelMockHttp.type = 'LIST_LOCATIONS'
        locations = self.driver.list_locations()

        self.assertEqual(len(locations), 2)
        self.assertEqual(locations[0].name, 'Amsterdam')

    def test_create_node_invalid_disk_size(self):
        image = NodeImage(
            id=1, name='Ubuntu 8.10 (intrepid)', driver=self.driver)
        size = NodeSize(
            1, '256 slice', None, None, None, None, driver=self.driver)
        location = NodeLocation(id=1, name='Europe', country='England',
                                driver=self.driver)

        try:
            self.driver.create_node(name='foo', image=image, size=size,
                                    location=location)
        except ValueError:
            pass
        else:
            self.fail('Invalid disk size provided but an exception was not'
                      ' thrown')

    def test_create_node(self):
        VoxelMockHttp.type = 'CREATE_NODE'
        image = NodeImage(
            id=1, name='Ubuntu 8.10 (intrepid)', driver=self.driver)
        size = NodeSize(
            1, '256 slice', 1024, 500, None, None, driver=self.driver)
        location = NodeLocation(id=1, name='Europe', country='England',
                                driver=self.driver)

        node = self.driver.create_node(name='foo', image=image, size=size,
                                       location=location)
        self.assertEqual(node.id, '1234')

        node = self.driver.create_node(name='foo', image=image, size=size,
                                       location=location, voxel_access=True)
        self.assertEqual(node.id, '1234')

    def test_reboot_node(self):
        VoxelMockHttp.type = 'REBOOT_NODE'
        node = Node(
            id=72258, name=None, state=None, public_ips=None, private_ips=None,
            driver=self.driver)

        self.assertTrue(node.reboot())

    def test_destroy_node(self):
        VoxelMockHttp.type = 'DESTROY_NODE'
        node = Node(
            id=72258, name=None, state=None, public_ips=None, private_ips=None,
            driver=self.driver)

        self.assertTrue(node.destroy())


class VoxelMockHttp(MockHttp):

    fixtures = ComputeFileFixtures('voxel')

    def _UNAUTHORIZED(self, method, url, body, headers):
        body = self.fixtures.load('unauthorized.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _FAILURE(self, method, url, body, headers):
        body = self.fixtures.load('failure.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _LIST_NODES(self, method, url, body, headers):
        body = self.fixtures.load('nodes.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _LIST_IMAGES(self, method, url, body, headers):
        body = self.fixtures.load('images.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _LIST_LOCATIONS(self, method, url, body, headers):
        body = self.fixtures.load('locations.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _CREATE_NODE(self, method, url, body, headers):
        body = self.fixtures.load('create_node.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _REBOOT_NODE(self, method, url, body, headers):
        body = self.fixtures.load('success.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _DESTROY_NODE(self, method, url, body, headers):
        body = self.fixtures.load('success.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

if __name__ == '__main__':
    sys.exit(unittest.main())
