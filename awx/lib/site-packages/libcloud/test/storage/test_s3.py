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

import os
import sys
import unittest

try:
    from lxml import etree as ET
except ImportError:
    from xml.etree import ElementTree as ET

from libcloud.utils.py3 import httplib
from libcloud.utils.py3 import urlparse
from libcloud.utils.py3 import parse_qs

from libcloud.common.types import InvalidCredsError
from libcloud.common.types import LibcloudError, MalformedResponseError
from libcloud.storage.base import Container, Object
from libcloud.storage.types import ContainerDoesNotExistError
from libcloud.storage.types import ContainerIsNotEmptyError
from libcloud.storage.types import InvalidContainerNameError
from libcloud.storage.types import ObjectDoesNotExistError
from libcloud.storage.types import ObjectHashMismatchError
from libcloud.storage.drivers.s3 import S3StorageDriver, S3USWestStorageDriver
from libcloud.storage.drivers.s3 import S3EUWestStorageDriver
from libcloud.storage.drivers.s3 import S3APSEStorageDriver
from libcloud.storage.drivers.s3 import S3APNEStorageDriver
from libcloud.storage.drivers.s3 import CHUNK_SIZE
from libcloud.storage.drivers.dummy import DummyIterator

from libcloud.test import StorageMockHttp, MockRawResponse  # pylint: disable-msg=E0611
from libcloud.test import MockHttpTestCase  # pylint: disable-msg=E0611
from libcloud.test.file_fixtures import StorageFileFixtures  # pylint: disable-msg=E0611
from libcloud.test.secrets import STORAGE_S3_PARAMS


class S3MockHttp(StorageMockHttp, MockHttpTestCase):

    fixtures = StorageFileFixtures('s3')
    base_headers = {}

    def _UNAUTHORIZED(self, method, url, body, headers):
        return (httplib.UNAUTHORIZED,
                '',
                self.base_headers,
                httplib.responses[httplib.OK])

    def _DIFFERENT_REGION(self, method, url, body, headers):
        return (httplib.MOVED_PERMANENTLY,
                '',
                self.base_headers,
                httplib.responses[httplib.OK])

    def _list_containers_EMPTY(self, method, url, body, headers):
        body = self.fixtures.load('list_containers_empty.xml')
        return (httplib.OK,
                body,
                self.base_headers,
                httplib.responses[httplib.OK])

    def _list_containers_TOKEN(self, method, url, body, headers):
        self.assertEqual(headers['x-amz-security-token'], 'asdf')
        body = self.fixtures.load('list_containers_empty.xml')
        return (httplib.OK,
                body,
                self.base_headers,
                httplib.responses[httplib.OK])

    def _list_containers(self, method, url, body, headers):
        body = self.fixtures.load('list_containers.xml')
        return (httplib.OK,
                body,
                self.base_headers,
                httplib.responses[httplib.OK])

    def _test_container_EMPTY(self, method, url, body, headers):
        body = self.fixtures.load('list_container_objects_empty.xml')
        return (httplib.OK,
                body,
                self.base_headers,
                httplib.responses[httplib.OK])

    def _test_container(self, method, url, body, headers):
        body = self.fixtures.load('list_container_objects.xml')
        return (httplib.OK,
                body,
                self.base_headers,
                httplib.responses[httplib.OK])

    def _test_container_ITERATOR(self, method, url, body, headers):
        if url.find('3.zip') == -1:
            # First part of the response (first 3 objects)
            file_name = 'list_container_objects_not_exhausted1.xml'
        else:
            file_name = 'list_container_objects_not_exhausted2.xml'

        body = self.fixtures.load(file_name)
        return (httplib.OK,
                body,
                self.base_headers,
                httplib.responses[httplib.OK])

    def _test2_get_object(self, method, url, body, headers):
        body = self.fixtures.load('list_container_objects.xml')
        return (httplib.OK,
                body,
                self.base_headers,
                httplib.responses[httplib.OK])

    def _test2_test_get_object(self, method, url, body, headers):
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

    def _new_container_INVALID_NAME(self, method, url, body, headers):
        # test_create_container
        return (httplib.BAD_REQUEST,
                body,
                headers,
                httplib.responses[httplib.OK])

    def _new_container_ALREADY_EXISTS(self, method, url, body, headers):
        # test_create_container
        return (httplib.CONFLICT,
                body,
                headers,
                httplib.responses[httplib.OK])

    def _new_container(self, method, url, body, headers):
        # test_create_container, test_delete_container

        if method == 'PUT':
            status = httplib.OK
        elif method == 'DELETE':
            status = httplib.NO_CONTENT

        return (status,
                body,
                headers,
                httplib.responses[httplib.OK])

    def _new_container_DOESNT_EXIST(self, method, url, body, headers):
        # test_delete_container
        return (httplib.NOT_FOUND,
                body,
                headers,
                httplib.responses[httplib.OK])

    def _new_container_NOT_EMPTY(self, method, url, body, headers):
        # test_delete_container
        return (httplib.CONFLICT,
                body,
                headers,
                httplib.responses[httplib.OK])

    def _test1_get_container(self, method, url, body, headers):
        body = self.fixtures.load('list_container_objects.xml')
        return (httplib.OK,
                body,
                self.base_headers,
                httplib.responses[httplib.OK])

    def _container1_get_container(self, method, url, body, headers):
        return (httplib.NOT_FOUND,
                '',
                self.base_headers,
                httplib.responses[httplib.NOT_FOUND])

    def _test_inexistent_get_object(self, method, url, body, headers):
        return (httplib.NOT_FOUND,
                '',
                self.base_headers,
                httplib.responses[httplib.NOT_FOUND])

    def _foo_bar_container(self, method, url, body, headers):
        # test_delete_container
        return (httplib.NO_CONTENT,
                body,
                headers,
                httplib.responses[httplib.OK])

    def _foo_bar_container_NOT_FOUND(self, method, url, body, headers):
        # test_delete_container_not_found
        return (httplib.NOT_FOUND,
                body,
                headers,
                httplib.responses[httplib.OK])

    def _foo_bar_container_foo_bar_object_NOT_FOUND(self, method, url, body,
                                                    headers):
        # test_delete_object_not_found
        return (httplib.NOT_FOUND,
                body,
                headers,
                httplib.responses[httplib.OK])

    def _foo_bar_container_foo_bar_object(self, method, url, body, headers):
        # test_delete_object
        return (httplib.NO_CONTENT,
                body,
                headers,
                httplib.responses[httplib.OK])

    def _foo_bar_container_foo_test_stream_data(self, method, url, body,
                                                headers):
        # test_upload_object_via_stream
        body = ''
        headers = {'etag': '"0cc175b9c0f1b6a831c399e269772661"'}
        return (httplib.OK,
                body,
                headers,
                httplib.responses[httplib.OK])

    def _foo_bar_container_foo_test_stream_data_MULTIPART(self, method, url,
                                                          body, headers):
        headers = {'etag': '"0cc175b9c0f1b6a831c399e269772661"'}
        TEST_ID = 'VXBsb2FkIElEIGZvciA2aWWpbmcncyBteS1tb3ZpZS5tMnRzIHVwbG9hZA'

        query_string = urlparse.urlsplit(url).query
        query = parse_qs(query_string)

        if not query.get('uploadId', False):
            self.fail('Request doesnt contain uploadId query parameter')

        upload_id = query['uploadId'][0]
        if upload_id != TEST_ID:
            self.fail('first uploadId doesnt match TEST_ID')

        if method == 'PUT':
            # PUT is used for uploading the part. part number is mandatory
            if not query.get('partNumber', False):
                self.fail('Request is missing partNumber query parameter')

            body = ''
            return (httplib.OK,
                    body,
                    headers,
                    httplib.responses[httplib.OK])

        elif method == 'DELETE':
            # DELETE is done for aborting the upload
            body = ''
            return (httplib.NO_CONTENT,
                    body,
                    headers,
                    httplib.responses[httplib.NO_CONTENT])

        else:
            # POST is done for committing the upload. Parse the XML and
            # check if the commit is proper (TODO: XML Schema based check?)
            commit = ET.fromstring(body)
            count = 0

            for part in commit.findall('Part'):
                count += 1
                part_no = part.find('PartNumber').text
                etag = part.find('ETag').text

                self.assertEqual(part_no, str(count))
                self.assertEqual(etag, headers['etag'])

            # Make sure that manifest contains at least one part
            self.assertTrue(count >= 1)

            body = self.fixtures.load('complete_multipart.xml')
            return (httplib.OK,
                    body,
                    headers,
                    httplib.responses[httplib.OK])

    def _foo_bar_container_LIST_MULTIPART(self, method, url, body, headers):
        query_string = urlparse.urlsplit(url).query
        query = parse_qs(query_string)

        if 'key-marker' not in query:
            body = self.fixtures.load('list_multipart_1.xml')
        else:
            body = self.fixtures.load('list_multipart_2.xml')

        return (httplib.OK,
                body,
                headers,
                httplib.responses[httplib.OK])

    def _foo_bar_container_my_divisor_LIST_MULTIPART(self, method, url,
                                                     body, headers):
        body = ''
        return (httplib.NO_CONTENT,
                body,
                headers,
                httplib.responses[httplib.NO_CONTENT])

    def _foo_bar_container_my_movie_m2ts_LIST_MULTIPART(self, method, url,
                                                        body, headers):
        body = ''
        return (httplib.NO_CONTENT,
                body,
                headers,
                httplib.responses[httplib.NO_CONTENT])


class S3MockRawResponse(MockRawResponse):

    fixtures = StorageFileFixtures('s3')

    def parse_body(self):
        if len(self.body) == 0 and not self.parse_zero_length_body:
            return self.body

        try:
            body = ET.XML(self.body)
        except:
            raise MalformedResponseError("Failed to parse XML",
                                         body=self.body,
                                         driver=self.connection.driver)
        return body

    def _foo_bar_container_foo_bar_object(self, method, url, body, headers):
        # test_download_object_success
        body = self._generate_random_data(1000)
        return (httplib.OK,
                body,
                headers,
                httplib.responses[httplib.OK])

    def _foo_bar_container_foo_test_upload_INVALID_HASH1(self, method, url,
                                                         body, headers):
        body = ''
        headers = {}
        headers['etag'] = '"foobar"'
        # test_upload_object_invalid_hash1
        return (httplib.OK,
                body,
                headers,
                httplib.responses[httplib.OK])

    def _foo_bar_container_foo_test_upload_INVALID_HASH2(self, method, url,
                                                         body, headers):
        # test_upload_object_invalid_hash2
        body = ''
        headers = {'etag': '"hash343hhash89h932439jsaa89"'}
        return (httplib.OK,
                body,
                headers,
                httplib.responses[httplib.OK])

    def _foo_bar_container_foo_test_upload(self, method, url, body, headers):
        # test_upload_object_success
        body = ''
        headers = {'etag': '"0cc175b9c0f1b6a831c399e269772661"'}
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

    def _foo_bar_container_foo_test_stream_data(self, method, url, body,
                                                headers):
        # test_upload_object_via_stream
        body = ''
        headers = {'etag': '"0cc175b9c0f1b6a831c399e269772661"'}
        return (httplib.OK,
                body,
                headers,
                httplib.responses[httplib.OK])

    def _foo_bar_container_foo_test_stream_data_MULTIPART(self, method, url,
                                                          body, headers):
        headers = {}
        # POST is done for initiating multipart upload
        if method == 'POST':
            body = self.fixtures.load('initiate_multipart.xml')
            return (httplib.OK,
                    body,
                    headers,
                    httplib.responses[httplib.OK])
        else:
            body = ''
            return (httplib.BAD_REQUEST,
                    body,
                    headers,
                    httplib.responses[httplib.BAD_REQUEST])


class S3Tests(unittest.TestCase):
    driver_type = S3StorageDriver
    driver_args = STORAGE_S3_PARAMS
    mock_response_klass = S3MockHttp
    mock_raw_response_klass = S3MockRawResponse

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

    def test_token(self):
        self.mock_response_klass.type = 'list_containers_TOKEN'
        self.driver = self.driver_type(*self.driver_args, token='asdf')
        self.driver.list_containers()

    def test_bucket_is_located_in_different_region(self):
        self.mock_response_klass.type = 'DIFFERENT_REGION'
        try:
            self.driver.list_containers()
        except LibcloudError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_list_containers_empty(self):
        self.mock_response_klass.type = 'list_containers_EMPTY'
        containers = self.driver.list_containers()
        self.assertEqual(len(containers), 0)

    def test_list_containers_success(self):
        self.mock_response_klass.type = 'list_containers'
        containers = self.driver.list_containers()
        self.assertEqual(len(containers), 2)

        self.assertTrue('creation_date' in containers[1].extra)

    def test_list_container_objects_empty(self):
        self.mock_response_klass.type = 'EMPTY'
        container = Container(name='test_container', extra={},
                              driver=self.driver)
        objects = self.driver.list_container_objects(container=container)
        self.assertEqual(len(objects), 0)

    def test_list_container_objects_success(self):
        self.mock_response_klass.type = None
        container = Container(name='test_container', extra={},
                              driver=self.driver)
        objects = self.driver.list_container_objects(container=container)
        self.assertEqual(len(objects), 1)

        obj = [o for o in objects if o.name == '1.zip'][0]
        self.assertEqual(obj.hash, '4397da7a7649e8085de9916c240e8166')
        self.assertEqual(obj.size, 1234567)
        self.assertEqual(obj.container.name, 'test_container')
        self.assertEqual(
            obj.extra['last_modified'], '2011-04-09T19:05:18.000Z')
        self.assertTrue('owner' in obj.meta_data)

    def test_list_container_objects_iterator_has_more(self):
        self.mock_response_klass.type = 'ITERATOR'
        container = Container(name='test_container', extra={},
                              driver=self.driver)
        objects = self.driver.list_container_objects(container=container)

        obj = [o for o in objects if o.name == '1.zip'][0]
        self.assertEqual(obj.hash, '4397da7a7649e8085de9916c240e8166')
        self.assertEqual(obj.size, 1234567)
        self.assertEqual(obj.container.name, 'test_container')

        self.assertTrue(obj in objects)
        self.assertEqual(len(objects), 5)

    def test_list_container_objects_with_prefix(self):
        self.mock_response_klass.type = None
        container = Container(name='test_container', extra={},
                              driver=self.driver)
        objects = self.driver.list_container_objects(container=container,
                                                     ex_prefix='test_prefix')
        self.assertEqual(len(objects), 1)

        obj = [o for o in objects if o.name == '1.zip'][0]
        self.assertEqual(obj.hash, '4397da7a7649e8085de9916c240e8166')
        self.assertEqual(obj.size, 1234567)
        self.assertEqual(obj.container.name, 'test_container')
        self.assertTrue('owner' in obj.meta_data)

    def test_get_container_doesnt_exist(self):
        self.mock_response_klass.type = 'get_container'
        try:
            self.driver.get_container(container_name='container1')
        except ContainerDoesNotExistError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_get_container_success(self):
        self.mock_response_klass.type = 'get_container'
        container = self.driver.get_container(container_name='test1')
        self.assertTrue(container.name, 'test1')

    def test_get_object_container_doesnt_exist(self):
        # This method makes two requests which makes mocking the response a bit
        # trickier
        self.mock_response_klass.type = 'get_object'
        try:
            self.driver.get_object(container_name='test-inexistent',
                                   object_name='test')
        except ContainerDoesNotExistError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_get_object_success(self):
        # This method makes two requests which makes mocking the response a bit
        # trickier
        self.mock_response_klass.type = 'get_object'
        obj = self.driver.get_object(container_name='test2',
                                     object_name='test')

        self.assertEqual(obj.name, 'test')
        self.assertEqual(obj.container.name, 'test2')
        self.assertEqual(obj.size, 12345)
        self.assertEqual(obj.hash, 'e31208wqsdoj329jd')
        self.assertEqual(obj.extra['last_modified'],
                         'Thu, 13 Sep 2012 07:13:22 GMT')
        self.assertEqual(obj.extra['content_type'], 'application/zip')
        self.assertEqual(obj.meta_data['rabbits'], 'monkeys')

    def test_create_container_invalid_name(self):
        # invalid container name
        self.mock_response_klass.type = 'INVALID_NAME'
        try:
            self.driver.create_container(container_name='new_container')
        except InvalidContainerNameError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_create_container_already_exists(self):
        # container with this name already exists
        self.mock_response_klass.type = 'ALREADY_EXISTS'
        try:
            self.driver.create_container(container_name='new-container')
        except InvalidContainerNameError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_create_container_success(self):
        # success
        self.mock_response_klass.type = None
        name = 'new_container'
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
        container = Container(name='new_container', extra=None,
                              driver=self.driver)
        self.mock_response_klass.type = 'NOT_EMPTY'
        try:
            self.driver.delete_container(container=container)
        except ContainerIsNotEmptyError:
            pass
        else:
            self.fail('Exception was not thrown')

        # success
        self.mock_response_klass.type = None
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

    def test_delete_container_success(self):
        self.mock_response_klass.type = None
        container = Container(name='new_container', extra=None,
                              driver=self.driver)
        self.assertTrue(self.driver.delete_container(container=container))

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

    def test_upload_object_invalid_ex_storage_class(self):
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
                                      ex_storage_class='invalid-class')
        except ValueError:
            e = sys.exc_info()[1]
            self.assertTrue(str(e).lower().find('invalid storage class') != -1)
        else:
            self.fail('Exception was not thrown')

    def test_upload_object_invalid_hash1(self):
        # Invalid hash is detected on the amazon side and BAD_REQUEST is
        # returned
        def upload_file(self, response, file_path, chunked=False,
                        calculate_hash=True):
            return True, 'hash343hhash89h932439jsaa89', 1000

        self.mock_raw_response_klass.type = 'INVALID_HASH1'

        old_func = self.driver_type._upload_file
        self.driver_type._upload_file = upload_file
        file_path = os.path.abspath(__file__)
        container = Container(name='foo_bar_container', extra={},
                              driver=self.driver)
        object_name = 'foo_test_upload'
        try:
            self.driver.upload_object(file_path=file_path, container=container,
                                      object_name=object_name,
                                      verify_hash=True)
        except ObjectHashMismatchError:
            pass
        else:
            self.fail(
                'Invalid hash was returned but an exception was not thrown')
        finally:
            self.driver_type._upload_file = old_func

    def test_upload_object_invalid_hash2(self):
        # Invalid hash is detected when comparing hash provided in the response
        # ETag header
        def upload_file(self, response, file_path, chunked=False,
                        calculate_hash=True):
            return True, '0cc175b9c0f1b6a831c399e269772661', 1000

        self.mock_raw_response_klass.type = 'INVALID_HASH2'

        old_func = self.driver_type._upload_file
        self.driver_type._upload_file = upload_file
        file_path = os.path.abspath(__file__)
        container = Container(name='foo_bar_container', extra={},
                              driver=self.driver)
        object_name = 'foo_test_upload'
        try:
            self.driver.upload_object(file_path=file_path, container=container,
                                      object_name=object_name,
                                      verify_hash=True)
        except ObjectHashMismatchError:
            pass
        else:
            self.fail(
                'Invalid hash was returned but an exception was not thrown')
        finally:
            self.driver_type._upload_file = old_func

    def test_upload_object_success(self):
        def upload_file(self, response, file_path, chunked=False,
                        calculate_hash=True):
            return True, '0cc175b9c0f1b6a831c399e269772661', 1000

        old_func = self.driver_type._upload_file
        self.driver_type._upload_file = upload_file
        file_path = os.path.abspath(__file__)
        container = Container(name='foo_bar_container', extra={},
                              driver=self.driver)
        object_name = 'foo_test_upload'
        extra = {'meta_data': {'some-value': 'foobar'}}
        obj = self.driver.upload_object(file_path=file_path,
                                        container=container,
                                        object_name=object_name,
                                        extra=extra,
                                        verify_hash=True)
        self.assertEqual(obj.name, 'foo_test_upload')
        self.assertEqual(obj.size, 1000)
        self.assertTrue('some-value' in obj.meta_data)
        self.driver_type._upload_file = old_func

    def test_upload_object_with_acl(self):
        def upload_file(self, response, file_path, chunked=False,
                        calculate_hash=True):
            return True, '0cc175b9c0f1b6a831c399e269772661', 1000

        old_func = self.driver_type._upload_file
        self.driver_type._upload_file = upload_file
        file_path = os.path.abspath(__file__)
        container = Container(name='foo_bar_container', extra={},
                              driver=self.driver)
        object_name = 'foo_test_upload'
        extra = {'acl': 'public-read'}
        obj = self.driver.upload_object(file_path=file_path,
                                        container=container,
                                        object_name=object_name,
                                        extra=extra,
                                        verify_hash=True)
        self.assertEqual(obj.name, 'foo_test_upload')
        self.assertEqual(obj.size, 1000)
        self.assertEqual(obj.extra['acl'], 'public-read')
        self.driver_type._upload_file = old_func

    def test_upload_empty_object_via_stream(self):
        if self.driver.supports_s3_multipart_upload:
            self.mock_raw_response_klass.type = 'MULTIPART'
            self.mock_response_klass.type = 'MULTIPART'
        else:
            self.mock_raw_response_klass.type = None
            self.mock_response_klass.type = None

        container = Container(name='foo_bar_container', extra={},
                              driver=self.driver)
        object_name = 'foo_test_stream_data'
        iterator = DummyIterator(data=[''])
        extra = {'content_type': 'text/plain'}
        obj = self.driver.upload_object_via_stream(container=container,
                                                   object_name=object_name,
                                                   iterator=iterator,
                                                   extra=extra)

        self.assertEqual(obj.name, object_name)
        self.assertEqual(obj.size, 0)

    def test_upload_small_object_via_stream(self):
        if self.driver.supports_s3_multipart_upload:
            self.mock_raw_response_klass.type = 'MULTIPART'
            self.mock_response_klass.type = 'MULTIPART'
        else:
            self.mock_raw_response_klass.type = None
            self.mock_response_klass.type = None

        container = Container(name='foo_bar_container', extra={},
                              driver=self.driver)
        object_name = 'foo_test_stream_data'
        iterator = DummyIterator(data=['2', '3', '5'])
        extra = {'content_type': 'text/plain'}
        obj = self.driver.upload_object_via_stream(container=container,
                                                   object_name=object_name,
                                                   iterator=iterator,
                                                   extra=extra)

        self.assertEqual(obj.name, object_name)
        self.assertEqual(obj.size, 3)

    def test_upload_big_object_via_stream(self):
        if self.driver.supports_s3_multipart_upload:
            self.mock_raw_response_klass.type = 'MULTIPART'
            self.mock_response_klass.type = 'MULTIPART'
        else:
            self.mock_raw_response_klass.type = None
            self.mock_response_klass.type = None

        container = Container(name='foo_bar_container', extra={},
                              driver=self.driver)
        object_name = 'foo_test_stream_data'
        iterator = DummyIterator(
            data=['2' * CHUNK_SIZE, '3' * CHUNK_SIZE, '5'])
        extra = {'content_type': 'text/plain'}
        obj = self.driver.upload_object_via_stream(container=container,
                                                   object_name=object_name,
                                                   iterator=iterator,
                                                   extra=extra)

        self.assertEqual(obj.name, object_name)
        self.assertEqual(obj.size, CHUNK_SIZE * 2 + 1)

    def test_upload_object_via_stream_abort(self):
        if not self.driver.supports_s3_multipart_upload:
            return

        self.mock_raw_response_klass.type = 'MULTIPART'
        self.mock_response_klass.type = 'MULTIPART'

        def _faulty_iterator():
            for i in range(0, 5):
                yield str(i)
            raise RuntimeError('Error in fetching data')

        container = Container(name='foo_bar_container', extra={},
                              driver=self.driver)
        object_name = 'foo_test_stream_data'
        iterator = _faulty_iterator()
        extra = {'content_type': 'text/plain'}

        try:
            self.driver.upload_object_via_stream(container=container,
                                                 object_name=object_name,
                                                 iterator=iterator,
                                                 extra=extra)
        except Exception:
            pass

        return

    def test_s3_list_multipart_uploads(self):
        if not self.driver.supports_s3_multipart_upload:
            return

        self.mock_response_klass.type = 'LIST_MULTIPART'
        S3StorageDriver.RESPONSES_PER_REQUEST = 2

        container = Container(name='foo_bar_container', extra={},
                              driver=self.driver)

        for upload in self.driver.ex_iterate_multipart_uploads(container):
            self.assertNotEqual(upload.key, None)
            self.assertNotEqual(upload.id, None)
            self.assertNotEqual(upload.created_at, None)
            self.assertNotEqual(upload.owner, None)
            self.assertNotEqual(upload.initiator, None)

    def test_s3_abort_multipart_uploads(self):
        if not self.driver.supports_s3_multipart_upload:
            return

        self.mock_response_klass.type = 'LIST_MULTIPART'
        S3StorageDriver.RESPONSES_PER_REQUEST = 2

        container = Container(name='foo_bar_container', extra={},
                              driver=self.driver)

        self.driver.ex_cleanup_all_multipart_uploads(container)

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


class S3USWestTests(S3Tests):
    driver_type = S3USWestStorageDriver


class S3EUWestTests(S3Tests):
    driver_type = S3EUWestStorageDriver


class S3APSETests(S3Tests):
    driver_type = S3APSEStorageDriver


class S3APNETests(S3Tests):
    driver_tyoe = S3APNEStorageDriver


if __name__ == '__main__':
    sys.exit(unittest.main())
