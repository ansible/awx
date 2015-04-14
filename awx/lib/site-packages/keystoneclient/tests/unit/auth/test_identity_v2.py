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

import copy
import uuid

from keystoneclient.auth.identity import v2
from keystoneclient import exceptions
from keystoneclient import session
from keystoneclient.tests.unit import utils


class V2IdentityPlugin(utils.TestCase):

    TEST_ROOT_URL = 'http://127.0.0.1:5000/'
    TEST_URL = '%s%s' % (TEST_ROOT_URL, 'v2.0')
    TEST_ROOT_ADMIN_URL = 'http://127.0.0.1:35357/'
    TEST_ADMIN_URL = '%s%s' % (TEST_ROOT_ADMIN_URL, 'v2.0')

    TEST_PASS = 'password'

    TEST_SERVICE_CATALOG = [{
        "endpoints": [{
            "adminURL": "http://cdn.admin-nets.local:8774/v1.0",
            "region": "RegionOne",
            "internalURL": "http://127.0.0.1:8774/v1.0",
            "publicURL": "http://cdn.admin-nets.local:8774/v1.0/"
        }],
        "type": "nova_compat",
        "name": "nova_compat"
    }, {
        "endpoints": [{
            "adminURL": "http://nova/novapi/admin",
            "region": "RegionOne",
            "internalURL": "http://nova/novapi/internal",
            "publicURL": "http://nova/novapi/public"
        }],
        "type": "compute",
        "name": "nova"
    }, {
        "endpoints": [{
            "adminURL": "http://glance/glanceapi/admin",
            "region": "RegionOne",
            "internalURL": "http://glance/glanceapi/internal",
            "publicURL": "http://glance/glanceapi/public"
        }],
        "type": "image",
        "name": "glance"
    }, {
        "endpoints": [{
            "adminURL": TEST_ADMIN_URL,
            "region": "RegionOne",
            "internalURL": "http://127.0.0.1:5000/v2.0",
            "publicURL": "http://127.0.0.1:5000/v2.0"
        }],
        "type": "identity",
        "name": "keystone"
    }, {
        "endpoints": [{
            "adminURL": "http://swift/swiftapi/admin",
            "region": "RegionOne",
            "internalURL": "http://swift/swiftapi/internal",
            "publicURL": "http://swift/swiftapi/public"
        }],
        "type": "object-store",
        "name": "swift"
    }]

    def setUp(self):
        super(V2IdentityPlugin, self).setUp()
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

    def stub_auth(self, **kwargs):
        self.stub_url('POST', ['tokens'], **kwargs)

    def test_authenticate_with_username_password(self):
        self.stub_auth(json=self.TEST_RESPONSE_DICT)
        a = v2.Password(self.TEST_URL, username=self.TEST_USER,
                        password=self.TEST_PASS)
        self.assertIsNone(a.user_id)
        s = session.Session(a)
        self.assertEqual({'X-Auth-Token': self.TEST_TOKEN},
                         s.get_auth_headers())

        req = {'auth': {'passwordCredentials': {'username': self.TEST_USER,
                                                'password': self.TEST_PASS}}}
        self.assertRequestBodyIs(json=req)
        self.assertRequestHeaderEqual('Content-Type', 'application/json')
        self.assertRequestHeaderEqual('Accept', 'application/json')
        self.assertEqual(s.auth.auth_ref.auth_token, self.TEST_TOKEN)

    def test_authenticate_with_user_id_password(self):
        self.stub_auth(json=self.TEST_RESPONSE_DICT)
        a = v2.Password(self.TEST_URL, user_id=self.TEST_USER,
                        password=self.TEST_PASS)
        self.assertIsNone(a.username)
        s = session.Session(a)
        self.assertEqual({'X-Auth-Token': self.TEST_TOKEN},
                         s.get_auth_headers())

        req = {'auth': {'passwordCredentials': {'userId': self.TEST_USER,
                                                'password': self.TEST_PASS}}}
        self.assertRequestBodyIs(json=req)
        self.assertRequestHeaderEqual('Content-Type', 'application/json')
        self.assertRequestHeaderEqual('Accept', 'application/json')
        self.assertEqual(s.auth.auth_ref.auth_token, self.TEST_TOKEN)

    def test_authenticate_with_username_password_scoped(self):
        self.stub_auth(json=self.TEST_RESPONSE_DICT)
        a = v2.Password(self.TEST_URL, username=self.TEST_USER,
                        password=self.TEST_PASS, tenant_id=self.TEST_TENANT_ID)
        self.assertIsNone(a.user_id)
        s = session.Session(a)
        self.assertEqual({'X-Auth-Token': self.TEST_TOKEN},
                         s.get_auth_headers())

        req = {'auth': {'passwordCredentials': {'username': self.TEST_USER,
                                                'password': self.TEST_PASS},
                        'tenantId': self.TEST_TENANT_ID}}
        self.assertRequestBodyIs(json=req)
        self.assertEqual(s.auth.auth_ref.auth_token, self.TEST_TOKEN)

    def test_authenticate_with_user_id_password_scoped(self):
        self.stub_auth(json=self.TEST_RESPONSE_DICT)
        a = v2.Password(self.TEST_URL, user_id=self.TEST_USER,
                        password=self.TEST_PASS, tenant_id=self.TEST_TENANT_ID)
        self.assertIsNone(a.username)
        s = session.Session(a)
        self.assertEqual({'X-Auth-Token': self.TEST_TOKEN},
                         s.get_auth_headers())

        req = {'auth': {'passwordCredentials': {'userId': self.TEST_USER,
                                                'password': self.TEST_PASS},
                        'tenantId': self.TEST_TENANT_ID}}
        self.assertRequestBodyIs(json=req)
        self.assertEqual(s.auth.auth_ref.auth_token, self.TEST_TOKEN)

    def test_authenticate_with_token(self):
        self.stub_auth(json=self.TEST_RESPONSE_DICT)
        a = v2.Token(self.TEST_URL, 'foo')
        s = session.Session(a)
        self.assertEqual({'X-Auth-Token': self.TEST_TOKEN},
                         s.get_auth_headers())

        req = {'auth': {'token': {'id': 'foo'}}}
        self.assertRequestBodyIs(json=req)
        self.assertRequestHeaderEqual('x-Auth-Token', 'foo')
        self.assertRequestHeaderEqual('Content-Type', 'application/json')
        self.assertRequestHeaderEqual('Accept', 'application/json')
        self.assertEqual(s.auth.auth_ref.auth_token, self.TEST_TOKEN)

    def test_with_trust_id(self):
        self.stub_auth(json=self.TEST_RESPONSE_DICT)
        a = v2.Password(self.TEST_URL, username=self.TEST_USER,
                        password=self.TEST_PASS, trust_id='trust')
        s = session.Session(a)
        self.assertEqual({'X-Auth-Token': self.TEST_TOKEN},
                         s.get_auth_headers())

        req = {'auth': {'passwordCredentials': {'username': self.TEST_USER,
                                                'password': self.TEST_PASS},
                        'trust_id': 'trust'}}

        self.assertRequestBodyIs(json=req)
        self.assertEqual(s.auth.auth_ref.auth_token, self.TEST_TOKEN)

    def _do_service_url_test(self, base_url, endpoint_filter):
        self.stub_auth(json=self.TEST_RESPONSE_DICT)
        self.stub_url('GET', ['path'],
                      base_url=base_url,
                      text='SUCCESS', status_code=200)

        a = v2.Password(self.TEST_URL, username=self.TEST_USER,
                        password=self.TEST_PASS)
        s = session.Session(auth=a)

        resp = s.get('/path', endpoint_filter=endpoint_filter)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.requests_mock.last_request.url,
                         base_url + '/path')

    def test_service_url(self):
        endpoint_filter = {'service_type': 'compute',
                           'interface': 'admin',
                           'service_name': 'nova'}
        self._do_service_url_test('http://nova/novapi/admin', endpoint_filter)

    def test_service_url_defaults_to_public(self):
        endpoint_filter = {'service_type': 'compute'}
        self._do_service_url_test('http://nova/novapi/public', endpoint_filter)

    def test_endpoint_filter_without_service_type_fails(self):
        self.stub_auth(json=self.TEST_RESPONSE_DICT)

        a = v2.Password(self.TEST_URL, username=self.TEST_USER,
                        password=self.TEST_PASS)
        s = session.Session(auth=a)

        self.assertRaises(exceptions.EndpointNotFound, s.get, '/path',
                          endpoint_filter={'interface': 'admin'})

    def test_full_url_overrides_endpoint_filter(self):
        self.stub_auth(json=self.TEST_RESPONSE_DICT)
        self.stub_url('GET', [],
                      base_url='http://testurl/',
                      text='SUCCESS', status_code=200)

        a = v2.Password(self.TEST_URL, username=self.TEST_USER,
                        password=self.TEST_PASS)
        s = session.Session(auth=a)

        resp = s.get('http://testurl/',
                     endpoint_filter={'service_type': 'compute'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.text, 'SUCCESS')

    def test_invalid_auth_response_dict(self):
        self.stub_auth(json={'hello': 'world'})

        a = v2.Password(self.TEST_URL, username=self.TEST_USER,
                        password=self.TEST_PASS)
        s = session.Session(auth=a)

        self.assertRaises(exceptions.InvalidResponse, s.get, 'http://any',
                          authenticated=True)

    def test_invalid_auth_response_type(self):
        self.stub_url('POST', ['tokens'], text='testdata')

        a = v2.Password(self.TEST_URL, username=self.TEST_USER,
                        password=self.TEST_PASS)
        s = session.Session(auth=a)

        self.assertRaises(exceptions.InvalidResponse, s.get, 'http://any',
                          authenticated=True)

    def test_invalidate_response(self):
        resp_data1 = copy.deepcopy(self.TEST_RESPONSE_DICT)
        resp_data2 = copy.deepcopy(self.TEST_RESPONSE_DICT)

        resp_data1['access']['token']['id'] = 'token1'
        resp_data2['access']['token']['id'] = 'token2'

        auth_responses = [{'json': resp_data1}, {'json': resp_data2}]
        self.stub_auth(response_list=auth_responses)

        a = v2.Password(self.TEST_URL, username=self.TEST_USER,
                        password=self.TEST_PASS)
        s = session.Session(auth=a)

        self.assertEqual('token1', s.get_token())
        self.assertEqual({'X-Auth-Token': 'token1'}, s.get_auth_headers())

        a.invalidate()
        self.assertEqual('token2', s.get_token())
        self.assertEqual({'X-Auth-Token': 'token2'}, s.get_auth_headers())

    def test_doesnt_log_password(self):
        self.stub_auth(json=self.TEST_RESPONSE_DICT)
        password = uuid.uuid4().hex

        a = v2.Password(self.TEST_URL, username=self.TEST_USER,
                        password=password)
        s = session.Session(auth=a)
        self.assertEqual(self.TEST_TOKEN, s.get_token())
        self.assertEqual({'X-Auth-Token': self.TEST_TOKEN},
                         s.get_auth_headers())
        self.assertNotIn(password, self.logger.output)

    def test_password_with_no_user_id_or_name(self):
        self.assertRaises(TypeError,
                          v2.Password, self.TEST_URL, password=self.TEST_PASS)
