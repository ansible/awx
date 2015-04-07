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

from keystoneclient import exceptions
from keystoneclient import fixture
from keystoneclient.tests.unit.v2_0 import utils
from keystoneclient.v2_0 import client
from keystoneclient.v2_0 import tenants
from keystoneclient.v2_0 import users


class TenantTests(utils.TestCase):
    def setUp(self):
        super(TenantTests, self).setUp()

        self.INVIS_ID = uuid.uuid4().hex
        self.DEMO_ID = uuid.uuid4().hex
        self.ADMIN_ID = uuid.uuid4().hex
        self.EXTRAS_ID = uuid.uuid4().hex

        self.TEST_TENANTS = {
            "tenants": {
                "values": [
                    {
                        "enabled": True,
                        "description": "A description change!",
                        "name": "invisible_to_admin",
                        "id": self.INVIS_ID,
                    },
                    {
                        "enabled": True,
                        "description": "None",
                        "name": "demo",
                        "id": self.DEMO_ID,
                    },
                    {
                        "enabled": True,
                        "description": "None",
                        "name": "admin",
                        "id": self.ADMIN_ID,
                    },
                    {
                        "extravalue01": "metadata01",
                        "enabled": True,
                        "description": "For testing extras",
                        "name": "test_extras",
                        "id": self.EXTRAS_ID,
                    }
                ],
                "links": [],
            },
        }

    def test_create(self):
        req_body = {
            "tenant": {
                "name": "tenantX",
                "description": "Like tenant 9, but better.",
                "enabled": True,
                "extravalue01": "metadata01",
            },
        }
        id_ = uuid.uuid4().hex
        resp_body = {
            "tenant": {
                "name": "tenantX",
                "enabled": True,
                "id": id_,
                "description": "Like tenant 9, but better.",
                "extravalue01": "metadata01",
            }
        }
        self.stub_url('POST', ['tenants'], json=resp_body)

        tenant = self.client.tenants.create(
            req_body['tenant']['name'],
            req_body['tenant']['description'],
            req_body['tenant']['enabled'],
            extravalue01=req_body['tenant']['extravalue01'],
            name="don't overwrite priors")
        self.assertIsInstance(tenant, tenants.Tenant)
        self.assertEqual(tenant.id, id_)
        self.assertEqual(tenant.name, "tenantX")
        self.assertEqual(tenant.description, "Like tenant 9, but better.")
        self.assertEqual(tenant.extravalue01, "metadata01")
        self.assertRequestBodyIs(json=req_body)

    def test_duplicate_create(self):
        req_body = {
            "tenant": {
                "name": "tenantX",
                "description": "The duplicate tenant.",
                "enabled": True
            },
        }
        resp_body = {
            "error": {
                "message": "Conflict occurred attempting to store project.",
                "code": 409,
                "title": "Conflict",
            }
        }
        self.stub_url('POST', ['tenants'], status_code=409, json=resp_body)

        def create_duplicate_tenant():
            self.client.tenants.create(req_body['tenant']['name'],
                                       req_body['tenant']['description'],
                                       req_body['tenant']['enabled'])

        self.assertRaises(exceptions.Conflict, create_duplicate_tenant)

    def test_delete(self):
        self.stub_url('DELETE', ['tenants', self.ADMIN_ID], status_code=204)
        self.client.tenants.delete(self.ADMIN_ID)

    def test_get(self):
        resp = {'tenant': self.TEST_TENANTS['tenants']['values'][2]}
        self.stub_url('GET', ['tenants', self.ADMIN_ID], json=resp)

        t = self.client.tenants.get(self.ADMIN_ID)
        self.assertIsInstance(t, tenants.Tenant)
        self.assertEqual(t.id, self.ADMIN_ID)
        self.assertEqual(t.name, 'admin')

    def test_list(self):
        self.stub_url('GET', ['tenants'], json=self.TEST_TENANTS)

        tenant_list = self.client.tenants.list()
        [self.assertIsInstance(t, tenants.Tenant) for t in tenant_list]

    def test_list_limit(self):
        self.stub_url('GET', ['tenants'], json=self.TEST_TENANTS)

        tenant_list = self.client.tenants.list(limit=1)
        self.assertQueryStringIs('limit=1')
        [self.assertIsInstance(t, tenants.Tenant) for t in tenant_list]

    def test_list_marker(self):
        self.stub_url('GET', ['tenants'], json=self.TEST_TENANTS)

        tenant_list = self.client.tenants.list(marker=1)
        self.assertQueryStringIs('marker=1')
        [self.assertIsInstance(t, tenants.Tenant) for t in tenant_list]

    def test_list_limit_marker(self):
        self.stub_url('GET', ['tenants'], json=self.TEST_TENANTS)

        tenant_list = self.client.tenants.list(limit=1, marker=1)
        self.assertQueryStringIs('marker=1&limit=1')
        [self.assertIsInstance(t, tenants.Tenant) for t in tenant_list]

    def test_update(self):
        req_body = {
            "tenant": {
                "id": self.EXTRAS_ID,
                "name": "tenantX",
                "description": "I changed you!",
                "enabled": False,
                "extravalue01": "metadataChanged",
                # "extraname": "dontoverwrite!",
            },
        }
        resp_body = {
            "tenant": {
                "name": "tenantX",
                "enabled": False,
                "id": self.EXTRAS_ID,
                "description": "I changed you!",
                "extravalue01": "metadataChanged",
            },
        }

        self.stub_url('POST', ['tenants', self.EXTRAS_ID], json=resp_body)

        tenant = self.client.tenants.update(
            req_body['tenant']['id'],
            req_body['tenant']['name'],
            req_body['tenant']['description'],
            req_body['tenant']['enabled'],
            extravalue01=req_body['tenant']['extravalue01'],
            name="don't overwrite priors")
        self.assertIsInstance(tenant, tenants.Tenant)
        self.assertRequestBodyIs(json=req_body)
        self.assertEqual(tenant.id, self.EXTRAS_ID)
        self.assertEqual(tenant.name, "tenantX")
        self.assertEqual(tenant.description, "I changed you!")
        self.assertFalse(tenant.enabled)
        self.assertEqual(tenant.extravalue01, "metadataChanged")

    def test_update_empty_description(self):
        req_body = {
            "tenant": {
                "id": self.EXTRAS_ID,
                "name": "tenantX",
                "description": "",
                "enabled": False,
            },
        }
        resp_body = {
            "tenant": {
                "name": "tenantX",
                "enabled": False,
                "id": self.EXTRAS_ID,
                "description": "",
            },
        }
        self.stub_url('POST', ['tenants', self.EXTRAS_ID], json=resp_body)

        tenant = self.client.tenants.update(req_body['tenant']['id'],
                                            req_body['tenant']['name'],
                                            req_body['tenant']['description'],
                                            req_body['tenant']['enabled'])
        self.assertIsInstance(tenant, tenants.Tenant)
        self.assertRequestBodyIs(json=req_body)
        self.assertEqual(tenant.id, self.EXTRAS_ID)
        self.assertEqual(tenant.name, "tenantX")
        self.assertEqual(tenant.description, "")
        self.assertFalse(tenant.enabled)

    def test_add_user(self):
        self.stub_url('PUT',
                      ['tenants', self.EXTRAS_ID, 'users', 'foo', 'roles',
                       'OS-KSADM', 'barrr'],
                      status_code=204)

        self.client.tenants.add_user(self.EXTRAS_ID, 'foo', 'barrr')

    def test_remove_user(self):
        self.stub_url('DELETE', ['tenants', self.EXTRAS_ID, 'users',
                                 'foo', 'roles', 'OS-KSADM', 'barrr'],
                      status_code=204)

        self.client.tenants.remove_user(self.EXTRAS_ID, 'foo', 'barrr')

    def test_tenant_add_user(self):
        self.stub_url('PUT', ['tenants', self.EXTRAS_ID, 'users',
                              'foo', 'roles', 'OS-KSADM', 'barrr'],
                      status_code=204)

        req_body = {
            "tenant": {
                "id": self.EXTRAS_ID,
                "name": "tenantX",
                "description": "I changed you!",
                "enabled": False,
            },
        }
        # make tenant object with manager
        tenant = self.client.tenants.resource_class(self.client.tenants,
                                                    req_body['tenant'])
        tenant.add_user('foo', 'barrr')
        self.assertIsInstance(tenant, tenants.Tenant)

    def test_tenant_remove_user(self):
        self.stub_url('DELETE', ['tenants', self.EXTRAS_ID, 'users',
                                 'foo', 'roles', 'OS-KSADM', 'barrr'],
                      status_code=204)

        req_body = {
            "tenant": {
                "id": self.EXTRAS_ID,
                "name": "tenantX",
                "description": "I changed you!",
                "enabled": False,
            },
        }

        # make tenant object with manager
        tenant = self.client.tenants.resource_class(self.client.tenants,
                                                    req_body['tenant'])
        tenant.remove_user('foo', 'barrr')
        self.assertIsInstance(tenant, tenants.Tenant)

    def test_tenant_list_users(self):
        tenant_id = uuid.uuid4().hex
        user_id1 = uuid.uuid4().hex
        user_id2 = uuid.uuid4().hex

        tenant_resp = {
            'tenant': {
                'name': uuid.uuid4().hex,
                'enabled': True,
                'id': tenant_id,
                'description': 'test tenant',
            }
        }

        users_resp = {
            'users': {
                'values': [
                    {
                        'email': uuid.uuid4().hex,
                        'enabled': True,
                        'id': user_id1,
                        'name': uuid.uuid4().hex,
                    },
                    {
                        'email': uuid.uuid4().hex,
                        'enabled': True,
                        'id': user_id2,
                        'name': uuid.uuid4().hex,
                    },
                ]
            }
        }

        self.stub_url('GET', ['tenants', tenant_id], json=tenant_resp)
        self.stub_url('GET',
                      ['tenants', tenant_id, 'users'],
                      json=users_resp)

        tenant = self.client.tenants.get(tenant_id)
        user_objs = tenant.list_users()

        for u in user_objs:
            self.assertIsInstance(u, users.User)

        self.assertEqual(set([user_id1, user_id2]),
                         set([u.id for u in user_objs]))

    def test_list_tenants_use_admin_url(self):
        self.stub_url('GET', ['tenants'], json=self.TEST_TENANTS)

        self.assertEqual(self.TEST_URL, self.client.management_url)

        tenant_list = self.client.tenants.list()
        [self.assertIsInstance(t, tenants.Tenant) for t in tenant_list]

        self.assertEqual(len(self.TEST_TENANTS['tenants']['values']),
                         len(tenant_list))

    def test_list_tenants_fallback_to_auth_url(self):
        new_auth_url = 'http://keystone.test:5000/v2.0'

        token = fixture.V2Token(token_id=self.TEST_TOKEN,
                                user_name=self.TEST_USER,
                                user_id=self.TEST_USER_ID)

        self.stub_auth(base_url=new_auth_url, json=token)
        self.stub_url('GET', ['tenants'], base_url=new_auth_url,
                      json=self.TEST_TENANTS)

        c = client.Client(username=self.TEST_USER,
                          auth_url=new_auth_url,
                          password=uuid.uuid4().hex)

        self.assertIsNone(c.management_url)
        tenant_list = c.tenants.list()
        [self.assertIsInstance(t, tenants.Tenant) for t in tenant_list]

        self.assertEqual(len(self.TEST_TENANTS['tenants']['values']),
                         len(tenant_list))
