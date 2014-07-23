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

import unittest
import sys

from libcloud.utils.py3 import httplib
from libcloud.utils.py3 import xmlrpclib

from libcloud.compute.drivers.vcl import VCLNodeDriver as VCL
from libcloud.compute.types import NodeState

from libcloud.test import MockHttp
from libcloud.test.file_fixtures import ComputeFileFixtures
from libcloud.test.secrets import VCL_PARAMS


class VCLTests(unittest.TestCase):

    def setUp(self):
        VCL.connectionCls.conn_classes = (
            VCLMockHttp, VCLMockHttp)
        VCLMockHttp.type = None
        self.driver = VCL(*VCL_PARAMS)

    def test_list_nodes(self):
        node = self.driver.list_nodes(ipaddr='192.168.1.1')[0]
        self.assertEqual(node.name, 'CentOS 5.4 Base (32 bit VM)')
        self.assertEqual(node.state, NodeState.RUNNING)
        self.assertEqual(node.extra['pass'], 'ehkNGW')

    def test_list_images(self):
        images = self.driver.list_images()
        image = images[0]
        self.assertEqual(image.id, '8')

    def test_list_sizes(self):
        sizes = self.driver.list_sizes()
        self.assertEqual(len(sizes), 1)

    def test_create_node(self):
        image = self.driver.list_images()[0]
        node = self.driver.create_node(image=image)
        self.assertEqual(node.id, '51')

    def test_destroy_node(self):
        node = self.driver.list_nodes(ipaddr='192.168.1.1')[0]
        self.assertTrue(self.driver.destroy_node(node))

    def test_ex_update_node_access(self):
        node = self.driver.list_nodes(ipaddr='192.168.1.1')[0]
        node = self.driver.ex_update_node_access(node, ipaddr='192.168.1.2')
        self.assertEqual(node.name, 'CentOS 5.4 Base (32 bit VM)')
        self.assertEqual(node.state, NodeState.RUNNING)
        self.assertEqual(node.extra['pass'], 'ehkNGW')

    def test_ex_extend_request_time(self):
        node = self.driver.list_nodes(ipaddr='192.168.1.1')[0]
        self.assertTrue(self.driver.ex_extend_request_time(node, 60))

    def test_ex_get_request_end_time(self):
        node = self.driver.list_nodes(ipaddr='192.168.1.1')[0]
        self.assertEqual(
            self.driver.ex_get_request_end_time(node),
            1334168100
        )


class VCLMockHttp(MockHttp):
    fixtures = ComputeFileFixtures('vcl')

    def _get_method_name(self, type, use_param, qs, path):
        return "_xmlrpc"

    def _xmlrpc(self, method, url, body, headers):
        params, meth_name = xmlrpclib.loads(body)
        if self.type:
            meth_name = "%s_%s" % (meth_name, self.type)
        return getattr(self, meth_name)(method, url, body, headers)

    def XMLRPCgetImages(self, method, url, body, headers):
        body = self.fixtures.load('XMLRPCgetImages.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def XMLRPCextendRequest(self, method, url, body, headers):
        body = self.fixtures.load('XMLRPCextendRequest.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def XMLRPCgetRequestIds(self, method, url, body, headers):
        body = self.fixtures.load(
            'XMLRPCgetRequestIds.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def XMLRPCgetRequestStatus(self, method, url, body, headers):
        body = self.fixtures.load(
            'XMLRPCgetRequestStatus.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def XMLRPCendRequest(self, method, url, body, headers):
        body = self.fixtures.load(
            'XMLRPCendRequest.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def XMLRPCaddRequest(self, method, url, body, headers):
        body = self.fixtures.load(
            'XMLRPCaddRequest.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def XMLRPCgetRequestConnectData(self, method, url, body, headers):
        body = self.fixtures.load(
            'XMLRPCgetRequestConnectData.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

if __name__ == '__main__':
    sys.exit(unittest.main())
