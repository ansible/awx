#    (c) Copyright 2013 Hewlett-Packard Development Company, L.P.
#    All Rights Reserved.
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
# @author: Swaminathan Vasudevan, Hewlett Packard.

import sys

from neutronclient.neutron.v2_0.vpn import vpnservice
from neutronclient.tests.unit import test_cli20


class CLITestV20VpnServiceJSON(test_cli20.CLITestV20Base):

    def test_create_vpnservice_all_params(self):
        """vpn-service-create all params."""
        resource = 'vpnservice'
        cmd = vpnservice.CreateVPNService(test_cli20.MyApp(sys.stdout), None)
        subnet = 'mysubnet-id'
        router = 'myrouter-id'
        tenant_id = 'mytenant-id'
        my_id = 'my-id'
        name = 'myvpnservice'
        description = 'my-vpn-service'
        admin_state = True

        args = ['--name', name,
                '--description', description,
                router,
                subnet,
                '--tenant-id', tenant_id]

        position_names = ['admin_state_up', 'name', 'description',
                          'subnet_id', 'router_id',
                          'tenant_id']

        position_values = [admin_state, name, description,
                           subnet, router, tenant_id]

        self._test_create_resource(resource, cmd, name, my_id, args,
                                   position_names, position_values)

    def test_create_vpnservice_with_limited_params(self):
        """vpn-service-create with limited params."""
        resource = 'vpnservice'
        cmd = vpnservice.CreateVPNService(test_cli20.MyApp(sys.stdout), None)
        subnet = 'mysubnet-id'
        router = 'myrouter-id'
        tenant_id = 'mytenant-id'
        my_id = 'my-id'
        admin_state = True

        args = [router,
                subnet,
                '--tenant-id', tenant_id]

        position_names = ['admin_state_up',
                          'subnet_id', 'router_id',
                          'tenant_id']

        position_values = [admin_state, subnet, router, tenant_id]

        self._test_create_resource(resource, cmd, None, my_id, args,
                                   position_names, position_values)

    def test_list_vpnservice(self):
        """vpn-service-list."""
        resources = "vpnservices"
        cmd = vpnservice.ListVPNService(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd, True)

    def test_list_vpnservice_pagination(self):
        """vpn-service-list."""
        resources = "vpnservices"
        cmd = vpnservice.ListVPNService(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources_with_pagination(resources, cmd)

    def test_list_vpnservice_sort(self):
        """vpn-service-list --sort-key name --sort-key id --sort-key asc
        --sort-key desc
        """
        resources = "vpnservices"
        cmd = vpnservice.ListVPNService(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd,
                                  sort_key=["name", "id"],
                                  sort_dir=["asc", "desc"])

    def test_list_vpnservice_limit(self):
        """vpn-service-list -P."""
        resources = "vpnservices"
        cmd = vpnservice.ListVPNService(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd, page_size=1000)

    def test_show_vpnservice_id(self):
        """vpn-service-show test_id."""
        resource = 'vpnservice'
        cmd = vpnservice.ShowVPNService(test_cli20.MyApp(sys.stdout), None)
        args = ['--fields', 'id', self.test_id]
        self._test_show_resource(resource, cmd, self.test_id, args, ['id'])

    def test_show_vpnservice_id_name(self):
        """vpn-service-show."""
        resource = 'vpnservice'
        cmd = vpnservice.ShowVPNService(test_cli20.MyApp(sys.stdout), None)
        args = ['--fields', 'id', '--fields', 'name', self.test_id]
        self._test_show_resource(resource, cmd, self.test_id,
                                 args, ['id', 'name'])

    def test_update_vpnservice(self):
        """vpn-service-update myid --name newname --tags a b."""
        resource = 'vpnservice'
        cmd = vpnservice.UpdateVPNService(test_cli20.MyApp(sys.stdout), None)
        self._test_update_resource(resource, cmd, 'myid',
                                   ['myid', '--name', 'newname'],
                                   {'name': 'newname', })

    def test_delete_vpnservice(self):
        """vpn-service-delete my-id."""
        resource = 'vpnservice'
        cmd = vpnservice.DeleteVPNService(test_cli20.MyApp(sys.stdout), None)
        my_id = 'my-id'
        args = [my_id]
        self._test_delete_resource(resource, cmd, my_id, args)


class CLITestV20VpnServiceXML(CLITestV20VpnServiceJSON):
    format = 'xml'
