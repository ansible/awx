# Copyright 2012 NEC Corporation
# All Rights Reserved
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
#

import json
import logging
import uuid

import fixtures
from oslo.serialization import jsonutils
from requests_mock.contrib import fixture as mock_fixture
import testtools

from keystoneclient.auth.identity import v2 as ks_v2_auth
from keystoneclient.auth.identity import v3 as ks_v3_auth
from keystoneclient import exceptions as ks_exceptions
from keystoneclient import fixture as ks_fixture
from keystoneclient import session

from neutronclient import client
from neutronclient.common import exceptions


USERNAME = 'testuser'
USER_ID = 'testuser_id'
TENANT_NAME = 'testtenant'
TENANT_ID = 'testtenant_id'
PASSWORD = 'password'
ENDPOINT_URL = 'http://localurl'
PUBLIC_ENDPOINT_URL = '%s/public' % ENDPOINT_URL
ADMIN_ENDPOINT_URL = '%s/admin' % ENDPOINT_URL
INTERNAL_ENDPOINT_URL = '%s/internal' % ENDPOINT_URL
ENDPOINT_OVERRIDE = 'http://otherurl'
TOKENID = uuid.uuid4().hex
REGION = 'RegionOne'
NOAUTH = 'noauth'

KS_TOKEN_RESULT = ks_fixture.V2Token()
KS_TOKEN_RESULT.set_scope()
_s = KS_TOKEN_RESULT.add_service('network', 'Neutron Service')
_s.add_endpoint(ENDPOINT_URL, region=REGION)

ENDPOINTS_RESULT = {
    'endpoints': [{
        'type': 'network',
        'name': 'Neutron Service',
        'region': REGION,
        'adminURL': ENDPOINT_URL,
        'internalURL': ENDPOINT_URL,
        'publicURL': ENDPOINT_URL
    }]
}

BASE_URL = "http://keystone.example.com:5000/"

V2_URL = "%sv2.0" % BASE_URL
V3_URL = "%sv3" % BASE_URL

_v2 = ks_fixture.V2Discovery(V2_URL)
_v3 = ks_fixture.V3Discovery(V3_URL)

V3_VERSION_LIST = jsonutils.dumps({'versions': {'values': [_v2, _v3]}})

V2_VERSION_ENTRY = {'version': _v2}
V3_VERSION_ENTRY = {'version': _v3}


def setup_keystone_v2(mrequests):
    v2_token = ks_fixture.V2Token(token_id=TOKENID)
    service = v2_token.add_service('network')
    service.add_endpoint(PUBLIC_ENDPOINT_URL, region=REGION)

    mrequests.register_uri('POST',
                           '%s/tokens' % (V2_URL),
                           json=v2_token)

    auth_session = session.Session()
    auth_plugin = ks_v2_auth.Password(V2_URL, 'xx', 'xx')
    return auth_session, auth_plugin


def setup_keystone_v3(mrequests):
    mrequests.register_uri('GET',
                           V3_URL,
                           json=V3_VERSION_ENTRY)

    v3_token = ks_fixture.V3Token()
    service = v3_token.add_service('network')
    service.add_standard_endpoints(public=PUBLIC_ENDPOINT_URL,
                                   admin=ADMIN_ENDPOINT_URL,
                                   internal=INTERNAL_ENDPOINT_URL,
                                   region=REGION)

    mrequests.register_uri('POST',
                           '%s/auth/tokens' % (V3_URL),
                           text=json.dumps(v3_token),
                           headers={'X-Subject-Token': TOKENID})

    auth_session = session.Session()
    auth_plugin = ks_v3_auth.Password(V3_URL,
                                      username='xx',
                                      user_id='xx',
                                      user_domain_name='xx',
                                      user_domain_id='xx')
    return auth_session, auth_plugin


AUTH_URL = V2_URL


class CLITestAuthNoAuth(testtools.TestCase):

    def setUp(self):
        """Prepare the test environment."""
        super(CLITestAuthNoAuth, self).setUp()

        self.requests = self.useFixture(mock_fixture.Fixture())

        self.client = client.HTTPClient(username=USERNAME,
                                        tenant_name=TENANT_NAME,
                                        password=PASSWORD,
                                        endpoint_url=ENDPOINT_URL,
                                        auth_strategy=NOAUTH,
                                        region_name=REGION)

    def test_get_noauth(self):
        url = ENDPOINT_URL + '/resource'
        self.requests.get(ENDPOINT_URL + '/resource')
        self.client.do_request('/resource', 'GET')
        self.assertEqual(url, self.requests.last_request.url)
        self.assertEqual(self.client.endpoint_url, ENDPOINT_URL)


class CLITestAuthKeystone(testtools.TestCase):

    def setUp(self):
        """Prepare the test environment."""
        super(CLITestAuthKeystone, self).setUp()

        for var in ('http_proxy', 'HTTP_PROXY'):
            self.useFixture(fixtures.EnvironmentVariableFixture(var))

        self.logger = self.useFixture(fixtures.FakeLogger(level=logging.DEBUG))
        self.requests = self.useFixture(mock_fixture.Fixture())

        self.client = client.construct_http_client(
            username=USERNAME,
            tenant_name=TENANT_NAME,
            password=PASSWORD,
            auth_url=AUTH_URL,
            region_name=REGION)

    def test_reused_token_get_auth_info(self):
        """Test that Client.get_auth_info() works even if client was
           instantiated with predefined token.
        """
        token_id = uuid.uuid4().hex
        client_ = client.HTTPClient(username=USERNAME,
                                    tenant_name=TENANT_NAME,
                                    token=token_id,
                                    password=PASSWORD,
                                    auth_url=AUTH_URL,
                                    region_name=REGION)
        expected = {'auth_token': token_id,
                    'auth_tenant_id': None,
                    'auth_user_id': None,
                    'endpoint_url': self.client.endpoint_url}
        self.assertEqual(client_.get_auth_info(), expected)

    def test_get_token(self):
        auth_session, auth_plugin = setup_keystone_v2(self.requests)

        self.client = client.construct_http_client(
            username=USERNAME,
            tenant_name=TENANT_NAME,
            password=PASSWORD,
            auth_url=AUTH_URL,
            region_name=REGION,
            session=auth_session,
            auth=auth_plugin)

        m = self.requests.get(PUBLIC_ENDPOINT_URL + '/resource',
                              request_headers={'X-Auth-Token': TOKENID})
        self.client.do_request('/resource', 'GET')
        self.assertTrue(m.called)

    def test_refresh_token(self):
        token_id = uuid.uuid4().hex
        text = uuid.uuid4().hex
        self.client.auth_token = token_id
        self.client.endpoint_url = ENDPOINT_URL

        res_url = ENDPOINT_URL + '/resource'
        v2_url = AUTH_URL + '/tokens'

        # token_id gives 401, KS_TOKEN_RESULT gives 200
        self.requests.get(res_url,
                          request_headers={'X-Auth-Token': token_id},
                          status_code=401)

        self.requests.get(
            res_url,
            text=text,
            status_code=200,
            request_headers={'X-Auth-Token': KS_TOKEN_RESULT.token_id})

        self.requests.post(v2_url, json=KS_TOKEN_RESULT)

        resp = self.client.do_request('/resource', 'GET')

        self.assertEqual(text, resp[1])
        self.assertEqual(3, len(self.requests.request_history))

        self.assertEqual(res_url, self.requests.request_history[0].url)
        self.assertEqual(v2_url, self.requests.request_history[1].url)
        self.assertEqual(res_url, self.requests.request_history[2].url)

    def test_refresh_token_no_auth_url(self):
        self.client.auth_url = None

        token_id = uuid.uuid4().hex
        self.client.auth_token = token_id
        self.client.endpoint_url = ENDPOINT_URL

        self.requests.get(ENDPOINT_URL + '/resource', status_code=401)
        self.assertRaises(exceptions.NoAuthURLProvided,
                          self.client.do_request,
                          '/resource',
                          'GET')

    def test_get_endpoint_url_with_invalid_auth_url(self):
        # Handle the case when auth_url is not provided
        self.client.auth_url = None
        self.assertRaises(exceptions.NoAuthURLProvided,
                          self.client._get_endpoint_url)

    def test_get_endpoint_url(self):
        token_id = uuid.uuid4().hex
        self.client.auth_token = token_id

        self.requests.get(AUTH_URL + '/tokens/%s/endpoints' % token_id,
                          json=ENDPOINTS_RESULT)
        self.requests.get(ENDPOINT_URL + '/resource')

        self.client.do_request('/resource', 'GET')

        self.assertEqual(token_id,
                         self.requests.last_request.headers['X-Auth-Token'])

    def test_use_given_endpoint_url(self):
        self.client = client.HTTPClient(
            username=USERNAME, tenant_name=TENANT_NAME, password=PASSWORD,
            auth_url=AUTH_URL, region_name=REGION,
            endpoint_url=ENDPOINT_OVERRIDE)
        self.assertEqual(self.client.endpoint_url, ENDPOINT_OVERRIDE)

        token_id = uuid.uuid4().hex
        self.client.auth_token = token_id

        self.requests.get(ENDPOINT_OVERRIDE + '/resource')

        self.client.do_request('/resource', 'GET')

        self.assertEqual(self.client.endpoint_url, ENDPOINT_OVERRIDE)
        self.assertEqual(token_id,
                         self.requests.last_request.headers['X-Auth-Token'])

    def test_get_endpoint_url_other(self):
        self.client = client.HTTPClient(
            username=USERNAME, tenant_name=TENANT_NAME, password=PASSWORD,
            auth_url=AUTH_URL, region_name=REGION, endpoint_type='otherURL')

        token_id = uuid.uuid4().hex
        self.client.auth_token = token_id

        self.requests.get(AUTH_URL + '/tokens/%s/endpoints' % token_id,
                          json=ENDPOINTS_RESULT)

        self.assertRaises(exceptions.EndpointTypeNotFound,
                          self.client.do_request,
                          '/resource',
                          'GET')

    def test_get_endpoint_url_failed(self):
        token_id = uuid.uuid4().hex
        self.client.auth_token = token_id

        self.requests.get(AUTH_URL + '/tokens/%s/endpoints' % token_id,
                          status_code=401)
        self.requests.post(AUTH_URL + '/tokens', json=KS_TOKEN_RESULT)
        m = self.requests.get(ENDPOINT_URL + '/resource')

        self.client.do_request('/resource', 'GET')

        self.assertEqual(KS_TOKEN_RESULT.token_id,
                         m.last_request.headers['X-Auth-Token'])

    def test_endpoint_type(self):
        auth_session, auth_plugin = setup_keystone_v3(self.requests)

        # Test default behavior is to choose public.
        self.client = client.construct_http_client(
            username=USERNAME, tenant_name=TENANT_NAME, password=PASSWORD,
            auth_url=AUTH_URL, region_name=REGION,
            session=auth_session, auth=auth_plugin)

        self.assertEqual(self.client.endpoint_url, PUBLIC_ENDPOINT_URL)

        # Test admin url
        self.client = client.construct_http_client(
            username=USERNAME, tenant_name=TENANT_NAME, password=PASSWORD,
            auth_url=AUTH_URL, region_name=REGION, endpoint_type='adminURL',
            session=auth_session, auth=auth_plugin)

        self.assertEqual(self.client.endpoint_url, ADMIN_ENDPOINT_URL)

        # Test public url
        self.client = client.construct_http_client(
            username=USERNAME, tenant_name=TENANT_NAME, password=PASSWORD,
            auth_url=AUTH_URL, region_name=REGION, endpoint_type='publicURL',
            session=auth_session, auth=auth_plugin)

        self.assertEqual(self.client.endpoint_url, PUBLIC_ENDPOINT_URL)

        # Test internal url
        self.client = client.construct_http_client(
            username=USERNAME, tenant_name=TENANT_NAME, password=PASSWORD,
            auth_url=AUTH_URL, region_name=REGION, endpoint_type='internalURL',
            session=auth_session, auth=auth_plugin)

        self.assertEqual(self.client.endpoint_url, INTERNAL_ENDPOINT_URL)

        # Test url that isn't found in the service catalog
        self.client = client.construct_http_client(
            username=USERNAME, tenant_name=TENANT_NAME, password=PASSWORD,
            auth_url=AUTH_URL, region_name=REGION, endpoint_type='privateURL',
            session=auth_session, auth=auth_plugin)

        self.assertRaises(
            ks_exceptions.EndpointNotFound,
            getattr, self.client, 'endpoint_url')

    def test_strip_credentials_from_log(self):
        m = self.requests.post(AUTH_URL + '/tokens', json=KS_TOKEN_RESULT)
        self.requests.get(ENDPOINT_URL + '/resource')
        self.client.do_request('/resource', 'GET')

        self.assertIn('REDACTED', self.logger.output)
        self.assertNotIn(self.client.password, self.logger.output)

        self.assertNotIn('REDACTED', m.last_request.body)
        self.assertIn(self.client.password, m.last_request.body)


class CLITestAuthKeystoneWithId(CLITestAuthKeystone):

    def setUp(self):
        """Prepare the test environment."""
        super(CLITestAuthKeystoneWithId, self).setUp()
        self.client = client.HTTPClient(user_id=USER_ID,
                                        tenant_id=TENANT_ID,
                                        password=PASSWORD,
                                        auth_url=AUTH_URL,
                                        region_name=REGION)


class CLITestAuthKeystoneWithIdandName(CLITestAuthKeystone):

    def setUp(self):
        """Prepare the test environment."""
        super(CLITestAuthKeystoneWithIdandName, self).setUp()
        self.client = client.HTTPClient(username=USERNAME,
                                        user_id=USER_ID,
                                        tenant_id=TENANT_ID,
                                        tenant_name=TENANT_NAME,
                                        password=PASSWORD,
                                        auth_url=AUTH_URL,
                                        region_name=REGION)


class TestKeystoneClientVersions(testtools.TestCase):

    def setUp(self):
        """Prepare the test environment."""
        super(TestKeystoneClientVersions, self).setUp()
        self.requests = self.useFixture(mock_fixture.Fixture())

    def test_v2_auth(self):
        auth_session, auth_plugin = setup_keystone_v2(self.requests)

        self.client = client.construct_http_client(
            username=USERNAME,
            tenant_name=TENANT_NAME,
            password=PASSWORD,
            auth_url=AUTH_URL,
            region_name=REGION,
            session=auth_session,
            auth=auth_plugin)

        m = self.requests.get(PUBLIC_ENDPOINT_URL + '/resource')

        self.client.do_request('/resource', 'GET')

        self.assertTrue(m.called)

    def test_v3_auth(self):
        auth_session, auth_plugin = setup_keystone_v3(self.requests)

        self.client = client.construct_http_client(
            user_id=USER_ID,
            tenant_id=TENANT_ID,
            password=PASSWORD,
            auth_url=V3_URL,
            region_name=REGION,
            session=auth_session,
            auth=auth_plugin)

        m = self.requests.get(PUBLIC_ENDPOINT_URL + '/resource')

        self.client.do_request('/resource', 'GET')

        self.assertTrue(m.called)
