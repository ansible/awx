# -*- coding: utf-8 -*-

# Copyright 2014 Rackspace

# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


from __future__ import print_function
from __future__ import absolute_import
import datetime
from functools import wraps
import hashlib
import hmac
import json
import logging
import math
import mimetypes
import os
import re
import six
import threading
import time
import uuid

import pyrax
from pyrax.client import BaseClient
import pyrax.exceptions as exc
from pyrax.manager import BaseManager
from pyrax.resource import BaseResource
import pyrax.utils as utils

ACCOUNT_META_PREFIX = "X-Account-Meta-"
CONTAINER_META_PREFIX = "X-Container-Meta-"
CONTAINER_HEAD_PREFIX = "X-Container-"
OBJECT_META_PREFIX = "X-Object-Meta-"

# Maximum size of a stored object: 5GB - 1
MAX_FILE_SIZE = 5368709119
# Default size for chunked uploads, in bytes
DEFAULT_CHUNKSIZE = 65536
# The default for CDN when TTL is not specified.
DEFAULT_CDN_TTL = 86400
# When comparing files dates, represents a date older than anything.
EARLY_DATE_STR = "1900-01-01T00:00:00"
# Maximum number of objects that can be passed to bulk-delete
MAX_BULK_DELETE = 10000

# Used to indicate values that are lazy-loaded
class Fault_cls(object):
    def __nonzero__(self):
        return False

FAULT = Fault_cls()


def assure_container(fnc):
    """
    Assures that whether a Container or a name of a container is passed, a
    Container object is available.
    """
    @wraps(fnc)
    def _wrapped(self, container, *args, **kwargs):
        if not isinstance(container, Container):
            # Must be the name
            container = self.get(container)
        return fnc(self, container, *args, **kwargs)
    return _wrapped


def _massage_metakeys(dct, prfx):
    """
    Returns a copy of the supplied dictionary, prefixing any keys that do
    not begin with the specified prefix accordingly.
    """
    lowprefix = prfx.lower()
    ret = {}
    for k, v in list(dct.items()):
        if not k.lower().startswith(lowprefix):
            k = "%s%s" % (prfx, k)
        ret[k] = v
    return ret


def _validate_file_or_path(file_or_path, obj_name):
    if isinstance(file_or_path, six.string_types):
        # Make sure it exists
        if not os.path.exists(file_or_path):
            raise exc.FileNotFound("The file '%s' does not exist." %
                    file_or_path)
        fname = os.path.basename(file_or_path)
    else:
        try:
            fname = os.path.basename(file_or_path.name)
        except AttributeError:
            fname = None
    return obj_name or fname


def _valid_upload_key(fnc):
    @wraps(fnc)
    def wrapped(self, upload_key, *args, **kwargs):
        try:
            self.folder_upload_status[upload_key]
        except KeyError:
            raise exc.InvalidUploadID("There is no folder upload with the "
                    "key '%s'." % upload_key)
        return fnc(self, upload_key, *args, **kwargs)
    return wrapped


def _handle_container_not_found(fnc):
    @wraps(fnc)
    def wrapped(self, container, *args, **kwargs):
        try:
            return fnc(self, container, *args, **kwargs)
        except exc.NotFound as e:
            name = utils.get_name(container)
            e.message = "Container '%s' doesn't exist" % name
            raise exc.NoSuchContainer(e)
    return wrapped


def _handle_object_not_found(fnc):
    @wraps(fnc)
    def wrapped(self, obj, *args, **kwargs):
        try:
            return fnc(self, obj, *args, **kwargs)
        except exc.NotFound as e:
            name = utils.get_name(obj)
            e.message = "Object '%s' doesn't exist" % name
            raise exc.NoSuchObject(e)
    return wrapped


def get_file_size(fileobj):
    """
    Returns the size of a file-like object.
    """
    currpos = fileobj.tell()
    fileobj.seek(0, 2)
    total_size = fileobj.tell()
    fileobj.seek(currpos)
    return total_size



class Container(BaseResource):
    def __init__(self, *args, **kwargs):
        super(Container, self).__init__(*args, **kwargs)
        self._cdn_enabled = FAULT
        self._cdn_uri = FAULT
        self._cdn_ttl = FAULT
        self._cdn_ssl_uri = FAULT
        self._cdn_streaming_uri = FAULT
        self._cdn_ios_uri = FAULT
        self._cdn_log_retention = FAULT
        self.object_manager = StorageObjectManager(self.manager.api,
                uri_base=self.name, resource_class=StorageObject)
        self._non_display = ["object_manager"]
        self._backwards_aliases()


    def _backwards_aliases(self):
        self.get_objects = self.list
        self.get_object_names = self.list_object_names
        # Prevent these from displaying
        self._non_display.extend(["get_objects", "get_object",
                "get_object_names"])


    def __repr__(self):
        return "<Container '%s'>" % self.name


    @property
    def id(self):
        """
        Since a container's name serves as its ID, this will allow both to be
        used.
        """
        return self.name


    def _set_cdn_defaults(self):
        """Sets all the CDN-related attributes to default values."""
        if self._cdn_enabled is FAULT:
            self._cdn_enabled = False
        self._cdn_uri = None
        self._cdn_ttl = DEFAULT_CDN_TTL
        self._cdn_ssl_uri = None
        self._cdn_streaming_uri = None
        self._cdn_ios_uri = None
        self._cdn_log_retention = False


    def _fetch_cdn_data(self):
        """Fetches the container's CDN data from the CDN service"""
        if self._cdn_enabled is FAULT:
            headers = self.manager.fetch_cdn_data(self)
        else:
            headers = {}
        # Set defaults in case not all headers are present.
        self._set_cdn_defaults()
        if not headers:
            # Not CDN enabled; return
            return
        else:
            self._cdn_enabled = True
        for key, value in headers.items():
            low_key = key.lower()
            if low_key == "x-cdn-uri":
                self._cdn_uri = value
            elif low_key == "x-ttl":
                self._cdn_ttl = int(value)
            elif low_key == "x-cdn-ssl-uri":
                self._cdn_ssl_uri = value
            elif low_key == "x-cdn-streaming-uri":
                self._cdn_streaming_uri = value
            elif low_key == "x-cdn-ios-uri":
                self._cdn_ios_uri = value
            elif low_key == "x-log-retention":
                self._cdn_log_retention = (value == "True")


    def get_metadata(self, prefix=None):
        """
        Returns a dictionary containing the metadata for this container.
        """
        return self.manager.get_metadata(self, prefix=prefix)


    def set_metadata(self, metadata, clear=False, prefix=None):
        """
        Accepts a dictionary of metadata key/value pairs and updates the
        specified container metadata with them.

        If 'clear' is True, any existing metadata is deleted and only the
        passed metadata is retained. Otherwise, the values passed here update
        the container's metadata.

        The 'extra_info' parameter is included for backwards compatibility. It
        is no longer used at all, and will not be modified with swiftclient
        info, since swiftclient is not used any more.

        By default, the standard container metadata prefix
        ('X-Container-Meta-') is prepended to the header name if it isn't
        present. For non-standard headers, you must include a non-None prefix,
        such as an empty string.
        """
        return self.manager.set_metadata(self, metadata, clear=clear,
                prefix=prefix)


    def remove_metadata_key(self, key, prefix=None):
        """
        Removes the specified key from the container's metadata. If the key
        does not exist in the metadata, nothing is done.
        """
        return self.manager.remove_metadata_key(self, key, prefix=prefix)


    def set_web_index_page(self, page):
        """
        Sets the header indicating the index page in this container when
        creating a static website.

        Note: the container must be CDN-enabled for this to have any effect.
        """
        return self.manager.set_web_index_page(self, page)


    def set_web_error_page(self, page):
        """
        Sets the header indicating the error page in this container when
        creating a static website.

        Note: the container must be CDN-enabled for this to have any effect.
        """
        return self.manager.set_web_error_page(self, page)


    def make_public(self, ttl=None):
        """
        Enables CDN access for this container, and optionally sets the TTL.
        """
        return self.manager.make_public(self, ttl=ttl)


    def make_private(self):
        """
        Disables CDN access to this container. It may still appear public until
        the TTL expires.
        """
        return self.manager.make_private(self)


    def purge_cdn_object(self, obj, email_addresses=None):
        """
        Removes a CDN-enabled object from public access before the TTL expires.
        Please note that there is a limit (at this time) of 25 such requests;
        if you need to purge more than that, you must contact support.

        If one or more email_addresses are included, an email confirming the
        purge is sent to each address.
        """
        return self.object_manager.purge(obj, email_addresses=email_addresses)


    def get_object(self, item):
        """
        Returns a StorageObject matching the specified item. If no such object
        exists, a NotFound exception is raised. If 'item' is not a string, that
        item is returned unchanged.
        """
        if isinstance(item, six.string_types):
            item = self.object_manager.get(item)
        return item


    def list(self, marker=None, limit=None, prefix=None, delimiter=None,
            end_marker=None, full_listing=False, return_raw=False):
        """
        List the objects in this container, using the parameters to control the
        number and content of objects. Note that this is limited by the
        absolute request limits of Swift (currently 10,000 objects). If you
        need to list all objects in the container, use the `list_all()` method
        instead.
        """
        if full_listing:
            return self.list_all(prefix=prefix)
        else:
            return self.object_manager.list(marker=marker, limit=limit,
                    prefix=prefix, delimiter=delimiter, end_marker=end_marker,
                    return_raw=return_raw)


    def list_all(self, prefix=None):
        """
        List all the objects in this container, optionally filtered by an
        initial prefix. Returns an iterator that will yield all the objects in
        the container, even if the number exceeds the absolute limits of Swift.
        """
        return self.manager.object_listing_iterator(self, prefix=prefix)


    def list_object_names(self, marker=None, limit=None, prefix=None,
            delimiter=None, end_marker=None, full_listing=False):
        """
        Returns a list of the names of all the objects in this container. The
        same pagination parameters apply as in self.list().
        """
        if full_listing:
            objects = self.list_all(prefix=prefix)
        else:
            objects = self.list(marker=marker, limit=limit, prefix=prefix,
                    delimiter=delimiter, end_marker=end_marker)
        return [obj.name for obj in objects]


    def find(self, **kwargs):
        """
        Finds a single object with attributes matching ``**kwargs``.

        This isn't very efficient: it loads the entire list then filters on
        the Python side.
        """
        return self.object_manager.find(**kwargs)


    def findall(self, **kwargs):
        """
        Finds all objects with attributes matching ``**kwargs``.

        This isn't very efficient: it loads the entire list then filters on
        the Python side.
        """
        return self.object_manager.findall(**kwargs)


    def create(self, file_or_path=None, data=None, obj_name=None,
            content_type=None, etag=None, content_encoding=None,
            content_length=None, ttl=None, chunked=False, metadata=None,
            chunk_size=None, headers=None, return_none=False):
        """
        Creates or replaces a storage object in this container.

        The content of the object can either be a stream of bytes (`data`), or
        a file on disk (`file_or_path`). The disk file can be either an open
        file-like object, or an absolute path to the file on disk.

        When creating object from a data stream, you must specify the name of
        the object to be created in the container via the `obj_name` parameter.
        When working with a file, though, if no `obj_name` value is specified,
        the file`s name will be used.

        You may optionally set the `content_type` and `content_encoding`
        parameters; pyrax will create the appropriate headers when the object
        is stored. If no `content_type` is specified, the object storage system
        will make an intelligent guess based on the content of the object.

        If the size of the file is known, it can be passed as `content_length`.

        If you wish for the object to be temporary, specify the time it should
        be stored in seconds in the `ttl` parameter. If this is specified, the
        object will be deleted after that number of seconds.

        If you wish to store a stream of data (i.e., where you don't know the
        total size in advance), set the `chunked` parameter to True, and omit
        the `content_length` and `etag` parameters. This allows the data to be
        streamed to the object in the container without having to be written to
        disk first.
        """
        return self.object_manager.create(file_or_path=file_or_path,
                data=data, obj_name=obj_name, content_type=content_type,
                etag=etag, content_encoding=content_encoding,
                content_length=content_length, ttl=ttl, chunked=chunked,
                metadata=metadata, chunk_size=chunk_size, headers=headers,
                return_none=return_none)


    def store_object(self, obj_name, data, content_type=None, etag=None,
            content_encoding=None, ttl=None, return_none=False,
            headers=None, extra_info=None):
        """
        Creates a new object in this container, and populates it with the given
        data. A StorageObject reference to the uploaded file will be returned,
        unless 'return_none' is set to True.

        The 'extra_info' parameter is included for backwards compatibility. It
        is no longer used at all, and will not be modified with swiftclient
        info, since swiftclient is not used any more.
        """
        return self.create(obj_name=obj_name, data=data,
                content_type=content_type, etag=etag,
                content_encoding=content_encoding, ttl=ttl,
                return_none=return_none, headers=headers)


    def upload_file(self, file_or_path, obj_name=None, content_type=None,
            etag=None, return_none=False, content_encoding=None, ttl=None,
            content_length=None, headers=None):
        """
        Uploads the specified file to this container. If no name is supplied,
        the file's name will be used. Either a file path or an open file-like
        object may be supplied. A StorageObject reference to the uploaded file
        will be returned, unless 'return_none' is set to True.

        You may optionally set the `content_type` and `content_encoding`
        parameters; pyrax will create the appropriate headers when the object
        is stored.

        If the size of the file is known, it can be passed as `content_length`.

        If you wish for the object to be temporary, specify the time it should
        be stored in seconds in the `ttl` parameter. If this is specified, the
        object will be deleted after that number of seconds.

        The 'extra_info' parameter is included for backwards compatibility. It
        is no longer used at all, and will not be modified with swiftclient
        info, since swiftclient is not used any more.
        """
        return self.create(file_or_path=file_or_path, obj_name=obj_name,
                content_type=content_type, etag=etag,
                content_encoding=content_encoding, headers=headers,
                content_length=content_length, ttl=ttl,
                return_none=return_none)


    def fetch(self, obj, include_meta=False, chunk_size=None, size=None,
            extra_info=None):
        """
        Fetches the object from storage.

        If 'include_meta' is False, only the bytes representing the
        stored object are returned.

        Note: if 'chunk_size' is defined, you must fully read the object's
        contents before making another request.

        If 'size' is specified, only the first 'size' bytes of the object will
        be returned. If the object if smaller than 'size', the entire object is
        returned.

        When 'include_meta' is True, what is returned from this method is a
        2-tuple:
            Element 0: a dictionary containing metadata about the file.
            Element 1: a stream of bytes representing the object's contents.

        The 'extra_info' parameter is included for backwards compatibility. It
        is no longer used at all, and will not be modified with swiftclient
        info, since swiftclient is not used any more.
        """
        return self.object_manager.fetch(obj, include_meta=include_meta,
                chunk_size=chunk_size, size=size)


    def fetch_object(self, obj_name, include_meta=False, chunk_size=None):
        """
        Alias for self.fetch(); included for backwards compatibility
        """
        return self.fetch(obj=obj_name, include_meta=include_meta,
                chunk_size=chunk_size)


    def fetch_partial(self, obj, size):
        """
        Returns the first 'size' bytes of an object. If the object is smaller
        than the specified 'size' value, the entire object is returned.
        """
        return self.object_manager.fetch_partial(obj, size)


    def download(self, obj, directory, structure=True):
        """
        Fetches the object from storage, and writes it to the specified
        directory. The directory must exist before calling this method.

        If the object name represents a nested folder structure, such as
        "foo/bar/baz.txt", that folder structure will be created in the target
        directory by default. If you do not want the nested folders to be
        created, pass `structure=False` in the parameters.
        """
        return self.object_manager.download(obj, directory, structure=structure)


    def download_object(self, obj_name, directory, structure=True):
        """
        Alias for self.download(); included for backwards compatibility
        """
        return self.download(obj=obj_name, directory=directory,
                structure=structure)


    def delete(self, del_objects=False):
        """
        Deletes this Container. If the container contains objects, the
        command will fail unless 'del_objects' is passed as True. In that
        case, each object will be deleted first, and then the container.
        """
        return self.manager.delete(self, del_objects=del_objects)


    def delete_object(self, obj):
        """
        Deletes the object from this container.

        The 'obj' parameter can either be the name of the object, or a
        StorageObject representing the object to be deleted.
        """
        return self.object_manager.delete(obj)


    def delete_object_in_seconds(self, obj, seconds, extra_info=None):
        """
        Sets the object in this container to be deleted after the specified
        number of seconds.

        The 'extra_info' parameter is included for backwards compatibility. It
        is no longer used at all, and will not be modified with swiftclient
        info, since swiftclient is not used any more.
        """
        return self.manager.delete_object_in_seconds(self, obj, seconds)


    def delete_all_objects(self, async=False):
        """
        Deletes all objects from this container.

        By default the call will block until all objects have been deleted. By
        passing True for the 'async' parameter, this method will not block, and
        instead return an object that can be used to follow the progress of the
        deletion. When deletion is complete the bulk deletion object's
        'results' attribute will be populated with the information returned
        from the API call. In synchronous mode this is the value that is
        returned when the call completes. It is a dictionary with the following
        keys:

            deleted - the number of objects deleted
            not_found - the number of objects not found
            status - the HTTP return status code. '200 OK' indicates success
            errors - a list of any errors returned by the bulk delete call
        """
        nms = self.list_object_names(full_listing=True)
        return self.object_manager.delete_all_objects(nms, async=async)


    def copy_object(self, obj, new_container, new_obj_name=None,
            content_type=None):
        """
        Copies the object to the new container, optionally giving it a new name.
        If you copy to the same container, you must supply a different name.
        """
        return self.manager.copy_object(self, obj, new_container,
                new_obj_name=new_obj_name, content_type=content_type)


    def move_object(self, obj, new_container, new_obj_name=None,
            new_reference=False, content_type=None, extra_info=None):
        """
        Works just like copy_object, except that the source object is deleted
        after a successful copy.

        You can optionally change the content_type of the object by supplying
        that in the 'content_type' parameter.

        NOTE: any references to the original object will no longer be valid;
        you will have to get a reference to the new object by passing True for
        the 'new_reference' parameter. When this is True, a reference to the
        newly moved object is returned. Otherwise, the etag for the moved
        object is returned.

        The 'extra_info' parameter is included for backwards compatibility. It
        is no longer used at all, and will not be modified with swiftclient
        info, since swiftclient is not used any more.
        """
        return self.manager.move_object(self, obj, new_container,
                new_obj_name=new_obj_name, new_reference=new_reference,
                content_type=content_type)


    def change_object_content_type(self, obj, new_ctype, guess=False):
        """
        Copies object to itself, but applies a new content-type. The guess
        feature requires this container to be CDN-enabled. If not, then the
        content-type must be supplied. If using guess with a CDN-enabled
        container, new_ctype can be set to None. Failure during the put will
        result in an exception.
        """
        return self.manager.change_object_content_type(self, obj, new_ctype,
                guess=guess)


    def get_temp_url(self, obj, seconds, method="GET", key=None, cached=True):
        """
        Given a storage object in this container, returns a URL that can be
        used to access that object. The URL will expire after `seconds`
        seconds.

        The only methods supported are GET and PUT. Anything else will raise an
        `InvalidTemporaryURLMethod` exception.

        If you have your Temporary URL key, you can pass it in directly and
        potentially save an API call to retrieve it. If you don't pass in the
        key, and don't wish to use any cached value, pass `cached=False`.
        """
        return self.manager.get_temp_url(self, obj, seconds, method=method,
                key=key, cached=cached)


    def get_object_metadata(self, obj, prefix=None):
        """
        Returns the metadata for the specified object as a dict.
        """
        return self.object_manager.get_metadata(obj, prefix)


    def set_object_metadata(self, obj, metadata, clear=False, extra_info=None,
            prefix=None):
        """
        Accepts a dictionary of metadata key/value pairs and updates the
        specified object metadata with them.

        If 'clear' is True, any existing metadata is deleted and only the
        passed metadata is retained. Otherwise, the values passed here update
        the object's metadata.

        The 'extra_info' parameter is included for backwards compatibility. It
        is no longer used at all, and will not be modified with swiftclient
        info, since swiftclient is not used any more.

        By default, the standard object metadata prefix ('X-Object-Meta-') is
        prepended to the header name if it isn't present. For non-standard
        headers, you must include a non-None prefix, such as an empty string.
        """
        return self.object_manager.set_metadata(obj, metadata, clear=clear,
                prefix=prefix)


    def list_subdirs(self, marker=None, limit=None, prefix=None, delimiter=None,
            full_listing=False):
        """
        Return a list of the namesrepresenting the pseudo-subdirectories in
        this container. You can use the marker and limit params to handle
        pagination, and the prefix param to filter the objects returned. The
        delimiter param is there for backwards compatibility only, as the call
        requires the delimiter to be '/'.
        """
        return self.manager.list_subdirs(self, marker=marker, limit=limit,
                prefix=prefix, delimiter=delimiter, full_listing=full_listing)


    def remove_from_cache(self, obj):
        """
        Not used anymore. Included for backwards compatibility.
        """
        pass


    # BEGIN - CDN property definitions ##
    def _get_cdn_log_retention(self):
        if self._cdn_log_retention is FAULT:
            self._fetch_cdn_data()
        return self._cdn_log_retention

    def _set_cdn_log_retention(self, val):
        self.manager.set_cdn_log_retention(self, val)
        self._cdn_log_retention = val


    def _get_cdn_enabled(self):
        if self._cdn_enabled is FAULT:
            self._fetch_cdn_data()
        return self._cdn_enabled

    def _set_cdn_enabled(self, val):
        self._cdn_enabled = val


    def _get_cdn_uri(self):
        if self._cdn_uri is FAULT:
            self._fetch_cdn_data()
        return self._cdn_uri

    def _set_cdn_uri(self, val):
        self._cdn_uri = val


    def _get_cdn_ttl(self):
        if self._cdn_ttl is FAULT:
            self._fetch_cdn_data()
        return self._cdn_ttl

    def _set_cdn_ttl(self, val):
        self._cdn_ttl = val


    def _get_cdn_ssl_uri(self):
        if self._cdn_ssl_uri is FAULT:
            self._fetch_cdn_data()
        return self._cdn_ssl_uri

    def _set_cdn_ssl_uri(self, val):
        self._cdn_ssl_uri = val


    def _get_cdn_streaming_uri(self):
        if self._cdn_streaming_uri is FAULT:
            self._fetch_cdn_data()
        return self._cdn_streaming_uri

    def _set_cdn_streaming_uri(self, val):
        self._cdn_streaming_uri = val


    def _get_cdn_ios_uri(self):
        if self._cdn_ios_uri is FAULT:
            self._fetch_cdn_data()
        return self._cdn_ios_uri

    def _set_cdn_ios_uri(self, val):
        self._cdn_ios_uri = val


    cdn_enabled = property(_get_cdn_enabled, _set_cdn_enabled)
    cdn_log_retention = property(_get_cdn_log_retention, _set_cdn_log_retention)
    cdn_uri = property(_get_cdn_uri, _set_cdn_uri)
    cdn_ttl = property(_get_cdn_ttl, _set_cdn_ttl)
    cdn_ssl_uri = property(_get_cdn_ssl_uri, _set_cdn_ssl_uri)
    cdn_streaming_uri = property(_get_cdn_streaming_uri, _set_cdn_streaming_uri)
    cdn_ios_uri = property(_get_cdn_ios_uri, _set_cdn_ios_uri)
    # END - CDN property definitions ##



class ContainerManager(BaseManager):
    def list(self, limit=None, marker=None, end_marker=None, prefix=None):
        """
        Swift doesn't return listings in the same format as the rest of
        OpenStack, so this method has to be overriden.
        """
        uri = "/%s" % self.uri_base
        qs = utils.dict_to_qs({"marker": marker, "limit": limit,
                "prefix": prefix, "end_marker": end_marker})
        if qs:
            uri = "%s?%s" % (uri, qs)
        resp, resp_body = self.api.method_get(uri)
        return [Container(self, res, loaded=False)
                for res in resp_body if res]


    @_handle_container_not_found
    def get(self, container):
        """
        Returns a Container matching the specified container name. If no such
        container exists, a NoSuchContainer exception is raised.
        """
        name = utils.get_name(container)
        uri = "/%s" % name
        resp, resp_body = self.api.method_head(uri)
        hdrs = resp.headers
        data = {"total_bytes": int(hdrs.get("x-container-bytes-used", "0")),
                "object_count": int(hdrs.get("x-container-object-count", "0")),
                "name": name}
        return Container(self, data, loaded=False)


    def create(self, name, metadata=None, prefix=None, *args, **kwargs):
        """
        Creates a new container, and returns a Container object that represents
        that contianer. If a container by the same name already exists, no
        exception is raised; instead, a reference to that existing container is
        returned.
        """
        uri = "/%s" % name
        headers = {}
        if prefix is None:
            prefix = CONTAINER_META_PREFIX
        if metadata:
            metadata = _massage_metakeys(metadata, prefix)
            headers = metadata
        resp, resp_body = self.api.method_put(uri, headers=headers)
        if resp.status_code in (201, 202):
            hresp, hresp_body = self.api.method_head(uri)
            num_obj = int(hresp.headers.get("x-container-object-count", "0"))
            num_bytes = int(hresp.headers.get("x-container-bytes-used", "0"))
            cont_info = {"name": name, "object_count": num_obj,
                    "total_bytes": num_bytes}
            return Container(self, cont_info)
        elif resp.status_code == 400:
            raise exc.ClientException("Container creation failed: %s" %
                    resp_body)


    @_handle_container_not_found
    def delete(self, container, del_objects=False):
        """
        Deletes the specified container. If the container contains objects, the
        command will fail unless 'del_objects' is passed as True. In that case,
        each object will be deleted first, and then the container.
        """
        if del_objects:
            nms = self.list_object_names(container, full_listing=True)
            self.api.bulk_delete(container, nms, async=False)
        uri = "/%s" % utils.get_name(container)
        resp, resp_body = self.api.method_delete(uri)


    def _create_body(self, name, *args, **kwargs):
        """
        Container creation requires no body.
        """
        return None


    @_handle_container_not_found
    def fetch_cdn_data(self, container):
        """
        Returns a dict containing the CDN information for the specified
        container. If the container is not CDN-enabled, returns an empty dict.
        """
        name = utils.get_name(container)
        uri = "/%s" % name
        try:
            resp, resp_body = self.api.cdn_request(uri, "HEAD")
        except exc.NotCDNEnabled:
            return {}
        return resp.headers


    def get_account_headers(self):
        """
        Return the headers for the account. This includes all the headers, not
        just the account-specific headers. The calling program is responsible
        for only using the ones that it needs.
        """
        resp, resp_body = self.api.method_head("/")
        return resp.headers


    @_handle_container_not_found
    def get_headers(self, container):
        """
        Return the headers for the specified container.
        """
        uri = "/%s" % utils.get_name(container)
        resp, resp_body = self.api.method_head(uri)
        return resp.headers


    def get_account_metadata(self, prefix=None):
        """
        Returns a dictionary containing metadata about the account.
        """
        headers = self.get_account_headers()
        if prefix is None:
            prefix = ACCOUNT_META_PREFIX
        low_prefix = prefix.lower()
        ret = {}
        for hkey, hval in list(headers.items()):
            lowkey = hkey.lower()
            if lowkey.startswith(low_prefix):
                cleaned = hkey.replace(low_prefix, "").replace("-", "_")
                ret[cleaned] = hval
        return ret


    def set_account_metadata(self, metadata, clear=False, prefix=None):
        """
        Accepts a dictionary of metadata key/value pairs and updates the
        account metadata with them.

        If 'clear' is True, any existing metadata is deleted and only the
        passed metadata is retained. Otherwise, the values passed here update
        the account's metadata.

        By default, the standard account metadata prefix ('X-Account-Meta-') is
        prepended to the header name if it isn't present. For non-standard
        headers, you must include a non-None prefix, such as an empty string.
        """
        # Add the metadata prefix, if needed.
        if prefix is None:
            prefix = ACCOUNT_META_PREFIX
        massaged = _massage_metakeys(metadata, prefix)
        new_meta = {}
        if clear:
            curr_meta = self.get_account_metadata(prefix=prefix)
            for ckey in curr_meta:
                new_meta[ckey] = ""
            new_meta = _massage_metakeys(new_meta, prefix)
        utils.case_insensitive_update(new_meta, massaged)
        uri = "/"
        resp, resp_body = self.api.method_post(uri, headers=new_meta)
        return 200 <= resp.status_code <= 299


    def delete_account_metadata(self, prefix=None):
        """
        Removes all metadata matching the specified prefix from the account.

        By default, the standard account metadata prefix ('X-Account-Meta-') is
        prepended to the header name if it isn't present. For non-standard
        headers, you must include a non-None prefix, such as an empty string.
        """
        # Add the metadata prefix, if needed.
        if prefix is None:
            prefix = ACCOUNT_META_PREFIX
        curr_meta = self.get_account_metadata(prefix=prefix)
        for ckey in curr_meta:
            curr_meta[ckey] = ""
        new_meta = _massage_metakeys(curr_meta, prefix)
        uri = "/"
        resp, resp_body = self.api.method_post(uri, headers=new_meta)
        return 200 <= resp.status_code <= 299


    def get_metadata(self, container, prefix=None):
        """
        Returns a dictionary containing the metadata for the container.
        """
        headers = self.get_headers(container)
        if prefix is None:
            prefix = CONTAINER_META_PREFIX
        low_prefix = prefix.lower()
        ret = {}
        for hkey, hval in list(headers.items()):
            if hkey.lower().startswith(low_prefix):
                cleaned = hkey.replace(low_prefix, "").replace("-", "_")
                ret[cleaned] = hval
        return ret


    @_handle_container_not_found
    def set_metadata(self, container, metadata, clear=False, prefix=None):
        """
        Accepts a dictionary of metadata key/value pairs and updates the
        specified container metadata with them.

        If 'clear' is True, any existing metadata is deleted and only the
        passed metadata is retained. Otherwise, the values passed here update
        the container's metadata.

        By default, the standard container metadata prefix
        ('X-Container-Meta-') is prepended to the header name if it isn't
        present. For non-standard headers, you must include a non-None prefix,
        such as an empty string.
        """
        # Add the metadata prefix, if needed.
        if prefix is None:
            prefix = CONTAINER_META_PREFIX
        massaged = _massage_metakeys(metadata, prefix)
        new_meta = {}
        if clear:
            curr_meta = self.api.get_container_metadata(container,
                    prefix=prefix)
            for ckey in curr_meta:
                new_meta[ckey] = ""
        utils.case_insensitive_update(new_meta, massaged)
        name = utils.get_name(container)
        uri = "/%s" % name
        resp, resp_body = self.api.method_post(uri, headers=new_meta)
        return 200 <= resp.status_code <= 299


    def remove_metadata_key(self, container, key):
        """
        Removes the specified key from the container's metadata. If the key
        does not exist in the metadata, nothing is done.
        """
        meta_dict = {key: ""}
        return self.set_metadata(container, meta_dict)


    @_handle_container_not_found
    def delete_metadata(self, container, prefix=None):
        """
        Removes all of the container's metadata.

        By default, all metadata beginning with the standard container metadata
        prefix ('X-Container-Meta-') is removed. If you wish to remove all
        metadata beginning with a different prefix, you must specify that
        prefix.
        """
        # Add the metadata prefix, if needed.
        if prefix is None:
            prefix = CONTAINER_META_PREFIX
        new_meta = {}
        curr_meta = self.get_metadata(container, prefix=prefix)
        for ckey in curr_meta:
            new_meta[ckey] = ""
        uri = "/%s" % utils.get_name(container)
        resp, resp_body = self.api.method_post(uri, headers=new_meta)
        return 200 <= resp.status_code <= 299


    @_handle_container_not_found
    def get_cdn_metadata(self, container):
        """
        Returns a dictionary containing the CDN metadata for the container. If
        the container does not exist, a NotFound exception is raised. If the
        container exists, but is not CDN-enabled, a NotCDNEnabled exception is
        raised.
        """
        uri = "%s/%s" % (self.uri_base, utils.get_name(container))
        resp, resp_body = self.api.cdn_request(uri, "HEAD")
        ret = dict(resp.headers)
        # Remove non-CDN headers
        ret.pop("content-length", None)
        ret.pop("content-type", None)
        ret.pop("date", None)
        return ret


    @_handle_container_not_found
    def set_cdn_metadata(self, container, metadata):
        """
        Accepts a dictionary of metadata key/value pairs and updates
        the specified container metadata with them.

        NOTE: arbitrary metadata headers are not allowed. The only metadata
        you can update are: X-Log-Retention, X-CDN-enabled, and X-TTL.
        """
        allowed = ("x-log-retention", "x-cdn-enabled", "x-ttl")
        hdrs = {}
        bad = []
        for mkey, mval in six.iteritems(metadata):
            if mkey.lower() not in allowed:
                bad.append(mkey)
                continue
            hdrs[mkey] = str(mval)
        if bad:
            raise exc.InvalidCDNMetadata("The only CDN metadata you can "
                    "update are: X-Log-Retention, X-CDN-enabled, and X-TTL. "
                    "Received the following illegal item(s): %s" %
                    ", ".join(bad))
        uri = "%s/%s" % (self.uri_base, utils.get_name(container))
        resp, resp_body = self.api.cdn_request(uri, "POST", headers=hdrs)
        return resp


    def get_temp_url(self, container, obj, seconds, method="GET", key=None,
            cached=True):
        """
        Given a storage object in a container, returns a URL that can be used
        to access that object. The URL will expire after `seconds` seconds.

        The only methods supported are GET and PUT. Anything else will raise
        an `InvalidTemporaryURLMethod` exception.

        If you have your Temporary URL key, you can pass it in directly and
        potentially save an API call to retrieve it. If you don't pass in the
        key, and don't wish to use any cached value, pass `cached=False`.
        """
        if not key:
            key = self.api.get_temp_url_key(cached=cached)
        if not key:
            raise exc.MissingTemporaryURLKey("You must set the key for "
                    "Temporary URLs before you can generate them. This is "
                    "done via the `set_temp_url_key()` method.")
        cname = utils.get_name(container)
        oname = utils.get_name(obj)
        mod_method = method.upper().strip()
        if mod_method not in ("GET", "PUT"):
            raise exc.InvalidTemporaryURLMethod("Method must be either 'GET' "
                    "or 'PUT'; received '%s'." % method)
        mgt_url = self.api.management_url
        mtch = re.search(r"/v\d/", mgt_url)
        start = mtch.start()
        base_url = mgt_url[:start]
        path_parts = (mgt_url[start:], cname, oname)
        cleaned = (part.strip("/\\") for part in path_parts)
        pth = "/%s" % "/".join(cleaned)
        if isinstance(pth, six.string_types):
            pth = pth.encode(pyrax.get_encoding())
        expires = int(time.time() + int(seconds))
        hmac_body = "%s\n%s\n%s" % (mod_method, expires, pth)
        try:
            sig = hmac.new(key, hmac_body, hashlib.sha1).hexdigest()
        except TypeError as e:
            raise exc.UnicodePathError("Due to a bug in Python, the TempURL "
                    "function only works with ASCII object paths.")
        temp_url = "%s%s?temp_url_sig=%s&temp_url_expires=%s" % (base_url, pth,
                sig, expires)
        return temp_url


    def list_containers_info(self, limit=None, marker=None):
        """Returns a list of info on Containers.

        For each container, a dict containing the following keys is returned:
        \code
            name - the name of the container
            count - the number of objects in the container
            bytes - the total bytes in the container
        """
        uri = ""
        qs = utils.dict_to_qs({"limit": limit, "marker": marker})
        if qs:
            uri += "%s?%s" % (uri, qs)
        resp, resp_body = self.api.method_get(uri)
        return resp_body


    def list_public_containers(self):
        """
        Returns a list of the names of all CDN-enabled containers.
        """
        resp, resp_body = self.api.cdn_request("", "GET")
        return [cont["name"] for cont in resp_body]


    def make_public(self, container, ttl=None):
        """
        Enables CDN access for the specified container, and optionally sets the
        TTL for the container.
        """
        return self._set_cdn_access(container, public=True, ttl=ttl)


    def make_private(self, container):
        """
        Disables CDN access to a container. It may still appear public until
        its TTL expires.
        """
        return self._set_cdn_access(container, public=False)


    @_handle_container_not_found
    def _set_cdn_access(self, container, public, ttl=None):
        """
        Enables or disables CDN access for the specified container, and
        optionally sets the TTL for the container when enabling access.
        """
        headers = {"X-Cdn-Enabled": "%s" % public}
        if public and ttl:
            headers["X-Ttl"] = ttl
        self.api.cdn_request("/%s" % utils.get_name(container), method="PUT",
                headers=headers)


    @_handle_container_not_found
    def get_cdn_log_retention(self, container):
        """
        Returns the status of the setting for CDN log retention for the
        specified container.
        """
        resp, resp_body = self.api.cdn_request("/%s" %
                utils.get_name(container), method="HEAD")
        return resp.headers.get("x-log-retention").lower() == "true"


    @_handle_container_not_found
    def set_cdn_log_retention(self, container, enabled):
        """
        Enables or disables whether CDN access logs for the specified container
        are collected and stored on Cloud Files.
        """
        headers = {"X-Log-Retention": "%s" % enabled}
        self.api.cdn_request("/%s" % utils.get_name(container), method="PUT",
                headers=headers)


    @_handle_container_not_found
    def get_container_streaming_uri(self, container):
        """
        Returns the URI for streaming content, or None if CDN is not enabled.
        """
        resp, resp_body = self.api.cdn_request("/%s" %
                utils.get_name(container), method="HEAD")
        return resp.headers.get("x-cdn-streaming-uri")


    @_handle_container_not_found
    def get_container_ios_uri(self, container):
        """
        Returns the iOS URI, or None if CDN is not enabled.
        """
        resp, resp_body = self.api.cdn_request("/%s" %
                utils.get_name(container), method="HEAD")
        return resp.headers.get("x-cdn-ios-uri")


    @_handle_container_not_found
    def set_web_index_page(self, container, page):
        """
        Sets the header indicating the index page in a container
        when creating a static website.

        Note: the container must be CDN-enabled for this to have
        any effect.
        """
        headers = {"X-Container-Meta-Web-Index": "%s" % page}
        self.api.cdn_request("/%s" % utils.get_name(container), method="POST",
                headers=headers)


    @_handle_container_not_found
    def set_web_error_page(self, container, page):
        """
        Sets the header indicating the error page in a container
        when creating a static website.

        Note: the container must be CDN-enabled for this to have
        any effect.
        """
        headers = {"X-Container-Meta-Web-Error": "%s" % page}
        self.api.cdn_request("/%s" % utils.get_name(container), method="POST",
                headers=headers)


    @assure_container
    def purge_cdn_object(self, container, obj, email_addresses=None):
        """
        Removes a CDN-enabled object from public access before the TTL expires.
        Please note that there is a limit (at this time) of 25 such requests;
        if you need to purge more than that, you must contact support.

        If one or more email_addresses are included, an email confirming the
        purge is sent to each address.
        """
        return container.purge_cdn_object(obj, email_addresses=email_addresses)


    @assure_container
    def list_objects(self, container, limit=None, marker=None, prefix=None,
            delimiter=None, end_marker=None, full_listing=False):
        """
        Return a list of StorageObjects representing the objects in this
        container. You can use the marker, end_marker, and limit params to
        handle pagination, and the prefix and delimiter params to filter the
        objects returned. By default only the first 10,000 objects are
        returned; if you need to access more than that, set the 'full_listing'
        parameter to True.
        """
        if full_listing:
            return container.list_all(prefix=prefix)
        return container.list(limit=limit, marker=marker, prefix=prefix,
                delimiter=delimiter, end_marker=end_marker)


    @assure_container
    def list_object_names(self, container, marker=None, limit=None, prefix=None,
            delimiter=None, end_marker=None, full_listing=False):
        """
        Return a list of then names of the objects in this container. You can
        use the marker, end_marker, and limit params to handle pagination, and
        the prefix and delimiter params to filter the objects returned. By
        default only the first 10,000 objects are returned; if you need to
        access more than that, set the 'full_listing' parameter to True.
        """
        return container.list_object_names(marker=marker, limit=limit,
                prefix=prefix, delimiter=delimiter, end_marker=end_marker,
                full_listing=full_listing)


    @assure_container
    def object_listing_iterator(self, container, prefix=None):
        """
        Returns an iterator that can be used to access the objects within this
        container. They can be optionally limited by a prefix.
        """
        return StorageObjectIterator(container.object_manager, prefix=prefix)


    @assure_container
    def list_subdirs(self, container, marker=None, limit=None, prefix=None,
            delimiter=None, full_listing=False):
        """
        Returns a list of StorageObjects representing the pseudo-subdirectories
        in the specified container. You can use the marker and limit params to
        handle pagination, and the prefix param to filter the objects returned.
        The 'delimiter' parameter is ignored, as the only meaningful value is
        '/'.
        """
        mthd = container.list_all if full_listing else container.list
        objs = mthd(marker=marker, limit=limit, prefix=prefix, delimiter="/",
                return_raw=True)
        sdirs = [obj for obj in objs if "subdir" in obj]
        mgr = container.object_manager
        return [StorageObject(mgr, sdir) for sdir in sdirs]


    @assure_container
    def get_object(self, container, obj):
        """
        Returns a StorageObject representing the requested object.
        """
        return container.get_object(obj)


    @assure_container
    def create_object(self, container, file_or_path=None, data=None,
            obj_name=None, content_type=None, etag=None, content_encoding=None,
            content_length=None, ttl=None, chunked=False, metadata=None,
            chunk_size=None, headers=None, return_none=False):
        """
        Creates or replaces a storage object in the specified container.
        Returns a StorageObject reference will be returned, unless the
        'return_none' parameter is True.

        The content of the object can either be a stream of bytes (`data`), or
        a file on disk (`file_or_path`). The disk file can be either an open
        file-like object, or an absolute path to the file on disk.

        When creating object from a data stream, you must specify the name of
        the object to be created in the container via the `obj_name` parameter.
        When working with a file, though, if no `obj_name` value is specified,
        the file`s name will be used.

        You may optionally set the `content_type` and `content_encoding`
        parameters; pyrax will create the appropriate headers when the object
        is stored. If no `content_type` is specified, the object storage system
        will make an intelligent guess based on the content of the object.

        If the size of the file is known, it can be passed as `content_length`.

        If you wish for the object to be temporary, specify the time it should
        be stored in seconds in the `ttl` parameter. If this is specified, the
        object will be deleted after that number of seconds.
        """
        return container.create(file_or_path=file_or_path, data=data,
                obj_name=obj_name, content_type=content_type, etag=etag,
                content_encoding=content_encoding,
                content_length=content_length, ttl=ttl, chunked=chunked,
                metadata=metadata, chunk_size=chunk_size, headers=headers,
                return_none=return_none)


    @assure_container
    def fetch_object(self, container, obj, include_meta=False,
            chunk_size=None, size=None, extra_info=None):
        """
        Fetches the object from storage.

        If 'include_meta' is False, only the bytes representing the
        stored object are returned.

        Note: if 'chunk_size' is defined, you must fully read the object's
        contents before making another request.

        If 'size' is specified, only the first 'size' bytes of the object will
        be returned. If the object if smaller than 'size', the entire object is
        returned.

        When 'include_meta' is True, what is returned from this method is a
        2-tuple:
            Element 0: a dictionary containing metadata about the file.
            Element 1: a stream of bytes representing the object's contents.

        The 'extra_info' parameter is included for backwards compatibility. It
        is no longer used at all, and will not be modified with swiftclient
        info, since swiftclient is not used any more.
        """
        return container.fetch(obj, include_meta=include_meta,
                chunk_size=chunk_size, size=size)


    @assure_container
    def fetch_partial(self, container, obj, size):
        """
        Returns the first 'size' bytes of an object. If the object is smaller
        than the specified 'size' value, the entire object is returned.
        """
        return container.fetch_partial(obj, size)


    @assure_container
    def download_object(self, container, obj, directory, structure=True):
        """
        Fetches the object from storage, and writes it to the specified
        directory. The directory must exist before calling this method.

        If the object name represents a nested folder structure, such as
        "foo/bar/baz.txt", that folder structure will be created in the target
        directory by default. If you do not want the nested folders to be
        created, pass `structure=False` in the parameters.
        """
        return container.download(obj, directory, structure=structure)


    @assure_container
    def delete_object(self, container, obj):
        """
        Deletes the object from the specified container.

        The 'obj' parameter can either be the name of the object, or a
        StorageObject representing the object to be deleted.
        """
        return container.delete_object(obj)


    @_handle_container_not_found
    def copy_object(self, container, obj, new_container, new_obj_name=None,
            content_type=None):
        """
        Copies the object to the new container, optionally giving it a new name.
        If you copy to the same container, you must supply a different name.

        Returns the etag of the newly-copied object.

        You can optionally change the content_type of the object by supplying
        that in the 'content_type' parameter.
        """
        nm = new_obj_name or utils.get_name(obj)
        uri = "/%s/%s" % (utils.get_name(new_container), nm)
        copy_from = "/%s/%s" % (utils.get_name(container), utils.get_name(obj))
        headers = {"X-Copy-From": copy_from,
                "Content-Length": "0"}
        if content_type:
            headers["Content-Type"] = content_type
        resp, resp_body = self.api.method_put(uri, headers=headers)
        return resp.headers.get("etag")


    def move_object(self, container, obj, new_container, new_obj_name=None,
            new_reference=False, content_type=None):
        """
        Works just like copy_object, except that the source object is deleted
        after a successful copy.

        You can optionally change the content_type of the object by supplying
        that in the 'content_type' parameter.

        NOTE: any references to the original object will no longer be valid;
        you will have to get a reference to the new object by passing True for
        the 'new_reference' parameter. When this is True, a reference to the
        newly moved object is returned. Otherwise, the etag for the moved
        object is returned.
        """
        new_obj_etag = self.copy_object(container, obj, new_container,
                new_obj_name=new_obj_name, content_type=content_type)
        if not new_obj_etag:
            return
        # Copy succeeded; delete the original.
        self.delete_object(container, obj)
        if new_reference:
            nm = new_obj_name or utils.get_name(obj)
            return self.get_object(new_container, nm)
        return new_obj_etag


    @assure_container
    def change_object_content_type(self, container, obj, new_ctype,
            guess=False):
        """
        Copies object to itself, but applies a new content-type. The guess
        feature requires the container to be CDN-enabled. If not, then the
        content-type must be supplied. If using guess with a CDN-enabled
        container, new_ctype can be set to None. Failure during the put will
        result in an exception.
        """
        cname = utils.get_name(container)
        oname = utils.get_name(obj)
        if guess and container.cdn_enabled:
            # Test against the CDN url to guess the content-type.
            obj_url = "%s/%s" % (container.cdn_uri, oname)
            new_ctype = mimetypes.guess_type(obj_url)[0]
        return self.copy_object(container, obj, container,
                content_type=new_ctype)


    def delete_object_in_seconds(self, cont, obj, seconds, extra_info=None):
        """
        Sets the object in the specified container to be deleted after the
        specified number of seconds.

        The 'extra_info' parameter is included for backwards compatibility. It
        is no longer used at all, and will not be modified with swiftclient
        info, since swiftclient is not used any more.
        """
        meta = {"X-Delete-After": seconds}
        self.set_object_metadata(cont, obj, meta, clear=True, prefix="")


    @assure_container
    def get_object_metadata(self, container, obj, prefix=None):
        """
        Returns the metadata for the specified object as a dict.
        """
        return container.get_object_metadata(obj, prefix=prefix)


    @assure_container
    def set_object_metadata(self, container, obj, metadata, clear=False,
            extra_info=None, prefix=None):
        """
        Accepts a dictionary of metadata key/value pairs and updates the
        specified object metadata with them.

        If 'clear' is True, any existing metadata is deleted and only the
        passed metadata is retained. Otherwise, the values passed here update
        the object's metadata.

        'extra_info; is an optional dictionary which will be populated with
        'status', 'reason', and 'headers' keys from the underlying swiftclient
        call.

        By default, the standard object metadata prefix ('X-Object-Meta-') is
        prepended to the header name if it isn't present. For non-standard
        headers, you must include a non-None prefix, such as an empty string.
        """
        return container.set_object_metadata(obj, metadata, clear=clear,
                prefix=prefix)



class StorageObject(BaseResource):
    """
    This class represents an object stored in a Container.
    """
    def __init__(self, manager, info, *args, **kwargs):
        self._container = None
        if ("name" not in info) and ("subdir" in info):
            # Subdir dicts lack a 'name' and 'content_type' key
            info["name"] = info["subdir"]
            info["content_type"] = "pseudo/subdirectory"
        return super(StorageObject, self).__init__(manager, info, *args,
                **kwargs)


    def __repr__(self):
        return "<Object '%s' (%s)>" % (self.name, self.content_type)


    @property
    def id(self):
        """
        StorageObjects use their 'name' attribute as their ID.
        """
        return self.name


    @property
    def total_bytes(self):
        """ Alias for backwards compatibility."""
        return self.bytes


    @property
    def etag(self):
        """ Alias for backwards compatibility."""
        return self.hash


    @property
    def container(self):
        if not self._container:
            self._container = self.manager.container
        return self._container


    def get(self, include_meta=False, chunk_size=None):
        """
        Fetches the object from storage.

        If 'include_meta' is False, only the bytes representing the
        file is returned.

        Note: if 'chunk_size' is defined, you must fully read the object's
        contents before making another request.

        When 'include_meta' is True, what is returned from this method is a
        2-tuple:
            Element 0: a dictionary containing metadata about the file.
            Element 1: a stream of bytes representing the object's contents.
        """
        return self.manager.fetch(obj=self, include_meta=include_meta,
                chunk_size=chunk_size)
    # Changing the name of this method to 'fetch', as 'get' is overloaded.
    fetch = get


    def download(self, directory, structure=True):
        """
        Fetches the object from storage, and writes it to the specified
        directory. The directory must exist before calling this method.

        If the object name represents a nested folder structure, such as
        "foo/bar/baz.txt", that folder structure will be created in the target
        directory by default. If you do not want the nested folders to be
        created, pass `structure=False` in the parameters.
        """
        return self.manager.download(self, directory, structure=structure)


    def copy(self, new_container, new_obj_name=None, extra_info=None):
        """
        Copies this object to the new container, optionally giving it a new
        name.  If you copy to the same container, you must supply a different
        name.
        """
        return self.container.copy_object(self, new_container,
                new_obj_name=new_obj_name)


    def move(self, new_container, new_obj_name=None, extra_info=None):
        """
        Works just like copy_object, except that this object is deleted after a
        successful copy. This means that this storage_object reference will no
        longer be valid.
        """
        return self.container.move_object(self, new_container,
                new_obj_name=new_obj_name)


    def change_content_type(self, new_ctype, guess=False):
        """
        Copies object to itself, but applies a new content-type. The guess
        feature requires the container to be CDN-enabled. If not then the
        content-type must be supplied. If using guess with a CDN-enabled
        container, new_ctype can be set to None.
        Failure during the put will result in a swift exception.
        """
        self.container.change_object_content_type(self, new_ctype=new_ctype,
                guess=guess)


    def purge(self, email_addresses=None):
        """
        Removes a CDN-enabled object from public access before the TTL expires.
        Please note that there is a limit (at this time) of 25 such requests;
        if you need to purge more than that, you must contact support.

        If one or more email_addresses are included, an email confirming the
        purge is sent to each address.
        """
        return self.manager.purge(self, email_addresses=email_addresses)


    def get_metadata(self, prefix=None):
        """
        Returns the metadata for this object as a dict.
        """
        return self.manager.get_metadata(self, prefix)


    def set_metadata(self, metadata, clear=False, prefix=None):
        """
        Accepts a dictionary of metadata key/value pairs and updates the
        specified object metadata with them.

        If 'clear' is True, any existing metadata is deleted and only the
        passed metadata is retained. Otherwise, the values passed here update
        the object's metadata.

        By default, the standard object metadata prefix ('X-Object-Meta-') is
        prepended to the header name if it isn't present. For non-standard
        headers, you must include a non-None prefix, such as an empty string.
        """
        return self.manager.set_metadata(self, metadata, clear=clear,
                prefix=prefix)


    def remove_metadata_key(self, key, prefix=None):
        """
        Removes the specified key from the storage object's metadata. If the
        key does not exist in the metadata, nothing is done.
        """
        self.manager.remove_metadata_key(self, key, prefix=prefix)


    def get_temp_url(self, seconds, method="GET"):
        """
        Returns a URL that can be used to access this object. The URL will
        expire after `seconds` seconds.

        The only methods supported are GET and PUT. Anything else will raise
        an InvalidTemporaryURLMethod exception.
        """
        return self.container.get_temp_url(self, seconds=seconds,
                method=method)


    def delete_in_seconds(self, seconds):
        """
        Sets the object to be deleted after the specified number of seconds.
        """
        self.container.delete_object_in_seconds(self, seconds)



class StorageObjectIterator(utils.ResultsIterator):
    """
    Allows you to iterate over all the objects in a container, even if they
    exceed the limit for any single listing call.
    """
    def _init_methods(self):
        self.list_method = self.manager.list
        # Swift uses the object name as its ID.
        self.marker_att = "name"



class StorageObjectManager(BaseManager):
    """
    Handles all the interactions with StorageObjects.
    """
    @property
    def name(self):
        """The URI base is the same as the container name."""
        return self.uri_base


    @property
    def container(self):
        try:
            return self._container
        except AttributeError:
            cont = self.api.get(self.uri_base)
            self._container = cont
            return cont


    def list(self, marker=None, limit=None, prefix=None, delimiter=None,
            end_marker=None, return_raw=False):
        uri = "/%s" % self.uri_base
        qs = utils.dict_to_qs({"marker": marker, "limit": limit,
                "prefix": prefix, "delimiter": delimiter,
                "end_marker": end_marker})
        if qs:
            uri = "%s?%s" % (uri, qs)
        resp, resp_body = self.api.method_get(uri)
        if return_raw:
            return resp_body
        objs = [StorageObject(self, elem) for elem in resp_body]
        return objs


    @_handle_object_not_found
    def get(self, obj):
        """
        Gets the information about the specified object.

        This overrides the base behavior, since Swift uses HEAD to get
        information, and GET to download the object.
        """
        name = utils.get_name(obj)
        uri = "/%s/%s" % (self.uri_base, name)
        resp, resp_body = self.api.method_head(uri)
        hdrs = resp.headers
        try:
            content_length = int(hdrs.get("content-length"))
        except (TypeError, ValueError):
            content_length = None
        data = {"name": name,
                "bytes": content_length,
                "content_type": hdrs.get("content-type"),
                "hash": hdrs.get("etag"),
                "last_modified": hdrs.get("last-modified"),
                "timestamp": hdrs.get("x-timestamp"),
                }
        return StorageObject(self, data, loaded=True)


    def create(self, file_or_path=None, data=None, obj_name=None,
            content_type=None, etag=None, content_encoding=None,
            content_length=None, ttl=None, chunked=False, metadata=None,
            chunk_size=None, headers=None, return_none=False):
        """
        Creates or replaces a storage object in this container.

        The content of the object can either be a stream of bytes (`data`), or
        a file on disk (`file_or_path`). The disk file can be either an open
        file-like object, or an absolute path to the file on disk.

        When creating object from a data stream, you must specify the name of
        the object to be created in the container via the `obj_name` parameter.
        When working with a file, though, if no `obj_name` value is specified,
        the file`s name will be used.

        You may optionally set the `content_type` and `content_encoding`
        parameters; pyrax will create the appropriate headers when the object
        is stored. If no `content_type` is specified, the object storage system
        will make an intelligent guess based on the content of the object.

        If the size of the file is known, it can be passed as `content_length`.

        If you wish for the object to be temporary, specify the time it should
        be stored in seconds in the `ttl` parameter. If this is specified, the
        object will be deleted after that number of seconds.

        If you wish to store a stream of data (i.e., where you don't know the
        total size in advance), set the `chunked` parameter to True, and omit
        the `content_length` and `etag` parameters. This allows the data to be
        streamed to the object in the container without having to be written to
        disk first.
        """
        # First make sure that there is a content source.
        if (data, file_or_path) == (None, None):
            raise exc.NoContentSpecified("You must specify either a file path, "
                    "an open file-like object, or a stream of bytes when "
                    "creating an object.")
        src = data if data else file_or_path
        if src is file_or_path:
            obj_name = _validate_file_or_path(file_or_path, obj_name)
        if not obj_name:
            raise exc.MissingName("No name for the object to be created has "
                    "been specified, and none can be inferred from context")
        if chunk_size:
            chunked = True
        if chunked:
            chunk_size = chunk_size or DEFAULT_CHUNKSIZE
        headers = headers or {}
        if metadata:
            metadata = _massage_metakeys(metadata, OBJECT_META_PREFIX)
            headers = metadata
        if ttl is not None:
            headers["X-Delete-After"] = ttl
        if src is data:
            self._upload(obj_name, data, content_type,
                    content_encoding, content_length, etag, chunked,
                    chunk_size, headers)
        elif hasattr(file_or_path, "read"):
            self._upload(obj_name, file_or_path, content_type,
                    content_encoding, content_length, etag, False,
                    chunk_size, headers)
        else:
            # Need to wrap the call in a context manager
            with open(file_or_path, "rb") as ff:
                self._upload(obj_name, ff, content_type,
                        content_encoding, content_length, etag, False,
                        chunk_size, headers)
        if return_none:
            return
        return self.get(obj_name)


    def _upload(self, obj_name, content, content_type, content_encoding,
            content_length, etag, chunked, chunk_size, headers):
        """
        Handles the uploading of content, including working around the 5GB
        maximum file size.
        """
        if content_type is not None:
            headers["Content-Type"] = content_type
        if content_encoding is not None:
            headers["Content-Encoding"] = content_encoding
        if isinstance(content, six.string_types):
            fsize = len(content)
        else:
            if chunked:
                fsize = None
            elif content_length is None:
                fsize = get_file_size(content)
            else:
                fsize = content_length
        if fsize <= MAX_FILE_SIZE:
            # We can just upload it as-is.
            return self._store_object(obj_name, content=content, etag=etag,
                    chunked=chunked, chunk_size=chunk_size, headers=headers)
        # Files larger than MAX_FILE_SIZE must be segmented
        # and uploaded separately.
        num_segments = int(math.ceil(float(fsize) / MAX_FILE_SIZE))
        digits = int(math.log10(num_segments)) + 1
        # NOTE: This could be greatly improved with threading or other
        # async design.
        for segment in range(num_segments):
            sequence = str(segment + 1).zfill(digits)
            seg_name = "%s.%s" % (obj_name, sequence)
            with utils.SelfDeletingTempfile() as tmpname:
                with open(tmpname, "wb") as tmp:
                    tmp.write(content.read(MAX_FILE_SIZE))
                with open(tmpname, "rb") as tmp:
                    # We have to calculate the etag for each segment
                    etag = utils.get_checksum(tmp)
                    self._store_object(seg_name, content=tmp, etag=etag,
                            chunked=False, headers=headers)
        # Upload the manifest
        headers.pop("ETag", "")
        headers["X-Object-Manifest"] = "%s/%s." % (self.name, obj_name)
        self._store_object(obj_name, content=None, headers=headers)


    def _store_object(self, obj_name, content, etag=None, chunked=False,
            chunk_size=None, headers=None):
        """
        Handles the low-level creation of a storage object and the uploading of
        the contents of that object.
        """
        head_etag = headers.pop("ETag", "")
        if chunked:
            headers.pop("Content-Length", "")
            headers["Transfer-Encoding"] = "chunked"
        elif etag is None and content is not None:
            etag = utils.get_checksum(content)
        if etag:
            headers["ETag"] = etag
        if not headers.get("Content-Type"):
            headers["Content-Type"] = None
        uri = "/%s/%s" % (self.uri_base, obj_name)
        resp, resp_body = self.api.method_put(uri, data=content,
                headers=headers)


    @_handle_object_not_found
    def fetch(self, obj, include_meta=False, chunk_size=None, size=None,
            extra_info=None):
        """
        Fetches the object from storage.

        If 'include_meta' is False, only the bytes representing the
        stored object are returned.

        Note: if 'chunk_size' is defined, the 'include_meta' parameter is
        ignored.

        If 'size' is specified, only the first 'size' bytes of the object will
        be returned. If the object if smaller than 'size', the entire object is
        returned.

        When 'include_meta' is True, what is returned from this method is a
        2-tuple:
            Element 0: a dictionary containing metadata about the file.
            Element 1: a stream of bytes representing the object's contents.

        The 'extra_info' parameter is included for backwards compatibility. It
        is no longer used at all, and will not be modified with swiftclient
        info, since swiftclient is not used any more.
        """
        uri = "/%s/%s" % (self.uri_base, utils.get_name(obj))
        if chunk_size:
            # Need the total size of the object
            if not isinstance(obj, StorageObject):
                obj = self.get(obj)
            obj_size = obj.total_bytes
            return self._fetch_chunker(uri, chunk_size, size, obj_size)
        headers = {}
        if size:
            headers = {"Range": "bytes=0-%s" % size}
        resp, resp_body = self.api.method_get(uri, headers=headers,
                raw_content=True)
        if include_meta:
            meta_resp, meta_body = self.api.method_head(uri)
            return (meta_resp.headers, resp_body)
        return resp_body


    def _fetch_chunker(self, uri, chunk_size, size, obj_size):
        """
        Returns a generator that returns an object in chunks.
        """
        pos = 0
        total_bytes = 0
        size = size or obj_size
        max_size = min(size, obj_size)
        while True:
            endpos = min(obj_size, pos + chunk_size - 1)
            headers = {"Range": "bytes=%s-%s" % (pos, endpos)}
            resp, resp_body = self.api.method_get(uri, headers=headers,
                    raw_content=True)
            pos = endpos + 1
            if not resp_body:
                # End of file
                raise StopIteration
            yield resp_body
            total_bytes += len(resp_body)
            if total_bytes >= max_size:
                raise StopIteration


    def fetch_partial(self, obj, size):
        """
        Returns the first 'size' bytes of an object. If the object is smaller
        than the specified 'size' value, the entire object is returned.
        """
        return self.fetch(obj, size=size)


    @_handle_object_not_found
    def delete(self, obj):
        """
        Deletes the object if it exists; raises NoSuchObject exception if it
        does not exist.
        """
        return super(StorageObjectManager, self).delete(obj)


    def delete_all_objects(self, nms, async=False):
        """
        Deletes all objects from this container.

        By default the call will block until all objects have been deleted. By
        passing True for the 'async' parameter, this method will not block, and
        instead return an object that can be used to follow the progress of the
        deletion. When deletion is complete the bulk deletion object's
        'results' attribute will be populated with the information returned
        from the API call. In synchronous mode this is the value that is
        returned when the call completes. It is a dictionary with the following
        keys:

            deleted - the number of objects deleted
            not_found - the number of objects not found
            status - the HTTP return status code. '200 OK' indicates success
            errors - a list of any errors returned by the bulk delete call
        """
        if nms is None:
            nms = self.api.list_object_names(self.name, full_listing=True)
        return self.api.bulk_delete(self.name, nms, async=async)


    @_handle_object_not_found
    def download(self, obj, directory, structure=True):
        """
        Fetches the object from storage, and writes it to the specified
        directory. The directory must exist before calling this method.

        If the object name represents a nested folder structure, such as
        "foo/bar/baz.txt", that folder structure will be created in the target
        directory by default. If you do not want the nested folders to be
        created, pass `structure=False` in the parameters.
        """
        if not os.path.isdir(directory):
            raise exc.FolderNotFound("The directory '%s' does not exist." %
                    directory)
        obj_name = utils.get_name(obj)
        path, fname = os.path.split(obj_name)
        if structure:
            fullpath = os.path.join(directory, path)
            if not os.path.exists(fullpath):
                os.makedirs(fullpath)
            target = os.path.join(fullpath, fname)
        else:
            target = os.path.join(directory, fname)
        with open(target, "wb") as dl:
            content = self.fetch(obj)
            try:
                dl.write(content)
            except UnicodeEncodeError:
                encoding = pyrax.get_encoding()
                dl.write(content.encode(encoding))


    @_handle_object_not_found
    def purge(self, obj, email_addresses=None):
        """
        Removes a CDN-enabled object from public access before the TTL expires.
        Please note that there is a limit (at this time) of 25 such requests;
        if you need to purge more than that, you must contact support.

        If one or more email_addresses are included, an email confirming the
        purge is sent to each address.
        """
        cname = utils.get_name(self.container)
        oname = utils.get_name(obj)
        headers = {}
        if email_addresses:
            email_addresses = utils.coerce_to_list(email_addresses)
            headers["X-Purge-Email"] = ", ".join(email_addresses)
        uri = "/%s/%s" % (cname, oname)
        resp, resp_body = self.api.cdn_request(uri, method="DELETE",
                headers=headers)


    @_handle_object_not_found
    def get_metadata(self, obj, prefix=None):
        """
        Returns the metadata for the specified object as a dict.
        """
        uri = "/%s/%s" % (self.uri_base, utils.get_name(obj))
        resp, resp_body = self.api.method_head(uri)
        ret = {}
        # Add the metadata prefix, if needed.
        if prefix is None:
            prefix = OBJECT_META_PREFIX
        low_prefix = prefix.lower()
        for hkey, hval in list(resp.headers.items()):
            lowkey = hkey.lower()
            if lowkey.startswith(low_prefix):
                cleaned = hkey.replace(low_prefix, "").replace("-", "_")
                ret[cleaned] = hval
        return ret


    @_handle_object_not_found
    def set_metadata(self, obj, metadata, clear=False, prefix=None):
        """
        Accepts a dictionary of metadata key/value pairs and updates the
        specified object metadata with them.

        If 'clear' is True, any existing metadata is deleted and only the
        passed metadata is retained. Otherwise, the values passed here update
        the object's metadata.

        By default, the standard object metadata prefix ('X-Object-Meta-') is
        prepended to the header name if it isn't present. For non-standard
        headers, you must include a non-None prefix, such as an empty string.
        """
        # Add the metadata prefix, if needed.
        if prefix is None:
            prefix = OBJECT_META_PREFIX
        massaged = _massage_metakeys(metadata, prefix)
        cname = utils.get_name(self.container)
        oname = utils.get_name(obj)
        new_meta = {}
        # Note that the API for object POST is the opposite of that for
        # container POST: for objects, all current metadata is deleted,
        # whereas for containers you need to set the values to an empty
        # string to delete them.
        if not clear:
            obj_meta = self.get_metadata(obj, prefix=prefix)
            new_meta = _massage_metakeys(obj_meta, prefix)
        utils.case_insensitive_update(new_meta, massaged)
        # Remove any empty values, since the object metadata API will
        # store them.
        to_pop = []
        for key, val in six.iteritems(new_meta):
            if not val:
                to_pop.append(key)
        for key in to_pop:
            new_meta.pop(key)
        uri = "/%s/%s" % (cname, oname)
        resp, resp_body = self.api.method_post(uri, headers=new_meta)


    @_handle_object_not_found
    def remove_metadata_key(self, obj, key):
        """
        Removes the specified key from the object's metadata. If the key does
        not exist in the metadata, nothing is done.
        """
        meta_dict = {key: ""}
        return self.set_metadata(obj, meta_dict)



class StorageClient(BaseClient):
    """
    This is the primary class for interacting with OpenStack Object Storage.
    """
    name = "Object Storage"
    # Folder upload status dict. Each upload will generate its own UUID key.
    # The app can use that key query the status of the upload. This dict
    # will also be used to hold the flag to interrupt uploads in progress.
    folder_upload_status = {}
    # Interval in seconds between checks for completion of bulk deletes.
    bulk_delete_interval = 1

    def __init__(self, *args, **kwargs):
        # Constants used in metadata headers
        super(StorageClient, self).__init__(*args, **kwargs)
        self._sync_summary = {"total": 0,
                "uploaded": 0,
                "ignored": 0,
                "older": 0,
                "duplicate": 0,
                "failed": 0,
                "failure_reasons": [],
                "deleted": 0,
                }
        self._cached_temp_url_key = None
        self.cdn_management_url = ""
        self.method_dict = {
                "HEAD": self.method_head,
                "GET": self.method_get,
                "POST": self.method_post,
                "PUT": self.method_put,
                "DELETE": self.method_delete,
                "PATCH": self.method_patch,
                }
        # Configure CDN, if available
        self._configure_cdn()
        # Alias old method names to new versions for backwards compatibility.
        self._backwards_aliases()


    def _configure_cdn(self):
        """
        Initialize CDN-related endpoints, if available.
        """
        ident = self.identity
        cdn_svc = ident.services.get("object_cdn")
        if cdn_svc:
            ep = cdn_svc.endpoints.get(self.region_name)
            if ep:
                self.cdn_management_url = ep.public_url


    def _backwards_aliases(self):
        """
        In order to keep this backwards-compatible with previous versions,
        alias the old names to the new methods.
        """
        self.list_containers = self.list_container_names
        self.get_all_containers = self.list
        self.get_container = self.get
        self.create_container = self.create
        self.delete_container = self.delete
        self.get_container_objects = self.list_container_objects
        self.get_container_object_names = self.list_container_object_names
        self.get_info = self.get_account_info


    def get(self, item):
        """
        Returns the container whose name is provided as 'item'. If 'item' is
        not a string, the original item is returned unchanged.
        """
        if isinstance(item, six.string_types):
            item = super(StorageClient, self).get(item)
        return item


    def _configure_manager(self):
        """
        Creates a manager to handle interacting with Containers.
        """
        self._manager = ContainerManager(self, resource_class=Container,
                response_key="", uri_base="")


    def remove_container_from_cache(self, container):
        """
        Not used anymore. Included for backwards compatibility.
        """
        pass


    def get_account_details(self):
        """
        Returns a dictionary containing information about the account.
        """
        headers = self._manager.get_account_headers()
        acct_prefix = "x-account-"
        meta_prefix = ACCOUNT_META_PREFIX.lower()
        ret = {}
        for hkey, hval in list(headers.items()):
            lowkey = hkey.lower()
            if lowkey.startswith(acct_prefix):
                if not lowkey.startswith(meta_prefix):
                    cleaned = hkey.replace(acct_prefix, "").replace("-", "_")
                    try:
                        # Most values are ints
                        ret[cleaned] = int(hval)
                    except ValueError:
                        ret[cleaned] = hval
        return ret


    def get_account_info(self):
        """
        Returns a tuple for the number of containers and total bytes in the
        account.
        """
        headers = self._manager.get_account_headers()
        return (headers.get("x-account-container-count"),
                headers.get("x-account-bytes-used"))


    def get_account_metadata(self, prefix=None):
        """
        Returns a dictionary containing metadata about the account.
        """
        return self._manager.get_account_metadata(prefix=prefix)


    def set_account_metadata(self, metadata, clear=False, prefix=None,
            extra_info=None):
        """
        Accepts a dictionary of metadata key/value pairs and updates the
        account's metadata with them.

        If 'clear' is True, any existing metadata is deleted and only the
        passed metadata is retained. Otherwise, the values passed here update
        the account's metadata.

        By default, the standard account metadata prefix ('X-Account-Meta-') is
        prepended to the header name if it isn't present. For non-standard
        headers, you must include a non-None prefix, such as an empty string.

        The 'extra_info' parameter is included for backwards compatibility. It
        is no longer used at all, and will not be modified with swiftclient
        info, since swiftclient is not used any more.
        """
        return self._manager.set_account_metadata(metadata, clear=clear,
                prefix=prefix)


    def delete_account_metadata(self, prefix=None):
        """
        Removes all metadata matching the specified prefix from the account.

        By default, the standard account metadata prefix ('X-Account-Meta-') is
        prepended to the header name if it isn't present. For non-standard
        headers, you must include a non-None prefix, such as an empty string.
        """
        return self._manager.delete_account_metadata(prefix=prefix)


    def get_temp_url_key(self, cached=True):
        """
        Returns the current TempURL key, or None if it has not been set.

        By default the value returned is cached. To force an API call to get
        the current value on the server, pass `cached=False`.
        """
        meta = self._cached_temp_url_key
        if not cached or not meta:
            key = "temp_url_key"
            meta = self.get_account_metadata().get(key)
            self._cached_temp_url_key = meta
        return meta


    def set_temp_url_key(self, key=None):
        """
        Sets the key for the Temporary URL for the account. It should be a key
        that is secret to the owner.

        If no key is provided, a UUID value will be generated and used. It can
        later be obtained by calling get_temp_url_key().
        """
        if key is None:
            key = uuid.uuid4().hex
        meta = {"Temp-Url-Key": key}
        self.set_account_metadata(meta)
        self._cached_temp_url_key = key


    def get_temp_url(self, container, obj, seconds, method="GET", key=None,
            cached=True):
        """
        Given a storage object in a container, returns a URL that can be used
        to access that object. The URL will expire after `seconds` seconds.

        The only methods supported are GET and PUT. Anything else will raise
        an `InvalidTemporaryURLMethod` exception.

        If you have your Temporary URL key, you can pass it in directly and
        potentially save an API call to retrieve it. If you don't pass in the
        key, and don't wish to use any cached value, pass `cached=False`.
        """
        return self._manager.get_temp_url(container, obj, seconds,
                method=method, key=key, cached=cached)


    def list(self, limit=None, marker=None, end_marker=None, prefix=None):
        """
        List the containers in this account, using the parameters to control
        the pagination of containers, since by default only the first 10,000
        containers are returned.
        """
        return self._manager.list(limit=limit, marker=marker,
                end_marker=end_marker, prefix=prefix)


    def list_public_containers(self):
        """
        Returns a list of the names of all CDN-enabled containers.
        """
        return self._manager.list_public_containers()


    def make_container_public(self, container, ttl=None):
        """
        Enables CDN access for the specified container, and optionally sets the
        TTL for the container.
        """
        return self._manager.make_public(container, ttl=ttl)


    def make_container_private(self, container):
        """
        Disables CDN access to a container. It may still appear public until
        its TTL expires.
        """
        return self._manager.make_private(container)


    def get_cdn_log_retention(self, container):
        """
        Returns the status of the setting for CDN log retention for the
        specified container.
        """
        return self._manager.get_cdn_log_retention(container)


    def set_cdn_log_retention(self, container, enabled):
        """
        Enables or disables whether CDN access logs for the specified container
        are collected and stored on Cloud Files.
        """
        return self._manager.set_cdn_log_retention(container, enabled)


    def get_container_streaming_uri(self, container):
        """
        Returns the URI for streaming content, or None if CDN is not enabled.
        """
        return self._manager.get_container_streaming_uri(container)


    def get_container_ios_uri(self, container):
        """
        Returns the iOS URI, or None if CDN is not enabled.
        """
        return self._manager.get_container_ios_uri(container)


    def set_container_web_index_page(self, container, page):
        """
        Sets the header indicating the index page in a container
        when creating a static website.

        Note: the container must be CDN-enabled for this to have
        any effect.
        """
        return self._manager.set_web_index_page(container, page)


    def set_container_web_error_page(self, container, page):
        """
        Sets the header indicating the error page in a container
        when creating a static website.

        Note: the container must be CDN-enabled for this to have
        any effect.
        """
        return self._manager.set_web_error_page(container, page)


    def purge_cdn_object(self, container, obj, email_addresses=None):
        """
        Removes a CDN-enabled object from public access before the TTL expires.
        Please note that there is a limit (at this time) of 25 such requests;
        if you need to purge more than that, you must contact support.

        If one or more email_addresses are included, an email confirming the
        purge is sent to each address.
        """
        return self._manager.purge_cdn_object(container, obj,
                email_addresses=email_addresses)


    def list_container_names(self):
        """
        Returns a list of the names of the containers in this account.
        """
        return [cont.name for cont in self.list()]


    def list_containers_info(self, limit=None, marker=None):
        """Returns a list of info on Containers.

        For each container, a dict containing the following keys is returned:
        \code
            name - the name of the container
            count - the number of objects in the container
            bytes - the total bytes in the container
        """
        return self._manager.list_containers_info(limit=limit, marker=marker)


    def list_container_subdirs(self, container, limit=None, marker=None,
            prefix=None, delimiter=None, full_listing=False):
        """
        Although you cannot nest directories, you can simulate a hierarchical
        structure within a single container by adding forward slash characters
        (/) in the object name. This method returns a list of all of these
        pseudo-subdirectories in the specified container.
        """
        return self._manager.list_subdirs(container, limit=limit,
                marker=marker, prefix=prefix, delimiter=delimiter,
                full_listing=full_listing)


    def list_container_object_names(self, container, limit=None, marker=None,
            prefix=None, delimiter=None, full_listing=False):
        """
        Returns the names of all the objects in the specified container,
        optionally limited by the pagination parameters.
        """
        return self._manager.list_object_names(container, marker=marker,
                limit=limit, prefix=prefix, delimiter=delimiter,
                full_listing=full_listing)


    def get_container_metadata(self, container, prefix=None):
        """
        Returns a dictionary containing the metadata for the container.
        """
        return self._manager.get_metadata(container, prefix=prefix)


    def set_container_metadata(self, container, metadata, clear=False,
            prefix=None):
        """
        Accepts a dictionary of metadata key/value pairs and updates the
        specified container metadata with them.

        If 'clear' is True, any existing metadata is deleted and only the
        passed metadata is retained. Otherwise, the values passed here update
        the container's metadata.

        By default, the standard container metadata prefix
        ('X-Container-Meta-') is prepended to the header name if it isn't
        present. For non-standard headers, you must include a non-None prefix,
        such as an empty string.
        """
        return self._manager.set_metadata(container, metadata, clear=clear,
                prefix=prefix)


    def remove_container_metadata_key(self, container, key):
        """
        Removes the specified key from the container's metadata. If the key
        does not exist in the metadata, nothing is done.
        """
        return self._manager.remove_metadata_key(container, key)


    def delete_container_metadata(self, container, prefix=None):
        """
        Removes all of thethe container's metadata.

        By default, all metadata beginning with the standard container metadata
        prefix ('X-Container-Meta-') is removed. If you wish to remove all
        metadata beginning with a different prefix, you must specify that
        prefix.
        """
        return self._manager.delete_metadata(container, prefix=prefix)


    def get_container_cdn_metadata(self, container):
        """
        Returns a dictionary containing the CDN metadata for the container.
        """
        return self._manager.get_cdn_metadata(container)


    def set_container_cdn_metadata(self, container, metadata):
        """
        Accepts a dictionary of metadata key/value pairs and updates
        the specified container metadata with them.

        NOTE: arbitrary metadata headers are not allowed. The only metadata
        you can update are: X-Log-Retention, X-CDN-enabled, and X-TTL.
        """
        return self._manager.set_cdn_metadata(container, metadata)


    def get_object_metadata(self, container, obj, prefix=None):
        """
        Returns the metadata for the specified object as a dict.
        """
        return self._manager.get_object_metadata(container, obj, prefix=prefix)


    def set_object_metadata(self, container, obj, metadata, clear=False,
            extra_info=None, prefix=None):
        """
        Accepts a dictionary of metadata key/value pairs and updates the
        specified object metadata with them.

        If 'clear' is True, any existing metadata is deleted and only the
        passed metadata is retained. Otherwise, the values passed here update
        the object's metadata.

        'extra_info; is an optional dictionary which will be populated with
        'status', 'reason', and 'headers' keys from the underlying swiftclient
        call.

        By default, the standard object metadata prefix ('X-Object-Meta-') is
        prepended to the header name if it isn't present. For non-standard
        headers, you must include a non-None prefix, such as an empty string.
        """
        return self._manager.set_object_metadata(container, obj, metadata,
                clear=clear, prefix=prefix)


    def remove_object_metadata_key(self, container, obj, key, prefix=None):
        """
        Removes the specified key from the storage object's metadata. If the key
        does not exist in the metadata, nothing is done.
        """
        self.set_object_metadata(container, obj, {key: ""}, prefix=prefix)


    def list_container_objects(self, container, limit=None, marker=None,
            prefix=None, delimiter=None, end_marker=None, full_listing=False):
        """
        Return a list of StorageObjects representing the objects in the
        container. You can use the marker, end_marker, and limit params to
        handle pagination, and the prefix and delimiter params to filter the
        objects returned.  Also, by default only the first 10,000 objects are
        returned; if you set full_listing to True, an iterator to return all
        the objects in the container is returned. In this case, only the
        'prefix' parameter is used; if you specify any others, they are
        ignored.
        """
        if full_listing:
            return self._manager.object_listing_iterator(container,
                    prefix=prefix)
        return self._manager.list_objects(container, limit=limit,
                marker=marker, prefix=prefix, delimiter=delimiter,
                end_marker=end_marker)


    def object_listing_iterator(self, container, prefix=None):
        return self._manager.object_listing_iterator(container, prefix=prefix)


    def delete_object_in_seconds(self, cont, obj, seconds, extra_info=None):
        """
        Sets the object in the specified container to be deleted after the
        specified number of seconds.

        The 'extra_info' parameter is included for backwards compatibility. It
        is no longer used at all, and will not be modified with swiftclient
        info, since swiftclient is not used any more.
        """
        return self._manager.delete_object_in_seconds(cont, obj, seconds)


    def get_object(self, container, obj):
        """
        Returns a StorageObject representing the requested object.
        """
        return self._manager.get_object(container, obj)


    def store_object(self, container, obj_name, data, content_type=None,
            etag=None, content_encoding=None, ttl=None, return_none=False,
            chunk_size=None, headers=None, metadata=None, extra_info=None):
        """
        Creates a new object in the specified container, and populates it with
        the given data. A StorageObject reference to the uploaded file
        will be returned, unless 'return_none' is set to True.

        The 'extra_info' parameter is included for backwards compatibility. It
        is no longer used at all, and will not be modified with swiftclient
        info, since swiftclient is not used any more.
        """
        return self.create_object(container, obj_name=obj_name, data=data,
                content_type=content_type, etag=etag,
                content_encoding=content_encoding, ttl=ttl,
                return_none=return_none, chunk_size=chunk_size,
                headers=headers, metadata=metadata)


    def upload_file(self, container, file_or_path, obj_name=None,
            content_type=None, etag=None, content_encoding=None, ttl=None,
            content_length=None, return_none=False, headers=None,
            metadata=None, extra_info=None):
        """
        Uploads the specified file to the container. If no name is supplied,
        the file's name will be used. Either a file path or an open file-like
        object may be supplied. A StorageObject reference to the uploaded file
        will be returned, unless 'return_none' is set to True.

        You may optionally set the `content_type` and `content_encoding`
        parameters; pyrax will create the appropriate headers when the object
        is stored.

        If the size of the file is known, it can be passed as `content_length`.

        If you wish for the object to be temporary, specify the time it should
        be stored in seconds in the `ttl` parameter. If this is specified, the
        object will be deleted after that number of seconds.

        The 'extra_info' parameter is included for backwards compatibility. It
        is no longer used at all, and will not be modified with swiftclient
        info, since swiftclient is not used any more.
        """
        return self.create_object(container, file_or_path=file_or_path,
                obj_name=obj_name, content_type=content_type, etag=etag,
                content_encoding=content_encoding, ttl=ttl, headers=headers,
                metadata=metadata, return_none=return_none)


    def create_object(self, container, file_or_path=None, data=None,
            obj_name=None, content_type=None, etag=None, content_encoding=None,
            content_length=None, ttl=None, chunk_size=None, metadata=None,
            headers=None, return_none=False):
        """
        Creates or replaces a storage object in the specified container.

        The content of the object can either be a stream of bytes (`data`), or
        a file on disk (`file_or_path`). The disk file can be either an open
        file-like object, or an absolute path to the file on disk.

        When creating object from a data stream, you must specify the name of
        the object to be created in the container via the `obj_name` parameter.
        When working with a file, though, if no `obj_name` value is specified,
        the file`s name will be used.

        You may optionally set the `content_type` and `content_encoding`
        parameters; pyrax will create the appropriate headers when the object
        is stored. If no `content_type` is specified, the object storage system
        will make an intelligent guess based on the content of the object.

        If the size of the file is known, it can be passed as `content_length`.

        If you wish for the object to be temporary, specify the time it should
        be stored in seconds in the `ttl` parameter. If this is specified, the
        object will be deleted after that number of seconds.

        If you wish to store a stream of data (i.e., where you don't know the
        total size in advance), set the `chunk_size` parameter to a non-zero
        value, and omit the `content_length` and `etag` parameters. This allows
        the data to be streamed to the object in the container without having
        to be written to disk first.
        """
        return self._manager.create_object(container, file_or_path=file_or_path,
                data=data, obj_name=obj_name, content_type=content_type,
                etag=etag, content_encoding=content_encoding,
                content_length=content_length, ttl=ttl, chunk_size=chunk_size,
                metadata=metadata, headers=headers, return_none=return_none)


    def fetch_object(self, container, obj, include_meta=False,
            chunk_size=None, size=None, extra_info=None):
        """
        Fetches the object from storage.

        If 'include_meta' is False, only the bytes representing the
        stored object are returned.

        Note: if 'chunk_size' is defined, you must fully read the object's
        contents before making another request.

        If 'size' is specified, only the first 'size' bytes of the object will
        be returned. If the object if smaller than 'size', the entire object is
        returned.

        When 'include_meta' is True, what is returned from this method is a
        2-tuple:
            Element 0: a dictionary containing metadata about the file.
            Element 1: a stream of bytes representing the object's contents.

        The 'extra_info' parameter is included for backwards compatibility. It
        is no longer used at all, and will not be modified with swiftclient
        info, since swiftclient is not used any more.
        """
        return self._manager.fetch_object(container, obj,
                include_meta=include_meta, chunk_size=chunk_size, size=size)


    def fetch_partial(self, container, obj, size):
        """
        Returns the first 'size' bytes of an object. If the object is smaller
        than the specified 'size' value, the entire object is returned.
        """
        return self._manager.fetch_partial(container, obj, size)


    def fetch_dlo(self, container, name, chunk_size=None, verbose=False):
        """
        Returns a list of 2-tuples in the form of (object_name,
        fetch_generator) representing the components of a multi-part DLO
        (Dynamic Large Object).  Each fetch_generator object can be interated
        to retrieve its contents.

        This is useful when transferring a DLO from one object storage system
        to another. Examples would be copying DLOs from one region of a
        provider to another, or copying a DLO from one provider to another.
        """
        if chunk_size is None:
            chunk_size = DEFAULT_CHUNKSIZE

        class FetchChunker(object):
            """
            Class that takes the generator objects returned by a chunked
            fetch_object() call and wraps them to behave as file-like objects
            for uploading.
            """
            def __init__(self, gen, verbose=False):
                self.gen = gen
                self.verbose = verbose
                self.processed = 0
                self.count = 0
                self.interval = 100

            def read(self, size=None):
                self.count += 1
                if self.verbose:
                    if self.count > self.interval:
                        self.count = 0
                        print(".")
                ret = self.gen.next()
                self.processed += len(ret)
                return ret

        parts = self.get_container_objects(container, prefix=name)
        fetches = [(part.name, self.fetch_object(container, part.name,
                    chunk_size=chunk_size))
                for part in parts
                if part.name != name]
        job = [(fetch[0], FetchChunker(fetch[1], verbose=verbose))
                for fetch in fetches]
        return job


    def download_object(self, container, obj, directory, structure=True):
        """
        Fetches the object from storage, and writes it to the specified
        directory. The directory must exist before calling this method.

        If the object name represents a nested folder structure, such as
        "foo/bar/baz.txt", that folder structure will be created in the target
        directory by default. If you do not want the nested folders to be
        created, pass `structure=False` in the parameters.
        """
        return self._manager.download_object(container, obj, directory,
                structure=structure)


    def delete(self, container, del_objects=False):
        """
        Deletes the specified container. If the container contains objects, the
        command will fail unless 'del_objects' is passed as True. In that case,
        each object will be deleted first, and then the container.
        """
        return self._manager.delete(container, del_objects=del_objects)


    def delete_object(self, container, obj):
        """
        Deletes the object from the specified container.

        The 'obj' parameter can either be the name of the object, or a
        StorageObject representing the object to be deleted.
        """
        return self._manager.delete_object(container, obj)


    def copy_object(self, container, obj, new_container, new_obj_name=None,
            content_type=None, extra_info=None):
        """
        Copies the object to the new container, optionally giving it a new name.
        If you copy to the same container, you must supply a different name.

        You can optionally change the content_type of the object by supplying
        that in the 'content_type' parameter.

        The 'extra_info' parameter is included for backwards compatibility. It
        is no longer used at all, and will not be modified with swiftclient
        info, since swiftclient is not used any more.
        """
        return self._manager.copy_object(container, obj, new_container,
                new_obj_name=new_obj_name, content_type=content_type)


    def move_object(self, container, obj, new_container, new_obj_name=None,
            new_reference=False, content_type=None, extra_info=None):
        """
        Works just like copy_object, except that the source object is deleted
        after a successful copy.

        You can optionally change the content_type of the object by supplying
        that in the 'content_type' parameter.

        NOTE: any references to the original object will no longer be valid;
        you will have to get a reference to the new object by passing True for
        the 'new_reference' parameter. When this is True, a reference to the
        newly moved object is returned. Otherwise, the etag for the moved
        object is returned.

        The 'extra_info' parameter is included for backwards compatibility. It
        is no longer used at all, and will not be modified with swiftclient
        info, since swiftclient is not used any more.
        """
        return self._manager.move_object(container, obj, new_container,
                new_obj_name=new_obj_name, new_reference=new_reference,
                content_type=content_type)


    def change_object_content_type(self, container, obj, new_ctype,
            guess=False, extra_info=None):
        """
        Copies object to itself, but applies a new content-type. The guess
        feature requires the container to be CDN-enabled. If not then the
        content-type must be supplied. If using guess with a CDN-enabled
        container, new_ctype can be set to None. Failure during the put will
        result in a swift exception.

        The 'extra_info' parameter is included for backwards compatibility. It
        is no longer used at all, and will not be modified with swiftclient
        info, since swiftclient is not used any more.
        """
        return self._manager.change_object_content_type(container, obj,
                new_ctype, guess=guess)


    def upload_folder(self, folder_path, container=None, ignore=None, ttl=None):
        """
        Convenience method for uploading an entire folder, including any
        sub-folders, to Cloud Files.

        All files will be uploaded to objects with the same name as the file.
        In the case of nested folders, files will be named with the full path
        relative to the base folder. E.g., if the folder you specify contains a
        folder named 'docs', and 'docs' contains a file named 'install.html',
        that file will be uploaded to an object named 'docs/install.html'.

        If 'container' is specified, the folder's contents will be uploaded to
        that container. If it is not specified, a new container with the same
        name as the specified folder will be created, and the files uploaded to
        this new container.

        You can selectively ignore files by passing either a single pattern or
        a list of patterns; these will be applied to the individual folder and
        file names, and any names that match any of the 'ignore' patterns will
        not be uploaded. The patterns should be standard *nix-style shell
        patterns; e.g., '*pyc' will ignore all files ending in 'pyc', such as
        'program.pyc' and 'abcpyc'.

        The upload will happen asynchronously; in other words, the call to
        upload_folder() will generate a UUID and return a 2-tuple of (UUID,
        total_bytes) immediately. Uploading will happen in the background; your
        app can call get_uploaded(uuid) to get the current status of the
        upload. When the upload is complete, the value returned by
        get_uploaded(uuid) will match the total_bytes for the upload.

        If you start an upload and need to cancel it, call
        cancel_folder_upload(uuid), passing the uuid returned by the initial
        call.  It will then be up to you to either keep or delete the
        partially-uploaded content.

        If you specify a `ttl` parameter, the uploaded files will be deleted
        after that number of seconds.
        """
        if not os.path.isdir(folder_path):
            raise exc.FolderNotFound("No such folder: '%s'" % folder_path)

        ignore = utils.coerce_to_list(ignore)
        total_bytes = utils.folder_size(folder_path, ignore)
        upload_key = str(uuid.uuid4())
        self.folder_upload_status[upload_key] = {"continue": True,
                "total_bytes": total_bytes,
                "uploaded": 0,
                }
        self._upload_folder_in_background(folder_path, container, ignore,
                upload_key, ttl)
        return (upload_key, total_bytes)


    def _upload_folder_in_background(self, folder_path, container, ignore,
            upload_key, ttl=None):
        """Runs the folder upload in the background."""
        uploader = FolderUploader(folder_path, container, ignore, upload_key,
                self, ttl=ttl)
        uploader.start()


    def sync_folder_to_container(self, folder_path, container, delete=False,
            include_hidden=False, ignore=None, ignore_timestamps=False,
            object_prefix="", verbose=False):
        """
        Compares the contents of the specified folder, and checks to make sure
        that the corresponding object is present in the specified container. If
        there is no remote object matching the local file, it is created. If a
        matching object exists, the etag is examined to determine if the object
        in the container matches the local file; if they differ, the container
        is updated with the local file if the local file is newer when
        `ignore_timestamps' is False (default). If `ignore_timestamps` is True,
        the object is overwritten with the local file contents whenever the
        etags differ. NOTE: the timestamp of a remote object is the time it was
        uploaded, not the original modification time of the file stored in that
        object.  Unless 'include_hidden' is True, files beginning with an
        initial period are ignored.

        If the 'delete' option is True, any objects in the container that do
        not have corresponding files in the local folder are deleted.

        You can selectively ignore files by passing either a single pattern or
        a list of patterns; these will be applied to the individual folder and
        file names, and any names that match any of the 'ignore' patterns will
        not be uploaded. The patterns should be standard *nix-style shell
        patterns; e.g., '*pyc' will ignore all files ending in 'pyc', such as
        'program.pyc' and 'abcpyc'.

        If `object_prefix` is set it will be appended to the object name when
        it is checked and uploaded to the container. For example, if you use
        sync_folder_to_container("folderToSync/", myContainer,
            object_prefix="imgFolder") it will upload the files to the
        container/imgFolder/... instead of just container/...

        Set `verbose` to True to make it print what is going on. It will
        show which files are being uploaded and which ones are not and why.
        """
        cont = self.get_container(container)
        self._local_files = []
        # Load a list of all the remote objects so we don't have to keep
        # hitting the service
        if verbose:
            log = logging.getLogger("pyrax")
            log.info("Loading remote object list (prefix=%s)", object_prefix)
        data = cont.get_objects(prefix=object_prefix, full_listing=True)
        self._remote_files = dict((d.name, d) for d in data)
        self._sync_summary = {"total": 0,
                "uploaded": 0,
                "ignored": 0,
                "older": 0,
                "duplicate": 0,
                "failed": 0,
                "failure_reasons": [],
                "deleted": 0,
                }
        self._sync_folder_to_container(folder_path, cont, prefix="",
                delete=delete, include_hidden=include_hidden, ignore=ignore,
                ignore_timestamps=ignore_timestamps,
                object_prefix=object_prefix, verbose=verbose)
        # Unset the _remote_files
        self._remote_files = None
        if verbose:
            # Log the summary
            summary = self._sync_summary
            log.info("Folder sync completed at %s" % time.ctime())
            log.info("  Total files processed: %s" % summary["total"])
            log.info("  Number Uploaded: %s" % summary["uploaded"])
            log.info("  Number Ignored: %s" % summary["ignored"])
            log.info("  Number Skipped (older): %s" % summary["older"])
            log.info("  Number Skipped (dupe): %s" % summary["duplicate"])
            log.info("  Number Deleted: %s" % summary["deleted"])
            log.info("  Number Failed: %s" % summary["failed"])
            if summary["failed"]:
                for reason in summary["failure_reasons"]:
                    log.info("  Reason: %s" % reason)


    def _sync_folder_to_container(self, folder_path, container, prefix, delete,
            include_hidden, ignore, ignore_timestamps, object_prefix, verbose):
        """
        This is the internal method that is called recursively to handle
        nested folder structures.
        """
        fnames = os.listdir(folder_path)
        ignore = utils.coerce_to_list(ignore)
        log = logging.getLogger("pyrax")
        if not include_hidden:
            ignore.append(".*")
        for fname in fnames:
            if utils.match_pattern(fname, ignore):
                self._sync_summary["ignored"] += 1
                continue
            pth = os.path.join(folder_path, fname)
            if os.path.isdir(pth):
                subprefix = fname
                if prefix:
                    subprefix = os.path.join(prefix, subprefix)
                self._sync_folder_to_container(pth, container, prefix=subprefix,
                        delete=delete, include_hidden=include_hidden,
                        ignore=ignore, ignore_timestamps=ignore_timestamps,
                        object_prefix=object_prefix, verbose=verbose)
                continue
            self._local_files.append(os.path.join(object_prefix, prefix,
                    fname))
            local_etag = utils.get_checksum(pth)
            if object_prefix:
                prefix = os.path.join(object_prefix, prefix)
                object_prefix = ""
            fullname_with_prefix = os.path.join(prefix, fname)
            try:
                obj = self._remote_files[fullname_with_prefix]
                obj_etag = obj.etag
            except KeyError:
                obj = None
                obj_etag = None
            if local_etag != obj_etag:
                if not ignore_timestamps:
                    if obj:
                        obj_time_str = obj.last_modified[:19]
                    else:
                        obj_time_str = EARLY_DATE_STR
                    local_mod = datetime.datetime.utcfromtimestamp(
                            os.stat(pth).st_mtime)
                    local_mod_str = local_mod.isoformat()
                    if obj_time_str >= local_mod_str:
                        # Remote object is newer
                        self._sync_summary["older"] += 1
                        if verbose:
                            log.info("%s NOT UPLOADED because remote object is "
                                    "newer", fullname_with_prefix)
                            log.info("  Local: %s   Remote: %s" % (
                                    local_mod_str, obj_time_str))
                        continue
                try:
                    container.upload_file(pth, obj_name=fullname_with_prefix,
                        etag=local_etag, return_none=True)
                    self._sync_summary["uploaded"] += 1
                    if verbose:
                        log.info("%s UPLOADED", fullname_with_prefix)
                except Exception as e:
                    # Record the failure, and move on
                    self._sync_summary["failed"] += 1
                    self._sync_summary["failure_reasons"].append("%s" % e)
                    if verbose:
                        log.error("%s UPLOAD FAILED. Exception: %s" %
                                (fullname_with_prefix, e))
            else:
                self._sync_summary["duplicate"] += 1
                if verbose:
                    log.info("%s NOT UPLOADED because it already exists",
                            fullname_with_prefix)
        if delete and not prefix:
            self._delete_objects_not_in_list(container, object_prefix)


    def _delete_objects_not_in_list(self, cont, object_prefix=""):
        """
        Finds all the objects in the specified container that are not present
        in the self._local_files list, and deletes them.
        """
        objnames = set(cont.get_object_names(prefix=object_prefix,
                full_listing=True))
        localnames = set(self._local_files)
        to_delete = list(objnames.difference(localnames))
        self._sync_summary["deleted"] += len(to_delete)
        # We don't need to wait around for this to complete. Store the thread
        # reference in case it is needed at some point.
        self._thread = self.bulk_delete(cont, to_delete, async=True)


    def bulk_delete(self, container, object_names, async=False):
        """
        Deletes multiple objects from a container in a single call.

        The bulk deletion call does not return until all of the specified
        objects have been processed. For large numbers of objects, this can
        take quite a while, so there is an 'async' parameter to give you the
        option to have this call return immediately. If 'async' is True, an
        object is returned with a 'completed' attribute that will be set to
        True as soon as the bulk deletion is complete, and a 'results'
        attribute that will contain a dictionary (described below) with the
        results of the bulk deletion.

        When deletion is complete the bulk deletion object's 'results'
        attribute will be populated with the information returned from the API
        call. In synchronous mode this is the value that is returned when the
        call completes. It is a dictionary with the following keys:

            deleted - the number of objects deleted
            not_found - the number of objects not found
            status - the HTTP return status code. '200 OK' indicates success
            errors - a list of any errors returned by the bulk delete call

        This isn't available in swiftclient yet, so it's using code patterned
        after the client code in that library.
        """
        deleter = BulkDeleter(self, container, object_names)
        deleter.start()
        if async:
            return deleter
        while not deleter.completed:
            time.sleep(self.bulk_delete_interval)
        return deleter.results


    def cdn_request(self, uri, method, *args, **kwargs):
        """
        If the service supports CDN, use this method to access CDN-specific
        URIs.
        """
        if not self.cdn_management_url:
            raise exc.NotCDNEnabled("CDN is not enabled for this service.")
        cdn_uri = "%s%s" % (self.cdn_management_url, uri)
        mthd = self.method_dict.get(method.upper())
        try:
            resp, resp_body = mthd(cdn_uri, *args, **kwargs)
        except exc.NotFound as e:
            # This could be due to either the container does not exist, or that
            # the container exists but is not CDN-enabled.
            try:
                mgt_uri = "%s%s" % (self.management_url, uri)
                resp, resp_body = self.method_head(mgt_uri)
            except exc.NotFound:
                raise
            raise exc.NotCDNEnabled("This container is not CDN-enabled.")
        return resp, resp_body


    @_valid_upload_key
    def _update_progress(self, upload_key, size):
        self.folder_upload_status[upload_key]["uploaded"] += size


    @_valid_upload_key
    def get_uploaded(self, upload_key):
        """Returns the number of bytes uploaded for the specified process."""
        return self.folder_upload_status[upload_key]["uploaded"]


    @_valid_upload_key
    def cancel_folder_upload(self, upload_key):
        """
        Cancels any folder upload happening in the background. If there is no
        such upload in progress, calling this method has no effect.
        """
        self.folder_upload_status[upload_key]["continue"] = False


    @_valid_upload_key
    def _should_abort_folder_upload(self, upload_key):
        """
        Returns True if the user has canceled upload; returns False otherwise.
        """
        return not self.folder_upload_status[upload_key]["continue"]



class FolderUploader(threading.Thread):
    """
    Threading class to allow for uploading multiple files in the background.
    """
    def __init__(self, root_folder, container, ignore, upload_key, client,
            ttl=None):
        self.root_folder = root_folder.rstrip("/")
        self.ignore = utils.coerce_to_list(ignore)
        self.upload_key = upload_key
        self.ttl = ttl
        self.client = client
        if container:
            if isinstance(container, six.string_types):
                self.container = self.client.create(container)
            else:
                self.container = container
        else:
            self.container = self.client.create(
                    self.folder_name_from_path(root_folder))
        threading.Thread.__init__(self)


    @staticmethod
    def folder_name_from_path(pth):
        """Convenience method that first strips trailing path separators."""
        return os.path.basename(pth.rstrip(os.sep))


    def upload_files_in_folder(self, arg, dirname, fnames):
        """Handles the iteration across files within a folder."""
        if utils.match_pattern(dirname, self.ignore):
            return False
        good_names = (nm for nm in fnames
                if not utils.match_pattern(nm, self.ignore))
        for fname in good_names:
            if self.client._should_abort_folder_upload(self.upload_key):
                return
            full_path = os.path.join(dirname, fname)
            if os.path.isdir(full_path):
                # Skip folders; os.walk will include them in the next pass.
                continue
            obj_name = os.path.relpath(full_path, self.root_folder)
            obj_size = os.stat(full_path).st_size
            self.client.upload_file(self.container, full_path,
                    obj_name=obj_name, return_none=True, ttl=self.ttl)
            self.client._update_progress(self.upload_key, obj_size)


    def run(self):
        """Starts the uploading thread."""
        root_path, folder_name = os.path.split(self.root_folder)
        self.root_folder = os.path.join(root_path, folder_name)
        os.path.walk(self.root_folder, self.upload_files_in_folder, None)



class BulkDeleter(threading.Thread):
    """
    Threading class to allow for bulk deletion of objects from a container.
    """
    def __init__(self, client, container, object_names):
        self.client = client
        self.container = container
        self.object_names = object_names
        self.completed = False
        self.results = {
            "deleted": 0,
            "not_found": 0,
            "status": "",
            "errors": []
        }
        threading.Thread.__init__(self)


    def run(self):
        client = self.client
        container = self.container
        object_names = self.object_names
        cname = utils.get_name(container)
        ident = self.client.identity
        headers = {
            "X-Auth-Token": ident.token,
            "Content-Type": "text/plain",
        }
        uri = "/?bulk-delete=1"
        key_map = {
            "Number Not Found": "not_found",
            "Response Status": "status",
            "Errors": "errors",
            "Number Deleted": "deleted",
            "Response Body": None,
        }
        batch = []
        while object_names:
            batch[:] = object_names[:MAX_BULK_DELETE]
            del object_names[:MAX_BULK_DELETE]

            obj_paths = ("%s/%s" % (cname, nm) for nm in batch)
            body = "\n".join(obj_paths)
            resp, resp_body = self.client.method_delete(uri, data=body,
                    headers=headers)
            for k, v in six.iteritems(resp_body):
                if key_map[k] == "errors":
                    status_code = int(resp_body.get("Response Status", "200")[:3])
                    if status_code != 200 and not v:
                        self.results["errors"].extend([[
                            resp_body.get("Response Body"),
                            resp_body.get("Response Status")
                        ]])
                    else:
                        self.results["errors"].extend(v)
                elif key_map[k] in ("deleted", "not_found"):
                    self.results[key_map[k]] += int(v)
                elif key_map[k]:
                    self.results[key_map[k]] = v

        self.completed = True
