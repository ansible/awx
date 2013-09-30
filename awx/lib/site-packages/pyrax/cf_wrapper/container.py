#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2012 Rackspace

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


import pyrax
from pyrax import exceptions as exc

# Used to indicate values that are lazy-loaded
class Fault(object):
    def __nonzero__(self):
        return False

FAULT = Fault()


class Container(object):
    """Represents a CloudFiles container."""
    def __init__(self, client, name, object_count=None, total_bytes=None):
        self.client = client
        self.name = name
        self.object_count = int(object_count)
        self.total_bytes = int(total_bytes)
        self._cdn_uri = FAULT
        self._cdn_ttl = FAULT
        self._cdn_ssl_uri = FAULT
        self._cdn_streaming_uri = FAULT
        self._cdn_ios_uri = FAULT
        self._cdn_log_retention = FAULT
        self._object_cache = {}


    def _set_cdn_defaults(self):
        """Sets all the CDN-related attributes to default values."""
        self._cdn_uri = None
        self._cdn_ttl = self.client.default_cdn_ttl
        self._cdn_ssl_uri = None
        self._cdn_streaming_uri = None
        self._cdn_ios_uri = None
        self._cdn_log_retention = False


    def _fetch_cdn_data(self):
        """Fetches the object's CDN data from the CDN service"""
        response = self.client.connection.cdn_request("HEAD", [self.name])
        if 200 <= response.status < 300:
            # Set defaults in case not all headers are present.
            self._set_cdn_defaults()
            for hdr in response.getheaders():
                low_hdr = hdr[0].lower()
                if low_hdr == "x-cdn-uri":
                    self._cdn_uri = hdr[1]
                elif low_hdr == "x-ttl":
                    self._cdn_ttl = int(hdr[1])
                elif low_hdr == "x-cdn-ssl-uri":
                    self._cdn_ssl_uri = hdr[1]
                elif low_hdr == "x-cdn-streaming-uri":
                    self._cdn_streaming_uri = hdr[1]
                elif low_hdr == "x-cdn-ios-uri":
                    self._cdn_ios_uri = hdr[1]
                elif low_hdr == "x-log-retention":
                    self._cdn_log_retention = (hdr[1] == "True")
        elif response.status == 404:
            # Not CDN enabled; set the defaults.
            self._set_cdn_defaults()
        # We need to read the response in order to clear it for
        # the next call
        response.read()


    def get_objects(self, marker=None, limit=None, prefix=None, delimiter=None,
            full_listing=False):
        """
        Returns a list of StorageObjects representing the objects in the
        container. You can use the marker and limit params to handle pagination,
        and the prefix and delimiter params to filter the objects returned.
        Also, by default only the first 10,000 objects are returned; if you set
        full_listing to True, all objects in the container are returned.
        """
        objs = self.client.get_container_objects(self.name, marker=marker,
                limit=limit, prefix=prefix, delimiter=delimiter,
                full_listing=full_listing)
        return objs


    def get_object(self, name):
        """
        Return the StorageObject in this container with the
        specified name.
        """
        if isinstance(name, str):
            name = name.decode(pyrax.get_encoding())
        ret = self._object_cache.get(name)
        if not ret:
            ret = self.client.get_object(self, name)
            self._object_cache[name] = ret
        return ret


    def get_object_names(self, marker=None, limit=None, prefix=None,
            delimiter=None, full_listing=False):
        """
        Returns a list of the names of all the objects in this container. The
        same pagination parameters apply as in self.get_objects().
        """
        objs = self.get_objects(marker=marker, limit=limit, prefix=prefix,
                delimiter=delimiter, full_listing=full_listing)
        return [obj.name for obj in objs]


    def store_object(self, obj_name, data, content_type=None, etag=None,
            content_encoding=None, ttl=None):
        """
        Creates a new object in this container, and populates it with
        the given data.
        """
        return self.client.store_object(self, obj_name, data,
                content_type=content_type, etag=etag,
                content_encoding=content_encoding, ttl=ttl)


    def upload_file(self, file_or_path, obj_name=None, content_type=None,
            etag=None, return_none=False, content_encoding=None, ttl=None,
            content_length=None):
        """
        Uploads the specified file to this container. If no name is supplied,
        the file's name will be used. Either a file path or an open file-like
        object may be supplied. A StorageObject reference to the uploaded file
        will be returned, unless 'return_none' is set to True.
        """
        return self.client.upload_file(self, file_or_path, obj_name=obj_name,
                content_type=content_type, etag=etag, return_none=return_none,
                content_encoding=content_encoding, ttl=None,
                content_length=content_length)


    def delete_object(self, obj):
        """Deletes the specified object from this container."""
        self.remove_from_cache(obj)
        return self.client.delete_object(self, obj)


    def delete_all_objects(self):
        """Deletes all objects from this container."""
        for obj_name in self.client.get_container_object_names(self):
            self.client.delete_object(self, obj_name)


    def remove_from_cache(self, obj):
        """Removes the object from the cache."""
        nm = self.client._resolve_name(obj)
        self._object_cache.pop(nm, None)


    def delete(self, del_objects=False):
        """
        Deletes this Container. If the container contains objects, the
        command will fail unless 'del_objects' is passed as True. In that
        case, each object will be deleted first, and then the container.
        """
        return self.client.delete_container(self.name, del_objects=del_objects)


    def fetch_object(self, obj_name, include_meta=False, chunk_size=None):
        """
        Fetches the object from storage.

        If 'include_meta' is False, only the bytes representing the
        file is returned.

        Note: if 'chunk_size' is defined, you must fully read the object's
        contents before making another request.

        When 'include_meta' is True, what is returned from this method is
        a 2-tuple:
            Element 0: a dictionary containing metadata about the file.
            Element 1: a stream of bytes representing the object's contents.
        """
        return self.client.fetch_object(self, obj_name,
                include_meta=include_meta, chunk_size=chunk_size)


    def download_object(self, obj_name, directory, structure=True):
        """
        Fetches the object from storage, and writes it to the specified
        directory. The directory must exist before calling this method.

        If the object name represents a nested folder structure, such as
        "foo/bar/baz.txt", that folder structure will be created in the target
        directory by default. If you do not want the nested folders to be
        created, pass `structure=False` in the parameters.
        """
        return self.client.download_object(self, obj_name, directory,
                structure=structure)


    def get_metadata(self):
        return self.client.get_container_metadata(self)


    def set_metadata(self, metadata, clear=False):
        return self.client.set_container_metadata(self, metadata, clear=clear)


    def remove_metadata_key(self, key):
        """
        Removes the specified key from the container's metadata. If the key
        does not exist in the metadata, nothing is done.
        """
        return self.client.remove_container_metadata_key(self, key)


    def set_web_index_page(self, page):
        """
        Sets the header indicating the index page for this container
        when creating a static website.

        Note: the container must be CDN-enabled for this to have
        any effect.
        """
        return self.client.set_container_web_index_page(self, page)


    def set_web_error_page(self, page):
        """
        Sets the header indicating the error page for this container
        when creating a static website.

        Note: the container must be CDN-enabled for this to have
        any effect.
        """
        return self.client.set_container_web_error_page(self, page)


    def make_public(self, ttl=None):
        """Enables CDN access for the specified container."""
        return self.client.make_container_public(self, ttl)


    def make_private(self):
        """
        Disables CDN access to this container. It may still appear public until
        its TTL expires.
        """
        return self.client.make_container_private(self)


    def change_object_content_type(self, obj, new_ctype, guess=False):
        """
        Copies object to itself, but applies a new content-type. The guess
        feature requires the container to be CDN-enabled. If not then the
        content-type must be supplied. If using guess with a CDN-enabled
        container, new_ctype can be set to None.
        Failure during the put will result in a swift exception.
        """
        self.client.change_object_content_type(self, obj, new_ctype=new_ctype,
                guess=guess)


    def get_temp_url(self, obj, seconds, method="GET"):
        """
        Returns a URL that can be used to access the specified object in this
        container. The URL will expire after `seconds` seconds.

        The only methods supported are GET and PUT. Anything else will raise
        an InvalidTemporaryURLMethod exception.
        """
        return self.client.get_temp_url(self, obj, seconds=seconds,
                method=method)


    def delete_object_in_seconds(self, obj, seconds):
        """
        Sets the object to be deleted after the specified number of seconds.
        """
        self.client.delete_object_in_seconds(self, obj, seconds)


    def __repr__(self):
        return "<Container '%s'>" % self.name


    ## BEGIN - CDN property definitions ##
    @property
    def cdn_enabled(self):
        return bool(self.cdn_uri)

    def _get_cdn_log_retention(self):
        if self._cdn_log_retention is FAULT:
            self._fetch_cdn_data()
        return self._cdn_log_retention

    def _set_cdn_log_retention(self, val):
        self.client._set_cdn_log_retention(self, val)
        self._cdn_log_retention = val


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


    cdn_log_retention = property(_get_cdn_log_retention, _set_cdn_log_retention)
    cdn_uri = property(_get_cdn_uri, _set_cdn_uri)
    cdn_ttl = property(_get_cdn_ttl, _set_cdn_ttl)
    cdn_ssl_uri = property(_get_cdn_ssl_uri, _set_cdn_ssl_uri)
    cdn_streaming_uri = property(_get_cdn_streaming_uri, _set_cdn_streaming_uri)
    cdn_ios_uri = property(_get_cdn_ios_uri, _set_cdn_ios_uri)
    ## END - CDN property definitions ##
