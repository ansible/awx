# Copyright 2012 OpenStack Foundation
#
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

import calendar
import datetime
import json
import os
import shutil
import stat
import tempfile
import time
import uuid

import fixtures
import iso8601
import mock
from oslo_serialization import jsonutils
from oslo_utils import timeutils
from requests_mock.contrib import fixture as mock_fixture
import six
from six.moves.urllib import parse as urlparse
import testresources
import testtools
from testtools import matchers
import webob

from keystoneclient import access
from keystoneclient.common import cms
from keystoneclient import exceptions
from keystoneclient import fixture
from keystoneclient.middleware import auth_token
from keystoneclient.openstack.common import memorycache
from keystoneclient.tests.unit import client_fixtures
from keystoneclient.tests.unit import utils


EXPECTED_V2_DEFAULT_ENV_RESPONSE = {
    'HTTP_X_IDENTITY_STATUS': 'Confirmed',
    'HTTP_X_TENANT_ID': 'tenant_id1',
    'HTTP_X_TENANT_NAME': 'tenant_name1',
    'HTTP_X_USER_ID': 'user_id1',
    'HTTP_X_USER_NAME': 'user_name1',
    'HTTP_X_ROLES': 'role1,role2',
    'HTTP_X_USER': 'user_name1',  # deprecated (diablo-compat)
    'HTTP_X_TENANT': 'tenant_name1',  # deprecated (diablo-compat)
    'HTTP_X_ROLE': 'role1,role2',  # deprecated (diablo-compat)
}


BASE_HOST = 'https://keystone.example.com:1234'
BASE_URI = '%s/testadmin' % BASE_HOST
FAKE_ADMIN_TOKEN_ID = 'admin_token2'
FAKE_ADMIN_TOKEN = jsonutils.dumps(
    {'access': {'token': {'id': FAKE_ADMIN_TOKEN_ID,
                          'expires': '2022-10-03T16:58:01Z'}}})


VERSION_LIST_v2 = jsonutils.dumps(fixture.DiscoveryList(href=BASE_URI,
                                                        v3=False))
VERSION_LIST_v3 = jsonutils.dumps(fixture.DiscoveryList(href=BASE_URI))

ERROR_TOKEN = '7ae290c2a06244c4b41692eb4e9225f2'
MEMCACHED_SERVERS = ['localhost:11211']
MEMCACHED_AVAILABLE = None


def memcached_available():
    """Do a sanity check against memcached.

    Returns ``True`` if the following conditions are met (otherwise, returns
    ``False``):

    - ``python-memcached`` is installed
    - a usable ``memcached`` instance is available via ``MEMCACHED_SERVERS``
    - the client is able to set and get a key/value pair

    """
    global MEMCACHED_AVAILABLE

    if MEMCACHED_AVAILABLE is None:
        try:
            import memcache
            c = memcache.Client(MEMCACHED_SERVERS)
            c.set('ping', 'pong', time=1)
            MEMCACHED_AVAILABLE = c.get('ping') == 'pong'
        except ImportError:
            MEMCACHED_AVAILABLE = False

    return MEMCACHED_AVAILABLE


def cleanup_revoked_file(filename):
    try:
        os.remove(filename)
    except OSError:
        pass


class TimezoneFixture(fixtures.Fixture):
    @staticmethod
    def supported():
        # tzset is only supported on Unix.
        return hasattr(time, 'tzset')

    def __init__(self, new_tz):
        super(TimezoneFixture, self).__init__()
        self.tz = new_tz
        self.old_tz = os.environ.get('TZ')

    def setUp(self):
        super(TimezoneFixture, self).setUp()
        if not self.supported():
            raise NotImplementedError('timezone override is not supported.')
        os.environ['TZ'] = self.tz
        time.tzset()
        self.addCleanup(self.cleanup)

    def cleanup(self):
        if self.old_tz is not None:
            os.environ['TZ'] = self.old_tz
        elif 'TZ' in os.environ:
            del os.environ['TZ']
        time.tzset()


class TimeFixture(fixtures.Fixture):

    def __init__(self, new_time, normalize=True):
        super(TimeFixture, self).__init__()
        if isinstance(new_time, six.string_types):
            new_time = timeutils.parse_isotime(new_time)
        if normalize:
            new_time = timeutils.normalize_time(new_time)
        self.new_time = new_time

    def setUp(self):
        super(TimeFixture, self).setUp()
        timeutils.set_time_override(self.new_time)
        self.addCleanup(timeutils.clear_time_override)


class FakeApp(object):
    """This represents a WSGI app protected by the auth_token middleware."""

    SUCCESS = b'SUCCESS'

    def __init__(self, expected_env=None):
        self.expected_env = dict(EXPECTED_V2_DEFAULT_ENV_RESPONSE)

        if expected_env:
            self.expected_env.update(expected_env)

    def __call__(self, env, start_response):
        for k, v in self.expected_env.items():
            assert env[k] == v, '%s != %s' % (env[k], v)

        resp = webob.Response()
        resp.body = FakeApp.SUCCESS
        return resp(env, start_response)


class v3FakeApp(FakeApp):
    """This represents a v3 WSGI app protected by the auth_token middleware."""

    def __init__(self, expected_env=None):

        # with v3 additions, these are for the DEFAULT TOKEN
        v3_default_env_additions = {
            'HTTP_X_PROJECT_ID': 'tenant_id1',
            'HTTP_X_PROJECT_NAME': 'tenant_name1',
            'HTTP_X_PROJECT_DOMAIN_ID': 'domain_id1',
            'HTTP_X_PROJECT_DOMAIN_NAME': 'domain_name1',
            'HTTP_X_USER_DOMAIN_ID': 'domain_id1',
            'HTTP_X_USER_DOMAIN_NAME': 'domain_name1'
        }

        if expected_env:
            v3_default_env_additions.update(expected_env)

        super(v3FakeApp, self).__init__(v3_default_env_additions)


class BaseAuthTokenMiddlewareTest(testtools.TestCase):
    """Base test class for auth_token middleware.

    All the tests allow for running with auth_token
    configured for receiving v2 or v3 tokens, with the
    choice being made by passing configuration data into
    setUp().

    The base class will, by default, run all the tests
    expecting v2 token formats.  Child classes can override
    this to specify, for instance, v3 format.

    """
    def setUp(self, expected_env=None, auth_version=None, fake_app=None):
        testtools.TestCase.setUp(self)

        self.expected_env = expected_env or dict()
        self.fake_app = fake_app or FakeApp
        self.middleware = None

        self.conf = {
            'identity_uri': 'https://keystone.example.com:1234/testadmin/',
            'signing_dir': client_fixtures.CERTDIR,
            'auth_version': auth_version,
            'auth_uri': 'https://keystone.example.com:1234',
        }

        self.auth_version = auth_version
        self.response_status = None
        self.response_headers = None

        self.requests_mock = self.useFixture(mock_fixture.Fixture())

    def set_middleware(self, expected_env=None, conf=None):
        """Configure the class ready to call the auth_token middleware.

        Set up the various fake items needed to run the middleware.
        Individual tests that need to further refine these can call this
        function to override the class defaults.

        """
        if conf:
            self.conf.update(conf)

        if expected_env:
            self.expected_env.update(expected_env)

        self.middleware = auth_token.AuthProtocol(
            self.fake_app(self.expected_env), self.conf)
        self.middleware._iso8601 = iso8601

        with tempfile.NamedTemporaryFile(dir=self.middleware.signing_dirname,
                                         delete=False) as f:
            pass
        self.middleware.revoked_file_name = f.name

        self.addCleanup(cleanup_revoked_file,
                        self.middleware.revoked_file_name)

        self.middleware.token_revocation_list = jsonutils.dumps(
            {"revoked": [], "extra": "success"})

    def start_fake_response(self, status, headers):
        self.response_status = int(status.split(' ', 1)[0])
        self.response_headers = dict(headers)

    def assertLastPath(self, path):
        if path:
            parts = urlparse.urlparse(self.requests_mock.last_request.url)
            self.assertEqual(path, parts.path)
        else:
            self.assertIsNone(self.requests_mock.last_request)


class MultiStepAuthTokenMiddlewareTest(BaseAuthTokenMiddlewareTest,
                                       testresources.ResourcedTestCase):

    resources = [('examples', client_fixtures.EXAMPLES_RESOURCE)]

    def test_fetch_revocation_list_with_expire(self):
        self.set_middleware()

        # Get a token, then try to retrieve revocation list and get a 401.
        # Get a new token, try to retrieve revocation list and return 200.
        self.requests_mock.post("%s/v2.0/tokens" % BASE_URI,
                                text=FAKE_ADMIN_TOKEN)

        text = self.examples.SIGNED_REVOCATION_LIST
        self.requests_mock.get("%s/v2.0/tokens/revoked" % BASE_URI,
                               response_list=[{'status_code': 401},
                                              {'text': text}])

        fetched_list = jsonutils.loads(self.middleware.fetch_revocation_list())
        self.assertEqual(fetched_list, self.examples.REVOCATION_LIST)

        # Check that 4 requests have been made
        self.assertEqual(len(self.requests_mock.request_history), 4)


class DiabloAuthTokenMiddlewareTest(BaseAuthTokenMiddlewareTest,
                                    testresources.ResourcedTestCase):

    resources = [('examples', client_fixtures.EXAMPLES_RESOURCE)]

    """Auth Token middleware should understand Diablo keystone responses."""
    def setUp(self):
        # pre-diablo only had Tenant ID, which was also the Name
        expected_env = {
            'HTTP_X_TENANT_ID': 'tenant_id1',
            'HTTP_X_TENANT_NAME': 'tenant_id1',
            # now deprecated (diablo-compat)
            'HTTP_X_TENANT': 'tenant_id1',
        }

        super(DiabloAuthTokenMiddlewareTest, self).setUp(
            expected_env=expected_env)

        self.requests_mock.get("%s/" % BASE_URI,
                               text=VERSION_LIST_v2,
                               status_code=300)

        self.requests_mock.post("%s/v2.0/tokens" % BASE_URI,
                                text=FAKE_ADMIN_TOKEN)

        self.token_id = self.examples.VALID_DIABLO_TOKEN
        token_response = self.examples.JSON_TOKEN_RESPONSES[self.token_id]

        url = '%s/v2.0/tokens/%s' % (BASE_URI, self.token_id)
        self.requests_mock.get(url, text=token_response)

        self.set_middleware()

    def test_valid_diablo_response(self):
        req = webob.Request.blank('/')
        req.headers['X-Auth-Token'] = self.token_id
        self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(self.response_status, 200)
        self.assertIn('keystone.token_info', req.environ)


class NoMemcacheAuthToken(BaseAuthTokenMiddlewareTest):
    """These tests will not have the memcache module available."""

    def setUp(self):
        super(NoMemcacheAuthToken, self).setUp()
        self.useFixture(utils.DisableModuleFixture('memcache'))

    def test_nomemcache(self):
        conf = {
            'admin_token': 'admin_token1',
            'auth_host': 'keystone.example.com',
            'auth_port': 1234,
            'memcached_servers': MEMCACHED_SERVERS,
            'auth_uri': 'https://keystone.example.com:1234',
        }

        auth_token.AuthProtocol(FakeApp(), conf)


class CachePoolTest(BaseAuthTokenMiddlewareTest):
    def test_use_cache_from_env(self):
        """If `swift.cache` is set in the environment and `cache` is set in the
        config then the env cache is used.
        """
        env = {'swift.cache': 'CACHE_TEST'}
        conf = {
            'cache': 'swift.cache'
        }
        self.set_middleware(conf=conf)
        self.middleware._token_cache.initialize(env)
        with self.middleware._token_cache._cache_pool.reserve() as cache:
            self.assertEqual(cache, 'CACHE_TEST')

    def test_not_use_cache_from_env(self):
        """If `swift.cache` is set in the environment but `cache` isn't set in
        the config then the env cache isn't used.
        """
        self.set_middleware()
        env = {'swift.cache': 'CACHE_TEST'}
        self.middleware._token_cache.initialize(env)
        with self.middleware._token_cache._cache_pool.reserve() as cache:
            self.assertNotEqual(cache, 'CACHE_TEST')

    def test_multiple_context_managers_share_single_client(self):
        self.set_middleware()
        token_cache = self.middleware._token_cache
        env = {}
        token_cache.initialize(env)

        caches = []

        with token_cache._cache_pool.reserve() as cache:
            caches.append(cache)

        with token_cache._cache_pool.reserve() as cache:
            caches.append(cache)

        self.assertIs(caches[0], caches[1])
        self.assertEqual(set(caches), set(token_cache._cache_pool))

    def test_nested_context_managers_create_multiple_clients(self):
        self.set_middleware()
        env = {}
        self.middleware._token_cache.initialize(env)
        token_cache = self.middleware._token_cache

        with token_cache._cache_pool.reserve() as outer_cache:
            with token_cache._cache_pool.reserve() as inner_cache:
                self.assertNotEqual(outer_cache, inner_cache)

        self.assertEqual(
            set([inner_cache, outer_cache]),
            set(token_cache._cache_pool))


class GeneralAuthTokenMiddlewareTest(BaseAuthTokenMiddlewareTest,
                                     testresources.ResourcedTestCase):
    """These tests are not affected by the token format
    (see CommonAuthTokenMiddlewareTest).
    """

    resources = [('examples', client_fixtures.EXAMPLES_RESOURCE)]

    def test_will_expire_soon(self):
        tenseconds = datetime.datetime.utcnow() + datetime.timedelta(
            seconds=10)
        self.assertTrue(auth_token.will_expire_soon(tenseconds))
        fortyseconds = datetime.datetime.utcnow() + datetime.timedelta(
            seconds=40)
        self.assertFalse(auth_token.will_expire_soon(fortyseconds))

    def test_token_is_v2_accepts_v2(self):
        token = self.examples.UUID_TOKEN_DEFAULT
        token_response = self.examples.TOKEN_RESPONSES[token]
        self.assertTrue(auth_token._token_is_v2(token_response))

    def test_token_is_v2_rejects_v3(self):
        token = self.examples.v3_UUID_TOKEN_DEFAULT
        token_response = self.examples.TOKEN_RESPONSES[token]
        self.assertFalse(auth_token._token_is_v2(token_response))

    def test_token_is_v3_rejects_v2(self):
        token = self.examples.UUID_TOKEN_DEFAULT
        token_response = self.examples.TOKEN_RESPONSES[token]
        self.assertFalse(auth_token._token_is_v3(token_response))

    def test_token_is_v3_accepts_v3(self):
        token = self.examples.v3_UUID_TOKEN_DEFAULT
        token_response = self.examples.TOKEN_RESPONSES[token]
        self.assertTrue(auth_token._token_is_v3(token_response))

    @testtools.skipUnless(memcached_available(), 'memcached not available')
    def test_encrypt_cache_data(self):
        conf = {
            'memcached_servers': MEMCACHED_SERVERS,
            'memcache_security_strategy': 'encrypt',
            'memcache_secret_key': 'mysecret'
        }
        self.set_middleware(conf=conf)
        token = b'my_token'
        some_time_later = timeutils.utcnow() + datetime.timedelta(hours=4)
        expires = timeutils.strtime(some_time_later)
        data = ('this_data', expires)
        token_cache = self.middleware._token_cache
        token_cache.initialize({})
        token_cache._cache_store(token, data)
        self.assertEqual(token_cache._cache_get(token), data[0])

    @testtools.skipUnless(memcached_available(), 'memcached not available')
    def test_sign_cache_data(self):
        conf = {
            'memcached_servers': MEMCACHED_SERVERS,
            'memcache_security_strategy': 'mac',
            'memcache_secret_key': 'mysecret'
        }
        self.set_middleware(conf=conf)
        token = b'my_token'
        some_time_later = timeutils.utcnow() + datetime.timedelta(hours=4)
        expires = timeutils.strtime(some_time_later)
        data = ('this_data', expires)
        token_cache = self.middleware._token_cache
        token_cache.initialize({})
        token_cache._cache_store(token, data)
        self.assertEqual(token_cache._cache_get(token), data[0])

    @testtools.skipUnless(memcached_available(), 'memcached not available')
    def test_no_memcache_protection(self):
        conf = {
            'memcached_servers': MEMCACHED_SERVERS,
            'memcache_secret_key': 'mysecret'
        }
        self.set_middleware(conf=conf)
        token = 'my_token'
        some_time_later = timeutils.utcnow() + datetime.timedelta(hours=4)
        expires = timeutils.strtime(some_time_later)
        data = ('this_data', expires)
        token_cache = self.middleware._token_cache
        token_cache.initialize({})
        token_cache._cache_store(token, data)
        self.assertEqual(token_cache._cache_get(token), data[0])

    def test_assert_valid_memcache_protection_config(self):
        # test missing memcache_secret_key
        conf = {
            'memcached_servers': MEMCACHED_SERVERS,
            'memcache_security_strategy': 'Encrypt'
        }
        self.assertRaises(auth_token.ConfigurationError, self.set_middleware,
                          conf=conf)
        # test invalue memcache_security_strategy
        conf = {
            'memcached_servers': MEMCACHED_SERVERS,
            'memcache_security_strategy': 'whatever'
        }
        self.assertRaises(auth_token.ConfigurationError, self.set_middleware,
                          conf=conf)
        # test missing memcache_secret_key
        conf = {
            'memcached_servers': MEMCACHED_SERVERS,
            'memcache_security_strategy': 'mac'
        }
        self.assertRaises(auth_token.ConfigurationError, self.set_middleware,
                          conf=conf)
        conf = {
            'memcached_servers': MEMCACHED_SERVERS,
            'memcache_security_strategy': 'Encrypt',
            'memcache_secret_key': ''
        }
        self.assertRaises(auth_token.ConfigurationError, self.set_middleware,
                          conf=conf)
        conf = {
            'memcached_servers': MEMCACHED_SERVERS,
            'memcache_security_strategy': 'mAc',
            'memcache_secret_key': ''
        }
        self.assertRaises(auth_token.ConfigurationError, self.set_middleware,
                          conf=conf)

    def test_config_revocation_cache_timeout(self):
        conf = {
            'revocation_cache_time': 24,
            'auth_uri': 'https://keystone.example.com:1234',
        }
        middleware = auth_token.AuthProtocol(self.fake_app, conf)
        self.assertEqual(middleware.token_revocation_list_cache_timeout,
                         datetime.timedelta(seconds=24))

    def test_conf_values_type_convert(self):
        conf = {
            'revocation_cache_time': '24',
            'identity_uri': 'https://keystone.example.com:1234',
            'include_service_catalog': '0',
            'nonexsit_option': '0',
        }

        middleware = auth_token.AuthProtocol(self.fake_app, conf)
        self.assertEqual(datetime.timedelta(seconds=24),
                         middleware.token_revocation_list_cache_timeout)
        self.assertEqual(False, middleware.include_service_catalog)
        self.assertEqual('https://keystone.example.com:1234',
                         middleware.identity_uri)
        self.assertEqual('0', middleware.conf['nonexsit_option'])

    def test_conf_values_type_convert_with_wrong_value(self):
        conf = {
            'include_service_catalog': '123',
        }
        self.assertRaises(auth_token.ConfigurationError,
                          auth_token.AuthProtocol, self.fake_app, conf)


class CommonAuthTokenMiddlewareTest(object):
    """These tests are run once using v2 tokens and again using v3 tokens."""

    def test_init_does_not_call_http(self):
        conf = {
            'revocation_cache_time': 1
        }
        self.set_middleware(conf=conf)
        self.assertLastPath(None)

    def test_init_by_ipv6Addr_auth_host(self):
        del self.conf['identity_uri']
        conf = {
            'auth_host': '2001:2013:1:f101::1',
            'auth_port': 1234,
            'auth_protocol': 'http',
            'auth_uri': None,
        }
        self.set_middleware(conf=conf)
        expected_auth_uri = 'http://[2001:2013:1:f101::1]:1234'
        self.assertEqual(expected_auth_uri, self.middleware.auth_uri)

    def assert_valid_request_200(self, token, with_catalog=True):
        req = webob.Request.blank('/')
        req.headers['X-Auth-Token'] = token
        body = self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(self.response_status, 200)
        if with_catalog:
            self.assertTrue(req.headers.get('X-Service-Catalog'))
        else:
            self.assertNotIn('X-Service-Catalog', req.headers)
        self.assertEqual(body, [FakeApp.SUCCESS])
        self.assertIn('keystone.token_info', req.environ)
        return req

    def test_valid_uuid_request(self):
        for _ in range(2):  # Do it twice because first result was cached.
            token = self.token_dict['uuid_token_default']
            self.assert_valid_request_200(token)
            self.assert_valid_last_url(token)

    def test_valid_uuid_request_with_auth_fragments(self):
        del self.conf['identity_uri']
        self.conf['auth_protocol'] = 'https'
        self.conf['auth_host'] = 'keystone.example.com'
        self.conf['auth_port'] = 1234
        self.conf['auth_admin_prefix'] = '/testadmin'
        self.set_middleware()
        self.assert_valid_request_200(self.token_dict['uuid_token_default'])
        self.assert_valid_last_url(self.token_dict['uuid_token_default'])

    def _test_cache_revoked(self, token, revoked_form=None):
        # When the token is cached and revoked, 401 is returned.
        self.middleware.check_revocations_for_cached = True

        req = webob.Request.blank('/')
        req.headers['X-Auth-Token'] = token

        # Token should be cached as ok after this.
        self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(200, self.response_status)

        # Put it in revocation list.
        self.middleware.token_revocation_list = self.get_revocation_list_json(
            token_ids=[revoked_form or token])
        self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(401, self.response_status)

    def test_cached_revoked_uuid(self):
        # When the UUID token is cached and revoked, 401 is returned.
        self._test_cache_revoked(self.token_dict['uuid_token_default'])

    def test_valid_signed_request(self):
        for _ in range(2):  # Do it twice because first result was cached.
            self.assert_valid_request_200(
                self.token_dict['signed_token_scoped'])
            # ensure that signed requests do not generate HTTP traffic
            self.assertLastPath(None)

    def test_valid_signed_compressed_request(self):
        self.assert_valid_request_200(
            self.token_dict['signed_token_scoped_pkiz'])
        # ensure that signed requests do not generate HTTP traffic
        self.assertLastPath(None)

    def test_revoked_token_receives_401(self):
        self.middleware.token_revocation_list = self.get_revocation_list_json()
        req = webob.Request.blank('/')
        req.headers['X-Auth-Token'] = self.token_dict['revoked_token']
        self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(self.response_status, 401)

    def test_revoked_token_receives_401_sha256(self):
        self.conf['hash_algorithms'] = ['sha256', 'md5']
        self.set_middleware()
        self.middleware.token_revocation_list = (
            self.get_revocation_list_json(mode='sha256'))
        req = webob.Request.blank('/')
        req.headers['X-Auth-Token'] = self.token_dict['revoked_token']
        self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(self.response_status, 401)

    def test_cached_revoked_pki(self):
        # When the PKI token is cached and revoked, 401 is returned.
        token = self.token_dict['signed_token_scoped']
        revoked_form = cms.cms_hash_token(token)
        self._test_cache_revoked(token, revoked_form)

    def test_cached_revoked_pkiz(self):
        # When the PKI token is cached and revoked, 401 is returned.
        token = self.token_dict['signed_token_scoped_pkiz']
        revoked_form = cms.cms_hash_token(token)
        self._test_cache_revoked(token, revoked_form)

    def test_revoked_token_receives_401_md5_secondary(self):
        # When hash_algorithms has 'md5' as the secondary hash and the
        # revocation list contains the md5 hash for a token, that token is
        # considered revoked so returns 401.
        self.conf['hash_algorithms'] = ['sha256', 'md5']
        self.set_middleware()
        self.middleware.token_revocation_list = self.get_revocation_list_json()
        req = webob.Request.blank('/')
        req.headers['X-Auth-Token'] = self.token_dict['revoked_token']
        self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(self.response_status, 401)

    def _test_revoked_hashed_token(self, token_key):
        # If hash_algorithms is set as ['sha256', 'md5'],
        # and check_revocations_for_cached is True,
        # and a token is in the cache because it was successfully validated
        # using the md5 hash, then
        # if the token is in the revocation list by md5 hash, it'll be
        # rejected and auth_token returns 401.
        self.conf['hash_algorithms'] = ['sha256', 'md5']
        self.conf['check_revocations_for_cached'] = True
        self.set_middleware()

        token = self.token_dict[token_key]

        # Put the token in the revocation list.
        token_hashed = cms.cms_hash_token(token)
        self.middleware.token_revocation_list = self.get_revocation_list_json(
            token_ids=[token_hashed])

        # request is using the hashed token, is valid so goes in
        # cache using the given hash.
        req = webob.Request.blank('/')
        req.headers['X-Auth-Token'] = token_hashed
        self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(200, self.response_status)

        # This time use the PKI(Z) token
        req.headers['X-Auth-Token'] = token
        self.middleware(req.environ, self.start_fake_response)

        # Should find the token in the cache and revocation list.
        self.assertEqual(401, self.response_status)

    def test_revoked_hashed_pki_token(self):
        self._test_revoked_hashed_token('signed_token_scoped')

    def test_revoked_hashed_pkiz_token(self):
        self._test_revoked_hashed_token('signed_token_scoped_pkiz')

    def get_revocation_list_json(self, token_ids=None, mode=None):
        if token_ids is None:
            key = 'revoked_token_hash' + (('_' + mode) if mode else '')
            token_ids = [self.token_dict[key]]
        revocation_list = {'revoked': [{'id': x, 'expires': timeutils.utcnow()}
                                       for x in token_ids]}
        return jsonutils.dumps(revocation_list)

    def test_is_signed_token_revoked_returns_false(self):
        # explicitly setting an empty revocation list here to document intent
        self.middleware.token_revocation_list = jsonutils.dumps(
            {"revoked": [], "extra": "success"})
        result = self.middleware.is_signed_token_revoked(
            [self.token_dict['revoked_token_hash']])
        self.assertFalse(result)

    def test_is_signed_token_revoked_returns_true(self):
        self.middleware.token_revocation_list = self.get_revocation_list_json()
        result = self.middleware.is_signed_token_revoked(
            [self.token_dict['revoked_token_hash']])
        self.assertTrue(result)

    def test_is_signed_token_revoked_returns_true_sha256(self):
        self.conf['hash_algorithms'] = ['sha256', 'md5']
        self.set_middleware()
        self.middleware.token_revocation_list = (
            self.get_revocation_list_json(mode='sha256'))
        result = self.middleware.is_signed_token_revoked(
            [self.token_dict['revoked_token_hash_sha256']])
        self.assertTrue(result)

    def test_verify_signed_token_raises_exception_for_revoked_token(self):
        self.middleware.token_revocation_list = self.get_revocation_list_json()
        self.assertRaises(auth_token.InvalidUserToken,
                          self.middleware.verify_signed_token,
                          self.token_dict['revoked_token'],
                          [self.token_dict['revoked_token_hash']])

    def test_verify_signed_token_raises_exception_for_revoked_token_s256(self):
        self.conf['hash_algorithms'] = ['sha256', 'md5']
        self.set_middleware()
        self.middleware.token_revocation_list = (
            self.get_revocation_list_json(mode='sha256'))
        self.assertRaises(auth_token.InvalidUserToken,
                          self.middleware.verify_signed_token,
                          self.token_dict['revoked_token'],
                          [self.token_dict['revoked_token_hash_sha256'],
                           self.token_dict['revoked_token_hash']])

    def test_verify_signed_token_raises_exception_for_revoked_pkiz_token(self):
        self.middleware.token_revocation_list = (
            self.examples.REVOKED_TOKEN_PKIZ_LIST_JSON)
        self.assertRaises(auth_token.InvalidUserToken,
                          self.middleware.verify_pkiz_token,
                          self.token_dict['revoked_token_pkiz'],
                          [self.token_dict['revoked_token_pkiz_hash']])

    def assertIsValidJSON(self, text):
        json.loads(text)

    def test_verify_signed_token_succeeds_for_unrevoked_token(self):
        self.middleware.token_revocation_list = self.get_revocation_list_json()
        text = self.middleware.verify_signed_token(
            self.token_dict['signed_token_scoped'],
            [self.token_dict['signed_token_scoped_hash']])
        self.assertIsValidJSON(text)

    def test_verify_signed_compressed_token_succeeds_for_unrevoked_token(self):
        self.middleware.token_revocation_list = self.get_revocation_list_json()
        text = self.middleware.verify_pkiz_token(
            self.token_dict['signed_token_scoped_pkiz'],
            [self.token_dict['signed_token_scoped_hash']])
        self.assertIsValidJSON(text)

    def test_verify_signed_token_succeeds_for_unrevoked_token_sha256(self):
        self.conf['hash_algorithms'] = ['sha256', 'md5']
        self.set_middleware()
        self.middleware.token_revocation_list = (
            self.get_revocation_list_json(mode='sha256'))
        text = self.middleware.verify_signed_token(
            self.token_dict['signed_token_scoped'],
            [self.token_dict['signed_token_scoped_hash_sha256'],
             self.token_dict['signed_token_scoped_hash']])
        self.assertIsValidJSON(text)

    def test_verify_signing_dir_create_while_missing(self):
        tmp_name = uuid.uuid4().hex
        test_parent_signing_dir = "/tmp/%s" % tmp_name
        self.middleware.signing_dirname = "/tmp/%s/%s" % ((tmp_name,) * 2)
        self.middleware.signing_cert_file_name = (
            "%s/test.pem" % self.middleware.signing_dirname)
        self.middleware.verify_signing_dir()
        # NOTE(wu_wenxiang): Verify if the signing dir was created as expected.
        self.assertTrue(os.path.isdir(self.middleware.signing_dirname))
        self.assertTrue(os.access(self.middleware.signing_dirname, os.W_OK))
        self.assertEqual(os.stat(self.middleware.signing_dirname).st_uid,
                         os.getuid())
        self.assertEqual(
            stat.S_IMODE(os.stat(self.middleware.signing_dirname).st_mode),
            stat.S_IRWXU)
        shutil.rmtree(test_parent_signing_dir)

    def test_get_token_revocation_list_fetched_time_returns_min(self):
        self.middleware.token_revocation_list_fetched_time = None
        self.middleware.revoked_file_name = ''
        self.assertEqual(self.middleware.token_revocation_list_fetched_time,
                         datetime.datetime.min)

    def test_get_token_revocation_list_fetched_time_returns_mtime(self):
        self.middleware.token_revocation_list_fetched_time = None
        mtime = os.path.getmtime(self.middleware.revoked_file_name)
        fetched_time = datetime.datetime.utcfromtimestamp(mtime)
        self.assertEqual(fetched_time,
                         self.middleware.token_revocation_list_fetched_time)

    @testtools.skipUnless(TimezoneFixture.supported(),
                          'TimezoneFixture not supported')
    def test_get_token_revocation_list_fetched_time_returns_utc(self):
        with TimezoneFixture('UTC-1'):
            self.middleware.token_revocation_list = jsonutils.dumps(
                self.examples.REVOCATION_LIST)
            self.middleware.token_revocation_list_fetched_time = None
            fetched_time = self.middleware.token_revocation_list_fetched_time
            self.assertTrue(timeutils.is_soon(fetched_time, 1))

    def test_get_token_revocation_list_fetched_time_returns_value(self):
        expected = self.middleware._token_revocation_list_fetched_time
        self.assertEqual(self.middleware.token_revocation_list_fetched_time,
                         expected)

    def test_get_revocation_list_returns_fetched_list(self):
        # auth_token uses v2 to fetch this, so don't allow the v3
        # tests to override the fake http connection
        self.middleware.token_revocation_list_fetched_time = None
        os.remove(self.middleware.revoked_file_name)
        self.assertEqual(self.middleware.token_revocation_list,
                         self.examples.REVOCATION_LIST)

    def test_get_revocation_list_returns_current_list_from_memory(self):
        self.assertEqual(self.middleware.token_revocation_list,
                         self.middleware._token_revocation_list)

    def test_get_revocation_list_returns_current_list_from_disk(self):
        in_memory_list = self.middleware.token_revocation_list
        self.middleware._token_revocation_list = None
        self.assertEqual(self.middleware.token_revocation_list, in_memory_list)

    def test_invalid_revocation_list_raises_service_error(self):
        self.requests_mock.get('%s/v2.0/tokens/revoked' % BASE_URI, text='{}')

        self.assertRaises(auth_token.ServiceError,
                          self.middleware.fetch_revocation_list)

    def test_fetch_revocation_list(self):
        # auth_token uses v2 to fetch this, so don't allow the v3
        # tests to override the fake http connection
        fetched_list = jsonutils.loads(self.middleware.fetch_revocation_list())
        self.assertEqual(fetched_list, self.examples.REVOCATION_LIST)

    def test_request_invalid_uuid_token(self):
        # remember because we are testing the middleware we stub the connection
        # to the keystone server, but this is not what gets returned
        invalid_uri = "%s/v2.0/tokens/invalid-token" % BASE_URI
        self.requests_mock.get(invalid_uri, text="", status_code=404)

        req = webob.Request.blank('/')
        req.headers['X-Auth-Token'] = 'invalid-token'
        self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(self.response_status, 401)
        self.assertEqual(self.response_headers['WWW-Authenticate'],
                         "Keystone uri='https://keystone.example.com:1234'")

    def test_request_invalid_signed_token(self):
        req = webob.Request.blank('/')
        req.headers['X-Auth-Token'] = self.examples.INVALID_SIGNED_TOKEN
        self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(401, self.response_status)
        self.assertEqual("Keystone uri='https://keystone.example.com:1234'",
                         self.response_headers['WWW-Authenticate'])

    def test_request_invalid_signed_pkiz_token(self):
        req = webob.Request.blank('/')
        req.headers['X-Auth-Token'] = self.examples.INVALID_SIGNED_PKIZ_TOKEN
        self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(401, self.response_status)
        self.assertEqual("Keystone uri='https://keystone.example.com:1234'",
                         self.response_headers['WWW-Authenticate'])

    def test_request_no_token(self):
        req = webob.Request.blank('/')
        self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(self.response_status, 401)
        self.assertEqual(self.response_headers['WWW-Authenticate'],
                         "Keystone uri='https://keystone.example.com:1234'")

    def test_request_no_token_log_message(self):
        class FakeLog(object):
            def __init__(self):
                self.msg = None
                self.debugmsg = None

            def warn(self, msg=None, *args, **kwargs):
                self.msg = msg

            def debug(self, msg=None, *args, **kwargs):
                self.debugmsg = msg

        self.middleware.LOG = FakeLog()
        self.middleware.delay_auth_decision = False
        self.assertRaises(auth_token.InvalidUserToken,
                          self.middleware._get_user_token_from_header, {})
        self.assertIsNotNone(self.middleware.LOG.msg)
        self.assertIsNotNone(self.middleware.LOG.debugmsg)

    def test_request_no_token_http(self):
        req = webob.Request.blank('/', environ={'REQUEST_METHOD': 'HEAD'})
        self.set_middleware()
        body = self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(self.response_status, 401)
        self.assertEqual(self.response_headers['WWW-Authenticate'],
                         "Keystone uri='https://keystone.example.com:1234'")
        self.assertEqual(body, [''])

    def test_request_blank_token(self):
        req = webob.Request.blank('/')
        req.headers['X-Auth-Token'] = ''
        self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(self.response_status, 401)
        self.assertEqual(self.response_headers['WWW-Authenticate'],
                         "Keystone uri='https://keystone.example.com:1234'")

    def _get_cached_token(self, token, mode='md5'):
        token_id = cms.cms_hash_token(token, mode=mode)
        return self.middleware._token_cache._cache_get(token_id)

    def test_memcache(self):
        req = webob.Request.blank('/')
        token = self.token_dict['signed_token_scoped']
        req.headers['X-Auth-Token'] = token
        self.middleware(req.environ, self.start_fake_response)
        self.assertIsNotNone(self._get_cached_token(token))

    def test_expired(self):
        req = webob.Request.blank('/')
        token = self.token_dict['signed_token_scoped_expired']
        req.headers['X-Auth-Token'] = token
        self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(self.response_status, 401)

    def test_memcache_set_invalid_uuid(self):
        invalid_uri = "%s/v2.0/tokens/invalid-token" % BASE_URI
        self.requests_mock.get(invalid_uri, status_code=404)

        req = webob.Request.blank('/')
        token = 'invalid-token'
        req.headers['X-Auth-Token'] = token
        self.middleware(req.environ, self.start_fake_response)
        self.assertRaises(auth_token.InvalidUserToken,
                          self._get_cached_token, token)

    def _test_memcache_set_invalid_signed(self, hash_algorithms=None,
                                          exp_mode='md5'):
        req = webob.Request.blank('/')
        token = self.token_dict['signed_token_scoped_expired']
        req.headers['X-Auth-Token'] = token
        if hash_algorithms:
            self.conf['hash_algorithms'] = hash_algorithms
            self.set_middleware()
        self.middleware(req.environ, self.start_fake_response)
        self.assertRaises(auth_token.InvalidUserToken,
                          self._get_cached_token, token, mode=exp_mode)

    def test_memcache_set_invalid_signed(self):
        self._test_memcache_set_invalid_signed()

    def test_memcache_set_invalid_signed_sha256_md5(self):
        hash_algorithms = ['sha256', 'md5']
        self._test_memcache_set_invalid_signed(hash_algorithms=hash_algorithms,
                                               exp_mode='sha256')

    def test_memcache_set_invalid_signed_sha256(self):
        hash_algorithms = ['sha256']
        self._test_memcache_set_invalid_signed(hash_algorithms=hash_algorithms,
                                               exp_mode='sha256')

    def test_memcache_set_expired(self, extra_conf={}, extra_environ={}):
        token_cache_time = 10
        conf = {
            'token_cache_time': token_cache_time,
            'signing_dir': client_fixtures.CERTDIR,
        }
        conf.update(extra_conf)
        self.set_middleware(conf=conf)
        req = webob.Request.blank('/')
        token = self.token_dict['signed_token_scoped']
        req.headers['X-Auth-Token'] = token
        req.environ.update(extra_environ)

        now = datetime.datetime.utcnow()
        self.useFixture(TimeFixture(now))

        self.middleware(req.environ, self.start_fake_response)
        self.assertIsNotNone(self._get_cached_token(token))

        timeutils.advance_time_seconds(token_cache_time)
        self.assertIsNone(self._get_cached_token(token))

    def test_swift_memcache_set_expired(self):
        extra_conf = {'cache': 'swift.cache'}
        extra_environ = {'swift.cache': memorycache.Client()}
        self.test_memcache_set_expired(extra_conf, extra_environ)

    def test_http_error_not_cached_token(self):
        """Test to don't cache token as invalid on network errors.

        We use UUID tokens since they are the easiest one to reach
        get_http_connection.
        """
        req = webob.Request.blank('/')
        req.headers['X-Auth-Token'] = ERROR_TOKEN
        self.middleware.http_request_max_retries = 0
        self.middleware(req.environ, self.start_fake_response)
        self.assertIsNone(self._get_cached_token(ERROR_TOKEN))
        self.assert_valid_last_url(ERROR_TOKEN)

    def test_http_request_max_retries(self):
        times_retry = 10

        req = webob.Request.blank('/')
        req.headers['X-Auth-Token'] = ERROR_TOKEN

        conf = {'http_request_max_retries': times_retry}
        self.set_middleware(conf=conf)

        with mock.patch('time.sleep') as mock_obj:
            self.middleware(req.environ, self.start_fake_response)

        self.assertEqual(mock_obj.call_count, times_retry)

    def test_nocatalog(self):
        conf = {
            'include_service_catalog': False
        }
        self.set_middleware(conf=conf)
        self.assert_valid_request_200(self.token_dict['uuid_token_default'],
                                      with_catalog=False)

    def assert_kerberos_bind(self, token, bind_level,
                             use_kerberos=True, success=True):
        conf = {
            'enforce_token_bind': bind_level,
            'auth_version': self.auth_version,
        }
        self.set_middleware(conf=conf)

        req = webob.Request.blank('/')
        req.headers['X-Auth-Token'] = token

        if use_kerberos:
            if use_kerberos is True:
                req.environ['REMOTE_USER'] = self.examples.KERBEROS_BIND
            else:
                req.environ['REMOTE_USER'] = use_kerberos

            req.environ['AUTH_TYPE'] = 'Negotiate'

        body = self.middleware(req.environ, self.start_fake_response)

        if success:
            self.assertEqual(self.response_status, 200)
            self.assertEqual(body, [FakeApp.SUCCESS])
            self.assertIn('keystone.token_info', req.environ)
            self.assert_valid_last_url(token)
        else:
            self.assertEqual(self.response_status, 401)
            self.assertEqual(self.response_headers['WWW-Authenticate'],
                             "Keystone uri='https://keystone.example.com:1234'"
                             )

    def test_uuid_bind_token_disabled_with_kerb_user(self):
        for use_kerberos in [True, False]:
            self.assert_kerberos_bind(self.token_dict['uuid_token_bind'],
                                      bind_level='disabled',
                                      use_kerberos=use_kerberos,
                                      success=True)

    def test_uuid_bind_token_disabled_with_incorrect_ticket(self):
        self.assert_kerberos_bind(self.token_dict['uuid_token_bind'],
                                  bind_level='kerberos',
                                  use_kerberos='ronald@MCDONALDS.COM',
                                  success=False)

    def test_uuid_bind_token_permissive_with_kerb_user(self):
        self.assert_kerberos_bind(self.token_dict['uuid_token_bind'],
                                  bind_level='permissive',
                                  use_kerberos=True,
                                  success=True)

    def test_uuid_bind_token_permissive_without_kerb_user(self):
        self.assert_kerberos_bind(self.token_dict['uuid_token_bind'],
                                  bind_level='permissive',
                                  use_kerberos=False,
                                  success=False)

    def test_uuid_bind_token_permissive_with_unknown_bind(self):
        token = self.token_dict['uuid_token_unknown_bind']

        for use_kerberos in [True, False]:
            self.assert_kerberos_bind(token,
                                      bind_level='permissive',
                                      use_kerberos=use_kerberos,
                                      success=True)

    def test_uuid_bind_token_permissive_with_incorrect_ticket(self):
        self.assert_kerberos_bind(self.token_dict['uuid_token_bind'],
                                  bind_level='kerberos',
                                  use_kerberos='ronald@MCDONALDS.COM',
                                  success=False)

    def test_uuid_bind_token_strict_with_kerb_user(self):
        self.assert_kerberos_bind(self.token_dict['uuid_token_bind'],
                                  bind_level='strict',
                                  use_kerberos=True,
                                  success=True)

    def test_uuid_bind_token_strict_with_kerbout_user(self):
        self.assert_kerberos_bind(self.token_dict['uuid_token_bind'],
                                  bind_level='strict',
                                  use_kerberos=False,
                                  success=False)

    def test_uuid_bind_token_strict_with_unknown_bind(self):
        token = self.token_dict['uuid_token_unknown_bind']

        for use_kerberos in [True, False]:
            self.assert_kerberos_bind(token,
                                      bind_level='strict',
                                      use_kerberos=use_kerberos,
                                      success=False)

    def test_uuid_bind_token_required_with_kerb_user(self):
        self.assert_kerberos_bind(self.token_dict['uuid_token_bind'],
                                  bind_level='required',
                                  use_kerberos=True,
                                  success=True)

    def test_uuid_bind_token_required_without_kerb_user(self):
        self.assert_kerberos_bind(self.token_dict['uuid_token_bind'],
                                  bind_level='required',
                                  use_kerberos=False,
                                  success=False)

    def test_uuid_bind_token_required_with_unknown_bind(self):
        token = self.token_dict['uuid_token_unknown_bind']

        for use_kerberos in [True, False]:
            self.assert_kerberos_bind(token,
                                      bind_level='required',
                                      use_kerberos=use_kerberos,
                                      success=False)

    def test_uuid_bind_token_required_without_bind(self):
        for use_kerberos in [True, False]:
            self.assert_kerberos_bind(self.token_dict['uuid_token_default'],
                                      bind_level='required',
                                      use_kerberos=use_kerberos,
                                      success=False)

    def test_uuid_bind_token_named_kerberos_with_kerb_user(self):
        self.assert_kerberos_bind(self.token_dict['uuid_token_bind'],
                                  bind_level='kerberos',
                                  use_kerberos=True,
                                  success=True)

    def test_uuid_bind_token_named_kerberos_without_kerb_user(self):
        self.assert_kerberos_bind(self.token_dict['uuid_token_bind'],
                                  bind_level='kerberos',
                                  use_kerberos=False,
                                  success=False)

    def test_uuid_bind_token_named_kerberos_with_unknown_bind(self):
        token = self.token_dict['uuid_token_unknown_bind']

        for use_kerberos in [True, False]:
            self.assert_kerberos_bind(token,
                                      bind_level='kerberos',
                                      use_kerberos=use_kerberos,
                                      success=False)

    def test_uuid_bind_token_named_kerberos_without_bind(self):
        for use_kerberos in [True, False]:
            self.assert_kerberos_bind(self.token_dict['uuid_token_default'],
                                      bind_level='kerberos',
                                      use_kerberos=use_kerberos,
                                      success=False)

    def test_uuid_bind_token_named_kerberos_with_incorrect_ticket(self):
        self.assert_kerberos_bind(self.token_dict['uuid_token_bind'],
                                  bind_level='kerberos',
                                  use_kerberos='ronald@MCDONALDS.COM',
                                  success=False)

    def test_uuid_bind_token_with_unknown_named_FOO(self):
        token = self.token_dict['uuid_token_bind']

        for use_kerberos in [True, False]:
            self.assert_kerberos_bind(token,
                                      bind_level='FOO',
                                      use_kerberos=use_kerberos,
                                      success=False)


class V2CertDownloadMiddlewareTest(BaseAuthTokenMiddlewareTest,
                                   testresources.ResourcedTestCase):

    resources = [('examples', client_fixtures.EXAMPLES_RESOURCE)]

    def __init__(self, *args, **kwargs):
        super(V2CertDownloadMiddlewareTest, self).__init__(*args, **kwargs)
        self.auth_version = 'v2.0'
        self.fake_app = None
        self.ca_path = '/v2.0/certificates/ca'
        self.signing_path = '/v2.0/certificates/signing'

    def setUp(self):
        super(V2CertDownloadMiddlewareTest, self).setUp(
            auth_version=self.auth_version,
            fake_app=self.fake_app)
        self.base_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.base_dir)
        self.cert_dir = os.path.join(self.base_dir, 'certs')
        os.makedirs(self.cert_dir, stat.S_IRWXU)
        conf = {
            'signing_dir': self.cert_dir,
            'auth_version': self.auth_version,
        }
        self.set_middleware(conf=conf)

    # Usually we supply a signed_dir with pre-installed certificates,
    # so invocation of /usr/bin/openssl succeeds. This time we give it
    # an empty directory, so it fails.
    def test_request_no_token_dummy(self):
        cms._ensure_subprocess()

        self.requests_mock.get("%s%s" % (BASE_URI, self.ca_path),
                               status_code=404)
        url = "%s%s" % (BASE_URI, self.signing_path)
        self.requests_mock.get(url, status_code=404)
        self.assertRaises(exceptions.CertificateConfigError,
                          self.middleware.verify_signed_token,
                          self.examples.SIGNED_TOKEN_SCOPED,
                          [self.examples.SIGNED_TOKEN_SCOPED_HASH])

    def test_fetch_signing_cert(self):
        data = 'FAKE CERT'
        url = '%s%s' % (BASE_URI, self.signing_path)
        self.requests_mock.get(url, text=data)
        self.middleware.fetch_signing_cert()

        with open(self.middleware.signing_cert_file_name, 'r') as f:
            self.assertEqual(f.read(), data)

        self.assertLastPath("/testadmin%s" % self.signing_path)

    def test_fetch_signing_ca(self):
        data = 'FAKE CA'
        self.requests_mock.get("%s%s" % (BASE_URI, self.ca_path), text=data)
        self.middleware.fetch_ca_cert()

        with open(self.middleware.signing_ca_file_name, 'r') as f:
            self.assertEqual(f.read(), data)

        self.assertLastPath("/testadmin%s" % self.ca_path)

    def test_prefix_trailing_slash(self):
        del self.conf['identity_uri']
        self.conf['auth_protocol'] = 'https'
        self.conf['auth_host'] = 'keystone.example.com'
        self.conf['auth_port'] = 1234
        self.conf['auth_admin_prefix'] = '/newadmin/'

        self.requests_mock.get("%s/newadmin%s" % (BASE_HOST, self.ca_path),
                               text='FAKECA')
        url = "%s/newadmin%s" % (BASE_HOST, self.signing_path)
        self.requests_mock.get(url, text='FAKECERT')

        self.set_middleware(conf=self.conf)

        self.middleware.fetch_ca_cert()

        self.assertLastPath('/newadmin%s' % self.ca_path)

        self.middleware.fetch_signing_cert()

        self.assertLastPath('/newadmin%s' % self.signing_path)

    def test_without_prefix(self):
        del self.conf['identity_uri']
        self.conf['auth_protocol'] = 'https'
        self.conf['auth_host'] = 'keystone.example.com'
        self.conf['auth_port'] = 1234
        self.conf['auth_admin_prefix'] = ''

        self.requests_mock.get("%s%s" % (BASE_HOST, self.ca_path),
                               text='FAKECA')
        self.requests_mock.get("%s%s" % (BASE_HOST, self.signing_path),
                               text='FAKECERT')

        self.set_middleware(conf=self.conf)

        self.middleware.fetch_ca_cert()

        self.assertLastPath(self.ca_path)

        self.middleware.fetch_signing_cert()

        self.assertLastPath(self.signing_path)


class V3CertDownloadMiddlewareTest(V2CertDownloadMiddlewareTest):

    def __init__(self, *args, **kwargs):
        super(V3CertDownloadMiddlewareTest, self).__init__(*args, **kwargs)
        self.auth_version = 'v3.0'
        self.fake_app = v3FakeApp
        self.ca_path = '/v3/OS-SIMPLE-CERT/ca'
        self.signing_path = '/v3/OS-SIMPLE-CERT/certificates'


def network_error_response(method, uri, headers):
    raise auth_token.NetworkError("Network connection error.")


class v2AuthTokenMiddlewareTest(BaseAuthTokenMiddlewareTest,
                                CommonAuthTokenMiddlewareTest,
                                testresources.ResourcedTestCase):
    """v2 token specific tests.

    There are some differences between how the auth-token middleware handles
    v2 and v3 tokens over and above the token formats, namely:

    - A v3 keystone server will auto scope a token to a user's default project
      if no scope is specified. A v2 server assumes that the auth-token
      middleware will do that.
    - A v2 keystone server may issue a token without a catalog, even with a
      tenant

    The tests below were originally part of the generic AuthTokenMiddlewareTest
    class, but now, since they really are v2 specific, they are included here.

    """

    resources = [('examples', client_fixtures.EXAMPLES_RESOURCE)]

    def setUp(self):
        super(v2AuthTokenMiddlewareTest, self).setUp()

        self.token_dict = {
            'uuid_token_default': self.examples.UUID_TOKEN_DEFAULT,
            'uuid_token_unscoped': self.examples.UUID_TOKEN_UNSCOPED,
            'uuid_token_bind': self.examples.UUID_TOKEN_BIND,
            'uuid_token_unknown_bind': self.examples.UUID_TOKEN_UNKNOWN_BIND,
            'signed_token_scoped': self.examples.SIGNED_TOKEN_SCOPED,
            'signed_token_scoped_pkiz': self.examples.SIGNED_TOKEN_SCOPED_PKIZ,
            'signed_token_scoped_hash': self.examples.SIGNED_TOKEN_SCOPED_HASH,
            'signed_token_scoped_hash_sha256':
            self.examples.SIGNED_TOKEN_SCOPED_HASH_SHA256,
            'signed_token_scoped_expired':
            self.examples.SIGNED_TOKEN_SCOPED_EXPIRED,
            'revoked_token': self.examples.REVOKED_TOKEN,
            'revoked_token_pkiz': self.examples.REVOKED_TOKEN_PKIZ,
            'revoked_token_pkiz_hash':
            self.examples.REVOKED_TOKEN_PKIZ_HASH,
            'revoked_token_hash': self.examples.REVOKED_TOKEN_HASH,
            'revoked_token_hash_sha256':
            self.examples.REVOKED_TOKEN_HASH_SHA256,
        }

        self.requests_mock.get("%s/" % BASE_URI,
                               text=VERSION_LIST_v2,
                               status_code=300)

        self.requests_mock.post("%s/v2.0/tokens" % BASE_URI,
                                text=FAKE_ADMIN_TOKEN)

        self.requests_mock.get("%s/v2.0/tokens/revoked" % BASE_URI,
                               text=self.examples.SIGNED_REVOCATION_LIST)

        for token in (self.examples.UUID_TOKEN_DEFAULT,
                      self.examples.UUID_TOKEN_UNSCOPED,
                      self.examples.UUID_TOKEN_BIND,
                      self.examples.UUID_TOKEN_UNKNOWN_BIND,
                      self.examples.UUID_TOKEN_NO_SERVICE_CATALOG,
                      self.examples.SIGNED_TOKEN_SCOPED_KEY,
                      self.examples.SIGNED_TOKEN_SCOPED_PKIZ_KEY,):
            text = self.examples.JSON_TOKEN_RESPONSES[token]
            self.requests_mock.get('%s/v2.0/tokens/%s' % (BASE_URI, token),
                                   text=text)

        self.requests_mock.get('%s/v2.0/tokens/%s' % (BASE_URI, ERROR_TOKEN),
                               text=network_error_response)

        self.set_middleware()

    def assert_unscoped_default_tenant_auto_scopes(self, token):
        """Unscoped v2 requests with a default tenant should "auto-scope."

        The implied scope is the user's tenant ID.

        """
        req = webob.Request.blank('/')
        req.headers['X-Auth-Token'] = token
        body = self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(self.response_status, 200)
        self.assertEqual(body, [FakeApp.SUCCESS])
        self.assertIn('keystone.token_info', req.environ)

    def assert_valid_last_url(self, token_id):
        self.assertLastPath("/testadmin/v2.0/tokens/%s" % token_id)

    def test_default_tenant_uuid_token(self):
        self.assert_unscoped_default_tenant_auto_scopes(
            self.examples.UUID_TOKEN_DEFAULT)

    def test_default_tenant_signed_token(self):
        self.assert_unscoped_default_tenant_auto_scopes(
            self.examples.SIGNED_TOKEN_SCOPED)

    def assert_unscoped_token_receives_401(self, token):
        """Unscoped requests with no default tenant ID should be rejected."""
        req = webob.Request.blank('/')
        req.headers['X-Auth-Token'] = token
        self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(self.response_status, 401)
        self.assertEqual(self.response_headers['WWW-Authenticate'],
                         "Keystone uri='https://keystone.example.com:1234'")

    def test_unscoped_uuid_token_receives_401(self):
        self.assert_unscoped_token_receives_401(
            self.examples.UUID_TOKEN_UNSCOPED)

    def test_unscoped_pki_token_receives_401(self):
        self.assert_unscoped_token_receives_401(
            self.examples.SIGNED_TOKEN_UNSCOPED)

    def test_request_prevent_service_catalog_injection(self):
        req = webob.Request.blank('/')
        req.headers['X-Service-Catalog'] = '[]'
        req.headers['X-Auth-Token'] = (
            self.examples.UUID_TOKEN_NO_SERVICE_CATALOG)
        body = self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(self.response_status, 200)
        self.assertFalse(req.headers.get('X-Service-Catalog'))
        self.assertEqual(body, [FakeApp.SUCCESS])


class CrossVersionAuthTokenMiddlewareTest(BaseAuthTokenMiddlewareTest,
                                          testresources.ResourcedTestCase):

    resources = [('examples', client_fixtures.EXAMPLES_RESOURCE)]

    def test_valid_uuid_request_forced_to_2_0(self):
        """Test forcing auth_token to use lower api version.

        By installing the v3 http hander, auth_token will be get
        a version list that looks like a v3 server - from which it
        would normally chose v3.0 as the auth version.  However, here
        we specify v2.0 in the configuration - which should force
        auth_token to use that version instead.

        """
        conf = {
            'signing_dir': client_fixtures.CERTDIR,
            'auth_version': 'v2.0'
        }

        self.requests_mock.get('%s/' % BASE_URI,
                               text=VERSION_LIST_v3,
                               status_code=300)

        self.requests_mock.post('%s/v2.0/tokens' % BASE_URI,
                                text=FAKE_ADMIN_TOKEN)

        token = self.examples.UUID_TOKEN_DEFAULT
        url = '%s/v2.0/tokens/%s' % (BASE_URI, token)
        response_body = self.examples.JSON_TOKEN_RESPONSES[token]
        self.requests_mock.get(url, text=response_body)

        self.set_middleware(conf=conf)

        # This tests will only work is auth_token has chosen to use the
        # lower, v2, api version
        req = webob.Request.blank('/')
        req.headers['X-Auth-Token'] = self.examples.UUID_TOKEN_DEFAULT
        self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(self.response_status, 200)
        self.assertLastPath("/testadmin/v2.0/tokens/%s" %
                            self.examples.UUID_TOKEN_DEFAULT)


class v3AuthTokenMiddlewareTest(BaseAuthTokenMiddlewareTest,
                                CommonAuthTokenMiddlewareTest,
                                testresources.ResourcedTestCase):
    """Test auth_token middleware with v3 tokens.

    Re-execute the AuthTokenMiddlewareTest class tests, but with the
    auth_token middleware configured to expect v3 tokens back from
    a keystone server.

    This is done by configuring the AuthTokenMiddlewareTest class via
    its Setup(), passing in v3 style data that will then be used by
    the tests themselves.  This approach has been used to ensure we
    really are running the same tests for both v2 and v3 tokens.

    There a few additional specific test for v3 only:

    - We allow an unscoped token to be validated (as unscoped), where
      as for v2 tokens, the auth_token middleware is expected to try and
      auto-scope it (and fail if there is no default tenant)
    - Domain scoped tokens

    Since we don't specify an auth version for auth_token to use, by
    definition we are thefore implicitely testing that it will use
    the highest available auth version, i.e. v3.0

    """

    resources = [('examples', client_fixtures.EXAMPLES_RESOURCE)]

    def setUp(self):
        super(v3AuthTokenMiddlewareTest, self).setUp(
            auth_version='v3.0',
            fake_app=v3FakeApp)

        self.token_dict = {
            'uuid_token_default': self.examples.v3_UUID_TOKEN_DEFAULT,
            'uuid_token_unscoped': self.examples.v3_UUID_TOKEN_UNSCOPED,
            'uuid_token_bind': self.examples.v3_UUID_TOKEN_BIND,
            'uuid_token_unknown_bind':
            self.examples.v3_UUID_TOKEN_UNKNOWN_BIND,
            'signed_token_scoped': self.examples.SIGNED_v3_TOKEN_SCOPED,
            'signed_token_scoped_pkiz':
            self.examples.SIGNED_v3_TOKEN_SCOPED_PKIZ,
            'signed_token_scoped_hash':
            self.examples.SIGNED_v3_TOKEN_SCOPED_HASH,
            'signed_token_scoped_hash_sha256':
            self.examples.SIGNED_v3_TOKEN_SCOPED_HASH_SHA256,
            'signed_token_scoped_expired':
            self.examples.SIGNED_TOKEN_SCOPED_EXPIRED,
            'revoked_token': self.examples.REVOKED_v3_TOKEN,
            'revoked_token_pkiz': self.examples.REVOKED_v3_TOKEN_PKIZ,
            'revoked_token_hash': self.examples.REVOKED_v3_TOKEN_HASH,
            'revoked_token_hash_sha256':
            self.examples.REVOKED_v3_TOKEN_HASH_SHA256,
            'revoked_token_pkiz_hash':
            self.examples.REVOKED_v3_PKIZ_TOKEN_HASH,
        }

        self.requests_mock.get(BASE_URI, text=VERSION_LIST_v3, status_code=300)

        # TODO(jamielennox): auth_token middleware uses a v2 admin token
        # regardless of the auth_version that is set.
        self.requests_mock.post('%s/v2.0/tokens' % BASE_URI,
                                text=FAKE_ADMIN_TOKEN)

        # TODO(jamielennox): there is no v3 revocation url yet, it uses v2
        self.requests_mock.get('%s/v2.0/tokens/revoked' % BASE_URI,
                               text=self.examples.SIGNED_REVOCATION_LIST)

        self.requests_mock.get('%s/v3/auth/tokens' % BASE_URI,
                               text=self.token_response)

        self.set_middleware()

    def token_response(self, request, context):
        auth_id = request.headers.get('X-Auth-Token')
        token_id = request.headers.get('X-Subject-Token')
        self.assertEqual(auth_id, FAKE_ADMIN_TOKEN_ID)

        response = ""

        if token_id == ERROR_TOKEN:
            raise auth_token.NetworkError("Network connection error.")

        try:
            response = self.examples.JSON_TOKEN_RESPONSES[token_id]
        except KeyError:
            context.status_code = 404

        return response

    def assert_valid_last_url(self, token_id):
        self.assertLastPath('/testadmin/v3/auth/tokens')

    def test_valid_unscoped_uuid_request(self):
        # Remove items that won't be in an unscoped token
        delta_expected_env = {
            'HTTP_X_PROJECT_ID': None,
            'HTTP_X_PROJECT_NAME': None,
            'HTTP_X_PROJECT_DOMAIN_ID': None,
            'HTTP_X_PROJECT_DOMAIN_NAME': None,
            'HTTP_X_TENANT_ID': None,
            'HTTP_X_TENANT_NAME': None,
            'HTTP_X_ROLES': '',
            'HTTP_X_TENANT': None,
            'HTTP_X_ROLE': '',
        }
        self.set_middleware(expected_env=delta_expected_env)
        self.assert_valid_request_200(self.examples.v3_UUID_TOKEN_UNSCOPED,
                                      with_catalog=False)
        self.assertLastPath('/testadmin/v3/auth/tokens')

    def test_domain_scoped_uuid_request(self):
        # Modify items compared to default token for a domain scope
        delta_expected_env = {
            'HTTP_X_DOMAIN_ID': 'domain_id1',
            'HTTP_X_DOMAIN_NAME': 'domain_name1',
            'HTTP_X_PROJECT_ID': None,
            'HTTP_X_PROJECT_NAME': None,
            'HTTP_X_PROJECT_DOMAIN_ID': None,
            'HTTP_X_PROJECT_DOMAIN_NAME': None,
            'HTTP_X_TENANT_ID': None,
            'HTTP_X_TENANT_NAME': None,
            'HTTP_X_TENANT': None
        }
        self.set_middleware(expected_env=delta_expected_env)
        self.assert_valid_request_200(
            self.examples.v3_UUID_TOKEN_DOMAIN_SCOPED)
        self.assertLastPath('/testadmin/v3/auth/tokens')

    def test_gives_v2_catalog(self):
        self.set_middleware()
        req = self.assert_valid_request_200(
            self.examples.SIGNED_v3_TOKEN_SCOPED)

        catalog = jsonutils.loads(req.headers['X-Service-Catalog'])

        for service in catalog:
            for endpoint in service['endpoints']:
                # no point checking everything, just that it's in v2 format
                self.assertIn('adminURL', endpoint)
                self.assertIn('publicURL', endpoint)
                self.assertIn('adminURL', endpoint)


class TokenEncodingTest(testtools.TestCase):
    def test_unquoted_token(self):
        self.assertEqual('foo%20bar', auth_token.safe_quote('foo bar'))

    def test_quoted_token(self):
        self.assertEqual('foo%20bar', auth_token.safe_quote('foo%20bar'))


class TokenExpirationTest(BaseAuthTokenMiddlewareTest):
    def setUp(self):
        super(TokenExpirationTest, self).setUp()
        self.now = timeutils.utcnow()
        self.delta = datetime.timedelta(hours=1)
        self.one_hour_ago = timeutils.isotime(self.now - self.delta,
                                              subsecond=True)
        self.one_hour_earlier = timeutils.isotime(self.now + self.delta,
                                                  subsecond=True)

    def create_v2_token_fixture(self, expires=None):
        v2_fixture = {
            'access': {
                'token': {
                    'id': 'blah',
                    'expires': expires or self.one_hour_earlier,
                    'tenant': {
                        'id': 'tenant_id1',
                        'name': 'tenant_name1',
                    },
                },
                'user': {
                    'id': 'user_id1',
                    'name': 'user_name1',
                    'roles': [
                        {'name': 'role1'},
                        {'name': 'role2'},
                    ],
                },
                'serviceCatalog': {}
            },
        }

        return v2_fixture

    def create_v3_token_fixture(self, expires=None):

        v3_fixture = {
            'token': {
                'expires_at': expires or self.one_hour_earlier,
                'user': {
                    'id': 'user_id1',
                    'name': 'user_name1',
                    'domain': {
                        'id': 'domain_id1',
                        'name': 'domain_name1'
                    }
                },
                'project': {
                    'id': 'tenant_id1',
                    'name': 'tenant_name1',
                    'domain': {
                        'id': 'domain_id1',
                        'name': 'domain_name1'
                    }
                },
                'roles': [
                    {'name': 'role1', 'id': 'Role1'},
                    {'name': 'role2', 'id': 'Role2'},
                ],
                'catalog': {}
            }
        }

        return v3_fixture

    def test_no_data(self):
        data = {}
        self.assertRaises(auth_token.InvalidUserToken,
                          auth_token.confirm_token_not_expired,
                          data)

    def test_bad_data(self):
        data = {'my_happy_token_dict': 'woo'}
        self.assertRaises(auth_token.InvalidUserToken,
                          auth_token.confirm_token_not_expired,
                          data)

    def test_v2_token_not_expired(self):
        data = self.create_v2_token_fixture()
        expected_expires = data['access']['token']['expires']
        actual_expires = auth_token.confirm_token_not_expired(data)
        self.assertEqual(actual_expires, expected_expires)

    def test_v2_token_expired(self):
        data = self.create_v2_token_fixture(expires=self.one_hour_ago)
        self.assertRaises(auth_token.InvalidUserToken,
                          auth_token.confirm_token_not_expired,
                          data)

    def test_v2_token_with_timezone_offset_not_expired(self):
        self.useFixture(TimeFixture('2000-01-01T00:01:10.000123Z'))
        data = self.create_v2_token_fixture(
            expires='2000-01-01T00:05:10.000123-05:00')
        expected_expires = '2000-01-01T05:05:10.000123Z'
        actual_expires = auth_token.confirm_token_not_expired(data)
        self.assertEqual(actual_expires, expected_expires)

    def test_v2_token_with_timezone_offset_expired(self):
        self.useFixture(TimeFixture('2000-01-01T00:01:10.000123Z'))
        data = self.create_v2_token_fixture(
            expires='2000-01-01T00:05:10.000123+05:00')
        data['access']['token']['expires'] = '2000-01-01T00:05:10.000123+05:00'
        self.assertRaises(auth_token.InvalidUserToken,
                          auth_token.confirm_token_not_expired,
                          data)

    def test_v3_token_not_expired(self):
        data = self.create_v3_token_fixture()
        expected_expires = data['token']['expires_at']
        actual_expires = auth_token.confirm_token_not_expired(data)
        self.assertEqual(actual_expires, expected_expires)

    def test_v3_token_expired(self):
        data = self.create_v3_token_fixture(expires=self.one_hour_ago)
        self.assertRaises(auth_token.InvalidUserToken,
                          auth_token.confirm_token_not_expired,
                          data)

    def test_v3_token_with_timezone_offset_not_expired(self):
        self.useFixture(TimeFixture('2000-01-01T00:01:10.000123Z'))
        data = self.create_v3_token_fixture(
            expires='2000-01-01T00:05:10.000123-05:00')
        expected_expires = '2000-01-01T05:05:10.000123Z'

        actual_expires = auth_token.confirm_token_not_expired(data)
        self.assertEqual(actual_expires, expected_expires)

    def test_v3_token_with_timezone_offset_expired(self):
        self.useFixture(TimeFixture('2000-01-01T00:01:10.000123Z'))
        data = self.create_v3_token_fixture(
            expires='2000-01-01T00:05:10.000123+05:00')
        self.assertRaises(auth_token.InvalidUserToken,
                          auth_token.confirm_token_not_expired,
                          data)

    def test_cached_token_not_expired(self):
        token = 'mytoken'
        data = 'this_data'
        self.set_middleware()
        self.middleware._token_cache.initialize({})
        some_time_later = timeutils.strtime(at=(self.now + self.delta))
        expires = some_time_later
        self.middleware._token_cache.store(token, data, expires)
        self.assertEqual(self.middleware._token_cache._cache_get(token), data)

    def test_cached_token_not_expired_with_old_style_nix_timestamp(self):
        """Ensure we cannot retrieve a token from the cache.

        Getting a token from the cache should return None when the token data
        in the cache stores the expires time as a \*nix style timestamp.

        """
        token = 'mytoken'
        data = 'this_data'
        self.set_middleware()
        token_cache = self.middleware._token_cache
        token_cache.initialize({})
        some_time_later = self.now + self.delta
        # Store a unix timestamp in the cache.
        expires = calendar.timegm(some_time_later.timetuple())
        token_cache.store(token, data, expires)
        self.assertIsNone(token_cache._cache_get(token))

    def test_cached_token_expired(self):
        token = 'mytoken'
        data = 'this_data'
        self.set_middleware()
        self.middleware._token_cache.initialize({})
        some_time_earlier = timeutils.strtime(at=(self.now - self.delta))
        expires = some_time_earlier
        self.middleware._token_cache.store(token, data, expires)
        self.assertThat(lambda: self.middleware._token_cache._cache_get(token),
                        matchers.raises(auth_token.InvalidUserToken))

    def test_cached_token_with_timezone_offset_not_expired(self):
        token = 'mytoken'
        data = 'this_data'
        self.set_middleware()
        self.middleware._token_cache.initialize({})
        timezone_offset = datetime.timedelta(hours=2)
        some_time_later = self.now - timezone_offset + self.delta
        expires = timeutils.strtime(some_time_later) + '-02:00'
        self.middleware._token_cache.store(token, data, expires)
        self.assertEqual(self.middleware._token_cache._cache_get(token), data)

    def test_cached_token_with_timezone_offset_expired(self):
        token = 'mytoken'
        data = 'this_data'
        self.set_middleware()
        self.middleware._token_cache.initialize({})
        timezone_offset = datetime.timedelta(hours=2)
        some_time_earlier = self.now - timezone_offset - self.delta
        expires = timeutils.strtime(some_time_earlier) + '-02:00'
        self.middleware._token_cache.store(token, data, expires)
        self.assertThat(lambda: self.middleware._token_cache._cache_get(token),
                        matchers.raises(auth_token.InvalidUserToken))


class CatalogConversionTests(BaseAuthTokenMiddlewareTest):

    PUBLIC_URL = 'http://server:5000/v2.0'
    ADMIN_URL = 'http://admin:35357/v2.0'
    INTERNAL_URL = 'http://internal:5000/v2.0'

    REGION_ONE = 'RegionOne'
    REGION_TWO = 'RegionTwo'
    REGION_THREE = 'RegionThree'

    def test_basic_convert(self):
        token = fixture.V3Token()
        s = token.add_service(type='identity')
        s.add_standard_endpoints(public=self.PUBLIC_URL,
                                 admin=self.ADMIN_URL,
                                 internal=self.INTERNAL_URL,
                                 region=self.REGION_ONE)

        auth_ref = access.AccessInfo.factory(body=token)
        catalog_data = auth_ref.service_catalog.get_data()
        catalog = auth_token._v3_to_v2_catalog(catalog_data)

        self.assertEqual(1, len(catalog))
        service = catalog[0]
        self.assertEqual(1, len(service['endpoints']))
        endpoints = service['endpoints'][0]

        self.assertEqual('identity', service['type'])
        self.assertEqual(4, len(endpoints))
        self.assertEqual(self.PUBLIC_URL, endpoints['publicURL'])
        self.assertEqual(self.ADMIN_URL, endpoints['adminURL'])
        self.assertEqual(self.INTERNAL_URL, endpoints['internalURL'])
        self.assertEqual(self.REGION_ONE, endpoints['region'])

    def test_multi_region(self):
        token = fixture.V3Token()
        s = token.add_service(type='identity')

        s.add_endpoint('internal', self.INTERNAL_URL, region=self.REGION_ONE)
        s.add_endpoint('public', self.PUBLIC_URL, region=self.REGION_TWO)
        s.add_endpoint('admin', self.ADMIN_URL, region=self.REGION_THREE)

        auth_ref = access.AccessInfo.factory(body=token)
        catalog_data = auth_ref.service_catalog.get_data()
        catalog = auth_token._v3_to_v2_catalog(catalog_data)

        self.assertEqual(1, len(catalog))
        service = catalog[0]

        # the 3 regions will come through as 3 separate endpoints
        expected = [{'internalURL': self.INTERNAL_URL,
                    'region': self.REGION_ONE},
                    {'publicURL': self.PUBLIC_URL,
                     'region': self.REGION_TWO},
                    {'adminURL': self.ADMIN_URL,
                     'region': self.REGION_THREE}]

        self.assertEqual('identity', service['type'])
        self.assertEqual(3, len(service['endpoints']))
        for e in expected:
            self.assertIn(e, expected)


def load_tests(loader, tests, pattern):
    return testresources.OptimisingTestSuite(tests)
