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

import re
import sys

import fixtures
from keystoneclient import fixture
import mock
import requests_mock
import six
import testtools
import uuid

import troveclient.client
from troveclient import exceptions
import troveclient.shell

try:
    import json
except ImportError:
    import simplejson as json

V2_URL = "http://no.where/v2.0"
V3_URL = "http://no.where/v3"

FAKE_V2_ENV = {'OS_USERNAME': uuid.uuid4().hex,
               'OS_PASSWORD': uuid.uuid4().hex,
               'OS_TENANT_ID': uuid.uuid4().hex,
               'OS_AUTH_URL': V2_URL}

FAKE_V3_ENV = {'OS_USERNAME': uuid.uuid4().hex,
               'OS_PASSWORD': uuid.uuid4().hex,
               'OS_PROJECT_ID': uuid.uuid4().hex,
               'OS_USER_DOMAIN_NAME': uuid.uuid4().hex,
               'OS_AUTH_URL': V3_URL}

UPDATED = '2013-03-06T00:00:00Z'

TEST_SERVICE_CATALOG = [{
    "endpoints": [{
        "adminURL": "http://no.where/admin",
        "region": "RegionOne",
        "internalURL": "http://no.where/internal",
        "publicURL": "http://no.where/v1.0"
    }],
    "type": "database",
    "name": "trove"
}]


def _create_ver_list(versions):
    return {'versions': {'values': versions}}


class ShellTest(testtools.TestCase):

    version_id = u'v2.0'
    links = [{u'href': u'http://no.where/v2.0', u'rel': u'self'}]

    v2_version = fixture.V2Discovery(V2_URL)
    v2_version.updated_str = UPDATED

    v2_auth_response = json.dumps({
        "access": {
            "token": {
                "expires_at": "2020-01-01T00:00:10.000123Z",
                "id": 'fakeToken',
                "tenant": {
                    "id": uuid.uuid4().hex
                },
            },
            "user": {
                "id": uuid.uuid4().hex
            },
            "serviceCatalog": TEST_SERVICE_CATALOG,
        },
    })

    def make_env(self, exclude=None, fake_env=FAKE_V2_ENV):
        env = dict((k, v) for k, v in fake_env.items() if k != exclude)
        self.useFixture(fixtures.MonkeyPatch('os.environ', env))

    def setUp(self):
        super(ShellTest, self).setUp()
        self.useFixture(fixtures.MonkeyPatch(
                        'troveclient.client.get_client_class',
                        mock.MagicMock))

    def shell(self, argstr, exitcodes=(0,)):
        orig = sys.stdout
        orig_stderr = sys.stderr
        try:
            sys.stdout = six.StringIO()
            sys.stderr = six.StringIO()
            _shell = troveclient.shell.OpenStackTroveShell()
            _shell.main(argstr.split())
        except SystemExit:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.assertIn(exc_value.code, exitcodes)
        finally:
            stdout = sys.stdout.getvalue()
            sys.stdout.close()
            sys.stdout = orig
            stderr = sys.stderr.getvalue()
            sys.stderr.close()
            sys.stderr = orig_stderr
        return (stdout, stderr)

    def register_keystone_discovery_fixture(self, mreq):
        mreq.register_uri('GET', V2_URL,
                          json=_create_ver_list([self.v2_version]),
                          status_code=200)

    def test_help_unknown_command(self):
        self.assertRaises(exceptions.CommandError, self.shell, 'help foofoo')

    def test_help(self):
        required = [
            '.*?^usage: ',
            '.*?^See "trove help COMMAND" for help on a specific command',
        ]
        stdout, stderr = self.shell('help')
        for r in required:
            self.assertThat(
                (stdout + stderr),
                testtools.matchers.MatchesRegex(r, re.DOTALL | re.MULTILINE))

    def test_no_username(self):
        required = ('You must provide a username'
                    ' via either --os-username or'
                    ' env[OS_USERNAME]')
        self.make_env(exclude='OS_USERNAME')
        try:
            self.shell('list')
        except exceptions.CommandError as message:
            self.assertEqual(required, message.args[0])
        else:
            self.fail('CommandError not raised')

    def test_no_auth_url(self):
        required = ('You must provide an auth url'
                    ' via either --os-auth-url or env[OS_AUTH_URL] '
                    'or specify an auth_system which defines a default '
                    'url with --os-auth-system or env[OS_AUTH_SYSTEM]',)
        self.make_env(exclude='OS_AUTH_URL')
        try:
            self.shell('list')
        except exceptions.CommandError as message:
            self.assertEqual(required, message.args)
        else:
            self.fail('CommandError not raised')

    @mock.patch('keystoneclient._discover.get_version_data',
                return_value=[{u'status': u'stable', u'id': version_id,
                               u'links': links}])
    @mock.patch('troveclient.v1.datastores.DatastoreVersions.list')
    @requests_mock.Mocker()
    def test_datastore_version_list(self, mock_discover,
                                    mock_list, mock_requests):
        expected = '\n'.join([
            '+----+------+',
            '| ID | Name |',
            '+----+------+',
            '+----+------+',
            ''
        ])
        self.make_env()
        self.register_keystone_discovery_fixture(mock_requests)
        mock_requests.register_uri('POST', "http://no.where/v2.0/tokens",
                                   text=self.v2_auth_response)
        stdout, stderr = self.shell('datastore-version-list XXX')
        self.assertEqual(expected, (stdout + stderr))

    @mock.patch('keystoneclient._discover.get_version_data',
                return_value=[{u'status': u'stable', u'id': version_id,
                               u'links': links}])
    @mock.patch('troveclient.v1.datastores.Datastores.list')
    @requests_mock.Mocker()
    def test_get_datastore_list(self, mock_discover,
                                mock_list, mock_requests):
        expected = '\n'.join([
            '+----+------+',
            '| ID | Name |',
            '+----+------+',
            '+----+------+',
            ''
        ])
        self.make_env()
        self.register_keystone_discovery_fixture(mock_requests)
        mock_requests.register_uri('POST', "http://no.where/v2.0/tokens",
                                   text=self.v2_auth_response)
        stdout, stderr = self.shell('datastore-list')
        self.assertEqual(expected, (stdout + stderr))


class ShellTestKeystoneV3(ShellTest):

    version_id = u'v3'
    links = [{u'href': u'http://no.where/v3', u'rel': u'self'}]

    v3_version = fixture.V3Discovery(V3_URL)
    v3_version.updated_str = UPDATED

    test_service_catalog = [{
        "endpoints": [{
            "url": "http://no.where/v1.0/",
            "region": "RegionOne",
            "interface": "public"
        }, {
            "url": "http://no.where/v1.0",
            "region": "RegionOne",
            "interface": "internal"
        }, {
            "url": "http://no.where/v1.0",
            "region": "RegionOne",
            "interface": "admin"
        }],
        "type": "database",
        "name": "trove"
    }]

    service_catalog2 = [{
        "endpoints": [{
            "url": "http://no.where/vXYZ",
            "region": "RegionOne",
            "interface": "public"
        }],
        "type": "database",
        "name": "trove"
    }]

    v3_auth_response = json.dumps({
        "token": {
            "methods": [
                "token",
                "password"
            ],
            "expires_at": "2020-01-01T00:00:10.000123Z",
            "project": {
                "domain": {
                    "id": uuid.uuid4().hex,
                    "name": uuid.uuid4().hex
                },
                "id": uuid.uuid4().hex,
                "name": uuid.uuid4().hex
            },
            "user": {
                "domain": {
                    "id": uuid.uuid4().hex,
                    "name": uuid.uuid4().hex
                },
                "id": uuid.uuid4().hex,
                "name": uuid.uuid4().hex
            },
            "issued_at": "2013-05-29T16:55:21.468960Z",
            "catalog": test_service_catalog
        },
    })

    def make_env(self, exclude=None, fake_env=FAKE_V3_ENV):
        if 'OS_AUTH_URL' in fake_env:
            fake_env.update({'OS_AUTH_URL': 'http://no.where/v3'})
        env = dict((k, v) for k, v in fake_env.items() if k != exclude)
        self.useFixture(fixtures.MonkeyPatch('os.environ', env))

    def register_keystone_discovery_fixture(self, mreq):
        v3_url = "http://no.where/v3"
        v3_version = fixture.V3Discovery(v3_url)
        mreq.register_uri('GET', v3_url, json=_create_ver_list([v3_version]),
                          status_code=200)

    def test_no_project_id(self):
        required = (
            u'You must provide a tenant_name, tenant_id, '
            u'project_id or project_name (with '
            u'project_domain_name or project_domain_id) via '
            u'  --os-tenant-name (env[OS_TENANT_NAME]),'
            u'  --os-tenant-id (env[OS_TENANT_ID]),'
            u'  --os-project-id (env[OS_PROJECT_ID])'
            u'  --os-project-name (env[OS_PROJECT_NAME]),'
            u'  --os-project-domain-id '
            u'(env[OS_PROJECT_DOMAIN_ID])'
            u'  --os-project-domain-name '
            u'(env[OS_PROJECT_DOMAIN_NAME])'
        )
        self.make_env(exclude='OS_PROJECT_ID')
        try:
            self.shell('list')
        except exceptions.CommandError as message:
            self.assertEqual(required, message.args[0])
        else:
            self.fail('CommandError not raised')

    @mock.patch('keystoneclient._discover.get_version_data',
                return_value=[{u'status': u'stable', u'id': version_id,
                               u'links': links}])
    @mock.patch('troveclient.v1.datastores.DatastoreVersions.list')
    @requests_mock.Mocker()
    def test_datastore_version_list(self, mock_discover,
                                    mock_list, mock_requests):
        expected = '\n'.join([
            '+----+------+',
            '| ID | Name |',
            '+----+------+',
            '+----+------+',
            ''
        ])
        self.make_env()
        self.register_keystone_discovery_fixture(mock_requests)
        mock_requests.register_uri('POST', "http://no.where/v3/auth/tokens",
                                   headers={'X-Subject-Token': 'fakeToken'},
                                   text=self.v3_auth_response)
        stdout, stderr = self.shell('datastore-version-list XXX')
        self.assertEqual(expected, (stdout + stderr))

    @mock.patch('keystoneclient._discover.get_version_data',
                return_value=[{u'status': u'stable', u'id': version_id,
                               u'links': links}])
    @mock.patch('troveclient.v1.datastores.Datastores.list')
    @requests_mock.Mocker()
    def test_get_datastore_list(self, mock_discover,
                                mock_list, mock_requests):
        expected = '\n'.join([
            '+----+------+',
            '| ID | Name |',
            '+----+------+',
            '+----+------+',
            ''
        ])
        self.make_env()
        self.register_keystone_discovery_fixture(mock_requests)
        mock_requests.register_uri('POST', "http://no.where/v3/auth/tokens",
                                   headers={'X-Subject-Token': 'fakeToken'},
                                   text=self.v3_auth_response)
        stdout, stderr = self.shell('datastore-list')
        self.assertEqual(expected, (stdout + stderr))

    @mock.patch('keystoneclient._discover.get_version_data',
                return_value=[{u'status': u'stable', u'id': version_id,
                               u'links': links}])
    @requests_mock.Mocker()
    def test_invalid_client_version(self, mock_discover,
                                    mock_requests):
        response = json.loads(self.v3_auth_response)
        response['token']['catalog'] = self.service_catalog2

        self.make_env()
        self.register_keystone_discovery_fixture(mock_requests)
        mock_requests.register_uri('POST', "http://no.where/v3/auth/tokens",
                                   headers={'X-Subject-Token': 'fakeToken'},
                                   text=json.dumps(response))
        try:
            self.shell('datastore-list')
        except exceptions.UnsupportedVersion:
            pass
        else:
            self.fail('UnsupportedVersion not raised')
