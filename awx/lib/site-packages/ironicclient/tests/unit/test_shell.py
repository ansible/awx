# -*- coding: utf-8 -*-
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.

import json
import os
import re
import sys

import fixtures
import httplib2
import httpretty
from keystoneclient import exceptions as keystone_exc
from keystoneclient.fixture import v2 as ks_v2_fixture
from keystoneclient.fixture import v3 as ks_v3_fixture
import mock
import six
import testtools
from testtools import matchers

from ironicclient import exc
from ironicclient import shell as ironic_shell
from ironicclient.tests.unit import keystone_client_fixtures
from ironicclient.tests.unit import utils

FAKE_ENV = {'OS_USERNAME': 'username',
            'OS_PASSWORD': 'password',
            'OS_TENANT_NAME': 'tenant_name',
            'OS_AUTH_URL': 'http://no.where/v2.0/'}

FAKE_ENV_KEYSTONE_V2 = {
    'OS_USERNAME': 'username',
    'OS_PASSWORD': 'password',
    'OS_TENANT_NAME': 'tenant_name',
    'OS_AUTH_URL': keystone_client_fixtures.BASE_URL,
}

FAKE_ENV_KEYSTONE_V3 = {
    'OS_USERNAME': 'username',
    'OS_PASSWORD': 'password',
    'OS_TENANT_NAME': 'tenant_name',
    'OS_AUTH_URL': keystone_client_fixtures.BASE_URL,
    'OS_USER_DOMAIN_ID': 'default',
    'OS_PROJECT_DOMAIN_ID': 'default',
}


class ShellTest(utils.BaseTestCase):
    re_options = re.DOTALL | re.MULTILINE

    # Patch os.environ to avoid required auth info.
    def make_env(self, exclude=None):
        env = dict((k, v) for k, v in FAKE_ENV.items() if k != exclude)
        self.useFixture(fixtures.MonkeyPatch('os.environ', env))

    def setUp(self):
        super(ShellTest, self).setUp()

    def shell(self, argstr):
        orig = sys.stdout
        try:
            sys.stdout = six.StringIO()
            _shell = ironic_shell.IronicShell()
            _shell.main(argstr.split())
        except SystemExit:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.assertEqual(0, exc_value.code)
        finally:
            out = sys.stdout.getvalue()
            sys.stdout.close()
            sys.stdout = orig
        return out

    def test_help_unknown_command(self):
        self.assertRaises(exc.CommandError, self.shell, 'help foofoo')

    def test_debug(self):
        httplib2.debuglevel = 0
        self.shell('--debug help')
        self.assertEqual(1, httplib2.debuglevel)

    def test_help(self):
        required = [
            '.*?^usage: ironic',
            '.*?^ +bash-completion',
            '.*?^See "ironic help COMMAND" '
            'for help on a specific command',
        ]
        for argstr in ['--help', 'help']:
            help_text = self.shell(argstr)
            for r in required:
                self.assertThat(help_text,
                                matchers.MatchesRegex(r,
                                                      self.re_options))

    def test_help_on_subcommand(self):
        required = [
            '.*?^usage: ironic chassis-show',
            ".*?^Show detailed information about a chassis",
        ]
        argstrings = [
            'help chassis-show',
        ]
        for argstr in argstrings:
            help_text = self.shell(argstr)
            for r in required:
                self.assertThat(help_text,
                                matchers.MatchesRegex(r, self.re_options))

    def test_auth_param(self):
        self.make_env(exclude='OS_USERNAME')
        self.test_help()

    @mock.patch('sys.stdin', side_effect=mock.MagicMock)
    @mock.patch('getpass.getpass', return_value='password')
    def test_password_prompted(self, mock_getpass, mock_stdin):
        self.make_env(exclude='OS_PASSWORD')
        # We will get a Connection Refused because there is no keystone.
        self.assertRaises(keystone_exc.ConnectionRefused,
                          self.shell, 'node-list')
        # Make sure we are actually prompted.
        mock_getpass.assert_called_with('OpenStack Password: ')

    @mock.patch('sys.stdin', side_effect=mock.MagicMock)
    @mock.patch('getpass.getpass', side_effect=EOFError)
    def test_password_prompted_ctrlD(self, mock_getpass, mock_stdin):
        self.make_env(exclude='OS_PASSWORD')
        # We should get Command Error because we mock Ctl-D.
        self.assertRaises(exc.CommandError,
                          self.shell, 'node-list')
        # Make sure we are actually prompted.
        mock_getpass.assert_called_with('OpenStack Password: ')

    @mock.patch('sys.stdin')
    def test_no_password_no_tty(self, mock_stdin):
        # delete the isatty attribute so that we do not get
        # prompted when manually running the tests
        del mock_stdin.isatty
        required = ('You must provide a password'
                    ' via either --os-password, env[OS_PASSWORD],'
                    ' or prompted response',)
        self.make_env(exclude='OS_PASSWORD')
        try:
            self.shell('node-list')
        except exc.CommandError as message:
            self.assertEqual(required, message.args)
        else:
            self.fail('CommandError not raised')

    def test_bash_completion(self):
        stdout = self.shell('bash-completion')
        # just check we have some output
        required = [
            '.*--driver_info',
            '.*--chassis_uuid',
            '.*help',
            '.*node-create',
            '.*chassis-create']
        for r in required:
            self.assertThat(stdout,
                            matchers.MatchesRegex(r, self.re_options))

    def test_ironic_api_version(self):
        self.shell('--ironic-api-version 1.2 help')
        self.shell('--ironic-api-version latest help')
        self.assertRaises(exc.CommandError,
                          self.shell, '--ironic-api-version 1.2.1 help')


class TestCase(testtools.TestCase):

    tokenid = keystone_client_fixtures.TOKENID

    def set_fake_env(self, fake_env):
        client_env = ('OS_USERNAME', 'OS_PASSWORD', 'OS_TENANT_ID',
                      'OS_TENANT_NAME', 'OS_AUTH_URL', 'OS_REGION_NAME',
                      'OS_AUTH_TOKEN', 'OS_NO_CLIENT_AUTH', 'OS_SERVICE_TYPE',
                      'OS_ENDPOINT_TYPE')

        for key in client_env:
            self.useFixture(
                fixtures.EnvironmentVariable(key, fake_env.get(key)))

    # required for testing with Python 2.6
    def assertRegexpMatches(self, text, expected_regexp, msg=None):
        """Fail the test unless the text matches the regular expression."""
        if isinstance(expected_regexp, six.string_types):
            expected_regexp = re.compile(expected_regexp)
        if not expected_regexp.search(text):
            msg = msg or "Regexp didn't match"
            msg = '%s: %r not found in %r' % (
                msg, expected_regexp.pattern, text)
            raise self.failureException(msg)

    def register_keystone_v2_token_fixture(self):
        v2_token = ks_v2_fixture.Token(token_id=self.tokenid)
        service = v2_token.add_service('baremetal')
        service.add_endpoint('http://ironic.example.com', region='RegionOne')
        httpretty.register_uri(
            httpretty.POST,
            '%s/tokens' % (keystone_client_fixtures.V2_URL),
            body=json.dumps(v2_token))

    def register_keystone_v3_token_fixture(self):
        v3_token = ks_v3_fixture.Token()
        service = v3_token.add_service('baremetal')
        service.add_standard_endpoints(public='http://ironic.example.com')
        httpretty.register_uri(
            httpretty.POST,
            '%s/auth/tokens' % (keystone_client_fixtures.V3_URL),
            body=json.dumps(v3_token),
            adding_headers={'X-Subject-Token': self.tokenid})

    def register_keystone_auth_fixture(self):
        self.register_keystone_v2_token_fixture()
        self.register_keystone_v3_token_fixture()
        httpretty.register_uri(
            httpretty.GET,
            keystone_client_fixtures.BASE_URL,
            body=keystone_client_fixtures.keystone_request_callback)


class ShellTestNoMox(TestCase):
    def setUp(self):
        super(ShellTestNoMox, self).setUp()
        # httpretty doesn't work as expected if http proxy environment
        # variable is set.
        os.environ = dict((k, v) for (k, v) in os.environ.items()
                          if k.lower() not in ('http_proxy', 'https_proxy'))
        self.set_fake_env(FAKE_ENV_KEYSTONE_V2)

    def shell(self, argstr):
        orig = sys.stdout
        try:
            sys.stdout = six.StringIO()
            _shell = ironic_shell.IronicShell()
            _shell.main(argstr.split())
            self.subcommands = _shell.subcommands.keys()
        except SystemExit:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.assertEqual(0, exc_value.code)
        finally:
            out = sys.stdout.getvalue()
            sys.stdout.close()
            sys.stdout = orig

        return out

    @httpretty.activate
    def test_node_list(self):
        self.register_keystone_auth_fixture()
        resp_dict = {"nodes": [
                     {"instance_uuid": "null",
                      "uuid": "351a82d6-9f04-4c36-b79a-a38b9e98ff71",
                      "links": [{"href": "http://ironic.example.com:6385/"
                                 "v1/nodes/foo",
                                 "rel": "self"},
                                {"href": "http://ironic.example.com:6385/"
                                 "nodes/foo",
                                 "rel": "bookmark"}],
                      "maintenance": "false",
                      "provision_state": "null",
                      "power_state": "power off"},
                     {"instance_uuid": "null",
                      "uuid": "66fbba13-29e8-4b8a-9e80-c655096a40d3",
                      "links": [{"href": "http://ironic.example.com:6385/"
                                 "v1/nodes/foo2",
                                 "rel": "self"},
                                {"href": "http://ironic.example.com:6385/"
                                 "nodes/foo2",
                                 "rel": "bookmark"}],
                      "maintenance": "false",
                      "provision_state": "null",
                      "power_state": "power off"}]}
        httpretty.register_uri(
            httpretty.GET,
            'http://ironic.example.com/v1/nodes',
            status=200,
            content_type='application/json; charset=UTF-8',
            body=json.dumps(resp_dict))

        event_list_text = self.shell('node-list')

        required = [
            '351a82d6-9f04-4c36-b79a-a38b9e98ff71',
            '66fbba13-29e8-4b8a-9e80-c655096a40d3',
        ]

        for r in required:
            self.assertRegexpMatches(event_list_text, r)


class ShellTestNoMoxV3(ShellTestNoMox):

    def _set_fake_env(self):
        self.set_fake_env(FAKE_ENV_KEYSTONE_V3)
