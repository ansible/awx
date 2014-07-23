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
import shutil
import unittest
import tempfile

import mock

from libcloud.common.types import LibcloudError
from libcloud.storage.base import Container
from libcloud.storage.types import ContainerDoesNotExistError
from libcloud.storage.types import ContainerAlreadyExistsError
from libcloud.storage.types import ContainerIsNotEmptyError
from libcloud.storage.types import InvalidContainerNameError

try:
    from libcloud.storage.drivers.local import LocalStorageDriver
    from libcloud.storage.drivers.local import LockLocalStorage
    from lockfile import LockTimeout
except ImportError:
    print('lockfile library is not available, skipping local_storage tests...')
    LocalStorageDriver = None
    LockTimeout = None


class LocalTests(unittest.TestCase):
    driver_type = LocalStorageDriver

    @classmethod
    def create_driver(self):
        self.key = tempfile.mkdtemp()
        return self.driver_type(self.key, None)

    def setUp(self):
        self.driver = self.create_driver()

    def tearDown(self):
        shutil.rmtree(self.key)
        self.key = None

    def make_tmp_file(self):
        _, tmppath = tempfile.mkstemp()

        with open(tmppath, 'w') as fp:
            fp.write('blah' * 1024)

        return tmppath

    def remove_tmp_file(self, tmppath):
        os.unlink(tmppath)

    def test_list_containers_empty(self):
        containers = self.driver.list_containers()
        self.assertEqual(len(containers), 0)

    def test_containers_success(self):
        self.driver.create_container('test1')
        self.driver.create_container('test2')
        containers = self.driver.list_containers()
        self.assertEqual(len(containers), 2)

        container = containers[1]

        self.assertTrue('creation_time' in container.extra)
        self.assertTrue('modify_time' in container.extra)
        self.assertTrue('access_time' in container.extra)

        objects = self.driver.list_container_objects(container=container)
        self.assertEqual(len(objects), 0)

        objects = container.list_objects()
        self.assertEqual(len(objects), 0)

        for container in containers:
            self.driver.delete_container(container)

    def test_objects_success(self):
        tmppath = self.make_tmp_file()
        tmpfile = open(tmppath)

        container = self.driver.create_container('test3')
        obj1 = container.upload_object(tmppath, 'object1')
        obj2 = container.upload_object(tmppath, 'path/object2')
        obj3 = container.upload_object(tmppath, 'path/to/object3')
        obj4 = container.upload_object(tmppath, 'path/to/object4.ext')
        obj5 = container.upload_object_via_stream(tmpfile, 'object5')

        objects = self.driver.list_container_objects(container=container)
        self.assertEqual(len(objects), 5)

        for obj in objects:
            self.assertNotEqual(obj.hash, None)
            self.assertEqual(obj.size, 4096)
            self.assertEqual(obj.container.name, 'test3')
            self.assertTrue('creation_time' in obj.extra)
            self.assertTrue('modify_time' in obj.extra)
            self.assertTrue('access_time' in obj.extra)

        obj1.delete()
        obj2.delete()

        objects = container.list_objects()
        self.assertEqual(len(objects), 3)

        container.delete_object(obj3)
        container.delete_object(obj4)
        container.delete_object(obj5)

        objects = container.list_objects()
        self.assertEqual(len(objects), 0)

        container.delete()
        tmpfile.close()
        self.remove_tmp_file(tmppath)

    def test_get_container_doesnt_exist(self):
        try:
            self.driver.get_container(container_name='container1')
        except ContainerDoesNotExistError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_get_container_success(self):
        self.driver.create_container('test4')
        container = self.driver.get_container(container_name='test4')
        self.assertTrue(container.name, 'test4')
        container.delete()

    def test_get_object_container_doesnt_exist(self):
        try:
            self.driver.get_object(container_name='test-inexistent',
                                   object_name='test')
        except ContainerDoesNotExistError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_get_object_success(self):
        tmppath = self.make_tmp_file()
        container = self.driver.create_container('test5')
        container.upload_object(tmppath, 'test')

        obj = self.driver.get_object(container_name='test5',
                                     object_name='test')

        self.assertEqual(obj.name, 'test')
        self.assertEqual(obj.container.name, 'test5')
        self.assertEqual(obj.size, 4096)
        self.assertNotEqual(obj.hash, None)
        self.assertTrue('creation_time' in obj.extra)
        self.assertTrue('modify_time' in obj.extra)
        self.assertTrue('access_time' in obj.extra)

        obj.delete()
        container.delete()
        self.remove_tmp_file(tmppath)

    def test_create_container_invalid_name(self):
        try:
            self.driver.create_container(container_name='new/container')
        except InvalidContainerNameError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_create_container_already_exists(self):
        container = self.driver.create_container(
            container_name='new-container')
        try:
            self.driver.create_container(container_name='new-container')
        except ContainerAlreadyExistsError:
            pass
        else:
            self.fail('Exception was not thrown')

        # success
        self.driver.delete_container(container)

    def test_create_container_success(self):
        name = 'new_container'
        container = self.driver.create_container(container_name=name)
        self.assertEqual(container.name, name)
        self.driver.delete_container(container)

    def test_delete_container_doesnt_exist(self):
        container = Container(name='new_container', extra=None,
                              driver=self.driver)
        try:
            self.driver.delete_container(container=container)
        except ContainerDoesNotExistError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_delete_container_not_empty(self):
        tmppath = self.make_tmp_file()
        container = self.driver.create_container('test6')
        obj = container.upload_object(tmppath, 'test')

        try:
            self.driver.delete_container(container=container)
        except ContainerIsNotEmptyError:
            pass
        else:
            self.fail('Exception was not thrown')

        # success
        obj.delete()
        self.remove_tmp_file(tmppath)
        self.assertTrue(self.driver.delete_container(container=container))

    def test_delete_container_not_found(self):
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
        container = self.driver.create_container('test7')
        self.assertTrue(self.driver.delete_container(container=container))

    def test_download_object_success(self):
        tmppath = self.make_tmp_file()
        container = self.driver.create_container('test6')
        obj = container.upload_object(tmppath, 'test')

        destination_path = tmppath + '.temp'
        result = self.driver.download_object(obj=obj,
                                             destination_path=destination_path,
                                             overwrite_existing=False,
                                             delete_on_failure=True)

        self.assertTrue(result)

        obj.delete()
        container.delete()
        self.remove_tmp_file(tmppath)
        os.unlink(destination_path)

    def test_download_object_and_overwrite(self):
        tmppath = self.make_tmp_file()
        container = self.driver.create_container('test6')
        obj = container.upload_object(tmppath, 'test')

        destination_path = tmppath + '.temp'
        result = self.driver.download_object(obj=obj,
                                             destination_path=destination_path,
                                             overwrite_existing=False,
                                             delete_on_failure=True)

        self.assertTrue(result)

        try:
            self.driver.download_object(obj=obj,
                                        destination_path=destination_path,
                                        overwrite_existing=False,
                                        delete_on_failure=True)
        except LibcloudError:
            pass
        else:
            self.fail('Exception was not thrown')

        result = self.driver.download_object(obj=obj,
                                             destination_path=destination_path,
                                             overwrite_existing=True,
                                             delete_on_failure=True)

        self.assertTrue(result)

        # success
        obj.delete()
        container.delete()
        self.remove_tmp_file(tmppath)
        os.unlink(destination_path)

    def test_download_object_as_stream_success(self):
        tmppath = self.make_tmp_file()
        container = self.driver.create_container('test6')
        obj = container.upload_object(tmppath, 'test')

        stream = self.driver.download_object_as_stream(obj=obj,
                                                       chunk_size=1024)

        self.assertTrue(hasattr(stream, '__iter__'))

        data = ''
        for buff in stream:
            data += buff.decode('utf-8')

        self.assertTrue(len(data), 4096)

        obj.delete()
        container.delete()
        self.remove_tmp_file(tmppath)

    @mock.patch("lockfile.mkdirlockfile.MkdirLockFile.acquire",
                mock.MagicMock(side_effect=LockTimeout))
    def test_proper_lockfile_imports(self):
        # LockLocalStorage was previously using an un-imported exception
        # in its __enter__ method, so the following would raise a NameError.
        lls = LockLocalStorage("blah")
        self.assertRaises(LibcloudError, lls.__enter__)


if not LocalStorageDriver:
    class LocalTests(unittest.TestCase):  # NOQA
        pass


if __name__ == '__main__':
    sys.exit(unittest.main())
