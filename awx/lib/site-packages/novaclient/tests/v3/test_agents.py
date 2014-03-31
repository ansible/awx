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

from novaclient.tests.v1_1 import test_agents
from novaclient.tests.v3 import fakes
from novaclient.v3 import agents


class AgentsTest(test_agents.AgentsTest):
    def _build_example_update_body(self):
        return {"agent": {
            "url": "/yyy/yyyy/yyyy",
            "version": "8.0",
            "md5hash": "add6bb58e139be103324d04d82d8f546"}}

    def _get_fake_client(self):
        return fakes.FakeClient()

    def _get_agent_type(self):
        return agents.Agent
