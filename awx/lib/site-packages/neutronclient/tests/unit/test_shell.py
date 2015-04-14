# Copyright (C) 2013 Yahoo! Inc.
# All Rights Reserved.
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

import argparse
import logging
import os
import re
import sys

import fixtures
from mox3 import mox
import requests_mock
import six
import testtools
from testtools import matchers

from keystoneclient.auth.identity import v2 as v2_auth
from keystoneclient.auth.identity import v3 as v3_auth
from keystoneclient import session

from neutronclient.common import clientmanager
from neutronclient import shell as openstack_shell
from neutronclient.tests.unit import test_auth as auth


DEFAULT_USERNAME = 'username'
DEFAULT_PASSWORD = 'password'
DEFAULT_TENANT_ID = 'tenant_id'
DEFAULT_TENANT_NAME = 'tenant_name'
DEFAULT_AUTH_URL = 'http://127.0.0.1:5000/v2.0/'
DEFAULT_TOKEN = '3bcc3d3a03f44e3d8377f9247b0ad155'
DEFAULT_URL = 'http://quantum.example.org:9696/'


class ShellTest(testtools.TestCase):

    FAKE_ENV = {
        'OS_USERNAME': DEFAULT_USERNAME,
        'OS_PASSWORD': DEFAULT_PASSWORD,
        'OS_TENANT_ID': DEFAULT_TENANT_ID,
        'OS_TENANT_NAME': DEFAULT_TENANT_NAME,
        'OS_AUTH_URL': DEFAULT_AUTH_URL,
        'OS_REGION_NAME': None,
        'HTTP_PROXY': None,
        'http_proxy': None,
    }

    # Patch os.environ to avoid required auth info.
    def setUp(self):
        super(ShellTest, self).setUp()
        self.mox = mox.Mox()
        for var in self.FAKE_ENV:
            self.useFixture(
                fixtures.EnvironmentVariable(
                    var, self.FAKE_ENV[var]))

    def shell(self, argstr, check=False):
        orig = (sys.stdout, sys.stderr)
        clean_env = {}
        _old_env, os.environ = os.environ, clean_env.copy()
        try:
            sys.stdout = six.moves.cStringIO()
            sys.stderr = six.moves.cStringIO()
            _shell = openstack_shell.NeutronShell('2.0')
            _shell.run(argstr.split())
        except SystemExit:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.assertEqual(exc_value.code, 0)
        finally:
            stdout = sys.stdout.getvalue()
            stderr = sys.stderr.getvalue()
            sys.stdout.close()
            sys.stderr.close()
            sys.stdout, sys.stderr = orig
            os.environ = _old_env
        return stdout, stderr

    def test_run_unknown_command(self):
        self.useFixture(fixtures.FakeLogger(level=logging.DEBUG))
        stdout, stderr = self.shell('fake', check=True)
        self.assertFalse(stdout)
        self.assertEqual("Unknown command ['fake']", stderr.strip())

    def test_help(self):
        required = 'usage:'
        help_text, stderr = self.shell('help')
        self.assertThat(
            help_text,
            matchers.MatchesRegex(required))
        self.assertFalse(stderr)

    def test_bash_completion(self):
        required = '.*os_user_domain_id.*'
        bash_completion, stderr = self.shell('bash-completion')
        self.assertThat(
            bash_completion,
            matchers.MatchesRegex(required))
        self.assertFalse(stderr)

    def test_help_on_subcommand(self):
        required = [
            '.*?^usage: .* quota-list']
        stdout, stderr = self.shell('help quota-list')
        for r in required:
            self.assertThat(
                stdout,
                matchers.MatchesRegex(r, re.DOTALL | re.MULTILINE))
        self.assertFalse(stderr)

    def test_help_command(self):
        required = 'usage:'
        help_text, stderr = self.shell('help network-create')
        self.assertThat(
            help_text,
            matchers.MatchesRegex(required))
        self.assertFalse(stderr)

    def test_bash_completion_in_outputs_of_help_command(self):
        help_text, stderr = self.shell('help')
        self.assertFalse(stderr)
        completion_cmd = "bash-completion"
        completion_help_str = ("Prints all of the commands and options "
                               "for bash-completion.")
        self.assertIn(completion_cmd, help_text)
        self.assertIn(completion_help_str, help_text)

    def test_bash_completion_command(self):
        # just check we have some output
        required = [
            '.*--tenant_id',
            '.*--client-certificate',
            '.*help',
            '.*gateway-device-create',
            '.*--dns-nameserver']
        help_text, stderr = self.shell('neutron bash-completion')
        self.assertFalse(stderr)
        for r in required:
            self.assertThat(help_text,
                            matchers.MatchesRegex(r, re.DOTALL | re.MULTILINE))

    def test_unknown_auth_strategy(self):
        self.useFixture(fixtures.FakeLogger(level=logging.DEBUG))
        stdout, stderr = self.shell('--os-auth-strategy fake quota-list')
        self.assertFalse(stdout)
        self.assertEqual('You must provide a service URL via '
                         'either --os-url or env[OS_URL]', stderr.strip())

    @requests_mock.Mocker()
    def test_auth(self, mrequests):
        # emulate Keystone version discovery
        mrequests.register_uri('GET',
                               auth.V3_URL,
                               json=auth.V3_VERSION_ENTRY)

        neutron_shell = openstack_shell.NeutronShell('2.0')
        self.addCleanup(self.mox.UnsetStubs)
        self.mox.StubOutWithMock(clientmanager.ClientManager, '__init__')
        self.mox.StubOutWithMock(neutron_shell, 'run_subcommand')
        clientmanager.ClientManager.__init__(
            token='', url='', auth_url=auth.V3_URL,
            tenant_name='test', tenant_id='tenant_id',
            username='test', user_id='',
            password='test', region_name='', api_version={'network': '2.0'},
            auth_strategy='keystone', service_type='network',
            endpoint_type='publicURL', insecure=False, ca_cert=None,
            timeout=None,
            raise_errors=False,
            retries=0,
            auth=mox.IsA(v3_auth.Password),
            session=mox.IsA(session.Session),
            log_credentials=True)
        neutron_shell.run_subcommand(['quota-list'])
        self.mox.ReplayAll()
        cmdline = ('--os-username test '
                   '--os-password test '
                   '--os-tenant-name test '
                   '--os-auth-url %s '
                   '--os-auth-strategy keystone quota-list'
                   % auth.V3_URL)
        neutron_shell.run(cmdline.split())
        self.mox.VerifyAll()

    @requests_mock.Mocker()
    def test_auth_cert_and_key(self, mrequests):
        # emulate Keystone version discovery
        mrequests.register_uri('GET',
                               auth.V3_URL,
                               json=auth.V3_VERSION_ENTRY)

        neutron_shell = openstack_shell.NeutronShell('2.0')
        self.addCleanup(self.mox.UnsetStubs)
        self.mox.StubOutWithMock(clientmanager.ClientManager, '__init__')
        self.mox.StubOutWithMock(neutron_shell, 'run_subcommand')
        clientmanager.ClientManager.__init__(
            token='', url='', auth_url=auth.V3_URL,
            tenant_name='test', tenant_id='tenant_id',
            username='test', user_id='',
            password='test', region_name='', api_version={'network': '2.0'},
            auth_strategy='keystone', service_type='network',
            raise_errors=False,
            endpoint_type='publicURL', insecure=False, ca_cert=None, retries=0,
            timeout=None,
            auth=mox.IsA(v3_auth.Password),
            session=mox.IsA(session.Session),
            log_credentials=True)
        neutron_shell.run_subcommand(['quota-list'])
        self.mox.ReplayAll()
        cmdline = ('--os-username test '
                   '--os-password test '
                   '--os-tenant-name test '
                   '--os-cert test '
                   '--os-key test '
                   '--os-auth-url %s '
                   '--os-auth-strategy keystone quota-list'
                   % auth.V3_URL)
        neutron_shell.run(cmdline.split())
        self.mox.VerifyAll()

    @requests_mock.Mocker()
    def test_v2_auth(self, mrequests):
        # emulate Keystone version discovery
        mrequests.register_uri('GET',
                               auth.V2_URL,
                               json=auth.V2_VERSION_ENTRY)

        neutron_shell = openstack_shell.NeutronShell('2.0')
        self.addCleanup(self.mox.UnsetStubs)
        self.mox.StubOutWithMock(clientmanager.ClientManager, '__init__')
        self.mox.StubOutWithMock(neutron_shell, 'run_subcommand')
        clientmanager.ClientManager.__init__(
            token='', url='', auth_url=auth.V2_URL,
            tenant_name='test', tenant_id='tenant_id',
            username='test', user_id='',
            password='test', region_name='', api_version={'network': '2.0'},
            auth_strategy='keystone', service_type='network',
            endpoint_type='publicURL', insecure=False, ca_cert=None,
            timeout=None,
            raise_errors=False,
            retries=0,
            auth=mox.IsA(v2_auth.Password),
            session=mox.IsA(session.Session),
            log_credentials=True)
        neutron_shell.run_subcommand(['quota-list'])
        self.mox.ReplayAll()
        cmdline = ('--os-username test '
                   '--os-password test '
                   '--os-tenant-name test '
                   '--os-auth-url %s '
                   '--os-auth-strategy keystone quota-list'
                   % auth.V2_URL)
        neutron_shell.run(cmdline.split())
        self.mox.VerifyAll()

    @requests_mock.Mocker()
    def test_failed_auth_version_discovery_v3_auth_url(self, mrequests):
        # emulate Keystone version discovery
        mrequests.register_uri('GET',
                               auth.V3_URL,
                               status_code=405)

        neutron_shell = openstack_shell.NeutronShell('2.0')
        self.addCleanup(self.mox.UnsetStubs)
        self.mox.StubOutWithMock(clientmanager.ClientManager, '__init__')
        self.mox.StubOutWithMock(neutron_shell, 'run_subcommand')
        clientmanager.ClientManager.__init__(
            token='', url='', auth_url=auth.V3_URL,
            tenant_name='test', tenant_id='tenant_id',
            username='test', user_id='',
            password='test', region_name='', api_version={'network': '2.0'},
            auth_strategy='keystone', service_type='network',
            endpoint_type='publicURL', insecure=False, ca_cert=None,
            timeout=None,
            raise_errors=False,
            retries=0,
            auth=mox.IsA(v3_auth.Password),
            session=mox.IsA(session.Session),
            log_credentials=True)
        neutron_shell.run_subcommand(['quota-list'])
        self.mox.ReplayAll()
        cmdline = ('--os-username test '
                   '--os-password test '
                   '--os-user-domain-name test '
                   '--os-tenant-name test '
                   '--os-auth-url %s '
                   '--os-auth-strategy keystone quota-list'
                   % auth.V3_URL)
        neutron_shell.run(cmdline.split())
        self.mox.VerifyAll()

    @requests_mock.Mocker()
    def test_failed_auth_version_discovery_v2_auth_url(self, mrequests):
        # emulate Keystone version discovery
        mrequests.register_uri('GET',
                               auth.V2_URL,
                               status_code=405)

        neutron_shell = openstack_shell.NeutronShell('2.0')
        self.addCleanup(self.mox.UnsetStubs)
        self.mox.StubOutWithMock(clientmanager.ClientManager, '__init__')
        self.mox.StubOutWithMock(neutron_shell, 'run_subcommand')
        clientmanager.ClientManager.__init__(
            token='', url='', auth_url=auth.V2_URL,
            tenant_name='test', tenant_id='tenant_id',
            username='test', user_id='',
            password='test', region_name='', api_version={'network': '2.0'},
            auth_strategy='keystone', service_type='network',
            endpoint_type='publicURL', insecure=False, ca_cert=None,
            timeout=None,
            raise_errors=False,
            retries=0,
            auth=mox.IsA(v2_auth.Password),
            session=mox.IsA(session.Session),
            log_credentials=True)
        neutron_shell.run_subcommand(['quota-list'])
        self.mox.ReplayAll()
        cmdline = ('--os-username test '
                   '--os-password test '
                   '--os-tenant-name test '
                   '--os-auth-url %s '
                   '--os-auth-strategy keystone quota-list'
                   % auth.V2_URL)
        neutron_shell.run(cmdline.split())
        self.mox.VerifyAll()

    @requests_mock.Mocker()
    def test_auth_version_discovery_v3(self, mrequests):
        # emulate Keystone version discovery
        mrequests.register_uri('GET',
                               auth.BASE_URL,
                               text=auth.V3_VERSION_LIST)

        neutron_shell = openstack_shell.NeutronShell('2.0')
        self.addCleanup(self.mox.UnsetStubs)
        self.mox.StubOutWithMock(clientmanager.ClientManager, '__init__')
        self.mox.StubOutWithMock(neutron_shell, 'run_subcommand')
        clientmanager.ClientManager.__init__(
            token='', url='', auth_url=auth.BASE_URL,
            tenant_name='test', tenant_id='tenant_id',
            username='test', user_id='',
            password='test', region_name='', api_version={'network': '2.0'},
            auth_strategy='keystone', service_type='network',
            endpoint_type='publicURL', insecure=False, ca_cert=None,
            timeout=None,
            raise_errors=False,
            retries=0,
            auth=mox.IsA(v3_auth.Password),
            session=mox.IsA(session.Session),
            log_credentials=True)
        neutron_shell.run_subcommand(['quota-list'])
        self.mox.ReplayAll()
        cmdline = ('--os-username test '
                   '--os-password test '
                   '--os-user-domain-name test '
                   '--os-tenant-name test '
                   '--os-auth-url %s '
                   '--os-auth-strategy keystone quota-list'
                   % auth.BASE_URL)
        neutron_shell.run(cmdline.split())
        self.mox.VerifyAll()

    @requests_mock.Mocker()
    def test_auth_version_discovery_v2(self, mrequests):
        # emulate Keystone version discovery
        mrequests.register_uri('GET',
                               auth.BASE_URL,
                               text=auth.V3_VERSION_LIST)

        neutron_shell = openstack_shell.NeutronShell('2.0')
        self.addCleanup(self.mox.UnsetStubs)
        self.mox.StubOutWithMock(clientmanager.ClientManager, '__init__')
        self.mox.StubOutWithMock(neutron_shell, 'run_subcommand')
        clientmanager.ClientManager.__init__(
            token='', url='', auth_url=auth.BASE_URL,
            tenant_name='test', tenant_id='tenant_id',
            username='test', user_id='',
            password='test', region_name='', api_version={'network': '2.0'},
            auth_strategy='keystone', service_type='network',
            endpoint_type='publicURL', insecure=False, ca_cert=None,
            timeout=None,
            raise_errors=False,
            retries=0,
            auth=mox.IsA(v2_auth.Password),
            session=mox.IsA(session.Session),
            log_credentials=True)
        neutron_shell.run_subcommand(['quota-list'])
        self.mox.ReplayAll()
        cmdline = ('--os-username test '
                   '--os-password test '
                   '--os-tenant-name test '
                   '--os-auth-url %s '
                   '--os-auth-strategy keystone quota-list'
                   % auth.BASE_URL)
        neutron_shell.run(cmdline.split())
        self.mox.VerifyAll()

    @requests_mock.Mocker()
    def test_insecure_auth(self, mrequests):
        # emulate Keystone version discovery
        mrequests.register_uri('GET',
                               auth.V2_URL,
                               json=auth.V2_VERSION_ENTRY)

        neutron_shell = openstack_shell.NeutronShell('2.0')
        self.addCleanup(self.mox.UnsetStubs)
        self.mox.StubOutWithMock(clientmanager.ClientManager, '__init__')
        self.mox.StubOutWithMock(neutron_shell, 'run_subcommand')
        clientmanager.ClientManager.__init__(
            token='', url='', auth_url=auth.V2_URL,
            tenant_name='test', tenant_id='tenant_id',
            username='test', user_id='',
            password='test', region_name='', api_version={'network': '2.0'},
            auth_strategy='keystone', service_type='network',
            endpoint_type='publicURL', insecure=True, ca_cert=None,
            timeout=None,
            raise_errors=False,
            retries=0,
            auth=mox.IgnoreArg(),
            session=mox.IgnoreArg(),
            log_credentials=True)
        neutron_shell.run_subcommand(['quota-list'])
        self.mox.ReplayAll()
        cmdline = ('--os-username test '
                   '--os-password test '
                   '--os-tenant-name test '
                   '--insecure '
                   '--os-auth-url %s '
                   '--os-auth-strategy keystone quota-list'
                   % auth.V2_URL)
        neutron_shell.run(cmdline.split())
        self.mox.VerifyAll()

    def test_build_option_parser(self):
        neutron_shell = openstack_shell.NeutronShell('2.0')
        result = neutron_shell.build_option_parser('descr', '2.0')
        self.assertEqual(True, isinstance(result, argparse.ArgumentParser))

    def test_main_with_unicode(self):
        self.mox.StubOutClassWithMocks(openstack_shell, 'NeutronShell')
        qshell_mock = openstack_shell.NeutronShell('2.0')
        unicode_text = u'\u7f51\u7edc'
        argv = ['net-list', unicode_text, unicode_text]
        qshell_mock.run([u'net-list', unicode_text,
                         unicode_text]).AndReturn(0)
        self.mox.ReplayAll()
        ret = openstack_shell.main(argv=argv)
        self.mox.VerifyAll()
        self.mox.UnsetStubs()
        self.assertEqual(ret, 0)

    def test_endpoint_option(self):
        shell = openstack_shell.NeutronShell('2.0')
        parser = shell.build_option_parser('descr', '2.0')

        # Neither $OS_ENDPOINT_TYPE nor --os-endpoint-type
        namespace = parser.parse_args([])
        self.assertEqual('publicURL', namespace.os_endpoint_type)

        # --endpoint-type but not $OS_ENDPOINT_TYPE
        namespace = parser.parse_args(['--os-endpoint-type=admin'])
        self.assertEqual('admin', namespace.os_endpoint_type)

    def test_endpoint_environment_variable(self):
        fixture = fixtures.EnvironmentVariable("OS_ENDPOINT_TYPE",
                                               "public")
        self.useFixture(fixture)

        shell = openstack_shell.NeutronShell('2.0')
        parser = shell.build_option_parser('descr', '2.0')

        # $OS_ENDPOINT_TYPE but not --endpoint-type
        namespace = parser.parse_args([])
        self.assertEqual("public", namespace.os_endpoint_type)

        # --endpoint-type and $OS_ENDPOINT_TYPE
        namespace = parser.parse_args(['--endpoint-type=admin'])
        self.assertEqual('admin', namespace.endpoint_type)

    def test_timeout_option(self):
        shell = openstack_shell.NeutronShell('2.0')
        parser = shell.build_option_parser('descr', '2.0')

        # Neither $OS_ENDPOINT_TYPE nor --endpoint-type
        namespace = parser.parse_args([])
        self.assertIsNone(namespace.http_timeout)

        # --endpoint-type but not $OS_ENDPOINT_TYPE
        namespace = parser.parse_args(['--http-timeout=50'])
        self.assertEqual(50, namespace.http_timeout)

    def test_timeout_environment_variable(self):
        fixture = fixtures.EnvironmentVariable("OS_NETWORK_TIMEOUT",
                                               "50")
        self.useFixture(fixture)

        shell = openstack_shell.NeutronShell('2.0')
        parser = shell.build_option_parser('descr', '2.0')

        namespace = parser.parse_args([])
        self.assertEqual(50, namespace.http_timeout)
