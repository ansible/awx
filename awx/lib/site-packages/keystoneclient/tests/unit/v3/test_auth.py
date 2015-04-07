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

from oslo_serialization import jsonutils

from keystoneclient import exceptions
from keystoneclient.tests.unit.v3 import utils
from keystoneclient.v3 import client


class AuthenticateAgainstKeystoneTests(utils.TestCase):
    def setUp(self):
        super(AuthenticateAgainstKeystoneTests, self).setUp()
        self.TEST_RESPONSE_DICT = {
            "token": {
                "methods": [
                    "token",
                    "password"
                ],

                "expires_at": "2020-01-01T00:00:10.000123Z",
                "project": {
                    "domain": {
                        "id": self.TEST_DOMAIN_ID,
                        "name": self.TEST_DOMAIN_NAME
                    },
                    "id": self.TEST_TENANT_ID,
                    "name": self.TEST_TENANT_NAME
                },
                "user": {
                    "domain": {
                        "id": self.TEST_DOMAIN_ID,
                        "name": self.TEST_DOMAIN_NAME
                    },
                    "id": self.TEST_USER,
                    "name": self.TEST_USER
                },
                "issued_at": "2013-05-29T16:55:21.468960Z",
                "catalog": self.TEST_SERVICE_CATALOG
            },
        }
        self.TEST_REQUEST_BODY = {
            "auth": {
                "identity": {
                    "methods": ["password"],
                    "password": {
                        "user": {
                            "domain": {
                                "name": self.TEST_DOMAIN_NAME
                            },
                            "name": self.TEST_USER,
                            "password": self.TEST_TOKEN
                        }
                    }
                },
                "scope": {
                    "project": {
                        "id": self.TEST_TENANT_ID
                    },
                }
            }
        }
        self.TEST_REQUEST_HEADERS = {
            'Content-Type': 'application/json',
            'User-Agent': 'python-keystoneclient'
        }
        self.TEST_RESPONSE_HEADERS = {
            'X-Subject-Token': self.TEST_TOKEN
        }

    def test_authenticate_success(self):
        TEST_TOKEN = "abcdef"
        ident = self.TEST_REQUEST_BODY['auth']['identity']
        del ident['password']['user']['domain']
        del ident['password']['user']['name']
        ident['password']['user']['id'] = self.TEST_USER

        self.stub_auth(json=self.TEST_RESPONSE_DICT, subject_token=TEST_TOKEN)

        cs = client.Client(user_id=self.TEST_USER,
                           password=self.TEST_TOKEN,
                           project_id=self.TEST_TENANT_ID,
                           auth_url=self.TEST_URL)
        self.assertEqual(cs.auth_token, TEST_TOKEN)
        self.assertRequestBodyIs(json=self.TEST_REQUEST_BODY)

    def test_authenticate_failure(self):
        ident = self.TEST_REQUEST_BODY['auth']['identity']
        ident['password']['user']['password'] = 'bad_key'
        error = {"unauthorized": {"message": "Unauthorized",
                                  "code": "401"}}

        self.stub_auth(status_code=401, json=error)

        # Workaround for issue with assertRaises on python2.6
        # where with assertRaises(exceptions.Unauthorized): doesn't work
        # right
        def client_create_wrapper():
            client.Client(user_domain_name=self.TEST_DOMAIN_NAME,
                          username=self.TEST_USER,
                          password="bad_key",
                          project_id=self.TEST_TENANT_ID,
                          auth_url=self.TEST_URL)

        self.assertRaises(exceptions.Unauthorized, client_create_wrapper)
        self.assertRequestBodyIs(json=self.TEST_REQUEST_BODY)

    def test_auth_redirect(self):
        headers = {'Location': self.TEST_ADMIN_URL + '/auth/tokens'}
        self.stub_auth(status_code=305, text='Use proxy', headers=headers)

        self.stub_auth(json=self.TEST_RESPONSE_DICT,
                       base_url=self.TEST_ADMIN_URL)

        cs = client.Client(user_domain_name=self.TEST_DOMAIN_NAME,
                           username=self.TEST_USER,
                           password=self.TEST_TOKEN,
                           project_id=self.TEST_TENANT_ID,
                           auth_url=self.TEST_URL)

        self.assertEqual(cs.management_url,
                         self.TEST_RESPONSE_DICT["token"]["catalog"][3]
                         ['endpoints'][2]["url"])
        self.assertEqual(cs.auth_token,
                         self.TEST_RESPONSE_HEADERS["X-Subject-Token"])

    def test_authenticate_success_domain_username_password_scoped(self):
        self.stub_auth(json=self.TEST_RESPONSE_DICT)

        cs = client.Client(user_domain_name=self.TEST_DOMAIN_NAME,
                           username=self.TEST_USER,
                           password=self.TEST_TOKEN,
                           project_id=self.TEST_TENANT_ID,
                           auth_url=self.TEST_URL)
        self.assertEqual(cs.management_url,
                         self.TEST_RESPONSE_DICT["token"]["catalog"][3]
                         ['endpoints'][2]["url"])
        self.assertEqual(cs.auth_token,
                         self.TEST_RESPONSE_HEADERS["X-Subject-Token"])

    def test_authenticate_success_userid_password_domain_scoped(self):
        ident = self.TEST_REQUEST_BODY['auth']['identity']
        del ident['password']['user']['domain']
        del ident['password']['user']['name']
        ident['password']['user']['id'] = self.TEST_USER

        scope = self.TEST_REQUEST_BODY['auth']['scope']
        del scope['project']
        scope['domain'] = {}
        scope['domain']['id'] = self.TEST_DOMAIN_ID

        token = self.TEST_RESPONSE_DICT['token']
        del token['project']
        token['domain'] = {}
        token['domain']['id'] = self.TEST_DOMAIN_ID
        token['domain']['name'] = self.TEST_DOMAIN_NAME

        self.stub_auth(json=self.TEST_RESPONSE_DICT)

        cs = client.Client(user_id=self.TEST_USER,
                           password=self.TEST_TOKEN,
                           domain_id=self.TEST_DOMAIN_ID,
                           auth_url=self.TEST_URL)
        self.assertEqual(cs.auth_domain_id,
                         self.TEST_DOMAIN_ID)
        self.assertEqual(cs.management_url,
                         self.TEST_RESPONSE_DICT["token"]["catalog"][3]
                         ['endpoints'][2]["url"])
        self.assertEqual(cs.auth_token,
                         self.TEST_RESPONSE_HEADERS["X-Subject-Token"])
        self.assertRequestBodyIs(json=self.TEST_REQUEST_BODY)

    def test_authenticate_success_userid_password_project_scoped(self):
        ident = self.TEST_REQUEST_BODY['auth']['identity']
        del ident['password']['user']['domain']
        del ident['password']['user']['name']
        ident['password']['user']['id'] = self.TEST_USER

        self.stub_auth(json=self.TEST_RESPONSE_DICT)

        cs = client.Client(user_id=self.TEST_USER,
                           password=self.TEST_TOKEN,
                           project_id=self.TEST_TENANT_ID,
                           auth_url=self.TEST_URL)
        self.assertEqual(cs.auth_tenant_id,
                         self.TEST_TENANT_ID)
        self.assertEqual(cs.management_url,
                         self.TEST_RESPONSE_DICT["token"]["catalog"][3]
                         ['endpoints'][2]["url"])
        self.assertEqual(cs.auth_token,
                         self.TEST_RESPONSE_HEADERS["X-Subject-Token"])
        self.assertRequestBodyIs(json=self.TEST_REQUEST_BODY)

    def test_authenticate_success_password_unscoped(self):
        del self.TEST_RESPONSE_DICT['token']['catalog']
        del self.TEST_REQUEST_BODY['auth']['scope']

        self.stub_auth(json=self.TEST_RESPONSE_DICT)

        cs = client.Client(user_domain_name=self.TEST_DOMAIN_NAME,
                           username=self.TEST_USER,
                           password=self.TEST_TOKEN,
                           auth_url=self.TEST_URL)
        self.assertEqual(cs.auth_token,
                         self.TEST_RESPONSE_HEADERS["X-Subject-Token"])
        self.assertFalse('catalog' in cs.service_catalog.catalog)
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
        body = jsonutils.loads(self.requests_mock.last_request.body)
        self.assertEqual(body['auth']['identity']['token']['id'], fake_token)

        resp, body = cl.get(fake_url)
        self.assertEqual(fake_resp, body)

        token = self.requests_mock.last_request.headers.get('X-Auth-Token')
        self.assertEqual(self.TEST_TOKEN, token)

    def test_authenticate_success_token_domain_scoped(self):
        ident = self.TEST_REQUEST_BODY['auth']['identity']
        del ident['password']
        ident['methods'] = ['token']
        ident['token'] = {}
        ident['token']['id'] = self.TEST_TOKEN

        scope = self.TEST_REQUEST_BODY['auth']['scope']
        del scope['project']
        scope['domain'] = {}
        scope['domain']['id'] = self.TEST_DOMAIN_ID

        token = self.TEST_RESPONSE_DICT['token']
        del token['project']
        token['domain'] = {}
        token['domain']['id'] = self.TEST_DOMAIN_ID
        token['domain']['name'] = self.TEST_DOMAIN_NAME

        self.TEST_REQUEST_HEADERS['X-Auth-Token'] = self.TEST_TOKEN

        self.stub_auth(json=self.TEST_RESPONSE_DICT)

        cs = client.Client(token=self.TEST_TOKEN,
                           domain_id=self.TEST_DOMAIN_ID,
                           auth_url=self.TEST_URL)
        self.assertEqual(cs.auth_domain_id,
                         self.TEST_DOMAIN_ID)
        self.assertEqual(cs.management_url,
                         self.TEST_RESPONSE_DICT["token"]["catalog"][3]
                         ['endpoints'][2]["url"])
        self.assertEqual(cs.auth_token,
                         self.TEST_RESPONSE_HEADERS["X-Subject-Token"])
        self.assertRequestBodyIs(json=self.TEST_REQUEST_BODY)

    def test_authenticate_success_token_project_scoped(self):
        ident = self.TEST_REQUEST_BODY['auth']['identity']
        del ident['password']
        ident['methods'] = ['token']
        ident['token'] = {}
        ident['token']['id'] = self.TEST_TOKEN
        self.TEST_REQUEST_HEADERS['X-Auth-Token'] = self.TEST_TOKEN

        self.stub_auth(json=self.TEST_RESPONSE_DICT)

        cs = client.Client(token=self.TEST_TOKEN,
                           project_id=self.TEST_TENANT_ID,
                           auth_url=self.TEST_URL)
        self.assertEqual(cs.auth_tenant_id,
                         self.TEST_TENANT_ID)
        self.assertEqual(cs.management_url,
                         self.TEST_RESPONSE_DICT["token"]["catalog"][3]
                         ['endpoints'][2]["url"])
        self.assertEqual(cs.auth_token,
                         self.TEST_RESPONSE_HEADERS["X-Subject-Token"])
        self.assertRequestBodyIs(json=self.TEST_REQUEST_BODY)

    def test_authenticate_success_token_unscoped(self):
        ident = self.TEST_REQUEST_BODY['auth']['identity']
        del ident['password']
        ident['methods'] = ['token']
        ident['token'] = {}
        ident['token']['id'] = self.TEST_TOKEN
        del self.TEST_REQUEST_BODY['auth']['scope']
        del self.TEST_RESPONSE_DICT['token']['catalog']
        self.TEST_REQUEST_HEADERS['X-Auth-Token'] = self.TEST_TOKEN

        self.stub_auth(json=self.TEST_RESPONSE_DICT)

        cs = client.Client(token=self.TEST_TOKEN,
                           auth_url=self.TEST_URL)
        self.assertEqual(cs.auth_token,
                         self.TEST_RESPONSE_HEADERS["X-Subject-Token"])
        self.assertFalse('catalog' in cs.service_catalog.catalog)
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
