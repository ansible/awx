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
#
# Created by Markos Gogoulos (https://mist.io)
#

import sys
import unittest
from libcloud.utils.py3 import httplib

from libcloud.compute.drivers.nephoscale import NephoscaleNodeDriver

from libcloud.test import MockHttp
from libcloud.test.compute import TestCaseMixin
from libcloud.test.file_fixtures import ComputeFileFixtures


class NephoScaleTest(unittest.TestCase, TestCaseMixin):

    def setUp(self):
        NephoscaleNodeDriver.connectionCls.conn_classes = (
            NephoscaleMockHttp, NephoscaleMockHttp)
        self.driver = NephoscaleNodeDriver('user', 'password')

    def test_list_sizes(self):
        sizes = self.driver.list_sizes()
        self.assertEqual(len(sizes), 13)
        for size in sizes:
            self.assertEqual(type(size.disk), int)
            self.assertEqual(type(size.ram), int)

    def test_list_images(self):
        images = self.driver.list_images()
        self.assertEqual(len(images), 18)
        for image in images:
            arch = image.extra.get('architecture')
            self.assertTrue(arch.startswith('x86'))

    def test_list_locations(self):
        locations = self.driver.list_locations()
        self.assertEqual(len(locations), 2)
        self.assertEqual(locations[0].name, "SJC-1")

    def test_list_nodes(self):
        nodes = self.driver.list_nodes()
        self.assertEqual(len(nodes), 2)
        self.assertEqual(nodes[0].extra.get('zone'), 'RIC-1')
        self.assertEqual(nodes[0].name, 'mongodb-staging')
        self.assertEqual(nodes[0].extra.get('service_type'),
                         'CS05 - 0.5GB, 1Core, 25GB')

    def test_list_keys(self):
        keys = self.driver.ex_list_keypairs()
        self.assertEqual(len(keys), 2)
        self.assertEqual(keys[0].name, 'mistio-ssh')

    def test_list_ssh_keys(self):
        ssh_keys = self.driver.ex_list_keypairs(ssh=True)
        self.assertEqual(len(ssh_keys), 1)
        self.assertTrue(ssh_keys[0].public_key.startswith('ssh-rsa'))

    def test_list_password_keys(self):
        password_keys = self.driver.ex_list_keypairs(password=True)
        self.assertEqual(len(password_keys), 1)
        self.assertEquals(password_keys[0].password, '23d493j5')

    def test_reboot_node(self):
        node = self.driver.list_nodes()[0]
        result = self.driver.reboot_node(node)
        self.assertTrue(result)

    def test_destroy_node(self):
        node = self.driver.list_nodes()[0]
        result = self.driver.destroy_node(node)
        self.assertTrue(result)

    def test_stop_node(self):
        node = self.driver.list_nodes()[0]
        result = self.driver.ex_stop_node(node)
        self.assertTrue(result)

    def test_start_node(self):
        node = self.driver.list_nodes()[0]
        result = self.driver.ex_start_node(node)
        self.assertTrue(result)

    def test_rename_node(self):
        node = self.driver.list_nodes()[0]
        result = self.driver.rename_node(node, 'new-name')
        self.assertTrue(result)

    def test_create_node(self):
        name = 'mongodb-staging'
        size = self.driver.list_sizes()[0]
        image = self.driver.list_images()[3]
        node = self.driver.create_node(name=name,
                                       size=size,
                                       nowait=True,
                                       image=image)
        self.assertEqual(node.name, 'mongodb-staging')

    def test_create_node_no_name(self):
        size = self.driver.list_sizes()[0]
        image = self.driver.list_images()[3]
        self.assertRaises(TypeError, self.driver.create_node, size=size,
                          image=image)

    def test_delete_ssh_keys(self):
        self.assertTrue(self.driver.ex_delete_keypair(key_id=72209, ssh=True))

    def test_delete_password_keys(self):
        self.assertTrue(self.driver.ex_delete_keypair(key_id=72211))


class NephoscaleMockHttp(MockHttp):
    fixtures = ComputeFileFixtures('nephoscale')

    def _server_type_cloud(self, method, url, body, headers):
        body = self.fixtures.load('list_sizes.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _server_cloud(self, method, url, body, headers):
        if method == 'POST':
            body = self.fixtures.load('success_action.json')
        else:
            body = self.fixtures.load('list_nodes.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _image_server(self, method, url, body, headers):
        body = self.fixtures.load('list_images.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _datacenter_zone(self, method, url, body, headers):
        body = self.fixtures.load('list_locations.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _key(self, method, url, body, headers):
        body = self.fixtures.load('list_keys.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _key_sshrsa(self, method, url, body, headers):
        body = self.fixtures.load('list_ssh_keys.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _key_password(self, method, url, body, headers):
        body = self.fixtures.load('list_password_keys.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _server_cloud_88241(self, method, url, body, headers):
        body = self.fixtures.load('success_action.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _server_cloud_88241_initiator_restart(self, method, url, body,
                                              headers):
        body = self.fixtures.load('success_action.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _server_cloud_88241_initiator_start(self, method, url, body, headers):
        body = self.fixtures.load('success_action.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _server_cloud_88241_initiator_stop(self, method, url, body, headers):
        body = self.fixtures.load('success_action.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _key_password_72211(self, method, url, body, headers):
        body = self.fixtures.load('success_action.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _key_sshrsa_72209(self, method, url, body, headers):
        body = self.fixtures.load('success_action.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])


if __name__ == '__main__':
    sys.exit(unittest.main())
