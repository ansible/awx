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

from neutronclient.neutron.v2_0.fw import firewall
from neutronclient.tests.unit import test_cli20


class CLITestV20FirewallJSON(test_cli20.CLITestV20Base):

    def test_create_firewall_with_mandatory_params(self):
        """firewall-create with mandatory (none) params."""
        resource = 'firewall'
        cmd = firewall.CreateFirewall(test_cli20.MyApp(sys.stdout), None)
        name = ''
        tenant_id = 'my-tenant'
        my_id = 'my-id'
        policy_id = 'my-policy-id'
        args = ['--tenant-id', tenant_id, policy_id, ]
        position_names = ['firewall_policy_id', ]
        position_values = [policy_id, ]
        self._test_create_resource(resource, cmd, name, my_id, args,
                                   position_names, position_values,
                                   admin_state_up=True, tenant_id=tenant_id)

    def test_create_firewall_with_all_params(self):
        """firewall-create with all params set."""
        resource = 'firewall'
        cmd = firewall.CreateFirewall(test_cli20.MyApp(sys.stdout), None)
        name = 'my-name'
        description = 'my-desc'
        policy_id = 'my-policy-id'
        tenant_id = 'my-tenant'
        my_id = 'my-id'
        args = ['--description', description,
                '--shared',
                '--admin-state-down',
                '--tenant-id', tenant_id,
                policy_id]
        position_names = ['firewall_policy_id', ]
        position_values = [policy_id, ]
        self._test_create_resource(resource, cmd, name, my_id, args,
                                   position_names, position_values,
                                   description=description,
                                   shared=True, admin_state_up=False,
                                   tenant_id=tenant_id)

    def test_list_firewalls(self):
        """firewall-list."""
        resources = "firewalls"
        cmd = firewall.ListFirewall(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd, True)

    def test_list_firewalls_pagination(self):
        """firewall-list with pagination."""
        resources = "firewalls"
        cmd = firewall.ListFirewall(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources_with_pagination(resources, cmd)

    def test_list_firewalls_sort(self):
        """sorted list: firewall-list --sort-key name --sort-key id
        --sort-key asc --sort-key desc
        """
        resources = "firewalls"
        cmd = firewall.ListFirewall(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd,
                                  sort_key=["name", "id"],
                                  sort_dir=["asc", "desc"])

    def test_list_firewalls_limit(self):
        """size (1000) limited list: firewall-list -P."""
        resources = "firewalls"
        cmd = firewall.ListFirewall(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd, page_size=1000)

    def test_show_firewall_id(self):
        """firewall-show test_id."""
        resource = 'firewall'
        cmd = firewall.ShowFirewall(test_cli20.MyApp(sys.stdout), None)
        args = ['--fields', 'id', self.test_id]
        self._test_show_resource(resource, cmd, self.test_id, args, ['id'])

    def test_show_firewall_id_name(self):
        """firewall-show."""
        resource = 'firewall'
        cmd = firewall.ShowFirewall(test_cli20.MyApp(sys.stdout), None)
        args = ['--fields', 'id', '--fields', 'name', self.test_id]
        self._test_show_resource(resource, cmd, self.test_id,
                                 args, ['id', 'name'])

    def test_update_firewall(self):
        """firewall-update myid --name newname --tags a b."""
        resource = 'firewall'
        cmd = firewall.UpdateFirewall(test_cli20.MyApp(sys.stdout), None)
        self._test_update_resource(resource, cmd, 'myid',
                                   ['myid', '--name', 'newname'],
                                   {'name': 'newname', })

    def test_update_firewall_using_policy_name(self):
        """firewall-update myid --policy newpolicy."""
        resource = 'firewall'
        cmd = firewall.UpdateFirewall(test_cli20.MyApp(sys.stdout), None)
        self._test_update_resource(resource, cmd, 'myid',
                                   ['myid', '--policy', 'newpolicy'],
                                   {'firewall_policy_id': 'newpolicy'})

    def test_delete_firewall(self):
        """firewall-delete my-id."""
        resource = 'firewall'
        cmd = firewall.DeleteFirewall(test_cli20.MyApp(sys.stdout), None)
        my_id = 'my-id'
        args = [my_id]
        self._test_delete_resource(resource, cmd, my_id, args)


class CLITestV20FirewallXML(CLITestV20FirewallJSON):
    format = 'xml'
