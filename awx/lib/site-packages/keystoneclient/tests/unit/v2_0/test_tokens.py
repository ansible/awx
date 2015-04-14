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

from keystoneclient import access
from keystoneclient import exceptions
from keystoneclient import fixture
from keystoneclient.tests.unit.v2_0 import utils
from keystoneclient.v2_0 import client
from keystoneclient.v2_0 import tokens


class TokenTests(utils.TestCase):

    def test_delete(self):
        id_ = uuid.uuid4().hex
        self.stub_url('DELETE', ['tokens', id_], status_code=204)
        self.client.tokens.delete(id_)

    def test_user_password(self):
        token_fixture = fixture.V2Token(user_name=self.TEST_USER)
        self.stub_auth(json=token_fixture)

        password = uuid.uuid4().hex
        token_ref = self.client.tokens.authenticate(username=self.TEST_USER,
                                                    password=password)

        self.assertIsInstance(token_ref, tokens.Token)
        self.assertEqual(token_fixture.token_id, token_ref.id)
        self.assertEqual(token_fixture.expires_str, token_ref.expires)

        req_body = {
            'auth': {
                'passwordCredentials': {
                    'username': self.TEST_USER,
                    'password': password,
                }
            }
        }

        self.assertRequestBodyIs(json=req_body)

    def test_with_token_id(self):
        token_fixture = fixture.V2Token()
        self.stub_auth(json=token_fixture)

        token_id = uuid.uuid4().hex
        token_ref = self.client.tokens.authenticate(token=token_id)

        self.assertIsInstance(token_ref, tokens.Token)
        self.assertEqual(token_fixture.token_id, token_ref.id)
        self.assertEqual(token_fixture.expires_str, token_ref.expires)

        req_body = {
            'auth': {
                'token': {
                    'id': token_id,
                }
            }
        }

        self.assertRequestBodyIs(json=req_body)

    def test_without_auth_params(self):
        self.assertRaises(ValueError, self.client.tokens.authenticate)
        self.assertRaises(ValueError, self.client.tokens.authenticate,
                          tenant_id=uuid.uuid4().hex)

    def test_with_tenant_id(self):
        token_fixture = fixture.V2Token()
        token_fixture.set_scope()
        self.stub_auth(json=token_fixture)

        token_id = uuid.uuid4().hex
        tenant_id = uuid.uuid4().hex
        token_ref = self.client.tokens.authenticate(token=token_id,
                                                    tenant_id=tenant_id)

        self.assertIsInstance(token_ref, tokens.Token)
        self.assertEqual(token_fixture.token_id, token_ref.id)
        self.assertEqual(token_fixture.expires_str, token_ref.expires)

        tenant_data = {'id': token_fixture.tenant_id,
                       'name': token_fixture.tenant_name}
        self.assertEqual(tenant_data, token_ref.tenant)

        req_body = {
            'auth': {
                'token': {
                    'id': token_id,
                },
                'tenantId': tenant_id
            }
        }

        self.assertRequestBodyIs(json=req_body)

    def test_with_tenant_name(self):
        token_fixture = fixture.V2Token()
        token_fixture.set_scope()
        self.stub_auth(json=token_fixture)

        token_id = uuid.uuid4().hex
        tenant_name = uuid.uuid4().hex
        token_ref = self.client.tokens.authenticate(token=token_id,
                                                    tenant_name=tenant_name)

        self.assertIsInstance(token_ref, tokens.Token)
        self.assertEqual(token_fixture.token_id, token_ref.id)
        self.assertEqual(token_fixture.expires_str, token_ref.expires)

        tenant_data = {'id': token_fixture.tenant_id,
                       'name': token_fixture.tenant_name}
        self.assertEqual(tenant_data, token_ref.tenant)

        req_body = {
            'auth': {
                'token': {
                    'id': token_id,
                },
                'tenantName': tenant_name
            }
        }

        self.assertRequestBodyIs(json=req_body)

    def test_authenticate_use_admin_url(self):
        token_fixture = fixture.V2Token()
        token_fixture.set_scope()
        self.stub_auth(json=token_fixture)

        self.assertEqual(self.TEST_URL, self.client.management_url)

        token_ref = self.client.tokens.authenticate(token=uuid.uuid4().hex)
        self.assertIsInstance(token_ref, tokens.Token)
        self.assertEqual(token_fixture.token_id, token_ref.id)
        self.assertEqual(token_fixture.expires_str, token_ref.expires)

    def test_authenticate_fallback_to_auth_url(self):
        new_auth_url = 'http://keystone.test:5000/v2.0'

        token_fixture = fixture.V2Token()
        self.stub_auth(base_url=new_auth_url, json=token_fixture)

        c = client.Client(username=self.TEST_USER,
                          auth_url=new_auth_url,
                          password=uuid.uuid4().hex)

        self.assertIsNone(c.management_url)

        token_ref = c.tokens.authenticate(token=uuid.uuid4().hex)
        self.assertIsInstance(token_ref, tokens.Token)
        self.assertEqual(token_fixture.token_id, token_ref.id)
        self.assertEqual(token_fixture.expires_str, token_ref.expires)

    def test_validate_token(self):
        id_ = uuid.uuid4().hex
        token_fixture = fixture.V2Token(token_id=id_)
        self.stub_url('GET', ['tokens', id_], json=token_fixture)

        token_ref = self.client.tokens.validate(id_)
        self.assertIsInstance(token_ref, tokens.Token)
        self.assertEqual(id_, token_ref.id)

    def test_validate_token_invalid_token(self):
        # If the token is invalid, typically a NotFound is raised.

        id_ = uuid.uuid4().hex
        # The server is expected to return 404 if the token is invalid.
        self.stub_url('GET', ['tokens', id_], status_code=404)
        self.assertRaises(exceptions.NotFound,
                          self.client.tokens.validate, id_)

    def test_validate_token_access_info_with_token_id(self):
        # Can validate a token passing a string token ID.
        token_id = uuid.uuid4().hex
        token_fixture = fixture.V2Token(token_id=token_id)
        self.stub_url('GET', ['tokens', token_id], json=token_fixture)
        access_info = self.client.tokens.validate_access_info(token_id)
        self.assertIsInstance(access_info, access.AccessInfoV2)
        self.assertEqual(token_id, access_info.auth_token)

    def test_validate_token_access_info_with_access_info(self):
        # Can validate a token passing an access info.
        token_id = uuid.uuid4().hex
        token_fixture = fixture.V2Token(token_id=token_id)
        self.stub_url('GET', ['tokens', token_id], json=token_fixture)
        token = access.AccessInfo.factory(body=token_fixture)
        access_info = self.client.tokens.validate_access_info(token)
        self.assertIsInstance(access_info, access.AccessInfoV2)
        self.assertEqual(token_id, access_info.auth_token)

    def test_get_revoked(self):
        sample_revoked_response = {'signed': '-----BEGIN CMS-----\nMIIB...'}
        self.stub_url('GET', ['tokens', 'revoked'],
                      json=sample_revoked_response)
        resp = self.client.tokens.get_revoked()
        self.assertEqual(sample_revoked_response, resp)
