# Copyright 2013 Mirantis Inc.
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
# @author: Ilya Shakhat, Mirantis Inc.
#

import sys

from neutronclient.neutron.v2_0.lb import member
from neutronclient.tests.unit import test_cli20


class CLITestV20LbMemberJSON(test_cli20.CLITestV20Base):
    def setUp(self):
        super(CLITestV20LbMemberJSON, self).setUp(plurals={'tags': 'tag'})

    def test_create_member(self):
        """lb-member-create with mandatory params only."""
        resource = 'member'
        cmd = member.CreateMember(test_cli20.MyApp(sys.stdout), None)
        address = '10.0.0.1'
        port = '8080'
        tenant_id = 'my-tenant'
        my_id = 'my-id'
        pool_id = 'pool-id'
        args = ['--address', address, '--protocol-port', port,
                '--tenant-id', tenant_id, pool_id]
        position_names = ['address', 'protocol_port', 'tenant_id', 'pool_id',
                          'admin_state_up']
        position_values = [address, port, tenant_id, pool_id, True]
        self._test_create_resource(resource, cmd, None, my_id, args,
                                   position_names, position_values,
                                   admin_state_up=None)

    def test_create_member_all_params(self):
        """lb-member-create with all available params."""
        resource = 'member'
        cmd = member.CreateMember(test_cli20.MyApp(sys.stdout), None)
        address = '10.0.0.1'
        admin_state_up = False
        port = '8080'
        weight = '1'
        tenant_id = 'my-tenant'
        my_id = 'my-id'
        pool_id = 'pool-id'
        args = ['--address', address, '--admin-state-down',
                '--protocol-port', port, '--weight', weight,
                '--tenant-id', tenant_id, pool_id]
        position_names = [
            'address', 'admin_state_up', 'protocol_port', 'weight',
            'tenant_id', 'pool_id'
        ]
        position_values = [address, admin_state_up, port, weight,
                           tenant_id, pool_id]
        self._test_create_resource(resource, cmd, None, my_id, args,
                                   position_names, position_values,
                                   admin_state_up=None)

    def test_list_members(self):
        """lb-member-list."""
        resources = "members"
        cmd = member.ListMember(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd, True)

    def test_list_members_pagination(self):
        """lb-member-list."""
        resources = "members"
        cmd = member.ListMember(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources_with_pagination(resources, cmd)

    def test_list_members_sort(self):
        """lb-member-list --sort-key name --sort-key id --sort-key asc
        --sort-key desc
        """
        resources = "members"
        cmd = member.ListMember(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd,
                                  sort_key=["name", "id"],
                                  sort_dir=["asc", "desc"])

    def test_list_members_limit(self):
        """lb-member-list -P."""
        resources = "members"
        cmd = member.ListMember(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd, page_size=1000)

    def test_show_member_id(self):
        """lb-member-show test_id."""
        resource = 'member'
        cmd = member.ShowMember(test_cli20.MyApp(sys.stdout), None)
        args = ['--fields', 'id', self.test_id]
        self._test_show_resource(resource, cmd, self.test_id, args, ['id'])

    def test_update_member(self):
        """lb-member-update  myid --name myname --tags a b."""
        resource = 'member'
        cmd = member.UpdateMember(test_cli20.MyApp(sys.stdout), None)
        self._test_update_resource(resource, cmd, 'myid',
                                   ['myid', '--name', 'myname',
                                    '--tags', 'a', 'b'],
                                   {'name': 'myname', 'tags': ['a', 'b'], })

    def test_delete_member(self):
        """lb-member-delete my-id."""
        resource = 'member'
        cmd = member.DeleteMember(test_cli20.MyApp(sys.stdout), None)
        my_id = 'my-id'
        args = [my_id]
        self._test_delete_resource(resource, cmd, my_id, args)


class CLITestV20LbMemberXML(CLITestV20LbMemberJSON):
    format = 'xml'
