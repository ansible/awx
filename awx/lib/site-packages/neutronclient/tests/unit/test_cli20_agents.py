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

import sys

from oslo.serialization import jsonutils

from neutronclient.neutron.v2_0 import agent
from neutronclient.tests.unit import test_cli20


class CLITestV20Agent(test_cli20.CLITestV20Base):
    def test_list_agents(self):
        contents = {'agents': [{'id': 'myname', 'agent_type': 'mytype',
                                'alive': True}]}
        args = ['-f', 'json']
        resources = "agents"

        cmd = agent.ListAgent(test_cli20.MyApp(sys.stdout), None)
        self._test_list_columns(cmd, resources, contents, args)
        _str = self.fake_stdout.make_string()

        returned_agents = jsonutils.loads(_str)
        self.assertEqual(1, len(returned_agents))
        ag = returned_agents[0]
        self.assertEqual(3, len(ag))
        self.assertIn("alive", ag.keys())

    def test_list_agents_field(self):
        contents = {'agents': [{'alive': True}]}
        args = ['-f', 'json']
        resources = "agents"
        smile = ':-)'

        cmd = agent.ListAgent(test_cli20.MyApp(sys.stdout), None)
        self._test_list_columns(cmd, resources, contents, args)
        _str = self.fake_stdout.make_string()

        returned_agents = jsonutils.loads(_str)
        self.assertEqual(1, len(returned_agents))
        ag = returned_agents[0]
        self.assertEqual(1, len(ag))
        self.assertIn("alive", ag.keys())
        self.assertIn(smile, ag.values())

    def test_update_agent(self):
        """agent-update myid --admin-state-down --description mydescr."""
        resource = 'agent'
        cmd = agent.UpdateAgent(test_cli20.MyApp(sys.stdout), None)
        self._test_update_resource(
            resource, cmd, 'myid',
            ['myid', '--admin-state-down', '--description', 'mydescr'],
            {'description': 'mydescr', 'admin_state_up': False}
        )

    def test_show_agent(self):
        """Show agent: --field id --field binary myid."""
        resource = 'agent'
        cmd = agent.ShowAgent(test_cli20.MyApp(sys.stdout), None)
        args = ['--field', 'id', '--field', 'binary', self.test_id]
        self._test_show_resource(resource, cmd, self.test_id,
                                 args, ['id', 'binary'])

    def test_delete_agent(self):
        """Delete agent: myid."""
        resource = 'agent'
        cmd = agent.DeleteAgent(test_cli20.MyApp(sys.stdout), None)
        myid = 'myid'
        args = [myid]
        self._test_delete_resource(resource, cmd, myid, args)
