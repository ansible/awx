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

from neutronclient.neutron.v2_0.lb.v2 import pool
from neutronclient.tests.unit import test_cli20


class CLITestV20LbPoolJSON(test_cli20.CLITestV20Base):

    def test_create_pool_with_mandatory_params(self):
        """lbaas-pool-create with mandatory params only."""
        resource = 'pool'
        cmd_resource = 'lbaas_pool'
        cmd = pool.CreatePool(test_cli20.MyApp(sys.stdout), None)
        my_id = 'my-id'
        lb_algorithm = 'ROUND_ROBIN'
        listener = 'listener'
        protocol = 'TCP'
        name = 'my-pool'
        args = ['--lb-algorithm', lb_algorithm, '--protocol', protocol,
                '--listener', listener, name]
        position_names = ['admin_state_up', 'lb_algorithm', 'protocol',
                          'listener_id', 'name']
        position_values = [True, lb_algorithm, protocol, listener, name]
        self._test_create_resource(resource, cmd, '', my_id, args,
                                   position_names, position_values,
                                   cmd_resource=cmd_resource)

    def test_create_pool_with_all_params(self):
        """lbaas-pool-create with all params set."""
        resource = 'pool'
        cmd_resource = 'lbaas_pool'
        cmd = pool.CreatePool(test_cli20.MyApp(sys.stdout), None)
        my_id = 'my-id'
        lb_algorithm = 'ROUND_ROBIN'
        listener = 'listener'
        protocol = 'TCP'
        description = 'description'
        session_persistence_str = 'HTTP_COOKIE:1234'
        session_persistence = {'type': 'HTTP_COOKIE',
                               'cookie_name': '1234'}
        healthmon_id = 'healthmon-id'
        name = 'my-pool'
        args = ['--lb-algorithm', lb_algorithm, '--protocol', protocol,
                '--description', description, '--session-persistence',
                session_persistence_str, '--healthmonitor-id',
                healthmon_id, '--admin-state-down', name,
                '--listener', listener]
        position_names = ['lb_algorithm', 'protocol', 'description',
                          'session_persistence', 'healthmonitor_id',
                          'admin_state_up', 'listener_id', 'name']
        position_values = [lb_algorithm, protocol, description,
                           session_persistence, healthmon_id,
                           False, listener, name]
        self._test_create_resource(resource, cmd, '', my_id, args,
                                   position_names, position_values,
                                   cmd_resource=cmd_resource)

    def test_list_pools(self):
        """lbaas-pool-list."""
        resources = 'pools'
        cmd_resources = 'lbaas_pools'
        cmd = pool.ListPool(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd, True,
                                  cmd_resources=cmd_resources)

    def test_list_pools_pagination(self):
        """lbaas-pool-list with pagination."""
        resources = 'pools'
        cmd_resources = 'lbaas_pools'
        cmd = pool.ListPool(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources_with_pagination(resources, cmd,
                                                  cmd_resources=cmd_resources)

    def test_list_pools_sort(self):
        """lbaas-pool-list --sort-key id --sort-key asc."""
        resources = 'pools'
        cmd_resources = 'lbaas_pools'
        cmd = pool.ListPool(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd, True,
                                  cmd_resources=cmd_resources)

    def test_list_pools_limit(self):
        """lbaas-pool-list -P."""
        resources = 'pools'
        cmd_resources = 'lbaas_pools'
        cmd = pool.ListPool(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd, page_size=1000,
                                  cmd_resources=cmd_resources)

    def test_show_pool_id(self):
        """lbaas-pool-show test_id."""
        resource = 'pool'
        cmd_resource = 'lbaas_pool'
        cmd = pool.ShowPool(test_cli20.MyApp(sys.stdout), None)
        args = ['--fields', 'id', self.test_id]
        self._test_show_resource(resource, cmd, self.test_id, args, ['id'],
                                 cmd_resource=cmd_resource)

    def test_show_pool_id_name(self):
        """lbaas-pool-show."""
        resource = 'pool'
        cmd_resource = 'lbaas_pool'
        cmd = pool.ShowPool(test_cli20.MyApp(sys.stdout), None)
        args = ['--fields', 'id', '--fields', 'name', self.test_id]
        self._test_show_resource(resource, cmd, self.test_id,
                                 args, ['id', 'name'],
                                 cmd_resource=cmd_resource)

    def test_update_pool(self):
        """lbaas-pool-update myid --name newname."""
        resource = 'pool'
        cmd_resource = 'lbaas_pool'
        cmd = pool.UpdatePool(test_cli20.MyApp(sys.stdout), None)
        self._test_update_resource(resource, cmd, 'myid',
                                   ['myid', '--name', 'newname'],
                                   {'name': 'newname', },
                                   cmd_resource=cmd_resource)

    def test_delete_pool(self):
        """lbaas-pool-delete my-id."""
        resource = 'pool'
        cmd_resource = 'lbaas_pool'
        cmd = pool.DeletePool(test_cli20.MyApp(sys.stdout), None)
        my_id = 'my-id'
        args = [my_id]
        self._test_delete_resource(resource, cmd, my_id, args,
                                   cmd_resource=cmd_resource)


class CLITestV20LbPoolXML(CLITestV20LbPoolJSON):
    format = 'xml'
