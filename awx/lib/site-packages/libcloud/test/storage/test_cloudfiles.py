# -*- coding: utf-8 -*-
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
from hashlib import sha1
import hmac
import os
import os.path                          # pylint: disable-msg=W0404
import math
import sys
import copy
import unittest

import mock

import libcloud.utils.files

from libcloud.utils.py3 import b
from libcloud.utils.py3 import httplib
from libcloud.utils.py3 import urlquote

from libcloud.common.types import LibcloudError, MalformedResponseError
from libcloud.storage.base import Container, Object
from libcloud.storage.types import ContainerAlreadyExistsError
from libcloud.storage.types import ContainerDoesNotExistError
from libcloud.storage.types import ContainerIsNotEmptyError
from libcloud.storage.types import ObjectDoesNotExistError
from libcloud.storage.types import ObjectHashMismatchError
from libcloud.storage.types import InvalidContainerNameError
from libcloud.storage.drivers.cloudfiles import CloudFilesStorageDriver
from libcloud.storage.drivers.cloudfiles import CloudFilesUSStorageDriver
from libcloud.storage.drivers.cloudfiles import CloudFilesUKStorageDriver
from libcloud.storage.drivers.dummy import DummyIterator

from libcloud.test import StorageMockHttp, MockRawResponse  # pylint: disable-msg=E0611
from libcloud.test import MockHttpTestCase  # pylint: disable-msg=E0611
from libcloud.test.file_fixtures import StorageFileFixtures  # pylint: disable-msg=E0611


class CloudFilesTests(unittest.TestCase):
    driver_klass = CloudFilesStorageDriver
    driver_args = ('dummy', 'dummy')
    driver_kwargs = {}
    region = 'ord'

    def setUp(self):
        self.driver_klass.connectionCls.conn_classes = (
            None, CloudFilesMockHttp)
        self.driver_klass.connectionCls.rawResponseCls = \
            CloudFilesMockRawResponse
        CloudFilesMockHttp.type = None
        CloudFilesMockRawResponse.type = None
        self.driver = self.driver_klass(*self.driver_args,
                                        **self.driver_kwargs)

        # normally authentication happens lazily, but we force it here
        self.driver.connection._populate_hosts_and_request_paths()
        self._remove_test_file()

    def tearDown(self):
        self._remove_test_file()

    def test_invalid_ex_force_service_region(self):
        driver = CloudFilesStorageDriver('driver', 'dummy',
                                         ex_force_service_region='invalid')

        try:
            driver.list_containers()
        except:
            e = sys.exc_info()[1]
            self.assertEqual(e.value, 'Could not find specified endpoint')
        else:
            self.fail('Exception was not thrown')

    def test_ex_force_service_region(self):
        driver = CloudFilesStorageDriver('driver', 'dummy',
                                         ex_force_service_region='ORD')
        driver.list_containers()

    def test_force_auth_token_kwargs(self):
        base_url = 'https://cdn2.clouddrive.com/v1/MossoCloudFS'
        kwargs = {
            'ex_force_auth_token': 'some-auth-token',
            'ex_force_base_url': base_url
        }
        driver = CloudFilesStorageDriver('driver', 'dummy', **kwargs)
        driver.list_containers()

        self.assertEqual(kwargs['ex_force_auth_token'],
                         driver.connection.auth_token)
        self.assertEqual('cdn2.clouddrive.com',
                         driver.connection.host)
        self.assertEqual('/v1/MossoCloudFS',
                         driver.connection.request_path)

    def test_force_auth_url_kwargs(self):
        kwargs = {
            'ex_force_auth_version': '2.0',
            'ex_force_auth_url': 'https://identity.api.rackspace.com'
        }
        driver = CloudFilesStorageDriver('driver', 'dummy', **kwargs)

        self.assertEqual(kwargs['ex_force_auth_url'],
                         driver.connection._ex_force_auth_url)
        self.assertEqual(kwargs['ex_force_auth_version'],
                         driver.connection._auth_version)

    def test_invalid_json_throws_exception(self):
        CloudFilesMockHttp.type = 'MALFORMED_JSON'
        try:
            self.driver.list_containers()
        except MalformedResponseError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_service_catalog(self):
        url = 'https://storage4.%s1.clouddrive.com/v1/MossoCloudFS' % \
              (self.region)
        self.assertEqual(
            url,
            self.driver.connection.get_endpoint())

        self.driver.connection.cdn_request = True
        self.assertEqual(
            'https://cdn.clouddrive.com/v1/MossoCloudFS',
            self.driver.connection.get_endpoint())
        self.driver.connection.cdn_request = False

    def test_endpoint_pointer(self):
        kwargs = {'use_internal_url': False}
        driver = CloudFilesStorageDriver('driver', 'dummy', **kwargs)
        self.assertEquals(driver.connection._get_endpoint_key(), libcloud.storage.drivers.cloudfiles.PUBLIC_ENDPOINT_KEY)
        kwargs = {'use_internal_url': True}
        driver = CloudFilesStorageDriver('driver', 'dummy', **kwargs)
        self.assertEquals(driver.connection._get_endpoint_key(), libcloud.storage.drivers.cloudfiles.INTERNAL_ENDPOINT_KEY)
        driver.connection.cdn_request = True
        self.assertEquals(driver.connection._get_endpoint_key(), libcloud.storage.drivers.cloudfiles.PUBLIC_ENDPOINT_KEY)

    def test_list_containers(self):
        CloudFilesMockHttp.type = 'EMPTY'
        containers = self.driver.list_containers()
        self.assertEqual(len(containers), 0)

        CloudFilesMockHttp.type = None
        containers = self.driver.list_containers()
        self.assertEqual(len(containers), 3)

        container = [c for c in containers if c.name == 'container2'][0]
        self.assertEqual(container.extra['object_count'], 120)
        self.assertEqual(container.extra['size'], 340084450)

    def test_list_container_objects(self):
        CloudFilesMockHttp.type = 'EMPTY'
        container = Container(
            name='test_container', extra={}, driver=self.driver)
        objects = self.driver.list_container_objects(container=container)
        self.assertEqual(len(objects), 0)

        CloudFilesMockHttp.type = None
        objects = self.driver.list_container_objects(container=container)
        self.assertEqual(len(objects), 4)

        obj = [o for o in objects if o.name == 'foo test 1'][0]
        self.assertEqual(obj.hash, '16265549b5bda64ecdaa5156de4c97cc')
        self.assertEqual(obj.size, 1160520)
        self.assertEqual(obj.container.name, 'test_container')

    def test_list_container_object_name_encoding(self):
        CloudFilesMockHttp.type = 'EMPTY'
        container = Container(name='test container 1', extra={},
                              driver=self.driver)
        objects = self.driver.list_container_objects(container=container)
        self.assertEqual(len(objects), 0)

    def test_list_container_objects_with_prefix(self):
        CloudFilesMockHttp.type = 'EMPTY'
        container = Container(
            name='test_container', extra={}, driver=self.driver)
        objects = self.driver.list_container_objects(container=container,
                                                     ex_prefix='test_prefix1')
        self.assertEqual(len(objects), 0)

        CloudFilesMockHttp.type = None
        objects = self.driver.list_container_objects(container=container,
                                                     ex_prefix='test_prefix2')
        self.assertEqual(len(objects), 4)

        obj = [o for o in objects if o.name == 'foo test 1'][0]
        self.assertEqual(obj.hash, '16265549b5bda64ecdaa5156de4c97cc')
        self.assertEqual(obj.size, 1160520)
        self.assertEqual(obj.container.name, 'test_container')

    def test_list_container_objects_iterator(self):
        CloudFilesMockHttp.type = 'ITERATOR'
        container = Container(
            name='test_container', extra={}, driver=self.driver)
        objects = self.driver.list_container_objects(container=container)
        self.assertEqual(len(objects), 5)

        obj = [o for o in objects if o.name == 'foo-test-1'][0]
        self.assertEqual(obj.hash, '16265549b5bda64ecdaa5156de4c97cc')
        self.assertEqual(obj.size, 1160520)
        self.assertEqual(obj.container.name, 'test_container')

    def test_get_container(self):
        container = self.driver.get_container(container_name='test_container')
        self.assertEqual(container.name, 'test_container')
        self.assertEqual(container.extra['object_count'], 800)
        self.assertEqual(container.extra['size'], 1234568)

    def test_get_container_not_found(self):
        try:
            self.driver.get_container(container_name='not_found')
        except ContainerDoesNotExistError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_get_object_success(self):
        obj = self.driver.get_object(container_name='test_container',
                                     object_name='test_object')
        self.assertEqual(obj.container.name, 'test_container')
        self.assertEqual(obj.size, 555)
        self.assertEqual(obj.hash, '6b21c4a111ac178feacf9ec9d0c71f17')
        self.assertEqual(obj.extra['content_type'], 'application/zip')
        self.assertEqual(
            obj.extra['last_modified'], 'Tue, 25 Jan 2011 22:01:49 GMT')
        self.assertEqual(obj.meta_data['foo-bar'], 'test 1')
        self.assertEqual(obj.meta_data['bar-foo'], 'test 2')

    def test_get_object_object_name_encoding(self):
        obj = self.driver.get_object(container_name='test_container',
                                     object_name='~/test_object/')
        self.assertEqual(obj.name, '~/test_object/')

    def test_get_object_not_found(self):
        try:
            self.driver.get_object(container_name='test_container',
                                   object_name='not_found')
        except ObjectDoesNotExistError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_create_container_success(self):
        container = self.driver.create_container(
            container_name='test_create_container')
        self.assertTrue(isinstance(container, Container))
        self.assertEqual(container.name, 'test_create_container')
        self.assertEqual(container.extra['object_count'], 0)

    def test_create_container_already_exists(self):
        CloudFilesMockHttp.type = 'ALREADY_EXISTS'

        try:
            self.driver.create_container(
                container_name='test_create_container')
        except ContainerAlreadyExistsError:
            pass
        else:
            self.fail(
                'Container already exists but an exception was not thrown')

    def test_create_container_invalid_name_too_long(self):
        name = ''.join(['x' for x in range(0, 257)])
        try:
            self.driver.create_container(container_name=name)
        except InvalidContainerNameError:
            pass
        else:
            self.fail(
                'Invalid name was provided (name is too long)'
                ', but exception was not thrown')

    def test_create_container_invalid_name_slashes_in_name(self):
        try:
            self.driver.create_container(container_name='test/slashes/')
        except InvalidContainerNameError:
            pass
        else:
            self.fail(
                'Invalid name was provided (name contains slashes)'
                ', but exception was not thrown')

    def test_delete_container_success(self):
        container = Container(name='foo_bar_container', extra={}, driver=self)
        result = self.driver.delete_container(container=container)
        self.assertTrue(result)

    def test_delete_container_not_found(self):
        CloudFilesMockHttp.type = 'NOT_FOUND'
        container = Container(name='foo_bar_container', extra={}, driver=self)
        try:
            self.driver.delete_container(container=container)
        except ContainerDoesNotExistError:
            pass
        else:
            self.fail(
                'Container does not exist but an exception was not thrown')

    def test_delete_container_not_empty(self):
        CloudFilesMockHttp.type = 'NOT_EMPTY'
        container = Container(name='foo_bar_container', extra={}, driver=self)
        try:
            self.driver.delete_container(container=container)
        except ContainerIsNotEmptyError:
            pass
        else:
            self.fail('Container is not empty but an exception was not thrown')

    def test_download_object_success(self):
        container = Container(name='foo_bar_container', extra={}, driver=self)
        obj = Object(name='foo_bar_object', size=1000, hash=None, extra={},
                     container=container, meta_data=None,
                     driver=CloudFilesStorageDriver)
        destination_path = os.path.abspath(__file__) + '.temp'
        result = self.driver.download_object(obj=obj,
                                             destination_path=destination_path,
                                             overwrite_existing=False,
                                             delete_on_failure=True)
        self.assertTrue(result)

    def test_download_object_invalid_file_size(self):
        CloudFilesMockRawResponse.type = 'INVALID_SIZE'
        container = Container(name='foo_bar_container', extra={}, driver=self)
        obj = Object(name='foo_bar_object', size=1000, hash=None, extra={},
                     container=container, meta_data=None,
                     driver=CloudFilesStorageDriver)
        destination_path = os.path.abspath(__file__) + '.temp'
        result = self.driver.download_object(obj=obj,
                                             destination_path=destination_path,
                                             overwrite_existing=False,
                                             delete_on_failure=True)
        self.assertFalse(result)

    def test_download_object_success_not_found(self):
        CloudFilesMockRawResponse.type = 'NOT_FOUND'
        container = Container(name='foo_bar_container', extra={}, driver=self)

        obj = Object(name='foo_bar_object', size=1000, hash=None, extra={},
                     container=container,
                     meta_data=None,
                     driver=CloudFilesStorageDriver)
        destination_path = os.path.abspath(__file__) + '.temp'
        try:
            self.driver.download_object(
                obj=obj,
                destination_path=destination_path,
                overwrite_existing=False,
                delete_on_failure=True)
        except ObjectDoesNotExistError:
            pass
        else:
            self.fail('Object does not exist but an exception was not thrown')

    def test_download_object_as_stream(self):
        container = Container(name='foo_bar_container', extra={}, driver=self)
        obj = Object(name='foo_bar_object', size=1000, hash=None, extra={},
                     container=container, meta_data=None,
                     driver=CloudFilesStorageDriver)

        stream = self.driver.download_object_as_stream(
            obj=obj, chunk_size=None)
        self.assertTrue(hasattr(stream, '__iter__'))

    def test_upload_object_success(self):
        def upload_file(self, response, file_path, chunked=False,
                        calculate_hash=True):
            return True, 'hash343hhash89h932439jsaa89', 1000

        old_func = CloudFilesStorageDriver._upload_file
        CloudFilesStorageDriver._upload_file = upload_file
        file_path = os.path.abspath(__file__)
        container = Container(name='foo_bar_container', extra={}, driver=self)
        object_name = 'foo_test_upload'
        extra = {'meta_data': {'some-value': 'foobar'}}
        obj = self.driver.upload_object(
            file_path=file_path, container=container,
            extra=extra, object_name=object_name)
        self.assertEqual(obj.name, 'foo_test_upload')
        self.assertEqual(obj.size, 1000)
        self.assertTrue('some-value' in obj.meta_data)
        CloudFilesStorageDriver._upload_file = old_func

    def test_upload_object_zero_size_object(self):
        def upload_file(self, response, file_path, chunked=False,
                        calculate_hash=True):
            return True, 'hash343hhash89h932439jsaa89', 0

        old_func = CloudFilesStorageDriver._upload_file
        old_request = self.driver.connection.request
        CloudFilesStorageDriver._upload_file = upload_file
        file_path = os.path.join(os.path.dirname(__file__), '__init__.py')
        container = Container(name='foo_bar_container', extra={}, driver=self)
        object_name = 'empty'
        extra = {}

        def func(*args, **kwargs):
            self.assertEqual(kwargs['headers']['Content-Length'], 0)
            func.called = True
            return old_request(*args, **kwargs)

        self.driver.connection.request = func
        func.called = False
        obj = self.driver.upload_object(
            file_path=file_path, container=container,
            extra=extra, object_name=object_name)
        self.assertEqual(obj.name, 'empty')
        self.assertEqual(obj.size, 0)
        self.assertTrue(func.called)
        CloudFilesStorageDriver._upload_file = old_func
        self.driver.connection.request = old_request

    def test_upload_object_invalid_hash(self):
        def upload_file(self, response, file_path, chunked=False,
                        calculate_hash=True):
            return True, 'hash343hhash89h932439jsaa89', 1000

        CloudFilesMockRawResponse.type = 'INVALID_HASH'

        old_func = CloudFilesStorageDriver._upload_file
        CloudFilesStorageDriver._upload_file = upload_file
        file_path = os.path.abspath(__file__)
        container = Container(name='foo_bar_container', extra={}, driver=self)
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
            CloudFilesStorageDriver._upload_file = old_func

    def test_upload_object_no_content_type(self):
        def no_content_type(name):
            return None, None

        old_func = libcloud.utils.files.guess_file_mime_type
        libcloud.utils.files.guess_file_mime_type = no_content_type
        file_path = os.path.abspath(__file__)
        container = Container(name='foo_bar_container', extra={}, driver=self)
        object_name = 'foo_test_upload'

        obj = self.driver.upload_object(file_path=file_path, verify_hash=False,
                                        container=container,
                                        object_name=object_name)

        self.assertEqual(obj.name, object_name)
        libcloud.utils.files.guess_file_mime_type = old_func

    def test_upload_object_error(self):
        def dummy_content_type(name):
            return 'application/zip', None

        def send(instance):
            raise Exception('')

        old_func1 = libcloud.utils.files.guess_file_mime_type
        libcloud.utils.files.guess_file_mime_type = dummy_content_type
        old_func2 = CloudFilesMockHttp.send
        CloudFilesMockHttp.send = send

        file_path = os.path.abspath(__file__)
        container = Container(name='foo_bar_container', extra={}, driver=self)
        object_name = 'foo_test_upload'
        try:
            self.driver.upload_object(
                file_path=file_path,
                container=container,
                object_name=object_name)
        except LibcloudError:
            pass
        else:
            self.fail(
                'Timeout while uploading but an exception was not thrown')
        finally:
            libcloud.utils.files.guess_file_mime_type = old_func1
            CloudFilesMockHttp.send = old_func2

    def test_upload_object_inexistent_file(self):
        def dummy_content_type(name):
            return 'application/zip', None

        old_func = libcloud.utils.files.guess_file_mime_type
        libcloud.utils.files.guess_file_mime_type = dummy_content_type

        file_path = os.path.abspath(__file__ + '.inexistent')
        container = Container(name='foo_bar_container', extra={}, driver=self)
        object_name = 'foo_test_upload'
        try:
            self.driver.upload_object(
                file_path=file_path,
                container=container,
                object_name=object_name)
        except OSError:
            pass
        else:
            self.fail('Inexistent but an exception was not thrown')
        finally:
            libcloud.utils.files.guess_file_mime_type = old_func

    def test_upload_object_via_stream(self):
        def dummy_content_type(name):
            return 'application/zip', None

        old_func = libcloud.utils.files.guess_file_mime_type
        libcloud.utils.files.guess_file_mime_type = dummy_content_type

        container = Container(name='foo_bar_container', extra={}, driver=self)
        object_name = 'foo_test_stream_data'
        iterator = DummyIterator(data=['2', '3', '5'])
        try:
            self.driver.upload_object_via_stream(container=container,
                                                 object_name=object_name,
                                                 iterator=iterator)
        finally:
            libcloud.utils.files.guess_file_mime_type = old_func

    def test_delete_object_success(self):
        container = Container(name='foo_bar_container', extra={}, driver=self)
        obj = Object(name='foo_bar_object', size=1000, hash=None, extra={},
                     container=container, meta_data=None,
                     driver=CloudFilesStorageDriver)
        status = self.driver.delete_object(obj=obj)
        self.assertTrue(status)

    def test_delete_object_not_found(self):
        CloudFilesMockHttp.type = 'NOT_FOUND'
        container = Container(name='foo_bar_container', extra={}, driver=self)
        obj = Object(name='foo_bar_object', size=1000, hash=None, extra={},
                     container=container, meta_data=None,
                     driver=CloudFilesStorageDriver)
        try:
            self.driver.delete_object(obj=obj)
        except ObjectDoesNotExistError:
            pass
        else:
            self.fail('Object does not exist but an exception was not thrown')

    def test_ex_get_meta_data(self):
        meta_data = self.driver.ex_get_meta_data()
        self.assertTrue(isinstance(meta_data, dict))
        self.assertTrue('object_count' in meta_data)
        self.assertTrue('container_count' in meta_data)
        self.assertTrue('bytes_used' in meta_data)
        self.assertTrue('temp_url_key' in meta_data)

    def test_ex_purge_object_from_cdn(self):
        CloudFilesMockHttp.type = 'PURGE_SUCCESS'
        container = Container(name='foo_bar_container', extra={},
                              driver=self.driver)
        obj = Object(name='object', size=1000, hash=None, extra={},
                     container=container, meta_data=None,
                     driver=self)

        self.assertTrue(self.driver.ex_purge_object_from_cdn(obj=obj))

    def test_ex_purge_object_from_cdn_with_email(self):
        CloudFilesMockHttp.type = 'PURGE_SUCCESS_EMAIL'
        container = Container(name='foo_bar_container', extra={},
                              driver=self.driver)
        obj = Object(name='object', size=1000, hash=None, extra={},
                     container=container, meta_data=None,
                     driver=self)
        self.assertTrue(self.driver.ex_purge_object_from_cdn(obj=obj,
                                                             email='test@test.com'))

    @mock.patch('os.path.getsize')
    def test_ex_multipart_upload_object_for_small_files(self, getsize_mock):
        getsize_mock.return_value = 0

        old_func = CloudFilesStorageDriver.upload_object
        mocked_upload_object = mock.Mock(return_value="test")
        CloudFilesStorageDriver.upload_object = mocked_upload_object

        file_path = os.path.abspath(__file__)
        container = Container(name='foo_bar_container', extra={}, driver=self)
        object_name = 'foo_test_upload'
        obj = self.driver.ex_multipart_upload_object(
            file_path=file_path, container=container,
            object_name=object_name)
        CloudFilesStorageDriver.upload_object = old_func

        self.assertTrue(mocked_upload_object.called)
        self.assertEqual(obj, "test")

    def test_ex_multipart_upload_object_success(self):
        _upload_object_part = CloudFilesStorageDriver._upload_object_part
        _upload_object_manifest = CloudFilesStorageDriver._upload_object_manifest

        mocked__upload_object_part = mock.Mock(return_value="test_part")
        mocked__upload_object_manifest = mock.Mock(
            return_value="test_manifest")

        CloudFilesStorageDriver._upload_object_part = mocked__upload_object_part
        CloudFilesStorageDriver._upload_object_manifest = mocked__upload_object_manifest

        parts = 5
        file_path = os.path.abspath(__file__)
        chunk_size = int(math.ceil(float(os.path.getsize(file_path)) / parts))
        container = Container(name='foo_bar_container', extra={}, driver=self)
        object_name = 'foo_test_upload'
        self.driver.ex_multipart_upload_object(
            file_path=file_path, container=container,
            object_name=object_name, chunk_size=chunk_size)

        CloudFilesStorageDriver._upload_object_part = _upload_object_part
        CloudFilesStorageDriver._upload_object_manifest = _upload_object_manifest

        self.assertEqual(mocked__upload_object_part.call_count, parts)
        self.assertTrue(mocked__upload_object_manifest.call_count, 1)

    def test__upload_object_part(self):
        _put_object = CloudFilesStorageDriver._put_object
        mocked__put_object = mock.Mock(return_value="test")
        CloudFilesStorageDriver._put_object = mocked__put_object

        part_number = 7
        object_name = "test_object"
        expected_name = object_name + '/%08d' % part_number
        container = Container(name='foo_bar_container', extra={}, driver=self)

        self.driver._upload_object_part(container, object_name,
                                        part_number, None)

        CloudFilesStorageDriver._put_object = _put_object

        func_kwargs = tuple(mocked__put_object.call_args)[1]
        self.assertEqual(func_kwargs['object_name'], expected_name)
        self.assertEqual(func_kwargs['container'], container)

    def test__upload_object_manifest(self):
        hash_function = self.driver._get_hash_function()
        hash_function.update(b(''))
        data_hash = hash_function.hexdigest()

        fake_response = type('CloudFilesResponse', (), {'headers':
                                                        {'etag': data_hash}
                                                        })

        _request = self.driver.connection.request
        mocked_request = mock.Mock(return_value=fake_response)
        self.driver.connection.request = mocked_request

        container = Container(name='foo_bar_container', extra={}, driver=self)
        object_name = "test_object"

        self.driver._upload_object_manifest(container, object_name)

        func_args, func_kwargs = tuple(mocked_request.call_args)

        self.driver.connection.request = _request

        self.assertEqual(
            func_args[0], "/" + container.name + "/" + object_name)
        self.assertEqual(func_kwargs["headers"]["X-Object-Manifest"],
                         container.name + "/" + object_name + "/")
        self.assertEqual(func_kwargs["method"], "PUT")

    def test__upload_object_manifest_wrong_hash(self):
        fake_response = type('CloudFilesResponse', (), {'headers':
                                                        {'etag': '0000000'}})

        _request = self.driver.connection.request
        mocked_request = mock.Mock(return_value=fake_response)
        self.driver.connection.request = mocked_request

        container = Container(name='foo_bar_container', extra={}, driver=self)
        object_name = "test_object"

        try:
            self.driver._upload_object_manifest(container, object_name)
        except ObjectHashMismatchError:
            pass
        else:
            self.fail('Exception was not thrown')
        finally:
            self.driver.connection.request = _request

    def test_create_container_put_object_name_encoding(self):
        def upload_file(self, response, file_path, chunked=False,
                        calculate_hash=True):
            return True, 'hash343hhash89h932439jsaa89', 1000

        old_func = CloudFilesStorageDriver._upload_file
        CloudFilesStorageDriver._upload_file = upload_file

        container_name = 'speci@l_name'
        object_name = 'm@obj€ct'
        file_path = os.path.abspath(__file__)

        container = self.driver.create_container(container_name=container_name)
        self.assertEqual(container.name, container_name)

        obj = self.driver.upload_object(
            file_path=file_path, container=container,
            object_name=object_name)
        self.assertEqual(obj.name, object_name)
        CloudFilesStorageDriver._upload_file = old_func

    def test_ex_enable_static_website(self):
        container = Container(name='foo_bar_container', extra={}, driver=self)
        result = self.driver.ex_enable_static_website(container=container,
                                                      index_file='index.html')
        self.assertTrue(result)

    def test_ex_set_error_page(self):
        container = Container(name='foo_bar_container', extra={}, driver=self)
        result = self.driver.ex_set_error_page(container=container,
                                               file_name='error.html')
        self.assertTrue(result)

    def test_ex_set_account_metadata_temp_url_key(self):
        result = self.driver.ex_set_account_metadata_temp_url_key("a key")
        self.assertTrue(result)

    @mock.patch("libcloud.storage.drivers.cloudfiles.time")
    def test_ex_get_object_temp_url(self, time):
        time.return_value = 0
        self.driver.ex_get_meta_data = mock.Mock()
        self.driver.ex_get_meta_data.return_value = {'container_count': 1,
                                                     'object_count': 1,
                                                     'bytes_used': 1,
                                                     'temp_url_key': 'foo'}
        container = Container(name='foo_bar_container', extra={}, driver=self)
        obj = Object(name='foo_bar_object', size=1000, hash=None, extra={},
                     container=container, meta_data=None,
                     driver=self)
        hmac_body = "%s\n%s\n%s" % ('GET', 60,
                                    "/v1/MossoCloudFS/foo_bar_container/foo_bar_object")
        sig = hmac.new(b('foo'), b(hmac_body), sha1).hexdigest()
        ret = self.driver.ex_get_object_temp_url(obj, 'GET')
        temp_url = ('https://storage4.%s1.clouddrive.com/v1/MossoCloudFS/'
                    'foo_bar_container/foo_bar_object?temp_url_expires=60&temp_url_sig=%s' %
                    (self.region, sig))

        self.assertEqual(''.join(sorted(ret)), ''.join(sorted(temp_url)))

    def test_ex_get_object_temp_url_no_key_raises_key_error(self):
        self.driver.ex_get_meta_data = mock.Mock()
        self.driver.ex_get_meta_data.return_value = {'container_count': 1,
                                                     'object_count': 1,
                                                     'bytes_used': 1,
                                                     'temp_url_key': None}
        container = Container(name='foo_bar_container', extra={}, driver=self)
        obj = Object(name='foo_bar_object', size=1000, hash=None, extra={},
                     container=container, meta_data=None,
                     driver=self)
        self.assertRaises(
            KeyError, self.driver.ex_get_object_temp_url, obj, 'GET')

    def _remove_test_file(self):
        file_path = os.path.abspath(__file__) + '.temp'

        try:
            os.unlink(file_path)
        except OSError:
            pass


class CloudFilesDeprecatedUSTests(CloudFilesTests):
    driver_klass = CloudFilesUSStorageDriver
    region = 'ord'


class CloudFilesDeprecatedUKTests(CloudFilesTests):
    driver_klass = CloudFilesUKStorageDriver
    region = 'lon'


class CloudFilesMockHttp(StorageMockHttp, MockHttpTestCase):

    fixtures = StorageFileFixtures('cloudfiles')
    base_headers = {'content-type': 'application/json; charset=UTF-8'}

    # fake auth token response
    def _v2_0_tokens(self, method, url, body, headers):
        headers = copy.deepcopy(self.base_headers)
        body = self.fixtures.load('_v2_0__auth.json')
        return (httplib.OK, body, headers,
                httplib.responses[httplib.OK])

    def _v1_MossoCloudFS_MALFORMED_JSON(self, method, url, body, headers):
        # test_invalid_json_throws_exception
        body = 'broken: json /*"'
        return (httplib.NO_CONTENT,
                body,
                self.base_headers,
                httplib.responses[httplib.OK])

    def _v1_MossoCloudFS_EMPTY(self, method, url, body, headers):
        return (httplib.NO_CONTENT,
                body,
                self.base_headers,
                httplib.responses[httplib.OK])

    def _v1_MossoCloudFS(self, method, url, body, headers):
        headers = copy.deepcopy(self.base_headers)
        if method == 'GET':
            # list_containers
            body = self.fixtures.load('list_containers.json')
            status_code = httplib.OK
        elif method == 'HEAD':
            # get_meta_data
            body = self.fixtures.load('meta_data.json')
            status_code = httplib.NO_CONTENT
            headers.update({'x-account-container-count': 10,
                            'x-account-object-count': 400,
                            'x-account-bytes-used': 1234567
                            })
        elif method == 'POST':
            body = ''
            status_code = httplib.NO_CONTENT
        return (status_code, body, headers, httplib.responses[httplib.OK])

    def _v1_MossoCloudFS_not_found(self, method, url, body, headers):
        # test_get_object_not_found
        if method == 'HEAD':
            body = ''
        else:
            raise ValueError('Invalid method')

        return (httplib.NOT_FOUND,
                body,
                self.base_headers,
                httplib.responses[httplib.OK])

    def _v1_MossoCloudFS_test_container_EMPTY(self, method, url, body, headers):
        body = self.fixtures.load('list_container_objects_empty.json')
        return (httplib.OK,
                body,
                self.base_headers,
                httplib.responses[httplib.OK])

    def _v1_MossoCloudFS_test_20container_201_EMPTY(self, method, url, body, headers):
        body = self.fixtures.load('list_container_objects_empty.json')
        return (httplib.OK,
                body,
                self.base_headers,
                httplib.responses[httplib.OK])

    def _v1_MossoCloudFS_test_container(self, method, url, body, headers):
        headers = copy.deepcopy(self.base_headers)
        if method == 'GET':
            # list_container_objects
            if url.find('marker') == -1:
                body = self.fixtures.load('list_container_objects.json')
                status_code = httplib.OK
            else:
                body = ''
                status_code = httplib.NO_CONTENT
        elif method == 'HEAD':
            # get_container
            body = self.fixtures.load('list_container_objects_empty.json')
            status_code = httplib.NO_CONTENT
            headers.update({'x-container-object-count': 800,
                            'x-container-bytes-used': 1234568
                            })
        return (status_code, body, headers, httplib.responses[httplib.OK])

    def _v1_MossoCloudFS_test_container_ITERATOR(self, method, url, body, headers):
        headers = copy.deepcopy(self.base_headers)
        # list_container_objects
        if url.find('foo-test-3') != -1:
            body = self.fixtures.load(
                'list_container_objects_not_exhausted2.json')
            status_code = httplib.OK
        elif url.find('foo-test-5') != -1:
            body = ''
            status_code = httplib.NO_CONTENT
        else:
            # First request
            body = self.fixtures.load(
                'list_container_objects_not_exhausted1.json')
            status_code = httplib.OK

        return (status_code, body, headers, httplib.responses[httplib.OK])

    def _v1_MossoCloudFS_test_container_not_found(
            self, method, url, body, headers):
        # test_get_container_not_found
        if method == 'HEAD':
            body = ''
        else:
            raise ValueError('Invalid method')

        return (httplib.NOT_FOUND, body,
                self.base_headers,
                httplib.responses[httplib.OK])

    def _v1_MossoCloudFS_test_container_test_object(
            self, method, url, body, headers):
        headers = copy.deepcopy(self.base_headers)
        if method == 'HEAD':
            # get_object
            body = self.fixtures.load('list_container_objects_empty.json')
            status_code = httplib.NO_CONTENT
            headers.update({'content-length': 555,
                            'last-modified': 'Tue, 25 Jan 2011 22:01:49 GMT',
                            'etag': '6b21c4a111ac178feacf9ec9d0c71f17',
                            'x-object-meta-foo-bar': 'test 1',
                            'x-object-meta-bar-foo': 'test 2',
                            'content-type': 'application/zip'})
        return (status_code, body, headers, httplib.responses[httplib.OK])

    def _v1_MossoCloudFS_test_container__7E_test_object(
            self, method, url, body, headers):
        headers = copy.deepcopy(self.base_headers)
        if method == 'HEAD':
            # get_object_name_encoding
            body = self.fixtures.load('list_container_objects_empty.json')
            status_code = httplib.NO_CONTENT
            headers.update({'content-length': 555,
                            'last-modified': 'Tue, 25 Jan 2011 22:01:49 GMT',
                            'etag': '6b21c4a111ac178feacf9ec9d0c71f17',
                            'x-object-meta-foo-bar': 'test 1',
                            'x-object-meta-bar-foo': 'test 2',
                            'content-type': 'application/zip'})
        return (status_code, body, headers, httplib.responses[httplib.OK])

    def _v1_MossoCloudFS_test_create_container(
            self, method, url, body, headers):
        # test_create_container_success
        headers = copy.deepcopy(self.base_headers)
        body = self.fixtures.load('list_container_objects_empty.json')
        headers = copy.deepcopy(self.base_headers)
        headers.update({'content-length': 18,
                        'date': 'Mon, 28 Feb 2011 07:52:57 GMT'
                        })
        status_code = httplib.CREATED
        return (status_code, body, headers, httplib.responses[httplib.OK])

    def _v1_MossoCloudFS_speci_40l_name(self, method, url, body, headers):
        # test_create_container_put_object_name_encoding
        # Verify that the name is properly url encoded
        container_name = 'speci@l_name'
        encoded_container_name = urlquote(container_name)
        self.assertTrue(encoded_container_name in url)

        headers = copy.deepcopy(self.base_headers)
        body = self.fixtures.load('list_container_objects_empty.json')
        headers = copy.deepcopy(self.base_headers)
        headers.update({'content-length': 18,
                        'date': 'Mon, 28 Feb 2011 07:52:57 GMT'
                        })
        status_code = httplib.CREATED
        return (status_code, body, headers, httplib.responses[httplib.OK])

    def _v1_MossoCloudFS_test_create_container_ALREADY_EXISTS(
            self, method, url, body, headers):
        # test_create_container_already_exists
        headers = copy.deepcopy(self.base_headers)
        body = self.fixtures.load('list_container_objects_empty.json')
        headers.update({'content-type': 'text/plain'})
        status_code = httplib.ACCEPTED
        return (status_code, body, headers, httplib.responses[httplib.OK])

    def _v1_MossoCloudFS_foo_bar_container(self, method, url, body, headers):
        if method == 'DELETE':
            # test_delete_container_success
            body = self.fixtures.load('list_container_objects_empty.json')
            headers = self.base_headers
            status_code = httplib.NO_CONTENT
        elif method == 'POST':
            # test_ex_enable_static_website
            body = ''
            headers = self.base_headers
            status_code = httplib.ACCEPTED
        return (status_code, body, headers, httplib.responses[httplib.OK])

    def _v1_MossoCloudFS_foo_bar_container_object_PURGE_SUCCESS(
            self, method, url, body, headers):

        if method == 'DELETE':
            # test_ex_purge_from_cdn
            headers = self.base_headers
            status_code = httplib.NO_CONTENT
        return (status_code, body, headers, httplib.responses[httplib.OK])

    def _v1_MossoCloudFS_foo_bar_container_object_PURGE_SUCCESS_EMAIL(
            self, method, url, body, headers):

        if method == 'DELETE':
            # test_ex_purge_from_cdn_with_email
            self.assertEqual(headers['X-Purge-Email'], 'test@test.com')
            headers = self.base_headers
            status_code = httplib.NO_CONTENT
        return (status_code, body, headers, httplib.responses[httplib.OK])

    def _v1_MossoCloudFS_foo_bar_container_NOT_FOUND(
            self, method, url, body, headers):

        if method == 'DELETE':
            # test_delete_container_not_found
            body = self.fixtures.load('list_container_objects_empty.json')
            headers = self.base_headers
            status_code = httplib.NOT_FOUND
        return (status_code, body, headers, httplib.responses[httplib.OK])

    def _v1_MossoCloudFS_foo_bar_container_NOT_EMPTY(
            self, method, url, body, headers):

        if method == 'DELETE':
            # test_delete_container_not_empty
            body = self.fixtures.load('list_container_objects_empty.json')
            headers = self.base_headers
            status_code = httplib.CONFLICT
        return (status_code, body, headers, httplib.responses[httplib.OK])

    def _v1_MossoCloudFS_foo_bar_container_foo_bar_object(
            self, method, url, body, headers):

        if method == 'DELETE':
            # test_delete_object_success
            body = self.fixtures.load('list_container_objects_empty.json')
            headers = self.base_headers
            status_code = httplib.NO_CONTENT
        return (status_code, body, headers, httplib.responses[httplib.OK])

    def _v1_MossoCloudFS_foo_bar_container_foo_bar_object_NOT_FOUND(
            self, method, url, body, headers):

        if method == 'DELETE':
            # test_delete_object_success
            body = self.fixtures.load('list_container_objects_empty.json')
            headers = self.base_headers
            status_code = httplib.NOT_FOUND

        return (status_code, body, headers, httplib.responses[httplib.OK])


class CloudFilesMockRawResponse(MockRawResponse):

    fixtures = StorageFileFixtures('cloudfiles')
    base_headers = {'content-type': 'application/json; charset=UTF-8'}

    def _v1_MossoCloudFS_foo_bar_container_foo_test_upload(
            self, method, url, body, headers):
        # test_object_upload_success

        body = ''
        headers = {}
        headers.update(self.base_headers)
        headers['etag'] = 'hash343hhash89h932439jsaa89'
        return (httplib.CREATED, body, headers, httplib.responses[httplib.OK])

    def _v1_MossoCloudFS_speci_40l_name_m_40obj_E2_82_ACct(self, method, url,
                                                           body, headers):
        # test_create_container_put_object_name_encoding
        # Verify that the name is properly url encoded
        object_name = 'm@obj€ct'
        urlquote(object_name)

        headers = copy.deepcopy(self.base_headers)
        body = ''
        headers['etag'] = 'hash343hhash89h932439jsaa89'
        return (httplib.CREATED, body, headers, httplib.responses[httplib.OK])

    def _v1_MossoCloudFS_foo_bar_container_empty(self, method, url, body,
                                                 headers):
        # test_upload_object_zero_size_object
        body = ''
        headers = {}
        headers.update(self.base_headers)
        headers['etag'] = 'hash343hhash89h932439jsaa89'
        return (httplib.CREATED, body, headers, httplib.responses[httplib.OK])

    def _v1_MossoCloudFS_foo_bar_container_foo_test_upload_INVALID_HASH(
            self, method, url, body, headers):
        # test_object_upload_invalid_hash
        body = ''
        headers = {}
        headers.update(self.base_headers)
        headers['etag'] = 'foobar'
        return (httplib.CREATED, body, headers,
                httplib.responses[httplib.OK])

    def _v1_MossoCloudFS_foo_bar_container_foo_bar_object(
            self, method, url, body, headers):

        # test_download_object_success
        body = self._generate_random_data(1000)
        return (httplib.OK,
                body,
                self.base_headers,
                httplib.responses[httplib.OK])

    def _v1_MossoCloudFS_foo_bar_container_foo_bar_object_INVALID_SIZE(
            self, method, url, body, headers):
        # test_download_object_invalid_file_size
        body = self._generate_random_data(100)
        return (httplib.OK, body,
                self.base_headers,
                httplib.responses[httplib.OK])

    def _v1_MossoCloudFS_foo_bar_container_foo_bar_object_NOT_FOUND(
            self, method, url, body, headers):
        body = ''
        return (httplib.NOT_FOUND, body,
                self.base_headers,
                httplib.responses[httplib.OK])

    def _v1_MossoCloudFS_foo_bar_container_foo_test_stream_data(
            self, method, url, body, headers):

        # test_upload_object_via_stream_success
        headers = {}
        headers.update(self.base_headers)
        headers['etag'] = '577ef1154f3240ad5b9b413aa7346a1e'
        body = 'test'
        return (httplib.CREATED,
                body,
                headers,
                httplib.responses[httplib.OK])

if __name__ == '__main__':
    sys.exit(unittest.main())
