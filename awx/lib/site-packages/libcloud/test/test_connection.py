# -*- coding: utf-8 -*-
# Licensed to the Apache Software Foundation (ASF) under one or more§
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

import sys
import ssl

from mock import Mock, call

from libcloud.test import unittest
from libcloud.common.base import Connection
from libcloud.common.base import LoggingConnection


class ConnectionClassTestCase(unittest.TestCase):
    def setUp(self):
        self.originalConnect = Connection.connect
        self.originalResponseCls = Connection.responseCls

        Connection.connect = Mock()
        Connection.responseCls = Mock()
        Connection.allow_insecure = True

    def tearDown(self):
        Connection.connect = self.originalConnect
        Connection.responseCls = Connection.responseCls
        Connection.allow_insecure = True

    def test_dont_allow_insecure(self):
        Connection.allow_insecure = True
        Connection(secure=False)

        Connection.allow_insecure = False

        expected_msg = (r'Non https connections are not allowed \(use '
                        'secure=True\)')
        self.assertRaisesRegexp(ValueError, expected_msg, Connection,
                                secure=False)

    def test_content_length(self):
        con = Connection()
        con.connection = Mock()

        # GET method
        # No data, no content length should be present
        con.request('/test', method='GET', data=None)
        call_kwargs = con.connection.request.call_args[1]
        self.assertTrue('Content-Length' not in call_kwargs['headers'])

        # '' as data, no content length should be present
        con.request('/test', method='GET', data='')
        call_kwargs = con.connection.request.call_args[1]
        self.assertTrue('Content-Length' not in call_kwargs['headers'])

        # 'a' as data, content length should be present (data in GET is not
        # correct, but anyways)
        con.request('/test', method='GET', data='a')
        call_kwargs = con.connection.request.call_args[1]
        self.assertEqual(call_kwargs['headers']['Content-Length'], '1')

        # POST, PUT method
        # No data, content length should be present
        for method in ['POST', 'PUT', 'post', 'put']:
            con.request('/test', method=method, data=None)
            call_kwargs = con.connection.request.call_args[1]
            self.assertEqual(call_kwargs['headers']['Content-Length'], '0')

        # '' as data, content length should be present
        for method in ['POST', 'PUT', 'post', 'put']:
            con.request('/test', method=method, data='')
            call_kwargs = con.connection.request.call_args[1]
            self.assertEqual(call_kwargs['headers']['Content-Length'], '0')

        # No data, raw request, do not touch Content-Length if present
        for method in ['POST', 'PUT', 'post', 'put']:
            con.request('/test', method=method, data=None,
                        headers={'Content-Length': '42'}, raw=True)
            putheader_call_list = con.connection.putheader.call_args_list
            self.assertIn(call('Content-Length', '42'), putheader_call_list)

        # '' as data, raw request, do not touch Content-Length if present
        for method in ['POST', 'PUT', 'post', 'put']:
            con.request('/test', method=method, data=None,
                        headers={'Content-Length': '42'}, raw=True)
            putheader_call_list = con.connection.putheader.call_args_list
            self.assertIn(call('Content-Length', '42'), putheader_call_list)

        # 'a' as data, content length should be present
        for method in ['POST', 'PUT', 'post', 'put']:
            con.request('/test', method=method, data='a')
            call_kwargs = con.connection.request.call_args[1]
            self.assertEqual(call_kwargs['headers']['Content-Length'], '1')

    def test_cache_busting(self):
        params1 = {'foo1': 'bar1', 'foo2': 'bar2'}
        params2 = [('foo1', 'bar1'), ('foo2', 'bar2')]

        con = Connection()
        con.connection = Mock()
        con.pre_connect_hook = Mock()
        con.pre_connect_hook.return_value = {}, {}
        con.cache_busting = False

        con.request(action='/path', params=params1)
        args, kwargs = con.pre_connect_hook.call_args
        self.assertFalse('cache-busting' in args[0])
        self.assertEqual(args[0], params1)

        con.request(action='/path', params=params2)
        args, kwargs = con.pre_connect_hook.call_args
        self.assertFalse('cache-busting' in args[0])
        self.assertEqual(args[0], params2)

        con.cache_busting = True

        con.request(action='/path', params=params1)
        args, kwargs = con.pre_connect_hook.call_args
        self.assertTrue('cache-busting' in args[0])

        con.request(action='/path', params=params2)
        args, kwargs = con.pre_connect_hook.call_args
        self.assertTrue('cache-busting' in args[0][len(params2)])

    def test_context_is_reset_after_request_has_finished(self):
        context = {'foo': 'bar'}

        def responseCls(connection, response):
            connection.called = True
            self.assertEqual(connection.context, context)

        con = Connection()
        con.called = False
        con.connection = Mock()
        con.responseCls = responseCls

        con.set_context(context)
        self.assertEqual(con.context, context)

        con.request('/')

        # Context should have been reset
        self.assertTrue(con.called)
        self.assertEqual(con.context, {})

        # Context should also be reset if a method inside request throws
        con = Connection()
        con.connection = Mock()

        con.set_context(context)
        self.assertEqual(con.context, context)

        con.connection.request = Mock(side_effect=ssl.SSLError())

        try:
            con.request('/')
        except ssl.SSLError:
            pass

        self.assertEqual(con.context, {})

        con.connection = Mock()
        con.set_context(context)
        self.assertEqual(con.context, context)

        con.responseCls = Mock(side_effect=ValueError())

        try:
            con.request('/')
        except ValueError:
            pass

        self.assertEqual(con.context, {})

    def test_log_curl(self):
        url = '/test/path'
        body = None
        headers = {}

        con = LoggingConnection()
        con.protocol = 'http'
        con.host = 'example.com'
        con.port = 80

        for method in ['GET', 'POST', 'PUT', 'DELETE']:
            cmd = con._log_curl(method=method, url=url, body=body,
                                headers=headers)
            self.assertEqual(cmd, 'curl -i -X %s --compress http://example.com:80/test/path' %
                             (method))

        # Should use --head for head requests
        cmd = con._log_curl(method='HEAD', url=url, body=body, headers=headers)
        self.assertEqual(cmd, 'curl -i --head --compress http://example.com:80/test/path')

if __name__ == '__main__':
    sys.exit(unittest.main())
