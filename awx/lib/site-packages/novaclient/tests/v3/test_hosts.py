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

from novaclient.tests import utils
from novaclient.tests.v3 import fakes
from novaclient.v3 import hosts


cs = fakes.FakeClient()


class HostsTest(utils.TestCase):

    def test_describe_resource(self):
        hs = cs.hosts.get('host')
        cs.assert_called('GET', '/os-hosts/host')
        for h in hs:
            self.assertIsInstance(h, hosts.Host)

    def test_list_host(self):
        hs = cs.hosts.list()
        cs.assert_called('GET', '/os-hosts')
        for h in hs:
            self.assertIsInstance(h, hosts.Host)
            self.assertEqual(h.zone, 'nova1')

    def test_list_host_with_zone(self):
        hs = cs.hosts.list('nova')
        cs.assert_called('GET', '/os-hosts?zone=nova')
        for h in hs:
            self.assertIsInstance(h, hosts.Host)
            self.assertEqual(h.zone, 'nova')

    def test_update_enable(self):
        host = cs.hosts.get('sample_host')[0]
        values = {"status": "enabled"}
        result = host.update(values)
        cs.assert_called('PUT', '/os-hosts/sample_host', {"host": values})
        self.assertIsInstance(result, hosts.Host)

    def test_update_maintenance(self):
        host = cs.hosts.get('sample_host')[0]
        values = {"maintenance_mode": "enable"}
        result = host.update(values)
        cs.assert_called('PUT', '/os-hosts/sample_host', {"host": values})
        self.assertIsInstance(result, hosts.Host)

    def test_update_both(self):
        host = cs.hosts.get('sample_host')[0]
        values = {"status": "enabled",
                  "maintenance_mode": "enable"}
        result = host.update(values)
        cs.assert_called('PUT', '/os-hosts/sample_host', {"host": values})
        self.assertIsInstance(result, hosts.Host)

    def test_host_startup(self):
        host = cs.hosts.get('sample_host')[0]
        result = host.startup()
        cs.assert_called(
            'GET', '/os-hosts/sample_host/startup')

    def test_host_reboot(self):
        host = cs.hosts.get('sample_host')[0]
        result = host.reboot()
        cs.assert_called(
            'GET', '/os-hosts/sample_host/reboot')

    def test_host_shutdown(self):
        host = cs.hosts.get('sample_host')[0]
        result = host.shutdown()
        cs.assert_called(
            'GET', '/os-hosts/sample_host/shutdown')
