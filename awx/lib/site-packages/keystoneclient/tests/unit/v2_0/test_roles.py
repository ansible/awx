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

import uuid

from keystoneclient.tests.unit.v2_0 import utils
from keystoneclient.v2_0 import roles


class RoleTests(utils.TestCase):
    def setUp(self):
        super(RoleTests, self).setUp()

        self.ADMIN_ROLE_ID = uuid.uuid4().hex
        self.MEMBER_ROLE_ID = uuid.uuid4().hex

        self.TEST_ROLES = {
            "roles": {
                "values": [
                    {
                        "name": "admin",
                        "id": self.ADMIN_ROLE_ID,
                    },
                    {
                        "name": "member",
                        "id": self.MEMBER_ROLE_ID,
                    }
                ],
            },
        }

    def test_create(self):
        req_body = {
            "role": {
                "name": "sysadmin",
            }
        }
        role_id = uuid.uuid4().hex
        resp_body = {
            "role": {
                "name": "sysadmin",
                "id": role_id,
            }
        }
        self.stub_url('POST', ['OS-KSADM', 'roles'], json=resp_body)

        role = self.client.roles.create(req_body['role']['name'])
        self.assertRequestBodyIs(json=req_body)
        self.assertIsInstance(role, roles.Role)
        self.assertEqual(role.id, role_id)
        self.assertEqual(role.name, req_body['role']['name'])

    def test_delete(self):
        self.stub_url('DELETE',
                      ['OS-KSADM', 'roles', self.ADMIN_ROLE_ID],
                      status_code=204)
        self.client.roles.delete(self.ADMIN_ROLE_ID)

    def test_get(self):
        self.stub_url('GET', ['OS-KSADM', 'roles', self.ADMIN_ROLE_ID],
                      json={'role': self.TEST_ROLES['roles']['values'][0]})

        role = self.client.roles.get(self.ADMIN_ROLE_ID)
        self.assertIsInstance(role, roles.Role)
        self.assertEqual(role.id, self.ADMIN_ROLE_ID)
        self.assertEqual(role.name, 'admin')

    def test_list(self):
        self.stub_url('GET', ['OS-KSADM', 'roles'],
                      json=self.TEST_ROLES)

        role_list = self.client.roles.list()
        [self.assertIsInstance(r, roles.Role) for r in role_list]

    def test_roles_for_user(self):
        self.stub_url('GET', ['users', 'foo', 'roles'],
                      json=self.TEST_ROLES)

        role_list = self.client.roles.roles_for_user('foo')
        [self.assertIsInstance(r, roles.Role) for r in role_list]

    def test_roles_for_user_tenant(self):
        self.stub_url('GET', ['tenants', 'barrr', 'users', 'foo',
                              'roles'], json=self.TEST_ROLES)

        role_list = self.client.roles.roles_for_user('foo', 'barrr')
        [self.assertIsInstance(r, roles.Role) for r in role_list]

    def test_add_user_role(self):
        self.stub_url('PUT', ['users', 'foo', 'roles', 'OS-KSADM',
                              'barrr'], status_code=204)

        self.client.roles.add_user_role('foo', 'barrr')

    def test_add_user_role_tenant(self):
        id_ = uuid.uuid4().hex
        self.stub_url('PUT', ['tenants', id_, 'users', 'foo', 'roles',
                              'OS-KSADM', 'barrr'], status_code=204)

        self.client.roles.add_user_role('foo', 'barrr', id_)

    def test_remove_user_role(self):
        self.stub_url('DELETE', ['users', 'foo', 'roles', 'OS-KSADM',
                                 'barrr'], status_code=204)
        self.client.roles.remove_user_role('foo', 'barrr')

    def test_remove_user_role_tenant(self):
        id_ = uuid.uuid4().hex
        self.stub_url('DELETE', ['tenants', id_, 'users', 'foo',
                                 'roles', 'OS-KSADM', 'barrr'],
                      status_code=204)
        self.client.roles.remove_user_role('foo', 'barrr', id_)
