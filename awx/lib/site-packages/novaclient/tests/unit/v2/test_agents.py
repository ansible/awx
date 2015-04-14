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

from novaclient.tests.unit.fixture_data import agents as data
from novaclient.tests.unit.fixture_data import client
from novaclient.tests.unit import utils
from novaclient.v2 import agents


class AgentsTest(utils.FixturedTestCase):

    data_fixture_class = data.Fixture

    scenarios = [('original', {'client_fixture_class': client.V1}),
                 ('session', {'client_fixture_class': client.SessionV1})]

    def stub_hypervisors(self, hypervisor='kvm'):
        get_os_agents = {
            'agents': [
                {
                    'hypervisor': hypervisor,
                    'os': 'win',
                    'architecture': 'x86',
                    'version': '7.0',
                    'url': 'xxx://xxxx/xxx/xxx',
                    'md5hash': 'add6bb58e139be103324d04d82d8f545',
                    'id': 1
                },
                {
                    'hypervisor': hypervisor,
                    'os': 'linux',
                    'architecture': 'x86',
                    'version': '16.0',
                    'url': 'xxx://xxxx/xxx/xxx1',
                    'md5hash': 'add6bb58e139be103324d04d82d8f546',
                    'id': 2
                },
            ]
        }

        headers = {'Content-Type': 'application/json'}
        self.requests.register_uri('GET', self.data_fixture.url(),
                                   json=get_os_agents,
                                   headers=headers)

    def test_list_agents(self):
        self.stub_hypervisors()
        ags = self.cs.agents.list()
        self.assert_called('GET', '/os-agents')
        for a in ags:
            self.assertIsInstance(a, agents.Agent)
            self.assertEqual('kvm', a.hypervisor)

    def test_list_agents_with_hypervisor(self):
        self.stub_hypervisors('xen')
        ags = self.cs.agents.list('xen')
        self.assert_called('GET', '/os-agents?hypervisor=xen')
        for a in ags:
            self.assertIsInstance(a, agents.Agent)
            self.assertEqual('xen', a.hypervisor)

    def test_agents_create(self):
        ag = self.cs.agents.create('win', 'x86', '7.0',
                                   '/xxx/xxx/xxx',
                                   'add6bb58e139be103324d04d82d8f546',
                                   'xen')
        body = {'agent': {'url': '/xxx/xxx/xxx',
                          'hypervisor': 'xen',
                          'md5hash': 'add6bb58e139be103324d04d82d8f546',
                          'version': '7.0',
                          'architecture': 'x86',
                          'os': 'win'}}
        self.assert_called('POST', '/os-agents', body)
        self.assertEqual(1, ag._info.copy()['id'])

    def test_agents_delete(self):
        self.cs.agents.delete('1')
        self.assert_called('DELETE', '/os-agents/1')

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
        self.assert_called('PUT', '/os-agents/1', body)
        self.assertEqual(1, ag.id)
