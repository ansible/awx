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

from neutronclient.neutron.v2_0.lb.v2 import loadbalancer as lb
from neutronclient.tests.unit import test_cli20


class CLITestV20LbLoadBalancerJSON(test_cli20.CLITestV20Base):

    def test_create_loadbalancer_with_mandatory_params(self):
        """lbaas-loadbalancer-create with mandatory params only."""
        resource = 'loadbalancer'
        cmd_resource = 'lbaas_loadbalancer'
        cmd = lb.CreateLoadBalancer(test_cli20.MyApp(sys.stdout), None)
        name = 'lbaas-loadbalancer-name'
        vip_subnet_id = 'vip-subnet'
        my_id = 'my-id'
        args = ['--name', name, vip_subnet_id]
        position_names = ['name', 'vip_subnet_id']
        position_values = [name, vip_subnet_id]
        self._test_create_resource(resource, cmd, name, my_id, args,
                                   position_names, position_values,
                                   cmd_resource=cmd_resource)

    def test_create_loadbalancer_with_all_params(self):
        """lbaas-loadbalancer-create with all params set."""
        resource = 'loadbalancer'
        cmd_resource = 'lbaas_loadbalancer'
        cmd = lb.CreateLoadBalancer(test_cli20.MyApp(sys.stdout), None)
        name = 'lbaas-loadbalancer-name'
        description = 'lbaas-loadbalancer-desc'
        vip_subnet_id = 'vip-subnet'
        my_id = 'my-id'
        args = ['--admin-state-down', '--description', description,
                '--name', name, vip_subnet_id]
        position_names = ['admin_state_up', 'description', 'name',
                          'vip_subnet_id']
        position_values = [False, description, name, vip_subnet_id]
        self._test_create_resource(resource, cmd, name, my_id, args,
                                   position_names, position_values,
                                   cmd_resource=cmd_resource)

    def test_list_loadbalancers(self):
        """lbaas-loadbalancer-list."""
        resources = 'loadbalancers'
        cmd_resources = 'lbaas_loadbalancers'
        cmd = lb.ListLoadBalancer(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd, True,
                                  cmd_resources=cmd_resources)

    def test_list_loadbalancers_pagination(self):
        """lbaas-loadbalancer-list with pagination."""
        resources = 'loadbalancers'
        cmd_resources = 'lbaas_loadbalancers'
        cmd = lb.ListLoadBalancer(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources_with_pagination(resources, cmd,
                                                  cmd_resources=cmd_resources)

    def test_list_loadbalancers_sort(self):
        """lbaas-loadbalancer-list --sort-key name --sort-key id
        --sort-key asc --sort-key desc
        """
        resources = 'loadbalancers'
        cmd_resources = 'lbaas_loadbalancers'
        cmd = lb.ListLoadBalancer(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd,
                                  sort_key=["name", "id"],
                                  sort_dir=["asc", "desc"],
                                  cmd_resources=cmd_resources)

    def test_list_loadbalancers_limit(self):
        """lbaas-loadbalancer-list -P."""
        resources = 'loadbalancers'
        cmd_resources = 'lbaas_loadbalancers'
        cmd = lb.ListLoadBalancer(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd, page_size=1000,
                                  cmd_resources=cmd_resources)

    def test_show_loadbalancer_id(self):
        """lbaas-loadbalancer-loadbalancer-show test_id."""
        resource = 'loadbalancer'
        cmd_resource = 'lbaas_loadbalancer'
        cmd = lb.ShowLoadBalancer(test_cli20.MyApp(sys.stdout), None)
        args = ['--fields', 'id', self.test_id]
        self._test_show_resource(resource, cmd, self.test_id, args, ['id'],
                                 cmd_resource=cmd_resource)

    def test_show_loadbalancer_id_name(self):
        """lbaas-loadbalancer-loadbalancer-show."""
        resource = 'loadbalancer'
        cmd_resource = 'lbaas_loadbalancer'
        cmd = lb.ShowLoadBalancer(test_cli20.MyApp(sys.stdout), None)
        args = ['--fields', 'id', '--fields', 'name', self.test_id]
        self._test_show_resource(resource, cmd, self.test_id,
                                 args, ['id', 'name'],
                                 cmd_resource=cmd_resource)

    def test_update_loadbalancer(self):
        """lbaas-loadbalancer-loadbalancer-update myid --name newname."""
        resource = 'loadbalancer'
        cmd_resource = 'lbaas_loadbalancer'
        cmd = lb.UpdateLoadBalancer(test_cli20.MyApp(sys.stdout), None)
        self._test_update_resource(resource, cmd, 'myid',
                                   ['myid', '--name', 'newname'],
                                   {'name': 'newname', },
                                   cmd_resource=cmd_resource)

    def test_delete_loadbalancer(self):
        """lbaas-loadbalancer-loadbalancer-delete my-id."""
        resource = 'loadbalancer'
        cmd_resource = 'lbaas_loadbalancer'
        cmd = lb.DeleteLoadBalancer(test_cli20.MyApp(sys.stdout), None)
        my_id = 'my-id'
        args = [my_id]
        self._test_delete_resource(resource, cmd, my_id, args,
                                   cmd_resource=cmd_resource)


class CLITestV20LbLoadBalancerXML(CLITestV20LbLoadBalancerJSON):
    format = 'xml'
