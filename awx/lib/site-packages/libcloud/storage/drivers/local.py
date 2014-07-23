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

"""
Provides storage driver for working with local filesystem
"""

from __future__ import with_statement

import errno
import os
import shutil
import sys

try:
    import lockfile
    from lockfile import LockTimeout, mkdirlockfile
except ImportError:
    raise ImportError('Missing lockfile dependency, you can install it '
                      'using pip: pip install lockfile')

from libcloud.utils.files import read_in_chunks
from libcloud.utils.py3 import relpath
from libcloud.utils.py3 import u
from libcloud.common.base import Connection
from libcloud.storage.base import Object, Container, StorageDriver
from libcloud.common.types import LibcloudError
from libcloud.storage.types import ContainerAlreadyExistsError
from libcloud.storage.types import ContainerDoesNotExistError
from libcloud.storage.types import ContainerIsNotEmptyError
from libcloud.storage.types import ObjectError
from libcloud.storage.types import ObjectDoesNotExistError
from libcloud.storage.types import InvalidContainerNameError

IGNORE_FOLDERS = ['.lock', '.hash']


class LockLocalStorage(object):
    """
    A class to help in locking a local path before being updated
    """
    def __init__(self, path):
        self.path = path
        self.lock = mkdirlockfile.MkdirLockFile(self.path, threaded=True)

    def __enter__(self):
        try:
            self.lock.acquire(timeout=0.1)
        except LockTimeout:
            raise LibcloudError('Lock timeout')

    def __exit__(self, type, value, traceback):
        if self.lock.is_locked():
            self.lock.release()

        if value is not None:
            raise value


class LocalStorageDriver(StorageDriver):
    """
    Implementation of local file-system based storage. This is helpful
    where the user would want to use the same code (using libcloud) and
    switch between cloud storage and local storage
    """

    connectionCls = Connection
    name = 'Local Storage'
    website = 'http://example.com'
    hash_type = 'md5'

    def __init__(self, key, secret=None, secure=True, host=None, port=None,
                 **kwargs):

        # Use the key as the path to the storage
        self.base_path = key

        if not os.path.isdir(self.base_path):
            raise LibcloudError('The base path is not a directory')

        super(StorageDriver, self).__init__(key=key, secret=secret,
                                            secure=secure, host=host,
                                            port=port, **kwargs)

    def _make_path(self, path, ignore_existing=True):
        """
        Create a path by checking if it already exists
        """

        try:
            os.makedirs(path)
        except OSError:
            exp = sys.exc_info()[1]
            if exp.errno == errno.EEXIST and not ignore_existing:
                raise exp

    def _check_container_name(self, container_name):
        """
        Check if the container name is valid

        :param container_name: Container name
        :type container_name: ``str``
        """

        if '/' in container_name or '\\' in container_name:
            raise InvalidContainerNameError(value=None, driver=self,
                                            container_name=container_name)

    def _make_container(self, container_name):
        """
        Create a container instance

        :param container_name: Container name.
        :type container_name: ``str``

        :return: Container instance.
        :rtype: :class:`Container`
        """

        self._check_container_name(container_name)

        full_path = os.path.join(self.base_path, container_name)

        try:
            stat = os.stat(full_path)
            if not os.path.isdir(full_path):
                raise OSError('Target path is not a directory')
        except OSError:
            raise ContainerDoesNotExistError(value=None, driver=self,
                                             container_name=container_name)

        extra = {}
        extra['creation_time'] = stat.st_ctime
        extra['access_time'] = stat.st_atime
        extra['modify_time'] = stat.st_mtime

        return Container(name=container_name, extra=extra, driver=self)

    def _make_object(self, container, object_name):
        """
        Create an object instance

        :param container: Container.
        :type container: :class:`Container`

        :param object_name: Object name.
        :type object_name: ``str``

        :return: Object instance.
        :rtype: :class:`Object`
        """

        full_path = os.path.join(self.base_path, container.name, object_name)

        if os.path.isdir(full_path):
            raise ObjectError(value=None, driver=self, object_name=object_name)

        try:
            stat = os.stat(full_path)
        except Exception:
            raise ObjectDoesNotExistError(value=None, driver=self,
                                          object_name=object_name)

        # Make a hash for the file based on the metadata. We can safely
        # use only the mtime attribute here. If the file contents change,
        # the underlying file-system will change mtime
        data_hash = self._get_hash_function()
        data_hash.update(u(stat.st_mtime).encode('ascii'))
        data_hash = data_hash.hexdigest()

        extra = {}
        extra['creation_time'] = stat.st_ctime
        extra['access_time'] = stat.st_atime
        extra['modify_time'] = stat.st_mtime

        return Object(name=object_name, size=stat.st_size, extra=extra,
                      driver=self, container=container, hash=data_hash,
                      meta_data=None)

    def iterate_containers(self):
        """
        Return a generator of containers.

        :return: A generator of Container instances.
        :rtype: ``generator`` of :class:`Container`
        """

        for container_name in os.listdir(self.base_path):
            full_path = os.path.join(self.base_path, container_name)
            if not os.path.isdir(full_path):
                continue
            yield self._make_container(container_name)

    def _get_objects(self, container):
        """
        Recursively iterate through the file-system and return the object names
        """

        cpath = self.get_container_cdn_url(container, check=True)

        for folder, subfolders, files in os.walk(cpath, topdown=True):
            # Remove unwanted subfolders
            for subf in IGNORE_FOLDERS:
                if subf in subfolders:
                    subfolders.remove(subf)

            for name in files:
                full_path = os.path.join(folder, name)
                object_name = relpath(full_path, start=cpath)
                yield self._make_object(container, object_name)

    def iterate_container_objects(self, container):
        """
        Returns a generator of objects for the given container.

        :param container: Container instance
        :type container: :class:`Container`

        :return: A generator of Object instances.
        :rtype: ``generator`` of :class:`Object`
        """

        return self._get_objects(container)

    def get_container(self, container_name):
        """
        Return a container instance.

        :param container_name: Container name.
        :type container_name: ``str``

        :return: :class:`Container` instance.
        :rtype: :class:`Container`
        """
        return self._make_container(container_name)

    def get_container_cdn_url(self, container, check=False):
        """
        Return a container CDN URL.

        :param container: Container instance
        :type  container: :class:`Container`

        :param check: Indicates if the path's existence must be checked
        :type check: ``bool``

        :return: A CDN URL for this container.
        :rtype: ``str``
        """
        path = os.path.join(self.base_path, container.name)

        if check and not os.path.isdir(path):
            raise ContainerDoesNotExistError(value=None, driver=self,
                                             container_name=container.name)

        return path

    def get_object(self, container_name, object_name):
        """
        Return an object instance.

        :param container_name: Container name.
        :type  container_name: ``str``

        :param object_name: Object name.
        :type  object_name: ``str``

        :return: :class:`Object` instance.
        :rtype: :class:`Object`
        """
        container = self._make_container(container_name)
        return self._make_object(container, object_name)

    def get_object_cdn_url(self, obj):
        """
        Return a object CDN URL.

        :param obj: Object instance
        :type  obj: :class:`Object`

        :return: A CDN URL for this object.
        :rtype: ``str``
        """
        return os.path.join(self.base_path, obj.container.name, obj.name)

    def enable_container_cdn(self, container):
        """
        Enable container CDN.

        :param container: Container instance
        :type  container: :class:`Container`

        :rtype: ``bool``
        """

        path = self.get_container_cdn_url(container)
        lockfile.MkdirFileLock(path, threaded=True)

        with LockLocalStorage(path):
            self._make_path(path)

        return True

    def enable_object_cdn(self, obj):
        """
        Enable object CDN.

        :param obj: Object instance
        :type  obj: :class:`Object`

        :rtype: ``bool``
        """
        path = self.get_object_cdn_url(obj)

        with LockLocalStorage(path):
            if os.path.exists(path):
                return False
            try:
                obj_file = open(path, 'w')
                obj_file.close()
            except:
                return False

        return True

    def download_object(self, obj, destination_path, overwrite_existing=False,
                        delete_on_failure=True):
        """
        Download an object to the specified destination path.

        :param obj: Object instance.
        :type obj: :class:`Object`

        :param destination_path: Full path to a file or a directory where the
                                incoming file will be saved.
        :type destination_path: ``str``

        :param overwrite_existing: True to overwrite an existing file,
            defaults to False.
        :type overwrite_existing: ``bool``

        :param delete_on_failure: True to delete a partially downloaded file if
        the download was not successful (hash mismatch / file size).
        :type delete_on_failure: ``bool``

        :return: True if an object has been successfully downloaded, False
        otherwise.
        :rtype: ``bool``
        """

        obj_path = self.get_object_cdn_url(obj)
        base_name = os.path.basename(destination_path)

        if not base_name and not os.path.exists(destination_path):
            raise LibcloudError(
                value='Path %s does not exist' % (destination_path),
                driver=self)

        if not base_name:
            file_path = os.path.join(destination_path, obj.name)
        else:
            file_path = destination_path

        if os.path.exists(file_path) and not overwrite_existing:
            raise LibcloudError(
                value='File %s already exists, but ' % (file_path) +
                'overwrite_existing=False',
                driver=self)

        try:
            shutil.copy(obj_path, file_path)
        except IOError:
            if delete_on_failure:
                try:
                    os.unlink(file_path)
                except Exception:
                    pass
            return False

        return True

    def download_object_as_stream(self, obj, chunk_size=None):
        """
        Return a generator which yields object data.

        :param obj: Object instance
        :type obj: :class:`Object`

        :param chunk_size: Optional chunk size (in bytes).
        :type chunk_size: ``int``

        :rtype: ``object``
        """

        path = self.get_object_cdn_url(obj)

        with open(path) as obj_file:
            for data in read_in_chunks(obj_file, chunk_size=chunk_size):
                yield data

    def upload_object(self, file_path, container, object_name, extra=None,
                      verify_hash=True):
        """
        Upload an object currently located on a disk.

        :param file_path: Path to the object on disk.
        :type file_path: ``str``

        :param container: Destination container.
        :type container: :class:`Container`

        :param object_name: Object name.
        :type object_name: ``str``

        :param verify_hash: Verify hast
        :type verify_hash: ``bool``

        :param extra: (optional) Extra attributes (driver specific).
        :type extra: ``dict``

        :rtype: ``object``
        """

        path = self.get_container_cdn_url(container, check=True)
        obj_path = os.path.join(path, object_name)
        base_path = os.path.dirname(obj_path)

        self._make_path(base_path)

        with LockLocalStorage(obj_path):
            shutil.copy(file_path, obj_path)

        os.chmod(obj_path, int('664', 8))

        return self._make_object(container, object_name)

    def upload_object_via_stream(self, iterator, container,
                                 object_name,
                                 extra=None):
        """
        Upload an object using an iterator.

        If a provider supports it, chunked transfer encoding is used and you
        don't need to know in advance the amount of data to be uploaded.

        Otherwise if a provider doesn't support it, iterator will be exhausted
        so a total size for data to be uploaded can be determined.

        Note: Exhausting the iterator means that the whole data must be
        buffered in memory which might result in memory exhausting when
        uploading a very large object.

        If a file is located on a disk you are advised to use upload_object
        function which uses fs.stat function to determine the file size and it
        doesn't need to buffer whole object in the memory.

        :type iterator: ``object``
        :param iterator: An object which implements the iterator interface.

        :type container: :class:`Container`
        :param container: Destination container.

        :type object_name: ``str``
        :param object_name: Object name.

        :type extra: ``dict``
        :param extra: (optional) Extra attributes (driver specific). Note:
            This dictionary must contain a 'content_type' key which represents
            a content type of the stored object.

        :rtype: ``object``
        """

        path = self.get_container_cdn_url(container, check=True)
        obj_path = os.path.join(path, object_name)
        base_path = os.path.dirname(obj_path)

        self._make_path(base_path)

        with LockLocalStorage(obj_path):
            obj_file = open(obj_path, 'w')
            for data in iterator:
                obj_file.write(data)

            obj_file.close()

        os.chmod(obj_path, int('664', 8))

        return self._make_object(container, object_name)

    def delete_object(self, obj):
        """
        Delete an object.

        :type obj: :class:`Object`
        :param obj: Object instance.

        :return: ``bool`` True on success.
        :rtype: ``bool``
        """

        path = self.get_object_cdn_url(obj)

        with LockLocalStorage(path):
            try:
                os.unlink(path)
            except Exception:
                return False

        # Check and delete all the empty parent folders
        path = os.path.dirname(path)
        container_url = obj.container.get_cdn_url()

        # Delete the empty parent folders till the container's level
        while path != container_url:
            try:
                os.rmdir(path)
            except OSError:
                exp = sys.exc_info()[1]
                if exp.errno == errno.ENOTEMPTY:
                    break
                raise exp

            path = os.path.dirname(path)

        return True

    def create_container(self, container_name):
        """
        Create a new container.

        :type container_name: ``str``
        :param container_name: Container name.

        :return: :class:`Container` instance on success.
        :rtype: :class:`Container`
        """

        self._check_container_name(container_name)

        path = os.path.join(self.base_path, container_name)

        try:
            self._make_path(path, ignore_existing=False)
        except OSError:
            exp = sys.exc_info()[1]
            if exp.errno == errno.EEXIST:
                raise ContainerAlreadyExistsError(
                    value='Container with this name already exists. The name '
                          'must be unique among all the containers in the '
                          'system',
                    container_name=container_name, driver=self)
            else:
                raise LibcloudError(
                    'Error creating container %s' % container_name,
                    driver=self)
        except Exception:
            raise LibcloudError(
                'Error creating container %s' % container_name, driver=self)

        return self._make_container(container_name)

    def delete_container(self, container):
        """
        Delete a container.

        :type container: :class:`Container`
        :param container: Container instance

        :return: True on success, False otherwise.
        :rtype: ``bool``
        """

        # Check if there are any objects inside this
        for obj in self._get_objects(container):
            raise ContainerIsNotEmptyError(value='Container is not empty',
                                           container_name=container.name,
                                           driver=self)

        path = self.get_container_cdn_url(container, check=True)

        with LockLocalStorage(path):
            try:
                shutil.rmtree(path)
            except Exception:
                return False

        return True
