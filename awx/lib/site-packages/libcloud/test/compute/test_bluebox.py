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

from libcloud.compute.drivers.bluebox import BlueboxNodeDriver as Bluebox
from libcloud.compute.base import Node, NodeAuthPassword
from libcloud.compute.types import NodeState


from libcloud.test import MockHttp
from libcloud.test.file_fixtures import ComputeFileFixtures
from libcloud.test.secrets import BLUEBOX_PARAMS


class BlueboxTest(unittest.TestCase):

    def setUp(self):
        Bluebox.connectionCls.conn_classes = (None, BlueboxMockHttp)
        self.driver = Bluebox(*BLUEBOX_PARAMS)

    def test_create_node(self):
        node = self.driver.create_node(
            name='foo',
            size=self.driver.list_sizes()[0],
            image=self.driver.list_images()[0],
            auth=NodeAuthPassword("test123")
        )
        self.assertTrue(isinstance(node, Node))
        self.assertEqual(node.state, NodeState.PENDING)
        self.assertEqual(node.name, 'foo.apitest.blueboxgrid.com')

    def test_list_nodes(self):
        node = self.driver.list_nodes()[0]
        self.assertEqual(node.name, 'foo.apitest.blueboxgrid.com')
        self.assertEqual(node.state, NodeState.RUNNING)

    def test_list_sizes(self):
        sizes = self.driver.list_sizes()
        self.assertEqual(len(sizes), 4)

        ids = [s.id for s in sizes]

        for size in sizes:
            self.assertTrue(size.price > 0)

        self.assertTrue('94fd37a7-2606-47f7-84d5-9000deda52ae' in ids)
        self.assertTrue('b412f354-5056-4bf0-a42f-6ddd998aa092' in ids)
        self.assertTrue('0cd183d3-0287-4b1a-8288-b3ea8302ed58' in ids)
        self.assertTrue('b9b87a5b-2885-4a2e-b434-44a163ca6251' in ids)

    def test_list_images(self):
        images = self.driver.list_images()
        image = images[0]
        self.assertEqual(len(images), 10)
        self.assertEqual(image.name, 'CentOS 5 (Latest Release)')
        self.assertEqual(image.id, 'c66b8145-f768-45ef-9878-395bf8b1b7ff')

    def test_reboot_node(self):
        node = self.driver.list_nodes()[0]
        ret = self.driver.reboot_node(node)
        self.assertTrue(ret)

    def test_destroy_node(self):
        node = self.driver.list_nodes()[0]
        ret = self.driver.destroy_node(node)
        self.assertTrue(ret)


class BlueboxMockHttp(MockHttp):

    fixtures = ComputeFileFixtures('bluebox')

    def _api_blocks_json(self, method, url, body, headers):
        if method == "POST":
            body = self.fixtures.load('api_blocks_json_post.json')
        else:
            body = self.fixtures.load('api_blocks_json.json')
        return (httplib.OK, body, headers, httplib.responses[httplib.OK])

    def _api_block_products_json(self, method, url, body, headers):
        body = self.fixtures.load('api_block_products_json.json')
        return (httplib.OK, body, headers, httplib.responses[httplib.OK])

    def _api_block_templates_json(self, method, url, body, headers):
        body = self.fixtures.load('api_block_templates_json.json')
        return (httplib.OK, body, headers, httplib.responses[httplib.OK])

    def _api_blocks_99df878c_6e5c_4945_a635_d94da9fd3146_json(self, method, url, body, headers):
        if method == 'DELETE':
            body = self.fixtures.load(
                'api_blocks_99df878c_6e5c_4945_a635_d94da9fd3146_json_delete.json')
        else:
            body = self.fixtures.load(
                'api_blocks_99df878c_6e5c_4945_a635_d94da9fd3146_json.json')
        return (httplib.OK, body, headers, httplib.responses[httplib.OK])

    def _api_blocks_99df878c_6e5c_4945_a635_d94da9fd3146_reboot_json(self, method, url, body, headers):
        body = self.fixtures.load(
            'api_blocks_99df878c_6e5c_4945_a635_d94da9fd3146_reboot_json.json')
        return (httplib.OK, body, headers, httplib.responses[httplib.OK])

if __name__ == '__main__':
    sys.exit(unittest.main())
