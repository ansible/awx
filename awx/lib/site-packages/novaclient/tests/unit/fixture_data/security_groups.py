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

from oslo.serialization import jsonutils

from novaclient.tests.unit import fakes
from novaclient.tests.unit.fixture_data import base


class Fixture(base.Fixture):

    base_url = 'os-security-groups'

    def setUp(self):
        super(Fixture, self).setUp()

        security_group_1 = {
            "name": "test",
            "description": "FAKE_SECURITY_GROUP",
            "tenant_id": "4ffc664c198e435e9853f2538fbcd7a7",
            "id": 1,
            "rules": [
                {
                    "id": 11,
                    "group": {},
                    "ip_protocol": "TCP",
                    "from_port": 22,
                    "to_port": 22,
                    "parent_group_id": 1,
                    "ip_range": {"cidr": "10.0.0.0/8"}
                },
                {
                    "id": 12,
                    "group": {
                        "tenant_id": "272bee4c1e624cd4a72a6b0ea55b4582",
                        "name": "test2"
                    },
                    "ip_protocol": "TCP",
                    "from_port": 222,
                    "to_port": 222,
                    "parent_group_id": 1,
                    "ip_range": {}
                }
            ]
        }

        security_group_2 = {
            "name": "test2",
            "description": "FAKE_SECURITY_GROUP2",
            "tenant_id": "272bee4c1e624cd4a72a6b0ea55b4582",
            "id": 2,
            "rules": []
        }

        get_groups = {'security_groups': [security_group_1, security_group_2]}
        headers = {'Content-Type': 'application/json'}

        self.requests.register_uri('GET', self.url(),
                                   json=get_groups,
                                   headers=headers)

        get_group_1 = {'security_group': security_group_1}
        self.requests.register_uri('GET', self.url(1),
                                   json=get_group_1,
                                   headers=headers)

        self.requests.register_uri('DELETE', self.url(1), status_code=202)

        def post_os_security_groups(request, context):
            body = jsonutils.loads(request.body)
            assert list(body) == ['security_group']
            fakes.assert_has_keys(body['security_group'],
                                  required=['name', 'description'])
            return {'security_group': security_group_1}

        self.requests.register_uri('POST', self.url(),
                                   json=post_os_security_groups,
                                   headers=headers,
                                   status_code=202)

        def put_os_security_groups_1(request, context):
            body = jsonutils.loads(request.body)
            assert list(body) == ['security_group']
            fakes.assert_has_keys(body['security_group'],
                                  required=['name', 'description'])
            return body

        self.requests.register_uri('PUT', self.url(1),
                                   json=put_os_security_groups_1,
                                   headers=headers,
                                   status_code=205)
