# Copyright 2013 OpenStack Foundation
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
from novaclient.tests.fixture_data import hosts as data
from novaclient.tests import utils
from novaclient.v3 import hosts


class HostsTest(utils.FixturedTestCase):

    client_fixture_class = client.V3
    data_fixture_class = data.V3

    def test_describe_resource(self):
        hs = self.cs.hosts.get('host')
        self.assert_called('GET', '/os-hosts/host')
        for h in hs:
            self.assertIsInstance(h, hosts.Host)

    def test_list_host(self):
        hs = self.cs.hosts.list()
        self.assert_called('GET', '/os-hosts')
        for h in hs:
            self.assertIsInstance(h, hosts.Host)
            self.assertEqual(h.zone, 'nova1')

    def test_list_host_with_zone(self):
        hs = self.cs.hosts.list('nova')
        self.assert_called('GET', '/os-hosts?zone=nova')
        for h in hs:
            self.assertIsInstance(h, hosts.Host)
            self.assertEqual(h.zone, 'nova')

    def test_update_enable(self):
        host = self.cs.hosts.get('sample_host')[0]
        values = {"status": "enabled"}
        result = host.update(values)
        self.assert_called('PUT', '/os-hosts/sample_host', {"host": values})
        self.assertIsInstance(result, hosts.Host)

    def test_update_maintenance(self):
        host = self.cs.hosts.get('sample_host')[0]
        values = {"maintenance_mode": "enable"}
        result = host.update(values)
        self.assert_called('PUT', '/os-hosts/sample_host', {"host": values})
        self.assertIsInstance(result, hosts.Host)

    def test_update_both(self):
        host = self.cs.hosts.get('sample_host')[0]
        values = {"status": "enabled",
                  "maintenance_mode": "enable"}
        result = host.update(values)
        self.assert_called('PUT', '/os-hosts/sample_host', {"host": values})
        self.assertIsInstance(result, hosts.Host)

    def test_host_startup(self):
        host = self.cs.hosts.get('sample_host')[0]
        host.startup()
        self.assert_called(
            'GET', '/os-hosts/sample_host/startup')

    def test_host_reboot(self):
        host = self.cs.hosts.get('sample_host')[0]
        host.reboot()
        self.assert_called(
            'GET', '/os-hosts/sample_host/reboot')

    def test_host_shutdown(self):
        host = self.cs.hosts.get('sample_host')[0]
        host.shutdown()
        self.assert_called(
            'GET', '/os-hosts/sample_host/shutdown')
