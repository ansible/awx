# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import re
import sys

import fixtures
import requests_mock
from six import moves
from testtools import matchers

from cinderclient import exceptions
from cinderclient import shell
from cinderclient.tests import utils
from cinderclient.tests.fixture_data import keystone_client
from keystoneclient.exceptions import DiscoveryFailure


class ShellTest(utils.TestCase):

    FAKE_ENV = {
        'OS_USERNAME': 'username',
        'OS_PASSWORD': 'password',
        'OS_TENANT_NAME': 'tenant_name',
        'OS_AUTH_URL': 'http://no.where',
    }

    # Patch os.environ to avoid required auth info.
    def setUp(self):
        super(ShellTest, self).setUp()
        for var in self.FAKE_ENV:
            self.useFixture(fixtures.EnvironmentVariable(var,
                                                         self.FAKE_ENV[var]))

    def shell(self, argstr):
        orig = sys.stdout
        try:
            sys.stdout = moves.StringIO()
            _shell = shell.OpenStackCinderShell()
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
        self.assertRaises(exceptions.CommandError, self.shell, 'help foofoo')

    def test_help(self):
        required = [
            '.*?^usage: ',
            '.*?(?m)^\s+create\s+Creates a volume.',
            '.*?(?m)^Run "cinder help SUBCOMMAND" for help on a subcommand.',
        ]
        help_text = self.shell('help')
        for r in required:
            self.assertThat(help_text,
                            matchers.MatchesRegex(r, re.DOTALL | re.MULTILINE))

    def test_help_on_subcommand(self):
        required = [
            '.*?^usage: cinder list',
            '.*?(?m)^Lists all volumes.',
        ]
        help_text = self.shell('help list')
        for r in required:
            self.assertThat(help_text,
                            matchers.MatchesRegex(r, re.DOTALL | re.MULTILINE))

    def register_keystone_auth_fixture(self, mocker, url):
        mocker.register_uri('GET', url,
                            text=keystone_client.keystone_request_callback)

    @requests_mock.Mocker()
    def test_version_discovery(self, mocker):
        _shell = shell.OpenStackCinderShell()

        os_auth_url = "https://WrongDiscoveryResponse.discovery.com:35357/v2.0"
        self.register_keystone_auth_fixture(mocker, os_auth_url)
        self.assertRaises(DiscoveryFailure, _shell._discover_auth_versions,
                          None, auth_url=os_auth_url)

        os_auth_url = "https://DiscoveryNotSupported.discovery.com:35357/v2.0"
        self.register_keystone_auth_fixture(mocker, os_auth_url)
        v2_url, v3_url = _shell._discover_auth_versions(
            None, auth_url=os_auth_url)
        self.assertEqual(v2_url, os_auth_url, "Expected v2 url")
        self.assertEqual(v3_url, None, "Expected no v3 url")

        os_auth_url = "https://DiscoveryNotSupported.discovery.com:35357/v3.0"
        self.register_keystone_auth_fixture(mocker, os_auth_url)
        v2_url, v3_url = _shell._discover_auth_versions(
            None, auth_url=os_auth_url)
        self.assertEqual(v3_url, os_auth_url, "Expected v3 url")
        self.assertEqual(v2_url, None, "Expected no v2 url")


class CinderClientArgumentParserTest(utils.TestCase):

    def test_ambiguity_solved_for_one_visible_argument(self):
        parser = shell.CinderClientArgumentParser(add_help=False)
        parser.add_argument('--test-parameter',
                            dest='visible_param',
                            action='store_true')
        parser.add_argument('--test_parameter',
                            dest='hidden_param',
                            action='store_true',
                            help=argparse.SUPPRESS)

        opts = parser.parse_args(['--test'])

        # visible argument must be set
        self.assertTrue(opts.visible_param)
        self.assertFalse(opts.hidden_param)

    def test_raise_ambiguity_error_two_visible_argument(self):
        parser = shell.CinderClientArgumentParser(add_help=False)
        parser.add_argument('--test-parameter',
                            dest="visible_param1",
                            action='store_true')
        parser.add_argument('--test_parameter',
                            dest="visible_param2",
                            action='store_true')

        self.assertRaises(SystemExit, parser.parse_args, ['--test'])

    def test_raise_ambiguity_error_two_hidden_argument(self):
        parser = shell.CinderClientArgumentParser(add_help=False)
        parser.add_argument('--test-parameter',
                            dest="hidden_param1",
                            action='store_true',
                            help=argparse.SUPPRESS)
        parser.add_argument('--test_parameter',
                            dest="hidden_param2",
                            action='store_true',
                            help=argparse.SUPPRESS)

        self.assertRaises(SystemExit, parser.parse_args, ['--test'])
