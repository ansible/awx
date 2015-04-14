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
import six

from novaclient import client
from novaclient import exceptions
from novaclient.tests.unit import utils


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

unknown_error_response = utils.TestResponse({
    "status_code": 503,
    "text": '',
})
unknown_error_mock_request = mock.Mock(return_value=unknown_error_response)

retry_after_response = utils.TestResponse({
    "status_code": 413,
    "text": '',
    "headers": {
        "retry-after": "5"
    },
})
retry_after_mock_request = mock.Mock(return_value=retry_after_response)

retry_after_no_headers_response = utils.TestResponse({
    "status_code": 413,
    "text": '',
})
retry_after_no_headers_mock_request = mock.Mock(
    return_value=retry_after_no_headers_response)

retry_after_non_supporting_response = utils.TestResponse({
    "status_code": 403,
    "text": '',
    "headers": {
        "retry-after": "5"
    },
})
retry_after_non_supporting_mock_request = mock.Mock(
    return_value=retry_after_non_supporting_response)


def get_client():
    cl = client.HTTPClient("username", "password",
                           "project_id",
                           utils.AUTH_URL_V2)
    return cl


def get_authed_client():
    cl = get_client()
    cl.management_url = "http://example.com"
    cl.auth_token = "token"
    return cl


class ClientTest(utils.TestCase):

    def test_get(self):
        cl = get_authed_client()

        @mock.patch.object(requests, "request", mock_request)
        @mock.patch('time.time', mock.Mock(return_value=1234))
        def test_get_call():
            resp, body = cl.get("/hi")
            headers = {"X-Auth-Token": "token",
                       "X-Auth-Project-Id": "project_id",
                       "User-Agent": cl.USER_AGENT,
                       'Accept': 'application/json'}
            mock_request.assert_called_with(
                "GET",
                "http://example.com/hi",
                headers=headers,
                **self.TEST_REQUEST_BASE)
            # Automatic JSON parsing
            self.assertEqual({"hi": "there"}, body)

        test_get_call()

    def test_post(self):
        cl = get_authed_client()

        @mock.patch.object(requests, "request", mock_request)
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

    def test_auth_failure_due_to_miss_of_auth_url(self):
        cl = client.HTTPClient("username", "password")

        self.assertRaises(exceptions.AuthorizationFailure, cl.authenticate)

    def test_connection_refused(self):
        cl = get_client()

        @mock.patch.object(requests, "request", refused_mock_request)
        def test_refused_call():
            self.assertRaises(exceptions.ConnectionRefused, cl.get, "/hi")

        test_refused_call()

    def test_bad_request(self):
        cl = get_client()

        @mock.patch.object(requests, "request", bad_req_mock_request)
        def test_refused_call():
            self.assertRaises(exceptions.BadRequest, cl.get, "/hi")

        test_refused_call()

    def test_client_logger(self):
        cl1 = client.HTTPClient("username", "password", "project_id",
                                "auth_test", http_log_debug=True)
        self.assertEqual(1, len(cl1._logger.handlers))

        cl2 = client.HTTPClient("username", "password", "project_id",
                                "auth_test", http_log_debug=True)
        self.assertEqual(1, len(cl2._logger.handlers))

    @mock.patch.object(requests, 'request', unknown_error_mock_request)
    def test_unknown_server_error(self):
        cl = get_client()
        # This would be cleaner with the context manager version of
        # assertRaises or assertRaisesRegexp, but both only appeared in
        # Python 2.7 and testtools doesn't match that implementation yet
        try:
            cl.get('/hi')
        except exceptions.ClientException as exc:
            self.assertIn('Unknown Error', six.text_type(exc))
        else:
            self.fail('Expected exceptions.ClientException')

    @mock.patch.object(requests, "request", retry_after_mock_request)
    def test_retry_after_request(self):
        cl = get_client()

        try:
            cl.get("/hi")
        except exceptions.OverLimit as exc:
            self.assertEqual(5, exc.retry_after)
        else:
            self.fail('Expected exceptions.OverLimit')

    @mock.patch.object(requests, "request",
                       retry_after_no_headers_mock_request)
    def test_retry_after_request_no_headers(self):
        cl = get_client()

        try:
            cl.get("/hi")
        except exceptions.OverLimit as exc:
            self.assertEqual(0, exc.retry_after)
        else:
            self.fail('Expected exceptions.OverLimit')

    @mock.patch.object(requests, "request",
                       retry_after_non_supporting_mock_request)
    def test_retry_after_request_non_supporting_exc(self):
        cl = get_client()

        self.assertRaises(exceptions.Forbidden, cl.get, "/hi")
