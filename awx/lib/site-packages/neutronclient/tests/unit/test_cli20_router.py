# Copyright 2012 VMware, Inc
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

import sys

from neutronclient.common import exceptions
from neutronclient.neutron.v2_0 import router
from neutronclient.tests.unit import test_cli20


class CLITestV20RouterJSON(test_cli20.CLITestV20Base):
    def test_create_router(self):
        """Create router: router1."""
        resource = 'router'
        cmd = router.CreateRouter(test_cli20.MyApp(sys.stdout), None)
        name = 'router1'
        myid = 'myid'
        args = [name, ]
        position_names = ['name', ]
        position_values = [name, ]
        self._test_create_resource(resource, cmd, name, myid, args,
                                   position_names, position_values)

    def test_create_router_tenant(self):
        """Create router: --tenant_id tenantid myname."""
        resource = 'router'
        cmd = router.CreateRouter(test_cli20.MyApp(sys.stdout), None)
        name = 'myname'
        myid = 'myid'
        args = ['--tenant_id', 'tenantid', name]
        position_names = ['name', ]
        position_values = [name, ]
        self._test_create_resource(resource, cmd, name, myid, args,
                                   position_names, position_values,
                                   tenant_id='tenantid')

    def test_create_router_admin_state(self):
        """Create router: --admin_state_down myname."""
        resource = 'router'
        cmd = router.CreateRouter(test_cli20.MyApp(sys.stdout), None)
        name = 'myname'
        myid = 'myid'
        args = ['--admin_state_down', name, ]
        position_names = ['name', ]
        position_values = [name, ]
        self._test_create_resource(resource, cmd, name, myid, args,
                                   position_names, position_values,
                                   admin_state_up=False)

    def _create_router_distributed_or_ha(self, distributed=None, ha=None):
        """Create router: --distributed distributed --ha ha myname."""
        resource = 'router'
        cmd = router.CreateRouter(test_cli20.MyApp(sys.stdout), None)
        name = 'myname'
        myid = 'myid'
        args = []
        if distributed is not None:
            args += ['--distributed', str(distributed)]
        if ha is not None:
            args += ['--ha', str(ha)]
        args.append(name)
        position_names = ['name', ]
        position_values = [name, ]
        expected = {}
        if distributed is not None:
            expected['distributed'] = str(distributed)
        if ha is not None:
            expected['ha'] = str(ha)
        self._test_create_resource(resource, cmd, name, myid, args,
                                   position_names, position_values,
                                   **expected)

    def test_create_router_distributed_True(self):
        """Create router: --distributed=True."""
        self._create_router_distributed_or_ha(distributed='True')

    def test_create_router_ha_with_True(self):
        self._create_router_distributed_or_ha(ha='True')

    def test_create_router_ha_with_true(self):
        self._create_router_distributed_or_ha(ha='true')

    def test_create_router_ha_with_False(self):
        self._create_router_distributed_or_ha(ha='False')

    def test_create_router_ha_with_false(self):
        self._create_router_distributed_or_ha(ha='false')

    def test_create_router_distributed_False(self):
        """Create router: --distributed=False."""
        self._create_router_distributed_or_ha(distributed='False')

    def test_create_router_distributed_true(self):
        """Create router: --distributed=true."""
        self._create_router_distributed_or_ha(distributed='true')

    def test_create_router_distributed_false(self):
        """Create router: --distributed=false."""
        self._create_router_distributed_or_ha(distributed='false')

    def test_list_routers_detail(self):
        """list routers: -D."""
        resources = "routers"
        cmd = router.ListRouter(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd, True)

    def test_list_routers_pagination(self):
        resources = "routers"
        cmd = router.ListRouter(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources_with_pagination(resources, cmd)

    def test_list_routers_sort(self):
        """list routers: --sort-key name --sort-key id --sort-key asc
        --sort-key desc
        """
        resources = "routers"
        cmd = router.ListRouter(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd,
                                  sort_key=["name", "id"],
                                  sort_dir=["asc", "desc"])

    def test_list_routers_limit(self):
        """list routers: -P."""
        resources = "routers"
        cmd = router.ListRouter(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd, page_size=1000)

    def test_update_router_exception(self):
        """Update router: myid."""
        resource = 'router'
        cmd = router.UpdateRouter(test_cli20.MyApp(sys.stdout), None)
        self.assertRaises(exceptions.CommandError, self._test_update_resource,
                          resource, cmd, 'myid', ['myid'], {})

    def test_update_router(self):
        """Update router: myid --name myname --tags a b."""
        resource = 'router'
        cmd = router.UpdateRouter(test_cli20.MyApp(sys.stdout), None)
        self._test_update_resource(resource, cmd, 'myid',
                                   ['myid', '--name', 'myname'],
                                   {'name': 'myname'}
                                   )

    def test_delete_router(self):
        """Delete router: myid."""
        resource = 'router'
        cmd = router.DeleteRouter(test_cli20.MyApp(sys.stdout), None)
        myid = 'myid'
        args = [myid]
        self._test_delete_resource(resource, cmd, myid, args)

    def test_show_router(self):
        """Show router: myid."""
        resource = 'router'
        cmd = router.ShowRouter(test_cli20.MyApp(sys.stdout), None)
        args = ['--fields', 'id', '--fields', 'name', self.test_id]
        self._test_show_resource(resource, cmd, self.test_id, args,
                                 ['id', 'name'])

    def _test_add_remove_interface(self, action, mode, cmd, args):
        resource = 'router'
        subcmd = '%s_router_interface' % action
        if mode == 'port':
            body = {'port_id': 'portid'}
        else:
            body = {'subnet_id': 'subnetid'}
        if action == 'add':
            retval = {'subnet_id': 'subnetid', 'port_id': 'portid'}
        else:
            retval = None
        self._test_update_resource_action(resource, cmd, 'myid',
                                          subcmd, args,
                                          body, retval)

    def test_add_interface_compat(self):
        """Add interface to router: myid subnetid."""
        cmd = router.AddInterfaceRouter(test_cli20.MyApp(sys.stdout), None)
        args = ['myid', 'subnetid']
        self._test_add_remove_interface('add', 'subnet', cmd, args)

    def test_add_interface_by_subnet(self):
        """Add interface to router: myid subnet=subnetid."""
        cmd = router.AddInterfaceRouter(test_cli20.MyApp(sys.stdout), None)
        args = ['myid', 'subnet=subnetid']
        self._test_add_remove_interface('add', 'subnet', cmd, args)

    def test_add_interface_by_port(self):
        """Add interface to router: myid port=portid."""
        cmd = router.AddInterfaceRouter(test_cli20.MyApp(sys.stdout), None)
        args = ['myid', 'port=portid']
        self._test_add_remove_interface('add', 'port', cmd, args)

    def test_del_interface_compat(self):
        """Delete interface from router: myid subnetid."""
        cmd = router.RemoveInterfaceRouter(test_cli20.MyApp(sys.stdout), None)
        args = ['myid', 'subnetid']
        self._test_add_remove_interface('remove', 'subnet', cmd, args)

    def test_del_interface_by_subnet(self):
        """Delete interface from router: myid subnet=subnetid."""
        cmd = router.RemoveInterfaceRouter(test_cli20.MyApp(sys.stdout), None)
        args = ['myid', 'subnet=subnetid']
        self._test_add_remove_interface('remove', 'subnet', cmd, args)

    def test_del_interface_by_port(self):
        """Delete interface from router: myid port=portid."""
        cmd = router.RemoveInterfaceRouter(test_cli20.MyApp(sys.stdout), None)
        args = ['myid', 'port=portid']
        self._test_add_remove_interface('remove', 'port', cmd, args)

    def test_set_gateway(self):
        """Set external gateway for router: myid externalid."""
        resource = 'router'
        cmd = router.SetGatewayRouter(test_cli20.MyApp(sys.stdout), None)
        args = ['myid', 'externalid']
        self._test_update_resource(resource, cmd, 'myid',
                                   args,
                                   {"external_gateway_info":
                                    {"network_id": "externalid"}}
                                   )

    def test_set_gateway_disable_snat(self):
        """set external gateway for router: myid externalid."""
        resource = 'router'
        cmd = router.SetGatewayRouter(test_cli20.MyApp(sys.stdout), None)
        args = ['myid', 'externalid', '--disable-snat']
        self._test_update_resource(resource, cmd, 'myid',
                                   args,
                                   {"external_gateway_info":
                                    {"network_id": "externalid",
                                     "enable_snat": False}}
                                   )

    def test_remove_gateway(self):
        """Remove external gateway from router: externalid."""
        resource = 'router'
        cmd = router.RemoveGatewayRouter(test_cli20.MyApp(sys.stdout), None)
        args = ['externalid']
        self._test_update_resource(resource, cmd, 'externalid',
                                   args, {"external_gateway_info": {}}
                                   )


class CLITestV20RouterXML(CLITestV20RouterJSON):
    format = 'xml'
