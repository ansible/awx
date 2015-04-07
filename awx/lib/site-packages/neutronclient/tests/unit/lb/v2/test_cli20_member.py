# Copyright 2014 Blue Box Group, Inc.
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
# @author: Craig Tracey <craigtracey@gmail.com>
#

import sys

from neutronclient.neutron.v2_0.lb.v2 import member
from neutronclient.tests.unit import test_cli20


class CLITestV20LbMemberJSON(test_cli20.CLITestV20Base):

    def test_create_member_with_mandatory_params(self):
        """lbaas-member-create with mandatory params only."""
        resource = 'member'
        cmd_resource = 'lbaas_member'
        cmd = member.CreateMember(test_cli20.MyApp(sys.stdout), None)
        my_id = 'my-id'
        address = '10.1.1.1'
        protocol_port = '80'
        pool_id = 'pool-id'
        subnet_id = 'subnet-id'
        args = ['--address', address, '--protocol-port', protocol_port,
                '--subnet', subnet_id, pool_id]
        position_names = ['admin_state_up', 'address',
                          'protocol_port', 'subnet_id']
        position_values = [True, address, protocol_port, subnet_id]
        self._test_create_resource(resource, cmd, '', my_id, args,
                                   position_names, position_values,
                                   cmd_resource=cmd_resource,
                                   parent_id=pool_id)

    def test_create_member_with_all_params(self):
        """lbaas-member-create with all params set."""
        resource = 'member'
        cmd_resource = 'lbaas_member'
        cmd = member.CreateMember(test_cli20.MyApp(sys.stdout), None)
        my_id = 'my-id'
        address = '10.1.1.1'
        protocol_port = '80'
        pool_id = 'pool-id'
        subnet_id = 'subnet-id'
        weight = '100'
        args = ['--address', address, '--protocol-port', protocol_port,
                '--subnet', subnet_id, pool_id, '--weight', weight,
                '--admin-state-down']
        position_names = ['admin_state_up', 'address', 'protocol_port',
                          'subnet_id', 'weight']
        position_values = [False, address, protocol_port, subnet_id, weight]
        self._test_create_resource(resource, cmd, '', my_id, args,
                                   position_names, position_values,
                                   cmd_resource=cmd_resource,
                                   parent_id=pool_id)

    def test_list_members(self):
        """lbaas-member-list."""
        resources = 'members'
        cmd_resources = 'lbaas_members'
        pool_id = 'pool-id'
        cmd = member.ListMember(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd, True, base_args=[pool_id],
                                  cmd_resources=cmd_resources,
                                  parent_id=pool_id)

    def test_list_members_pagination(self):
        """lbaas-member-list with pagination."""
        resources = 'members'
        cmd_resources = 'lbaas_members'
        pool_id = 'pool-id'
        cmd = member.ListMember(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources_with_pagination(resources, cmd,
                                                  base_args=[pool_id],
                                                  cmd_resources=cmd_resources,
                                                  parent_id=pool_id)

    def test_list_members_sort(self):
        """lbaas-member-list --sort-key id --sort-key asc."""
        resources = 'members'
        cmd_resources = 'lbaas_members'
        pool_id = 'pool-id'
        cmd = member.ListMember(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd, True, base_args=[pool_id],
                                  cmd_resources=cmd_resources,
                                  parent_id=pool_id)

    def test_list_members_limit(self):
        """lbaas-member-list -P."""
        resources = 'members'
        cmd_resources = 'lbaas_members'
        pool_id = 'pool-id'
        cmd = member.ListMember(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd, page_size=1000,
                                  base_args=[pool_id],
                                  cmd_resources=cmd_resources,
                                  parent_id=pool_id)

    def test_show_member_id(self):
        """lbaas-member-show test_id."""
        resource = 'member'
        cmd_resource = 'lbaas_member'
        pool_id = 'pool-id'
        cmd = member.ShowMember(test_cli20.MyApp(sys.stdout), None)
        args = ['--fields', 'id', self.test_id, pool_id]
        self._test_show_resource(resource, cmd, self.test_id, args, ['id'],
                                 cmd_resource=cmd_resource, parent_id=pool_id)

    def test_show_member_id_name(self):
        """lbaas-member-show."""
        resource = 'member'
        cmd_resource = 'lbaas_member'
        pool_id = 'pool-id'
        cmd = member.ShowMember(test_cli20.MyApp(sys.stdout), None)
        args = ['--fields', 'id', '--fields', 'name', self.test_id, pool_id]
        self._test_show_resource(resource, cmd, self.test_id,
                                 args, ['id', 'name'],
                                 cmd_resource=cmd_resource, parent_id=pool_id)

    def test_update_member(self):
        """lbaas-member-update myid --name newname."""
        resource = 'member'
        cmd_resource = 'lbaas_member'
        my_id = 'my-id'
        pool_id = 'pool-id'
        args = [my_id, pool_id, '--name', 'newname']
        cmd = member.UpdateMember(test_cli20.MyApp(sys.stdout), None)
        self._test_update_resource(resource, cmd, my_id, args,
                                   {'name': 'newname', },
                                   cmd_resource=cmd_resource,
                                   parent_id=pool_id)

    def test_delete_member(self):
        """lbaas-member-delete my-id."""
        resource = 'member'
        cmd_resource = 'lbaas_member'
        cmd = member.DeleteMember(test_cli20.MyApp(sys.stdout), None)
        my_id = 'my-id'
        pool_id = 'pool-id'
        args = [my_id, pool_id]
        self._test_delete_resource(resource, cmd, my_id, args,
                                   cmd_resource=cmd_resource,
                                   parent_id=pool_id)


class CLITestV20LbMemberXML(CLITestV20LbMemberJSON):
    format = 'xml'
