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

from libcloud.compute.drivers.vpsnet import VPSNetNodeDriver
from libcloud.compute.base import Node
from libcloud.compute.types import NodeState

from libcloud.test import MockHttp
from libcloud.test.compute import TestCaseMixin

from libcloud.test.secrets import VPSNET_PARAMS
from libcloud.test.file_fixtures import ComputeFileFixtures


class VPSNetTests(unittest.TestCase, TestCaseMixin):

    def setUp(self):
        VPSNetNodeDriver.connectionCls.conn_classes = (None, VPSNetMockHttp)
        self.driver = VPSNetNodeDriver(*VPSNET_PARAMS)

    def test_create_node(self):
        VPSNetMockHttp.type = 'create'
        image = self.driver.list_images()[0]
        size = self.driver.list_sizes()[0]
        node = self.driver.create_node('foo', image, size)
        self.assertEqual(node.name, 'foo')

    def test_list_nodes(self):
        VPSNetMockHttp.type = 'virtual_machines'
        node = self.driver.list_nodes()[0]
        self.assertEqual(node.id, '1384')
        self.assertEqual(node.state, NodeState.RUNNING)

    def test_reboot_node(self):
        VPSNetMockHttp.type = 'virtual_machines'
        node = self.driver.list_nodes()[0]

        VPSNetMockHttp.type = 'reboot'
        ret = self.driver.reboot_node(node)
        self.assertEqual(ret, True)

    def test_destroy_node(self):
        VPSNetMockHttp.type = 'delete'
        node = Node('2222', None, None, None, None, self.driver)
        ret = self.driver.destroy_node(node)
        self.assertTrue(ret)
        VPSNetMockHttp.type = 'delete_fail'
        node = Node('2223', None, None, None, None, self.driver)
        self.assertRaises(Exception, self.driver.destroy_node, node)

    def test_list_images(self):
        VPSNetMockHttp.type = 'templates'
        ret = self.driver.list_images()
        self.assertEqual(ret[0].id, '9')
        self.assertEqual(ret[-1].id, '160')

    def test_list_sizes(self):
        VPSNetMockHttp.type = 'sizes'
        ret = self.driver.list_sizes()
        self.assertEqual(len(ret), 1)
        self.assertEqual(ret[0].id, '1')
        self.assertEqual(ret[0].name, '1 Node')

    def test_destroy_node_response(self):
        # should return a node object
        node = Node('2222', None, None, None, None, self.driver)
        VPSNetMockHttp.type = 'delete'
        ret = self.driver.destroy_node(node)
        self.assertTrue(isinstance(ret, bool))

    def test_reboot_node_response(self):
        # should return a node object
        VPSNetMockHttp.type = 'virtual_machines'
        node = self.driver.list_nodes()[0]
        VPSNetMockHttp.type = 'reboot'
        ret = self.driver.reboot_node(node)
        self.assertTrue(isinstance(ret, bool))


class VPSNetMockHttp(MockHttp):
    fixtures = ComputeFileFixtures('vpsnet')

    def _nodes_api10json_sizes(self, method, url, body, headers):
        body = """[{"slice":{"virtual_machine_id":8592,"id":12256,"consumer_id":0}},
                   {"slice":{"virtual_machine_id":null,"id":12258,"consumer_id":0}},
                   {"slice":{"virtual_machine_id":null,"id":12434,"consumer_id":0}}]"""
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _nodes_api10json_create(self, method, url, body, headers):
        body = """[{"slice":{"virtual_machine_id":8592,"id":12256,"consumer_id":0}},
                   {"slice":{"virtual_machine_id":null,"id":12258,"consumer_id":0}},
                   {"slice":{"virtual_machine_id":null,"id":12434,"consumer_id":0}}]"""
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _virtual_machines_2222_api10json_delete_fail(self, method, url, body, headers):
        return (httplib.FORBIDDEN, '', {}, httplib.responses[httplib.FORBIDDEN])

    def _virtual_machines_2222_api10json_delete(self, method, url, body, headers):
        return (httplib.OK, '', {}, httplib.responses[httplib.OK])

    def _virtual_machines_1384_reboot_api10json_reboot(self, method, url, body, headers):
        body = """{
              "virtual_machine":
                {
                  "running": true,
                  "updated_at": "2009-05-15T06:55:02-04:00",
                  "power_action_pending": false,
                  "system_template_id": 41,
                  "id": 1384,
                  "cloud_id": 3,
                  "domain_name": "demodomain.com",
                  "hostname": "web01",
                  "consumer_id": 0,
                  "backups_enabled": false,
                  "password": "a8hjsjnbs91",
                  "label": "foo",
                  "slices_count": null,
                  "created_at": "2009-04-16T08:17:39-04:00"
                }
              }"""
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _virtual_machines_api10json_create(self, method, url, body, headers):
        body = """{
              "virtual_machine":
                {
                  "running": true,
                  "updated_at": "2009-05-15T06:55:02-04:00",
                  "power_action_pending": false,
                  "system_template_id": 41,
                  "id": 1384,
                  "cloud_id": 3,
                  "domain_name": "demodomain.com",
                  "hostname": "web01",
                  "consumer_id": 0,
                  "backups_enabled": false,
                  "password": "a8hjsjnbs91",
                  "label": "foo",
                  "slices_count": null,
                  "created_at": "2009-04-16T08:17:39-04:00"
                }
              }"""
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _virtual_machines_api10json_virtual_machines(self, method, url, body, headers):
        body = """     [{
              "virtual_machine":
                {
                  "running": true,
                  "updated_at": "2009-05-15T06:55:02-04:00",
                  "power_action_pending": false,
                  "system_template_id": 41,
                  "id": 1384,
                  "cloud_id": 3,
                  "domain_name": "demodomain.com",
                  "hostname": "web01",
                  "consumer_id": 0,
                  "backups_enabled": false,
                  "password": "a8hjsjnbs91",
                  "label": "Web Server 01",
                  "slices_count": null,
                  "created_at": "2009-04-16T08:17:39-04:00"
                }
              },
              {
                "virtual_machine":
                  {
                    "running": true,
                    "updated_at": "2009-05-15T06:55:02-04:00",
                    "power_action_pending": false,
                    "system_template_id": 41,
                    "id": 1385,
                    "cloud_id": 3,
                    "domain_name": "demodomain.com",
                    "hostname": "mysql01",
                    "consumer_id": 0,
                    "backups_enabled": false,
                    "password": "dsi8h38hd2s",
                    "label": "MySQL Server 01",
                    "slices_count": null,
                    "created_at": "2009-04-16T08:17:39-04:00"
                  }
                }]"""
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _available_clouds_api10json_templates(self, method, url, body, headers):
        body = self.fixtures.load('_available_clouds_api10json_templates.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _available_clouds_api10json_create(self, method, url, body, headers):
        body = """
        [{"cloud":{"system_templates":[{"id":9,"label":"Ubuntu 8.04 x64"}],"id":2,"label":"USA VPS Cloud"}}]
        """
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

if __name__ == '__main__':
    sys.exit(unittest.main())
