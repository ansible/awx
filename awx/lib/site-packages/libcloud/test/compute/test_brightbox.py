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
import base64

try:
    import simplejson as json
except ImportError:
    import json

from libcloud.utils.py3 import httplib
from libcloud.utils.py3 import b

from libcloud.common.types import InvalidCredsError
from libcloud.compute.drivers.brightbox import BrightboxNodeDriver
from libcloud.compute.types import NodeState

from libcloud.test import MockHttp
from libcloud.test.compute import TestCaseMixin
from libcloud.test.file_fixtures import ComputeFileFixtures
from libcloud.test.secrets import BRIGHTBOX_PARAMS

USER_DATA = '#!/bin/sh\ntest_script.sh\n'


class BrightboxTest(unittest.TestCase, TestCaseMixin):

    def setUp(self):
        BrightboxNodeDriver.connectionCls.conn_classes = (
            None, BrightboxMockHttp)
        BrightboxMockHttp.type = None
        self.driver = BrightboxNodeDriver(*BRIGHTBOX_PARAMS)

    def test_authentication(self):
        BrightboxMockHttp.type = 'INVALID_CLIENT'
        self.assertRaises(InvalidCredsError, self.driver.list_nodes)

        BrightboxMockHttp.type = 'UNAUTHORIZED_CLIENT'
        self.assertRaises(InvalidCredsError, self.driver.list_nodes)

    def test_invalid_api_version(self):
        kwargs = {'api_version': '2.0'}
        self.driver = BrightboxNodeDriver(*BRIGHTBOX_PARAMS, **kwargs)
        self.assertRaises(Exception, self.driver.list_locations)

    def test_other_host(self):
        kwargs = {'host': 'api.gbt.brightbox.com'}
        self.driver = BrightboxNodeDriver(*BRIGHTBOX_PARAMS, **kwargs)
        locations = self.driver.list_locations()
        self.assertEqual(len(locations), 0)

    def test_list_nodes(self):
        nodes = self.driver.list_nodes()
        self.assertEqual(len(nodes), 2)
        self.assertEqual(len(nodes[0].public_ips), 1)
        self.assertEqual(len(nodes[1].public_ips), 1)
        self.assertEqual(len(nodes[0].private_ips), 1)
        self.assertEqual(len(nodes[1].private_ips), 1)
        self.assertTrue('109.107.35.16' in nodes[0].public_ips)
        self.assertTrue('10.74.210.210' in nodes[0].private_ips)
        self.assertTrue('10.240.228.234' in nodes[1].private_ips)
        self.assertTrue(
            '2a02:1348:14c:393a:24:19ff:fef0:e4ea' in nodes[1].public_ips)
        self.assertEqual(nodes[0].state, NodeState.RUNNING)
        self.assertEqual(nodes[1].state, NodeState.RUNNING)

    def test_list_node_extras(self):
        nodes = self.driver.list_nodes()
        self.assertFalse(nodes[0].size is None)
        self.assertFalse(nodes[1].size is None)
        self.assertFalse(nodes[0].image is None)
        self.assertFalse(nodes[1].image is None)
        self.assertEqual(nodes[0].image.id, 'img-arm8f')
        self.assertEqual(nodes[0].size.id, 'typ-urtky')
        self.assertEqual(nodes[1].image.id, 'img-j93gd')
        self.assertEqual(nodes[1].size.id, 'typ-qdiwq')
        self.assertEqual(nodes[0].extra['fqdn'], 'srv-xvpn7.gb1.brightbox.com')
        self.assertEqual(nodes[1].extra['fqdn'], 'srv-742vn.gb1.brightbox.com')
        self.assertEqual(nodes[0].extra['hostname'], 'srv-xvpn7')
        self.assertEqual(nodes[1].extra['hostname'], 'srv-742vn')
        self.assertEqual(nodes[0].extra['status'], 'active')
        self.assertEqual(nodes[1].extra['status'], 'active')
        self.assertTrue('interfaces' in nodes[0].extra)
        self.assertTrue('zone' in nodes[0].extra)
        self.assertTrue('snapshots' in nodes[0].extra)
        self.assertTrue('server_groups' in nodes[0].extra)
        self.assertTrue('started_at' in nodes[0].extra)
        self.assertTrue('created_at' in nodes[0].extra)
        self.assertFalse('deleted_at' in nodes[0].extra)

    def test_list_sizes(self):
        sizes = self.driver.list_sizes()
        self.assertEqual(len(sizes), 7)
        self.assertEqual(sizes[0].id, 'typ-4nssg')
        self.assertEqual(sizes[0].name, 'Brightbox Nano Instance')
        self.assertEqual(sizes[0].ram, 512)
        self.assertEqual(sizes[0].disk, 20480)
        self.assertEqual(sizes[0].bandwidth, 0)
        self.assertEqual(sizes[0].price, 0)

    def test_list_images(self):
        images = self.driver.list_images()
        self.assertEqual(len(images), 3)
        self.assertEqual(images[0].id, 'img-99q79')
        self.assertEqual(images[0].name, 'CentOS 5.5 server')
        self.assertTrue('ancestor' in images[0].extra)
        self.assertFalse('licence_name' in images[0].extra)

    def test_list_images_extras(self):
        images = self.driver.list_images()
        extra = images[-1].extra
        self.assertEqual(extra['arch'], 'i686')
        self.assertFalse(extra['compatibility_mode'])
        self.assertEqual(extra['created_at'], '2012-01-22T05:36:24Z')
        self.assertTrue('description' in extra)
        self.assertEqual(extra['disk_size'], 671)
        self.assertFalse('min_ram' in extra)
        self.assertFalse(extra['official'])
        self.assertEqual(extra['owner'], 'acc-tqs4c')
        self.assertTrue(extra['public'])
        self.assertEqual(extra['source'], 'oneiric-i386-20178.gz')
        self.assertEqual(extra['source_type'], 'upload')
        self.assertEqual(extra['status'], 'deprecated')
        self.assertEqual(extra['username'], 'ubuntu')
        self.assertEqual(extra['virtual_size'], 1025)
        self.assertFalse('ancestor' in extra)
        self.assertFalse('licence_name' in extra)

    def test_list_locations(self):
        locations = self.driver.list_locations()
        self.assertEqual(locations[0].id, 'zon-6mxqw')
        self.assertEqual(locations[0].name, 'gb1-a')
        self.assertEqual(locations[1].id, 'zon-remk1')
        self.assertEqual(locations[1].name, 'gb1-b')

    def test_reboot_node_response(self):
        node = self.driver.list_nodes()[0]
        self.assertRaises(NotImplementedError, self.driver.reboot_node, [node])

    def test_destroy_node(self):
        node = self.driver.list_nodes()[0]
        self.assertTrue(self.driver.destroy_node(node))

    def test_create_node(self):
        size = self.driver.list_sizes()[0]
        image = self.driver.list_images()[0]
        node = self.driver.create_node(
            name='Test Node', image=image, size=size)
        self.assertEqual('srv-p61uj', node.id)
        self.assertEqual('Test Node', node.name)
        self.assertEqual('gb1-a', node.extra['zone'].name)

    def test_create_node_in_location(self):
        size = self.driver.list_sizes()[0]
        image = self.driver.list_images()[0]
        location = self.driver.list_locations()[1]
        node = self.driver.create_node(
            name='Test Node', image=image, size=size, location=location)
        self.assertEqual('srv-nnumd', node.id)
        self.assertEqual('Test Node', node.name)
        self.assertEqual('gb1-b', node.extra['zone'].name)

    def test_create_node_with_user_data(self):
        size = self.driver.list_sizes()[0]
        image = self.driver.list_images()[0]
        node = self.driver.create_node(
            name='Test Node', image=image, size=size, ex_userdata=USER_DATA)
        decoded = base64.b64decode(b(node.extra['user_data'])).decode('ascii')
        self.assertEqual('gb1-a', node.extra['zone'].name)
        self.assertEqual(USER_DATA, decoded)

    def test_create_node_with_a_server_group(self):
        size = self.driver.list_sizes()[0]
        image = self.driver.list_images()[0]
        node = self.driver.create_node(
            name='Test Node', image=image, size=size, ex_servergroup='grp-12345')
        self.assertEqual('gb1-a', node.extra['zone'].name)
        self.assertEqual(len(node.extra['server_groups']), 1)
        self.assertEqual(node.extra['server_groups'][0]['id'], 'grp-12345')

    def test_create_node_with_a_list_of_server_groups(self):
        size = self.driver.list_sizes()[0]
        image = self.driver.list_images()[0]
        node = self.driver.create_node(
            name='Test Node', image=image, size=size, ex_servergroup=['grp-12345', 'grp-67890'])
        self.assertEqual('gb1-a', node.extra['zone'].name)
        self.assertEqual(len(node.extra['server_groups']), 2)
        self.assertEqual(node.extra['server_groups'][0]['id'], 'grp-12345')
        self.assertEqual(node.extra['server_groups'][1]['id'], 'grp-67890')

    def test_list_cloud_ips(self):
        cip_list = self.driver.ex_list_cloud_ips()
        self.assertEqual(len(cip_list), 4)
        self.assertEqual(cip_list[2]['status'], 'mapped')
        cip_check = cip_list[0]
        self.assertEqual(cip_check['id'], 'cip-tlrp3')
        self.assertEqual(cip_check['public_ip'], '109.107.35.16')
        self.assertEqual(
            cip_check['reverse_dns'], 'cip-109-107-35-16.gb1.brightbox.com')
        self.assertEqual(cip_check['status'], 'unmapped')
        self.assertTrue(cip_check['server'] is None)
        self.assertTrue(cip_check['server_group'] is None)
        self.assertTrue(cip_check['interface'] is None)
        self.assertTrue(cip_check['load_balancer'] is None)

    def test_create_cloud_ip(self):
        cip = self.driver.ex_create_cloud_ip()
        self.assertEqual(cip['id'], 'cip-jsjc5')
        self.assertEqual(
            cip['reverse_dns'], 'cip-109-107-37-234.gb1.brightbox.com')

    def test_create_cloud_ip_with_dns(self):
        cip = self.driver.ex_create_cloud_ip('fred.co.uk')
        self.assertEqual(cip['id'], 'cip-jsjc5')
        self.assertEqual(cip['reverse_dns'], 'fred.co.uk')

    def test_map_cloud_ip(self):
        self.assertTrue(self.driver.ex_map_cloud_ip('cip-jsjc5', 'int-ztqbx'))

    def test_unmap_cloud_ip(self):
        self.assertTrue(self.driver.ex_unmap_cloud_ip('cip-jsjc5'))

    def test_update_cloud_ip(self):
        self.assertTrue(
            self.driver.ex_update_cloud_ip('cip-jsjc5', 'fred.co.uk'))

    def test_destroy_cloud_ip(self):
        self.assertTrue(self.driver.ex_destroy_cloud_ip('cip-jsjc5'))


class BrightboxMockHttp(MockHttp):
    fixtures = ComputeFileFixtures('brightbox')

    def _token(self, method, url, body, headers):
        if method == 'POST':
            return self.response(httplib.OK, self.fixtures.load('token.json'))

    def _token_INVALID_CLIENT(self, method, url, body, headers):
        if method == 'POST':
            return self.response(httplib.BAD_REQUEST, '{"error":"invalid_client"}')

    def _token_UNAUTHORIZED_CLIENT(self, method, url, body, headers):
        if method == 'POST':
            return self.response(httplib.UNAUTHORIZED, '{"error":"unauthorized_client"}')

    def _1_0_images(self, method, url, body, headers):
        if method == 'GET':
            return self.response(httplib.OK, self.fixtures.load('list_images.json'))

    def _1_0_servers(self, method, url, body, headers):
        if method == 'GET':
            return self.response(httplib.OK, self.fixtures.load('list_servers.json'))
        elif method == 'POST':
            body = json.loads(body)
            encoded = base64.b64encode(b(USER_DATA)).decode('ascii')

            if 'user_data' in body and body['user_data'] != encoded:
                data = '{"error_name":"dodgy user data", "errors": ["User data not encoded properly"]}'
                return self.response(httplib.BAD_REQUEST, data)
            if body.get('zone', '') == 'zon-remk1':
                node = json.loads(
                    self.fixtures.load('create_server_gb1_b.json'))
            else:
                node = json.loads(
                    self.fixtures.load('create_server_gb1_a.json'))
            node['name'] = body['name']
            if 'server_groups' in body:
                node['server_groups'] = [{'id': x}
                                         for x in body['server_groups']]
            if 'user_data' in body:
                node['user_data'] = body['user_data']
            return self.response(httplib.ACCEPTED, json.dumps(node))

    def _1_0_servers_srv_xvpn7(self, method, url, body, headers):
        if method == 'DELETE':
            return self.response(httplib.ACCEPTED, '')

    def _1_0_server_types(self, method, url, body, headers):
        if method == 'GET':
            return self.response(httplib.OK, self.fixtures.load('list_server_types.json'))

    def _1_0_zones(self, method, url, body, headers):
        if method == 'GET':
            if headers['Host'] == 'api.gbt.brightbox.com':
                return self.response(httplib.OK, "{}")
            else:
                return self.response(httplib.OK, self.fixtures.load('list_zones.json'))

    def _2_0_zones(self, method, url, body, headers):
        data = '{"error_name":"unrecognised_endpoint", "errors": ["The request was for an unrecognised API endpoint"]}'
        return self.response(httplib.BAD_REQUEST, data)

    def _1_0_cloud_ips(self, method, url, body, headers):
        if method == 'GET':
            return self.response(httplib.OK, self.fixtures.load('list_cloud_ips.json'))
        elif method == 'POST':
            if body:
                body = json.loads(body)

            node = json.loads(self.fixtures.load('create_cloud_ip.json'))

            if 'reverse_dns' in body:
                node['reverse_dns'] = body['reverse_dns']
            return self.response(httplib.ACCEPTED, json.dumps(node))

    def _1_0_cloud_ips_cip_jsjc5(self, method, url, body, headers):
        if method == 'DELETE':
            return self.response(httplib.OK, '')
        elif method == 'PUT':
            body = json.loads(body)
            if body.get('reverse_dns', None) == 'fred.co.uk':
                return self.response(httplib.OK, '')
            else:
                return self.response(httplib.BAD_REQUEST, '{"error_name":"bad dns", "errors": ["Bad dns"]}')

    def _1_0_cloud_ips_cip_jsjc5_map(self, method, url, body, headers):
        if method == 'POST':
            body = json.loads(body)
            if 'destination' in body:
                return self.response(httplib.ACCEPTED, '')
            else:
                data = '{"error_name":"bad destination", "errors": ["Bad destination"]}'
                return self.response(httplib.BAD_REQUEST, data)

    def _1_0_cloud_ips_cip_jsjc5_unmap(self, method, url, body, headers):
        if method == 'POST':
            return self.response(httplib.ACCEPTED, '')

    def response(self, status, body):
        return (status, body, {'content-type': 'application/json'}, httplib.responses[status])


if __name__ == '__main__':
    sys.exit(unittest.main())

# vim: autoindent tabstop=4 shiftwidth=4 expandtab softtabstop=4
# filetype=python
