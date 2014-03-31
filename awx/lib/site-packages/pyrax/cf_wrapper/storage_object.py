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

import six

class StorageObject(object):
    """Represents a CloudFiles storage object."""
    def __init__(self, client, container, name=None, total_bytes=None,
            content_type=None, last_modified=None, etag=None, attdict=None):
        """
        The object can either be initialized with individual params, or by
        passing the dict that is returned by swiftclient.
        """
        self.client = client
        if isinstance(container, six.string_types):
            self.container = self.client.get_container(container)
        else:
            self.container = container
        self.name = name
        self.total_bytes = total_bytes
        self.content_type = content_type
        self.last_modified = last_modified
        self.etag = etag
        if attdict:
            self._read_attdict(attdict)


    def _read_attdict(self, dct):
        """
        Populates the object attributes using the dict returned by swiftclient.
        """
        self.name = dct.get("name")
        if not self.name:
            # Could be a pseudo-subdirectory
            self.name = dct.get("subdir").rstrip("/")
            self.content_type = "pseudo/subdir"
        else:
            self.content_type = dct.get("content_type")
        self.total_bytes = dct.get("bytes")
        self.last_modified = dct.get("last_modified")
        self.etag = dct.get("hash")


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
        return self.client.fetch_object(container=self.container.name,
                obj=self, include_meta=include_meta, chunk_size=chunk_size)
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
        return self.client.download_object(self.container, self, directory,
                structure=structure)


    def delete(self):
        """Deletes the object from storage."""
        self.client.delete_object(container=self.container.name, name=self.name)


    def purge(self, email_addresses=[]):
        """
        Purges the object from the CDN network, sending an optional
        email confirmation.
        """
        self.client.purge_cdn_object(container=self.container.name,
                name=self.name, email_addresses=email_addresses)


    def get_metadata(self):
        """Returns this object's metadata."""
        return self.client.get_object_metadata(self.container, self)


    def set_metadata(self, metadata, clear=False, prefix=None):
        """
        Sets this object's metadata, optionally clearing existing metadata.
        """
        self.client.set_object_metadata(self.container, self, metadata,
                clear=clear, prefix=prefix)


    def remove_metadata_key(self, key):
        """
        Removes the specified key from the storage object's metadata. If the
        key does not exist in the metadata, nothing is done.
        """
        self.client.remove_object_metadata_key(self.container, self, key)


    def copy(self, new_container, new_obj_name=None, extra_info=None):
        """
        Copies this object to the new container, optionally giving it a new name.
        If you copy to the same container, you must supply a different name.
        """
        return self.container.copy_object(self, new_container,
                new_obj_name=new_obj_name, extra_info=extra_info)


    def move(self, new_container, new_obj_name=None, extra_info=None):
        """
        Works just like copy_object, except that this object is deleted after a
        successful copy. This means that this storage_object reference will no
        longer be valid.
        """
        return self.container.move_object(self, new_container,
                new_obj_name=new_obj_name, extra_info=extra_info)


    def change_content_type(self, new_ctype, guess=False):
        """
        Copies object to itself, but applies a new content-type. The guess
        feature requires the container to be CDN-enabled. If not then the
        content-type must be supplied. If using guess with a CDN-enabled
        container, new_ctype can be set to None.
        Failure during the put will result in a swift exception.
        """
        self.client.change_object_content_type(self.container, self,
                new_ctype=new_ctype, guess=guess)


    def get_temp_url(self, seconds, method="GET"):
        """
        Returns a URL that can be used to access this object. The URL will
        expire after `seconds` seconds.

        The only methods supported are GET and PUT. Anything else will raise
        an InvalidTemporaryURLMethod exception.
        """
        return self.client.get_temp_url(self.container, self, seconds=seconds,
                method=method)


    def delete_in_seconds(self, seconds):
        """
        Sets the object to be deleted after the specified number of seconds.
        """
        self.client.delete_object_in_seconds(self.container, self, seconds)


    def __repr__(self):
        return "<Object '%s' (%s)>" % (self.name, self.content_type)
