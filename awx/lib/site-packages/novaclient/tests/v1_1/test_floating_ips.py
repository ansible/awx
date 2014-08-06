# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
#
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from novaclient.tests.fixture_data import client
from novaclient.tests.fixture_data import floatingips as data
from novaclient.tests import utils
from novaclient.v1_1 import floating_ips


class FloatingIPsTest(utils.FixturedTestCase):

    client_fixture_class = client.V1
    data_fixture_class = data.FloatingFixture

    def test_list_floating_ips(self):
        fips = self.cs.floating_ips.list()
        self.assert_called('GET', '/os-floating-ips')
        for fip in fips:
            self.assertIsInstance(fip, floating_ips.FloatingIP)

    def test_list_floating_ips_all_tenants(self):
        fips = self.cs.floating_ips.list(all_tenants=True)
        self.assert_called('GET', '/os-floating-ips?all_tenants=1')
        for fip in fips:
            self.assertIsInstance(fip, floating_ips.FloatingIP)

    def test_delete_floating_ip(self):
        fl = self.cs.floating_ips.list()[0]
        fl.delete()
        self.assert_called('DELETE', '/os-floating-ips/1')
        self.cs.floating_ips.delete(1)
        self.assert_called('DELETE', '/os-floating-ips/1')
        self.cs.floating_ips.delete(fl)
        self.assert_called('DELETE', '/os-floating-ips/1')

    def test_create_floating_ip(self):
        fl = self.cs.floating_ips.create()
        self.assert_called('POST', '/os-floating-ips')
        self.assertIsNone(fl.pool)
        self.assertIsInstance(fl, floating_ips.FloatingIP)

    def test_create_floating_ip_with_pool(self):
        fl = self.cs.floating_ips.create('nova')
        self.assert_called('POST', '/os-floating-ips')
        self.assertEqual(fl.pool, 'nova')
        self.assertIsInstance(fl, floating_ips.FloatingIP)
