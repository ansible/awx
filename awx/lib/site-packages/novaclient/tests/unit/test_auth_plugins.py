# Copyright 2012 OpenStack Foundation
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

from keystoneclient import fixture
import mock
import pkg_resources
import requests

try:
    import json
except ImportError:
    import simplejson as json

from novaclient import auth_plugin
from novaclient import exceptions
from novaclient.tests.unit import utils
from novaclient.v2 import client


def mock_http_request(resp=None):
    """Mock an HTTP Request."""
    if not resp:
        resp = fixture.V2Token()
        resp.set_scope()
        s = resp.add_service('compute')
        s.add_endpoint("http://localhost:8774/v1.1", region='RegionOne')

    auth_response = utils.TestResponse({
        "status_code": 200,
        "text": json.dumps(resp),
    })
    return mock.Mock(return_value=(auth_response))


def requested_headers(cs):
    """Return requested passed headers."""
    return {
        'User-Agent': cs.client.USER_AGENT,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }


class DeprecatedAuthPluginTest(utils.TestCase):
    def test_auth_system_success(self):
        class MockEntrypoint(pkg_resources.EntryPoint):
            def load(self):
                return self.authenticate

            def authenticate(self, cls, auth_url):
                cls._authenticate(auth_url, {"fake": "me"})

        def mock_iter_entry_points(_type, name):
            if _type == 'openstack.client.authenticate':
                return [MockEntrypoint("fake", "fake", ["fake"])]
            else:
                return []

        mock_request = mock_http_request()

        @mock.patch.object(pkg_resources, "iter_entry_points",
                           mock_iter_entry_points)
        @mock.patch.object(requests, "request", mock_request)
        def test_auth_call():
            plugin = auth_plugin.DeprecatedAuthPlugin("fake")
            cs = client.Client("username", "password", "project_id",
                               utils.AUTH_URL_V2, auth_system="fake",
                               auth_plugin=plugin)
            cs.client.authenticate()

            headers = requested_headers(cs)
            token_url = cs.client.auth_url + "/tokens"

            mock_request.assert_called_with(
                "POST",
                token_url,
                headers=headers,
                data='{"fake": "me"}',
                allow_redirects=True,
                **self.TEST_REQUEST_BASE)

        test_auth_call()

    def test_auth_system_not_exists(self):
        def mock_iter_entry_points(_t, name=None):
            return [pkg_resources.EntryPoint("fake", "fake", ["fake"])]

        mock_request = mock_http_request()

        @mock.patch.object(pkg_resources, "iter_entry_points",
                           mock_iter_entry_points)
        @mock.patch.object(requests, "request", mock_request)
        def test_auth_call():
            auth_plugin.discover_auth_systems()
            plugin = auth_plugin.DeprecatedAuthPlugin("notexists")
            cs = client.Client("username", "password", "project_id",
                               utils.AUTH_URL_V2, auth_system="notexists",
                               auth_plugin=plugin)
            self.assertRaises(exceptions.AuthSystemNotFound,
                              cs.client.authenticate)

        test_auth_call()

    def test_auth_system_defining_auth_url(self):
        class MockAuthUrlEntrypoint(pkg_resources.EntryPoint):
            def load(self):
                return self.auth_url

            def auth_url(self):
                return "http://faked/v2.0"

        class MockAuthenticateEntrypoint(pkg_resources.EntryPoint):
            def load(self):
                return self.authenticate

            def authenticate(self, cls, auth_url):
                cls._authenticate(auth_url, {"fake": "me"})

        def mock_iter_entry_points(_type, name):
            if _type == 'openstack.client.auth_url':
                return [MockAuthUrlEntrypoint("fakewithauthurl",
                                              "fakewithauthurl",
                                              ["auth_url"])]
            elif _type == 'openstack.client.authenticate':
                return [MockAuthenticateEntrypoint("fakewithauthurl",
                                                   "fakewithauthurl",
                                                   ["authenticate"])]
            else:
                return []

        mock_request = mock_http_request()

        @mock.patch.object(pkg_resources, "iter_entry_points",
                           mock_iter_entry_points)
        @mock.patch.object(requests, "request", mock_request)
        def test_auth_call():
            plugin = auth_plugin.DeprecatedAuthPlugin("fakewithauthurl")
            cs = client.Client("username", "password", "project_id",
                               auth_system="fakewithauthurl",
                               auth_plugin=plugin)
            cs.client.authenticate()
            self.assertEqual("http://faked/v2.0", cs.client.auth_url)

        test_auth_call()

    @mock.patch.object(pkg_resources, "iter_entry_points")
    def test_client_raises_exc_without_auth_url(self, mock_iter_entry_points):
        class MockAuthUrlEntrypoint(pkg_resources.EntryPoint):
            def load(self):
                return self.auth_url

            def auth_url(self):
                return None

        mock_iter_entry_points.side_effect = lambda _t, name: [
            MockAuthUrlEntrypoint("fakewithauthurl",
                                  "fakewithauthurl",
                                  ["auth_url"])]

        plugin = auth_plugin.DeprecatedAuthPlugin("fakewithauthurl")
        self.assertRaises(
            exceptions.EndpointNotFound,
            client.Client, "username", "password", "project_id",
            auth_system="fakewithauthurl", auth_plugin=plugin)


class AuthPluginTest(utils.TestCase):
    @mock.patch.object(requests, "request")
    @mock.patch.object(pkg_resources, "iter_entry_points")
    def test_auth_system_success(self, mock_iter_entry_points, mock_request):
        """Test that we can authenticate using the auth system."""
        class MockEntrypoint(pkg_resources.EntryPoint):
            def load(self):
                return FakePlugin

        class FakePlugin(auth_plugin.BaseAuthPlugin):
            def authenticate(self, cls, auth_url):
                cls._authenticate(auth_url, {"fake": "me"})

        mock_iter_entry_points.side_effect = lambda _t: [
            MockEntrypoint("fake", "fake", ["FakePlugin"])]

        mock_request.side_effect = mock_http_request()

        auth_plugin.discover_auth_systems()
        plugin = auth_plugin.load_plugin("fake")
        cs = client.Client("username", "password", "project_id",
                           utils.AUTH_URL_V2, auth_system="fake",
                           auth_plugin=plugin)
        cs.client.authenticate()

        headers = requested_headers(cs)
        token_url = cs.client.auth_url + "/tokens"

        mock_request.assert_called_with(
            "POST",
            token_url,
            headers=headers,
            data='{"fake": "me"}',
            allow_redirects=True,
            **self.TEST_REQUEST_BASE)

    @mock.patch.object(pkg_resources, "iter_entry_points")
    def test_discover_auth_system_options(self, mock_iter_entry_points):
        """Test that we can load the auth system options."""
        class FakePlugin(auth_plugin.BaseAuthPlugin):
            @staticmethod
            def add_opts(parser):
                parser.add_argument('--auth_system_opt',
                                    default=False,
                                    action='store_true',
                                    help="Fake option")
                return parser

        class MockEntrypoint(pkg_resources.EntryPoint):
            def load(self):
                return FakePlugin

        mock_iter_entry_points.side_effect = lambda _t: [
            MockEntrypoint("fake", "fake", ["FakePlugin"])]

        parser = argparse.ArgumentParser()
        auth_plugin.discover_auth_systems()
        auth_plugin.load_auth_system_opts(parser)
        opts, args = parser.parse_known_args(['--auth_system_opt'])

        self.assertTrue(opts.auth_system_opt)

    @mock.patch.object(pkg_resources, "iter_entry_points")
    def test_parse_auth_system_options(self, mock_iter_entry_points):
        """Test that we can parse the auth system options."""
        class MockEntrypoint(pkg_resources.EntryPoint):
            def load(self):
                return FakePlugin

        class FakePlugin(auth_plugin.BaseAuthPlugin):
            def __init__(self):
                self.opts = {"fake_argument": True}

            def parse_opts(self, args):
                return self.opts

        mock_iter_entry_points.side_effect = lambda _t: [
            MockEntrypoint("fake", "fake", ["FakePlugin"])]

        auth_plugin.discover_auth_systems()
        plugin = auth_plugin.load_plugin("fake")

        plugin.parse_opts([])
        self.assertIn("fake_argument", plugin.opts)

    @mock.patch.object(pkg_resources, "iter_entry_points")
    def test_auth_system_defining_url(self, mock_iter_entry_points):
        """Test the auth_system defining an url."""
        class MockEntrypoint(pkg_resources.EntryPoint):
            def load(self):
                return FakePlugin

        class FakePlugin(auth_plugin.BaseAuthPlugin):
            def get_auth_url(self):
                return "http://faked/v2.0"

        mock_iter_entry_points.side_effect = lambda _t: [
            MockEntrypoint("fake", "fake", ["FakePlugin"])]

        auth_plugin.discover_auth_systems()
        plugin = auth_plugin.load_plugin("fake")

        cs = client.Client("username", "password", "project_id",
                           auth_system="fakewithauthurl",
                           auth_plugin=plugin)
        self.assertEqual("http://faked/v2.0", cs.client.auth_url)

    @mock.patch.object(pkg_resources, "iter_entry_points")
    def test_exception_if_no_authenticate(self, mock_iter_entry_points):
        """Test that no authenticate raises a proper exception."""
        class MockEntrypoint(pkg_resources.EntryPoint):
            def load(self):
                return FakePlugin

        class FakePlugin(auth_plugin.BaseAuthPlugin):
            pass

        mock_iter_entry_points.side_effect = lambda _t: [
            MockEntrypoint("fake", "fake", ["FakePlugin"])]

        auth_plugin.discover_auth_systems()
        plugin = auth_plugin.load_plugin("fake")

        self.assertRaises(
            exceptions.EndpointNotFound,
            client.Client, "username", "password", "project_id",
            auth_system="fake", auth_plugin=plugin)

    @mock.patch.object(pkg_resources, "iter_entry_points")
    def test_exception_if_no_url(self, mock_iter_entry_points):
        """Test that no auth_url at all raises exception."""
        class MockEntrypoint(pkg_resources.EntryPoint):
            def load(self):
                return FakePlugin

        class FakePlugin(auth_plugin.BaseAuthPlugin):
            pass

        mock_iter_entry_points.side_effect = lambda _t: [
            MockEntrypoint("fake", "fake", ["FakePlugin"])]

        auth_plugin.discover_auth_systems()
        plugin = auth_plugin.load_plugin("fake")

        self.assertRaises(
            exceptions.EndpointNotFound,
            client.Client, "username", "password", "project_id",
            auth_system="fake", auth_plugin=plugin)
