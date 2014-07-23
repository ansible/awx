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

from __future__ import with_statement

import os
import sys
import unittest
import tempfile

from libcloud.utils.py3 import httplib
from libcloud.utils.py3 import urlparse
from libcloud.utils.py3 import parse_qs

from libcloud.common.types import InvalidCredsError
from libcloud.common.types import LibcloudError
from libcloud.storage.base import Container, Object
from libcloud.storage.types import ContainerDoesNotExistError
from libcloud.storage.types import ContainerIsNotEmptyError
from libcloud.storage.types import ContainerAlreadyExistsError
from libcloud.storage.types import InvalidContainerNameError
from libcloud.storage.types import ObjectDoesNotExistError
from libcloud.storage.types import ObjectHashMismatchError
from libcloud.storage.drivers.azure_blobs import AzureBlobsStorageDriver
from libcloud.storage.drivers.azure_blobs import AZURE_BLOCK_MAX_SIZE
from libcloud.storage.drivers.azure_blobs import AZURE_PAGE_CHUNK_SIZE
from libcloud.storage.drivers.dummy import DummyIterator

from libcloud.test import StorageMockHttp, MockRawResponse  # pylint: disable-msg=E0611
from libcloud.test import MockHttpTestCase  # pylint: disable-msg=E0611
from libcloud.test.file_fixtures import StorageFileFixtures  # pylint: disable-msg=E0611
from libcloud.test.secrets import STORAGE_AZURE_BLOBS_PARAMS


class AzureBlobsMockHttp(StorageMockHttp, MockHttpTestCase):

    fixtures = StorageFileFixtures('azure_blobs')
    base_headers = {}

    def _UNAUTHORIZED(self, method, url, body, headers):
        return (httplib.UNAUTHORIZED,
                '',
                self.base_headers,
                httplib.responses[httplib.UNAUTHORIZED])

    def _list_containers_EMPTY(self, method, url, body, headers):
        body = self.fixtures.load('list_containers_empty.xml')
        return (httplib.OK,
                body,
                self.base_headers,
                httplib.responses[httplib.OK])

    def _list_containers(self, method, url, body, headers):
        query_string = urlparse.urlsplit(url).query
        query = parse_qs(query_string)

        if 'marker' not in query:
            body = self.fixtures.load('list_containers_1.xml')
        else:
            body = self.fixtures.load('list_containers_2.xml')

        return (httplib.OK,
                body,
                self.base_headers,
                httplib.responses[httplib.OK])

    def _test_container_EMPTY(self, method, url, body, headers):
        if method == 'DELETE':
            body = ''
            return (httplib.ACCEPTED,
                    body,
                    self.base_headers,
                    httplib.responses[httplib.ACCEPTED])

        else:
            body = self.fixtures.load('list_objects_empty.xml')
            return (httplib.OK,
                    body,
                    self.base_headers,
                    httplib.responses[httplib.OK])

    def _new__container_INVALID_NAME(self, method, url, body, headers):
        return (httplib.BAD_REQUEST,
                body,
                self.base_headers,
                httplib.responses[httplib.BAD_REQUEST])

    def _test_container(self, method, url, body, headers):
        query_string = urlparse.urlsplit(url).query
        query = parse_qs(query_string)

        if 'marker' not in query:
            body = self.fixtures.load('list_objects_1.xml')
        else:
            body = self.fixtures.load('list_objects_2.xml')

        return (httplib.OK,
                body,
                self.base_headers,
                httplib.responses[httplib.OK])

    def _test_container100(self, method, url, body, headers):
        body = ''

        if method != 'HEAD':
            return (httplib.BAD_REQUEST,
                    body,
                    self.base_headers,
                    httplib.responses[httplib.BAD_REQUEST])

        return (httplib.NOT_FOUND,
                body,
                self.base_headers,
                httplib.responses[httplib.NOT_FOUND])

    def _test_container200(self, method, url, body, headers):
        body = ''

        if method != 'HEAD':
            return (httplib.BAD_REQUEST,
                    body,
                    self.base_headers,
                    httplib.responses[httplib.BAD_REQUEST])

        headers = {}

        headers['etag'] = '0x8CFB877BB56A6FB'
        headers['last-modified'] = 'Fri, 04 Jan 2013 09:48:06 GMT'
        headers['x-ms-lease-status'] = 'unlocked'
        headers['x-ms-lease-state'] = 'available'
        headers['x-ms-meta-meta1'] = 'value1'

        return (httplib.OK,
                body,
                headers,
                httplib.responses[httplib.OK])

    def _test_container200_test(self, method, url, body, headers):
        body = ''

        if method != 'HEAD':
            return (httplib.BAD_REQUEST,
                    body,
                    self.base_headers,
                    httplib.responses[httplib.BAD_REQUEST])

        headers = {}

        headers['etag'] = '0x8CFB877BB56A6FB'
        headers['last-modified'] = 'Fri, 04 Jan 2013 09:48:06 GMT'
        headers['content-length'] = 12345
        headers['content-type'] = 'application/zip'
        headers['x-ms-blob-type'] = 'Block'
        headers['x-ms-lease-status'] = 'unlocked'
        headers['x-ms-lease-state'] = 'available'
        headers['x-ms-meta-rabbits'] = 'monkeys'

        return (httplib.OK,
                body,
                headers,
                httplib.responses[httplib.OK])

    def _test2_test_list_containers(self, method, url, body, headers):
        # test_get_object
        body = self.fixtures.load('list_containers.xml')
        headers = {'content-type': 'application/zip',
                   'etag': '"e31208wqsdoj329jd"',
                   'x-amz-meta-rabbits': 'monkeys',
                   'content-length': 12345,
                   'last-modified': 'Thu, 13 Sep 2012 07:13:22 GMT'
                   }

        return (httplib.OK,
                body,
                headers,
                httplib.responses[httplib.OK])

    def _new_container_ALREADY_EXISTS(self, method, url, body, headers):
        # test_create_container
        return (httplib.CONFLICT,
                body,
                headers,
                httplib.responses[httplib.CONFLICT])

    def _new_container(self, method, url, body, headers):
        # test_create_container, test_delete_container

        headers = {}

        if method == 'PUT':
            status = httplib.CREATED

            headers['etag'] = '0x8CFB877BB56A6FB'
            headers['last-modified'] = 'Fri, 04 Jan 2013 09:48:06 GMT'
            headers['x-ms-lease-status'] = 'unlocked'
            headers['x-ms-lease-state'] = 'available'
            headers['x-ms-meta-meta1'] = 'value1'

        elif method == 'DELETE':
            status = httplib.NO_CONTENT

        return (status,
                body,
                headers,
                httplib.responses[status])

    def _new_container_DOESNT_EXIST(self, method, url, body, headers):
        # test_delete_container
        return (httplib.NOT_FOUND,
                body,
                headers,
                httplib.responses[httplib.NOT_FOUND])

    def _foo_bar_container_NOT_FOUND(self, method, url, body, headers):
        # test_delete_container_not_found
        return (httplib.NOT_FOUND,
                body,
                headers,
                httplib.responses[httplib.NOT_FOUND])

    def _foo_bar_container_foo_bar_object_NOT_FOUND(self, method, url, body,
                                                    headers):
        # test_delete_object_not_found
        return (httplib.NOT_FOUND,
                body,
                headers,
                httplib.responses[httplib.NOT_FOUND])

    def _foo_bar_container_foo_bar_object(self, method, url, body, headers):
        # test_delete_object
        return (httplib.ACCEPTED,
                body,
                headers,
                httplib.responses[httplib.ACCEPTED])

    def _foo_bar_container_foo_test_upload(self, method, url, body, headers):
        # test_upload_object_success
        body = ''
        headers = {}
        headers['etag'] = '0x8CFB877BB56A6FB'
        headers['content-md5'] = 'd4fe4c9829f7ca1cc89db7ad670d2bbd'
        return (httplib.CREATED,
                body,
                headers,
                httplib.responses[httplib.CREATED])

    def _foo_bar_container_foo_test_upload_block(self, method, url,
                                                 body, headers):
        # test_upload_object_success
        body = ''
        headers = {}
        headers['etag'] = '0x8CFB877BB56A6FB'
        return (httplib.CREATED,
                body,
                headers,
                httplib.responses[httplib.CREATED])

    def _foo_bar_container_foo_test_upload_page(self, method, url,
                                                body, headers):
        # test_upload_object_success
        body = ''
        headers = {}
        headers['etag'] = '0x8CFB877BB56A6FB'
        return (httplib.CREATED,
                body,
                headers,
                httplib.responses[httplib.CREATED])

    def _foo_bar_container_foo_test_upload_blocklist(self, method, url,
                                                     body, headers):
        # test_upload_object_success
        body = ''
        headers = {}
        headers['etag'] = '0x8CFB877BB56A6FB'
        headers['content-md5'] = 'd4fe4c9829f7ca1cc89db7ad670d2bbd'

        return (httplib.CREATED,
                body,
                headers,
                httplib.responses[httplib.CREATED])

    def _foo_bar_container_foo_test_upload_lease(self, method, url,
                                                 body, headers):
        # test_upload_object_success
        action = headers['x-ms-lease-action']
        rheaders = {'x-ms-lease-id': 'someleaseid'}
        body = ''

        if action == 'acquire':
            return (httplib.CREATED,
                    body,
                    rheaders,
                    httplib.responses[httplib.CREATED])

        else:
            if headers.get('x-ms-lease-id', None) != 'someleaseid':
                return (httplib.BAD_REQUEST,
                        body,
                        rheaders,
                        httplib.responses[httplib.BAD_REQUEST])

            return (httplib.OK,
                    body,
                    headers,
                    httplib.responses[httplib.CREATED])


class AzureBlobsMockRawResponse(MockRawResponse):

    fixtures = StorageFileFixtures('azure_blobs')

    def _foo_bar_container_foo_test_upload_INVALID_HASH(self, method, url,
                                                        body, headers):
        body = ''
        headers = {}
        headers['etag'] = '0x8CFB877BB56A6FB'
        headers['content-md5'] = 'd4fe4c9829f7ca1cc89db7ad670d2bbd'

        # test_upload_object_invalid_hash1
        return (httplib.CREATED,
                body,
                headers,
                httplib.responses[httplib.CREATED])

    def _foo_bar_container_foo_test_upload(self, method, url, body, headers):
        # test_upload_object_success
        body = ''
        headers = {}
        headers['etag'] = '0x8CFB877BB56A6FB'
        headers['content-md5'] = 'd4fe4c9829f7ca1cc89db7ad670d2bbd'
        return (httplib.CREATED,
                body,
                headers,
                httplib.responses[httplib.CREATED])

    def _foo_bar_container_foo_bar_object(self, method, url, body, headers):
        # test_upload_object_invalid_file_size
        body = self._generate_random_data(1000)
        return (httplib.OK,
                body,
                headers,
                httplib.responses[httplib.OK])

    def _foo_bar_container_foo_bar_object_INVALID_SIZE(self, method, url,
                                                       body, headers):
        # test_upload_object_invalid_file_size
        body = ''
        return (httplib.OK,
                body,
                headers,
                httplib.responses[httplib.OK])


class AzureBlobsTests(unittest.TestCase):
    driver_type = AzureBlobsStorageDriver
    driver_args = STORAGE_AZURE_BLOBS_PARAMS
    mock_response_klass = AzureBlobsMockHttp
    mock_raw_response_klass = AzureBlobsMockRawResponse

    @classmethod
    def create_driver(self):
        return self.driver_type(*self.driver_args)

    def setUp(self):
        self.driver_type.connectionCls.conn_classes = (None,
                                                       self.mock_response_klass)
        self.driver_type.connectionCls.rawResponseCls = \
            self.mock_raw_response_klass
        self.mock_response_klass.type = None
        self.mock_raw_response_klass.type = None
        self.driver = self.create_driver()

    def tearDown(self):
        self._remove_test_file()

    def _remove_test_file(self):
        file_path = os.path.abspath(__file__) + '.temp'

        try:
            os.unlink(file_path)
        except OSError:
            pass

    def test_invalid_credentials(self):
        self.mock_response_klass.type = 'UNAUTHORIZED'
        try:
            self.driver.list_containers()
        except InvalidCredsError:
            e = sys.exc_info()[1]
            self.assertEqual(True, isinstance(e, InvalidCredsError))
        else:
            self.fail('Exception was not thrown')

    def test_list_containers_empty(self):
        self.mock_response_klass.type = 'list_containers_EMPTY'
        containers = self.driver.list_containers()
        self.assertEqual(len(containers), 0)

    def test_list_containers_success(self):
        self.mock_response_klass.type = 'list_containers'
        AzureBlobsStorageDriver.RESPONSES_PER_REQUEST = 2
        containers = self.driver.list_containers()
        self.assertEqual(len(containers), 4)

        self.assertTrue('last_modified' in containers[1].extra)
        self.assertTrue('url' in containers[1].extra)
        self.assertTrue('etag' in containers[1].extra)
        self.assertTrue('lease' in containers[1].extra)
        self.assertTrue('meta_data' in containers[1].extra)

    def test_list_container_objects_empty(self):
        self.mock_response_klass.type = 'EMPTY'
        container = Container(name='test_container', extra={},
                              driver=self.driver)
        objects = self.driver.list_container_objects(container=container)
        self.assertEqual(len(objects), 0)

    def test_list_container_objects_success(self):
        self.mock_response_klass.type = None
        AzureBlobsStorageDriver.RESPONSES_PER_REQUEST = 2

        container = Container(name='test_container', extra={},
                              driver=self.driver)

        objects = self.driver.list_container_objects(container=container)
        self.assertEqual(len(objects), 4)

        obj = objects[1]
        self.assertEqual(obj.name, 'object2.txt')
        self.assertEqual(obj.hash, '0x8CFB90F1BA8CD8F')
        self.assertEqual(obj.size, 1048576)
        self.assertEqual(obj.container.name, 'test_container')
        self.assertTrue('meta1' in obj.meta_data)
        self.assertTrue('meta2' in obj.meta_data)
        self.assertTrue('last_modified' in obj.extra)
        self.assertTrue('content_type' in obj.extra)
        self.assertTrue('content_encoding' in obj.extra)
        self.assertTrue('content_language' in obj.extra)

    def test_get_container_doesnt_exist(self):
        self.mock_response_klass.type = None
        try:
            self.driver.get_container(container_name='test_container100')
        except ContainerDoesNotExistError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_get_container_success(self):
        self.mock_response_klass.type = None
        container = self.driver.get_container(
            container_name='test_container200')

        self.assertTrue(container.name, 'test_container200')
        self.assertTrue(container.extra['etag'], '0x8CFB877BB56A6FB')
        self.assertTrue(container.extra['last_modified'],
                        'Fri, 04 Jan 2013 09:48:06 GMT')
        self.assertTrue(container.extra['lease']['status'], 'unlocked')
        self.assertTrue(container.extra['lease']['state'], 'available')
        self.assertTrue(container.extra['meta_data']['meta1'], 'value1')

    def test_get_object_container_doesnt_exist(self):
        # This method makes two requests which makes mocking the response a bit
        # trickier
        self.mock_response_klass.type = None
        try:
            self.driver.get_object(container_name='test_container100',
                                   object_name='test')
        except ContainerDoesNotExistError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_get_object_success(self):
        # This method makes two requests which makes mocking the response a bit
        # trickier
        self.mock_response_klass.type = None
        obj = self.driver.get_object(container_name='test_container200',
                                     object_name='test')

        self.assertEqual(obj.name, 'test')
        self.assertEqual(obj.container.name, 'test_container200')
        self.assertEqual(obj.size, 12345)
        self.assertEqual(obj.hash, '0x8CFB877BB56A6FB')
        self.assertEqual(obj.extra['last_modified'],
                         'Fri, 04 Jan 2013 09:48:06 GMT')
        self.assertEqual(obj.extra['content_type'], 'application/zip')
        self.assertEqual(obj.meta_data['rabbits'], 'monkeys')

    def test_create_container_invalid_name(self):
        # invalid container name
        self.mock_response_klass.type = 'INVALID_NAME'
        try:
            self.driver.create_container(container_name='new--container')
        except InvalidContainerNameError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_create_container_already_exists(self):
        # container with this name already exists
        self.mock_response_klass.type = 'ALREADY_EXISTS'
        try:
            self.driver.create_container(container_name='new-container')
        except ContainerAlreadyExistsError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_create_container_success(self):
        # success
        self.mock_response_klass.type = None
        name = 'new-container'
        container = self.driver.create_container(container_name=name)
        self.assertEqual(container.name, name)

    def test_delete_container_doesnt_exist(self):
        container = Container(name='new_container', extra=None,
                              driver=self.driver)
        self.mock_response_klass.type = 'DOESNT_EXIST'
        try:
            self.driver.delete_container(container=container)
        except ContainerDoesNotExistError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_delete_container_not_empty(self):
        self.mock_response_klass.type = None
        AzureBlobsStorageDriver.RESPONSES_PER_REQUEST = 2

        container = Container(name='test_container', extra={},
                              driver=self.driver)

        try:
            self.driver.delete_container(container=container)
        except ContainerIsNotEmptyError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_delete_container_success(self):
        self.mock_response_klass.type = 'EMPTY'
        AzureBlobsStorageDriver.RESPONSES_PER_REQUEST = 2

        container = Container(name='test_container', extra={},
                              driver=self.driver)

        self.assertTrue(self.driver.delete_container(container=container))

    def test_delete_container_not_found(self):
        self.mock_response_klass.type = 'NOT_FOUND'
        container = Container(name='foo_bar_container', extra={},
                              driver=self.driver)
        try:
            self.driver.delete_container(container=container)
        except ContainerDoesNotExistError:
            pass
        else:
            self.fail('Container does not exist but an exception was not' +
                      'thrown')

    def test_download_object_success(self):
        container = Container(name='foo_bar_container', extra={},
                              driver=self.driver)
        obj = Object(name='foo_bar_object', size=1000, hash=None, extra={},
                     container=container, meta_data=None,
                     driver=self.driver_type)
        destination_path = os.path.abspath(__file__) + '.temp'
        result = self.driver.download_object(obj=obj,
                                             destination_path=destination_path,
                                             overwrite_existing=False,
                                             delete_on_failure=True)
        self.assertTrue(result)

    def test_download_object_invalid_file_size(self):
        self.mock_raw_response_klass.type = 'INVALID_SIZE'
        container = Container(name='foo_bar_container', extra={},
                              driver=self.driver)
        obj = Object(name='foo_bar_object', size=1000, hash=None, extra={},
                     container=container, meta_data=None,
                     driver=self.driver_type)
        destination_path = os.path.abspath(__file__) + '.temp'
        result = self.driver.download_object(obj=obj,
                                             destination_path=destination_path,
                                             overwrite_existing=False,
                                             delete_on_failure=True)
        self.assertFalse(result)

    def test_download_object_invalid_file_already_exists(self):
        self.mock_raw_response_klass.type = 'INVALID_SIZE'
        container = Container(name='foo_bar_container', extra={},
                              driver=self.driver)
        obj = Object(name='foo_bar_object', size=1000, hash=None, extra={},
                     container=container, meta_data=None,
                     driver=self.driver_type)
        destination_path = os.path.abspath(__file__)
        try:
            self.driver.download_object(obj=obj,
                                        destination_path=destination_path,
                                        overwrite_existing=False,
                                        delete_on_failure=True)
        except LibcloudError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_download_object_as_stream_success(self):
        container = Container(name='foo_bar_container', extra={},
                              driver=self.driver)

        obj = Object(name='foo_bar_object', size=1000, hash=None, extra={},
                     container=container, meta_data=None,
                     driver=self.driver_type)

        stream = self.driver.download_object_as_stream(obj=obj,
                                                       chunk_size=None)
        self.assertTrue(hasattr(stream, '__iter__'))

    def test_upload_object_invalid_ex_blob_type(self):
        # Invalid hash is detected on the amazon side and BAD_REQUEST is
        # returned
        file_path = os.path.abspath(__file__)
        container = Container(name='foo_bar_container', extra={},
                              driver=self.driver)
        object_name = 'foo_test_upload'
        try:
            self.driver.upload_object(file_path=file_path, container=container,
                                      object_name=object_name,
                                      verify_hash=True,
                                      ex_blob_type='invalid-blob')
        except LibcloudError:
            e = sys.exc_info()[1]
            self.assertTrue(str(e).lower().find('invalid blob type') != -1)
        else:
            self.fail('Exception was not thrown')

    def test_upload_object_invalid_md5(self):
        # Invalid md5 is returned by azure
        self.mock_raw_response_klass.type = 'INVALID_HASH'

        container = Container(name='foo_bar_container', extra={},
                              driver=self.driver)
        object_name = 'foo_test_upload'
        file_path = os.path.abspath(__file__)
        try:
            self.driver.upload_object(file_path=file_path, container=container,
                                      object_name=object_name,
                                      verify_hash=True)
        except ObjectHashMismatchError:
            pass
        else:
            self.fail(
                'Invalid hash was returned but an exception was not thrown')

    def test_upload_small_block_object_success(self):
        file_path = os.path.abspath(__file__)
        file_size = os.stat(file_path).st_size

        container = Container(name='foo_bar_container', extra={},
                              driver=self.driver)
        object_name = 'foo_test_upload'
        extra = {'meta_data': {'some-value': 'foobar'}}
        obj = self.driver.upload_object(file_path=file_path,
                                        container=container,
                                        object_name=object_name,
                                        extra=extra,
                                        verify_hash=False,
                                        ex_blob_type='BlockBlob')

        self.assertEqual(obj.name, 'foo_test_upload')
        self.assertEqual(obj.size, file_size)
        self.assertTrue('some-value' in obj.meta_data)

    def test_upload_big_block_object_success(self):
        file_path = tempfile.mktemp(suffix='.jpg')
        file_size = AZURE_BLOCK_MAX_SIZE + 1

        with open(file_path, 'w') as file_hdl:
            file_hdl.write('0' * file_size)

        container = Container(name='foo_bar_container', extra={},
                              driver=self.driver)
        object_name = 'foo_test_upload'
        extra = {'meta_data': {'some-value': 'foobar'}}
        obj = self.driver.upload_object(file_path=file_path,
                                        container=container,
                                        object_name=object_name,
                                        extra=extra,
                                        verify_hash=False,
                                        ex_blob_type='BlockBlob')

        self.assertEqual(obj.name, 'foo_test_upload')
        self.assertEqual(obj.size, file_size)
        self.assertTrue('some-value' in obj.meta_data)

        os.remove(file_path)

    def test_upload_page_object_success(self):
        self.mock_response_klass.use_param = None
        file_path = tempfile.mktemp(suffix='.jpg')
        file_size = AZURE_PAGE_CHUNK_SIZE * 4

        with open(file_path, 'w') as file_hdl:
            file_hdl.write('0' * file_size)

        container = Container(name='foo_bar_container', extra={},
                              driver=self.driver)
        object_name = 'foo_test_upload'
        extra = {'meta_data': {'some-value': 'foobar'}}
        obj = self.driver.upload_object(file_path=file_path,
                                        container=container,
                                        object_name=object_name,
                                        extra=extra,
                                        verify_hash=False,
                                        ex_blob_type='PageBlob')

        self.assertEqual(obj.name, 'foo_test_upload')
        self.assertEqual(obj.size, file_size)
        self.assertTrue('some-value' in obj.meta_data)

        os.remove(file_path)

    def test_upload_page_object_failure(self):
        file_path = tempfile.mktemp(suffix='.jpg')
        file_size = AZURE_PAGE_CHUNK_SIZE * 2 + 1

        with open(file_path, 'w') as file_hdl:
            file_hdl.write('0' * file_size)

        container = Container(name='foo_bar_container', extra={},
                              driver=self.driver)
        object_name = 'foo_test_upload'
        extra = {'meta_data': {'some-value': 'foobar'}}

        try:
            self.driver.upload_object(file_path=file_path,
                                      container=container,
                                      object_name=object_name,
                                      extra=extra,
                                      verify_hash=False,
                                      ex_blob_type='PageBlob')
        except LibcloudError:
            e = sys.exc_info()[1]
            self.assertTrue(str(e).lower().find('not aligned') != -1)

        os.remove(file_path)

    def test_upload_small_block_object_success_with_lease(self):
        self.mock_response_klass.use_param = 'comp'
        file_path = os.path.abspath(__file__)
        file_size = os.stat(file_path).st_size

        container = Container(name='foo_bar_container', extra={},
                              driver=self.driver)
        object_name = 'foo_test_upload'
        extra = {'meta_data': {'some-value': 'foobar'}}
        obj = self.driver.upload_object(file_path=file_path,
                                        container=container,
                                        object_name=object_name,
                                        extra=extra,
                                        verify_hash=False,
                                        ex_blob_type='BlockBlob',
                                        ex_use_lease=True)

        self.assertEqual(obj.name, 'foo_test_upload')
        self.assertEqual(obj.size, file_size)
        self.assertTrue('some-value' in obj.meta_data)
        self.mock_response_klass.use_param = None

    def test_upload_big_block_object_success_with_lease(self):
        self.mock_response_klass.use_param = 'comp'
        file_path = tempfile.mktemp(suffix='.jpg')
        file_size = AZURE_BLOCK_MAX_SIZE * 2

        with open(file_path, 'w') as file_hdl:
            file_hdl.write('0' * file_size)

        container = Container(name='foo_bar_container', extra={},
                              driver=self.driver)
        object_name = 'foo_test_upload'
        extra = {'meta_data': {'some-value': 'foobar'}}
        obj = self.driver.upload_object(file_path=file_path,
                                        container=container,
                                        object_name=object_name,
                                        extra=extra,
                                        verify_hash=False,
                                        ex_blob_type='BlockBlob',
                                        ex_use_lease=False)

        self.assertEqual(obj.name, 'foo_test_upload')
        self.assertEqual(obj.size, file_size)
        self.assertTrue('some-value' in obj.meta_data)

        os.remove(file_path)
        self.mock_response_klass.use_param = None

    def test_upload_page_object_success_with_lease(self):
        self.mock_response_klass.use_param = 'comp'
        file_path = tempfile.mktemp(suffix='.jpg')
        file_size = AZURE_PAGE_CHUNK_SIZE * 4

        with open(file_path, 'w') as file_hdl:
            file_hdl.write('0' * file_size)

        container = Container(name='foo_bar_container', extra={},
                              driver=self.driver)
        object_name = 'foo_test_upload'
        extra = {'meta_data': {'some-value': 'foobar'}}
        obj = self.driver.upload_object(file_path=file_path,
                                        container=container,
                                        object_name=object_name,
                                        extra=extra,
                                        verify_hash=False,
                                        ex_blob_type='PageBlob',
                                        ex_use_lease=True)

        self.assertEqual(obj.name, 'foo_test_upload')
        self.assertEqual(obj.size, file_size)
        self.assertTrue('some-value' in obj.meta_data)

        os.remove(file_path)
        self.mock_response_klass.use_param = None

    def test_upload_blob_object_via_stream(self):
        self.mock_response_klass.use_param = 'comp'
        container = Container(name='foo_bar_container', extra={},
                              driver=self.driver)

        object_name = 'foo_test_upload'
        iterator = DummyIterator(data=['2', '3', '5'])
        extra = {'content_type': 'text/plain'}
        obj = self.driver.upload_object_via_stream(container=container,
                                                   object_name=object_name,
                                                   iterator=iterator,
                                                   extra=extra,
                                                   ex_blob_type='BlockBlob')

        self.assertEqual(obj.name, object_name)
        self.assertEqual(obj.size, 3)
        self.mock_response_klass.use_param = None

    def test_upload_blob_object_via_stream_with_lease(self):
        self.mock_response_klass.use_param = 'comp'
        container = Container(name='foo_bar_container', extra={},
                              driver=self.driver)

        object_name = 'foo_test_upload'
        iterator = DummyIterator(data=['2', '3', '5'])
        extra = {'content_type': 'text/plain'}
        obj = self.driver.upload_object_via_stream(container=container,
                                                   object_name=object_name,
                                                   iterator=iterator,
                                                   extra=extra,
                                                   ex_blob_type='BlockBlob',
                                                   ex_use_lease=True)

        self.assertEqual(obj.name, object_name)
        self.assertEqual(obj.size, 3)
        self.mock_response_klass.use_param = None

    def test_upload_page_object_via_stream(self):
        self.mock_response_klass.use_param = 'comp'
        container = Container(name='foo_bar_container', extra={},
                              driver=self.driver)

        object_name = 'foo_test_upload'
        blob_size = AZURE_PAGE_CHUNK_SIZE
        iterator = DummyIterator(data=['1'] * blob_size)
        extra = {'content_type': 'text/plain'}
        obj = self.driver.upload_object_via_stream(container=container,
                                                   object_name=object_name,
                                                   iterator=iterator,
                                                   extra=extra,
                                                   ex_blob_type='PageBlob',
                                                   ex_page_blob_size=blob_size)

        self.assertEqual(obj.name, object_name)
        self.assertEqual(obj.size, blob_size)
        self.mock_response_klass.use_param = None

    def test_upload_page_object_via_stream_with_lease(self):
        self.mock_response_klass.use_param = 'comp'
        container = Container(name='foo_bar_container', extra={},
                              driver=self.driver)

        object_name = 'foo_test_upload'
        blob_size = AZURE_PAGE_CHUNK_SIZE
        iterator = DummyIterator(data=['1'] * blob_size)
        extra = {'content_type': 'text/plain'}
        obj = self.driver.upload_object_via_stream(container=container,
                                                   object_name=object_name,
                                                   iterator=iterator,
                                                   extra=extra,
                                                   ex_blob_type='PageBlob',
                                                   ex_page_blob_size=blob_size,
                                                   ex_use_lease=True)

        self.assertEqual(obj.name, object_name)
        self.assertEqual(obj.size, blob_size)

    def test_delete_object_not_found(self):
        self.mock_response_klass.type = 'NOT_FOUND'
        container = Container(name='foo_bar_container', extra={},
                              driver=self.driver)
        obj = Object(name='foo_bar_object', size=1234, hash=None, extra=None,
                     meta_data=None, container=container, driver=self.driver)
        try:
            self.driver.delete_object(obj=obj)
        except ObjectDoesNotExistError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_delete_object_success(self):
        container = Container(name='foo_bar_container', extra={},
                              driver=self.driver)
        obj = Object(name='foo_bar_object', size=1234, hash=None, extra=None,
                     meta_data=None, container=container, driver=self.driver)

        result = self.driver.delete_object(obj=obj)
        self.assertTrue(result)

    def test_storage_driver_host(self):
        # Non regression tests for issue LIBCLOUD-399 dealing with the bad
        # management of the connectionCls.host class attribute
        driver1 = self.driver_type('fakeaccount1', 'deadbeafcafebabe==')
        driver2 = self.driver_type('fakeaccount2', 'deadbeafcafebabe==')
        driver3 = self.driver_type('fakeaccount3', 'deadbeafcafebabe==',
                                   host='test.foo.bar.com')

        host1 = driver1.connection.host
        host2 = driver2.connection.host
        host3 = driver3.connection.host

        self.assertEquals(host1, 'fakeaccount1.blob.core.windows.net')
        self.assertEquals(host2, 'fakeaccount2.blob.core.windows.net')
        self.assertEquals(host3, 'test.foo.bar.com')


if __name__ == '__main__':
    sys.exit(unittest.main())
