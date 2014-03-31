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
import requests

from novaclient import client
from novaclient import exceptions
from novaclient.tests import utils


fake_response = utils.TestResponse({
    "status_code": 200,
    "text": '{"hi": "there"}',
})
mock_request = mock.Mock(return_value=(fake_response))

refused_response = utils.TestResponse({
    "status_code": 400,
    "text": '[Errno 111] Connection refused',
})
refused_mock_request = mock.Mock(return_value=(refused_response))

bad_req_response = utils.TestResponse({
    "status_code": 400,
    "text": '',
})
bad_req_mock_request = mock.Mock(return_value=(bad_req_response))


def get_client():
    cl = client.HTTPClient("username", "password",
                           "project_id", "auth_test")
    return cl


def get_authed_client():
    cl = get_client()
    cl.management_url = "http://example.com"
    cl.auth_token = "token"
    return cl


class ClientTest(utils.TestCase):

    def test_get(self):
        cl = get_authed_client()

        @mock.patch.object(requests.Session, "request", mock_request)
        @mock.patch('time.time', mock.Mock(return_value=1234))
        def test_get_call():
            resp, body = cl.get("/hi")
            headers = {"X-Auth-Token": "token",
                       "X-Auth-Project-Id": "project_id",
                       "User-Agent": cl.USER_AGENT,
                       'Accept': 'application/json',
            }
            mock_request.assert_called_with(
                "GET",
                "http://example.com/hi",
                headers=headers,
                **self.TEST_REQUEST_BASE)
            # Automatic JSON parsing
            self.assertEqual(body, {"hi": "there"})

        test_get_call()

    def test_post(self):
        cl = get_authed_client()

        @mock.patch.object(requests.Session, "request", mock_request)
        def test_post_call():
            cl.post("/hi", body=[1, 2, 3])
            headers = {
                "X-Auth-Token": "token",
                "X-Auth-Project-Id": "project_id",
                "Content-Type": "application/json",
                'Accept': 'application/json',
                "User-Agent": cl.USER_AGENT
            }
            mock_request.assert_called_with(
                "POST",
                "http://example.com/hi",
                headers=headers,
                data='[1, 2, 3]',
                **self.TEST_REQUEST_BASE)

        test_post_call()

    def test_auth_failure(self):
        cl = get_client()

        # response must not have x-server-management-url header
        @mock.patch.object(requests.Session, "request", mock_request)
        def test_auth_call():
            self.assertRaises(exceptions.AuthorizationFailure, cl.authenticate)

        test_auth_call()

    def test_connection_refused(self):
        cl = get_client()

        @mock.patch.object(requests.Session, "request", refused_mock_request)
        def test_refused_call():
            self.assertRaises(exceptions.ConnectionRefused, cl.get, "/hi")

        test_refused_call()

    def test_bad_request(self):
        cl = get_client()

        @mock.patch.object(requests.Session, "request", bad_req_mock_request)
        def test_refused_call():
            self.assertRaises(exceptions.BadRequest, cl.get, "/hi")

        test_refused_call()

    def test_client_logger(self):
        cl1 = client.HTTPClient("username", "password", "project_id",
                                "auth_test", http_log_debug=True)
        self.assertEqual(len(cl1._logger.handlers), 1)

        cl2 = client.HTTPClient("username", "password", "project_id",
                                "auth_test", http_log_debug=True)
        self.assertEqual(len(cl2._logger.handlers), 1)
