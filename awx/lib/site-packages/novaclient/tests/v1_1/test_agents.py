# Copyright 2012 IBM Corp.
# All Rights Reserved.
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

from novaclient.tests import utils
from novaclient.tests.v1_1 import fakes
from novaclient.v1_1 import agents


class AgentsTest(utils.TestCase):
    def setUp(self):
        super(AgentsTest, self).setUp()
        self.cs = self._get_fake_client()
        self.agent_type = self._get_agent_type()

    def _get_fake_client(self):
        return fakes.FakeClient()

    def _get_agent_type(self):
        return agents.Agent

    def test_list_agents(self):
        ags = self.cs.agents.list()
        self.cs.assert_called('GET', '/os-agents')
        for a in ags:
            self.assertIsInstance(a, self.agent_type)
            self.assertEqual(a.hypervisor, 'kvm')

    def test_list_agents_with_hypervisor(self):
        ags = self.cs.agents.list('xen')
        self.cs.assert_called('GET', '/os-agents?hypervisor=xen')
        for a in ags:
            self.assertIsInstance(a, self.agent_type)
            self.assertEqual(a.hypervisor, 'xen')

    def test_agents_create(self):
        ag = self.cs.agents.create('win', 'x86', '7.0',
                              '/xxx/xxx/xxx',
                              'add6bb58e139be103324d04d82d8f546',
                              'xen')
        body = {'agent': {
                        'url': '/xxx/xxx/xxx',
                        'hypervisor': 'xen',
                        'md5hash': 'add6bb58e139be103324d04d82d8f546',
                        'version': '7.0',
                        'architecture': 'x86',
                        'os': 'win'}}
        self.cs.assert_called('POST', '/os-agents', body)
        self.assertEqual(1, ag._info.copy()['id'])

    def test_agents_delete(self):
        self.cs.agents.delete('1')
        self.cs.assert_called('DELETE', '/os-agents/1')

    def _build_example_update_body(self):
        return {"para": {
            "url": "/yyy/yyyy/yyyy",
            "version": "8.0",
            "md5hash": "add6bb58e139be103324d04d82d8f546"}}

    def test_agents_modify(self):
        ag = self.cs.agents.update('1', '8.0',
                              '/yyy/yyyy/yyyy',
                              'add6bb58e139be103324d04d82d8f546')
        body = self._build_example_update_body()
        self.cs.assert_called('PUT', '/os-agents/1', body)
        self.assertEqual(1, ag.id)
