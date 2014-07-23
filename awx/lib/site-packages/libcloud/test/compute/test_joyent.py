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

from libcloud.utils.py3 import httplib
from libcloud.common.types import LibcloudError
from libcloud.compute.base import NodeState
from libcloud.compute.drivers.joyent import JoyentNodeDriver

from libcloud.test import MockHttp, unittest
from libcloud.test.file_fixtures import ComputeFileFixtures
from libcloud.test.secrets import JOYENT_PARAMS


class JoyentTestCase(unittest.TestCase):

    def setUp(self):
        JoyentNodeDriver.connectionCls.conn_classes = (None, JoyentHttp)
        self.driver = JoyentNodeDriver(*JOYENT_PARAMS)

    def test_instantiate_multiple_drivers_with_different_region(self):
        kwargs1 = {'region': 'us-east-1'}
        kwargs2 = {'region': 'us-west-1'}
        driver1 = JoyentNodeDriver(*JOYENT_PARAMS, **kwargs1)
        driver2 = JoyentNodeDriver(*JOYENT_PARAMS, **kwargs2)

        self.assertTrue(driver1.connection.host.startswith(kwargs1['region']))
        self.assertTrue(driver2.connection.host.startswith(kwargs2['region']))

        driver1.list_nodes()
        driver2.list_nodes()
        driver1.list_nodes()

        self.assertTrue(driver1.connection.host.startswith(kwargs1['region']))
        self.assertTrue(driver2.connection.host.startswith(kwargs2['region']))

    def test_location_backward_compatibility(self):
        kwargs = {'location': 'us-west-1'}
        driver = JoyentNodeDriver(*JOYENT_PARAMS, **kwargs)
        self.assertTrue(driver.connection.host.startswith(kwargs['location']))

    def test_instantiate_invalid_region(self):
        expected_msg = 'Invalid region.+'

        self.assertRaisesRegexp(LibcloudError, expected_msg, JoyentNodeDriver,
                                'user', 'key', location='invalid')
        self.assertRaisesRegexp(LibcloudError, expected_msg, JoyentNodeDriver,
                                'user', 'key', region='invalid')

    def test_list_sizes(self):
        sizes = self.driver.list_sizes()

        self.assertEqual(sizes[0].ram, 16384)

    def test_list_images(self):
        images = self.driver.list_images()

        self.assertEqual(images[0].name, 'nodejs')

    def test_list_nodes_with_and_without_credentials(self):
        nodes = self.driver.list_nodes()
        self.assertEqual(len(nodes), 2)

        node = nodes[0]
        self.assertEqual(node.public_ips[0], '165.225.129.129')
        self.assertEqual(node.private_ips[0], '10.112.1.130')
        self.assertEqual(node.state, NodeState.RUNNING)

        node = nodes[1]
        self.assertEqual(node.public_ips[0], '165.225.129.128')
        self.assertEqual(node.private_ips[0], '10.112.1.131')
        self.assertEqual(node.state, NodeState.RUNNING)
        self.assertEqual(node.extra['password'], 'abc')

    def test_create_node(self):
        image = self.driver.list_images()[0]
        size = self.driver.list_sizes()[0]
        node = self.driver.create_node(image=image, size=size, name='testlc')

        self.assertEqual(node.name, 'testlc')

    def test_ex_stop_node(self):
        node = self.driver.list_nodes()[0]
        self.assertTrue(self.driver.ex_stop_node(node))

    def test_ex_start_node(self):
        node = self.driver.list_nodes()[0]
        self.assertTrue(self.driver.ex_start_node(node))


class JoyentHttp(MockHttp):
    fixtures = ComputeFileFixtures('joyent')

    def _my_packages(self, method, url, body, headers):
        body = self.fixtures.load('my_packages.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _my_datasets(self, method, url, body, headers):
        body = self.fixtures.load('my_datasets.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _my_machines(self, method, url, body, headers):
        if method == 'GET':
            body = self.fixtures.load('my_machines.json')
        elif method == 'POST':
            body = self.fixtures.load('my_machines_create.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _my_machines_2fb67f5f_53f2_40ab_9d99_b9ff68cfb2ab(self, method, url,
                                                          body, headers):
        return (httplib.ACCEPTED, '', {}, httplib.responses[httplib.ACCEPTED])


if __name__ == '__main__':
    sys.exit(unittest.main())
