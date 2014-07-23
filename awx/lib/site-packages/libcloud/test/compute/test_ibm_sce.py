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
import unittest
from libcloud.utils.py3 import httplib
import sys

from libcloud.compute.types import InvalidCredsError
from libcloud.compute.drivers.ibm_sce import IBMNodeDriver as IBM
from libcloud.compute.base import Node, NodeImage, NodeSize, NodeLocation

from libcloud.test import MockHttp
from libcloud.test.compute import TestCaseMixin
from libcloud.test.file_fixtures import ComputeFileFixtures
from libcloud.test.secrets import IBM_PARAMS


class IBMTests(unittest.TestCase, TestCaseMixin):

    """
    Tests the IBM SmartCloud Enterprise driver.
    """

    def setUp(self):
        IBM.connectionCls.conn_classes = (None, IBMMockHttp)
        IBMMockHttp.type = None
        self.driver = IBM(*IBM_PARAMS)

    def test_auth(self):
        IBMMockHttp.type = 'UNAUTHORIZED'

        try:
            self.driver.list_nodes()
        except InvalidCredsError:
            e = sys.exc_info()[1]
            self.assertTrue(isinstance(e, InvalidCredsError))
            self.assertEqual(e.value, '401: Unauthorized')
        else:
            self.fail('test should have thrown')

    def test_list_nodes(self):
        ret = self.driver.list_nodes()
        self.assertEqual(len(ret), 3)
        self.assertEqual(ret[0].id, '26557')
        self.assertEqual(ret[0].name, 'Insight Instance')
        self.assertEqual(ret[0].public_ips, ['129.33.196.128'])
        self.assertEqual(ret[0].private_ips, [])  # Private IPs not supported
        self.assertEqual(ret[1].public_ips, [])   # Node is non-active (no IP)
        self.assertEqual(ret[1].private_ips, [])
        self.assertEqual(ret[1].id, '28193')

    def test_list_sizes(self):
        ret = self.driver.list_sizes()
        self.assertEqual(len(ret), 9)  # 9 instance configurations supported
        self.assertEqual(ret[0].id, 'BRZ32.1/2048/60*175')
        self.assertEqual(ret[1].id, 'BRZ64.2/4096/60*500*350')
        self.assertEqual(ret[2].id, 'COP32.1/2048/60')
        self.assertEqual(ret[0].name, 'Bronze 32 bit')
        self.assertEqual(ret[0].disk, None)

    def test_list_images(self):
        ret = self.driver.list_images()
        self.assertEqual(len(ret), 21)
        self.assertEqual(ret[10].name, "Rational Asset Manager 7.2.0.1")
        self.assertEqual(ret[9].id, '10002573')

    def test_list_locations(self):
        ret = self.driver.list_locations()
        self.assertEqual(len(ret), 6)
        self.assertEqual(ret[0].id, '41')
        self.assertEqual(ret[0].name, 'Raleigh')
        self.assertEqual(ret[0].country, 'U.S.A')

    def test_create_node(self):
        # Test creation of node
        IBMMockHttp.type = 'CREATE'
        image = NodeImage(id=11, name='Rational Insight', driver=self.driver)
        size = NodeSize('LARGE', 'LARGE', None, None, None, None, self.driver)
        location = NodeLocation('1', 'POK', 'US', driver=self.driver)
        ret = self.driver.create_node(name='RationalInsight4',
                                      image=image,
                                      size=size,
                                      location=location,
                                      publicKey='MyPublicKey',
                                      configurationData={
                                           'insight_admin_password': 'myPassword1',
                                          'db2_admin_password': 'myPassword2',
                                          'report_user_password': 'myPassword3'})
        self.assertTrue(isinstance(ret, Node))
        self.assertEqual(ret.name, 'RationalInsight4')

        # Test creation attempt with invalid location
        IBMMockHttp.type = 'CREATE_INVALID'
        location = NodeLocation('3', 'DOESNOTEXIST', 'US', driver=self.driver)
        try:
            ret = self.driver.create_node(name='RationalInsight5',
                                          image=image,
                                          size=size,
                                          location=location,
                                          publicKey='MyPublicKey',
                                          configurationData={
                                               'insight_admin_password': 'myPassword1',
                                              'db2_admin_password': 'myPassword2',
                                              'report_user_password': 'myPassword3'})
        except Exception:
            e = sys.exc_info()[1]
            self.assertEqual(e.args[0], 'Error 412: No DataCenter with id: 3')
        else:
            self.fail('test should have thrown')

    def test_destroy_node(self):
        # Delete existent node
        nodes = self.driver.list_nodes()            # retrieves 3 nodes
        self.assertEqual(len(nodes), 3)
        IBMMockHttp.type = 'DELETE'
        toDelete = nodes[1]
        ret = self.driver.destroy_node(toDelete)
        self.assertTrue(ret)

        # Delete non-existent node
        IBMMockHttp.type = 'DELETED'
        nodes = self.driver.list_nodes()            # retrieves 2 nodes
        self.assertEqual(len(nodes), 2)
        try:
            self.driver.destroy_node(toDelete)      # delete non-existent node
        except Exception:
            e = sys.exc_info()[1]
            self.assertEqual(e.args[0], 'Error 404: Invalid Instance ID 28193')
        else:
            self.fail('test should have thrown')

    def test_reboot_node(self):
        nodes = self.driver.list_nodes()
        IBMMockHttp.type = 'REBOOT'

        # Reboot active node
        self.assertEqual(len(nodes), 3)
        ret = self.driver.reboot_node(nodes[0])
        self.assertTrue(ret)

        # Reboot inactive node
        try:
            ret = self.driver.reboot_node(nodes[1])
        except Exception:
            e = sys.exc_info()[1]
            self.assertEqual(
                e.args[0], 'Error 412: Instance must be in the Active state')
        else:
            self.fail('test should have thrown')

    def test_list_volumes(self):
        ret = self.driver.list_volumes()
        self.assertEqual(len(ret), 1)
        self.assertEqual(ret[0].name, 'libcloudvol')
        self.assertEqual(ret[0].extra['location'], '141')
        self.assertEqual(ret[0].size, '2048')
        self.assertEqual(ret[0].id, '39281')

    def test_attach_volume(self):
        vols = self.driver.list_volumes()
        nodes = self.driver.list_nodes()
        IBMMockHttp.type = 'ATTACH'
        ret = self.driver.attach_volume(nodes[0], vols[0])
        self.assertTrue(ret)

    def test_create_volume(self):
        IBMMockHttp.type = 'CREATE'
        ret = self.driver.create_volume('256',
                                        'test-volume',
                                        location='141',
                                        format='RAW',
                                        offering_id='20001208')
        self.assertEqual(ret.id, '39293')
        self.assertEqual(ret.size, '256')
        self.assertEqual(ret.name, 'test-volume')
        self.assertEqual(ret.extra['location'], '141')

    def test_destroy_volume(self):
        vols = self.driver.list_volumes()
        IBMMockHttp.type = 'DESTROY'
        ret = self.driver.destroy_volume(vols[0])
        self.assertTrue(ret)

    def test_ex_destroy_image(self):
        image = self.driver.list_images()
        IBMMockHttp.type = 'DESTROY'
        ret = self.driver.ex_destroy_image(image[0])
        self.assertTrue(ret)

    def test_detach_volume(self):
        nodes = self.driver.list_nodes()
        vols = self.driver.list_volumes()
        IBMMockHttp.type = 'DETACH'
        ret = self.driver.detach_volume(nodes[0], vols[0])
        self.assertTrue(ret)

    def test_ex_allocate_address(self):
        IBMMockHttp.type = 'ALLOCATE'
        ret = self.driver.ex_allocate_address('141', '20001223')
        self.assertEqual(ret.id, '292795')
        self.assertEqual(ret.state, '0')
        self.assertEqual(ret.options['location'], '141')

    def test_ex_delete_address(self):
        IBMMockHttp.type = 'DELETE'
        ret = self.driver.ex_delete_address('292795')
        self.assertTrue(ret)

    def test_ex_list_addresses(self):
        ret = self.driver.ex_list_addresses()
        self.assertEqual(ret[0].ip, '170.225.160.218')
        self.assertEqual(ret[0].options['location'], '141')
        self.assertEqual(ret[0].id, '292795')
        self.assertEqual(ret[0].state, '2')

    def test_ex_list_storage_offerings(self):
        ret = self.driver.ex_list_storage_offerings()
        self.assertEqual(ret[0].name, 'Small')
        self.assertEqual(ret[0].location, '61')
        self.assertEqual(ret[0].id, '20001208')


class IBMMockHttp(MockHttp):
    fixtures = ComputeFileFixtures('ibm_sce')

    def _computecloud_enterprise_api_rest_20100331_instances(self, method, url, body, headers):
        body = self.fixtures.load('instances.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _computecloud_enterprise_api_rest_20100331_instances_DELETED(self, method, url, body, headers):
        body = self.fixtures.load('instances_deleted.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _computecloud_enterprise_api_rest_20100331_instances_UNAUTHORIZED(self, method, url, body, headers):
        return (httplib.UNAUTHORIZED, body, {}, httplib.responses[httplib.UNAUTHORIZED])

    def _computecloud_enterprise_api_rest_20100331_offerings_image(self, method, url, body, headers):
        body = self.fixtures.load('images.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _computecloud_enterprise_api_rest_20100331_locations(self, method, url, body, headers):
        body = self.fixtures.load('locations.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _computecloud_enterprise_api_rest_20100331_instances_26557_REBOOT(self, method, url, body, headers):
        body = self.fixtures.load('reboot_active.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _computecloud_enterprise_api_rest_20100331_instances_28193_REBOOT(self, method, url, body, headers):
        return (412, 'Error 412: Instance must be in the Active state', {}, 'Precondition Failed')

    def _computecloud_enterprise_api_rest_20100331_instances_28193_DELETE(self, method, url, body, headers):
        body = self.fixtures.load('delete.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _computecloud_enterprise_api_rest_20100331_instances_28193_DELETED(self, method, url, body, headers):
        return (404, 'Error 404: Invalid Instance ID 28193', {}, 'Precondition Failed')

    def _computecloud_enterprise_api_rest_20100331_instances_CREATE(self, method, url, body, headers):
        body = self.fixtures.load('create.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _computecloud_enterprise_api_rest_20100331_instances_CREATE_INVALID(self, method, url, body, headers):
        return (412, 'Error 412: No DataCenter with id: 3', {}, 'Precondition Failed')

    def _computecloud_enterprise_api_rest_20100331_storage(self, method, url, body, headers):
        body = self.fixtures.load('list_volumes.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _computecloud_enterprise_api_rest_20100331_instances_26557_ATTACH(self, method, url, body, headers):
        body = self.fixtures.load('attach_volume.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _computecloud_enterprise_api_rest_20100331_storage_CREATE(self, method, url, body, headers):
        body = self.fixtures.load('create_volume.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _computecloud_enterprise_api_rest_20100331_storage_39281_DESTROY(self, method, url, body, headers):
        body = self.fixtures.load('destroy_volume.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _computecloud_enterprise_api_rest_20100331_offerings_image_2_DESTROY(self, method, url, body, headers):
        body = self.fixtures.load('destroy_image.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _computecloud_enterprise_api_rest_20100331_instances_26557_DETACH(self, method, url, body, headers):
        body = self.fixtures.load('detach_volume.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _computecloud_enterprise_api_rest_20100331_addresses_ALLOCATE(self, method, url, body, headers):
        body = self.fixtures.load('allocate_address.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _computecloud_enterprise_api_rest_20100331_addresses_292795_DELETE(self, method, url, body, headers):
        body = self.fixtures.load('delete_address.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _computecloud_enterprise_api_rest_20100331_addresses(self, method, url, body, headers):
        body = self.fixtures.load('list_addresses.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _computecloud_enterprise_api_rest_20100331_offerings_storage(self, method, url, body, headers):
        body = self.fixtures.load('list_storage_offerings.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    # This is only to accommodate the response tests built into test\__init__.py
    def _computecloud_enterprise_api_rest_20100331_instances_26557(self, method, url, body, headers):
        if method == 'DELETE':
            body = self.fixtures.load('delete.xml')
        else:
            body = self.fixtures.load('reboot_active.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

if __name__ == '__main__':
    sys.exit(unittest.main())
