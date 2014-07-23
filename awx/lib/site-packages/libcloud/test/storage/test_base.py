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
import hashlib

from mock import Mock

from libcloud.utils.py3 import StringIO
from libcloud.utils.py3 import PY3
from libcloud.utils.py3 import b

if PY3:
    from io import FileIO as file

from libcloud.storage.base import StorageDriver
from libcloud.storage.base import DEFAULT_CONTENT_TYPE

from libcloud.test import unittest
from libcloud.test import StorageMockHttp


class BaseStorageTests(unittest.TestCase):

    def setUp(self):
        self.send_called = 0
        StorageDriver.connectionCls.conn_classes = (None, StorageMockHttp)

        self.driver1 = StorageDriver('username', 'key', host='localhost')
        self.driver1.supports_chunked_encoding = True
        self.driver2 = StorageDriver('username', 'key', host='localhost')
        self.driver2.supports_chunked_encoding = False

        self.driver1.strict_mode = False
        self.driver1.strict_mode = False

    def test__upload_object_iterator_must_have_next_method(self):
        class Iterator(object):

            def next(self):
                pass

        class Iterator2(file):

            def __init__(self):
                pass

        class SomeClass(object):
            pass

        valid_iterators = [Iterator(), Iterator2(), StringIO('bar')]
        invalid_iterators = ['foobar', '', False, True, 1, object()]

        def upload_func(*args, **kwargs):
            return True, 'barfoo', 100

        kwargs = {'object_name': 'foo', 'content_type': 'foo/bar',
                  'upload_func': upload_func, 'upload_func_kwargs': {},
                  'request_path': '/', 'headers': {}}

        for value in valid_iterators:
            kwargs['iterator'] = value
            self.driver1._upload_object(**kwargs)

        for value in invalid_iterators:
            kwargs['iterator'] = value

            try:
                self.driver1._upload_object(**kwargs)
            except AttributeError:
                pass
            else:
                self.fail('Exception was not thrown')

    def test_upload_zero_bytes_long_object_via_stream(self):
        iterator = Mock()

        if PY3:
            iterator.__next__ = Mock()
            iterator.__next__.side_effect = StopIteration()
        else:
            iterator.next.side_effect = StopIteration()

        def mock_send(data):
            self.send_called += 1

        response = Mock()
        response.connection.connection.send = mock_send

        # Normal
        success, data_hash, bytes_transferred = \
            self.driver1._stream_data(response=response,
                                      iterator=iterator,
                                      chunked=False, calculate_hash=True)

        self.assertTrue(success)
        self.assertEqual(data_hash, hashlib.md5(b('')).hexdigest())
        self.assertEqual(bytes_transferred, 0)
        self.assertEqual(self.send_called, 1)

        # Chunked
        success, data_hash, bytes_transferred = \
            self.driver1._stream_data(response=response,
                                      iterator=iterator,
                                      chunked=True, calculate_hash=True)

        self.assertTrue(success)
        self.assertEqual(data_hash, hashlib.md5(b('')).hexdigest())
        self.assertEqual(bytes_transferred, 0)
        self.assertEqual(self.send_called, 5)

    def test__upload_data(self):
        def mock_send(data):
            self.send_called += 1

        response = Mock()
        response.connection.connection.send = mock_send

        data = '123456789901234567'
        success, data_hash, bytes_transferred = \
            self.driver1._upload_data(response=response, data=data,
                                      calculate_hash=True)

        self.assertTrue(success)
        self.assertEqual(data_hash, hashlib.md5(b(data)).hexdigest())
        self.assertEqual(bytes_transferred, (len(data)))
        self.assertEqual(self.send_called, 1)

    def test__get_hash_function(self):
        self.driver1.hash_type = 'md5'
        func = self.driver1._get_hash_function()
        self.assertTrue(func)

        self.driver1.hash_type = 'sha1'
        func = self.driver1._get_hash_function()
        self.assertTrue(func)

        try:
            self.driver1.hash_type = 'invalid-hash-function'
            func = self.driver1._get_hash_function()
        except RuntimeError:
            pass
        else:
            self.fail('Invalid hash type but exception was not thrown')

    def test_upload_no_content_type_supplied_or_detected(self):
        iterator = StringIO()

        upload_func = Mock()
        upload_func.return_value = True, '', 0

        # strict_mode is disabled, default content type should be used
        self.driver1.connection = Mock()

        self.driver1._upload_object(object_name='test',
                                    content_type=None,
                                    upload_func=upload_func,
                                    upload_func_kwargs={},
                                    request_path='/',
                                    iterator=iterator)

        headers = self.driver1.connection.request.call_args[-1]['headers']
        self.assertEqual(headers['Content-Type'], DEFAULT_CONTENT_TYPE)

        # strict_mode is enabled, exception should be thrown

        self.driver1.strict_mode = True
        expected_msg = ('File content-type could not be guessed and no'
                        ' content_type value is provided')
        self.assertRaisesRegexp(AttributeError, expected_msg,
                                self.driver1._upload_object,
                                object_name='test',
                                content_type=None,
                                upload_func=upload_func,
                                upload_func_kwargs={},
                                request_path='/',
                                iterator=iterator)


if __name__ == '__main__':
    sys.exit(unittest.main())
