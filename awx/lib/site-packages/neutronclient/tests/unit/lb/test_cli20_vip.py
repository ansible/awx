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

from neutronclient.neutron.v2_0.lb import vip
from neutronclient.tests.unit import test_cli20


class CLITestV20LbVipJSON(test_cli20.CLITestV20Base):
    def setUp(self):
        super(CLITestV20LbVipJSON, self).setUp(plurals={'tags': 'tag'})

    def test_create_vip_with_mandatory_params(self):
        """lb-vip-create with all mandatory params."""
        resource = 'vip'
        cmd = vip.CreateVip(test_cli20.MyApp(sys.stdout), None)
        pool_id = 'my-pool-id'
        name = 'my-name'
        subnet_id = 'subnet-id'
        protocol_port = '1000'
        protocol = 'TCP'
        tenant_id = 'my-tenant'
        my_id = 'my-id'
        args = ['--name', name,
                '--protocol-port', protocol_port,
                '--protocol', protocol,
                '--subnet-id', subnet_id,
                '--tenant-id', tenant_id,
                pool_id]
        position_names = ['pool_id', 'name', 'protocol_port', 'protocol',
                          'subnet_id', 'tenant_id']
        position_values = [pool_id, name, protocol_port, protocol,
                           subnet_id, tenant_id]
        self._test_create_resource(resource, cmd, name, my_id, args,
                                   position_names, position_values,
                                   admin_state_up=True)

    def test_create_vip_with_all_params(self):
        """lb-vip-create with all params."""
        resource = 'vip'
        cmd = vip.CreateVip(test_cli20.MyApp(sys.stdout), None)
        pool_id = 'my-pool-id'
        name = 'my-name'
        description = 'my-desc'
        address = '10.0.0.2'
        admin_state = False
        connection_limit = '1000'
        subnet_id = 'subnet-id'
        protocol_port = '80'
        protocol = 'TCP'
        tenant_id = 'my-tenant'
        my_id = 'my-id'
        args = ['--name', name,
                '--description', description,
                '--address', address,
                '--admin-state-down',
                '--connection-limit', connection_limit,
                '--protocol-port', protocol_port,
                '--protocol', protocol,
                '--subnet-id', subnet_id,
                '--tenant-id', tenant_id,
                pool_id]
        position_names = ['pool_id', 'name', 'description', 'address',
                          'admin_state_up', 'connection_limit',
                          'protocol_port', 'protocol', 'subnet_id',
                          'tenant_id']
        position_values = [pool_id, name, description, address,
                           admin_state, connection_limit, protocol_port,
                           protocol, subnet_id,
                           tenant_id]
        self._test_create_resource(resource, cmd, name, my_id, args,
                                   position_names, position_values)

    def test_create_vip_with_session_persistence_params(self):
        """lb-vip-create with mandatory and session-persistence params."""
        resource = 'vip'
        cmd = vip.CreateVip(test_cli20.MyApp(sys.stdout), None)
        pool_id = 'my-pool-id'
        name = 'my-name'
        subnet_id = 'subnet-id'
        protocol_port = '1000'
        protocol = 'TCP'
        tenant_id = 'my-tenant'
        my_id = 'my-id'
        args = ['--name', name,
                '--protocol-port', protocol_port,
                '--protocol', protocol,
                '--subnet-id', subnet_id,
                '--tenant-id', tenant_id,
                pool_id,
                '--session-persistence', 'type=dict',
                'type=cookie,cookie_name=pie',
                '--optional-param', 'any']
        position_names = ['pool_id', 'name', 'protocol_port', 'protocol',
                          'subnet_id', 'tenant_id', 'optional_param']
        position_values = [pool_id, name, protocol_port, protocol,
                           subnet_id, tenant_id, 'any']
        extra_body = {
            'session_persistence': {
                'type': 'cookie',
                'cookie_name': 'pie',
            },
        }
        self._test_create_resource(resource, cmd, name, my_id, args,
                                   position_names, position_values,
                                   admin_state_up=True, extra_body=extra_body)

    def test_list_vips(self):
        """lb-vip-list."""
        resources = "vips"
        cmd = vip.ListVip(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd, True)

    def test_list_vips_pagination(self):
        """lb-vip-list."""
        resources = "vips"
        cmd = vip.ListVip(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources_with_pagination(resources, cmd)

    def test_list_vips_sort(self):
        """lb-vip-list --sort-key name --sort-key id --sort-key asc
        --sort-key desc
        """
        resources = "vips"
        cmd = vip.ListVip(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd,
                                  sort_key=["name", "id"],
                                  sort_dir=["asc", "desc"])

    def test_list_vips_limit(self):
        """lb-vip-list -P."""
        resources = "vips"
        cmd = vip.ListVip(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd, page_size=1000)

    def test_show_vip_id(self):
        """lb-vip-show test_id."""
        resource = 'vip'
        cmd = vip.ShowVip(test_cli20.MyApp(sys.stdout), None)
        args = ['--fields', 'id', self.test_id]
        self._test_show_resource(resource, cmd, self.test_id, args, ['id'])

    def test_show_vip_id_name(self):
        """lb-vip-show."""
        resource = 'vip'
        cmd = vip.ShowVip(test_cli20.MyApp(sys.stdout), None)
        args = ['--fields', 'id', '--fields', 'name', self.test_id]
        self._test_show_resource(resource, cmd, self.test_id,
                                 args, ['id', 'name'])

    def test_update_vip(self):
        """lb-vip-update  myid --name myname --tags a b."""
        resource = 'vip'
        cmd = vip.UpdateVip(test_cli20.MyApp(sys.stdout), None)
        self._test_update_resource(resource, cmd, 'myid',
                                   ['myid', '--name', 'myname',
                                    '--tags', 'a', 'b'],
                                   {'name': 'myname', 'tags': ['a', 'b'], })

    def test_update_vip_with_session_persistence(self):
        resource = 'vip'
        cmd = vip.UpdateVip(test_cli20.MyApp(sys.stdout), None)
        body = {
            'session_persistence': {
                'type': 'source',
            },
        }
        args = ['myid', '--session-persistence', 'type=dict',
                'type=source']
        self._test_update_resource(resource, cmd, 'myid', args, body)

    def test_update_vip_with_session_persistence_and_name(self):
        resource = 'vip'
        cmd = vip.UpdateVip(test_cli20.MyApp(sys.stdout), None)
        body = {
            'name': 'newname',
            'session_persistence': {
                'type': 'cookie',
                'cookie_name': 'pie',
            },
        }
        args = ['myid', '--name', 'newname',
                '--session-persistence', 'type=dict',
                'type=cookie,cookie_name=pie']
        self._test_update_resource(resource, cmd, 'myid', args, body)

    def test_delete_vip(self):
        """lb-vip-delete my-id."""
        resource = 'vip'
        cmd = vip.DeleteVip(test_cli20.MyApp(sys.stdout), None)
        my_id = 'my-id'
        args = [my_id]
        self._test_delete_resource(resource, cmd, my_id, args)


class CLITestV20LbVipXML(CLITestV20LbVipJSON):
    format = 'xml'
