# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Tests for Google Connection classes.
"""
import datetime
import sys
import unittest

try:
    import simplejson as json
except ImportError:
    import json

from libcloud.utils.py3 import httplib

from libcloud.test import MockHttp, LibcloudTestCase
from libcloud.common.google import (GoogleAuthError,
                                    GoogleBaseAuthConnection,
                                    GoogleInstalledAppAuthConnection,
                                    GoogleServiceAcctAuthConnection,
                                    GoogleBaseConnection)
from libcloud.test.secrets import GCE_PARAMS

# Skip some tests if PyCrypto is unavailable
try:
    from Crypto.Hash import SHA256
except ImportError:
    SHA256 = None


class MockJsonResponse(object):
    def __init__(self, body):
        self.object = body


class GoogleBaseAuthConnectionTest(LibcloudTestCase):
    """
    Tests for GoogleBaseAuthConnection
    """
    GoogleBaseAuthConnection._now = lambda x: datetime.datetime(2013, 6, 26,
                                                                19, 0, 0)

    def setUp(self):
        GoogleBaseAuthConnection.conn_classes = (GoogleAuthMockHttp,
                                                 GoogleAuthMockHttp)
        self.mock_scopes = ['foo', 'bar']
        kwargs = {'scopes': self.mock_scopes}
        self.conn = GoogleInstalledAppAuthConnection(*GCE_PARAMS,
                                                     **kwargs)

    def test_scopes(self):
        self.assertEqual(self.conn.scopes, 'foo bar')

    def test_add_default_headers(self):
        old_headers = {}
        expected_headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': 'accounts.google.com'}
        new_headers = self.conn.add_default_headers(old_headers)
        self.assertEqual(new_headers, expected_headers)

    def test_token_request(self):
        request_body = {'code': 'asdf', 'client_id': self.conn.user_id,
                        'client_secret': self.conn.key,
                        'redirect_uri': self.conn.redirect_uri,
                        'grant_type': 'authorization_code'}
        new_token = self.conn._token_request(request_body)
        self.assertEqual(new_token['access_token'], 'installedapp')
        self.assertEqual(new_token['expire_time'], '2013-06-26T20:00:00Z')


class GoogleInstalledAppAuthConnectionTest(LibcloudTestCase):
    """
    Tests for GoogleInstalledAppAuthConnection
    """
    GoogleInstalledAppAuthConnection.get_code = lambda x: '1234'

    def setUp(self):
        GoogleInstalledAppAuthConnection.conn_classes = (GoogleAuthMockHttp,
                                                         GoogleAuthMockHttp)
        self.mock_scopes = ['https://www.googleapis.com/auth/foo']
        kwargs = {'scopes': self.mock_scopes}
        self.conn = GoogleInstalledAppAuthConnection(*GCE_PARAMS,
                                                     **kwargs)

    def test_refresh_token(self):
        # This token info doesn't have a refresh token, so a new token will be
        # requested
        token_info1 = {'access_token': 'tokentoken', 'token_type': 'Bearer',
                       'expires_in': 3600}
        new_token1 = self.conn.refresh_token(token_info1)
        self.assertEqual(new_token1['access_token'], 'installedapp')

        # This token info has a refresh token, so it will be able to be
        # refreshed.
        token_info2 = {'access_token': 'tokentoken', 'token_type': 'Bearer',
                       'expires_in': 3600, 'refresh_token': 'refreshrefresh'}
        new_token2 = self.conn.refresh_token(token_info2)
        self.assertEqual(new_token2['access_token'], 'refreshrefresh')

        # Both sets should have refresh info
        self.assertTrue('refresh_token' in new_token1)
        self.assertTrue('refresh_token' in new_token2)


class GoogleBaseConnectionTest(LibcloudTestCase):
    """
    Tests for GoogleBaseConnection
    """
    GoogleBaseConnection._get_token_info_from_file = lambda x: None
    GoogleBaseConnection._write_token_info_to_file = lambda x: None
    GoogleInstalledAppAuthConnection.get_code = lambda x: '1234'
    GoogleServiceAcctAuthConnection.get_new_token = \
        lambda x: x._token_request({})
    GoogleBaseConnection._now = lambda x: datetime.datetime(2013, 6, 26,
                                                            19, 0, 0)

    def setUp(self):
        GoogleBaseAuthConnection.conn_classes = (GoogleAuthMockHttp,
                                                 GoogleAuthMockHttp)
        self.mock_scopes = ['https://www.googleapis.com/auth/foo']
        kwargs = {'scopes': self.mock_scopes, 'auth_type': 'IA'}
        self.conn = GoogleBaseConnection(*GCE_PARAMS, **kwargs)

    def test_auth_type(self):
        self.assertRaises(GoogleAuthError, GoogleBaseConnection, *GCE_PARAMS,
                          **{'auth_type': 'XX'})

        kwargs = {'scopes': self.mock_scopes}

        if SHA256:
            kwargs['auth_type'] = 'SA'
            conn1 = GoogleBaseConnection(*GCE_PARAMS, **kwargs)
            self.assertTrue(isinstance(conn1.auth_conn,
                                       GoogleServiceAcctAuthConnection))

        kwargs['auth_type'] = 'IA'
        conn2 = GoogleBaseConnection(*GCE_PARAMS, **kwargs)
        self.assertTrue(isinstance(conn2.auth_conn,
                                   GoogleInstalledAppAuthConnection))

    def test_add_default_headers(self):
        old_headers = {}
        new_expected_headers = {'Content-Type': 'application/json',
                                'Host': 'www.googleapis.com'}
        new_headers = self.conn.add_default_headers(old_headers)
        self.assertEqual(new_headers, new_expected_headers)

    def test_pre_connect_hook(self):
        old_params = {}
        old_headers = {}
        new_expected_params = {}
        new_expected_headers = {'Authorization': 'Bearer installedapp'}
        new_params, new_headers = self.conn.pre_connect_hook(old_params,
                                                             old_headers)
        self.assertEqual(new_params, new_expected_params)
        self.assertEqual(new_headers, new_expected_headers)

    def test_encode_data(self):
        data = {'key': 'value'}
        json_data = '{"key": "value"}'
        encoded_data = self.conn.encode_data(data)
        self.assertEqual(encoded_data, json_data)

    def test_has_completed(self):
        body1 = {"endTime": "2013-06-26T10:05:07.630-07:00",
                 "id": "3681664092089171723",
                 "kind": "compute#operation",
                 "status": "DONE",
                 "targetId": "16211908079305042870"}
        body2 = {"endTime": "2013-06-26T10:05:07.630-07:00",
                 "id": "3681664092089171723",
                 "kind": "compute#operation",
                 "status": "RUNNING",
                 "targetId": "16211908079305042870"}
        response1 = MockJsonResponse(body1)
        response2 = MockJsonResponse(body2)
        self.assertTrue(self.conn.has_completed(response1))
        self.assertFalse(self.conn.has_completed(response2))

    def test_get_poll_request_kwargs(self):
        body = {"endTime": "2013-06-26T10:05:07.630-07:00",
                "id": "3681664092089171723",
                "kind": "compute#operation",
                "selfLink": "https://www.googleapis.com/operations-test"}
        response = MockJsonResponse(body)
        expected_kwargs = {'action':
                           'https://www.googleapis.com/operations-test'}
        kwargs = self.conn.get_poll_request_kwargs(response, None, {})
        self.assertEqual(kwargs, expected_kwargs)

    def test_morph_action_hook(self):
        self.conn.request_path = '/compute/apiver/project/project-name'
        action1 = ('https://www.googleapis.com/compute/apiver/project'
                   '/project-name/instances')
        action2 = '/instances'
        expected_request = '/compute/apiver/project/project-name/instances'
        request1 = self.conn.morph_action_hook(action1)
        request2 = self.conn.morph_action_hook(action2)
        self.assertEqual(request1, expected_request)
        self.assertEqual(request2, expected_request)


class GoogleAuthMockHttp(MockHttp):
    """
    Mock HTTP Class for Google Auth Connections.
    """
    json_hdr = {'content-type': 'application/json; charset=UTF-8'}

    def _o_oauth2_token(self, method, url, body, headers):
        token_info = {'access_token': 'tokentoken',
                      'token_type': 'Bearer',
                      'expires_in': 3600}
        refresh_token = {'access_token': 'refreshrefresh',
                         'token_type': 'Bearer',
                         'expires_in': 3600}
        ia_token = {'access_token': 'installedapp',
                    'token_type': 'Bearer',
                    'expires_in': 3600,
                    'refresh_token': 'refreshrefresh'}
        if 'code' in body:
            body = json.dumps(ia_token)
        elif 'refresh_token' in body:
            body = json.dumps(refresh_token)
        else:
            body = json.dumps(token_info)
        return (httplib.OK, body, self.json_hdr, httplib.responses[httplib.OK])


if __name__ == '__main__':
    sys.exit(unittest.main())
