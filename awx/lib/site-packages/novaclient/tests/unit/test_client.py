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


import json
import logging

import fixtures
import mock
import requests

import novaclient.client
import novaclient.extension
from novaclient.tests.unit import utils
import novaclient.v2.client


class ClientConnectionPoolTest(utils.TestCase):

    @mock.patch("novaclient.client.TCPKeepAliveAdapter")
    def test_get(self, mock_http_adapter):
        mock_http_adapter.side_effect = lambda: mock.Mock()
        pool = novaclient.client._ClientConnectionPool()
        self.assertEqual(pool.get("abc"), pool.get("abc"))
        self.assertNotEqual(pool.get("abc"), pool.get("def"))


class ClientTest(utils.TestCase):

    def test_client_with_timeout(self):
        instance = novaclient.client.HTTPClient(user='user',
                                                password='password',
                                                projectid='project',
                                                timeout=2,
                                                auth_url="http://www.blah.com")
        self.assertEqual(2, instance.timeout)
        mock_request = mock.Mock()
        mock_request.return_value = requests.Response()
        mock_request.return_value.status_code = 200
        mock_request.return_value.headers = {
            'x-server-management-url': 'blah.com',
            'x-auth-token': 'blah',
        }
        with mock.patch('requests.request', mock_request):
            instance.authenticate()
            requests.request.assert_called_with(
                mock.ANY, mock.ANY, timeout=2, headers=mock.ANY,
                verify=mock.ANY)

    def test_client_reauth(self):
        instance = novaclient.client.HTTPClient(user='user',
                                                password='password',
                                                projectid='project',
                                                timeout=2,
                                                auth_url="http://www.blah.com")
        instance.auth_token = 'foobar'
        instance.management_url = 'http://example.com'
        instance.version = 'v2.0'
        mock_request = mock.Mock()
        mock_request.side_effect = novaclient.exceptions.Unauthorized(401)
        with mock.patch('requests.request', mock_request):
            try:
                instance.get('/servers/detail')
            except Exception:
                pass
            get_headers = {'X-Auth-Project-Id': 'project',
                           'X-Auth-Token': 'foobar',
                           'User-Agent': 'python-novaclient',
                           'Accept': 'application/json'}
            reauth_headers = {'Content-Type': 'application/json',
                              'Accept': 'application/json',
                              'User-Agent': 'python-novaclient'}
            data = {
                "auth": {
                    "tenantName": "project",
                    "passwordCredentials": {
                        "username": "user",
                        "password": "password"
                    }
                }
            }

            expected = [mock.call('GET',
                                  'http://example.com/servers/detail',
                                  timeout=mock.ANY,
                                  headers=get_headers,
                                  verify=mock.ANY),
                        mock.call('POST', 'http://www.blah.com/tokens',
                                  timeout=mock.ANY,
                                  headers=reauth_headers,
                                  allow_redirects=mock.ANY,
                                  data=mock.ANY,
                                  verify=mock.ANY)]
            self.assertEqual(expected, mock_request.call_args_list)
            token_post_call = mock_request.call_args_list[1]
            self.assertEqual(data, json.loads(token_post_call[1]['data']))

    @mock.patch.object(novaclient.client.HTTPClient, 'request',
                       return_value=(200, "{'versions':[]}"))
    def _check_version_url(self, management_url, version_url, mock_request):
        projectid = '25e469aa1848471b875e68cde6531bc5'
        instance = novaclient.client.HTTPClient(user='user',
                                                password='password',
                                                projectid=projectid,
                                                auth_url="http://www.blah.com")
        instance.auth_token = 'foobar'
        instance.management_url = management_url % projectid
        instance.version = 'v2.0'

        # If passing None as the part of url, a client accesses the url which
        # doesn't include "v2/<projectid>" for getting API version info.
        instance.get(None)
        mock_request.assert_called_once_with(version_url, 'GET',
                                             headers=mock.ANY)
        mock_request.reset_mock()

        # Otherwise, a client accesses the url which includes "v2/<projectid>".
        instance.get('servers')
        url = instance.management_url + 'servers'
        mock_request.assert_called_once_with(url, 'GET', headers=mock.ANY)

    def test_client_version_url(self):
        self._check_version_url('http://foo.com/v2/%s', 'http://foo.com/')

    def test_client_version_url_with_project_name(self):
        self._check_version_url('http://foo.com/nova/v2/%s',
                                'http://foo.com/nova/')

    def test_get_client_class_v3(self):
        output = novaclient.client.get_client_class('3')
        self.assertEqual(output, novaclient.v2.client.Client)

    def test_get_client_class_v2(self):
        output = novaclient.client.get_client_class('2')
        self.assertEqual(output, novaclient.v2.client.Client)

    def test_get_client_class_v2_int(self):
        output = novaclient.client.get_client_class(2)
        self.assertEqual(output, novaclient.v2.client.Client)

    def test_get_client_class_v1_1(self):
        output = novaclient.client.get_client_class('1.1')
        self.assertEqual(output, novaclient.v2.client.Client)

    def test_get_client_class_unknown(self):
        self.assertRaises(novaclient.exceptions.UnsupportedVersion,
                          novaclient.client.get_client_class, '0')

    def test_client_with_os_cache_enabled(self):
        cs = novaclient.v2.client.Client("user", "password", "project_id",
                                         auth_url="foo/v2", os_cache=True)
        self.assertEqual(True, cs.os_cache)
        self.assertEqual(True, cs.client.os_cache)

    def test_client_with_os_cache_disabled(self):
        cs = novaclient.v2.client.Client("user", "password", "project_id",
                                         auth_url="foo/v2", os_cache=False)
        self.assertEqual(False, cs.os_cache)
        self.assertEqual(False, cs.client.os_cache)

    def test_client_with_no_cache_enabled(self):
        cs = novaclient.v2.client.Client("user", "password", "project_id",
                                         auth_url="foo/v2", no_cache=True)
        self.assertEqual(False, cs.os_cache)
        self.assertEqual(False, cs.client.os_cache)

    def test_client_with_no_cache_disabled(self):
        cs = novaclient.v2.client.Client("user", "password", "project_id",
                                         auth_url="foo/v2", no_cache=False)
        self.assertEqual(True, cs.os_cache)
        self.assertEqual(True, cs.client.os_cache)

    def test_client_set_management_url_v1_1(self):
        cs = novaclient.v2.client.Client("user", "password", "project_id",
                                         auth_url="foo/v2")
        cs.set_management_url("blabla")
        self.assertEqual("blabla", cs.client.management_url)

    def test_client_get_reset_timings_v1_1(self):
        cs = novaclient.v2.client.Client("user", "password", "project_id",
                                         auth_url="foo/v2")
        self.assertEqual(0, len(cs.get_timings()))
        cs.client.times.append("somevalue")
        self.assertEqual(1, len(cs.get_timings()))
        self.assertEqual("somevalue", cs.get_timings()[0])

        cs.reset_timings()
        self.assertEqual(0, len(cs.get_timings()))

    @mock.patch('novaclient.client.HTTPClient')
    def test_contextmanager_v1_1(self, mock_http_client):
        fake_client = mock.Mock()
        mock_http_client.return_value = fake_client
        with novaclient.v2.client.Client("user", "password", "project_id",
                                         auth_url="foo/v2"):
            pass
        self.assertTrue(fake_client.open_session.called)
        self.assertTrue(fake_client.close_session.called)

    def test_get_password_simple(self):
        cs = novaclient.client.HTTPClient("user", "password", "", "")
        cs.password_func = mock.Mock()
        self.assertEqual("password", cs._get_password())
        self.assertFalse(cs.password_func.called)

    def test_get_password_none(self):
        cs = novaclient.client.HTTPClient("user", None, "", "")
        self.assertIsNone(cs._get_password())

    def test_get_password_func(self):
        cs = novaclient.client.HTTPClient("user", None, "", "")
        cs.password_func = mock.Mock(return_value="password")
        self.assertEqual("password", cs._get_password())
        cs.password_func.assert_called_once_with()

        cs.password_func = mock.Mock()
        self.assertEqual("password", cs._get_password())
        self.assertFalse(cs.password_func.called)

    def test_auth_url_rstrip_slash(self):
        cs = novaclient.client.HTTPClient("user", "password", "project_id",
                                          auth_url="foo/v2/")
        self.assertEqual("foo/v2", cs.auth_url)

    def test_token_and_bypass_url(self):
        cs = novaclient.client.HTTPClient(None, None, None,
                                          auth_token="12345",
                                          bypass_url="compute/v100/")
        self.assertIsNone(cs.auth_url)
        self.assertEqual("12345", cs.auth_token)
        self.assertEqual("compute/v100", cs.bypass_url)
        self.assertEqual("compute/v100", cs.management_url)

    @mock.patch("novaclient.client.requests.Session")
    def test_session(self, mock_session):
        fake_session = mock.Mock()
        mock_session.return_value = fake_session
        cs = novaclient.client.HTTPClient("user", None, "", "")
        cs.open_session()
        self.assertEqual(cs._session, fake_session)
        cs.close_session()
        self.assertIsNone(cs._session)

    def test_session_connection_pool(self):
        cs = novaclient.client.HTTPClient("user", None, "",
                                          "", connection_pool=True)
        cs.open_session()
        self.assertIsNone(cs._session)
        cs.close_session()
        self.assertIsNone(cs._session)

    def test_get_session(self):
        cs = novaclient.client.HTTPClient("user", None, "", "")
        self.assertIsNone(cs._get_session("http://nooooooooo.com"))

    @mock.patch("novaclient.client.requests.Session")
    def test_get_session_open_session(self, mock_session):
        fake_session = mock.Mock()
        mock_session.return_value = fake_session
        cs = novaclient.client.HTTPClient("user", None, "", "")
        cs.open_session()
        self.assertEqual(fake_session, cs._get_session("http://example.com"))

    @mock.patch("novaclient.client.requests.Session")
    @mock.patch("novaclient.client._ClientConnectionPool")
    def test_get_session_connection_pool(self, mock_pool, mock_session):
        service_url = "http://example.com"

        pool = mock.MagicMock()
        pool.get.return_value = "http_adapter"
        mock_pool.return_value = pool
        cs = novaclient.client.HTTPClient("user", None, "",
                                          "", connection_pool=True)
        cs._current_url = "http://another.com"

        session = cs._get_session(service_url)
        self.assertEqual(session, mock_session.return_value)
        pool.get.assert_called_once_with(service_url)
        mock_session().mount.assert_called_once_with(service_url,
                                                     'http_adapter')

    def test_init_without_connection_pool(self):
        cs = novaclient.client.HTTPClient("user", None, "", "")
        self.assertIsNone(cs._connection_pool)

    @mock.patch("novaclient.client._ClientConnectionPool")
    def test_init_with_proper_connection_pool(self, mock_pool):
        fake_pool = mock.Mock()
        mock_pool.return_value = fake_pool
        cs = novaclient.client.HTTPClient("user", None, "",
                                          connection_pool=True)
        self.assertEqual(cs._connection_pool, fake_pool)

    def test_log_req(self):
        self.logger = self.useFixture(
            fixtures.FakeLogger(
                format="%(message)s",
                level=logging.DEBUG,
                nuke_handlers=True
            )
        )
        cs = novaclient.client.HTTPClient("user", None, "",
                                          connection_pool=True)
        cs.http_log_debug = True
        cs.http_log_req('GET', '/foo', {'headers': {}})
        cs.http_log_req('GET', '/foo', {'headers':
                                        {'X-Auth-Token': 'totally_bogus'}})
        cs.http_log_req('GET', '/foo', {'headers':
                                        {'X-Foo': 'bar',
                                         'X-Auth-Token': 'totally_bogus'}})
        cs.http_log_req('GET', '/foo', {'headers': {},
                                        'data':
                                            '{"auth": {"passwordCredentials": '
                                            '{"password": "zhaoqin"}}}'})

        output = self.logger.output.split('\n')

        self.assertIn("REQ: curl -g -i '/foo' -X GET", output)
        self.assertIn(
            "REQ: curl -g -i '/foo' -X GET -H "
            '"X-Auth-Token: {SHA1}b42162b6ffdbd7c3c37b7c95b7ba9f51dda0236d"',
            output)
        self.assertIn(
            "REQ: curl -g -i '/foo' -X GET -H "
            '"X-Auth-Token: {SHA1}b42162b6ffdbd7c3c37b7c95b7ba9f51dda0236d"'
            ' -H "X-Foo: bar"',
            output)
        self.assertIn(
            "REQ: curl -g -i '/foo' -X GET -d "
            '\'{"auth": {"passwordCredentials": {"password":'
            ' "{SHA1}4fc49c6a671ce889078ff6b250f7066cf6d2ada2"}}}\'',
            output)

    def test_log_resp(self):
        self.logger = self.useFixture(
            fixtures.FakeLogger(
                format="%(message)s",
                level=logging.DEBUG,
                nuke_handlers=True
            )
        )

        cs = novaclient.client.HTTPClient("user", None, "",
                                          connection_pool=True)
        cs.http_log_debug = True
        text = ('{"access": {"token": {"id": "zhaoqin"}}}')
        resp = utils.TestResponse({'status_code': 200, 'headers': {},
                                   'text': text})

        cs.http_log_resp(resp)
        output = self.logger.output.split('\n')

        self.assertIn('RESP: [200] {}', output)
        self.assertIn('RESP BODY: {"access": {"token": {"id":'
                      ' "{SHA1}4fc49c6a671ce889078ff6b250f7066cf6d2ada2"}}}',
                      output)
