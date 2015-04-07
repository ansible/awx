# Copyright 2013 Big Switch Networks Inc.
# All Rights Reserved
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
#
# @author: KC Wang, Big Switch Networks Inc.
#

import sys

from neutronclient.neutron.v2_0.fw import firewallrule
from neutronclient.tests.unit import test_cli20


class CLITestV20FirewallRuleJSON(test_cli20.CLITestV20Base):

    def _test_create_firewall_rule_with_mandatory_params(self, enabled):
        """firewall-rule-create with mandatory (none) params only."""
        resource = 'firewall_rule'
        cmd = firewallrule.CreateFirewallRule(test_cli20.MyApp(sys.stdout),
                                              None)
        tenant_id = 'my-tenant'
        name = ''
        my_id = 'myid'
        protocol = 'tcp'
        action = 'allow'
        args = ['--tenant-id', tenant_id,
                '--admin-state-up',
                '--protocol', protocol,
                '--action', action,
                '--enabled', enabled]
        position_names = []
        position_values = []
        self._test_create_resource(resource, cmd, name, my_id, args,
                                   position_names, position_values,
                                   protocol=protocol, action=action,
                                   enabled=enabled, tenant_id=tenant_id)

    def test_create_enabled_firewall_rule_with_mandatory_params_lcase(self):
        self._test_create_firewall_rule_with_mandatory_params(enabled='true')

    def test_create_disabled_firewall_rule_with_mandatory_params_lcase(self):
        self._test_create_firewall_rule_with_mandatory_params(enabled='false')

    def test_create_enabled_firewall_rule_with_mandatory_params(self):
        self._test_create_firewall_rule_with_mandatory_params(enabled='True')

    def test_create_disabled_firewall_rule_with_mandatory_params(self):
        self._test_create_firewall_rule_with_mandatory_params(enabled='False')

    def _setup_create_firewall_rule_with_all_params(self, protocol='tcp'):
        """firewall-rule-create with all params set."""
        resource = 'firewall_rule'
        cmd = firewallrule.CreateFirewallRule(test_cli20.MyApp(sys.stdout),
                                              None)
        name = 'my-name'
        description = 'my-desc'
        source_ip = '192.168.1.0/24'
        destination_ip = '192.168.2.0/24'
        source_port = '0:65535'
        destination_port = '0:65535'
        action = 'allow'
        tenant_id = 'my-tenant'
        my_id = 'myid'
        enabled = 'True'
        args = ['--description', description,
                '--shared',
                '--protocol', protocol,
                '--source-ip-address', source_ip,
                '--destination-ip-address', destination_ip,
                '--source-port', source_port,
                '--destination-port', destination_port,
                '--action', action,
                '--enabled', enabled,
                '--admin-state-up',
                '--tenant-id', tenant_id]
        position_names = []
        position_values = []
        if protocol == 'any':
            protocol = None
        self._test_create_resource(resource, cmd, name, my_id, args,
                                   position_names, position_values,
                                   description=description, shared=True,
                                   protocol=protocol,
                                   source_ip_address=source_ip,
                                   destination_ip_address=destination_ip,
                                   source_port=source_port,
                                   destination_port=destination_port,
                                   action=action, enabled='True',
                                   tenant_id=tenant_id)

    def test_create_firewall_rule_with_all_params(self):
        self._setup_create_firewall_rule_with_all_params()

    def test_create_firewall_rule_with_proto_any(self):
        self._setup_create_firewall_rule_with_all_params(protocol='any')

    def test_list_firewall_rules(self):
        """firewall-rule-list."""
        resources = "firewall_rules"
        cmd = firewallrule.ListFirewallRule(test_cli20.MyApp(sys.stdout),
                                            None)
        self._test_list_resources(resources, cmd, True)

    def test_list_firewall_rules_pagination(self):
        """firewall-rule-list."""
        resources = "firewall_rules"
        cmd = firewallrule.ListFirewallRule(test_cli20.MyApp(sys.stdout),
                                            None)
        self._test_list_resources_with_pagination(resources, cmd)

    def test_list_firewall_rules_sort(self):
        """firewall-rule-list --sort-key name --sort-key id --sort-key asc
        --sort-key desc
        """
        resources = "firewall_rules"
        cmd = firewallrule.ListFirewallRule(test_cli20.MyApp(sys.stdout),
                                            None)
        self._test_list_resources(resources, cmd,
                                  sort_key=["name", "id"],
                                  sort_dir=["asc", "desc"])

    def test_list_firewall_rules_limit(self):
        """firewall-rule-list -P."""
        resources = "firewall_rules"
        cmd = firewallrule.ListFirewallRule(test_cli20.MyApp(sys.stdout),
                                            None)
        self._test_list_resources(resources, cmd, page_size=1000)

    def test_show_firewall_rule_id(self):
        """firewall-rule-show test_id."""
        resource = 'firewall_rule'
        cmd = firewallrule.ShowFirewallRule(test_cli20.MyApp(sys.stdout),
                                            None)
        args = ['--fields', 'id', self.test_id]
        self._test_show_resource(resource, cmd, self.test_id, args, ['id'])

    def test_show_firewall_rule_id_name(self):
        """firewall-rule-show."""
        resource = 'firewall_rule'
        cmd = firewallrule.ShowFirewallRule(test_cli20.MyApp(sys.stdout),
                                            None)
        args = ['--fields', 'id', '--fields', 'name', self.test_id]
        self._test_show_resource(resource, cmd, self.test_id,
                                 args, ['id', 'name'])

    def test_update_firewall_rule(self):
        """firewall-rule-update myid --name newname."""
        resource = 'firewall_rule'
        cmd = firewallrule.UpdateFirewallRule(test_cli20.MyApp(sys.stdout),
                                              None)
        self._test_update_resource(resource, cmd, 'myid',
                                   ['myid', '--name', 'newname'],
                                   {'name': 'newname', })

    def test_update_firewall_rule_protocol(self):
        """firewall-rule-update myid --protocol any."""
        resource = 'firewall_rule'
        cmd = firewallrule.UpdateFirewallRule(test_cli20.MyApp(sys.stdout),
                                              None)
        self._test_update_resource(resource, cmd, 'myid',
                                   ['myid', '--protocol', 'any'],
                                   {'protocol': None, })

    def test_delete_firewall_rule(self):
        """firewall-rule-delete my-id."""
        resource = 'firewall_rule'
        cmd = firewallrule.DeleteFirewallRule(test_cli20.MyApp(sys.stdout),
                                              None)
        my_id = 'myid1'
        args = [my_id]
        self._test_delete_resource(resource, cmd, my_id, args)


class CLITestV20FirewallRuleXML(CLITestV20FirewallRuleJSON):
    format = 'xml'
