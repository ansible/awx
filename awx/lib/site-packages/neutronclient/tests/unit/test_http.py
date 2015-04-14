# Copyright (C) 2013 OpenStack Foundation.
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

import abc

from requests_mock.contrib import fixture as mock_fixture
import six
import testtools

from neutronclient import client
from neutronclient.common import exceptions
from neutronclient.tests.unit import test_auth


AUTH_TOKEN = 'test_token'
END_URL = 'test_url'
METHOD = 'GET'
URL = 'http://test.test:1234/v2.0/test'
BODY = 'IAMFAKE'


@six.add_metaclass(abc.ABCMeta)
class TestHTTPClientMixin(object):

    def setUp(self):
        super(TestHTTPClientMixin, self).setUp()

        self.requests = self.useFixture(mock_fixture.Fixture())
        self.clazz, self.http = self.initialize()

    @abc.abstractmethod
    def initialize(self):
        """Return client class, instance."""

    def _test_headers(self, expected_headers, **kwargs):
        """Test headers."""
        self.requests.register_uri(METHOD, URL,
                                   request_headers=expected_headers)
        self.http.request(URL, METHOD, **kwargs)
        self.assertEqual(kwargs.get('body'), self.requests.last_request.body)

    def test_headers_without_body(self):
        self._test_headers({'Accept': 'application/json'})

    def test_headers_with_body(self):
        headers = {'Accept': 'application/json',
                   'Content-Type': 'application/json'}
        self._test_headers(headers, body=BODY)

    def test_headers_without_body_with_content_type(self):
        headers = {'Accept': 'application/xml'}
        self._test_headers(headers, content_type='application/xml')

    def test_headers_with_body_with_content_type(self):
        headers = {'Accept': 'application/xml',
                   'Content-Type': 'application/xml'}
        self._test_headers(headers, body=BODY, content_type='application/xml')

    def test_headers_defined_in_headers(self):
        headers = {'Accept': 'application/xml',
                   'Content-Type': 'application/xml'}
        self._test_headers(headers, body=BODY, headers=headers)


class TestSessionClient(TestHTTPClientMixin, testtools.TestCase):

    def initialize(self):
        session, auth = test_auth.setup_keystone_v2(self.requests)
        return [client.SessionClient,
                client.SessionClient(session=session, auth=auth)]


class TestHTTPClient(TestHTTPClientMixin, testtools.TestCase):

    def initialize(self):
        return [client.HTTPClient,
                client.HTTPClient(token=AUTH_TOKEN, endpoint_url=END_URL)]

    def test_request_error(self):
        def cb(*args, **kwargs):
            raise Exception('error msg')

        self.requests.get(URL, body=cb)
        self.assertRaises(
            exceptions.ConnectionFailed,
            self.http._cs_request,
            URL, METHOD
        )

    def test_request_success(self):
        text = 'test content'
        self.requests.register_uri(METHOD, URL, text=text)

        resp, resp_text = self.http._cs_request(URL, METHOD)
        self.assertEqual(200, resp.status_code)
        self.assertEqual(text, resp_text)

    def test_request_unauthorized(self):
        text = 'unauthorized message'
        self.requests.register_uri(METHOD, URL, status_code=401, text=text)
        e = self.assertRaises(exceptions.Unauthorized,
                              self.http._cs_request, URL, METHOD)
        self.assertEqual(text, e.message)

    def test_request_forbidden_is_returned_to_caller(self):
        text = 'forbidden message'
        self.requests.register_uri(METHOD, URL, status_code=403, text=text)

        resp, resp_text = self.http._cs_request(URL, METHOD)
        self.assertEqual(403, resp.status_code)
        self.assertEqual(text, resp_text)
