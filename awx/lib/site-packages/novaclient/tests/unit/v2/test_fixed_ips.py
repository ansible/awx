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

from novaclient.tests.unit.fixture_data import client
from novaclient.tests.unit.fixture_data import fixedips as data
from novaclient.tests.unit import utils


class FixedIpsTest(utils.FixturedTestCase):

    data_fixture_class = data.Fixture

    scenarios = [('original', {'client_fixture_class': client.V1}),
                 ('session', {'client_fixture_class': client.SessionV1})]

    def test_get_fixed_ip(self):
        info = self.cs.fixed_ips.get(fixed_ip='192.168.1.1')
        self.assert_called('GET', '/os-fixed-ips/192.168.1.1')
        self.assertEqual('192.168.1.0/24', info.cidr)
        self.assertEqual('192.168.1.1', info.address)
        self.assertEqual('foo', info.hostname)
        self.assertEqual('bar', info.host)

    def test_reserve_fixed_ip(self):
        body = {"reserve": None}
        self.cs.fixed_ips.reserve(fixed_ip='192.168.1.1')
        self.assert_called('POST', '/os-fixed-ips/192.168.1.1/action', body)

    def test_unreserve_fixed_ip(self):
        body = {"unreserve": None}
        self.cs.fixed_ips.unreserve(fixed_ip='192.168.1.1')
        self.assert_called('POST', '/os-fixed-ips/192.168.1.1/action', body)
