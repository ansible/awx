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

from keystoneclient import httpclient
from keystoneclient.tests.unit import utils


FAKE_RESPONSE = utils.TestResponse({
    "status_code": 200,
    "text": '{"hi": "there"}',
})

REQUEST_URL = 'https://127.0.0.1:5000/hi'
RESPONSE_BODY = '{"hi": "there"}'


def get_client():
    cl = httpclient.HTTPClient(username="username", password="password",
                               tenant_id="tenant", auth_url="auth_test",
                               cacert="ca.pem", key="key.pem", cert="cert.pem")
    return cl


def get_authed_client():
    cl = get_client()
    cl.management_url = "https://127.0.0.1:5000"
    cl.auth_token = "token"
    return cl


class ClientTest(utils.TestCase):

    def setUp(self):
        super(ClientTest, self).setUp()
        self.request_patcher = mock.patch.object(requests, 'request',
                                                 self.mox.CreateMockAnything())
        self.request_patcher.start()
        self.addCleanup(self.request_patcher.stop)

    @mock.patch.object(requests, 'request')
    def test_get(self, MOCK_REQUEST):
        MOCK_REQUEST.return_value = FAKE_RESPONSE
        cl = get_authed_client()

        resp, body = cl.get("/hi")

        # this may become too tightly couple later
        mock_args, mock_kwargs = MOCK_REQUEST.call_args

        self.assertEqual(mock_args[0], 'GET')
        self.assertEqual(mock_args[1], REQUEST_URL)
        self.assertEqual(mock_kwargs['headers']['X-Auth-Token'], 'token')
        self.assertEqual(mock_kwargs['cert'], ('cert.pem', 'key.pem'))
        self.assertEqual(mock_kwargs['verify'], 'ca.pem')

        # Automatic JSON parsing
        self.assertEqual(body, {"hi": "there"})

    @mock.patch.object(requests, 'request')
    def test_post(self, MOCK_REQUEST):
        MOCK_REQUEST.return_value = FAKE_RESPONSE
        cl = get_authed_client()

        cl.post("/hi", body=[1, 2, 3])

        # this may become too tightly couple later
        mock_args, mock_kwargs = MOCK_REQUEST.call_args

        self.assertEqual(mock_args[0], 'POST')
        self.assertEqual(mock_args[1], REQUEST_URL)
        self.assertEqual(mock_kwargs['data'], '[1, 2, 3]')
        self.assertEqual(mock_kwargs['headers']['X-Auth-Token'], 'token')
        self.assertEqual(mock_kwargs['cert'], ('cert.pem', 'key.pem'))
        self.assertEqual(mock_kwargs['verify'], 'ca.pem')

    @mock.patch.object(requests, 'request')
    def test_post_auth(self, MOCK_REQUEST):
        MOCK_REQUEST.return_value = FAKE_RESPONSE
        cl = httpclient.HTTPClient(
            username="username", password="password", tenant_id="tenant",
            auth_url="auth_test", cacert="ca.pem", key="key.pem",
            cert="cert.pem")
        cl.management_url = "https://127.0.0.1:5000"
        cl.auth_token = "token"
        cl.post("/hi", body=[1, 2, 3])

        # this may become too tightly couple later
        mock_args, mock_kwargs = MOCK_REQUEST.call_args

        self.assertEqual(mock_args[0], 'POST')
        self.assertEqual(mock_args[1], REQUEST_URL)
        self.assertEqual(mock_kwargs['data'], '[1, 2, 3]')
        self.assertEqual(mock_kwargs['headers']['X-Auth-Token'], 'token')
        self.assertEqual(mock_kwargs['cert'], ('cert.pem', 'key.pem'))
        self.assertEqual(mock_kwargs['verify'], 'ca.pem')
