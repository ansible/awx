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

import abc
import datetime
import uuid

from oslo_utils import timeutils
import six

from keystoneclient import access
from keystoneclient.auth import base
from keystoneclient.auth import identity
from keystoneclient import fixture
from keystoneclient import session
from keystoneclient.tests.unit import utils


@six.add_metaclass(abc.ABCMeta)
class CommonIdentityTests(object):

    TEST_ROOT_URL = 'http://127.0.0.1:5000/'
    TEST_ROOT_ADMIN_URL = 'http://127.0.0.1:35357/'

    TEST_COMPUTE_PUBLIC = 'http://nova/novapi/public'
    TEST_COMPUTE_INTERNAL = 'http://nova/novapi/internal'
    TEST_COMPUTE_ADMIN = 'http://nova/novapi/admin'

    TEST_PASS = uuid.uuid4().hex

    def setUp(self):
        super(CommonIdentityTests, self).setUp()

        self.TEST_URL = '%s%s' % (self.TEST_ROOT_URL, self.version)
        self.TEST_ADMIN_URL = '%s%s' % (self.TEST_ROOT_ADMIN_URL, self.version)
        self.TEST_DISCOVERY = fixture.DiscoveryList(href=self.TEST_ROOT_URL)

        self.stub_auth_data()

    @abc.abstractmethod
    def create_auth_plugin(self, **kwargs):
        """Create an auth plugin that makes sense for the auth data.

        It doesn't really matter what auth mechanism is used but it should be
        appropriate to the API version.
        """

    @abc.abstractmethod
    def get_auth_data(self, **kwargs):
        """Return fake authentication data.

        This should register a valid token response and ensure that the compute
        endpoints are set to TEST_COMPUTE_PUBLIC, _INTERNAL and _ADMIN.
        """

    def stub_auth_data(self, **kwargs):
        token = self.get_auth_data(**kwargs)
        self.user_id = token.user_id

        try:
            self.project_id = token.project_id
        except AttributeError:
            self.project_id = token.tenant_id

        self.stub_auth(json=token)

    @abc.abstractproperty
    def version(self):
        """The API version being tested."""

    def test_discovering(self):
        self.stub_url('GET', [],
                      base_url=self.TEST_COMPUTE_ADMIN,
                      json=self.TEST_DISCOVERY)

        body = 'SUCCESS'

        # which gives our sample values
        self.stub_url('GET', ['path'], text=body)

        a = self.create_auth_plugin()
        s = session.Session(auth=a)

        resp = s.get('/path', endpoint_filter={'service_type': 'compute',
                                               'interface': 'admin',
                                               'version': self.version})

        self.assertEqual(200, resp.status_code)
        self.assertEqual(body, resp.text)

        new_body = 'SC SUCCESS'
        # if we don't specify a version, we use the URL from the SC
        self.stub_url('GET', ['path'],
                      base_url=self.TEST_COMPUTE_ADMIN,
                      text=new_body)

        resp = s.get('/path', endpoint_filter={'service_type': 'compute',
                                               'interface': 'admin'})

        self.assertEqual(200, resp.status_code)
        self.assertEqual(new_body, resp.text)

    def test_discovery_uses_session_cache(self):
        # register responses such that if the discovery URL is hit more than
        # once then the response will be invalid and not point to COMPUTE_ADMIN
        resps = [{'json': self.TEST_DISCOVERY}, {'status_code': 500}]
        self.requests_mock.get(self.TEST_COMPUTE_ADMIN, resps)

        body = 'SUCCESS'
        self.stub_url('GET', ['path'], text=body)

        # now either of the two plugins I use, it should not cause a second
        # request to the discovery url.
        s = session.Session()
        a = self.create_auth_plugin()
        b = self.create_auth_plugin()

        for auth in (a, b):
            resp = s.get('/path',
                         auth=auth,
                         endpoint_filter={'service_type': 'compute',
                                          'interface': 'admin',
                                          'version': self.version})

            self.assertEqual(200, resp.status_code)
            self.assertEqual(body, resp.text)

    def test_discovery_uses_plugin_cache(self):
        # register responses such that if the discovery URL is hit more than
        # once then the response will be invalid and not point to COMPUTE_ADMIN
        resps = [{'json': self.TEST_DISCOVERY}, {'status_code': 500}]
        self.requests_mock.get(self.TEST_COMPUTE_ADMIN, resps)

        body = 'SUCCESS'
        self.stub_url('GET', ['path'], text=body)

        # now either of the two sessions I use, it should not cause a second
        # request to the discovery url.
        sa = session.Session()
        sb = session.Session()
        auth = self.create_auth_plugin()

        for sess in (sa, sb):
            resp = sess.get('/path',
                            auth=auth,
                            endpoint_filter={'service_type': 'compute',
                                             'interface': 'admin',
                                             'version': self.version})

            self.assertEqual(200, resp.status_code)
            self.assertEqual(body, resp.text)

    def test_discovering_with_no_data(self):
        # which returns discovery information pointing to TEST_URL but there is
        # no data there.
        self.stub_url('GET', [],
                      base_url=self.TEST_COMPUTE_ADMIN,
                      status_code=400)

        # so the url that will be used is the same TEST_COMPUTE_ADMIN
        body = 'SUCCESS'
        self.stub_url('GET', ['path'], base_url=self.TEST_COMPUTE_ADMIN,
                      text=body, status_code=200)

        a = self.create_auth_plugin()
        s = session.Session(auth=a)

        resp = s.get('/path', endpoint_filter={'service_type': 'compute',
                                               'interface': 'admin',
                                               'version': self.version})

        self.assertEqual(200, resp.status_code)
        self.assertEqual(body, resp.text)

    def test_asking_for_auth_endpoint_ignores_checks(self):
        a = self.create_auth_plugin()
        s = session.Session(auth=a)

        auth_url = s.get_endpoint(service_type='compute',
                                  interface=base.AUTH_INTERFACE)

        self.assertEqual(self.TEST_URL, auth_url)

    def _create_expired_auth_plugin(self, **kwargs):
        expires = timeutils.utcnow() - datetime.timedelta(minutes=20)
        expired_token = self.get_auth_data(expires=expires)
        expired_auth_ref = access.AccessInfo.factory(body=expired_token)

        body = 'SUCCESS'
        self.stub_url('GET', ['path'],
                      base_url=self.TEST_COMPUTE_ADMIN, text=body)

        a = self.create_auth_plugin(**kwargs)
        a.auth_ref = expired_auth_ref
        return a

    def test_reauthenticate(self):
        a = self._create_expired_auth_plugin()
        expired_auth_ref = a.auth_ref
        s = session.Session(auth=a)
        self.assertIsNot(expired_auth_ref, a.get_access(s))

    def test_no_reauthenticate(self):
        a = self._create_expired_auth_plugin(reauthenticate=False)
        expired_auth_ref = a.auth_ref
        s = session.Session(auth=a)
        self.assertIs(expired_auth_ref, a.get_access(s))

    def test_invalidate(self):
        a = self.create_auth_plugin()
        s = session.Session(auth=a)

        # trigger token fetching
        s.get_auth_headers()

        self.assertTrue(a.auth_ref)
        self.assertTrue(a.invalidate())
        self.assertIsNone(a.auth_ref)
        self.assertFalse(a.invalidate())

    def test_get_auth_properties(self):
        a = self.create_auth_plugin()
        s = session.Session()

        self.assertEqual(self.user_id, a.get_user_id(s))
        self.assertEqual(self.project_id, a.get_project_id(s))


class V3(CommonIdentityTests, utils.TestCase):

    @property
    def version(self):
        return 'v3'

    def get_auth_data(self, **kwargs):
        token = fixture.V3Token(**kwargs)
        region = 'RegionOne'

        svc = token.add_service('identity')
        svc.add_standard_endpoints(admin=self.TEST_ADMIN_URL, region=region)

        svc = token.add_service('compute')
        svc.add_standard_endpoints(admin=self.TEST_COMPUTE_ADMIN,
                                   public=self.TEST_COMPUTE_PUBLIC,
                                   internal=self.TEST_COMPUTE_INTERNAL,
                                   region=region)

        return token

    def stub_auth(self, subject_token=None, **kwargs):
        if not subject_token:
            subject_token = self.TEST_TOKEN

        kwargs.setdefault('headers', {})['X-Subject-Token'] = subject_token
        self.stub_url('POST', ['auth', 'tokens'], **kwargs)

    def create_auth_plugin(self, **kwargs):
        kwargs.setdefault('auth_url', self.TEST_URL)
        kwargs.setdefault('username', self.TEST_USER)
        kwargs.setdefault('password', self.TEST_PASS)
        return identity.V3Password(**kwargs)


class V2(CommonIdentityTests, utils.TestCase):

    @property
    def version(self):
        return 'v2.0'

    def create_auth_plugin(self, **kwargs):
        kwargs.setdefault('auth_url', self.TEST_URL)
        kwargs.setdefault('username', self.TEST_USER)
        kwargs.setdefault('password', self.TEST_PASS)
        return identity.V2Password(**kwargs)

    def get_auth_data(self, **kwargs):
        token = fixture.V2Token(**kwargs)
        region = 'RegionOne'

        svc = token.add_service('identity')
        svc.add_endpoint(self.TEST_ADMIN_URL, region=region)

        svc = token.add_service('compute')
        svc.add_endpoint(public=self.TEST_COMPUTE_PUBLIC,
                         internal=self.TEST_COMPUTE_INTERNAL,
                         admin=self.TEST_COMPUTE_ADMIN,
                         region=region)

        return token

    def stub_auth(self, **kwargs):
        self.stub_url('POST', ['tokens'], **kwargs)


class CatalogHackTests(utils.TestCase):

    TEST_URL = 'http://keystone.server:5000/v2.0'
    OTHER_URL = 'http://other.server:5000/path'

    IDENTITY = 'identity'

    BASE_URL = 'http://keystone.server:5000/'
    V2_URL = BASE_URL + 'v2.0'
    V3_URL = BASE_URL + 'v3'

    def test_getting_endpoints(self):
        disc = fixture.DiscoveryList(href=self.BASE_URL)
        self.stub_url('GET',
                      ['/'],
                      base_url=self.BASE_URL,
                      json=disc)

        token = fixture.V2Token()
        service = token.add_service(self.IDENTITY)
        service.add_endpoint(public=self.V2_URL,
                             admin=self.V2_URL,
                             internal=self.V2_URL)

        self.stub_url('POST',
                      ['tokens'],
                      base_url=self.V2_URL,
                      json=token)

        v2_auth = identity.V2Password(self.V2_URL,
                                      username=uuid.uuid4().hex,
                                      password=uuid.uuid4().hex)

        sess = session.Session(auth=v2_auth)

        endpoint = sess.get_endpoint(service_type=self.IDENTITY,
                                     interface='public',
                                     version=(3, 0))

        self.assertEqual(self.V3_URL, endpoint)

    def test_returns_original_when_discover_fails(self):
        token = fixture.V2Token()
        service = token.add_service(self.IDENTITY)
        service.add_endpoint(public=self.V2_URL,
                             admin=self.V2_URL,
                             internal=self.V2_URL)

        self.stub_url('POST',
                      ['tokens'],
                      base_url=self.V2_URL,
                      json=token)

        self.stub_url('GET', [], base_url=self.BASE_URL, status_code=404)

        v2_auth = identity.V2Password(self.V2_URL,
                                      username=uuid.uuid4().hex,
                                      password=uuid.uuid4().hex)

        sess = session.Session(auth=v2_auth)

        endpoint = sess.get_endpoint(service_type=self.IDENTITY,
                                     interface='public',
                                     version=(3, 0))

        self.assertEqual(self.V2_URL, endpoint)


class GenericPlugin(base.BaseAuthPlugin):

    BAD_TOKEN = uuid.uuid4().hex

    def __init__(self):
        super(GenericPlugin, self).__init__()

        self.endpoint = 'http://keystone.host:5000'

        self.headers = {'headerA': 'valueA',
                        'headerB': 'valueB'}

    def url(self, prefix):
        return '%s/%s' % (self.endpoint, prefix)

    def get_token(self, session, **kwargs):
        # NOTE(jamielennox): by specifying get_headers this should not be used
        return self.BAD_TOKEN

    def get_headers(self, session, **kwargs):
        return self.headers

    def get_endpoint(self, session, **kwargs):
        return self.endpoint


class GenericAuthPluginTests(utils.TestCase):

    # filter doesn't matter to GenericPlugin, but we have to specify one
    ENDPOINT_FILTER = {uuid.uuid4().hex: uuid.uuid4().hex}

    def setUp(self):
        super(GenericAuthPluginTests, self).setUp()
        self.auth = GenericPlugin()
        self.session = session.Session(auth=self.auth)

    def test_setting_headers(self):
        text = uuid.uuid4().hex
        self.stub_url('GET', base_url=self.auth.url('prefix'), text=text)

        resp = self.session.get('prefix', endpoint_filter=self.ENDPOINT_FILTER)

        self.assertEqual(text, resp.text)

        for k, v in six.iteritems(self.auth.headers):
            self.assertRequestHeaderEqual(k, v)

        self.assertIsNone(self.session.get_token())
        self.assertEqual(self.auth.headers,
                         self.session.get_auth_headers())
        self.assertNotIn('X-Auth-Token',
                         self.requests_mock.last_request.headers)
