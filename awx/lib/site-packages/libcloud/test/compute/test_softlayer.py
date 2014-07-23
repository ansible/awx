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

from libcloud.common.types import InvalidCredsError

from libcloud.utils.py3 import httplib
from libcloud.utils.py3 import xmlrpclib
from libcloud.utils.py3 import next

from libcloud.compute.drivers.softlayer import SoftLayerNodeDriver as SoftLayer
from libcloud.compute.drivers.softlayer import SoftLayerException, \
    NODE_STATE_MAP
from libcloud.compute.types import NodeState

from libcloud.test import MockHttp               # pylint: disable-msg=E0611
from libcloud.test.file_fixtures import ComputeFileFixtures
from libcloud.test.secrets import SOFTLAYER_PARAMS


class SoftLayerTests(unittest.TestCase):

    def setUp(self):
        SoftLayer.connectionCls.conn_classes = (
            SoftLayerMockHttp, SoftLayerMockHttp)
        SoftLayerMockHttp.type = None
        self.driver = SoftLayer(*SOFTLAYER_PARAMS)

    def test_list_nodes(self):
        nodes = self.driver.list_nodes()
        node = nodes[0]
        self.assertEqual(node.name, 'libcloud-testing1.example.com')
        self.assertEqual(node.state, NodeState.RUNNING)
        self.assertEqual(node.extra['password'], 'L3TJVubf')

    def test_initializing_state(self):
        nodes = self.driver.list_nodes()
        node = nodes[1]
        self.assertEqual(node.state, NODE_STATE_MAP['INITIATING'])

    def test_list_locations(self):
        locations = self.driver.list_locations()
        dal = next(l for l in locations if l.id == 'dal05')
        self.assertEqual(dal.country, 'US')
        self.assertEqual(dal.id, 'dal05')
        self.assertEqual(dal.name, 'Dallas - Central U.S.')

    def test_list_images(self):
        images = self.driver.list_images()
        image = images[0]
        self.assertEqual(image.id, 'CENTOS_6_64')

    def test_list_sizes(self):
        sizes = self.driver.list_sizes()
        self.assertEqual(len(sizes), 13)

    def test_create_node(self):
        node = self.driver.create_node(name="libcloud-testing",
                                       location=self.driver.list_locations()[0],
                                       size=self.driver.list_sizes()[0],
                                       image=self.driver.list_images()[0])
        self.assertEqual(node.name, 'libcloud-testing.example.com')
        self.assertEqual(node.state, NODE_STATE_MAP['RUNNING'])

    def test_create_fail(self):
        SoftLayerMockHttp.type = "SOFTLAYEREXCEPTION"
        self.assertRaises(
            SoftLayerException,
            self.driver.create_node,
            name="SOFTLAYEREXCEPTION",
            location=self.driver.list_locations()[0],
            size=self.driver.list_sizes()[0],
            image=self.driver.list_images()[0])

    def test_create_creds_error(self):
        SoftLayerMockHttp.type = "INVALIDCREDSERROR"
        self.assertRaises(
            InvalidCredsError,
            self.driver.create_node,
            name="INVALIDCREDSERROR",
            location=self.driver.list_locations()[0],
            size=self.driver.list_sizes()[0],
            image=self.driver.list_images()[0])

    def test_create_node_no_location(self):
        self.driver.create_node(name="Test",
                                size=self.driver.list_sizes()[0],
                                image=self.driver.list_images()[0])

    def test_create_node_no_image(self):
        self.driver.create_node(name="Test", size=self.driver.list_sizes()[0])

    def test_create_node_san(self):
        self.driver.create_node(name="Test", ex_local_disk=False)

    def test_create_node_domain_for_name(self):
        self.driver.create_node(name="libcloud.org")

    def test_create_node_ex_options(self):
        self.driver.create_node(name="Test",
                                location=self.driver.list_locations()[0],
                                size=self.driver.list_sizes()[0],
                                image=self.driver.list_images()[0],
                                ex_domain='libcloud.org',
                                ex_cpus=2,
                                ex_ram=2048,
                                ex_disk=100,
                                ex_bandwidth=10,
                                ex_local_disk=False,
                                ex_datacenter='Dal05',
                                ex_os='UBUNTU_LATEST')

    def test_reboot_node(self):
        node = self.driver.list_nodes()[0]
        self.driver.reboot_node(node)

    def test_destroy_node(self):
        node = self.driver.list_nodes()[0]
        self.driver.destroy_node(node)


class SoftLayerMockHttp(MockHttp):
    fixtures = ComputeFileFixtures('softlayer')

    def _get_method_name(self, type, use_param, qs, path):
        return "_xmlrpc"

    def _xmlrpc(self, method, url, body, headers):
        params, meth_name = xmlrpclib.loads(body)
        url = url.replace("/", "_")
        meth_name = "%s_%s" % (url, meth_name)
        return getattr(self, meth_name)(method, url, body, headers)

    def _xmlrpc_v3_SoftLayer_Virtual_Guest_getCreateObjectOptions(
            self, method, url, body, headers):
        body = self.fixtures.load(
            'v3__SoftLayer_Virtual_Guest_getCreateObjectOptions.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc_v3_SoftLayer_Account_getVirtualGuests(
            self, method, url, body, headers):
        body = self.fixtures.load('v3_SoftLayer_Account_getVirtualGuests.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc_v3_SoftLayer_Location_Datacenter_getDatacenters(
            self, method, url, body, headers):
        body = self.fixtures.load(
            'v3_SoftLayer_Location_Datacenter_getDatacenters.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc_v3_SoftLayer_Virtual_Guest_createObject(
            self, method, url, body, headers):
        fixture = {
            None: 'v3__SoftLayer_Virtual_Guest_createObject.xml',
            'INVALIDCREDSERROR': 'SoftLayer_Account.xml',
            'SOFTLAYEREXCEPTION': 'fail.xml',
        }[self.type]
        body = self.fixtures.load(fixture)
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc_v3_SoftLayer_Virtual_Guest_getObject(
            self, method, url, body, headers):
        body = self.fixtures.load(
            'v3__SoftLayer_Virtual_Guest_getObject.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc_v3_SoftLayer_Virtual_Guest_rebootSoft(
            self, method, url, body, headers):
        body = self.fixtures.load('empty.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc_v3_SoftLayer_Virtual_Guest_deleteObject(
            self, method, url, body, headers):
        body = self.fixtures.load('empty.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])


if __name__ == '__main__':
    sys.exit(unittest.main())
