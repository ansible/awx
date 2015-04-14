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

from neutronclient.neutron.v2_0.lb import healthmonitor
from neutronclient.tests.unit import test_cli20


class CLITestV20LbHealthmonitorJSON(test_cli20.CLITestV20Base):
    def test_create_healthmonitor_with_mandatory_params(self):
        """lb-healthmonitor-create with mandatory params only."""
        resource = 'health_monitor'
        cmd = healthmonitor.CreateHealthMonitor(test_cli20.MyApp(sys.stdout),
                                                None)
        admin_state_up = False
        delay = '60'
        max_retries = '2'
        timeout = '10'
        type = 'TCP'
        tenant_id = 'my-tenant'
        my_id = 'my-id'
        args = ['--admin-state-down',
                '--delay', delay,
                '--max-retries', max_retries,
                '--timeout', timeout,
                '--type', type,
                '--tenant-id', tenant_id]
        position_names = ['admin_state_up', 'delay', 'max_retries', 'timeout',
                          'type', 'tenant_id']
        position_values = [admin_state_up, delay, max_retries, timeout, type,
                           tenant_id]
        self._test_create_resource(resource, cmd, '', my_id, args,
                                   position_names, position_values)

    def test_create_healthmonitor_with_all_params(self):
        """lb-healthmonitor-create with all params set."""
        resource = 'health_monitor'
        cmd = healthmonitor.CreateHealthMonitor(test_cli20.MyApp(sys.stdout),
                                                None)
        admin_state_up = False
        delay = '60'
        expected_codes = '200-202,204'
        http_method = 'HEAD'
        max_retries = '2'
        timeout = '10'
        type = 'TCP'
        tenant_id = 'my-tenant'
        url_path = '/health'
        my_id = 'my-id'
        args = ['--admin-state-down',
                '--delay', delay,
                '--expected-codes', expected_codes,
                '--http-method', http_method,
                '--max-retries', max_retries,
                '--timeout', timeout,
                '--type', type,
                '--tenant-id', tenant_id,
                '--url-path', url_path]
        position_names = ['admin_state_up', 'delay',
                          'expected_codes', 'http_method',
                          'max_retries', 'timeout',
                          'type', 'tenant_id', 'url_path']
        position_values = [admin_state_up, delay,
                           expected_codes, http_method,
                           max_retries, timeout,
                           type, tenant_id, url_path]
        self._test_create_resource(resource, cmd, '', my_id, args,
                                   position_names, position_values)

    def test_list_healthmonitors(self):
        """lb-healthmonitor-list."""
        resources = "health_monitors"
        cmd = healthmonitor.ListHealthMonitor(test_cli20.MyApp(sys.stdout),
                                              None)
        self._test_list_resources(resources, cmd, True)

    def test_list_healthmonitors_pagination(self):
        """lb-healthmonitor-list."""
        resources = "health_monitors"
        cmd = healthmonitor.ListHealthMonitor(test_cli20.MyApp(sys.stdout),
                                              None)
        self._test_list_resources_with_pagination(resources, cmd)

    def test_list_healthmonitors_sort(self):
        """lb-healthmonitor-list --sort-key name --sort-key id --sort-key asc
        --sort-key desc
        """
        resources = "health_monitors"
        cmd = healthmonitor.ListHealthMonitor(test_cli20.MyApp(sys.stdout),
                                              None)
        self._test_list_resources(resources, cmd,
                                  sort_key=["name", "id"],
                                  sort_dir=["asc", "desc"])

    def test_list_healthmonitors_limit(self):
        """lb-healthmonitor-list -P."""
        resources = "health_monitors"
        cmd = healthmonitor.ListHealthMonitor(test_cli20.MyApp(sys.stdout),
                                              None)
        self._test_list_resources(resources, cmd, page_size=1000)

    def test_show_healthmonitor_id(self):
        """lb-healthmonitor-show test_id."""
        resource = 'health_monitor'
        cmd = healthmonitor.ShowHealthMonitor(test_cli20.MyApp(sys.stdout),
                                              None)
        args = ['--fields', 'id', self.test_id]
        self._test_show_resource(resource, cmd, self.test_id, args, ['id'])

    def test_update_health_monitor(self):
        """lb-healthmonitor-update  myid --name myname --tags a b."""
        resource = 'health_monitor'
        cmd = healthmonitor.UpdateHealthMonitor(test_cli20.MyApp(sys.stdout),
                                                None)
        self._test_update_resource(resource, cmd, 'myid',
                                   ['myid', '--timeout', '5'],
                                   {'timeout': '5', })

    def test_delete_healthmonitor(self):
        """lb-healthmonitor-delete my-id."""
        resource = 'health_monitor'
        cmd = healthmonitor.DeleteHealthMonitor(test_cli20.MyApp(sys.stdout),
                                                None)
        my_id = 'my-id'
        args = [my_id]
        self._test_delete_resource(resource, cmd, my_id, args)

    def test_associate_healthmonitor(self):
        cmd = healthmonitor.AssociateHealthMonitor(
            test_cli20.MyApp(sys.stdout),
            None)
        resource = 'health_monitor'
        health_monitor_id = 'hm-id'
        pool_id = 'p_id'
        args = [health_monitor_id, pool_id]

        self.mox.StubOutWithMock(cmd, "get_client")
        self.mox.StubOutWithMock(self.client.httpclient, "request")
        cmd.get_client().MultipleTimes().AndReturn(self.client)

        body = {resource: {'id': health_monitor_id}}
        result = {resource: {'id': health_monitor_id}, }
        result_str = self.client.serialize(result)

        path = getattr(self.client,
                       "associate_pool_health_monitors_path") % pool_id
        return_tup = (test_cli20.MyResp(200), result_str)
        self.client.httpclient.request(
            test_cli20.end_url(path), 'POST',
            body=test_cli20.MyComparator(body, self.client),
            headers=mox.ContainsKeyValue(
                'X-Auth-Token', test_cli20.TOKEN)).AndReturn(return_tup)
        self.mox.ReplayAll()
        cmd_parser = cmd.get_parser('test_' + resource)
        parsed_args = cmd_parser.parse_args(args)
        cmd.run(parsed_args)
        self.mox.VerifyAll()
        self.mox.UnsetStubs()

    def test_disassociate_healthmonitor(self):
        cmd = healthmonitor.DisassociateHealthMonitor(
            test_cli20.MyApp(sys.stdout),
            None)
        resource = 'health_monitor'
        health_monitor_id = 'hm-id'
        pool_id = 'p_id'
        args = [health_monitor_id, pool_id]

        self.mox.StubOutWithMock(cmd, "get_client")
        self.mox.StubOutWithMock(self.client.httpclient, "request")
        cmd.get_client().MultipleTimes().AndReturn(self.client)

        path = (getattr(self.client,
                        "disassociate_pool_health_monitors_path") %
                {'pool': pool_id, 'health_monitor': health_monitor_id})
        return_tup = (test_cli20.MyResp(204), None)
        self.client.httpclient.request(
            test_cli20.end_url(path), 'DELETE',
            body=None,
            headers=mox.ContainsKeyValue(
                'X-Auth-Token', test_cli20.TOKEN)).AndReturn(return_tup)
        self.mox.ReplayAll()
        cmd_parser = cmd.get_parser('test_' + resource)
        parsed_args = cmd_parser.parse_args(args)
        cmd.run(parsed_args)
        self.mox.VerifyAll()
        self.mox.UnsetStubs()


class CLITestV20LbHealthmonitorXML(CLITestV20LbHealthmonitorJSON):
    format = 'xml'
