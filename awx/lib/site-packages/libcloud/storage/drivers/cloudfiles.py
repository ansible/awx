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
from time import time

from libcloud.utils.py3 import httplib
from libcloud.utils.py3 import urlencode

try:
    import simplejson as json
except ImportError:
    import json

from libcloud.utils.py3 import PY3
from libcloud.utils.py3 import b
from libcloud.utils.py3 import urlquote

if PY3:
    from io import FileIO as file

from libcloud.utils.files import read_in_chunks
from libcloud.common.types import MalformedResponseError, LibcloudError
from libcloud.common.base import Response, RawResponse

from libcloud.storage.providers import Provider
from libcloud.storage.base import Object, Container, StorageDriver
from libcloud.storage.types import ContainerAlreadyExistsError
from libcloud.storage.types import ContainerDoesNotExistError
from libcloud.storage.types import ContainerIsNotEmptyError
from libcloud.storage.types import ObjectDoesNotExistError
from libcloud.storage.types import ObjectHashMismatchError
from libcloud.storage.types import InvalidContainerNameError
from libcloud.common.openstack import OpenStackBaseConnection
from libcloud.common.openstack import OpenStackDriverMixin

from libcloud.common.rackspace import AUTH_URL

CDN_HOST = 'cdn.clouddrive.com'
API_VERSION = 'v1.0'

# Keys which are used to select a correct endpoint from the service catalog.
INTERNAL_ENDPOINT_KEY = 'internalURL'
PUBLIC_ENDPOINT_KEY = 'publicURL'


class CloudFilesResponse(Response):
    valid_response_codes = [httplib.NOT_FOUND, httplib.CONFLICT]

    def success(self):
        i = int(self.status)
        return i >= 200 and i <= 299 or i in self.valid_response_codes

    def parse_body(self):
        if not self.body:
            return None

        if 'content-type' in self.headers:
            key = 'content-type'
        elif 'Content-Type' in self.headers:
            key = 'Content-Type'
        else:
            raise LibcloudError('Missing content-type header')

        content_type = self.headers[key]
        if content_type.find(';') != -1:
            content_type = content_type.split(';')[0]

        if content_type == 'application/json':
            try:
                data = json.loads(self.body)
            except:
                raise MalformedResponseError('Failed to parse JSON',
                                             body=self.body,
                                             driver=CloudFilesStorageDriver)
        elif content_type == 'text/plain':
            data = self.body
        else:
            data = self.body

        return data


class CloudFilesRawResponse(CloudFilesResponse, RawResponse):
    pass


class OpenStackSwiftConnection(OpenStackBaseConnection):
    """
    Connection class for the OpenStack Swift endpoint.
    """

    responseCls = CloudFilesResponse
    rawResponseCls = CloudFilesRawResponse

    auth_url = AUTH_URL
    _auth_version = '1.0'

    # TODO: Reverse the relationship - Swift -> CloudFiles
    def __init__(self, user_id, key, secure=True, **kwargs):
        # Ignore this for now
        kwargs.pop('use_internal_url', None)
        super(OpenStackSwiftConnection, self).__init__(user_id, key,
                                                       secure=secure,
                                                       **kwargs)
        self.api_version = API_VERSION
        self.accept_format = 'application/json'

        self._service_type = self._ex_force_service_type or 'object-store'
        self._service_name = self._ex_force_service_name or 'swift'

        if self._ex_force_service_region:
            self._service_region = self._ex_force_service_region
        else:
            self._service_region = None

    def get_endpoint(self, *args, **kwargs):
        if '2.0' in self._auth_version:
            endpoint = self.service_catalog.get_endpoint(
                service_type=self._service_type,
                name=self._service_name,
                region=self._service_region)
        elif ('1.1' in self._auth_version) or ('1.0' in self._auth_version):
            endpoint = self.service_catalog.get_endpoint(
                name=self._service_name, region=self._service_region)

        if PUBLIC_ENDPOINT_KEY in endpoint:
            return endpoint[PUBLIC_ENDPOINT_KEY]
        else:
            raise LibcloudError('Could not find specified endpoint')

    def request(self, action, params=None, data='', headers=None, method='GET',
                raw=False, cdn_request=False):
        if not headers:
            headers = {}
        if not params:
            params = {}

        self.cdn_request = cdn_request
        params['format'] = 'json'

        if method in ['POST', 'PUT'] and 'Content-Type' not in headers:
            headers.update({'Content-Type': 'application/json; charset=UTF-8'})

        return super(OpenStackSwiftConnection, self).request(
            action=action,
            params=params, data=data,
            method=method, headers=headers,
            raw=raw)


class CloudFilesConnection(OpenStackSwiftConnection):
    """
    Base connection class for the Cloudfiles driver.
    """

    responseCls = CloudFilesResponse
    rawResponseCls = CloudFilesRawResponse

    auth_url = AUTH_URL
    _auth_version = '2.0'

    def __init__(self, user_id, key, secure=True,
                 use_internal_url=False, **kwargs):
        super(CloudFilesConnection, self).__init__(user_id, key, secure=secure,
                                                   **kwargs)
        self.api_version = API_VERSION
        self.accept_format = 'application/json'
        self.cdn_request = False
        self.use_internal_url = use_internal_url

    def _get_endpoint_key(self):
        if self.use_internal_url:
            endpoint_key = INTERNAL_ENDPOINT_KEY
        else:
            endpoint_key = PUBLIC_ENDPOINT_KEY

        if self.cdn_request:
            # cdn endpoints don't have internal urls
            endpoint_key = PUBLIC_ENDPOINT_KEY

        return endpoint_key

    def get_endpoint(self):
        region = self._ex_force_service_region.upper()

        if '2.0' in self._auth_version:
            ep = self.service_catalog.get_endpoint(
                service_type='object-store',
                name='cloudFiles',
                region=region)
            cdn_ep = self.service_catalog.get_endpoint(
                service_type='rax:object-cdn',
                name='cloudFilesCDN',
                region=region)
        else:
            raise LibcloudError(
                'Auth version "%s" not supported' % (self._auth_version))

        # if this is a CDN request, return the cdn url instead
        if self.cdn_request:
            ep = cdn_ep

        endpoint_key = self._get_endpoint_key()

        if not ep:
            raise LibcloudError('Could not find specified endpoint')

        if endpoint_key in ep:
            return ep[endpoint_key]
        else:
            raise LibcloudError('Could not find specified endpoint')

    def request(self, action, params=None, data='', headers=None, method='GET',
                raw=False, cdn_request=False):
        if not headers:
            headers = {}
        if not params:
            params = {}

        self.cdn_request = cdn_request
        params['format'] = 'json'

        if method in ['POST', 'PUT'] and 'Content-Type' not in headers:
            headers.update({'Content-Type': 'application/json; charset=UTF-8'})

        return super(CloudFilesConnection, self).request(
            action=action,
            params=params, data=data,
            method=method, headers=headers,
            raw=raw)


class CloudFilesStorageDriver(StorageDriver, OpenStackDriverMixin):
    """
    CloudFiles driver.
    """
    name = 'CloudFiles'
    website = 'http://www.rackspace.com/'

    connectionCls = CloudFilesConnection
    hash_type = 'md5'
    supports_chunked_encoding = True

    def __init__(self, key, secret=None, secure=True, host=None, port=None,
                 region='ord', use_internal_url=False, **kwargs):
        """
        @inherits:  :class:`StorageDriver.__init__`

        :param region: ID of the region which should be used.
        :type region: ``str``
        """
        # This is here for backard compatibility
        if 'ex_force_service_region' in kwargs:
            region = kwargs['ex_force_service_region']

        self.use_internal_url = use_internal_url
        OpenStackDriverMixin.__init__(self, (), **kwargs)
        super(CloudFilesStorageDriver, self).__init__(key=key, secret=secret,
                                                      secure=secure, host=host,
                                                      port=port, region=region,
                                                      **kwargs)

    def iterate_containers(self):
        response = self.connection.request('')

        if response.status == httplib.NO_CONTENT:
            return []
        elif response.status == httplib.OK:
            return self._to_container_list(json.loads(response.body))

        raise LibcloudError('Unexpected status code: %s' % (response.status))

    def get_container(self, container_name):
        container_name_encoded = self._encode_container_name(container_name)
        response = self.connection.request('/%s' % (container_name_encoded),
                                           method='HEAD')

        if response.status == httplib.NO_CONTENT:
            container = self._headers_to_container(
                container_name, response.headers)
            return container
        elif response.status == httplib.NOT_FOUND:
            raise ContainerDoesNotExistError(None, self, container_name)

        raise LibcloudError('Unexpected status code: %s' % (response.status))

    def get_object(self, container_name, object_name):
        container = self.get_container(container_name)
        container_name_encoded = self._encode_container_name(container_name)
        object_name_encoded = self._encode_object_name(object_name)

        response = self.connection.request('/%s/%s' % (container_name_encoded,
                                                       object_name_encoded),
                                           method='HEAD')
        if response.status in [httplib.OK, httplib.NO_CONTENT]:
            obj = self._headers_to_object(
                object_name, container, response.headers)
            return obj
        elif response.status == httplib.NOT_FOUND:
            raise ObjectDoesNotExistError(None, self, object_name)

        raise LibcloudError('Unexpected status code: %s' % (response.status))

    def get_container_cdn_url(self, container):
        container_name_encoded = self._encode_container_name(container.name)
        response = self.connection.request('/%s' % (container_name_encoded),
                                           method='HEAD',
                                           cdn_request=True)

        if response.status == httplib.NO_CONTENT:
            cdn_url = response.headers['x-cdn-uri']
            return cdn_url
        elif response.status == httplib.NOT_FOUND:
            raise ContainerDoesNotExistError(value='',
                                             container_name=container.name,
                                             driver=self)

        raise LibcloudError('Unexpected status code: %s' % (response.status))

    def get_object_cdn_url(self, obj):
        container_cdn_url = self.get_container_cdn_url(container=obj.container)
        return '%s/%s' % (container_cdn_url, obj.name)

    def enable_container_cdn(self, container, ex_ttl=None):
        """
        @inherits: :class:`StorageDriver.enable_container_cdn`

        :param ex_ttl: cache time to live
        :type ex_ttl: ``int``
        """
        container_name = container.name
        headers = {'X-CDN-Enabled': 'True'}

        if ex_ttl:
            headers['X-TTL'] = ex_ttl

        response = self.connection.request('/%s' % (container_name),
                                           method='PUT',
                                           headers=headers,
                                           cdn_request=True)

        return response.status in [httplib.CREATED, httplib.ACCEPTED]

    def create_container(self, container_name):
        container_name_encoded = self._encode_container_name(container_name)
        response = self.connection.request(
            '/%s' % (container_name_encoded), method='PUT')

        if response.status == httplib.CREATED:
            # Accepted mean that container is not yet created but it will be
            # eventually
            extra = {'object_count': 0}
            container = Container(name=container_name,
                                  extra=extra, driver=self)

            return container
        elif response.status == httplib.ACCEPTED:
            error = ContainerAlreadyExistsError(None, self, container_name)
            raise error

        raise LibcloudError('Unexpected status code: %s' % (response.status))

    def delete_container(self, container):
        name = self._encode_container_name(container.name)

        # Only empty container can be deleted
        response = self.connection.request('/%s' % (name), method='DELETE')

        if response.status == httplib.NO_CONTENT:
            return True
        elif response.status == httplib.NOT_FOUND:
            raise ContainerDoesNotExistError(value='',
                                             container_name=name, driver=self)
        elif response.status == httplib.CONFLICT:
            # @TODO: Add "delete_all_objects" parameter?
            raise ContainerIsNotEmptyError(value='',
                                           container_name=name, driver=self)

    def download_object(self, obj, destination_path, overwrite_existing=False,
                        delete_on_failure=True):
        container_name = obj.container.name
        object_name = obj.name
        response = self.connection.request('/%s/%s' % (container_name,
                                                       object_name),
                                           method='GET', raw=True)

        return self._get_object(
            obj=obj, callback=self._save_object, response=response,
            callback_kwargs={'obj': obj,
                             'response': response.response,
                             'destination_path': destination_path,
                             'overwrite_existing': overwrite_existing,
                             'delete_on_failure': delete_on_failure},
            success_status_code=httplib.OK)

    def download_object_as_stream(self, obj, chunk_size=None):
        container_name = obj.container.name
        object_name = obj.name
        response = self.connection.request('/%s/%s' % (container_name,
                                                       object_name),
                                           method='GET', raw=True)

        return self._get_object(obj=obj, callback=read_in_chunks,
                                response=response,
                                callback_kwargs={'iterator': response.response,
                                                 'chunk_size': chunk_size},
                                success_status_code=httplib.OK)

    def upload_object(self, file_path, container, object_name, extra=None,
                      verify_hash=True):
        """
        Upload an object.

        Note: This will override file with a same name if it already exists.
        """
        upload_func = self._upload_file
        upload_func_kwargs = {'file_path': file_path}

        return self._put_object(container=container, object_name=object_name,
                                upload_func=upload_func,
                                upload_func_kwargs=upload_func_kwargs,
                                extra=extra, file_path=file_path,
                                verify_hash=verify_hash)

    def upload_object_via_stream(self, iterator,
                                 container, object_name, extra=None):
        if isinstance(iterator, file):
            iterator = iter(iterator)

        upload_func = self._stream_data
        upload_func_kwargs = {'iterator': iterator}

        return self._put_object(container=container, object_name=object_name,
                                upload_func=upload_func,
                                upload_func_kwargs=upload_func_kwargs,
                                extra=extra, iterator=iterator)

    def delete_object(self, obj):
        container_name = self._encode_container_name(obj.container.name)
        object_name = self._encode_object_name(obj.name)

        response = self.connection.request(
            '/%s/%s' % (container_name, object_name), method='DELETE')

        if response.status == httplib.NO_CONTENT:
            return True
        elif response.status == httplib.NOT_FOUND:
            raise ObjectDoesNotExistError(value='', object_name=object_name,
                                          driver=self)

        raise LibcloudError('Unexpected status code: %s' % (response.status))

    def ex_purge_object_from_cdn(self, obj, email=None):
        """
        Purge edge cache for the specified object.

        :param email: Email where a notification will be sent when the job
        completes. (optional)
        :type email: ``str``
        """
        container_name = self._encode_container_name(obj.container.name)
        object_name = self._encode_object_name(obj.name)
        headers = {'X-Purge-Email': email} if email else {}

        response = self.connection.request('/%s/%s' % (container_name,
                                                       object_name),
                                           method='DELETE',
                                           headers=headers,
                                           cdn_request=True)

        return response.status == httplib.NO_CONTENT

    def ex_get_meta_data(self):
        """
        Get meta data

        :rtype: ``dict``
        """
        response = self.connection.request('', method='HEAD')

        if response.status == httplib.NO_CONTENT:
            container_count = response.headers.get(
                'x-account-container-count', 'unknown')
            object_count = response.headers.get(
                'x-account-object-count', 'unknown')
            bytes_used = response.headers.get(
                'x-account-bytes-used', 'unknown')
            temp_url_key = response.headers.get(
                'x-account-meta-temp-url-key', None)

            return {'container_count': int(container_count),
                    'object_count': int(object_count),
                    'bytes_used': int(bytes_used),
                    'temp_url_key': temp_url_key}

        raise LibcloudError('Unexpected status code: %s' % (response.status))

    def ex_multipart_upload_object(self, file_path, container, object_name,
                                   chunk_size=33554432, extra=None,
                                   verify_hash=True):
        object_size = os.path.getsize(file_path)
        if object_size < chunk_size:
            return self.upload_object(file_path, container, object_name,
                                      extra=extra, verify_hash=verify_hash)

        iter_chunk_reader = FileChunkReader(file_path, chunk_size)

        for index, iterator in enumerate(iter_chunk_reader):
            self._upload_object_part(container=container,
                                     object_name=object_name,
                                     part_number=index,
                                     iterator=iterator,
                                     verify_hash=verify_hash)

        return self._upload_object_manifest(container=container,
                                            object_name=object_name,
                                            extra=extra,
                                            verify_hash=verify_hash)

    def ex_enable_static_website(self, container, index_file='index.html'):
        """
        Enable serving a static website.

        :param container: Container instance
        :type container: :class:`Container`

        :param index_file: Name of the object which becomes an index page for
        every sub-directory in this container.
        :type index_file: ``str``

        :rtype: ``bool``
        """
        container_name = container.name
        headers = {'X-Container-Meta-Web-Index': index_file}

        response = self.connection.request('/%s' % (container_name),
                                           method='POST',
                                           headers=headers,
                                           cdn_request=False)

        return response.status in [httplib.CREATED, httplib.ACCEPTED]

    def ex_set_error_page(self, container, file_name='error.html'):
        """
        Set a custom error page which is displayed if file is not found and
        serving of a static website is enabled.

        :param container: Container instance
        :type container: :class:`Container`

        :param file_name: Name of the object which becomes the error page.
        :type file_name: ``str``

        :rtype: ``bool``
        """
        container_name = container.name
        headers = {'X-Container-Meta-Web-Error': file_name}

        response = self.connection.request('/%s' % (container_name),
                                           method='POST',
                                           headers=headers,
                                           cdn_request=False)

        return response.status in [httplib.CREATED, httplib.ACCEPTED]

    def ex_set_account_metadata_temp_url_key(self, key):
        """
        Set the metadata header X-Account-Meta-Temp-URL-Key on your Cloud
        Files account.

        :param key: X-Account-Meta-Temp-URL-Key
        :type key: ``str``

        :rtype: ``bool``
        """
        headers = {'X-Account-Meta-Temp-URL-Key': key}

        response = self.connection.request('',
                                           method='POST',
                                           headers=headers,
                                           cdn_request=False)

        return response.status in [httplib.OK, httplib.NO_CONTENT,
                                   httplib.CREATED, httplib.ACCEPTED]

    def ex_get_object_temp_url(self, obj, method='GET', timeout=60):
        """
        Create a temporary URL to allow others to retrieve or put objects
        in your Cloud Files account for as long or as short a time as you
        wish.  This method is specifically for allowing users to retrieve
        or update an object.

        :param obj: The object that you wish to make temporarily public
        :type obj: :class:`Object`

        :param method: Which method you would like to allow, 'PUT' or 'GET'
        :type method: ``str``

        :param timeout: Time (in seconds) after which you want the TempURL
        to expire.
        :type timeout: ``int``

        :rtype: ``bool``
        """
        self.connection._populate_hosts_and_request_paths()
        expires = int(time() + timeout)
        path = '%s/%s/%s' % (self.connection.request_path,
                             obj.container.name, obj.name)
        try:
            key = self.ex_get_meta_data()['temp_url_key']
            assert key is not None
        except Exception:
            raise KeyError('You must first set the ' +
                           'X-Account-Meta-Temp-URL-Key header on your ' +
                           'Cloud Files account using ' +
                           'ex_set_account_metadata_temp_url_key before ' +
                           'you can use this method.')
        hmac_body = '%s\n%s\n%s' % (method, expires, path)
        sig = hmac.new(b(key), b(hmac_body), sha1).hexdigest()
        params = urlencode({'temp_url_sig': sig,
                            'temp_url_expires': expires})

        temp_url = 'https://%s/%s/%s?%s' %\
                   (self.connection.host + self.connection.request_path,
                    obj.container.name, obj.name, params)

        return temp_url

    def _upload_object_part(self, container, object_name, part_number,
                            iterator, verify_hash=True):
        upload_func = self._stream_data
        upload_func_kwargs = {'iterator': iterator}
        part_name = object_name + '/%08d' % part_number
        extra = {'content_type': 'application/octet-stream'}

        self._put_object(container=container,
                         object_name=part_name,
                         upload_func=upload_func,
                         upload_func_kwargs=upload_func_kwargs,
                         extra=extra, iterator=iterator,
                         verify_hash=verify_hash)

    def _upload_object_manifest(self, container, object_name, extra=None,
                                verify_hash=True):
        extra = extra or {}
        meta_data = extra.get('meta_data')

        container_name_encoded = self._encode_container_name(container.name)
        object_name_encoded = self._encode_object_name(object_name)
        request_path = '/%s/%s' % (container_name_encoded, object_name_encoded)

        headers = {'X-Auth-Token': self.connection.auth_token,
                   'X-Object-Manifest': '%s/%s/' %
                                        (container_name_encoded,
                                         object_name_encoded)}

        data = ''
        response = self.connection.request(request_path,
                                           method='PUT', data=data,
                                           headers=headers, raw=True)

        object_hash = None

        if verify_hash:
            hash_function = self._get_hash_function()
            hash_function.update(b(data))
            data_hash = hash_function.hexdigest()
            object_hash = response.headers.get('etag')

            if object_hash != data_hash:
                raise ObjectHashMismatchError(
                    value=('MD5 hash checksum does not match (expected=%s, ' +
                           'actual=%s)') %
                          (data_hash, object_hash),
                    object_name=object_name, driver=self)

        obj = Object(name=object_name, size=0, hash=object_hash, extra=None,
                     meta_data=meta_data, container=container, driver=self)

        return obj

    def list_container_objects(self, container, ex_prefix=None):
        """
        Return a list of objects for the given container.

        :param container: Container instance.
        :type container: :class:`Container`

        :param ex_prefix: Only get objects with names starting with ex_prefix
        :type ex_prefix: ``str``

        :return: A list of Object instances.
        :rtype: ``list`` of :class:`Object`
        """
        return list(self.iterate_container_objects(container,
                                                   ex_prefix=ex_prefix))

    def iterate_container_objects(self, container, ex_prefix=None):
        """
        Return a generator of objects for the given container.

        :param container: Container instance
        :type container: :class:`Container`

        :param ex_prefix: Only get objects with names starting with ex_prefix
        :type ex_prefix: ``str``

        :return: A generator of Object instances.
        :rtype: ``generator`` of :class:`Object`
        """
        params = {}
        if ex_prefix:
            params['prefix'] = ex_prefix

        while True:
            container_name_encoded = \
                self._encode_container_name(container.name)
            response = self.connection.request('/%s' %
                                               (container_name_encoded),
                                               params=params)

            if response.status == httplib.NO_CONTENT:
                # Empty or non-existent container
                break
            elif response.status == httplib.OK:
                objects = self._to_object_list(json.loads(response.body),
                                               container)

                if len(objects) == 0:
                    break

                for obj in objects:
                    yield obj
                params['marker'] = obj.name

            else:
                raise LibcloudError('Unexpected status code: %s' %
                                    (response.status))

    def _put_object(self, container, object_name, upload_func,
                    upload_func_kwargs, extra=None, file_path=None,
                    iterator=None, verify_hash=True):
        extra = extra or {}
        container_name_encoded = self._encode_container_name(container.name)
        object_name_encoded = self._encode_object_name(object_name)
        content_type = extra.get('content_type', None)
        meta_data = extra.get('meta_data', None)
        content_disposition = extra.get('content_disposition', None)

        headers = {}
        if meta_data:
            for key, value in list(meta_data.items()):
                key = 'X-Object-Meta-%s' % (key)
                headers[key] = value

        if content_disposition is not None:
            headers['Content-Disposition'] = content_disposition

        request_path = '/%s/%s' % (container_name_encoded, object_name_encoded)
        result_dict = self._upload_object(
            object_name=object_name, content_type=content_type,
            upload_func=upload_func, upload_func_kwargs=upload_func_kwargs,
            request_path=request_path, request_method='PUT',
            headers=headers, file_path=file_path, iterator=iterator)

        response = result_dict['response'].response
        bytes_transferred = result_dict['bytes_transferred']
        server_hash = result_dict['response'].headers.get('etag', None)

        if response.status == httplib.EXPECTATION_FAILED:
            raise LibcloudError(value='Missing content-type header',
                                driver=self)
        elif verify_hash and not server_hash:
            raise LibcloudError(value='Server didn\'t return etag',
                                driver=self)
        elif (verify_hash and result_dict['data_hash'] != server_hash):
            raise ObjectHashMismatchError(
                value=('MD5 hash checksum does not match (expected=%s, ' +
                       'actual=%s)') % (result_dict['data_hash'], server_hash),
                object_name=object_name, driver=self)
        elif response.status == httplib.CREATED:
            obj = Object(
                name=object_name, size=bytes_transferred, hash=server_hash,
                extra=None, meta_data=meta_data, container=container,
                driver=self)

            return obj
        else:
            # @TODO: Add test case for this condition (probably 411)
            raise LibcloudError('status_code=%s' % (response.status),
                                driver=self)

    def _encode_container_name(self, name):
        """
        Encode container name so it can be used as part of the HTTP request.
        """
        if name.startswith('/'):
            name = name[1:]
        name = urlquote(name)

        if name.find('/') != -1:
            raise InvalidContainerNameError(value='Container name cannot'
                                                  ' contain slashes',
                                            container_name=name, driver=self)

        if len(name) > 256:
            raise InvalidContainerNameError(
                value='Container name cannot be longer than 256 bytes',
                container_name=name, driver=self)

        return name

    def _encode_object_name(self, name):
        name = urlquote(name)
        return name

    def _to_container_list(self, response):
        # @TODO: Handle more than 10k containers - use "lazy list"?
        for container in response:
            extra = {'object_count': int(container['count']),
                     'size': int(container['bytes'])}
            yield Container(name=container['name'], extra=extra, driver=self)

    def _to_object_list(self, response, container):
        objects = []

        for obj in response:
            name = obj['name']
            size = int(obj['bytes'])
            hash = obj['hash']
            extra = {'content_type': obj['content_type'],
                     'last_modified': obj['last_modified']}
            objects.append(Object(
                name=name, size=size, hash=hash, extra=extra,
                meta_data=None, container=container, driver=self))

        return objects

    def _headers_to_container(self, name, headers):
        size = int(headers.get('x-container-bytes-used', 0))
        object_count = int(headers.get('x-container-object-count', 0))

        extra = {'object_count': object_count,
                 'size': size}
        container = Container(name=name, extra=extra, driver=self)
        return container

    def _headers_to_object(self, name, container, headers):
        size = int(headers.pop('content-length', 0))
        last_modified = headers.pop('last-modified', None)
        etag = headers.pop('etag', None)
        content_type = headers.pop('content-type', None)

        meta_data = {}
        for key, value in list(headers.items()):
            if key.find('x-object-meta-') != -1:
                key = key.replace('x-object-meta-', '')
                meta_data[key] = value

        extra = {'content_type': content_type, 'last_modified': last_modified}

        obj = Object(name=name, size=size, hash=etag, extra=extra,
                     meta_data=meta_data, container=container, driver=self)
        return obj

    def _ex_connection_class_kwargs(self):
        kwargs = self.openstack_connection_kwargs()
        kwargs['ex_force_service_region'] = self.region
        kwargs['use_internal_url'] = self.use_internal_url
        return kwargs


class CloudFilesUSStorageDriver(CloudFilesStorageDriver):
    """
    Cloudfiles storage driver for the US endpoint.
    """

    type = Provider.CLOUDFILES_US
    name = 'CloudFiles (US)'

    def __init__(self, *args, **kwargs):
        kwargs['region'] = 'ord'
        super(CloudFilesUSStorageDriver, self).__init__(*args, **kwargs)


class OpenStackSwiftStorageDriver(CloudFilesStorageDriver):
    """
    Storage driver for the OpenStack Swift.
    """
    type = Provider.CLOUDFILES_SWIFT
    name = 'OpenStack Swift'
    connectionCls = OpenStackSwiftConnection

    # TODO: Reverse the relationship - Swift -> CloudFiles

    def __init__(self, key, secret=None, secure=True, host=None, port=None,
                 region=None, **kwargs):
        super(OpenStackSwiftStorageDriver, self).__init__(key=key,
                                                          secret=secret,
                                                          secure=secure,
                                                          host=host,
                                                          port=port,
                                                          region=region,
                                                          **kwargs)


class CloudFilesUKStorageDriver(CloudFilesStorageDriver):
    """
    Cloudfiles storage driver for the UK endpoint.
    """

    type = Provider.CLOUDFILES_UK
    name = 'CloudFiles (UK)'

    def __init__(self, *args, **kwargs):
        kwargs['region'] = 'lon'
        super(CloudFilesUKStorageDriver, self).__init__(*args, **kwargs)


class FileChunkReader(object):
    def __init__(self, file_path, chunk_size):
        self.file_path = file_path
        self.total = os.path.getsize(file_path)
        self.chunk_size = chunk_size
        self.bytes_read = 0
        self.stop_iteration = False

    def __iter__(self):
        return self

    def next(self):
        if self.stop_iteration:
            raise StopIteration

        start_block = self.bytes_read
        end_block = start_block + self.chunk_size
        if end_block >= self.total:
            end_block = self.total
            self.stop_iteration = True
        self.bytes_read += end_block - start_block
        return ChunkStreamReader(file_path=self.file_path,
                                 start_block=start_block,
                                 end_block=end_block,
                                 chunk_size=8192)

    def __next__(self):
        return self.next()


class ChunkStreamReader(object):
    def __init__(self, file_path, start_block, end_block, chunk_size):
        self.fd = open(file_path, 'rb')
        self.fd.seek(start_block)
        self.start_block = start_block
        self.end_block = end_block
        self.chunk_size = chunk_size
        self.bytes_read = 0
        self.stop_iteration = False

    def __iter__(self):
        return self

    def next(self):
        if self.stop_iteration:
            self.fd.close()
            raise StopIteration

        block_size = self.chunk_size
        if self.bytes_read + block_size > \
                self.end_block - self.start_block:
            block_size = self.end_block - self.start_block - self.bytes_read
            self.stop_iteration = True

        block = self.fd.read(block_size)
        self.bytes_read += block_size
        return block

    def __next__(self):
        return self.next()
