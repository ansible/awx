# Copyright 2013 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging

import six
from testtools import matchers

from keystoneclient import exceptions
from keystoneclient import httpclient
from keystoneclient import session
from keystoneclient.tests.unit import utils


RESPONSE_BODY = '{"hi": "there"}'


def get_client():
    cl = httpclient.HTTPClient(username="username", password="password",
                               tenant_id="tenant", auth_url="auth_test")
    return cl


def get_authed_client():
    cl = get_client()
    cl.management_url = "http://127.0.0.1:5000"
    cl.auth_token = "token"
    return cl


class FakeLog(object):
    def __init__(self):
        self.warn_log = str()
        self.debug_log = str()

    def warn(self, msg=None, *args, **kwargs):
        self.warn_log = "%s\n%s" % (self.warn_log, (msg % args))

    def debug(self, msg=None, *args, **kwargs):
        self.debug_log = "%s\n%s" % (self.debug_log, (msg % args))


class ClientTest(utils.TestCase):

    TEST_URL = 'http://127.0.0.1:5000/hi'

    def test_unauthorized_client_requests(self):
        cl = get_client()
        self.assertRaises(exceptions.AuthorizationFailure, cl.get, '/hi')
        self.assertRaises(exceptions.AuthorizationFailure, cl.post, '/hi')
        self.assertRaises(exceptions.AuthorizationFailure, cl.put, '/hi')
        self.assertRaises(exceptions.AuthorizationFailure, cl.delete, '/hi')

    def test_get(self):
        cl = get_authed_client()

        self.stub_url('GET', text=RESPONSE_BODY)

        resp, body = cl.get("/hi")
        self.assertEqual(self.requests_mock.last_request.method, 'GET')
        self.assertEqual(self.requests_mock.last_request.url, self.TEST_URL)

        self.assertRequestHeaderEqual('X-Auth-Token', 'token')
        self.assertRequestHeaderEqual('User-Agent', httpclient.USER_AGENT)

        # Automatic JSON parsing
        self.assertEqual(body, {"hi": "there"})

    def test_get_error_with_plaintext_resp(self):
        cl = get_authed_client()
        self.stub_url('GET', status_code=400,
                      text='Some evil plaintext string')

        self.assertRaises(exceptions.BadRequest, cl.get, '/hi')

    def test_get_error_with_json_resp(self):
        cl = get_authed_client()
        err_response = {
            "error": {
                "code": 400,
                "title": "Error title",
                "message": "Error message string"
            }
        }
        self.stub_url('GET', status_code=400, json=err_response)
        exc_raised = False
        try:
            cl.get('/hi')
        except exceptions.BadRequest as exc:
            exc_raised = True
            self.assertEqual(exc.message, "Error message string")
        self.assertTrue(exc_raised, 'Exception not raised.')

    def test_post(self):
        cl = get_authed_client()

        self.stub_url('POST')
        cl.post("/hi", body=[1, 2, 3])

        self.assertEqual(self.requests_mock.last_request.method, 'POST')
        self.assertEqual(self.requests_mock.last_request.body, '[1, 2, 3]')

        self.assertRequestHeaderEqual('X-Auth-Token', 'token')
        self.assertRequestHeaderEqual('Content-Type', 'application/json')
        self.assertRequestHeaderEqual('User-Agent', httpclient.USER_AGENT)

    def test_forwarded_for(self):
        ORIGINAL_IP = "10.100.100.1"
        cl = httpclient.HTTPClient(username="username", password="password",
                                   tenant_id="tenant", auth_url="auth_test",
                                   original_ip=ORIGINAL_IP)

        self.stub_url('GET')

        cl.request(self.TEST_URL, 'GET')
        forwarded = "for=%s;by=%s" % (ORIGINAL_IP, httpclient.USER_AGENT)
        self.assertRequestHeaderEqual('Forwarded', forwarded)

    def test_client_deprecated(self):
        # Can resolve symbols from the keystoneclient.client module.
        # keystoneclient.client was deprecated and renamed to
        # keystoneclient.httpclient. This tests that keystoneclient.client
        # can still be used.

        from keystoneclient import client

        # These statements will raise an AttributeError if the symbol isn't
        # defined in the module.

        client.HTTPClient


class BasicRequestTests(utils.TestCase):

    url = 'http://keystone.test.com/'

    def setUp(self):
        super(BasicRequestTests, self).setUp()
        self.logger_message = six.moves.cStringIO()
        handler = logging.StreamHandler(self.logger_message)
        handler.setLevel(logging.DEBUG)

        self.logger = logging.getLogger(session.__name__)
        level = self.logger.getEffectiveLevel()
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(handler)

        self.addCleanup(self.logger.removeHandler, handler)
        self.addCleanup(self.logger.setLevel, level)

    def request(self, method='GET', response='Test Response', status_code=200,
                url=None, **kwargs):
        if not url:
            url = self.url

        self.requests_mock.register_uri(method, url, text=response,
                                        status_code=status_code)

        return httpclient.request(url, method, **kwargs)

    def test_basic_params(self):
        method = 'GET'
        response = 'Test Response'
        status = 200

        self.request(method=method, status_code=status, response=response)

        self.assertEqual(self.requests_mock.last_request.method, method)

        logger_message = self.logger_message.getvalue()

        self.assertThat(logger_message, matchers.Contains('curl'))
        self.assertThat(logger_message, matchers.Contains('-X %s' %
                                                          method))
        self.assertThat(logger_message, matchers.Contains(self.url))

        self.assertThat(logger_message, matchers.Contains(str(status)))
        self.assertThat(logger_message, matchers.Contains(response))

    def test_headers(self):
        headers = {'key': 'val', 'test': 'other'}

        self.request(headers=headers)

        for k, v in six.iteritems(headers):
            self.assertRequestHeaderEqual(k, v)

        for header in six.iteritems(headers):
            self.assertThat(self.logger_message.getvalue(),
                            matchers.Contains('-H "%s: %s"' % header))

    def test_body(self):
        data = "BODY DATA"
        self.request(response=data)
        logger_message = self.logger_message.getvalue()
        self.assertThat(logger_message, matchers.Contains('BODY:'))
        self.assertThat(logger_message, matchers.Contains(data))
