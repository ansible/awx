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

import copy
import datetime

from oslo_serialization import jsonutils
from oslo_utils import timeutils

from keystoneclient import exceptions
from keystoneclient.tests.unit.v2_0 import utils
from keystoneclient.v2_0 import client


class AuthenticateAgainstKeystoneTests(utils.TestCase):
    def setUp(self):
        super(AuthenticateAgainstKeystoneTests, self).setUp()
        self.TEST_RESPONSE_DICT = {
            "access": {
                "token": {
                    "expires": "2020-01-01T00:00:10.000123Z",
                    "id": self.TEST_TOKEN,
                    "tenant": {
                        "id": self.TEST_TENANT_ID
                    },
                },
                "user": {
                    "id": self.TEST_USER
                },
                "serviceCatalog": self.TEST_SERVICE_CATALOG,
            },
        }
        self.TEST_REQUEST_BODY = {
            "auth": {
                "passwordCredentials": {
                    "username": self.TEST_USER,
                    "password": self.TEST_TOKEN,
                },
                "tenantId": self.TEST_TENANT_ID,
            },
        }

    def test_authenticate_success_expired(self):
        resp_a = copy.deepcopy(self.TEST_RESPONSE_DICT)
        resp_b = copy.deepcopy(self.TEST_RESPONSE_DICT)
        headers = {'Content-Type': 'application/json'}

        # Build an expired token
        resp_a['access']['token']['expires'] = (
            (timeutils.utcnow() - datetime.timedelta(1)).isoformat())

        # Build a new response
        TEST_TOKEN = "abcdef"
        resp_b['access']['token']['expires'] = '2020-01-01T00:00:10.000123Z'
        resp_b['access']['token']['id'] = TEST_TOKEN

        # return expired first, and then the new response
        self.stub_auth(response_list=[{'json': resp_a, 'headers': headers},
                                      {'json': resp_b, 'headers': headers}])

        cs = client.Client(tenant_id=self.TEST_TENANT_ID,
                           auth_url=self.TEST_URL,
                           username=self.TEST_USER,
                           password=self.TEST_TOKEN)

        self.assertEqual(cs.management_url,
                         self.TEST_RESPONSE_DICT["access"]["serviceCatalog"][3]
                         ['endpoints'][0]["adminURL"])

        self.assertEqual(cs.auth_token, TEST_TOKEN)
        self.assertRequestBodyIs(json=self.TEST_REQUEST_BODY)

    def test_authenticate_failure(self):
        _auth = 'auth'
        _cred = 'passwordCredentials'
        _pass = 'password'
        self.TEST_REQUEST_BODY[_auth][_cred][_pass] = 'bad_key'
        error = {"unauthorized": {"message": "Unauthorized",
                                  "code": "401"}}

        self.stub_auth(status_code=401, json=error)

        # Workaround for issue with assertRaises on python2.6
        # where with assertRaises(exceptions.Unauthorized): doesn't work
        # right
        def client_create_wrapper():
            client.Client(username=self.TEST_USER,
                          password="bad_key",
                          tenant_id=self.TEST_TENANT_ID,
                          auth_url=self.TEST_URL)

        self.assertRaises(exceptions.Unauthorized, client_create_wrapper)
        self.assertRequestBodyIs(json=self.TEST_REQUEST_BODY)

    def test_auth_redirect(self):
        self.stub_auth(status_code=305, text='Use Proxy',
                       headers={'Location': self.TEST_ADMIN_URL + "/tokens"})

        self.stub_auth(base_url=self.TEST_ADMIN_URL,
                       json=self.TEST_RESPONSE_DICT)

        cs = client.Client(username=self.TEST_USER,
                           password=self.TEST_TOKEN,
                           tenant_id=self.TEST_TENANT_ID,
                           auth_url=self.TEST_URL)

        self.assertEqual(cs.management_url,
                         self.TEST_RESPONSE_DICT["access"]["serviceCatalog"][3]
                         ['endpoints'][0]["adminURL"])
        self.assertEqual(cs.auth_token,
                         self.TEST_RESPONSE_DICT["access"]["token"]["id"])
        self.assertRequestBodyIs(json=self.TEST_REQUEST_BODY)

    def test_authenticate_success_password_scoped(self):
        self.stub_auth(json=self.TEST_RESPONSE_DICT)

        cs = client.Client(username=self.TEST_USER,
                           password=self.TEST_TOKEN,
                           tenant_id=self.TEST_TENANT_ID,
                           auth_url=self.TEST_URL)
        self.assertEqual(cs.management_url,
                         self.TEST_RESPONSE_DICT["access"]["serviceCatalog"][3]
                         ['endpoints'][0]["adminURL"])
        self.assertEqual(cs.auth_token,
                         self.TEST_RESPONSE_DICT["access"]["token"]["id"])
        self.assertRequestBodyIs(json=self.TEST_REQUEST_BODY)

    def test_authenticate_success_password_unscoped(self):
        del self.TEST_RESPONSE_DICT['access']['serviceCatalog']
        del self.TEST_REQUEST_BODY['auth']['tenantId']

        self.stub_auth(json=self.TEST_RESPONSE_DICT)

        cs = client.Client(username=self.TEST_USER,
                           password=self.TEST_TOKEN,
                           auth_url=self.TEST_URL)
        self.assertEqual(cs.auth_token,
                         self.TEST_RESPONSE_DICT["access"]["token"]["id"])
        self.assertFalse('serviceCatalog' in cs.service_catalog.catalog)
        self.assertRequestBodyIs(json=self.TEST_REQUEST_BODY)

    def test_auth_url_token_authentication(self):
        fake_token = 'fake_token'
        fake_url = '/fake-url'
        fake_resp = {'result': True}

        self.stub_auth(json=self.TEST_RESPONSE_DICT)
        self.stub_url('GET', [fake_url], json=fake_resp,
                      base_url=self.TEST_ADMIN_IDENTITY_ENDPOINT)

        cl = client.Client(auth_url=self.TEST_URL,
                           token=fake_token)
        json_body = jsonutils.loads(self.requests_mock.last_request.body)
        self.assertEqual(json_body['auth']['token']['id'], fake_token)

        resp, body = cl.get(fake_url)
        self.assertEqual(fake_resp, body)

        token = self.requests_mock.last_request.headers.get('X-Auth-Token')
        self.assertEqual(self.TEST_TOKEN, token)

    def test_authenticate_success_token_scoped(self):
        del self.TEST_REQUEST_BODY['auth']['passwordCredentials']
        self.TEST_REQUEST_BODY['auth']['token'] = {'id': self.TEST_TOKEN}
        self.stub_auth(json=self.TEST_RESPONSE_DICT)

        cs = client.Client(token=self.TEST_TOKEN,
                           tenant_id=self.TEST_TENANT_ID,
                           auth_url=self.TEST_URL)
        self.assertEqual(cs.management_url,
                         self.TEST_RESPONSE_DICT["access"]["serviceCatalog"][3]
                         ['endpoints'][0]["adminURL"])
        self.assertEqual(cs.auth_token,
                         self.TEST_RESPONSE_DICT["access"]["token"]["id"])
        self.assertRequestBodyIs(json=self.TEST_REQUEST_BODY)

    def test_authenticate_success_token_scoped_trust(self):
        del self.TEST_REQUEST_BODY['auth']['passwordCredentials']
        self.TEST_REQUEST_BODY['auth']['token'] = {'id': self.TEST_TOKEN}
        self.TEST_REQUEST_BODY['auth']['trust_id'] = self.TEST_TRUST_ID
        response = self.TEST_RESPONSE_DICT.copy()
        response['access']['trust'] = {"trustee_user_id": self.TEST_USER,
                                       "id": self.TEST_TRUST_ID}
        self.stub_auth(json=response)

        cs = client.Client(token=self.TEST_TOKEN,
                           tenant_id=self.TEST_TENANT_ID,
                           trust_id=self.TEST_TRUST_ID,
                           auth_url=self.TEST_URL)
        self.assertTrue(cs.auth_ref.trust_scoped)
        self.assertEqual(cs.auth_ref.trust_id, self.TEST_TRUST_ID)
        self.assertEqual(cs.auth_ref.trustee_user_id, self.TEST_USER)
        self.assertRequestBodyIs(json=self.TEST_REQUEST_BODY)

    def test_authenticate_success_token_unscoped(self):
        del self.TEST_REQUEST_BODY['auth']['passwordCredentials']
        del self.TEST_REQUEST_BODY['auth']['tenantId']
        del self.TEST_RESPONSE_DICT['access']['serviceCatalog']
        self.TEST_REQUEST_BODY['auth']['token'] = {'id': self.TEST_TOKEN}

        self.stub_auth(json=self.TEST_RESPONSE_DICT)

        cs = client.Client(token=self.TEST_TOKEN,
                           auth_url=self.TEST_URL)
        self.assertEqual(cs.auth_token,
                         self.TEST_RESPONSE_DICT["access"]["token"]["id"])
        self.assertFalse('serviceCatalog' in cs.service_catalog.catalog)
        self.assertRequestBodyIs(json=self.TEST_REQUEST_BODY)

    def test_allow_override_of_auth_token(self):
        fake_url = '/fake-url'
        fake_token = 'fake_token'
        fake_resp = {'result': True}

        self.stub_auth(json=self.TEST_RESPONSE_DICT)
        self.stub_url('GET', [fake_url], json=fake_resp,
                      base_url=self.TEST_ADMIN_IDENTITY_ENDPOINT)

        cl = client.Client(username='exampleuser',
                           password='password',
                           tenant_name='exampleproject',
                           auth_url=self.TEST_URL)

        self.assertEqual(cl.auth_token, self.TEST_TOKEN)

        # the token returned from the authentication will be used
        resp, body = cl.get(fake_url)
        self.assertEqual(fake_resp, body)

        token = self.requests_mock.last_request.headers.get('X-Auth-Token')
        self.assertEqual(self.TEST_TOKEN, token)

        # then override that token and the new token shall be used
        cl.auth_token = fake_token

        resp, body = cl.get(fake_url)
        self.assertEqual(fake_resp, body)

        token = self.requests_mock.last_request.headers.get('X-Auth-Token')
        self.assertEqual(fake_token, token)

        # if we clear that overridden token then we fall back to the original
        del cl.auth_token

        resp, body = cl.get(fake_url)
        self.assertEqual(fake_resp, body)

        token = self.requests_mock.last_request.headers.get('X-Auth-Token')
        self.assertEqual(self.TEST_TOKEN, token)
