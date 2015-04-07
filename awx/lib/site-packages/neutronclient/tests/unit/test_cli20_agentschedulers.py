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
# @author: Oleg Bondarev, Mirantis Inc.
#

import sys

from mox3 import mox

from neutronclient.neutron.v2_0 import agentscheduler
from neutronclient.neutron.v2_0 import network
from neutronclient.tests.unit import test_cli20


AGENT_ID = 'agent_id1'
NETWORK_ID = 'net_id1'
ROUTER_ID = 'router_id1'


class CLITestV20AgentScheduler(test_cli20.CLITestV20Base):
    def _test_add_to_agent(self, resource, cmd, cmd_args, destination,
                           body, result):
        path = ((self.client.agent_path + destination) %
                cmd_args[0])

        self.mox.StubOutWithMock(cmd, "get_client")
        self.mox.StubOutWithMock(self.client.httpclient, "request")
        cmd.get_client().MultipleTimes().AndReturn(self.client)
        result_str = self.client.serialize(result)
        return_tup = (test_cli20.MyResp(200), result_str)

        self.client.httpclient.request(
            test_cli20.end_url(path), 'POST',
            body=test_cli20.MyComparator(body, self.client),
            headers=mox.ContainsKeyValue(
                'X-Auth-Token', test_cli20.TOKEN)).AndReturn(return_tup)
        self.mox.ReplayAll()
        cmd_parser = cmd.get_parser('test_' + resource)
        parsed_args = cmd_parser.parse_args(cmd_args)
        cmd.run(parsed_args)
        self.mox.VerifyAll()
        self.mox.UnsetStubs()

    def _test_remove_from_agent(self, resource, cmd, cmd_args, destination):
        path = ((self.client.agent_path + destination + '/%s') %
                cmd_args)
        self.mox.StubOutWithMock(cmd, "get_client")
        self.mox.StubOutWithMock(self.client.httpclient, "request")
        cmd.get_client().MultipleTimes().AndReturn(self.client)

        return_tup = (test_cli20.MyResp(204), None)
        self.client.httpclient.request(
            test_cli20.end_url(path), 'DELETE',
            body=None,
            headers=mox.ContainsKeyValue(
                'X-Auth-Token', test_cli20.TOKEN)).AndReturn(return_tup)
        self.mox.ReplayAll()
        cmd_parser = cmd.get_parser('test_' + resource)
        parsed_args = cmd_parser.parse_args(cmd_args)
        cmd.run(parsed_args)
        self.mox.VerifyAll()
        self.mox.UnsetStubs()


class CLITestV20DHCPAgentScheduler(CLITestV20AgentScheduler):

    def test_add_network_to_agent(self):
        resource = 'agent'
        cmd = agentscheduler.AddNetworkToDhcpAgent(
            test_cli20.MyApp(sys.stdout), None)
        args = (AGENT_ID, NETWORK_ID)
        body = {'network_id': NETWORK_ID}
        result = {'network_id': 'net_id', }
        self._test_add_to_agent(resource, cmd, args, self.client.DHCP_NETS,
                                body, result)

    def test_remove_network_from_agent(self):
        resource = 'agent'
        cmd = agentscheduler.RemoveNetworkFromDhcpAgent(
            test_cli20.MyApp(sys.stdout), None)
        args = (AGENT_ID, NETWORK_ID)
        self._test_remove_from_agent(resource, cmd, args,
                                     self.client.DHCP_NETS)

    def test_list_networks_on_agent(self):
        resources = 'networks'
        cmd = agentscheduler.ListNetworksOnDhcpAgent(
            test_cli20.MyApp(sys.stdout), None)
        agent_id = 'agent_id1'
        path = ((self.client.agent_path + self.client.DHCP_NETS) %
                agent_id)
        self.mox.StubOutWithMock(network.ListNetwork, "extend_list")
        network.ListNetwork.extend_list(mox.IsA(list), mox.IgnoreArg())
        self._test_list_resources(resources, cmd, base_args=[agent_id],
                                  path=path)

    def test_list_agents_hosting_network(self):
        resources = 'agent'
        cmd = agentscheduler.ListDhcpAgentsHostingNetwork(
            test_cli20.MyApp(sys.stdout), None)
        agent_id = 'agent_id1'
        path = ((self.client.network_path + self.client.DHCP_AGENTS) %
                agent_id)
        contents = {self.id_field: 'myid1', 'alive': True}
        self._test_list_resources(resources, cmd, base_args=[agent_id],
                                  path=path, response_contents=contents)


class CLITestV20L3AgentScheduler(CLITestV20AgentScheduler):

    def test_add_router_to_agent(self):
        resource = 'agent'
        cmd = agentscheduler.AddRouterToL3Agent(
            test_cli20.MyApp(sys.stdout), None)
        args = (AGENT_ID, ROUTER_ID)
        body = {'router_id': ROUTER_ID}
        result = {'network_id': 'net_id', }
        self._test_add_to_agent(resource, cmd, args, self.client.L3_ROUTERS,
                                body, result)

    def test_remove_router_from_agent(self):
        resource = 'agent'
        cmd = agentscheduler.RemoveRouterFromL3Agent(
            test_cli20.MyApp(sys.stdout), None)
        args = (AGENT_ID, ROUTER_ID)
        self._test_remove_from_agent(resource, cmd, args,
                                     self.client.L3_ROUTERS)

    def test_list_routers_on_agent(self):
        resources = 'router'
        cmd = agentscheduler.ListRoutersOnL3Agent(
            test_cli20.MyApp(sys.stdout), None)
        agent_id = 'agent_id1'
        path = ((self.client.agent_path + self.client.L3_ROUTERS) %
                agent_id)
        contents = {self.id_field: 'myid1', 'name': 'my_name'}
        self._test_list_resources(resources, cmd, base_args=[agent_id],
                                  path=path, response_contents=contents)

    def test_list_agents_hosting_router(self):
        resources = 'agent'
        cmd = agentscheduler.ListL3AgentsHostingRouter(
            test_cli20.MyApp(sys.stdout), None)
        agent_id = 'agent_id1'
        path = ((self.client.router_path + self.client.L3_AGENTS) %
                agent_id)
        contents = {self.id_field: 'myid1', 'alive': True}
        self._test_list_resources(resources, cmd, base_args=[agent_id],
                                  path=path, response_contents=contents)


class CLITestV20LBaaSAgentScheduler(test_cli20.CLITestV20Base):

    def test_list_pools_on_agent(self):
        resources = 'pools'
        cmd = agentscheduler.ListPoolsOnLbaasAgent(
            test_cli20.MyApp(sys.stdout), None)
        agent_id = 'agent_id1'
        path = ((self.client.agent_path + self.client.LOADBALANCER_POOLS) %
                agent_id)
        self._test_list_resources(resources, cmd, base_args=[agent_id],
                                  path=path)

    def test_get_lbaas_agent_hosting_pool(self):
        resources = 'agent'
        cmd = agentscheduler.GetLbaasAgentHostingPool(
            test_cli20.MyApp(sys.stdout), None)
        pool_id = 'pool_id1'
        path = ((self.client.pool_path + self.client.LOADBALANCER_AGENT) %
                pool_id)
        contents = {self.id_field: 'myid1', 'alive': True}
        self._test_list_resources(resources, cmd, base_args=[pool_id],
                                  path=path, response_contents=contents)


class CLITestV20LBaaSAgentSchedulerXML(CLITestV20LBaaSAgentScheduler):
    format = 'xml'
