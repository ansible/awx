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

import base64
import os.path
import sys
import unittest

from libcloud.utils.py3 import httplib
from libcloud.utils.py3 import urlparse
from libcloud.utils.py3 import b

import libcloud.utils.files

from libcloud.common.types import LibcloudError
from libcloud.storage.base import Container, Object
from libcloud.storage.types import ContainerAlreadyExistsError, \
    ContainerDoesNotExistError, \
    ContainerIsNotEmptyError, \
    ObjectDoesNotExistError
from libcloud.storage.drivers.atmos import AtmosConnection, AtmosDriver
from libcloud.storage.drivers.dummy import DummyIterator

from libcloud.test import StorageMockHttp, MockRawResponse
from libcloud.test.file_fixtures import StorageFileFixtures


class AtmosTests(unittest.TestCase):

    def setUp(self):
        AtmosDriver.connectionCls.conn_classes = (None, AtmosMockHttp)
        AtmosDriver.connectionCls.rawResponseCls = AtmosMockRawResponse
        AtmosDriver.path = ''
        AtmosMockHttp.type = None
        AtmosMockHttp.upload_created = False
        AtmosMockRawResponse.type = None
        self.driver = AtmosDriver('dummy', base64.b64encode(b('dummy')))
        self._remove_test_file()

    def tearDown(self):
        self._remove_test_file()

    def _remove_test_file(self):
        file_path = os.path.abspath(__file__) + '.temp'

        try:
            os.unlink(file_path)
        except OSError:
            pass

    def test_list_containers(self):
        AtmosMockHttp.type = 'EMPTY'
        containers = self.driver.list_containers()
        self.assertEqual(len(containers), 0)

        AtmosMockHttp.type = None
        containers = self.driver.list_containers()
        self.assertEqual(len(containers), 6)

    def test_list_container_objects(self):
        container = Container(name='test_container', extra={},
                              driver=self.driver)

        AtmosMockHttp.type = 'EMPTY'
        objects = self.driver.list_container_objects(container=container)
        self.assertEqual(len(objects), 0)

        AtmosMockHttp.type = None
        objects = self.driver.list_container_objects(container=container)
        self.assertEqual(len(objects), 2)

        obj = [o for o in objects if o.name == 'not-a-container1'][0]
        self.assertEqual(obj.meta_data['object_id'],
                         '651eae32634bf84529c74eabd555fda48c7cead6')
        self.assertEqual(obj.container.name, 'test_container')

    def test_get_container(self):
        container = self.driver.get_container(container_name='test_container')
        self.assertEqual(container.name, 'test_container')
        self.assertEqual(container.extra['object_id'],
                         'b21cb59a2ba339d1afdd4810010b0a5aba2ab6b9')

    def test_get_container_escaped(self):
        container = self.driver.get_container(
            container_name='test & container')
        self.assertEqual(container.name, 'test & container')
        self.assertEqual(container.extra['object_id'],
                         'b21cb59a2ba339d1afdd4810010b0a5aba2ab6b9')

    def test_get_container_not_found(self):
        try:
            self.driver.get_container(container_name='not_found')
        except ContainerDoesNotExistError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_create_container_success(self):
        container = self.driver.create_container(
            container_name='test_create_container')
        self.assertTrue(isinstance(container, Container))
        self.assertEqual(container.name, 'test_create_container')
        self.assertEqual(container.extra['object_id'],
                         '31a27b593629a3fe59f887fd973fd953e80062ce')

    def test_create_container_already_exists(self):
        AtmosMockHttp.type = 'ALREADY_EXISTS'

        try:
            self.driver.create_container(
                container_name='test_create_container')
        except ContainerAlreadyExistsError:
            pass
        else:
            self.fail(
                'Container already exists but an exception was not thrown')

    def test_delete_container_success(self):
        container = Container(name='foo_bar_container', extra={}, driver=self)
        result = self.driver.delete_container(container=container)
        self.assertTrue(result)

    def test_delete_container_not_found(self):
        AtmosMockHttp.type = 'NOT_FOUND'
        container = Container(name='foo_bar_container', extra={}, driver=self)
        try:
            self.driver.delete_container(container=container)
        except ContainerDoesNotExistError:
            pass
        else:
            self.fail(
                'Container does not exist but an exception was not thrown')

    def test_delete_container_not_empty(self):
        AtmosMockHttp.type = 'NOT_EMPTY'
        container = Container(name='foo_bar_container', extra={}, driver=self)
        try:
            self.driver.delete_container(container=container)
        except ContainerIsNotEmptyError:
            pass
        else:
            self.fail('Container is not empty but an exception was not thrown')

    def test_get_object_success(self):
        obj = self.driver.get_object(container_name='test_container',
                                     object_name='test_object')
        self.assertEqual(obj.container.name, 'test_container')
        self.assertEqual(obj.size, 555)
        self.assertEqual(obj.hash, '6b21c4a111ac178feacf9ec9d0c71f17')
        self.assertEqual(obj.extra['object_id'],
                         '322dce3763aadc41acc55ef47867b8d74e45c31d6643')
        self.assertEqual(
            obj.extra['last_modified'], 'Tue, 25 Jan 2011 22:01:49 GMT')
        self.assertEqual(obj.meta_data['foo-bar'], 'test 1')
        self.assertEqual(obj.meta_data['bar-foo'], 'test 2')

    def test_get_object_escaped(self):
        obj = self.driver.get_object(container_name='test & container',
                                     object_name='test & object')
        self.assertEqual(obj.container.name, 'test & container')
        self.assertEqual(obj.size, 555)
        self.assertEqual(obj.hash, '6b21c4a111ac178feacf9ec9d0c71f17')
        self.assertEqual(obj.extra['object_id'],
                         '322dce3763aadc41acc55ef47867b8d74e45c31d6643')
        self.assertEqual(
            obj.extra['last_modified'], 'Tue, 25 Jan 2011 22:01:49 GMT')
        self.assertEqual(obj.meta_data['foo-bar'], 'test 1')
        self.assertEqual(obj.meta_data['bar-foo'], 'test 2')

    def test_get_object_not_found(self):
        try:
            self.driver.get_object(container_name='test_container',
                                   object_name='not_found')
        except ObjectDoesNotExistError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_delete_object_success(self):
        container = Container(name='foo_bar_container', extra={},
                              driver=self.driver)
        obj = Object(name='foo_bar_object', size=1000, hash=None, extra={},
                     container=container, meta_data=None,
                     driver=self.driver)
        status = self.driver.delete_object(obj=obj)
        self.assertTrue(status)

    def test_delete_object_escaped_success(self):
        container = Container(name='foo & bar_container', extra={},
                              driver=self.driver)
        obj = Object(name='foo & bar_object', size=1000, hash=None, extra={},
                     container=container, meta_data=None,
                     driver=self.driver)
        status = self.driver.delete_object(obj=obj)
        self.assertTrue(status)

    def test_delete_object_not_found(self):
        AtmosMockHttp.type = 'NOT_FOUND'
        container = Container(name='foo_bar_container', extra={},
                              driver=self.driver)
        obj = Object(name='foo_bar_object', size=1000, hash=None, extra={},
                     container=container, meta_data=None,
                     driver=self.driver)
        try:
            self.driver.delete_object(obj=obj)
        except ObjectDoesNotExistError:
            pass
        else:
            self.fail('Object does not exist but an exception was not thrown')

    def test_download_object_success(self):
        container = Container(name='foo_bar_container', extra={},
                              driver=self.driver)
        obj = Object(name='foo_bar_object', size=1000, hash=None, extra={},
                     container=container, meta_data=None,
                     driver=self.driver)
        destination_path = os.path.abspath(__file__) + '.temp'
        result = self.driver.download_object(obj=obj,
                                             destination_path=destination_path,
                                             overwrite_existing=False,
                                             delete_on_failure=True)
        self.assertTrue(result)

    def test_download_object_escaped_success(self):
        container = Container(name='foo & bar_container', extra={},
                              driver=self.driver)
        obj = Object(name='foo & bar_object', size=1000, hash=None, extra={},
                     container=container, meta_data=None,
                     driver=self.driver)
        destination_path = os.path.abspath(__file__) + '.temp'
        result = self.driver.download_object(obj=obj,
                                             destination_path=destination_path,
                                             overwrite_existing=False,
                                             delete_on_failure=True)
        self.assertTrue(result)

    def test_download_object_success_not_found(self):
        AtmosMockRawResponse.type = 'NOT_FOUND'
        container = Container(name='foo_bar_container', extra={},
                              driver=self.driver)

        obj = Object(name='foo_bar_object', size=1000, hash=None, extra={},
                     container=container,
                     meta_data=None,
                     driver=self.driver)
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
        container = Container(name='foo_bar_container', extra={},
                              driver=self.driver)
        obj = Object(name='foo_bar_object', size=1000, hash=None, extra={},
                     container=container, meta_data=None,
                     driver=self.driver)

        stream = self.driver.download_object_as_stream(
            obj=obj, chunk_size=None)
        self.assertTrue(hasattr(stream, '__iter__'))

    def test_download_object_as_stream_escaped(self):
        container = Container(name='foo & bar_container', extra={},
                              driver=self.driver)
        obj = Object(name='foo & bar_object', size=1000, hash=None, extra={},
                     container=container, meta_data=None,
                     driver=self.driver)

        stream = self.driver.download_object_as_stream(
            obj=obj, chunk_size=None)
        self.assertTrue(hasattr(stream, '__iter__'))

    def test_upload_object_success(self):
        def upload_file(self, response, file_path, chunked=False,
                        calculate_hash=True):
            return True, 'hash343hhash89h932439jsaa89', 1000

        old_func = AtmosDriver._upload_file
        AtmosDriver._upload_file = upload_file
        path = os.path.abspath(__file__)
        container = Container(name='fbc', extra={}, driver=self)
        object_name = 'ftu'
        extra = {'meta_data': {'some-value': 'foobar'}}
        obj = self.driver.upload_object(file_path=path, container=container,
                                        extra=extra, object_name=object_name)
        self.assertEqual(obj.name, 'ftu')
        self.assertEqual(obj.size, 1000)
        self.assertTrue('some-value' in obj.meta_data)
        AtmosDriver._upload_file = old_func

    def test_upload_object_no_content_type(self):
        def no_content_type(name):
            return None, None

        old_func = libcloud.utils.files.guess_file_mime_type
        libcloud.utils.files.guess_file_mime_type = no_content_type
        file_path = os.path.abspath(__file__)
        container = Container(name='fbc', extra={}, driver=self)
        object_name = 'ftu'
        obj = self.driver.upload_object(file_path=file_path,
                                        container=container,
                                        object_name=object_name)

        # Just check that the file was uploaded OK, as the fallback
        # Content-Type header should be set (application/octet-stream).
        self.assertEqual(obj.name, object_name)
        libcloud.utils.files.guess_file_mime_type = old_func

    def test_upload_object_error(self):
        def dummy_content_type(name):
            return 'application/zip', None

        def send(instance):
            raise Exception('')

        old_func1 = libcloud.utils.files.guess_file_mime_type
        libcloud.utils.files.guess_file_mime_type = dummy_content_type
        old_func2 = AtmosMockHttp.send
        AtmosMockHttp.send = send

        file_path = os.path.abspath(__file__)
        container = Container(name='fbc', extra={}, driver=self)
        object_name = 'ftu'
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
            AtmosMockHttp.send = old_func2

    def test_upload_object_nonexistent_file(self):
        def dummy_content_type(name):
            return 'application/zip', None

        old_func = libcloud.utils.files.guess_file_mime_type
        libcloud.utils.files.guess_file_mime_type = dummy_content_type

        file_path = os.path.abspath(__file__ + '.inexistent')
        container = Container(name='fbc', extra={}, driver=self)
        object_name = 'ftu'
        try:
            self.driver.upload_object(
                file_path=file_path,
                container=container,
                object_name=object_name)
        except OSError:
            pass
        else:
            self.fail('Inesitent but an exception was not thrown')
        finally:
            libcloud.utils.files.guess_file_mime_type = old_func

    def test_upload_object_via_stream_new_object(self):
        def dummy_content_type(name):
            return 'application/zip', None

        old_func = libcloud.storage.drivers.atmos.guess_file_mime_type
        libcloud.storage.drivers.atmos.guess_file_mime_type = dummy_content_type

        container = Container(name='fbc', extra={}, driver=self)
        object_name = 'ftsdn'
        iterator = DummyIterator(data=['2', '3', '5'])
        try:
            self.driver.upload_object_via_stream(container=container,
                                                 object_name=object_name,
                                                 iterator=iterator)
        finally:
            libcloud.storage.drivers.atmos.guess_file_mime_type = old_func

    def test_upload_object_via_stream_existing_object(self):
        def dummy_content_type(name):
            return 'application/zip', None

        old_func = libcloud.storage.drivers.atmos.guess_file_mime_type
        libcloud.storage.drivers.atmos.guess_file_mime_type = dummy_content_type

        container = Container(name='fbc', extra={}, driver=self)
        object_name = 'ftsde'
        iterator = DummyIterator(data=['2', '3', '5'])
        try:
            self.driver.upload_object_via_stream(container=container,
                                                 object_name=object_name,
                                                 iterator=iterator)
        finally:
            libcloud.storage.drivers.atmos.guess_file_mime_type = old_func

    def test_upload_object_via_stream_no_content_type(self):
        def no_content_type(name):
            return None, None

        old_func = libcloud.storage.drivers.atmos.guess_file_mime_type
        libcloud.storage.drivers.atmos.guess_file_mime_type = no_content_type

        container = Container(name='fbc', extra={}, driver=self)
        object_name = 'ftsdct'
        iterator = DummyIterator(data=['2', '3', '5'])
        try:
            self.driver.upload_object_via_stream(container=container,
                                                 object_name=object_name,
                                                 iterator=iterator)
        except AttributeError:
            pass
        else:
            self.fail(
                'File content type not provided'
                ' but an exception was not thrown')
        finally:
            libcloud.storage.drivers.atmos.guess_file_mime_type = old_func

    def test_signature_algorithm(self):
        test_uid = 'fredsmagicuid'
        test_key = base64.b64encode(b('ssssshhhhhmysecretkey'))
        test_date = 'Mon, 04 Jul 2011 07:39:19 GMT'
        test_values = [
            ('GET', '/rest/namespace/foo', '', {},
                'WfSASIA25TuqO2n0aO9k/dtg6S0='),
            ('GET', '/rest/namespace/foo%20%26%20bar', '', {},
                'vmlqXqcInxxoP4YX5mR09BonjX4='),
            ('POST', '/rest/namespace/foo', '', {},
                'oYKdsF+1DOuUT7iX5CJCDym2EQk='),
            ('PUT', '/rest/namespace/foo', '', {},
                'JleF9dpSWhaT3B2swZI3s41qqs4='),
            ('DELETE', '/rest/namespace/foo', '', {},
                '2IX+Bd5XZF5YY+g4P59qXV1uLpo='),
            ('GET', '/rest/namespace/foo?metata/system', '', {},
                'zuHDEAgKM1winGnWn3WBsqnz4ks='),
            ('POST', '/rest/namespace/foo?metadata/user', '', {
                'x-emc-meta': 'fakemeta=fake, othermeta=faketoo'
            }, '7sLx1nxPIRAtocfv02jz9h1BjbU='),
        ]

        class FakeDriver(object):
            path = ''

        for method, action, api_path, headers, expected in test_values:
            c = AtmosConnection(test_uid, test_key)
            c.method = method
            c.action = action
            d = FakeDriver()
            d.path = api_path
            c.driver = d
            headers = c.add_default_headers(headers)
            headers['Date'] = headers['x-emc-date'] = test_date
            self.assertEqual(c._calculate_signature({}, headers),
                             b(expected).decode('utf-8'))


class AtmosMockHttp(StorageMockHttp, unittest.TestCase):
    fixtures = StorageFileFixtures('atmos')
    upload_created = False
    upload_stream_created = False

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self)

        if kwargs.get('host', None) and kwargs.get('port', None):
            StorageMockHttp.__init__(self, *args, **kwargs)

        self._upload_object_via_stream_first_request = True

    def runTest(self):
        pass

    def request(self, method, url, body=None, headers=None, raw=False):
        headers = headers or {}
        parsed = urlparse.urlparse(url)
        if parsed.query.startswith('metadata/'):
            parsed = list(parsed)
            parsed[2] = parsed[2] + '/' + parsed[4]
            parsed[4] = ''
            url = urlparse.urlunparse(parsed)
        return super(AtmosMockHttp, self).request(method, url, body, headers,
                                                  raw)

    def _rest_namespace_EMPTY(self, method, url, body, headers):
        body = self.fixtures.load('empty_directory_listing.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _rest_namespace(self, method, url, body, headers):
        body = self.fixtures.load('list_containers.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _rest_namespace_test_container_EMPTY(self, method, url, body, headers):
        body = self.fixtures.load('empty_directory_listing.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _rest_namespace_test_container(self, method, url, body, headers):
        body = self.fixtures.load('list_containers.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _rest_namespace_test_container__metadata_system(
        self, method, url, body,
            headers):
        headers = {
            'x-emc-meta': 'objectid=b21cb59a2ba339d1afdd4810010b0a5aba2ab6b9'
        }
        return (httplib.OK, '', headers, httplib.responses[httplib.OK])

    def _rest_namespace_test_20_26_20container__metadata_system(
        self, method, url, body,
            headers):
        headers = {
            'x-emc-meta': 'objectid=b21cb59a2ba339d1afdd4810010b0a5aba2ab6b9'
        }
        return (httplib.OK, '', headers, httplib.responses[httplib.OK])

    def _rest_namespace_not_found__metadata_system(self, method, url, body,
                                                   headers):
        body = self.fixtures.load('not_found.xml')
        return (httplib.NOT_FOUND, body, {},
                httplib.responses[httplib.NOT_FOUND])

    def _rest_namespace_test_create_container(self, method, url, body, headers):
        return (httplib.OK, '', {}, httplib.responses[httplib.OK])

    def _rest_namespace_test_create_container__metadata_system(self, method,
                                                               url, body,
                                                               headers):
        headers = {
            'x-emc-meta': 'objectid=31a27b593629a3fe59f887fd973fd953e80062ce'
        }
        return (httplib.OK, '', headers, httplib.responses[httplib.OK])

    def _rest_namespace_test_create_container_ALREADY_EXISTS(self, method, url,
                                                             body, headers):
        body = self.fixtures.load('already_exists.xml')
        return (httplib.BAD_REQUEST, body, {},
                httplib.responses[httplib.BAD_REQUEST])

    def _rest_namespace_foo_bar_container(self, method, url, body, headers):
        return (httplib.OK, '', {}, httplib.responses[httplib.OK])

    def _rest_namespace_foo_bar_container_NOT_FOUND(self, method, url, body,
                                                    headers):
        body = self.fixtures.load('not_found.xml')
        return (httplib.NOT_FOUND, body, {},
                httplib.responses[httplib.NOT_FOUND])

    def _rest_namespace_foo_bar_container_NOT_EMPTY(self, method, url, body,
                                                    headers):
        body = self.fixtures.load('not_empty.xml')
        return (httplib.BAD_REQUEST, body, {},
                httplib.responses[httplib.BAD_REQUEST])

    def _rest_namespace_test_container_test_object_metadata_system(
        self, method,
        url, body,
            headers):
        meta = {
            'objectid': '322dce3763aadc41acc55ef47867b8d74e45c31d6643',
            'size': '555',
            'mtime': '2011-01-25T22:01:49Z'
        }
        headers = {
            'x-emc-meta': ', '.join([k + '=' + v for k, v in list(meta.items())])
        }
        return (httplib.OK, '', headers, httplib.responses[httplib.OK])

    def _rest_namespace_test_20_26_20container_test_20_26_20object_metadata_system(
        self, method,
        url, body,
            headers):
        meta = {
            'objectid': '322dce3763aadc41acc55ef47867b8d74e45c31d6643',
            'size': '555',
            'mtime': '2011-01-25T22:01:49Z'
        }
        headers = {
            'x-emc-meta': ', '.join([k + '=' + v for k, v in list(meta.items())])
        }
        return (httplib.OK, '', headers, httplib.responses[httplib.OK])

    def _rest_namespace_test_container_test_object_metadata_user(self, method,
                                                                 url, body,
                                                                 headers):
        meta = {
            'md5': '6b21c4a111ac178feacf9ec9d0c71f17',
            'foo-bar': 'test 1',
            'bar-foo': 'test 2',
        }
        headers = {
            'x-emc-meta': ', '.join([k + '=' + v for k, v in list(meta.items())])
        }
        return (httplib.OK, '', headers, httplib.responses[httplib.OK])

    def _rest_namespace_test_20_26_20container_test_20_26_20object_metadata_user(
        self, method,
        url, body,
            headers):
        meta = {
            'md5': '6b21c4a111ac178feacf9ec9d0c71f17',
            'foo-bar': 'test 1',
            'bar-foo': 'test 2',
        }
        headers = {
            'x-emc-meta': ', '.join([k + '=' + v for k, v in list(meta.items())])
        }
        return (httplib.OK, '', headers, httplib.responses[httplib.OK])

    def _rest_namespace_test_container_not_found_metadata_system(self, method,
                                                                 url, body,
                                                                 headers):
        body = self.fixtures.load('not_found.xml')
        return (httplib.NOT_FOUND, body, {},
                httplib.responses[httplib.NOT_FOUND])

    def _rest_namespace_foo_bar_container_foo_bar_object(self, method, url,
                                                         body, headers):
        return (httplib.OK, '', {}, httplib.responses[httplib.OK])

    def _rest_namespace_foo_20_26_20bar_container_foo_20_26_20bar_object(
        self, method, url,
            body, headers):
        return (httplib.OK, '', {}, httplib.responses[httplib.OK])

    def _rest_namespace_foo_bar_container_foo_bar_object_NOT_FOUND(
        self, method,
        url, body,
            headers):
        body = self.fixtures.load('not_found.xml')
        return (httplib.NOT_FOUND, body, {},
                httplib.responses[httplib.NOT_FOUND])

    def _rest_namespace_fbc_ftu_metadata_system(self, method, url, body,
                                                headers):
        if not self.upload_created:
            self.__class__.upload_created = True
            body = self.fixtures.load('not_found.xml')
            return (httplib.NOT_FOUND, body, {},
                    httplib.responses[httplib.NOT_FOUND])

        self.__class__.upload_created = False
        meta = {
            'objectid': '322dce3763aadc41acc55ef47867b8d74e45c31d6643',
            'size': '555',
            'mtime': '2011-01-25T22:01:49Z'
        }
        headers = {
            'x-emc-meta': ', '.join([k + '=' + v for k, v in list(meta.items())])
        }
        return (httplib.OK, '', headers, httplib.responses[httplib.OK])

    def _rest_namespace_fbc_ftu_metadata_user(self, method, url, body, headers):
        self.assertTrue('x-emc-meta' in headers)
        return (httplib.OK, '', {}, httplib.responses[httplib.OK])

    def _rest_namespace_fbc_ftsdn_metadata_system(self, method, url, body,
                                                  headers):
        if not self.upload_stream_created:
            self.__class__.upload_stream_created = True
            body = self.fixtures.load('not_found.xml')
            return (httplib.NOT_FOUND, body, {},
                    httplib.responses[httplib.NOT_FOUND])

        self.__class__.upload_stream_created = False
        meta = {
            'objectid': '322dce3763aadc41acc55ef47867b8d74e45c31d6643',
            'size': '555',
            'mtime': '2011-01-25T22:01:49Z'
        }
        headers = {
            'x-emc-meta': ', '.join([k + '=' + v for k, v in list(meta.items())])
        }
        return (httplib.OK, '', headers, httplib.responses[httplib.OK])

    def _rest_namespace_fbc_ftsdn(self, method, url, body, headers):
        if self._upload_object_via_stream_first_request:
            self.assertTrue('Range' not in headers)
            self.assertEqual(method, 'POST')
            self._upload_object_via_stream_first_request = False
        else:
            self.assertTrue('Range' in headers)
            self.assertEqual(method, 'PUT')
        return (httplib.OK, '', {}, httplib.responses[httplib.OK])

    def _rest_namespace_fbc_ftsdn_metadata_user(self, method, url, body,
                                                headers):
        self.assertTrue('x-emc-meta' in headers)
        return (httplib.OK, '', {}, httplib.responses[httplib.OK])

    def _rest_namespace_fbc_ftsde_metadata_system(self, method, url, body,
                                                  headers):
        meta = {
            'objectid': '322dce3763aadc41acc55ef47867b8d74e45c31d6643',
            'size': '555',
            'mtime': '2011-01-25T22:01:49Z'
        }
        headers = {
            'x-emc-meta': ', '.join([k + '=' + v for k, v in list(meta.items())])
        }
        return (httplib.OK, '', headers, httplib.responses[httplib.OK])

    def _rest_namespace_fbc_ftsde(self, method, url, body, headers):
        if self._upload_object_via_stream_first_request:
            self.assertTrue('Range' not in headers)
            self._upload_object_via_stream_first_request = False
        else:
            self.assertTrue('Range' in headers)
        self.assertEqual(method, 'PUT')
        return (httplib.OK, '', {}, httplib.responses[httplib.OK])

    def _rest_namespace_fbc_ftsde_metadata_user(self, method, url, body,
                                                headers):
        self.assertTrue('x-emc-meta' in headers)
        return (httplib.OK, '', {}, httplib.responses[httplib.OK])

    def _rest_namespace_fbc_ftsd_metadata_system(self, method, url, body,
                                                 headers):
        meta = {
            'objectid': '322dce3763aadc41acc55ef47867b8d74e45c31d6643',
            'size': '555',
            'mtime': '2011-01-25T22:01:49Z'
        }
        headers = {
            'x-emc-meta': ', '.join([k + '=' + v for k, v in list(meta.items())])
        }
        return (httplib.OK, '', headers, httplib.responses[httplib.OK])


class AtmosMockRawResponse(MockRawResponse):
    fixtures = StorageFileFixtures('atmos')

    def _rest_namespace_foo_bar_container_foo_bar_object(self, method, url,
                                                         body, headers):
        body = self._generate_random_data(1000)
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _rest_namespace_foo_20_26_20bar_container_foo_20_26_20bar_object(
        self, method, url,
            body, headers):
        body = self._generate_random_data(1000)
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _rest_namespace_foo_bar_container_foo_bar_object_NOT_FOUND(
        self, method,
        url, body,
            headers):
        body = self.fixtures.load('not_found.xml')
        return (httplib.NOT_FOUND, body, {},
                httplib.responses[httplib.NOT_FOUND])

    def _rest_namespace_fbc_ftu(self, method, url, body, headers):
        return (httplib.CREATED, '', {}, httplib.responses[httplib.CREATED])

if __name__ == '__main__':
    sys.exit(unittest.main())
