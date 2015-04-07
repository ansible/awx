# Copyright 2014 OpenStack Foundation
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

import mock
from six import moves

from keystoneclient.generic import shell
from keystoneclient.tests.unit import utils


class DoDiscoverTest(utils.TestCase):
    """Unit tests for do_discover function."""
    foo_version = {
        'id': 'foo_id',
        'status': 'foo_status',
        'url': 'http://foo/url',
    }
    bar_version = {
        'id': 'bar_id',
        'status': 'bar_status',
        'url': 'http://bar/url',
    }
    foo_extension = {
        'foo': 'foo_extension',
        'message': 'extension_message',
        'bar': 'bar_extension',
    }
    stub_message = 'This is a stub message'

    def setUp(self):
        super(DoDiscoverTest, self).setUp()

        self.client_mock = mock.Mock()
        self.client_mock.discover.return_value = {}

    def _execute_discover(self):
        """Call do_discover function and capture output

        :returns: captured output is returned
        """
        with mock.patch('sys.stdout',
                        new_callable=moves.StringIO) as mock_stdout:
            shell.do_discover(self.client_mock, args=None)
            output = mock_stdout.getvalue()
        return output

    def _check_version_print(self, output, version):
        """Checks all api version's parameters are present in output."""
        self.assertIn(version['id'], output)
        self.assertIn(version['status'], output)
        self.assertIn(version['url'], output)

    def test_no_keystones(self):
        # No servers configured for client,
        # corresponding message should be printed
        output = self._execute_discover()
        self.assertIn('No Keystone-compatible endpoint found', output)

    def test_endpoint(self):
        # Endpoint is configured for client,
        # client's discover method should be called with that value
        self.client_mock.endpoint = 'Some non-empty value'
        shell.do_discover(self.client_mock, args=None)
        self.client_mock.discover.assert_called_with(self.client_mock.endpoint)

    def test_auth_url(self):
        # No endpoint provided for client, but there is an auth_url
        # client's discover method should be called with auth_url value
        self.client_mock.endpoint = False
        self.client_mock.auth_url = 'Some non-empty value'
        shell.do_discover(self.client_mock, args=None)
        self.client_mock.discover.assert_called_with(self.client_mock.auth_url)

    def test_empty(self):
        # No endpoint or auth_url is configured for client.
        # client.discover() should be called without parameters
        self.client_mock.endpoint = False
        self.client_mock.auth_url = False
        shell.do_discover(self.client_mock, args=None)
        self.client_mock.discover.assert_called_with()

    def test_message(self):
        # If client.discover() result contains message - it should be printed
        self.client_mock.discover.return_value = {'message': self.stub_message}
        output = self._execute_discover()
        self.assertIn(self.stub_message, output)

    def test_versions(self):
        # Every version in client.discover() result should be printed
        # and client.discover_extension() should be called on its url
        self.client_mock.discover.return_value = {
            'foo': self.foo_version,
            'bar': self.bar_version,
        }
        self.client_mock.discover_extensions.return_value = {}
        output = self._execute_discover()
        self._check_version_print(output, self.foo_version)
        self._check_version_print(output, self.bar_version)

        discover_extension_calls = [
            mock.call(self.foo_version['url']),
            mock.call(self.bar_version['url']),
        ]

        self.client_mock.discover_extensions.assert_has_calls(
            discover_extension_calls,
            any_order=True)

    def test_extensions(self):
        # Every extension's parameters should be printed
        # Extension's message should be omitted
        self.client_mock.discover.return_value = {'foo': self.foo_version}
        self.client_mock.discover_extensions.return_value = self.foo_extension
        output = self._execute_discover()
        self.assertIn(self.foo_extension['foo'], output)
        self.assertIn(self.foo_extension['bar'], output)
        self.assertNotIn(self.foo_extension['message'], output)
