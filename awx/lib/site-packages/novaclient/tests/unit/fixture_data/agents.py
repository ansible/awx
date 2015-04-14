# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from novaclient.tests.unit.fixture_data import base


class Fixture(base.Fixture):

    base_url = 'os-agents'

    def setUp(self):
        super(Fixture, self).setUp()

        post_os_agents = {
            'agent': {
                'url': '/xxx/xxx/xxx',
                'hypervisor': 'kvm',
                'md5hash': 'add6bb58e139be103324d04d82d8f546',
                'version': '7.0',
                'architecture': 'x86',
                'os': 'win',
                'id': 1
            }
        }

        self.requests.register_uri('POST', self.url(),
                                   json=post_os_agents,
                                   headers=self.json_headers)

        put_os_agents_1 = {
            "agent": {
                "url": "/yyy/yyyy/yyyy",
                "version": "8.0",
                "md5hash": "add6bb58e139be103324d04d82d8f546",
                'id': 1
            }
        }

        self.requests.register_uri('PUT', self.url(1),
                                   json=put_os_agents_1,
                                   headers=self.json_headers)

        self.requests.register_uri('DELETE', self.url(1),
                                   headers=self.json_headers,
                                   status_code=202)
