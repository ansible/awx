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

import argparse
import json
import logging
import os
import sys
import uuid

import fixtures
import mock
import six
import testtools
from testtools import matchers

from keystoneclient import exceptions
from keystoneclient import session
from keystoneclient import shell as openstack_shell
from keystoneclient.tests.unit import utils
from keystoneclient.v2_0 import shell as shell_v2_0


DEFAULT_USERNAME = 'username'
DEFAULT_PASSWORD = 'password'
DEFAULT_TENANT_ID = 'tenant_id'
DEFAULT_TENANT_NAME = 'tenant_name'
DEFAULT_AUTH_URL = 'http://127.0.0.1:5000/v2.0/'


# Make a fake shell object, a helping wrapper to call it
def shell(cmd):
    openstack_shell.OpenStackIdentityShell().main(cmd.split())


class NoExitArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise exceptions.CommandError(message)


class ShellTest(utils.TestCase):

    FAKE_ENV = {
        'OS_USERNAME': DEFAULT_USERNAME,
        'OS_PASSWORD': DEFAULT_PASSWORD,
        'OS_TENANT_ID': DEFAULT_TENANT_ID,
        'OS_TENANT_NAME': DEFAULT_TENANT_NAME,
        'OS_AUTH_URL': DEFAULT_AUTH_URL,
    }

    def _tolerant_shell(self, cmd):
        t_shell = openstack_shell.OpenStackIdentityShell(NoExitArgumentParser)
        t_shell.main(cmd.split())

    # Patch os.environ to avoid required auth info.
    def setUp(self):

        super(ShellTest, self).setUp()
        for var in os.environ:
            if var.startswith("OS_"):
                self.useFixture(fixtures.EnvironmentVariable(var, ""))

        for var in self.FAKE_ENV:
            self.useFixture(fixtures.EnvironmentVariable(var,
                            self.FAKE_ENV[var]))

    def test_help_unknown_command(self):
        self.assertRaises(exceptions.CommandError, shell, 'help %s'
                          % uuid.uuid4().hex)

    def shell(self, argstr):
        orig = sys.stdout
        clean_env = {}
        _old_env, os.environ = os.environ, clean_env.copy()
        try:
            sys.stdout = six.StringIO()
            _shell = openstack_shell.OpenStackIdentityShell()
            _shell.main(argstr.split())
        except SystemExit:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.assertEqual(exc_value.code, 0)
        finally:
            out = sys.stdout.getvalue()
            sys.stdout.close()
            sys.stdout = orig
            os.environ = _old_env
        return out

    def test_help_no_args(self):
        do_tenant_mock = mock.MagicMock()
        with mock.patch('keystoneclient.shell.OpenStackIdentityShell.do_help',
                        do_tenant_mock):
            self.shell('')
            assert do_tenant_mock.called

    def test_help(self):
        required = 'usage:'
        help_text = self.shell('help')
        self.assertThat(help_text,
                        matchers.MatchesRegex(required))

    def test_help_command(self):
        required = 'usage: keystone user-create'
        help_text = self.shell('help user-create')
        self.assertThat(help_text,
                        matchers.MatchesRegex(required))

    def test_help_command_with_no_action_choices(self):
        required = 'usage: keystone user-update'
        help_text = self.shell('help user-update')
        self.assertThat(help_text,
                        matchers.MatchesRegex(required))

    def test_auth_no_credentials(self):
        with testtools.ExpectedException(
                exceptions.CommandError, 'Expecting'):
            self.shell('user-list')

    def test_debug(self):
        logging_mock = mock.MagicMock()
        with mock.patch('logging.basicConfig', logging_mock):
            self.assertRaises(exceptions.CommandError,
                              self.shell, '--debug user-list')
            self.assertTrue(logging_mock.called)
            self.assertEqual([(), {'level': logging.DEBUG}],
                             list(logging_mock.call_args))

    def test_auth_password_authurl_no_username(self):
        with testtools.ExpectedException(
                exceptions.CommandError,
                'Expecting a username provided via either'):
            self.shell('--os-password=%s --os-auth-url=%s user-list'
                       % (uuid.uuid4().hex, uuid.uuid4().hex))

    def test_auth_username_password_no_authurl(self):
        with testtools.ExpectedException(
                exceptions.CommandError, 'Expecting an auth URL via either'):
            self.shell('--os-password=%s --os-username=%s user-list'
                       % (uuid.uuid4().hex, uuid.uuid4().hex))

    def test_token_no_endpoint(self):
        with testtools.ExpectedException(
                exceptions.CommandError, 'Expecting an endpoint provided'):
            self.shell('--os-token=%s user-list' % uuid.uuid4().hex)

    def test_endpoint_no_token(self):
        with testtools.ExpectedException(
                exceptions.CommandError, 'Expecting a token provided'):
            self.shell('--os-endpoint=http://10.0.0.1:5000/v2.0/ user-list')

    def test_shell_args(self):
        do_tenant_mock = mock.MagicMock()
        with mock.patch('keystoneclient.v2_0.shell.do_user_list',
                        do_tenant_mock):
            shell('user-list')
            assert do_tenant_mock.called
            ((a, b), c) = do_tenant_mock.call_args
            actual = (b.os_auth_url, b.os_password, b.os_tenant_id,
                      b.os_tenant_name, b.os_username,
                      b.os_identity_api_version)
            expect = (DEFAULT_AUTH_URL, DEFAULT_PASSWORD, DEFAULT_TENANT_ID,
                      DEFAULT_TENANT_NAME, DEFAULT_USERNAME, '')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))

            # Old_style options
            shell('--os_auth_url http://0.0.0.0:5000/ --os_password xyzpdq '
                  '--os_tenant_id 1234 --os_tenant_name fred '
                  '--os_username barney '
                  '--os_identity_api_version 2.0 user-list')
            assert do_tenant_mock.called
            ((a, b), c) = do_tenant_mock.call_args
            actual = (b.os_auth_url, b.os_password, b.os_tenant_id,
                      b.os_tenant_name, b.os_username,
                      b.os_identity_api_version)
            expect = ('http://0.0.0.0:5000/', 'xyzpdq', '1234',
                      'fred', 'barney', '2.0')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))

            # New-style options
            shell('--os-auth-url http://1.1.1.1:5000/ --os-password xyzpdq '
                  '--os-tenant-id 4321 --os-tenant-name wilma '
                  '--os-username betty '
                  '--os-identity-api-version 2.0 user-list')
            assert do_tenant_mock.called
            ((a, b), c) = do_tenant_mock.call_args
            actual = (b.os_auth_url, b.os_password, b.os_tenant_id,
                      b.os_tenant_name, b.os_username,
                      b.os_identity_api_version)
            expect = ('http://1.1.1.1:5000/', 'xyzpdq', '4321',
                      'wilma', 'betty', '2.0')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))

            # Test keyring options
            shell('--os-auth-url http://1.1.1.1:5000/ --os-password xyzpdq '
                  '--os-tenant-id 4321 --os-tenant-name wilma '
                  '--os-username betty '
                  '--os-identity-api-version 2.0 '
                  '--os-cache '
                  '--stale-duration 500 '
                  '--force-new-token user-list')
            assert do_tenant_mock.called
            ((a, b), c) = do_tenant_mock.call_args
            actual = (b.os_auth_url, b.os_password, b.os_tenant_id,
                      b.os_tenant_name, b.os_username,
                      b.os_identity_api_version, b.os_cache,
                      b.stale_duration, b.force_new_token)
            expect = ('http://1.1.1.1:5000/', 'xyzpdq', '4321',
                      'wilma', 'betty', '2.0', True, '500', True)
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))

            # Test os-identity-api-version fall back to 2.0
            shell('--os-identity-api-version 3.0 user-list')
            assert do_tenant_mock.called
            self.assertTrue(b.os_identity_api_version, '2.0')

    def test_shell_user_create_args(self):
        """Test user-create args."""
        do_uc_mock = mock.MagicMock()
        # grab the decorators for do_user_create
        uc_func = getattr(shell_v2_0, 'do_user_create')
        do_uc_mock.arguments = getattr(uc_func, 'arguments', [])
        with mock.patch('keystoneclient.v2_0.shell.do_user_create',
                        do_uc_mock):

            # Old_style options
            # Test case with one --tenant_id args present: ec2 creds
            shell('user-create --name=FOO '
                  '--pass=secret --tenant_id=barrr --enabled=true')
            assert do_uc_mock.called
            ((a, b), c) = do_uc_mock.call_args
            actual = (b.os_auth_url, b.os_password, b.os_tenant_id,
                      b.os_tenant_name, b.os_username,
                      b.os_identity_api_version)
            expect = (DEFAULT_AUTH_URL, DEFAULT_PASSWORD, DEFAULT_TENANT_ID,
                      DEFAULT_TENANT_NAME, DEFAULT_USERNAME, '')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))
            actual = (b.tenant_id, b.name, b.passwd, b.enabled)
            expect = ('barrr', 'FOO', 'secret', 'true')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))

            # New-style options
            # Test case with one --tenant args present: ec2 creds
            shell('user-create --name=foo '
                  '--pass=secret --tenant=BARRR --enabled=true')
            assert do_uc_mock.called
            ((a, b), c) = do_uc_mock.call_args
            actual = (b.os_auth_url, b.os_password, b.os_tenant_id,
                      b.os_tenant_name, b.os_username,
                      b.os_identity_api_version)
            expect = (DEFAULT_AUTH_URL, DEFAULT_PASSWORD, DEFAULT_TENANT_ID,
                      DEFAULT_TENANT_NAME, DEFAULT_USERNAME, '')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))
            actual = (b.tenant, b.name, b.passwd, b.enabled)
            expect = ('BARRR', 'foo', 'secret', 'true')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))

            # New-style options
            # Test case with one --tenant-id args present: ec2 creds
            shell('user-create --name=foo '
                  '--pass=secret --tenant-id=BARRR --enabled=true')
            assert do_uc_mock.called
            ((a, b), c) = do_uc_mock.call_args
            actual = (b.os_auth_url, b.os_password, b.os_tenant_id,
                      b.os_tenant_name, b.os_username,
                      b.os_identity_api_version)
            expect = (DEFAULT_AUTH_URL, DEFAULT_PASSWORD, DEFAULT_TENANT_ID,
                      DEFAULT_TENANT_NAME, DEFAULT_USERNAME, '')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))
            actual = (b.tenant, b.name, b.passwd, b.enabled)
            expect = ('BARRR', 'foo', 'secret', 'true')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))

            # Old_style options
            # Test case with --os_tenant_id and --tenant_id args present
            shell('--os_tenant_id=os-tenant user-create --name=FOO '
                  '--pass=secret --tenant_id=barrr --enabled=true')
            assert do_uc_mock.called
            ((a, b), c) = do_uc_mock.call_args
            actual = (b.os_auth_url, b.os_password, b.os_tenant_id,
                      b.os_tenant_name, b.os_username,
                      b.os_identity_api_version)
            expect = (DEFAULT_AUTH_URL, DEFAULT_PASSWORD, 'os-tenant',
                      DEFAULT_TENANT_NAME, DEFAULT_USERNAME, '')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))
            actual = (b.tenant_id, b.name, b.passwd, b.enabled)
            expect = ('barrr', 'FOO', 'secret', 'true')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))

            # New-style options
            # Test case with --os-tenant-id and --tenant-id args present
            shell('--os-tenant-id=ostenant user-create --name=foo '
                  '--pass=secret --tenant-id=BARRR --enabled=true')
            assert do_uc_mock.called
            ((a, b), c) = do_uc_mock.call_args
            actual = (b.os_auth_url, b.os_password, b.os_tenant_id,
                      b.os_tenant_name, b.os_username,
                      b.os_identity_api_version)
            expect = (DEFAULT_AUTH_URL, DEFAULT_PASSWORD, 'ostenant',
                      DEFAULT_TENANT_NAME, DEFAULT_USERNAME, '')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))
            actual = (b.tenant, b.name, b.passwd, b.enabled)
            expect = ('BARRR', 'foo', 'secret', 'true')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))

    def test_do_tenant_create(self):
        do_tenant_mock = mock.MagicMock()
        with mock.patch('keystoneclient.v2_0.shell.do_tenant_create',
                        do_tenant_mock):
            shell('tenant-create')
            assert do_tenant_mock.called
            # FIXME(dtroyer): how do you test the decorators?
            # shell('tenant-create --tenant-name wilma '
            #        '--description "fred\'s wife"')
            # assert do_tenant_mock.called

    def test_do_tenant_list(self):
        do_tenant_mock = mock.MagicMock()
        with mock.patch('keystoneclient.v2_0.shell.do_tenant_list',
                        do_tenant_mock):
            shell('tenant-list')
            assert do_tenant_mock.called

    def test_shell_tenant_id_args(self):
        """Test a corner case where --tenant_id appears on the
           command-line twice.
        """
        do_ec2_mock = mock.MagicMock()
        # grab the decorators for do_ec2_create_credentials
        ec2_func = getattr(shell_v2_0, 'do_ec2_credentials_create')
        do_ec2_mock.arguments = getattr(ec2_func, 'arguments', [])
        with mock.patch('keystoneclient.v2_0.shell.do_ec2_credentials_create',
                        do_ec2_mock):

            # Old_style options
            # Test case with one --tenant_id args present: ec2 creds
            shell('ec2-credentials-create '
                  '--tenant_id=ec2-tenant --user_id=ec2-user')
            assert do_ec2_mock.called
            ((a, b), c) = do_ec2_mock.call_args
            actual = (b.os_auth_url, b.os_password, b.os_tenant_id,
                      b.os_tenant_name, b.os_username,
                      b.os_identity_api_version)
            expect = (DEFAULT_AUTH_URL, DEFAULT_PASSWORD, DEFAULT_TENANT_ID,
                      DEFAULT_TENANT_NAME, DEFAULT_USERNAME, '')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))
            actual = (b.tenant_id, b.user_id)
            expect = ('ec2-tenant', 'ec2-user')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))

            # New-style options
            # Test case with one --tenant-id args present: ec2 creds
            shell('ec2-credentials-create '
                  '--tenant-id=dash-tenant --user-id=dash-user')
            assert do_ec2_mock.called
            ((a, b), c) = do_ec2_mock.call_args
            actual = (b.os_auth_url, b.os_password, b.os_tenant_id,
                      b.os_tenant_name, b.os_username,
                      b.os_identity_api_version)
            expect = (DEFAULT_AUTH_URL, DEFAULT_PASSWORD, DEFAULT_TENANT_ID,
                      DEFAULT_TENANT_NAME, DEFAULT_USERNAME, '')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))
            actual = (b.tenant_id, b.user_id)
            expect = ('dash-tenant', 'dash-user')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))

            # Old_style options
            # Test case with two --tenant_id args present
            shell('--os_tenant_id=os-tenant ec2-credentials-create '
                  '--tenant_id=ec2-tenant --user_id=ec2-user')
            assert do_ec2_mock.called
            ((a, b), c) = do_ec2_mock.call_args
            actual = (b.os_auth_url, b.os_password, b.os_tenant_id,
                      b.os_tenant_name, b.os_username,
                      b.os_identity_api_version)
            expect = (DEFAULT_AUTH_URL, DEFAULT_PASSWORD, 'os-tenant',
                      DEFAULT_TENANT_NAME, DEFAULT_USERNAME, '')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))
            actual = (b.tenant_id, b.user_id)
            expect = ('ec2-tenant', 'ec2-user')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))

            # New-style options
            # Test case with two --tenant-id args present
            shell('--os-tenant-id=ostenant ec2-credentials-create '
                  '--tenant-id=dash-tenant --user-id=dash-user')
            assert do_ec2_mock.called
            ((a, b), c) = do_ec2_mock.call_args
            actual = (b.os_auth_url, b.os_password, b.os_tenant_id,
                      b.os_tenant_name, b.os_username,
                      b.os_identity_api_version)
            expect = (DEFAULT_AUTH_URL, DEFAULT_PASSWORD, 'ostenant',
                      DEFAULT_TENANT_NAME, DEFAULT_USERNAME, '')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))
            actual = (b.tenant_id, b.user_id)
            expect = ('dash-tenant', 'dash-user')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))

    def test_do_ec2_get(self):
        do_shell_mock = mock.MagicMock()

        with mock.patch('keystoneclient.v2_0.shell.do_ec2_credentials_create',
                        do_shell_mock):
            shell('ec2-credentials-create')
            assert do_shell_mock.called

        with mock.patch('keystoneclient.v2_0.shell.do_ec2_credentials_get',
                        do_shell_mock):
            shell('ec2-credentials-get')
            assert do_shell_mock.called

        with mock.patch('keystoneclient.v2_0.shell.do_ec2_credentials_list',
                        do_shell_mock):
            shell('ec2-credentials-list')
            assert do_shell_mock.called

        with mock.patch('keystoneclient.v2_0.shell.do_ec2_credentials_delete',
                        do_shell_mock):
            shell('ec2-credentials-delete')
            assert do_shell_mock.called

    def test_timeout_parse_invalid_type(self):
        for f in ['foobar', 'xyz']:
            cmd = '--timeout %s endpoint-create' % (f)
            self.assertRaises(exceptions.CommandError,
                              self._tolerant_shell, cmd)

    def test_timeout_parse_invalid_number(self):
        for f in [-1, 0]:
            cmd = '--timeout %s endpoint-create' % (f)
            self.assertRaises(exceptions.CommandError,
                              self._tolerant_shell, cmd)

    def test_do_timeout(self):
        response_mock = mock.MagicMock()
        response_mock.status_code = 200
        response_mock.text = json.dumps({
            'endpoints': [],
        })
        request_mock = mock.MagicMock(return_value=response_mock)
        with mock.patch.object(session.requests, 'request',
                               request_mock):
            shell(('--timeout 2 --os-token=blah  --os-endpoint=blah'
                   ' --os-auth-url=blah.com endpoint-list'))
            request_mock.assert_called_with(mock.ANY, mock.ANY,
                                            timeout=2,
                                            allow_redirects=False,
                                            headers=mock.ANY,
                                            verify=mock.ANY)

    def test_do_endpoints(self):
        do_shell_mock = mock.MagicMock()
        # grab the decorators for do_endpoint_create
        shell_func = getattr(shell_v2_0, 'do_endpoint_create')
        do_shell_mock.arguments = getattr(shell_func, 'arguments', [])
        with mock.patch('keystoneclient.v2_0.shell.do_endpoint_create',
                        do_shell_mock):

            # Old_style options
            # Test create args
            shell('endpoint-create '
                  '--service_id=2 --publicurl=http://example.com:1234/go '
                  '--adminurl=http://example.com:9876/adm')
            assert do_shell_mock.called
            ((a, b), c) = do_shell_mock.call_args
            actual = (b.os_auth_url, b.os_password, b.os_tenant_id,
                      b.os_tenant_name, b.os_username,
                      b.os_identity_api_version)
            expect = (DEFAULT_AUTH_URL, DEFAULT_PASSWORD, DEFAULT_TENANT_ID,
                      DEFAULT_TENANT_NAME, DEFAULT_USERNAME, '')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))
            actual = (b.service, b.publicurl, b.adminurl)
            expect = ('2',
                      'http://example.com:1234/go',
                      'http://example.com:9876/adm')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))

            # New-style options
            # Test create args
            shell('endpoint-create '
                  '--service-id=3 --publicurl=http://example.com:4321/go '
                  '--adminurl=http://example.com:9876/adm')
            assert do_shell_mock.called
            ((a, b), c) = do_shell_mock.call_args
            actual = (b.os_auth_url, b.os_password, b.os_tenant_id,
                      b.os_tenant_name, b.os_username,
                      b.os_identity_api_version)
            expect = (DEFAULT_AUTH_URL, DEFAULT_PASSWORD, DEFAULT_TENANT_ID,
                      DEFAULT_TENANT_NAME, DEFAULT_USERNAME, '')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))
            actual = (b.service, b.publicurl, b.adminurl)
            expect = ('3',
                      'http://example.com:4321/go',
                      'http://example.com:9876/adm')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))

            # New-style options
            # Test create args
            shell('endpoint-create '
                  '--service=3 --publicurl=http://example.com:4321/go '
                  '--adminurl=http://example.com:9876/adm')
            assert do_shell_mock.called
            ((a, b), c) = do_shell_mock.call_args
            actual = (b.os_auth_url, b.os_password, b.os_tenant_id,
                      b.os_tenant_name, b.os_username,
                      b.os_identity_api_version)
            expect = (DEFAULT_AUTH_URL, DEFAULT_PASSWORD, DEFAULT_TENANT_ID,
                      DEFAULT_TENANT_NAME, DEFAULT_USERNAME, '')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))
            actual = (b.service, b.publicurl, b.adminurl)
            expect = ('3',
                      'http://example.com:4321/go',
                      'http://example.com:9876/adm')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))

    def test_shell_keyboard_interrupt(self):
        shell_mock = mock.MagicMock()
        with mock.patch('keystoneclient.shell.OpenStackIdentityShell.main',
                        shell_mock):
            try:
                shell_mock.side_effect = KeyboardInterrupt()
                openstack_shell.main()
            except SystemExit as ex:
                self.assertEqual(130, ex.code)
