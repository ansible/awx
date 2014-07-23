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

import base64
import os
import binascii

from xml.etree.ElementTree import Element, SubElement

from libcloud.utils.py3 import PY3
from libcloud.utils.py3 import httplib
from libcloud.utils.py3 import urlquote
from libcloud.utils.py3 import tostring
from libcloud.utils.py3 import b

from libcloud.utils.xml import fixxpath
from libcloud.utils.files import read_in_chunks
from libcloud.common.types import LibcloudError
from libcloud.common.azure import AzureConnection

from libcloud.storage.base import Object, Container, StorageDriver
from libcloud.storage.types import ContainerIsNotEmptyError
from libcloud.storage.types import ContainerAlreadyExistsError
from libcloud.storage.types import InvalidContainerNameError
from libcloud.storage.types import ContainerDoesNotExistError
from libcloud.storage.types import ObjectDoesNotExistError
from libcloud.storage.types import ObjectHashMismatchError

if PY3:
    from io import FileIO as file

# Desired number of items in each response inside a paginated request
RESPONSES_PER_REQUEST = 100

# As per the Azure documentation, if the upload file size is less than
# 64MB, we can upload it in a single request. However, in real life azure
# servers seem to disconnect randomly after around 5 MB or 200s of upload.
# So, it is better that for file sizes greater than 4MB, we upload it in
# chunks.
# Also, with large sizes, if we use a lease, the lease will timeout after
# 60 seconds, but the upload might still be in progress. This can be
# handled in code, but if we use chunked uploads, the lease renewal will
# happen automatically.
AZURE_BLOCK_MAX_SIZE = 4 * 1024 * 1024

# Azure block blocks must be maximum 4MB
# Azure page blobs must be aligned in 512 byte boundaries (4MB fits that)
AZURE_CHUNK_SIZE = 4 * 1024 * 1024

# Azure page blob must be aligned in 512 byte boundaries
AZURE_PAGE_CHUNK_SIZE = 512

# The time period (in seconds) for which a lease must be obtained.
# If set as -1, we get an infinite lease, but that is a bad idea. If
# after getting an infinite lease, there was an issue in releasing the
# lease, the object will remain 'locked' forever, unless the lease is
# released using the lease_id (which is not exposed to the user)
AZURE_LEASE_PERIOD = 60

AZURE_STORAGE_HOST_SUFFIX = 'blob.core.windows.net'


class AzureBlobLease(object):
    """
    A class to help in leasing an azure blob and renewing the lease
    """
    def __init__(self, driver, object_path, use_lease):
        """
        :param driver: The Azure storage driver that is being used
        :type driver: :class:`AzureStorageDriver`

        :param object_path: The path of the object we need to lease
        :type object_path: ``str``

        :param use_lease: Indicates if we must take a lease or not
        :type use_lease: ``bool``
        """
        self.object_path = object_path
        self.driver = driver
        self.use_lease = use_lease
        self.lease_id = None
        self.params = {'comp': 'lease'}

    def renew(self):
        """
        Renew the lease if it is older than a predefined time period
        """
        if self.lease_id is None:
            return

        headers = {'x-ms-lease-action': 'renew',
                   'x-ms-lease-id': self.lease_id,
                   'x-ms-lease-duration': '60'}

        response = self.driver.connection.request(self.object_path,
                                                  headers=headers,
                                                  params=self.params,
                                                  method='PUT')

        if response.status != httplib.OK:
            raise LibcloudError('Unable to obtain lease', driver=self)

    def update_headers(self, headers):
        """
        Update the lease id in the headers
        """
        if self.lease_id:
            headers['x-ms-lease-id'] = self.lease_id

    def __enter__(self):
        if not self.use_lease:
            return self

        headers = {'x-ms-lease-action': 'acquire',
                   'x-ms-lease-duration': '60'}

        response = self.driver.connection.request(self.object_path,
                                                  headers=headers,
                                                  params=self.params,
                                                  method='PUT')

        if response.status == httplib.NOT_FOUND:
            return self
        elif response.status != httplib.CREATED:
            raise LibcloudError('Unable to obtain lease', driver=self)

        self.lease_id = response.headers['x-ms-lease-id']
        return self

    def __exit__(self, type, value, traceback):
        if self.lease_id is None:
            return

        headers = {'x-ms-lease-action': 'release',
                   'x-ms-lease-id': self.lease_id}
        response = self.driver.connection.request(self.object_path,
                                                  headers=headers,
                                                  params=self.params,
                                                  method='PUT')

        if response.status != httplib.OK:
            raise LibcloudError('Unable to release lease', driver=self)


class AzureBlobsConnection(AzureConnection):
    """
    Represents a single connection to Azure Blobs
    """


class AzureBlobsStorageDriver(StorageDriver):
    name = 'Microsoft Azure (blobs)'
    website = 'http://windows.azure.com/'
    connectionCls = AzureBlobsConnection
    hash_type = 'md5'
    supports_chunked_encoding = False
    ex_blob_type = 'BlockBlob'

    def __init__(self, key, secret=None, secure=True, host=None, port=None,
                 **kwargs):
        self._host_argument_set = bool(host)

        # B64decode() this key and keep it, so that we don't have to do
        # so for every request. Minor performance improvement
        secret = base64.b64decode(b(secret))

        super(AzureBlobsStorageDriver, self).__init__(key=key, secret=secret,
                                                      secure=secure, host=host,
                                                      port=port, **kwargs)

    def _ex_connection_class_kwargs(self):
        result = {}

        # host argument has precedence
        if not self._host_argument_set:
            result['host'] = '%s.%s' % (self.key, AZURE_STORAGE_HOST_SUFFIX)

        return result

    def _xml_to_container(self, node):
        """
        Converts a container XML node to a container instance

        :param node: XML info of the container
        :type node: :class:`xml.etree.ElementTree.Element`

        :return: A container instance
        :rtype: :class:`Container`
        """

        name = node.findtext(fixxpath(xpath='Name'))
        props = node.find(fixxpath(xpath='Properties'))
        metadata = node.find(fixxpath(xpath='Metadata'))

        extra = {
            'url': node.findtext(fixxpath(xpath='Url')),
            'last_modified': node.findtext(fixxpath(xpath='Last-Modified')),
            'etag': props.findtext(fixxpath(xpath='Etag')),
            'lease': {
                'status': props.findtext(fixxpath(xpath='LeaseStatus')),
                'state': props.findtext(fixxpath(xpath='LeaseState')),
                'duration': props.findtext(fixxpath(xpath='LeaseDuration')),
            },
            'meta_data': {}
        }

        for meta in metadata.getchildren():
            extra['meta_data'][meta.tag] = meta.text

        return Container(name=name, extra=extra, driver=self)

    def _response_to_container(self, container_name, response):
        """
        Converts a HTTP response to a container instance

        :param container_name: Name of the container
        :type container_name: ``str``

        :param response: HTTP Response
        :type node: L{}

        :return: A container instance
        :rtype: :class:`Container`
        """

        headers = response.headers
        extra = {
            'url': 'http://%s%s' % (response.connection.host,
                                    response.connection.action),
            'etag': headers['etag'],
            'last_modified': headers['last-modified'],
            'lease': {
                'status': headers.get('x-ms-lease-status', None),
                'state': headers.get('x-ms-lease-state', None),
                'duration': headers.get('x-ms-lease-duration', None),
            },
            'meta_data': {}
        }

        for key, value in response.headers.items():
            if key.startswith('x-ms-meta-'):
                key = key.split('x-ms-meta-')[1]
                extra['meta_data'][key] = value

        return Container(name=container_name, extra=extra, driver=self)

    def _xml_to_object(self, container, blob):
        """
        Converts a BLOB XML node to an object instance

        :param container: Instance of the container holding the blob
        :type: :class:`Container`

        :param blob: XML info of the blob
        :type blob: L{}

        :return: An object instance
        :rtype: :class:`Object`
        """

        name = blob.findtext(fixxpath(xpath='Name'))
        props = blob.find(fixxpath(xpath='Properties'))
        metadata = blob.find(fixxpath(xpath='Metadata'))
        etag = props.findtext(fixxpath(xpath='Etag'))
        size = int(props.findtext(fixxpath(xpath='Content-Length')))

        extra = {
            'content_type': props.findtext(fixxpath(xpath='Content-Type')),
            'etag': etag,
            'md5_hash': props.findtext(fixxpath(xpath='Content-MD5')),
            'last_modified': props.findtext(fixxpath(xpath='Last-Modified')),
            'url': blob.findtext(fixxpath(xpath='Url')),
            'hash': props.findtext(fixxpath(xpath='Etag')),
            'lease': {
                'status': props.findtext(fixxpath(xpath='LeaseStatus')),
                'state': props.findtext(fixxpath(xpath='LeaseState')),
                'duration': props.findtext(fixxpath(xpath='LeaseDuration')),
            },
            'content_encoding': props.findtext(fixxpath(
                                               xpath='Content-Encoding')),
            'content_language': props.findtext(fixxpath(
                                               xpath='Content-Language')),
            'blob_type': props.findtext(fixxpath(xpath='BlobType'))
        }

        if extra['md5_hash']:
            value = binascii.hexlify(base64.b64decode(b(extra['md5_hash'])))
            value = value.decode('ascii')
            extra['md5_hash'] = value

        meta_data = {}
        for meta in metadata.getchildren():
            meta_data[meta.tag] = meta.text

        return Object(name=name, size=size, hash=etag, meta_data=meta_data,
                      extra=extra, container=container, driver=self)

    def _response_to_object(self, object_name, container, response):
        """
        Converts a HTTP response to an object (from headers)

        :param object_name: Name of the object
        :type object_name: ``str``

        :param container: Instance of the container holding the blob
        :type: :class:`Container`

        :param response: HTTP Response
        :type node: L{}

        :return: An object instance
        :rtype: :class:`Object`
        """

        headers = response.headers
        size = int(headers['content-length'])
        etag = headers['etag']

        extra = {
            'url': 'http://%s%s' % (response.connection.host,
                                    response.connection.action),
            'etag': etag,
            'md5_hash': headers.get('content-md5', None),
            'content_type': headers.get('content-type', None),
            'content_language': headers.get('content-language', None),
            'content_encoding': headers.get('content-encoding', None),
            'last_modified': headers['last-modified'],
            'lease': {
                'status': headers.get('x-ms-lease-status', None),
                'state': headers.get('x-ms-lease-state', None),
                'duration': headers.get('x-ms-lease-duration', None),
            },
            'blob_type': headers['x-ms-blob-type']
        }

        if extra['md5_hash']:
            value = binascii.hexlify(base64.b64decode(b(extra['md5_hash'])))
            value = value.decode('ascii')
            extra['md5_hash'] = value

        meta_data = {}
        for key, value in response.headers.items():
            if key.startswith('x-ms-meta-'):
                key = key.split('x-ms-meta-')[1]
                meta_data[key] = value

        return Object(name=object_name, size=size, hash=etag, extra=extra,
                      meta_data=meta_data, container=container, driver=self)

    def iterate_containers(self):
        """
        @inherits: :class:`StorageDriver.iterate_containers`
        """
        params = {'comp': 'list',
                  'maxresults': RESPONSES_PER_REQUEST,
                  'include': 'metadata'}

        while True:
            response = self.connection.request('/', params)
            if response.status != httplib.OK:
                raise LibcloudError('Unexpected status code: %s' %
                                    (response.status), driver=self)

            body = response.parse_body()
            containers = body.find(fixxpath(xpath='Containers'))
            containers = containers.findall(fixxpath(xpath='Container'))

            for container in containers:
                yield self._xml_to_container(container)

            params['marker'] = body.findtext('NextMarker')
            if not params['marker']:
                break

    def iterate_container_objects(self, container):
        """
        @inherits: :class:`StorageDriver.iterate_container_objects`
        """
        params = {'restype': 'container',
                  'comp': 'list',
                  'maxresults': RESPONSES_PER_REQUEST,
                  'include': 'metadata'}

        container_path = self._get_container_path(container)

        while True:
            response = self.connection.request(container_path,
                                               params=params)

            if response.status == httplib.NOT_FOUND:
                raise ContainerDoesNotExistError(value=None,
                                                 driver=self,
                                                 container_name=container.name)

            elif response.status != httplib.OK:
                raise LibcloudError('Unexpected status code: %s' %
                                    (response.status), driver=self)

            body = response.parse_body()
            blobs = body.find(fixxpath(xpath='Blobs'))
            blobs = blobs.findall(fixxpath(xpath='Blob'))

            for blob in blobs:
                yield self._xml_to_object(container, blob)

            params['marker'] = body.findtext('NextMarker')
            if not params['marker']:
                break

    def get_container(self, container_name):
        """
        @inherits: :class:`StorageDriver.get_container`
        """
        params = {'restype': 'container'}

        container_path = '/%s' % (container_name)

        response = self.connection.request(container_path, params=params,
                                           method='HEAD')

        if response.status == httplib.NOT_FOUND:
            raise ContainerDoesNotExistError('Container %s does not exist' %
                                             (container_name), driver=self,
                                             container_name=container_name)
        elif response.status != httplib.OK:
            raise LibcloudError('Unexpected status code: %s' %
                                (response.status), driver=self)

        return self._response_to_container(container_name, response)

    def get_object(self, container_name, object_name):
        """
        @inherits: :class:`StorageDriver.get_object`
        """

        container = self.get_container(container_name=container_name)
        object_path = self._get_object_path(container, object_name)

        response = self.connection.request(object_path, method='HEAD')

        if response.status == httplib.OK:
            obj = self._response_to_object(object_name, container, response)
            return obj

        raise ObjectDoesNotExistError(value=None, driver=self,
                                      object_name=object_name)

    def _get_container_path(self, container):
        """
        Return a container path

        :param container: Container instance
        :type  container: :class:`Container`

        :return: A path for this container.
        :rtype: ``str``
        """
        return '/%s' % (container.name)

    def _get_object_path(self, container, object_name):
        """
        Return an object's CDN path.

        :param container: Container instance
        :type  container: :class:`Container`

        :param object_name: Object name
        :type  object_name: :class:`str`

        :return: A  path for this object.
        :rtype: ``str``
        """
        container_url = self._get_container_path(container)
        object_name_cleaned = urlquote(object_name)
        object_path = '%s/%s' % (container_url, object_name_cleaned)
        return object_path

    def create_container(self, container_name):
        """
        @inherits: :class:`StorageDriver.create_container`
        """
        params = {'restype': 'container'}

        container_path = '/%s' % (container_name)
        response = self.connection.request(container_path, params=params,
                                           method='PUT')

        if response.status == httplib.CREATED:
            return self._response_to_container(container_name, response)
        elif response.status == httplib.CONFLICT:
            raise ContainerAlreadyExistsError(
                value='Container with this name already exists. The name must '
                      'be unique among all the containers in the system',
                container_name=container_name, driver=self)
        elif response.status == httplib.BAD_REQUEST:
            raise InvalidContainerNameError(value='Container name contains ' +
                                            'invalid characters.',
                                            container_name=container_name,
                                            driver=self)

        raise LibcloudError('Unexpected status code: %s' % (response.status),
                            driver=self)

    def delete_container(self, container):
        """
        @inherits: :class:`StorageDriver.delete_container`
        """
        # Azure does not check if the container is empty. So, we will do
        # a check to ensure that the behaviour is similar to other drivers
        for obj in container.iterate_objects():
            raise ContainerIsNotEmptyError(
                value='Container must be empty before it can be deleted.',
                container_name=container.name, driver=self)

        params = {'restype': 'container'}
        container_path = self._get_container_path(container)

        # Note: All the objects in the container must be deleted first
        response = self.connection.request(container_path, params=params,
                                           method='DELETE')

        if response.status == httplib.ACCEPTED:
            return True
        elif response.status == httplib.NOT_FOUND:
            raise ContainerDoesNotExistError(value=None,
                                             driver=self,
                                             container_name=container.name)

        return False

    def download_object(self, obj, destination_path, overwrite_existing=False,
                        delete_on_failure=True):
        """
        @inherits: :class:`StorageDriver.download_object`
        """
        obj_path = self._get_object_path(obj.container, obj.name)
        response = self.connection.request(obj_path, raw=True, data=None)

        return self._get_object(obj=obj, callback=self._save_object,
                                response=response,
                                callback_kwargs={
                                    'obj': obj,
                                    'response': response.response,
                                    'destination_path': destination_path,
                                    'overwrite_existing': overwrite_existing,
                                    'delete_on_failure': delete_on_failure},
                                success_status_code=httplib.OK)

    def download_object_as_stream(self, obj, chunk_size=None):
        """
        @inherits: :class:`StorageDriver.download_object_as_stream`
        """
        obj_path = self._get_object_path(obj.container, obj.name)
        response = self.connection.request(obj_path, raw=True, data=None)

        return self._get_object(obj=obj, callback=read_in_chunks,
                                response=response,
                                callback_kwargs={'iterator': response.response,
                                                 'chunk_size': chunk_size},
                                success_status_code=httplib.OK)

    def _upload_in_chunks(self, response, data, iterator, object_path,
                          blob_type, lease, calculate_hash=True):
        """
        Uploads data from an interator in fixed sized chunks to S3

        :param response: Response object from the initial POST request
        :type response: :class:`RawResponse`

        :param data: Any data from the initial POST request
        :type data: ``str``

        :param iterator: The generator for fetching the upload data
        :type iterator: ``generator``

        :param object_path: The path of the object to which we are uploading
        :type object_name: ``str``

        :param blob_type: The blob type being uploaded
        :type blob_type: ``str``

        :param lease: The lease object to be used for renewal
        :type lease: :class:`AzureBlobLease`

        :keyword calculate_hash: Indicates if we must calculate the data hash
        :type calculate_hash: ``bool``

        :return: A tuple of (status, checksum, bytes transferred)
        :rtype: ``tuple``
        """

        # Get the upload id from the response xml
        if response.status != httplib.CREATED:
            raise LibcloudError('Error initializing upload. Code: %d' %
                                (response.status), driver=self)

        data_hash = None
        if calculate_hash:
            data_hash = self._get_hash_function()

        bytes_transferred = 0
        count = 1
        chunks = []
        headers = {}

        lease.update_headers(headers)

        if blob_type == 'BlockBlob':
            params = {'comp': 'block'}
        else:
            params = {'comp': 'page'}

        # Read the input data in chunk sizes suitable for AWS
        for data in read_in_chunks(iterator, AZURE_CHUNK_SIZE):
            data = b(data)
            content_length = len(data)
            offset = bytes_transferred
            bytes_transferred += content_length

            if calculate_hash:
                data_hash.update(data)

            chunk_hash = self._get_hash_function()
            chunk_hash.update(data)
            chunk_hash = base64.b64encode(b(chunk_hash.digest()))

            headers['Content-MD5'] = chunk_hash.decode('utf-8')
            headers['Content-Length'] = content_length

            if blob_type == 'BlockBlob':
                # Block id can be any unique string that is base64 encoded
                # A 10 digit number can hold the max value of 50000 blocks
                # that are allowed for azure
                block_id = base64.b64encode(b('%10d' % (count)))
                block_id = block_id.decode('utf-8')
                params['blockid'] = block_id

                # Keep this data for a later commit
                chunks.append(block_id)
            else:
                headers['x-ms-page-write'] = 'update'
                headers['x-ms-range'] = 'bytes=%d-%d' % \
                    (offset, bytes_transferred-1)

            # Renew lease before updating
            lease.renew()

            resp = self.connection.request(object_path, method='PUT',
                                           data=data, headers=headers,
                                           params=params)

            if resp.status != httplib.CREATED:
                resp.parse_error()
                raise LibcloudError('Error uploading chunk %d. Code: %d' %
                                    (count, resp.status), driver=self)

            count += 1

        if calculate_hash:
            data_hash = data_hash.hexdigest()

        if blob_type == 'BlockBlob':
            self._commit_blocks(object_path, chunks, lease)

        # The Azure service does not return a hash immediately for
        # chunked uploads. It takes some time for the data to get synced
        response.headers['content-md5'] = None

        return (True, data_hash, bytes_transferred)

    def _commit_blocks(self, object_path, chunks, lease):
        """
        Makes a final commit of the data.

        :param object_path: Server side object path.
        :type object_path: ``str``

        :param upload_id: A list of (chunk_number, chunk_hash) tuples.
        :type upload_id: ``list``
        """

        root = Element('BlockList')

        for block_id in chunks:
            part = SubElement(root, 'Uncommitted')
            part.text = str(block_id)

        data = tostring(root)
        params = {'comp': 'blocklist'}
        headers = {}

        lease.update_headers(headers)
        lease.renew()

        response = self.connection.request(object_path, data=data,
                                           params=params, headers=headers,
                                           method='PUT')

        if response.status != httplib.CREATED:
            raise LibcloudError('Error in blocklist commit', driver=self)

    def _check_values(self, blob_type, object_size):
        """
        Checks if extension arguments are valid

        :param blob_type: The blob type that is being uploaded
        :type blob_type: ``str``

        :param object_size: The (max) size of the object being uploaded
        :type object_size: ``int``
        """

        if blob_type not in ['BlockBlob', 'PageBlob']:
            raise LibcloudError('Invalid blob type', driver=self)

        if blob_type == 'PageBlob':
            if not object_size:
                raise LibcloudError('Max blob size is mandatory for page blob',
                                    driver=self)

            if object_size % AZURE_PAGE_CHUNK_SIZE:
                raise LibcloudError('Max blob size is not aligned to '
                                    'page boundary', driver=self)

    def upload_object(self, file_path, container, object_name, extra=None,
                      verify_hash=True, ex_blob_type=None, ex_use_lease=False):
        """
        Upload an object currently located on a disk.

        @inherits: :class:`StorageDriver.upload_object`

        :param ex_blob_type: Storage class
        :type ex_blob_type: ``str``

        :param ex_use_lease: Indicates if we must take a lease before upload
        :type ex_use_lease: ``bool``
        """

        if ex_blob_type is None:
            ex_blob_type = self.ex_blob_type

        # Get the size of the file
        file_size = os.stat(file_path).st_size

        # The presumed size of the object
        object_size = file_size

        self._check_values(ex_blob_type, file_size)

        with file(file_path, 'rb') as file_handle:
            iterator = iter(file_handle)

            # If size is greater than 64MB or type is Page, upload in chunks
            if ex_blob_type == 'PageBlob' or file_size > AZURE_BLOCK_MAX_SIZE:
                # For chunked upload of block blobs, the initial size must
                # be 0.
                if ex_blob_type == 'BlockBlob':
                    object_size = None

                object_path = self._get_object_path(container, object_name)

                upload_func = self._upload_in_chunks
                upload_func_kwargs = {'iterator': iterator,
                                      'object_path': object_path,
                                      'blob_type': ex_blob_type,
                                      'lease': None}
            else:
                upload_func = self._stream_data
                upload_func_kwargs = {'iterator': iterator,
                                      'chunked': False,
                                      'calculate_hash': verify_hash}

            return self._put_object(container=container,
                                    object_name=object_name,
                                    object_size=object_size,
                                    upload_func=upload_func,
                                    upload_func_kwargs=upload_func_kwargs,
                                    file_path=file_path, extra=extra,
                                    verify_hash=verify_hash,
                                    blob_type=ex_blob_type,
                                    use_lease=ex_use_lease)

    def upload_object_via_stream(self, iterator, container, object_name,
                                 verify_hash=False, extra=None,
                                 ex_use_lease=False, ex_blob_type=None,
                                 ex_page_blob_size=None):
        """
        @inherits: :class:`StorageDriver.upload_object_via_stream`

        :param ex_blob_type: Storage class
        :type ex_blob_type: ``str``

        :param ex_page_blob_size: The maximum size to which the
            page blob can grow to
        :type ex_page_blob_size: ``int``

        :param ex_use_lease: Indicates if we must take a lease before upload
        :type ex_use_lease: ``bool``
        """

        if ex_blob_type is None:
            ex_blob_type = self.ex_blob_type

        self._check_values(ex_blob_type, ex_page_blob_size)

        object_path = self._get_object_path(container, object_name)

        upload_func = self._upload_in_chunks
        upload_func_kwargs = {'iterator': iterator,
                              'object_path': object_path,
                              'blob_type': ex_blob_type,
                              'lease': None}

        return self._put_object(container=container,
                                object_name=object_name,
                                object_size=ex_page_blob_size,
                                upload_func=upload_func,
                                upload_func_kwargs=upload_func_kwargs,
                                extra=extra, verify_hash=verify_hash,
                                blob_type=ex_blob_type,
                                use_lease=ex_use_lease)

    def delete_object(self, obj):
        """
        @inherits: :class:`StorageDriver.delete_object`
        """
        object_path = self._get_object_path(obj.container, obj.name)
        response = self.connection.request(object_path, method='DELETE')

        if response.status == httplib.ACCEPTED:
            return True
        elif response.status == httplib.NOT_FOUND:
            raise ObjectDoesNotExistError(value=None, driver=self,
                                          object_name=obj.name)

        return False

    def _update_metadata(self, headers, meta_data):
        """
        Update the given metadata in the headers

        :param headers: The headers dictionary to be updated
        :type headers: ``dict``

        :param meta_data: Metadata key value pairs
        :type meta_data: ``dict``
        """
        for key, value in list(meta_data.items()):
            key = 'x-ms-meta-%s' % (key)
            headers[key] = value

    def _prepare_upload_headers(self, object_name, object_size,
                                extra, meta_data, blob_type):
        """
        Prepare headers for uploading an object

        :param object_name: The full name of the object being updated
        :type object_name: ``str``

        :param object_size: The size of the object. In case of PageBlobs,
            this indicates the maximum size the blob can grow to
        :type object_size: ``int``

        :param extra: Extra control data for the upload
        :type extra: ``dict``

        :param meta_data: Metadata key value pairs
        :type meta_data: ``dict``

        :param blob_type: Page or Block blob type
        :type blob_type: ``str``
        """
        headers = {}

        if blob_type is None:
            blob_type = self.ex_blob_type

        headers['x-ms-blob-type'] = blob_type

        self._update_metadata(headers, meta_data)

        if object_size is not None:
            headers['Content-Length'] = object_size

        if blob_type == 'PageBlob':
            headers['Content-Length'] = 0
            headers['x-ms-blob-content-length'] = object_size

        return headers

    def _put_object(self, container, object_name, object_size, upload_func,
                    upload_func_kwargs, file_path=None, extra=None,
                    verify_hash=True, blob_type=None, use_lease=False):
        """
        Control function that does the real job of uploading data to a blob
        """
        extra = extra or {}
        meta_data = extra.get('meta_data', {})
        content_type = extra.get('content_type', None)

        headers = self._prepare_upload_headers(object_name, object_size,
                                               extra, meta_data, blob_type)

        object_path = self._get_object_path(container, object_name)

        # Get a lease if required and do the operations
        with AzureBlobLease(self, object_path, use_lease) as lease:
            if 'lease' in upload_func_kwargs:
                upload_func_kwargs['lease'] = lease

            lease.update_headers(headers)

            iterator = iter('')
            result_dict = self._upload_object(object_name, content_type,
                                              upload_func, upload_func_kwargs,
                                              object_path, headers=headers,
                                              file_path=file_path,
                                              iterator=iterator)

            response = result_dict['response']
            bytes_transferred = result_dict['bytes_transferred']
            data_hash = result_dict['data_hash']
            headers = response.headers
            response = response.response

        if response.status != httplib.CREATED:
            raise LibcloudError(
                'Unexpected status code, status_code=%s' % (response.status),
                driver=self)

        server_hash = headers['content-md5']

        if server_hash:
            server_hash = binascii.hexlify(base64.b64decode(b(server_hash)))
            server_hash = server_hash.decode('utf-8')
        else:
            # TODO: HACK - We could poll the object for a while and get
            # the hash
            pass

        if (verify_hash and server_hash and data_hash != server_hash):
            raise ObjectHashMismatchError(
                value='MD5 hash checksum does not match',
                object_name=object_name, driver=self)

        return Object(name=object_name, size=bytes_transferred,
                      hash=headers['etag'], extra=None,
                      meta_data=meta_data, container=container,
                      driver=self)

    def ex_set_object_metadata(self, obj, meta_data):
        """
        Set metadata for an object

        :param obj: The blob object
        :type obj: :class:`Object`

        :param meta_data: Metadata key value pairs
        :type meta_data: ``dict``
        """
        object_path = self._get_object_path(obj.container, obj.name)
        params = {'comp': 'metadata'}
        headers = {}

        self._update_metadata(headers, meta_data)

        response = self.connection.request(object_path, method='PUT',
                                           params=params,
                                           headers=headers)

        if response.status != httplib.OK:
            response.parse_error('Setting metadata')
