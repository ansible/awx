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

import sys
import unittest
import zlib
import gzip

from mock import Mock

from libcloud.utils.py3 import httplib, b, StringIO, PY3
from libcloud.common.base import Response, XmlResponse, JsonResponse
from libcloud.common.types import MalformedResponseError


class ResponseClassesTests(unittest.TestCase):
    def setUp(self):
        self._mock_response = Mock()
        self._mock_response.getheaders.return_value = []
        self._mock_response.status = httplib.OK
        self._mock_response._original_data = None
        self._mock_connection = Mock()

    def test_XmlResponse_class(self):
        self._mock_response.read.return_value = '<foo>bar</foo>'
        response = XmlResponse(response=self._mock_response,
                               connection=self._mock_connection)

        parsed = response.parse_body()
        self.assertEqual(parsed.tag, 'foo')
        self.assertEqual(parsed.text, 'bar')

    def test_XmlResponse_class_malformed_response(self):
        self._mock_response.read.return_value = '<foo>'

        try:
            XmlResponse(response=self._mock_response,
                        connection=self._mock_connection)
        except MalformedResponseError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_XmlResponse_class_zero_length_body_strip(self):
        self._mock_response.read.return_value = ' '

        response = XmlResponse(response=self._mock_response,
                               connection=self._mock_connection)

        parsed = response.parse_body()
        self.assertEqual(parsed, '')

    def test_JsonResponse_class_success(self):
        self._mock_response.read.return_value = '{"foo": "bar"}'
        response = JsonResponse(response=self._mock_response,
                                connection=self._mock_connection)

        parsed = response.parse_body()
        self.assertEqual(parsed, {'foo': 'bar'})

    def test_JsonResponse_class_malformed_response(self):
        self._mock_response.read.return_value = '{"foo": "bar'

        try:
            JsonResponse(response=self._mock_response,
                         connection=self._mock_connection)
        except MalformedResponseError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_JsonResponse_class_zero_length_body_strip(self):
        self._mock_response.read.return_value = ' '

        response = JsonResponse(response=self._mock_response,
                                connection=self._mock_connection)

        parsed = response.parse_body()
        self.assertEqual(parsed, '')

    def test_deflate_encoding(self):
        original_data = 'foo bar ponies, wooo zlib'
        compressed_data = zlib.compress(b(original_data))

        self._mock_response.read.return_value = compressed_data
        self._mock_response.getheaders.return_value = \
            {'Content-Encoding': 'deflate'}

        response = Response(response=self._mock_response,
                            connection=self._mock_connection)

        body = response.parse_body()
        self.assertEqual(body, original_data)

        self._mock_response.getheaders.return_value = \
            {'Content-Encoding': 'zlib'}

        response = Response(response=self._mock_response,
                            connection=self._mock_connection)

        body = response.parse_body()
        self.assertEqual(body, original_data)

    def test_gzip_encoding(self):
        original_data = 'foo bar ponies, wooo gzip'

        if PY3:
            from io import BytesIO
            string_io = BytesIO()
        else:
            string_io = StringIO()

        stream = gzip.GzipFile(fileobj=string_io, mode='w')
        stream.write(b(original_data))
        stream.close()
        compressed_data = string_io.getvalue()

        self._mock_response.read.return_value = compressed_data
        self._mock_response.getheaders.return_value = \
            {'Content-Encoding': 'gzip'}

        response = Response(response=self._mock_response,
                            connection=self._mock_connection)

        body = response.parse_body()
        self.assertEqual(body, original_data)

        self._mock_response.getheaders.return_value = \
            {'Content-Encoding': 'x-gzip'}

        response = Response(response=self._mock_response,
                            connection=self._mock_connection)

        body = response.parse_body()
        self.assertEqual(body, original_data)


if __name__ == '__main__':
    sys.exit(unittest.main())
