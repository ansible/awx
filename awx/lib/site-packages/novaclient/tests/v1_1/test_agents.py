# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from novaclient.v1_1 import agents
from novaclient.tests.v1_1 import fakes
from novaclient.tests import utils


cs = fakes.FakeClient()


class AgentsTest(utils.TestCase):

    def test_list_agents(self):
        ags = cs.agents.list()
        cs.assert_called('GET', '/os-agents')
        [self.assertTrue(isinstance(a, agents.Agent)) for a in ags]
        [self.assertEqual(a.hypervisor, 'kvm') for a in ags]

    def test_list_agents_with_hypervisor(self):
        ags = cs.agents.list('xen')
        cs.assert_called('GET', '/os-agents?hypervisor=xen')
        [self.assertTrue(isinstance(a, agents.Agent)) for a in ags]
        [self.assertEqual(a.hypervisor, 'xen') for a in ags]

    def test_agents_create(self):
        ag = cs.agents.create('win', 'x86', '7.0',
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
        cs.assert_called('POST', '/os-agents', body)
        self.assertEqual(1, ag._info.copy()['id'])

    def test_agents_delete(self):
        cs.agents.delete('1')
        cs.assert_called('DELETE', '/os-agents/1')

    def test_agents_modify(self):
        ag = cs.agents.update('1', '8.0',
                              '/yyy/yyyy/yyyy',
                              'add6bb58e139be103324d04d82d8f546')
        body = {"para": {
                       "url": "/yyy/yyyy/yyyy",
                       "version": "8.0",
                       "md5hash": "add6bb58e139be103324d04d82d8f546"}}
        cs.assert_called('PUT', '/os-agents/1', body)
        self.assertEqual(1, ag.id)
