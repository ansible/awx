# Copyright 2012 OpenStack Foundation
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

import mock
from oslo_serialization import jsonutils
import requests
import six
import testtools
import webob

from keystoneclient.middleware import s3_token
from keystoneclient.tests.unit import utils


GOOD_RESPONSE = {'access': {'token': {'id': 'TOKEN_ID',
                                      'tenant': {'id': 'TENANT_ID'}}}}


class FakeApp(object):
    """This represents a WSGI app protected by the auth_token middleware."""
    def __call__(self, env, start_response):
        resp = webob.Response()
        resp.environ = env
        return resp(env, start_response)


class S3TokenMiddlewareTestBase(utils.TestCase):

    TEST_PROTOCOL = 'https'
    TEST_HOST = 'fakehost'
    TEST_PORT = 35357
    TEST_URL = '%s://%s:%d/v2.0/s3tokens' % (TEST_PROTOCOL,
                                             TEST_HOST,
                                             TEST_PORT)

    def setUp(self):
        super(S3TokenMiddlewareTestBase, self).setUp()

        self.conf = {
            'auth_host': self.TEST_HOST,
            'auth_port': self.TEST_PORT,
            'auth_protocol': self.TEST_PROTOCOL,
        }

    def start_fake_response(self, status, headers):
        self.response_status = int(status.split(' ', 1)[0])
        self.response_headers = dict(headers)


class S3TokenMiddlewareTestGood(S3TokenMiddlewareTestBase):

    def setUp(self):
        super(S3TokenMiddlewareTestGood, self).setUp()
        self.middleware = s3_token.S3Token(FakeApp(), self.conf)

        self.requests_mock.post(self.TEST_URL,
                                status_code=201,
                                json=GOOD_RESPONSE)

    # Ignore the request and pass to the next middleware in the
    # pipeline if no path has been specified.
    def test_no_path_request(self):
        req = webob.Request.blank('/')
        self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(self.response_status, 200)

    # Ignore the request and pass to the next middleware in the
    # pipeline if no Authorization header has been specified
    def test_without_authorization(self):
        req = webob.Request.blank('/v1/AUTH_cfa/c/o')
        self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(self.response_status, 200)

    def test_without_auth_storage_token(self):
        req = webob.Request.blank('/v1/AUTH_cfa/c/o')
        req.headers['Authorization'] = 'badboy'
        self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(self.response_status, 200)

    def test_authorized(self):
        req = webob.Request.blank('/v1/AUTH_cfa/c/o')
        req.headers['Authorization'] = 'access:signature'
        req.headers['X-Storage-Token'] = 'token'
        req.get_response(self.middleware)
        self.assertTrue(req.path.startswith('/v1/AUTH_TENANT_ID'))
        self.assertEqual(req.headers['X-Auth-Token'], 'TOKEN_ID')

    def test_authorized_http(self):
        TEST_URL = 'http://%s:%d/v2.0/s3tokens' % (self.TEST_HOST,
                                                   self.TEST_PORT)

        self.requests_mock.post(TEST_URL, status_code=201, json=GOOD_RESPONSE)

        self.middleware = (
            s3_token.filter_factory({'auth_protocol': 'http',
                                     'auth_host': self.TEST_HOST,
                                     'auth_port': self.TEST_PORT})(FakeApp()))
        req = webob.Request.blank('/v1/AUTH_cfa/c/o')
        req.headers['Authorization'] = 'access:signature'
        req.headers['X-Storage-Token'] = 'token'
        req.get_response(self.middleware)
        self.assertTrue(req.path.startswith('/v1/AUTH_TENANT_ID'))
        self.assertEqual(req.headers['X-Auth-Token'], 'TOKEN_ID')

    def test_authorization_nova_toconnect(self):
        req = webob.Request.blank('/v1/AUTH_swiftint/c/o')
        req.headers['Authorization'] = 'access:FORCED_TENANT_ID:signature'
        req.headers['X-Storage-Token'] = 'token'
        req.get_response(self.middleware)
        path = req.environ['PATH_INFO']
        self.assertTrue(path.startswith('/v1/AUTH_FORCED_TENANT_ID'))

    @mock.patch.object(requests, 'post')
    def test_insecure(self, MOCK_REQUEST):
        self.middleware = (
            s3_token.filter_factory({'insecure': True})(FakeApp()))

        text_return_value = jsonutils.dumps(GOOD_RESPONSE)
        if six.PY3:
            text_return_value = text_return_value.encode()
        MOCK_REQUEST.return_value = utils.TestResponse({
            'status_code': 201,
            'text': text_return_value})

        req = webob.Request.blank('/v1/AUTH_cfa/c/o')
        req.headers['Authorization'] = 'access:signature'
        req.headers['X-Storage-Token'] = 'token'
        req.get_response(self.middleware)

        self.assertTrue(MOCK_REQUEST.called)
        mock_args, mock_kwargs = MOCK_REQUEST.call_args
        self.assertIs(mock_kwargs['verify'], False)


class S3TokenMiddlewareTestBad(S3TokenMiddlewareTestBase):
    def setUp(self):
        super(S3TokenMiddlewareTestBad, self).setUp()
        self.middleware = s3_token.S3Token(FakeApp(), self.conf)

    def test_unauthorized_token(self):
        ret = {"error":
               {"message": "EC2 access key not found.",
                "code": 401,
                "title": "Unauthorized"}}
        self.requests_mock.post(self.TEST_URL, status_code=403, json=ret)
        req = webob.Request.blank('/v1/AUTH_cfa/c/o')
        req.headers['Authorization'] = 'access:signature'
        req.headers['X-Storage-Token'] = 'token'
        resp = req.get_response(self.middleware)
        s3_denied_req = self.middleware.deny_request('AccessDenied')
        self.assertEqual(resp.body, s3_denied_req.body)
        self.assertEqual(resp.status_int, s3_denied_req.status_int)

    def test_bogus_authorization(self):
        req = webob.Request.blank('/v1/AUTH_cfa/c/o')
        req.headers['Authorization'] = 'badboy'
        req.headers['X-Storage-Token'] = 'token'
        resp = req.get_response(self.middleware)
        self.assertEqual(resp.status_int, 400)
        s3_invalid_req = self.middleware.deny_request('InvalidURI')
        self.assertEqual(resp.body, s3_invalid_req.body)
        self.assertEqual(resp.status_int, s3_invalid_req.status_int)

    def test_fail_to_connect_to_keystone(self):
        with mock.patch.object(self.middleware, '_json_request') as o:
            s3_invalid_req = self.middleware.deny_request('InvalidURI')
            o.side_effect = s3_token.ServiceError(s3_invalid_req)

            req = webob.Request.blank('/v1/AUTH_cfa/c/o')
            req.headers['Authorization'] = 'access:signature'
            req.headers['X-Storage-Token'] = 'token'
            resp = req.get_response(self.middleware)
            self.assertEqual(resp.body, s3_invalid_req.body)
            self.assertEqual(resp.status_int, s3_invalid_req.status_int)

    def test_bad_reply(self):
        self.requests_mock.post(self.TEST_URL,
                                status_code=201,
                                text="<badreply>")

        req = webob.Request.blank('/v1/AUTH_cfa/c/o')
        req.headers['Authorization'] = 'access:signature'
        req.headers['X-Storage-Token'] = 'token'
        resp = req.get_response(self.middleware)
        s3_invalid_req = self.middleware.deny_request('InvalidURI')
        self.assertEqual(resp.body, s3_invalid_req.body)
        self.assertEqual(resp.status_int, s3_invalid_req.status_int)


class S3TokenMiddlewareTestUtil(testtools.TestCase):
    def test_split_path_failed(self):
        self.assertRaises(ValueError, s3_token.split_path, '')
        self.assertRaises(ValueError, s3_token.split_path, '/')
        self.assertRaises(ValueError, s3_token.split_path, '//')
        self.assertRaises(ValueError, s3_token.split_path, '//a')
        self.assertRaises(ValueError, s3_token.split_path, '/a/c')
        self.assertRaises(ValueError, s3_token.split_path, '//c')
        self.assertRaises(ValueError, s3_token.split_path, '/a/c/')
        self.assertRaises(ValueError, s3_token.split_path, '/a//')
        self.assertRaises(ValueError, s3_token.split_path, '/a', 2)
        self.assertRaises(ValueError, s3_token.split_path, '/a', 2, 3)
        self.assertRaises(ValueError, s3_token.split_path, '/a', 2, 3, True)
        self.assertRaises(ValueError, s3_token.split_path, '/a/c/o/r', 3, 3)
        self.assertRaises(ValueError, s3_token.split_path, '/a', 5, 4)

    def test_split_path_success(self):
        self.assertEqual(s3_token.split_path('/a'), ['a'])
        self.assertEqual(s3_token.split_path('/a/'), ['a'])
        self.assertEqual(s3_token.split_path('/a/c', 2), ['a', 'c'])
        self.assertEqual(s3_token.split_path('/a/c/o', 3), ['a', 'c', 'o'])
        self.assertEqual(s3_token.split_path('/a/c/o/r', 3, 3, True),
                         ['a', 'c', 'o/r'])
        self.assertEqual(s3_token.split_path('/a/c', 2, 3, True),
                         ['a', 'c', None])
        self.assertEqual(s3_token.split_path('/a/c/', 2), ['a', 'c'])
        self.assertEqual(s3_token.split_path('/a/c/', 2, 3), ['a', 'c', ''])

    def test_split_path_invalid_path(self):
        try:
            s3_token.split_path('o\nn e', 2)
        except ValueError as err:
            self.assertEqual(str(err), 'Invalid path: o%0An%20e')
        try:
            s3_token.split_path('o\nn e', 2, 3, True)
        except ValueError as err:
            self.assertEqual(str(err), 'Invalid path: o%0An%20e')
