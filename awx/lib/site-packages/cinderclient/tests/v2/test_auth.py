# Copyright (c) 2013 OpenStack Foundation
#
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

import mock
import requests

from cinderclient import exceptions
from cinderclient.v2 import client
from cinderclient.tests import utils


class AuthenticateAgainstKeystoneTests(utils.TestCase):
    def test_authenticate_success(self):
        cs = client.Client("username", "password", "project_id",
                           "http://localhost:8776/v2", service_type='volumev2')
        resp = {
            "access": {
                "token": {
                    "expires": "2014-11-01T03:32:15-05:00",
                    "id": "FAKE_ID",
                },
                "serviceCatalog": [
                    {
                        "type": "volumev2",
                        "endpoints": [
                            {
                                "region": "RegionOne",
                                "adminURL": "http://localhost:8776/v2",
                                "internalURL": "http://localhost:8776/v2",
                                "publicURL": "http://localhost:8776/v2",
                            },
                        ],
                    },
                ],
            },
        }
        auth_response = utils.TestResponse({
            "status_code": 200,
            "text": json.dumps(resp),
        })

        mock_request = mock.Mock(return_value=(auth_response))

        @mock.patch.object(requests, "request", mock_request)
        def test_auth_call():
            cs.client.authenticate()
            headers = {
                'User-Agent': cs.client.USER_AGENT,
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }
            body = {
                'auth': {
                    'passwordCredentials': {
                        'username': cs.client.user,
                        'password': cs.client.password,
                    },
                    'tenantName': cs.client.projectid,
                },
            }

            token_url = cs.client.auth_url + "/tokens"
            mock_request.assert_called_with(
                "POST",
                token_url,
                headers=headers,
                data=json.dumps(body),
                allow_redirects=True,
                **self.TEST_REQUEST_BASE)

            endpoints = resp["access"]["serviceCatalog"][0]['endpoints']
            public_url = endpoints[0]["publicURL"].rstrip('/')
            self.assertEqual(public_url, cs.client.management_url)
            token_id = resp["access"]["token"]["id"]
            self.assertEqual(token_id, cs.client.auth_token)

        test_auth_call()

    def test_authenticate_tenant_id(self):
        cs = client.Client("username", "password",
                           auth_url="http://localhost:8776/v2",
                           tenant_id='tenant_id', service_type='volumev2')
        resp = {
            "access": {
                "token": {
                    "expires": "2014-11-01T03:32:15-05:00",
                    "id": "FAKE_ID",
                    "tenant": {
                        "description": None,
                        "enabled": True,
                        "id": "tenant_id",
                        "name": "demo"
                    }  # tenant associated with token
                },
                "serviceCatalog": [
                    {
                        "type": 'volumev2',
                        "endpoints": [
                            {
                                "region": "RegionOne",
                                "adminURL": "http://localhost:8776/v2",
                                "internalURL": "http://localhost:8776/v2",
                                "publicURL": "http://localhost:8776/v2",
                            },
                        ],
                    },
                ],
            },
        }
        auth_response = utils.TestResponse({
            "status_code": 200,
            "text": json.dumps(resp),
        })

        mock_request = mock.Mock(return_value=(auth_response))

        @mock.patch.object(requests, "request", mock_request)
        def test_auth_call():
            cs.client.authenticate()
            headers = {
                'User-Agent': cs.client.USER_AGENT,
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }
            body = {
                'auth': {
                    'passwordCredentials': {
                        'username': cs.client.user,
                        'password': cs.client.password,
                    },
                    'tenantId': cs.client.tenant_id,
                },
            }

            token_url = cs.client.auth_url + "/tokens"
            mock_request.assert_called_with(
                "POST",
                token_url,
                headers=headers,
                data=json.dumps(body),
                allow_redirects=True,
                **self.TEST_REQUEST_BASE)

            endpoints = resp["access"]["serviceCatalog"][0]['endpoints']
            public_url = endpoints[0]["publicURL"].rstrip('/')
            self.assertEqual(public_url, cs.client.management_url)
            token_id = resp["access"]["token"]["id"]
            self.assertEqual(token_id, cs.client.auth_token)
            tenant_id = resp["access"]["token"]["tenant"]["id"]
            self.assertEqual(tenant_id, cs.client.tenant_id)

        test_auth_call()

    def test_authenticate_failure(self):
        cs = client.Client("username", "password", "project_id",
                           "http://localhost:8776/v2")
        resp = {"unauthorized": {"message": "Unauthorized", "code": "401"}}
        auth_response = utils.TestResponse({
            "status_code": 401,
            "text": json.dumps(resp),
        })

        mock_request = mock.Mock(return_value=(auth_response))

        @mock.patch.object(requests, "request", mock_request)
        def test_auth_call():
            self.assertRaises(exceptions.Unauthorized, cs.client.authenticate)

        test_auth_call()

    def test_auth_redirect(self):
        cs = client.Client("username", "password", "project_id",
                           "http://localhost:8776/v2", service_type='volumev2')
        dict_correct_response = {
            "access": {
                "token": {
                    "expires": "2014-11-01T03:32:15-05:00",
                    "id": "FAKE_ID",
                },
                "serviceCatalog": [
                    {
                        "type": "volumev2",
                        "endpoints": [
                            {
                                "adminURL": "http://localhost:8776/v2",
                                "region": "RegionOne",
                                "internalURL": "http://localhost:8776/v2",
                                "publicURL": "http://localhost:8776/v2/",
                            },
                        ],
                    },
                ],
            },
        }
        correct_response = json.dumps(dict_correct_response)
        dict_responses = [
            {"headers": {'location': 'http://127.0.0.1:5001'},
             "status_code": 305,
             "text": "Use proxy"},
            # Configured on admin port, cinder redirects to v2.0 port.
            # When trying to connect on it, keystone auth succeed by v1.0
            # protocol (through headers) but tokens are being returned in
            # body (looks like keystone bug). Leaved for compatibility.
            {"headers": {},
             "status_code": 200,
             "text": correct_response},
            {"headers": {},
             "status_code": 200,
             "text": correct_response}
        ]

        responses = [(utils.TestResponse(resp)) for resp in dict_responses]

        def side_effect(*args, **kwargs):
            return responses.pop(0)

        mock_request = mock.Mock(side_effect=side_effect)

        @mock.patch.object(requests, "request", mock_request)
        def test_auth_call():
            cs.client.authenticate()
            headers = {
                'User-Agent': cs.client.USER_AGENT,
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }
            body = {
                'auth': {
                    'passwordCredentials': {
                        'username': cs.client.user,
                        'password': cs.client.password,
                    },
                    'tenantName': cs.client.projectid,
                },
            }

            token_url = cs.client.auth_url + "/tokens"
            mock_request.assert_called_with(
                "POST",
                token_url,
                headers=headers,
                data=json.dumps(body),
                allow_redirects=True,
                **self.TEST_REQUEST_BASE)

            resp = dict_correct_response
            endpoints = resp["access"]["serviceCatalog"][0]['endpoints']
            public_url = endpoints[0]["publicURL"].rstrip('/')
            self.assertEqual(public_url, cs.client.management_url)
            token_id = resp["access"]["token"]["id"]
            self.assertEqual(token_id, cs.client.auth_token)

        test_auth_call()


class AuthenticationTests(utils.TestCase):
    def test_authenticate_success(self):
        cs = client.Client("username", "password", "project_id", "auth_url")
        management_url = 'https://localhost/v2.1/443470'
        auth_response = utils.TestResponse({
            'status_code': 204,
            'headers': {
                'x-server-management-url': management_url,
                'x-auth-token': '1b751d74-de0c-46ae-84f0-915744b582d1',
            },
        })
        mock_request = mock.Mock(return_value=(auth_response))

        @mock.patch.object(requests, "request", mock_request)
        def test_auth_call():
            cs.client.authenticate()
            headers = {
                'Accept': 'application/json',
                'X-Auth-User': 'username',
                'X-Auth-Key': 'password',
                'X-Auth-Project-Id': 'project_id',
                'User-Agent': cs.client.USER_AGENT
            }
            mock_request.assert_called_with(
                "GET",
                cs.client.auth_url,
                headers=headers,
                **self.TEST_REQUEST_BASE)

            self.assertEqual(auth_response.headers['x-server-management-url'],
                             cs.client.management_url)
            self.assertEqual(auth_response.headers['x-auth-token'],
                             cs.client.auth_token)

        test_auth_call()

    def test_authenticate_failure(self):
        cs = client.Client("username", "password", "project_id", "auth_url")
        auth_response = utils.TestResponse({"status_code": 401})
        mock_request = mock.Mock(return_value=(auth_response))

        @mock.patch.object(requests, "request", mock_request)
        def test_auth_call():
            self.assertRaises(exceptions.Unauthorized, cs.client.authenticate)

        test_auth_call()

    def test_auth_automatic(self):
        cs = client.Client("username", "password", "project_id", "auth_url")
        http_client = cs.client
        http_client.management_url = ''
        mock_request = mock.Mock(return_value=(None, None))

        @mock.patch.object(http_client, 'request', mock_request)
        @mock.patch.object(http_client, 'authenticate')
        def test_auth_call(m):
            http_client.get('/')
            m.assert_called()
            mock_request.assert_called()

        test_auth_call()

    def test_auth_manual(self):
        cs = client.Client("username", "password", "project_id", "auth_url")

        @mock.patch.object(cs.client, 'authenticate')
        def test_auth_call(m):
            cs.authenticate()
            m.assert_called()

        test_auth_call()
