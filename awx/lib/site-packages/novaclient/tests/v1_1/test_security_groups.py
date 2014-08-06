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
from novaclient.tests.fixture_data import security_groups as data
from novaclient.tests import utils
from novaclient.v1_1 import security_groups


class SecurityGroupsTest(utils.FixturedTestCase):

    client_fixture_class = client.V1
    data_fixture_class = data.Fixture

    def _do_test_list_security_groups(self, search_opts, path):
        sgs = self.cs.security_groups.list(search_opts=search_opts)
        self.assert_called('GET', path)
        for sg in sgs:
            self.assertIsInstance(sg, security_groups.SecurityGroup)

    def test_list_security_groups_all_tenants_on(self):
        self._do_test_list_security_groups(
            None, '/os-security-groups')

    def test_list_security_groups_all_tenants_on(self):
        self._do_test_list_security_groups(
            {'all_tenants': 1}, '/os-security-groups?all_tenants=1')

    def test_list_security_groups_all_tenants_off(self):
        self._do_test_list_security_groups(
            {'all_tenants': 0}, '/os-security-groups')

    def test_get_security_groups(self):
        sg = self.cs.security_groups.get(1)
        self.assert_called('GET', '/os-security-groups/1')
        self.assertIsInstance(sg, security_groups.SecurityGroup)
        self.assertEqual('1', str(sg))

    def test_delete_security_group(self):
        sg = self.cs.security_groups.list()[0]
        sg.delete()
        self.assert_called('DELETE', '/os-security-groups/1')
        self.cs.security_groups.delete(1)
        self.assert_called('DELETE', '/os-security-groups/1')
        self.cs.security_groups.delete(sg)
        self.assert_called('DELETE', '/os-security-groups/1')

    def test_create_security_group(self):
        sg = self.cs.security_groups.create("foo", "foo barr")
        self.assert_called('POST', '/os-security-groups')
        self.assertIsInstance(sg, security_groups.SecurityGroup)

    def test_update_security_group(self):
        sg = self.cs.security_groups.list()[0]
        secgroup = self.cs.security_groups.update(sg, "update", "update")
        self.assert_called('PUT', '/os-security-groups/1')
        self.assertIsInstance(secgroup, security_groups.SecurityGroup)

    def test_refresh_security_group(self):
        sg = self.cs.security_groups.get(1)
        sg2 = self.cs.security_groups.get(1)
        self.assertEqual(sg.name, sg2.name)
        sg2.name = "should be test"
        self.assertNotEqual(sg.name, sg2.name)
        sg2.get()
        self.assertEqual(sg.name, sg2.name)
