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

from novaclient import exceptions
from novaclient.tests.unit.fixture_data import client
from novaclient.tests.unit.fixture_data import security_group_rules as data
from novaclient.tests.unit import utils
from novaclient.v2 import security_group_rules


class SecurityGroupRulesTest(utils.FixturedTestCase):

    client_fixture_class = client.V1
    data_fixture_class = data.Fixture

    def test_delete_security_group_rule(self):
        self.cs.security_group_rules.delete(1)
        self.assert_called('DELETE', '/os-security-group-rules/1')

    def test_create_security_group_rule(self):
        sg = self.cs.security_group_rules.create(1, "tcp", 1, 65535,
                                                 "10.0.0.0/16")

        body = {
            "security_group_rule": {
                "ip_protocol": "tcp",
                "from_port": 1,
                "to_port": 65535,
                "cidr": "10.0.0.0/16",
                "group_id": None,
                "parent_group_id": 1,
            }
        }

        self.assert_called('POST', '/os-security-group-rules', body)
        self.assertTrue(isinstance(sg, security_group_rules.SecurityGroupRule))

    def test_create_security_group_group_rule(self):
        sg = self.cs.security_group_rules.create(1, "tcp", 1, 65535,
                                                 "10.0.0.0/16", 101)

        body = {
            "security_group_rule": {
                "ip_protocol": "tcp",
                "from_port": 1,
                "to_port": 65535,
                "cidr": "10.0.0.0/16",
                "group_id": 101,
                "parent_group_id": 1,
            }
        }

        self.assert_called('POST', '/os-security-group-rules', body)
        self.assertTrue(isinstance(sg, security_group_rules.SecurityGroupRule))

    def test_invalid_parameters_create(self):
        self.assertRaises(exceptions.CommandError,
                          self.cs.security_group_rules.create,
                          1, "invalid_ip_protocol", 1, 65535,
                          "10.0.0.0/16", 101)
        self.assertRaises(exceptions.CommandError,
                          self.cs.security_group_rules.create,
                          1, "tcp", "invalid_from_port", 65535,
                          "10.0.0.0/16", 101)
        self.assertRaises(exceptions.CommandError,
                          self.cs.security_group_rules.create,
                          1, "tcp", 1, "invalid_to_port",
                          "10.0.0.0/16", 101)

    def test_security_group_rule_str(self):
        sg = self.cs.security_group_rules.create(1, "tcp", 1, 65535,
                                                 "10.0.0.0/16")
        self.assertEqual('1', str(sg))

    def test_security_group_rule_del(self):
        sg = self.cs.security_group_rules.create(1, "tcp", 1, 65535,
                                                 "10.0.0.0/16")
        sg.delete()
        self.assert_called('DELETE', '/os-security-group-rules/1')
