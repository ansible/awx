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

from novaclient.v1_1 import floating_ips
from novaclient.tests import utils
from novaclient.tests.v1_1 import fakes


cs = fakes.FakeClient()


class FloatingIPsTest(utils.TestCase):

    def test_list_floating_ips(self):
        fl = cs.floating_ips.list()
        cs.assert_called('GET', '/os-floating-ips')
        [self.assertTrue(isinstance(f, floating_ips.FloatingIP)) for f in fl]

    def test_delete_floating_ip(self):
        fl = cs.floating_ips.list()[0]
        fl.delete()
        cs.assert_called('DELETE', '/os-floating-ips/1')
        cs.floating_ips.delete(1)
        cs.assert_called('DELETE', '/os-floating-ips/1')
        cs.floating_ips.delete(fl)
        cs.assert_called('DELETE', '/os-floating-ips/1')

    def test_create_floating_ip(self):
        fl = cs.floating_ips.create()
        cs.assert_called('POST', '/os-floating-ips')
        self.assertEqual(fl.pool, None)
        self.assertTrue(isinstance(fl, floating_ips.FloatingIP))

    def test_create_floating_ip_with_pool(self):
        fl = cs.floating_ips.create('foo')
        cs.assert_called('POST', '/os-floating-ips')
        self.assertEqual(fl.pool, 'nova')
        self.assertTrue(isinstance(fl, floating_ips.FloatingIP))
