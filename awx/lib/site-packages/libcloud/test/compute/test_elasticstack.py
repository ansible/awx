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

from libcloud.compute.base import Node
from libcloud.compute.drivers.elasticstack import ElasticStackException
from libcloud.compute.drivers.elastichosts import \
    ElasticHostsNodeDriver as ElasticHosts
from libcloud.compute.drivers.skalicloud import \
    SkaliCloudNodeDriver as SkaliCloud
from libcloud.compute.drivers.serverlove import \
    ServerLoveNodeDriver as ServerLove
from libcloud.common.types import InvalidCredsError, MalformedResponseError

from libcloud.test import MockHttp, unittest
from libcloud.test.file_fixtures import ComputeFileFixtures


class ElasticStackTestCase(object):

    def setUp(self):
        # Re-use ElasticHosts fixtures for the base ElasticStack platform tests
        """ElasticStack.type = Provider.ELASTICHOSTS
        ElasticStack.api_name = 'elastichosts'

        ElasticStackBaseConnection.host = 'test.com'
        ElasticStack.connectionCls.conn_classes = (None,
                                                   ElasticStackMockHttp)
        ElasticStack._standard_drives = ElasticHosts._standard_drives

        self.driver = ElasticStack('foo', 'bar')
        """
        self.mockHttp = ElasticStackMockHttp
        self.mockHttp.type = None

        self.node = Node(id=72258, name=None, state=None, public_ips=None,
                         private_ips=None, driver=self.driver)

    def test_invalid_creds(self):
        self.mockHttp.type = 'UNAUTHORIZED'
        try:
            self.driver.list_nodes()
        except InvalidCredsError:
            e = sys.exc_info()[1]
            self.assertEqual(True, isinstance(e, InvalidCredsError))
        else:
            self.fail('test should have thrown')

    def test_malformed_response(self):
        self.mockHttp.type = 'MALFORMED'
        try:
            self.driver.list_nodes()
        except MalformedResponseError:
            pass
        else:
            self.fail('test should have thrown')

    def test_parse_error(self):
        self.mockHttp.type = 'PARSE_ERROR'
        try:
            self.driver.list_nodes()
        except Exception:
            e = sys.exc_info()[1]
            self.assertTrue(str(e).find('X-Elastic-Error') != -1)
        else:
            self.fail('test should have thrown')

    def test_ex_set_node_configuration(self):
        success = self.driver.ex_set_node_configuration(node=self.node,
                                                        name='name',
                                                        cpu='2')
        self.assertTrue(success)

    def test_ex_set_node_configuration_invalid_keys(self):
        try:
            self.driver.ex_set_node_configuration(node=self.node, foo='bar')
        except ElasticStackException:
            pass
        else:
            self.fail(
                'Invalid option specified, but an exception was not thrown')

    def test_list_nodes(self):
        nodes = self.driver.list_nodes()
        self.assertTrue(isinstance(nodes, list))
        self.assertEqual(len(nodes), 1)

        node = nodes[0]
        self.assertEqual(node.public_ips[0], "1.2.3.4")
        self.assertEqual(node.public_ips[1], "1.2.3.5")
        self.assertEqual(node.extra['smp'], 1)
        self.assertEqual(
            node.extra['ide:0:0'], "b6049e7a-aa1b-47f9-b21d-cdf2354e28d3")

    def test_list_sizes(self):
        images = self.driver.list_sizes()
        self.assertEqual(len(images), 6)
        image = [i for i in images if i.id == 'small'][0]
        self.assertEqual(image.id, 'small')
        self.assertEqual(image.name, 'Small instance')
        self.assertEqual(image.cpu, 2000)
        self.assertEqual(image.ram, 1700)
        self.assertEqual(image.disk, 160)
        self.assertTrue(isinstance(image.price, float))

    def test_list_images(self):
        images = self.driver.list_images()
        self.assertEqual(len(images), len(self.driver._standard_drives))

        for uuid, values in list(self.driver._standard_drives.items()):
            self.assertEqual(
                len([image for image in images if image.id == uuid]), 1)

    def test_reboot_node(self):
        node = self.driver.list_nodes()[0]
        self.assertTrue(self.driver.reboot_node(node))

    def test_destroy_node(self):
        node = self.driver.list_nodes()[0]
        self.assertTrue(self.driver.destroy_node(node))

    def test_create_node(self):
        sizes = self.driver.list_sizes()
        size = [s for s in sizes if s.id == 'large'][0]
        image = self.image

        self.assertTrue(self.driver.create_node(name="api.ivan.net.nz",
                                                image=image, size=size))


class ElasticHostsTestCase(ElasticStackTestCase, unittest.TestCase):

    def setUp(self):
        ElasticHosts.connectionCls.conn_classes = (None,
                                                   ElasticStackMockHttp)

        self.driver = ElasticHosts('foo', 'bar')
        images = self.driver.list_images()
        self.image = [i for i in images if
                      i.id == '38df0986-4d85-4b76-b502-3878ffc80161'][0]
        super(ElasticHostsTestCase, self).setUp()

    def test_multiple_drivers_with_different_regions(self):
        driver1 = ElasticHosts('foo', 'bar', region='lon-p')
        driver2 = ElasticHosts('foo', 'bar', region='sat-p')

        self.assertTrue(driver1.connection.host.startswith('api-lon-p'))
        self.assertTrue(driver2.connection.host.startswith('api-sat-p'))

        driver1.list_nodes()
        driver2.list_nodes()
        driver1.list_nodes()

        self.assertTrue(driver1.connection.host.startswith('api-lon-p'))
        self.assertTrue(driver2.connection.host.startswith('api-sat-p'))

    def test_invalid_region(self):
        expected_msg = r'Invalid region.+'
        self.assertRaisesRegexp(ValueError, expected_msg, ElasticHosts,
                                'foo', 'bar', region='invalid')


class SkaliCloudTestCase(ElasticStackTestCase, unittest.TestCase):

    def setUp(self):
        SkaliCloud.connectionCls.conn_classes = (None,
                                                 ElasticStackMockHttp)

        self.driver = SkaliCloud('foo', 'bar')

        images = self.driver.list_images()
        self.image = [i for i in images if
                      i.id == '90aa51f2-15c0-4cff-81ee-e93aa20b9468'][0]
        super(SkaliCloudTestCase, self).setUp()


class ServerLoveTestCase(ElasticStackTestCase, unittest.TestCase):

    def setUp(self):
        ServerLove.connectionCls.conn_classes = (None,
                                                 ElasticStackMockHttp)

        self.driver = ServerLove('foo', 'bar')

        images = self.driver.list_images()
        self.image = [i for i in images if
                      i.id == '679f5f44-0be7-4745-a658-cccd4334c1aa'][0]
        super(ServerLoveTestCase, self).setUp()


class ElasticStackMockHttp(MockHttp):

    fixtures = ComputeFileFixtures('elastichosts')

    def _servers_info_UNAUTHORIZED(self, method, url, body, headers):
        return (httplib.UNAUTHORIZED, body, {}, httplib.responses[httplib.NO_CONTENT])

    def _servers_info_MALFORMED(self, method, url, body, headers):
        body = "{malformed: '"
        return (httplib.OK, body, {}, httplib.responses[httplib.NO_CONTENT])

    def _servers_info_PARSE_ERROR(self, method, url, body, headers):
        return (505, body, {}, httplib.responses[httplib.NO_CONTENT])

    def _servers_b605ca90_c3e6_4cee_85f8_a8ebdf8f9903_reset(self, method, url, body, headers):
        return (httplib.NO_CONTENT, body, {}, httplib.responses[httplib.NO_CONTENT])

    def _servers_b605ca90_c3e6_4cee_85f8_a8ebdf8f9903_destroy(self, method, url, body, headers):
        return (httplib.NO_CONTENT, body, {}, httplib.responses[httplib.NO_CONTENT])

    def _drives_create(self, method, url, body, headers):
        body = self.fixtures.load('drives_create.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _drives_0012e24a_6eae_4279_9912_3432f698cec8_image_38df0986_4d85_4b76_b502_3878ffc80161_gunzip(self, method,
                                                                                                       url, body,
                                                                                                       headers):
        # ElasticHosts image
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _drives_0012e24a_6eae_4279_9912_3432f698cec8_image_90aa51f2_15c0_4cff_81ee_e93aa20b9468_gunzip(self, method,
                                                                                                       url, body,
                                                                                                       headers):
        # Skalikloud image
        return (httplib.NO_CONTENT, body, {}, httplib.responses[httplib.NO_CONTENT])

    def _drives_0012e24a_6eae_4279_9912_3432f698cec8_image_679f5f44_0be7_4745_a658_cccd4334c1aa_gunzip(self, method,
                                                                                                       url, body,
                                                                                                       headers):
        # ServerLove image
        return (httplib.NO_CONTENT, body, {}, httplib.responses[httplib.NO_CONTENT])

    def _drives_0012e24a_6eae_4279_9912_3432f698cec8_info(self, method, url, body, headers):
        body = self.fixtures.load('drives_info.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _servers_create(self, method, url, body, headers):
        body = self.fixtures.load('servers_create.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _servers_info(self, method, url, body, headers):
        body = self.fixtures.load('servers_info.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _servers_72258_set(self, method, url, body, headers):
        body = '{}'
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

if __name__ == '__main__':
    sys.exit(unittest.main())
