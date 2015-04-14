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

from mox3 import mox

from neutronclient.neutron.v2_0.lb import pool
from neutronclient.tests.unit import test_cli20


class CLITestV20LbPoolJSON(test_cli20.CLITestV20Base):

    def test_create_pool_with_mandatory_params(self):
        """lb-pool-create with mandatory params only."""
        resource = 'pool'
        cmd = pool.CreatePool(test_cli20.MyApp(sys.stdout), None)
        name = 'my-name'
        lb_method = 'ROUND_ROBIN'
        protocol = 'HTTP'
        subnet_id = 'subnet-id'
        tenant_id = 'my-tenant'
        my_id = 'my-id'
        args = ['--lb-method', lb_method,
                '--name', name,
                '--protocol', protocol,
                '--subnet-id', subnet_id,
                '--tenant-id', tenant_id]
        position_names = ['admin_state_up', 'lb_method', 'name',
                          'protocol', 'subnet_id', 'tenant_id']
        position_values = [True, lb_method, name,
                           protocol, subnet_id, tenant_id]
        self._test_create_resource(resource, cmd, name, my_id, args,
                                   position_names, position_values)

    def test_create_pool_with_all_params(self):
        """lb-pool-create with all params set."""
        resource = 'pool'
        cmd = pool.CreatePool(test_cli20.MyApp(sys.stdout), None)
        name = 'my-name'
        description = 'my-desc'
        lb_method = 'ROUND_ROBIN'
        protocol = 'HTTP'
        subnet_id = 'subnet-id'
        tenant_id = 'my-tenant'
        my_id = 'my-id'
        provider = 'lbaas'
        args = ['--admin-state-down',
                '--description', description,
                '--lb-method', lb_method,
                '--name', name,
                '--protocol', protocol,
                '--subnet-id', subnet_id,
                '--tenant-id', tenant_id,
                '--provider', provider]
        position_names = ['admin_state_up', 'description', 'lb_method', 'name',
                          'protocol', 'subnet_id', 'tenant_id', 'provider']
        position_values = [False, description, lb_method, name,
                           protocol, subnet_id, tenant_id, provider]
        self._test_create_resource(resource, cmd, name, my_id, args,
                                   position_names, position_values)

    def test_list_pools(self):
        """lb-pool-list."""
        resources = "pools"
        cmd = pool.ListPool(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd, True)

    def test_list_pools_pagination(self):
        """lb-pool-list."""
        resources = "pools"
        cmd = pool.ListPool(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources_with_pagination(resources, cmd)

    def test_list_pools_sort(self):
        """lb-pool-list --sort-key name --sort-key id --sort-key asc
        --sort-key desc
        """
        resources = "pools"
        cmd = pool.ListPool(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd,
                                  sort_key=["name", "id"],
                                  sort_dir=["asc", "desc"])

    def test_list_pools_limit(self):
        """lb-pool-list -P."""
        resources = "pools"
        cmd = pool.ListPool(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd, page_size=1000)

    def test_show_pool_id(self):
        """lb-pool-show test_id."""
        resource = 'pool'
        cmd = pool.ShowPool(test_cli20.MyApp(sys.stdout), None)
        args = ['--fields', 'id', self.test_id]
        self._test_show_resource(resource, cmd, self.test_id, args, ['id'])

    def test_show_pool_id_name(self):
        """lb-pool-show."""
        resource = 'pool'
        cmd = pool.ShowPool(test_cli20.MyApp(sys.stdout), None)
        args = ['--fields', 'id', '--fields', 'name', self.test_id]
        self._test_show_resource(resource, cmd, self.test_id,
                                 args, ['id', 'name'])

    def test_update_pool(self):
        """lb-pool-update myid --name newname --tags a b."""
        resource = 'pool'
        cmd = pool.UpdatePool(test_cli20.MyApp(sys.stdout), None)
        self._test_update_resource(resource, cmd, 'myid',
                                   ['myid', '--name', 'newname'],
                                   {'name': 'newname', })

    def test_delete_pool(self):
        """lb-pool-delete my-id."""
        resource = 'pool'
        cmd = pool.DeletePool(test_cli20.MyApp(sys.stdout), None)
        my_id = 'my-id'
        args = [my_id]
        self._test_delete_resource(resource, cmd, my_id, args)

    def test_retrieve_pool_stats(self):
        """lb-pool-stats test_id."""
        resource = 'pool'
        cmd = pool.RetrievePoolStats(test_cli20.MyApp(sys.stdout), None)
        my_id = self.test_id
        fields = ['bytes_in', 'bytes_out']
        args = ['--fields', 'bytes_in', '--fields', 'bytes_out', my_id]

        self.mox.StubOutWithMock(cmd, "get_client")
        self.mox.StubOutWithMock(self.client.httpclient, "request")
        cmd.get_client().MultipleTimes().AndReturn(self.client)
        query = "&".join(["fields=%s" % field for field in fields])
        expected_res = {'stats': {'bytes_in': '1234', 'bytes_out': '4321'}}
        resstr = self.client.serialize(expected_res)
        path = getattr(self.client, "pool_path_stats")
        return_tup = (test_cli20.MyResp(200), resstr)
        self.client.httpclient.request(
            test_cli20.end_url(path % my_id, query), 'GET',
            body=None,
            headers=mox.ContainsKeyValue(
                'X-Auth-Token', test_cli20.TOKEN)).AndReturn(return_tup)
        self.mox.ReplayAll()

        cmd_parser = cmd.get_parser("test_" + resource)
        parsed_args = cmd_parser.parse_args(args)
        cmd.run(parsed_args)

        self.mox.VerifyAll()
        self.mox.UnsetStubs()
        _str = self.fake_stdout.make_string()
        self.assertIn('bytes_in', _str)
        self.assertIn('bytes_out', _str)


class CLITestV20LbPoolXML(CLITestV20LbPoolJSON):
    format = 'xml'
