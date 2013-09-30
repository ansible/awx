# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 IBM Corp.
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

from novaclient.tests.v1_1 import fakes
from novaclient.tests import utils

cs = fakes.FakeClient()


class FixedIpsTest(utils.TestCase):

    def test_get_fixed_ip(self):
        info = cs.fixed_ips.get(fixed_ip='192.168.1.1')
        cs.assert_called('GET', '/os-fixed-ips/192.168.1.1')
        self.assertEqual(info.cidr, '192.168.1.0/24')
        self.assertEqual(info.address, '192.168.1.1')
        self.assertEqual(info.hostname, 'foo')
        self.assertEqual(info.host, 'bar')

    def test_reserve_fixed_ip(self):
        body = {"reserve": None}
        res = cs.fixed_ips.reserve(fixed_ip='192.168.1.1')
        cs.assert_called('POST', '/os-fixed-ips/192.168.1.1/action', body)

    def test_unreserve_fixed_ip(self):
        body = {"unreserve": None}
        res = cs.fixed_ips.unreserve(fixed_ip='192.168.1.1')
        cs.assert_called('POST', '/os-fixed-ips/192.168.1.1/action', body)
