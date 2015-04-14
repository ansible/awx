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

import re
import uuid

from oslo_serialization import jsonutils
import six
from testtools import matchers

from keystoneclient import _discover
from keystoneclient.auth import token_endpoint
from keystoneclient import client
from keystoneclient import discover
from keystoneclient import exceptions
from keystoneclient import fixture
from keystoneclient import session
from keystoneclient.tests.unit import utils
from keystoneclient.v2_0 import client as v2_client
from keystoneclient.v3 import client as v3_client


BASE_HOST = 'http://keystone.example.com'
BASE_URL = "%s:5000/" % BASE_HOST
UPDATED = '2013-03-06T00:00:00Z'

TEST_SERVICE_CATALOG = [{
    "endpoints": [{
        "adminURL": "%s:8774/v1.0" % BASE_HOST,
        "region": "RegionOne",
        "internalURL": "%s://127.0.0.1:8774/v1.0" % BASE_HOST,
        "publicURL": "%s:8774/v1.0/" % BASE_HOST
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
        "adminURL": "%s:35357/v2.0" % BASE_HOST,
        "region": "RegionOne",
        "internalURL": "%s:5000/v2.0" % BASE_HOST,
        "publicURL": "%s:5000/v2.0" % BASE_HOST
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

V2_URL = "%sv2.0" % BASE_URL
V2_VERSION = fixture.V2Discovery(V2_URL)
V2_VERSION.updated_str = UPDATED

V2_AUTH_RESPONSE = jsonutils.dumps({
    "access": {
        "token": {
            "expires": "2020-01-01T00:00:10.000123Z",
            "id": 'fakeToken',
            "tenant": {
                "id": '1'
            },
        },
        "user": {
            "id": 'test'
        },
        "serviceCatalog": TEST_SERVICE_CATALOG,
    },
})

V3_URL = "%sv3" % BASE_URL
V3_VERSION = fixture.V3Discovery(V3_URL)
V3_MEDIA_TYPES = V3_VERSION.media_types
V3_VERSION.updated_str = UPDATED

V3_TOKEN = six.u('3e2813b7ba0b4006840c3825860b86ed'),
V3_AUTH_RESPONSE = jsonutils.dumps({
    "token": {
        "methods": [
            "token",
            "password"
        ],

        "expires_at": "2020-01-01T00:00:10.000123Z",
        "project": {
            "domain": {
                "id": '1',
                "name": 'test-domain'
            },
            "id": '1',
            "name": 'test-project'
        },
        "user": {
            "domain": {
                "id": '1',
                "name": 'test-domain'
            },
            "id": '1',
            "name": 'test-user'
        },
        "issued_at": "2013-05-29T16:55:21.468960Z",
    },
})

CINDER_EXAMPLES = {
    "versions": [
        {
            "status": "CURRENT",
            "updated": "2012-01-04T11:33:21Z",
            "id": "v1.0",
            "links": [
                {
                    "href": "%sv1/" % BASE_URL,
                    "rel": "self"
                }
            ]
        },
        {
            "status": "CURRENT",
            "updated": "2012-11-21T11:33:21Z",
            "id": "v2.0",
            "links": [
                {
                    "href": "%sv2/" % BASE_URL,
                    "rel": "self"
                }
            ]
        }
    ]
}

GLANCE_EXAMPLES = {
    "versions": [
        {
            "status": "CURRENT",
            "id": "v2.2",
            "links": [
                {
                    "href": "%sv2/" % BASE_URL,
                    "rel": "self"
                }
            ]
        },
        {
            "status": "SUPPORTED",
            "id": "v2.1",
            "links": [
                {
                    "href": "%sv2/" % BASE_URL,
                    "rel": "self"
                }
            ]
        },
        {
            "status": "SUPPORTED",
            "id": "v2.0",
            "links": [
                {
                    "href": "%sv2/" % BASE_URL,
                    "rel": "self"
                }
            ]
        },
        {
            "status": "CURRENT",
            "id": "v1.1",
            "links": [
                {
                    "href": "%sv1/" % BASE_URL,
                    "rel": "self"
                }
            ]
        },
        {
            "status": "SUPPORTED",
            "id": "v1.0",
            "links": [
                {
                    "href": "%sv1/" % BASE_URL,
                    "rel": "self"
                }
            ]
        }
    ]
}


def _create_version_list(versions):
    return jsonutils.dumps({'versions': {'values': versions}})


def _create_single_version(version):
    return jsonutils.dumps({'version': version})


V3_VERSION_LIST = _create_version_list([V3_VERSION, V2_VERSION])
V2_VERSION_LIST = _create_version_list([V2_VERSION])

V3_VERSION_ENTRY = _create_single_version(V3_VERSION)
V2_VERSION_ENTRY = _create_single_version(V2_VERSION)


class AvailableVersionsTests(utils.TestCase):

    def test_available_versions_basics(self):
        examples = {'keystone': V3_VERSION_LIST,
                    'cinder': jsonutils.dumps(CINDER_EXAMPLES),
                    'glance': jsonutils.dumps(GLANCE_EXAMPLES)}

        for path, text in six.iteritems(examples):
            url = "%s%s" % (BASE_URL, path)

            self.requests_mock.get(url, status_code=300, text=text)
            versions = discover.available_versions(url)

            for v in versions:
                for n in ('id', 'status', 'links'):
                    msg = '%s missing from %s version data' % (n, path)
                    self.assertThat(v, matchers.Annotate(msg,
                                                         matchers.Contains(n)))

    def test_available_versions_individual(self):
        self.requests_mock.get(V3_URL, status_code=200, text=V3_VERSION_ENTRY)

        versions = discover.available_versions(V3_URL)

        for v in versions:
            self.assertEqual(v['id'], 'v3.0')
            self.assertEqual(v['status'], 'stable')
            self.assertIn('media-types', v)
            self.assertIn('links', v)

    def test_available_keystone_data(self):
        self.requests_mock.get(BASE_URL, status_code=300, text=V3_VERSION_LIST)

        versions = discover.available_versions(BASE_URL)
        self.assertEqual(2, len(versions))

        for v in versions:
            self.assertIn(v['id'], ('v2.0', 'v3.0'))
            self.assertEqual(v['updated'], UPDATED)
            self.assertEqual(v['status'], 'stable')

            if v['id'] == 'v3.0':
                self.assertEqual(v['media-types'], V3_MEDIA_TYPES)

    def test_available_cinder_data(self):
        text = jsonutils.dumps(CINDER_EXAMPLES)
        self.requests_mock.get(BASE_URL, status_code=300, text=text)

        versions = discover.available_versions(BASE_URL)
        self.assertEqual(2, len(versions))

        for v in versions:
            self.assertEqual(v['status'], 'CURRENT')
            if v['id'] == 'v1.0':
                self.assertEqual(v['updated'], '2012-01-04T11:33:21Z')
            elif v['id'] == 'v2.0':
                self.assertEqual(v['updated'], '2012-11-21T11:33:21Z')
            else:
                self.fail("Invalid version found")

    def test_available_glance_data(self):
        text = jsonutils.dumps(GLANCE_EXAMPLES)
        self.requests_mock.get(BASE_URL, status_code=200, text=text)

        versions = discover.available_versions(BASE_URL)
        self.assertEqual(5, len(versions))

        for v in versions:
            if v['id'] in ('v2.2', 'v1.1'):
                self.assertEqual(v['status'], 'CURRENT')
            elif v['id'] in ('v2.1', 'v2.0', 'v1.0'):
                self.assertEqual(v['status'], 'SUPPORTED')
            else:
                self.fail("Invalid version found")


class ClientDiscoveryTests(utils.TestCase):

    def assertCreatesV3(self, **kwargs):
        self.requests_mock.post('%s/auth/tokens' % V3_URL,
                                text=V3_AUTH_RESPONSE,
                                headers={'X-Subject-Token': V3_TOKEN})

        kwargs.setdefault('username', 'foo')
        kwargs.setdefault('password', 'bar')
        keystone = client.Client(**kwargs)
        self.assertIsInstance(keystone, v3_client.Client)
        return keystone

    def assertCreatesV2(self, **kwargs):
        self.requests_mock.post("%s/tokens" % V2_URL, text=V2_AUTH_RESPONSE)

        kwargs.setdefault('username', 'foo')
        kwargs.setdefault('password', 'bar')
        keystone = client.Client(**kwargs)
        self.assertIsInstance(keystone, v2_client.Client)
        return keystone

    def assertVersionNotAvailable(self, **kwargs):
        kwargs.setdefault('username', 'foo')
        kwargs.setdefault('password', 'bar')

        self.assertRaises(exceptions.VersionNotAvailable,
                          client.Client, **kwargs)

    def assertDiscoveryFailure(self, **kwargs):
        kwargs.setdefault('username', 'foo')
        kwargs.setdefault('password', 'bar')

        self.assertRaises(exceptions.DiscoveryFailure,
                          client.Client, **kwargs)

    def test_discover_v3(self):
        self.requests_mock.get(BASE_URL, status_code=300, text=V3_VERSION_LIST)

        self.assertCreatesV3(auth_url=BASE_URL)

    def test_discover_v2(self):
        self.requests_mock.get(BASE_URL, status_code=300, text=V2_VERSION_LIST)
        self.requests_mock.post("%s/tokens" % V2_URL, text=V2_AUTH_RESPONSE)

        self.assertCreatesV2(auth_url=BASE_URL)

    def test_discover_endpoint_v2(self):
        self.requests_mock.get(BASE_URL, status_code=300, text=V2_VERSION_LIST)
        self.assertCreatesV2(endpoint=BASE_URL, token='fake-token')

    def test_discover_endpoint_v3(self):
        self.requests_mock.get(BASE_URL, status_code=300, text=V3_VERSION_LIST)
        self.assertCreatesV3(endpoint=BASE_URL, token='fake-token')

    def test_discover_invalid_major_version(self):
        self.requests_mock.get(BASE_URL, status_code=300, text=V3_VERSION_LIST)

        self.assertVersionNotAvailable(auth_url=BASE_URL, version=5)

    def test_discover_200_response_fails(self):
        self.requests_mock.get(BASE_URL, text='ok')
        self.assertDiscoveryFailure(auth_url=BASE_URL)

    def test_discover_minor_greater_than_available_fails(self):
        self.requests_mock.get(BASE_URL, status_code=300, text=V3_VERSION_LIST)

        self.assertVersionNotAvailable(endpoint=BASE_URL, version=3.4)

    def test_discover_individual_version_v2(self):
        self.requests_mock.get(V2_URL, text=V2_VERSION_ENTRY)

        self.assertCreatesV2(auth_url=V2_URL)

    def test_discover_individual_version_v3(self):
        self.requests_mock.get(V3_URL, text=V3_VERSION_ENTRY)

        self.assertCreatesV3(auth_url=V3_URL)

    def test_discover_individual_endpoint_v2(self):
        self.requests_mock.get(V2_URL, text=V2_VERSION_ENTRY)
        self.assertCreatesV2(endpoint=V2_URL, token='fake-token')

    def test_discover_individual_endpoint_v3(self):
        self.requests_mock.get(V3_URL, text=V3_VERSION_ENTRY)
        self.assertCreatesV3(endpoint=V3_URL, token='fake-token')

    def test_discover_fail_to_create_bad_individual_version(self):
        self.requests_mock.get(V2_URL, text=V2_VERSION_ENTRY)
        self.requests_mock.get(V3_URL, text=V3_VERSION_ENTRY)

        self.assertVersionNotAvailable(auth_url=V2_URL, version=3)
        self.assertVersionNotAvailable(auth_url=V3_URL, version=2)

    def test_discover_unstable_versions(self):
        version_list = fixture.DiscoveryList(BASE_URL, v3_status='beta')
        self.requests_mock.get(BASE_URL, status_code=300, json=version_list)

        self.assertCreatesV2(auth_url=BASE_URL)
        self.assertVersionNotAvailable(auth_url=BASE_URL, version=3)
        self.assertCreatesV3(auth_url=BASE_URL, unstable=True)

    def test_discover_forwards_original_ip(self):
        self.requests_mock.get(BASE_URL, status_code=300, text=V3_VERSION_LIST)

        ip = '192.168.1.1'
        self.assertCreatesV3(auth_url=BASE_URL, original_ip=ip)

        self.assertThat(self.requests_mock.last_request.headers['forwarded'],
                        matchers.Contains(ip))

    def test_discover_bad_args(self):
        self.assertRaises(exceptions.DiscoveryFailure,
                          client.Client)

    def test_discover_bad_response(self):
        self.requests_mock.get(BASE_URL, status_code=300, json={'FOO': 'BAR'})
        self.assertDiscoveryFailure(auth_url=BASE_URL)

    def test_discovery_ignore_invalid(self):
        resp = [{'id': 'v3.0',
                 'links': [1, 2, 3, 4],  # invalid links
                 'media-types': V3_MEDIA_TYPES,
                 'status': 'stable',
                 'updated': UPDATED}]
        self.requests_mock.get(BASE_URL, status_code=300,
                               text=_create_version_list(resp))
        self.assertDiscoveryFailure(auth_url=BASE_URL)

    def test_ignore_entry_without_links(self):
        v3 = V3_VERSION.copy()
        v3['links'] = []
        self.requests_mock.get(BASE_URL, status_code=300,
                               text=_create_version_list([v3, V2_VERSION]))
        self.assertCreatesV2(auth_url=BASE_URL)

    def test_ignore_entry_without_status(self):
        v3 = V3_VERSION.copy()
        del v3['status']
        self.requests_mock.get(BASE_URL, status_code=300,
                               text=_create_version_list([v3, V2_VERSION]))
        self.assertCreatesV2(auth_url=BASE_URL)

    def test_greater_version_than_required(self):
        versions = fixture.DiscoveryList(BASE_URL, v3_id='v3.6')
        self.requests_mock.get(BASE_URL, json=versions)
        self.assertCreatesV3(auth_url=BASE_URL, version=(3, 4))

    def test_lesser_version_than_required(self):
        versions = fixture.DiscoveryList(BASE_URL, v3_id='v3.4')
        self.requests_mock.get(BASE_URL, json=versions)
        self.assertVersionNotAvailable(auth_url=BASE_URL, version=(3, 6))

    def test_bad_response(self):
        self.requests_mock.get(BASE_URL, status_code=300, text="Ugly Duckling")
        self.assertDiscoveryFailure(auth_url=BASE_URL)

    def test_pass_client_arguments(self):
        self.requests_mock.get(BASE_URL, status_code=300, text=V2_VERSION_LIST)
        kwargs = {'original_ip': '100', 'use_keyring': False,
                  'stale_duration': 15}

        cl = self.assertCreatesV2(auth_url=BASE_URL, **kwargs)

        self.assertEqual(cl.original_ip, '100')
        self.assertEqual(cl.stale_duration, 15)
        self.assertFalse(cl.use_keyring)

    def test_overriding_stored_kwargs(self):
        self.requests_mock.get(BASE_URL, status_code=300, text=V3_VERSION_LIST)

        self.requests_mock.post("%s/auth/tokens" % V3_URL,
                                text=V3_AUTH_RESPONSE,
                                headers={'X-Subject-Token': V3_TOKEN})

        disc = discover.Discover(auth_url=BASE_URL, debug=False,
                                 username='foo')
        client = disc.create_client(debug=True, password='bar')

        self.assertIsInstance(client, v3_client.Client)
        self.assertTrue(client.debug_log)
        self.assertFalse(disc._client_kwargs['debug'])
        self.assertEqual(client.username, 'foo')
        self.assertEqual(client.password, 'bar')

    def test_available_versions(self):
        self.requests_mock.get(BASE_URL,
                               status_code=300,
                               text=V3_VERSION_ENTRY)
        disc = discover.Discover(auth_url=BASE_URL)

        versions = disc.available_versions()
        self.assertEqual(1, len(versions))
        self.assertEqual(V3_VERSION, versions[0])

    def test_unknown_client_version(self):
        V4_VERSION = {'id': 'v4.0',
                      'links': [{'href': 'http://url', 'rel': 'self'}],
                      'media-types': V3_MEDIA_TYPES,
                      'status': 'stable',
                      'updated': UPDATED}
        versions = fixture.DiscoveryList()
        versions.add_version(V4_VERSION)
        self.requests_mock.get(BASE_URL, status_code=300, json=versions)

        disc = discover.Discover(auth_url=BASE_URL)
        self.assertRaises(exceptions.DiscoveryFailure,
                          disc.create_client, version=4)

    def test_discovery_fail_for_missing_v3(self):
        versions = fixture.DiscoveryList(v2=True, v3=False)
        self.requests_mock.get(BASE_URL, status_code=300, json=versions)

        disc = discover.Discover(auth_url=BASE_URL)
        self.assertRaises(exceptions.DiscoveryFailure,
                          disc.create_client, version=(3, 0))

    def _do_discovery_call(self, token=None, **kwargs):
        self.requests_mock.get(BASE_URL, status_code=300, text=V3_VERSION_LIST)

        if not token:
            token = uuid.uuid4().hex

        url = 'http://testurl'
        a = token_endpoint.Token(url, token)
        s = session.Session(auth=a)

        # will default to true as there is a plugin on the session
        discover.Discover(s, auth_url=BASE_URL, **kwargs)

        self.assertEqual(BASE_URL, self.requests_mock.last_request.url)

    def test_setting_authenticated_true(self):
        token = uuid.uuid4().hex
        self._do_discovery_call(token)
        self.assertRequestHeaderEqual('X-Auth-Token', token)

    def test_setting_authenticated_false(self):
        self._do_discovery_call(authenticated=False)
        self.assertNotIn('X-Auth-Token',
                         self.requests_mock.last_request.headers)


class DiscoverQueryTests(utils.TestCase):

    def test_available_keystone_data(self):
        self.requests_mock.get(BASE_URL, status_code=300, text=V3_VERSION_LIST)

        disc = discover.Discover(auth_url=BASE_URL)
        versions = disc.version_data()

        self.assertEqual((2, 0), versions[0]['version'])
        self.assertEqual('stable', versions[0]['raw_status'])
        self.assertEqual(V2_URL, versions[0]['url'])
        self.assertEqual((3, 0), versions[1]['version'])
        self.assertEqual('stable', versions[1]['raw_status'])
        self.assertEqual(V3_URL, versions[1]['url'])

        version = disc.data_for('v3.0')
        self.assertEqual((3, 0), version['version'])
        self.assertEqual('stable', version['raw_status'])
        self.assertEqual(V3_URL, version['url'])

        version = disc.data_for(2)
        self.assertEqual((2, 0), version['version'])
        self.assertEqual('stable', version['raw_status'])
        self.assertEqual(V2_URL, version['url'])

        self.assertIsNone(disc.url_for('v4'))
        self.assertEqual(V3_URL, disc.url_for('v3'))
        self.assertEqual(V2_URL, disc.url_for('v2'))

    def test_available_cinder_data(self):
        text = jsonutils.dumps(CINDER_EXAMPLES)
        self.requests_mock.get(BASE_URL, status_code=300, text=text)

        v1_url = "%sv1/" % BASE_URL
        v2_url = "%sv2/" % BASE_URL

        disc = discover.Discover(auth_url=BASE_URL)
        versions = disc.version_data()

        self.assertEqual((1, 0), versions[0]['version'])
        self.assertEqual('CURRENT', versions[0]['raw_status'])
        self.assertEqual(v1_url, versions[0]['url'])
        self.assertEqual((2, 0), versions[1]['version'])
        self.assertEqual('CURRENT', versions[1]['raw_status'])
        self.assertEqual(v2_url, versions[1]['url'])

        version = disc.data_for('v2.0')
        self.assertEqual((2, 0), version['version'])
        self.assertEqual('CURRENT', version['raw_status'])
        self.assertEqual(v2_url, version['url'])

        version = disc.data_for(1)
        self.assertEqual((1, 0), version['version'])
        self.assertEqual('CURRENT', version['raw_status'])
        self.assertEqual(v1_url, version['url'])

        self.assertIsNone(disc.url_for('v3'))
        self.assertEqual(v2_url, disc.url_for('v2'))
        self.assertEqual(v1_url, disc.url_for('v1'))

    def test_available_glance_data(self):
        text = jsonutils.dumps(GLANCE_EXAMPLES)
        self.requests_mock.get(BASE_URL, text=text)

        v1_url = "%sv1/" % BASE_URL
        v2_url = "%sv2/" % BASE_URL

        disc = discover.Discover(auth_url=BASE_URL)
        versions = disc.version_data()

        self.assertEqual((1, 0), versions[0]['version'])
        self.assertEqual('SUPPORTED', versions[0]['raw_status'])
        self.assertEqual(v1_url, versions[0]['url'])
        self.assertEqual((1, 1), versions[1]['version'])
        self.assertEqual('CURRENT', versions[1]['raw_status'])
        self.assertEqual(v1_url, versions[1]['url'])
        self.assertEqual((2, 0), versions[2]['version'])
        self.assertEqual('SUPPORTED', versions[2]['raw_status'])
        self.assertEqual(v2_url, versions[2]['url'])
        self.assertEqual((2, 1), versions[3]['version'])
        self.assertEqual('SUPPORTED', versions[3]['raw_status'])
        self.assertEqual(v2_url, versions[3]['url'])
        self.assertEqual((2, 2), versions[4]['version'])
        self.assertEqual('CURRENT', versions[4]['raw_status'])
        self.assertEqual(v2_url, versions[4]['url'])

        for ver in (2, 2.1, 2.2):
            version = disc.data_for(ver)
            self.assertEqual((2, 2), version['version'])
            self.assertEqual('CURRENT', version['raw_status'])
            self.assertEqual(v2_url, version['url'])
            self.assertEqual(v2_url, disc.url_for(ver))

        for ver in (1, 1.1):
            version = disc.data_for(ver)
            self.assertEqual((1, 1), version['version'])
            self.assertEqual('CURRENT', version['raw_status'])
            self.assertEqual(v1_url, version['url'])
            self.assertEqual(v1_url, disc.url_for(ver))

        self.assertIsNone(disc.url_for('v3'))
        self.assertIsNone(disc.url_for('v2.3'))

    def test_allow_deprecated(self):
        status = 'deprecated'
        version_list = [{'id': 'v3.0',
                         'links': [{'href': V3_URL, 'rel': 'self'}],
                         'media-types': V3_MEDIA_TYPES,
                         'status': status,
                         'updated': UPDATED}]
        text = jsonutils.dumps({'versions': version_list})
        self.requests_mock.get(BASE_URL, text=text)

        disc = discover.Discover(auth_url=BASE_URL)

        # deprecated is allowed by default
        versions = disc.version_data(allow_deprecated=False)
        self.assertEqual(0, len(versions))

        versions = disc.version_data(allow_deprecated=True)
        self.assertEqual(1, len(versions))
        self.assertEqual(status, versions[0]['raw_status'])
        self.assertEqual(V3_URL, versions[0]['url'])
        self.assertEqual((3, 0), versions[0]['version'])

    def test_allow_experimental(self):
        status = 'experimental'
        version_list = [{'id': 'v3.0',
                         'links': [{'href': V3_URL, 'rel': 'self'}],
                         'media-types': V3_MEDIA_TYPES,
                         'status': status,
                         'updated': UPDATED}]
        text = jsonutils.dumps({'versions': version_list})
        self.requests_mock.get(BASE_URL, text=text)

        disc = discover.Discover(auth_url=BASE_URL)

        versions = disc.version_data()
        self.assertEqual(0, len(versions))

        versions = disc.version_data(allow_experimental=True)
        self.assertEqual(1, len(versions))
        self.assertEqual(status, versions[0]['raw_status'])
        self.assertEqual(V3_URL, versions[0]['url'])
        self.assertEqual((3, 0), versions[0]['version'])

    def test_allow_unknown(self):
        status = 'abcdef'
        version_list = fixture.DiscoveryList(BASE_URL, v2=False,
                                             v3_status=status)
        self.requests_mock.get(BASE_URL, json=version_list)
        disc = discover.Discover(auth_url=BASE_URL)

        versions = disc.version_data()
        self.assertEqual(0, len(versions))

        versions = disc.version_data(allow_unknown=True)
        self.assertEqual(1, len(versions))
        self.assertEqual(status, versions[0]['raw_status'])
        self.assertEqual(V3_URL, versions[0]['url'])
        self.assertEqual((3, 0), versions[0]['version'])

    def test_ignoring_invalid_lnks(self):
        version_list = [{'id': 'v3.0',
                         'links': [{'href': V3_URL, 'rel': 'self'}],
                         'media-types': V3_MEDIA_TYPES,
                         'status': 'stable',
                         'updated': UPDATED},
                        {'id': 'v3.1',
                         'media-types': V3_MEDIA_TYPES,
                         'status': 'stable',
                         'updated': UPDATED},
                        {'media-types': V3_MEDIA_TYPES,
                         'status': 'stable',
                         'updated': UPDATED,
                         'links': [{'href': V3_URL, 'rel': 'self'}],
                         }]

        text = jsonutils.dumps({'versions': version_list})
        self.requests_mock.get(BASE_URL, text=text)

        disc = discover.Discover(auth_url=BASE_URL)

        # raw_version_data will return all choices, even invalid ones
        versions = disc.raw_version_data()
        self.assertEqual(3, len(versions))

        # only the version with both id and links will be actually returned
        versions = disc.version_data()
        self.assertEqual(1, len(versions))


class CatalogHackTests(utils.TestCase):

    TEST_URL = 'http://keystone.server:5000/v2.0'
    OTHER_URL = 'http://other.server:5000/path'

    IDENTITY = 'identity'

    BASE_URL = 'http://keystone.server:5000/'
    V2_URL = BASE_URL + 'v2.0'
    V3_URL = BASE_URL + 'v3'

    def setUp(self):
        super(CatalogHackTests, self).setUp()
        self.hacks = _discover._VersionHacks()
        self.hacks.add_discover_hack(self.IDENTITY,
                                     re.compile('/v2.0/?$'),
                                     '/')

    def test_version_hacks(self):
        self.assertEqual(self.BASE_URL,
                         self.hacks.get_discover_hack(self.IDENTITY,
                                                      self.V2_URL))

        self.assertEqual(self.BASE_URL,
                         self.hacks.get_discover_hack(self.IDENTITY,
                                                      self.V2_URL + '/'))

        self.assertEqual(self.OTHER_URL,
                         self.hacks.get_discover_hack(self.IDENTITY,
                                                      self.OTHER_URL))

    def test_ignored_non_service_type(self):
        self.assertEqual(self.V2_URL,
                         self.hacks.get_discover_hack('other', self.V2_URL))


class DiscoverUtils(utils.TestCase):

    def test_version_number(self):
        def assertVersion(inp, out):
            self.assertEqual(out, _discover.normalize_version_number(inp))

        def versionRaises(inp):
            self.assertRaises(TypeError,
                              _discover.normalize_version_number,
                              inp)

        assertVersion('v1.2', (1, 2))
        assertVersion('v11', (11, 0))
        assertVersion('1.2', (1, 2))
        assertVersion('1.5.1', (1, 5, 1))
        assertVersion('1', (1, 0))
        assertVersion(1, (1, 0))
        assertVersion(5.2, (5, 2))
        assertVersion((6, 1), (6, 1))
        assertVersion([1, 4], (1, 4))

        versionRaises('hello')
        versionRaises('1.a')
        versionRaises('vacuum')
