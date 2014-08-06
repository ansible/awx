#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c)2012 Rackspace US, Inc.

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

import logging
import datetime
from functools import wraps
import hashlib
import hmac
# Use eventlet if available
try:
    import eventlet.green.httplib as httplib
except ImportError:
    import httplib
import locale
import math
import os
import re
import socket
import threading
import time
import urllib
import urlparse
import uuid
import mimetypes

import six

from swiftclient import client as _swift_client
import pyrax
from pyrax.cf_wrapper.container import Container
from pyrax.cf_wrapper.storage_object import StorageObject
import pyrax.utils as utils
import pyrax.exceptions as exc


EARLY_DATE_STR = "1900-01-01T00:00:00"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"
HEAD_DATE_FORMAT = "%a, %d %b %Y %H:%M:%S %Z"
# Format of last_modified in list responses, reverse engineered from sample
# responses at
# http://docs.rackspace.com/files/api/v1/cf-devguide/content/
#   Serialized_List_Output-d1e1460.html
LIST_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"
CONNECTION_TIMEOUT = 20
CONNECTION_RETRIES = 5
AUTH_ATTEMPTS = 2
MAX_BULK_DELETE = 10000
DEFAULT_CHUNKSIZE = 65536

no_such_container_pattern = re.compile(
        r"Container (?:GET|HEAD) failed: .+/(.+) 404")
no_such_object_pattern = re.compile(r"Object (?:GET|HEAD) failed: .+/(.+) 404")
etag_fail_pat = r"Object PUT failed: .+/([^/]+)/(\S+) 422 Unprocessable Entity"
etag_failed_pattern = re.compile(etag_fail_pat)


def _close_swiftclient_conn(conn):
    """Swiftclient often leaves the connection open."""
    try:
        conn.http_conn[1].close()
    except Exception:
        pass


def plug_hole_in_swiftclient_auth(clt, url):
    """
    This is necessary because swiftclient has an issue when a token expires and
    it needs to re-authenticate against Rackspace auth. It is a temporary
    workaround until we can fix swiftclient.
    """
    conn = clt.connection
    conn.token = clt.identity.token
    conn.url = url


def handle_swiftclient_exception(fnc):
    @wraps(fnc)
    def _wrapped(self, *args, **kwargs):
        attempts = 0
        clt_url = self.connection.url

        while attempts < AUTH_ATTEMPTS:
            attempts += 1
            try:
                _close_swiftclient_conn(self.connection)
                ret = fnc(self, *args, **kwargs)
                return ret
            except _swift_client.ClientException as e:
                str_error = "%s" % e
                if e.http_status == 401:
                    if attempts < AUTH_ATTEMPTS:
                        # Assume it is an auth failure. Re-auth and retry.
                        # NOTE: This is a hack to get around an apparent bug
                        # in python-swiftclient when using Rackspace auth.
                        self.identity.authenticate(connect=False)
                        if self.identity.authenticated:
                            self.plug_hole_in_swiftclient_auth(self, clt_url)
                        continue
                elif e.http_status == 404:
                    bad_container = no_such_container_pattern.search(str_error)
                    if bad_container:
                        raise exc.NoSuchContainer("Container '%s' doesn't exist"
                                % bad_container.groups()[0])
                    bad_object = no_such_object_pattern.search(str_error)
                    if bad_object:
                        raise exc.NoSuchObject("Object '%s' doesn't exist" %
                                bad_object.groups()[0])
                failed_upload = etag_failed_pattern.search(str_error)
                if failed_upload:
                    cont, fname = failed_upload.groups()
                    raise exc.UploadFailed("Upload of file '%(fname)s' to "
                            "container '%(cont)s' failed." % locals())
                # Not handled; re-raise
                raise
    return _wrapped


def ensure_cdn(fnc):
    @wraps(fnc)
    def _wrapped(self, *args, **kwargs):
        if not self.connection.cdn_connection:
            raise exc.NotCDNEnabled("This service does not support "
                    "CDN-enabled containers.")
        return fnc(self, *args, **kwargs)
    return _wrapped


def _convert_head_object_last_modified_to_local(lm_str):
    # Need to convert last modified time to a datetime object.
    # Times are returned in default locale format, so we need to read
    # them as such, no matter what the locale setting may be.
    orig_locale = locale.getlocale(locale.LC_TIME)
    locale.setlocale(locale.LC_TIME, (None, None))
    try:
        tm_tuple = time.strptime(lm_str, HEAD_DATE_FORMAT)
    finally:
        locale.setlocale(locale.LC_TIME, orig_locale)
    dttm = datetime.datetime.fromtimestamp(time.mktime(tm_tuple))
    # Now convert it back to the format returned by GETting the object.
    dtstr = dttm.strftime(DATE_FORMAT)
    return dtstr


def _convert_list_last_modified_to_local(attdict):
    if "last_modified" in attdict:
        attdict = attdict.copy()
        list_date_format_with_tz = LIST_DATE_FORMAT + " %Z"
        last_modified_utc = attdict["last_modified"] + " UTC"
        tm_tuple = time.strptime(last_modified_utc,
                                 list_date_format_with_tz)
        dttm = datetime.datetime.fromtimestamp(time.mktime(tm_tuple))

        dttm_with_micros = datetime.datetime.strptime(last_modified_utc,
                list_date_format_with_tz)
        # Round the date *up* in seconds, to match the last modified time
        # in head requests
        # https://review.openstack.org/#/c/55488/
        if dttm_with_micros.microsecond > 0:
            dttm += datetime.timedelta(seconds=1)
        attdict["last_modified"] = dttm.strftime(DATE_FORMAT)
    return attdict


def _quote(val):
    if isinstance(val, six.text_type):
        val = val.encode("utf-8")
    return urllib.quote(val)



class CFClient(object):
    """
    Wraps the calls to swiftclient with objects representing Containers
    and StorageObjects.

    These classes allow a developer to work with regular Python objects
    instead of calling functions that return primitive types.
    """
    # Defaults for CDN
    cdn_enabled = False
    default_cdn_ttl = 86400
    _container_cache = {}
    _cached_temp_url_key = ""
    # Upload size limit
    max_file_size = 5368709119  # 5GB - 1
    # Folder upload status dict. Each upload will generate its own UUID key.
    # The app can use that key query the status of the upload. This dict
    # will also be used to hold the flag to interrupt uploads in progress.
    folder_upload_status = {}
    # Interval in seconds between checks for completion of bulk deletes.
    bulk_delete_interval = 1


    def __init__(self, auth_endpoint, username, api_key=None, password=None,
            tenant_name=None, preauthurl=None, preauthtoken=None,
            auth_version="2", os_options=None, verify_ssl=True,
            http_log_debug=False):
        self.connection = None
        self.cdn_connection = None
        self.http_log_debug = http_log_debug
        self._http_log = _swift_client.http_log
        os.environ["SWIFTCLIENT_DEBUG"] = "True" if http_log_debug else ""
        self._make_connections(auth_endpoint, username, api_key, password,
                tenant_name=tenant_name, preauthurl=preauthurl,
                preauthtoken=preauthtoken, auth_version=auth_version,
                os_options=os_options, verify_ssl=verify_ssl,
                http_log_debug=http_log_debug)


    # Constants used in metadata headers
    @property
    def account_meta_prefix(self):
        return "X-Account-Meta-"

    @property
    def container_meta_prefix(self):
        return "X-Container-Meta-"

    @property
    def object_meta_prefix(self):
        return "X-Object-Meta-"

    @property
    def cdn_meta_prefix(self):
        return "X-Cdn-"


    def _make_connections(self, auth_endpoint, username, api_key, password,
            tenant_name=None, preauthurl=None, preauthtoken=None,
            auth_version="2", os_options=None, verify_ssl=True,
            http_log_debug=None):
        cdn_url = os_options.pop("object_cdn_url", None)
        pw_key = api_key or password
        insecure = not verify_ssl
        self.connection = Connection(authurl=auth_endpoint, user=username,
                key=pw_key, tenant_name=tenant_name, preauthurl=preauthurl,
                preauthtoken=preauthtoken, auth_version=auth_version,
                os_options=os_options, insecure=insecure,
                http_log_debug=http_log_debug)
        if cdn_url:
            self.connection._make_cdn_connection(cdn_url)


    def _massage_metakeys(self, dct, prfx):
        """
        Returns a copy of the supplied dictionary, prefixing any keys that do
        not begin with the specified prefix accordingly.
        """
        lowprefix = prfx.lower()
        ret = {}
        for k, v in dct.iteritems():
            if not k.lower().startswith(lowprefix):
                k = "%s%s" % (prfx, k)
            ret[k] = v
        return ret


    def _resolve_name(self, val):
        return val if isinstance(val, six.string_types) else val.name


    @handle_swiftclient_exception
    def get_account_metadata(self, prefix=None):
        headers = self.connection.head_account()
        if prefix is None:
            prefix = self.account_meta_prefix
        prefix = prefix.lower()
        ret = {}
        for hkey, hval in headers.iteritems():
            if hkey.lower().startswith(prefix):
                ret[hkey] = hval
        return ret


    @handle_swiftclient_exception
    def set_account_metadata(self, metadata, clear=False,
            extra_info=None, prefix=None):
        """
        Accepts a dictionary of metadata key/value pairs and updates the
        specified account metadata with them.

        If 'clear' is True, any existing metadata is deleted and only the
        passed metadata is retained. Otherwise, the values passed here update
        the account's metadata.

        'extra_info' is an optional dictionary which will be populated with
        'status', 'reason', and 'headers' keys from the underlying swiftclient
        call.

        By default, the standard account metadata prefix ('X-Account-Meta-') is
        prepended to the header name if it isn't present. For non-standard
        headers, you must include a non-None prefix, such as an empty string.
        """
        # Add the metadata prefix, if needed.
        if prefix is None:
            prefix = self.account_meta_prefix
        massaged = self._massage_metakeys(metadata, prefix)
        new_meta = {}
        if clear:
            curr_meta = self.get_account_metadata()
            for ckey in curr_meta:
                new_meta[ckey] = ""
        utils.case_insensitive_update(new_meta, massaged)
        self.connection.post_account(new_meta, response_dict=extra_info)


    @handle_swiftclient_exception
    def get_temp_url_key(self, cached=True):
        """
        Returns the current TempURL key, or None if it has not been set.

        By default the value returned is cached. To force an API call to get
        the current value on the server, pass `cached=False`.
        """
        meta = self._cached_temp_url_key
        if not cached or not meta:
            key = "%stemp-url-key" % self.account_meta_prefix.lower()
            meta = self.get_account_metadata().get(key)
            self._cached_temp_url_key = meta
        return meta


    @handle_swiftclient_exception
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
        an InvalidTemporaryURLMethod exception.

        If you have your Temporary URL key, you can pass it in directly and
        potentially save an API call to retrieve it. If you don't pass in the
        key, and don't wish to use any cached value, pass `cached=False`.
        """
        cname = self._resolve_name(container)
        oname = self._resolve_name(obj)
        mod_method = method.upper().strip()
        if mod_method not in ("GET", "PUT"):
            raise exc.InvalidTemporaryURLMethod("Method must be either 'GET' "
                    "or 'PUT'; received '%s'." % method)
        if not key:
            key = self.get_temp_url_key(cached=cached)
        if not key:
            raise exc.MissingTemporaryURLKey("You must set the key for "
                    "Temporary URLs before you can generate them. This is "
                    "done via the `set_temp_url_key()` method.")
        conn_url = self.connection.url
        v1pos = conn_url.index("/v1/")
        base_url = conn_url[:v1pos]
        path_parts = (conn_url[v1pos:], cname, oname)
        cleaned = (part.strip("/\\") for part in path_parts)
        pth = "/%s" % "/".join(cleaned)
        if isinstance(pth, six.text_type):
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


    def delete_object_in_seconds(self, cont, obj, seconds,
            extra_info=None):
        """
        Sets the object in the specified container to be deleted after the
        specified number of seconds.
        """
        meta = {"X-Delete-After": str(seconds)}
        self.set_object_metadata(cont, obj, meta, prefix="", clear=True)


    @handle_swiftclient_exception
    def get_container_metadata(self, container, prefix=None):
        """Returns a dictionary containing the metadata for the container."""
        cname = self._resolve_name(container)
        headers = self.connection.head_container(cname)
        if prefix is None:
            prefix = self.container_meta_prefix
        prefix = prefix.lower()
        ret = {}
        for hkey, hval in headers.iteritems():
            if hkey.lower().startswith(prefix):
                ret[hkey] = hval
        return ret


    @handle_swiftclient_exception
    def set_container_metadata(self, container, metadata, clear=False,
            extra_info=None, prefix=None):
        """
        Accepts a dictionary of metadata key/value pairs and updates the
        specified container metadata with them.

        If 'clear' is True, any existing metadata is deleted and only the
        passed metadata is retained. Otherwise, the values passed here update
        the container's metadata.

        'extra_info' is an optional dictionary which will be populated with
        'status', 'reason', and 'headers' keys from the underlying swiftclient
        call.

        By default, the standard container metadata prefix
        ('X-Container-Meta-') is prepended to the header name if it isn't
        present. For non-standard headers, you must include a non-None prefix,
        such as an empty string.
        """
        # Add the metadata prefix, if needed.
        if prefix is None:
            prefix = self.container_meta_prefix
        massaged = self._massage_metakeys(metadata, prefix)
        cname = self._resolve_name(container)
        new_meta = {}
        if clear:
            curr_meta = self.get_container_metadata(cname)
            for ckey in curr_meta:
                new_meta[ckey] = ""
        utils.case_insensitive_update(new_meta, massaged)
        self.connection.post_container(cname, new_meta,
                response_dict=extra_info)


    @handle_swiftclient_exception
    def remove_container_metadata_key(self, container, key,
            prefix=None, extra_info=None):
        """
        Removes the specified key from the container's metadata. If the key
        does not exist in the metadata, nothing is done.
        """
        if prefix is None:
            prefix = self.container_meta_prefix
        prefix = prefix.lower()
        meta_dict = {key: ""}
        # Add the metadata prefix, if needed.
        massaged = self._massage_metakeys(meta_dict, prefix)
        cname = self._resolve_name(container)
        self.connection.post_container(cname, massaged,
                response_dict=extra_info)


    @ensure_cdn
    @handle_swiftclient_exception
    def get_container_cdn_metadata(self, container):
        """
        Returns a dictionary containing the CDN metadata for the container.
        """
        cname = self._resolve_name(container)
        response = self.connection.cdn_request("HEAD", [cname])
        headers = response.getheaders()
        # Read the response to force it to close for the next request.
        response.read()
        # headers is a list of 2-tuples instead of a dict.
        return dict(headers)


    @ensure_cdn
    @handle_swiftclient_exception
    def set_container_cdn_metadata(self, container, metadata):
        """
        Accepts a dictionary of metadata key/value pairs and updates
        the specified container metadata with them.

        NOTE: arbitrary metadata headers are not allowed. The only metadata
        you can update are: X-Log-Retention, X-CDN-enabled, and X-TTL.
        """
        ct = self.get_container(container)
        allowed = ("x-log-retention", "x-cdn-enabled", "x-ttl")
        hdrs = {}
        bad = []
        for mkey, mval in metadata.iteritems():
            if mkey.lower() not in allowed:
                bad.append(mkey)
                continue
            hdrs[mkey] = str(mval)
        if bad:
            raise exc.InvalidCDNMetadata("The only CDN metadata you can "
                    "update are: X-Log-Retention, X-CDN-enabled, and X-TTL. "
                    "Received the following illegal item(s): %s" %
                    ", ".join(bad))
        response = self.connection.cdn_request("POST", [ct.name], hdrs=hdrs)
        response.close()


    @handle_swiftclient_exception
    def get_object_metadata(self, container, obj, prefix=None):
        """Retrieves any metadata for the specified object."""
        if prefix is None:
            prefix = self.object_meta_prefix
        cname = self._resolve_name(container)
        oname = self._resolve_name(obj)
        headers = self.connection.head_object(cname, oname)
        prefix = prefix.lower()
        ret = {}
        for hkey, hval in headers.iteritems():
            if hkey.lower().startswith(prefix):
                ret[hkey] = hval
        return ret


    @handle_swiftclient_exception
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
        # Add the metadata prefix, if needed.
        if prefix is None:
            prefix = self.object_meta_prefix
        massaged = self._massage_metakeys(metadata, prefix)
        cname = self._resolve_name(container)
        oname = self._resolve_name(obj)
        new_meta = {}
        # Note that the API for object POST is the opposite of that for
        # container POST: for objects, all current metadata is deleted,
        # whereas for containers you need to set the values to an empty
        # string to delete them.
        if not clear:
            obj_meta = self.get_object_metadata(cname, oname, prefix=prefix)
            new_meta = self._massage_metakeys(obj_meta, prefix)
        utils.case_insensitive_update(new_meta, massaged)
        # Remove any empty values, since the object metadata API will
        # store them.
        to_pop = []
        for key, val in new_meta.iteritems():
            if not val:
                to_pop.append(key)
        for key in to_pop:
            new_meta.pop(key)
        self.connection.post_object(cname, oname, new_meta,
                response_dict=extra_info)


    @handle_swiftclient_exception
    def remove_object_metadata_key(self, container, obj, key, prefix=None):
        """
        Removes the specified key from the storage object's metadata. If the
        key does not exist in the metadata, nothing is done.
        """
        self.set_object_metadata(container, obj, {key: ""}, prefix=prefix)


    @handle_swiftclient_exception
    def create_container(self, name, extra_info=None):
        """Creates a container with the specified name.

        'extra_info' is an optional dictionary which will be
        populated with 'status', 'reason', and 'headers' keys from the
        underlying swiftclient call.
        """
        name = self._resolve_name(name)
        self.connection.put_container(name, response_dict=extra_info)
        return self.get_container(name)


    @handle_swiftclient_exception
    def delete_container(self, container, del_objects=False, extra_info=None):
        """
        Deletes the specified container. This will fail if the container
        still has objects stored in it; if that's the case and you want
        to delete the container anyway, set del_objects to True, and
        the container's objects will be deleted before the container is
        deleted.

        'extra_info' is an optional dictionary which will be
        populated with 'status', 'reason', and 'headers' keys from the
        underlying swiftclient call.
        """
        self.remove_container_from_cache(container)
        cname = self._resolve_name(container)
        if del_objects:
            nms = self.get_container_object_names(cname, full_listing=True)
            self.bulk_delete(cname, nms, async=False)
        self.connection.delete_container(cname, response_dict=extra_info)
        return True


    def remove_container_from_cache(self, container):
        """Removes the container from the cache."""
        nm = self._resolve_name(container)
        self._container_cache.pop(nm, None)


    @handle_swiftclient_exception
    def delete_object(self, container, name, extra_info=None):
        """
        Deletes the specified object from the container.

        'extra_info' is an optional dictionary which will be
        populated with 'status', 'reason', and 'headers' keys from the
        underlying swiftclient call.
        """
        ct = self.get_container(container)
        ct.remove_from_cache(name)
        oname = self._resolve_name(name)
        self.connection.delete_object(ct.name, oname,
                response_dict=extra_info)
        return True


    @handle_swiftclient_exception
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


    @handle_swiftclient_exception
    def get_object(self, container, obj):
        """Returns a StorageObject instance for the object in the container."""
        cname = self._resolve_name(container)
        oname = self._resolve_name(obj)
        obj_info = self.connection.head_object(cname, oname)
        lm_str = obj_info["last-modified"]
        dtstr = _convert_head_object_last_modified_to_local(lm_str)
        obj = StorageObject(self, self.get_container(container),
                name=oname, content_type=obj_info["content-type"],
                total_bytes=int(obj_info["content-length"]),
                last_modified=dtstr, etag=obj_info["etag"])
        return obj


    @handle_swiftclient_exception
    def store_object(self, container, obj_name, data, content_type=None,
            etag=None, content_encoding=None, ttl=None, return_none=False,
            chunk_size=None, headers=None, extra_info=None):
        """
        Creates a new object in the specified container, and populates it with
        the given data. A StorageObject reference to the uploaded file
        will be returned, unless 'return_none' is set to True.

        'chunk_size' represents the number of bytes of data to write; it
        defaults to 65536. It is used only if the the 'data' parameter is an
        object with a 'read' method; otherwise, it is ignored.

        If you wish to specify additional headers to be passed to the PUT
        request, pass them as a dict in the 'headers' parameter. It is the
        developer's responsibility to ensure that any headers are valid; pyrax
        does no checking.

        'extra_info' is an optional dictionary which will be
        populated with 'status', 'reason', and 'headers' keys from the
        underlying swiftclient call.
        """
        cont = self.get_container(container)
        if headers is None:
            headers = {}
        if content_encoding is not None:
            headers["Content-Encoding"] = content_encoding
        if ttl is not None:
            headers["X-Delete-After"] = ttl
        if chunk_size and hasattr(data, "read"):
            # Chunked file-like object
            self.connection.put_object(cont.name, obj_name, contents=data,
                    content_type=content_type, etag=etag, headers=headers,
                    chunk_size=chunk_size, response_dict=extra_info)
        else:
            with utils.SelfDeletingTempfile() as tmp:
                with open(tmp, "wb") as tmpfile:
                    try:
                        tmpfile.write(data)
                    except UnicodeEncodeError:
                        udata = data.encode("utf-8")
                        tmpfile.write(udata)
                with open(tmp, "rb") as tmpfile:
                    self.connection.put_object(cont.name, obj_name,
                            contents=tmpfile, content_type=content_type,
                            etag=etag, headers=headers, chunk_size=chunk_size,
                            response_dict=extra_info)
        if return_none:
            return None
        else:
            return self.get_object(container, obj_name)


    @handle_swiftclient_exception
    def copy_object(self, container, obj, new_container, new_obj_name=None,
            extra_info=None):
        """
        Copies the object to the new container, optionally giving it a new name.
        If you copy to the same container, you must supply a different name.
        """
        cont = self.get_container(container)
        obj = self.get_object(cont, obj)
        new_cont = self.get_container(new_container)
        if new_obj_name is None:
            new_obj_name = obj.name
        hdrs = {"X-Copy-From": "/%s/%s" % (cont.name, obj.name)}
        return self.connection.put_object(new_cont.name, new_obj_name,
                contents=None, headers=hdrs, response_dict=extra_info)


    @handle_swiftclient_exception
    def move_object(self, container, obj, new_container, new_obj_name=None,
            extra_info=None):
        """
        Works just like copy_object, except that the source object is deleted
        after a successful copy.
        """
        new_obj_etag = self.copy_object(container, obj, new_container,
                new_obj_name=new_obj_name, extra_info=extra_info)
        if new_obj_etag:
            # Copy succeeded; delete the original.
            self.delete_object(container, obj)
        return new_obj_etag


    @handle_swiftclient_exception
    def change_object_content_type(self, container, obj, new_ctype,
            guess=False, extra_info=None):
        """
        Copies object to itself, but applies a new content-type. The guess
        feature requires the container to be CDN-enabled. If not then the
        content-type must be supplied. If using guess with a CDN-enabled
        container, new_ctype can be set to None.
        Failure during the put will result in a swift exception.
        """
        cont = self.get_container(container)
        obj = self.get_object(cont, obj)
        if guess and cont.cdn_enabled:
            # Test against the CDN url to guess the content-type.
            obj_url = "%s/%s" % (cont.cdn_uri, obj.name)
            new_ctype = mimetypes.guess_type(obj_url)[0]
        hdrs = {"X-Copy-From": "/%s/%s" % (cont.name, obj.name)}
        self.connection.put_object(cont.name, obj.name, contents=None,
                headers=hdrs, content_type=new_ctype,
                response_dict=extra_info)
        cont.remove_from_cache(obj.name)
        return

    @handle_swiftclient_exception
    def upload_file(self, container, file_or_path, obj_name=None,
            content_type=None, etag=None, return_none=False,
            content_encoding=None, ttl=None, extra_info=None,
            content_length=None, headers=None):
        """
        Uploads the specified file to the container. If no name is supplied,
        the file's name will be used. Either a file path or an open file-like
        object may be supplied. A StorageObject reference to the uploaded file
        will be returned, unless 'return_none' is set to True.

        You may optionally set the `content_type` and `content_encoding`
        parameters; pyrax will create the appropriate headers when the object
        is stored.

        If the size of the file is known, it can be passed as `content_length`.

        If you wish to specify additional headers to be passed to the PUT
        request, pass them as a dict in the 'headers' parameter. It is the
        developer's responsibility to ensure that any headers are valid; pyrax
        does no checking.

        If you wish for the object to be temporary, specify the time it should
        be stored in seconds in the `ttl` parameter. If this is specified, the
        object will be deleted after that number of seconds.
        """
        # TODO-BC: response_dict when looping? as a list of them?
        cont = self.get_container(container)

        def get_file_size(fileobj):
            """Returns the size of a file-like object."""
            currpos = fileobj.tell()
            fileobj.seek(0, 2)
            total_size = fileobj.tell()
            fileobj.seek(currpos)
            return total_size

        def upload(fileobj, content_type, etag, headers):
            if isinstance(fileobj, six.string_types):
                # This is an empty directory file
                fsize = 0
            else:
                if content_length is None:
                    fsize = get_file_size(fileobj)
                else:
                    fsize = content_length
            if fsize <= self.max_file_size:
                # We can just upload it as-is.
                return self.connection.put_object(cont.name, obj_name,
                        contents=fileobj, content_type=content_type,
                        etag=etag, headers=headers, response_dict=extra_info)
            # Files larger than self.max_file_size must be segmented
            # and uploaded separately.
            num_segments = int(math.ceil(float(fsize) / self.max_file_size))
            digits = int(math.log10(num_segments)) + 1
            # NOTE: This could be greatly improved with threading or other
            # async design.
            for segment in six.moves.range(num_segments):
                sequence = str(segment + 1).zfill(digits)
                seg_name = "%s.%s" % (obj_name, sequence)
                with utils.SelfDeletingTempfile() as tmpname:
                    with open(tmpname, "wb") as tmp:
                        tmp.write(fileobj.read(self.max_file_size))
                    with open(tmpname, "rb") as tmp:
                        # We have to calculate the etag for each segment
                        etag = utils.get_checksum(tmp)
                        self.connection.put_object(cont.name, seg_name,
                                contents=tmp, content_type=content_type,
                                etag=etag, headers=headers,
                                response_dict=extra_info)
            # Upload the manifest
            headers["X-Object-Manifest"] = "%s/%s." % (cont.name, obj_name)
            return self.connection.put_object(cont.name, obj_name,
                    contents=None, headers=headers,
                    response_dict=extra_info)

        ispath = isinstance(file_or_path, six.string_types)
        if ispath:
            # Make sure it exists
            if not os.path.exists(file_or_path):
                raise exc.FileNotFound("The file '%s' does not exist" %
                        file_or_path)
            fname = os.path.basename(file_or_path)
        else:
            try:
                fname = os.path.basename(file_or_path.name)
            except AttributeError:
                fname = None
        if not obj_name:
            obj_name = fname
        if not obj_name:
            raise InvalidUploadID("No filename provided and/or it cannot be "
                    "inferred from context")

        if headers is None:
            headers = {}
        if content_encoding is not None:
            headers["Content-Encoding"] = content_encoding
        if ttl is not None:
            headers["X-Delete-After"] = ttl

        if ispath and os.path.isfile(file_or_path):
            # Need to wrap the call in a context manager
            with open(file_or_path, "rb") as ff:
                upload(ff, content_type, etag, headers)
        else:
            upload(file_or_path, content_type, etag, headers)
        if return_none:
            return None
        else:
            return self.get_object(container, obj_name)


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

        ignore = utils.coerce_string_to_list(ignore)
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
        self._sync_folder_to_container(folder_path, cont, prefix="",
                delete=delete, include_hidden=include_hidden, ignore=ignore,
                ignore_timestamps=ignore_timestamps,
                object_prefix=object_prefix, verbose=verbose)
        # Unset the _remote_files
        self._remote_files = None


    def _sync_folder_to_container(self, folder_path, cont, prefix, delete,
            include_hidden, ignore, ignore_timestamps, object_prefix, verbose):
        """
        This is the internal method that is called recursively to handle
        nested folder structures.
        """
        fnames = os.listdir(folder_path)
        ignore = utils.coerce_string_to_list(ignore)
        log = logging.getLogger("pyrax")
        if not include_hidden:
            ignore.append(".*")
        for fname in fnames:
            if utils.match_pattern(fname, ignore):
                continue
            pth = os.path.join(folder_path, fname)
            if os.path.isdir(pth):
                subprefix = fname
                if prefix:
                    subprefix = "%s/%s" % (prefix, subprefix)
                self._sync_folder_to_container(pth, cont, prefix=subprefix,
                        delete=delete, include_hidden=include_hidden,
                        ignore=ignore, ignore_timestamps=ignore_timestamps,
                        object_prefix=object_prefix, verbose=verbose)
                continue
            self._local_files.append(os.path.join(object_prefix, prefix, fname))
            local_etag = utils.get_checksum(pth)
            fullname = fname
            fullname_with_prefix = "%s/%s" % (object_prefix, fname)
            if prefix:
                fullname = "%s/%s" % (prefix, fname)
                fullname_with_prefix = "%s/%s/%s" % (object_prefix, prefix, fname)
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
                        if verbose:
                            log.info("%s NOT UPLOADED because remote object is "
                                    "newer", fullname)
                        continue
                cont.upload_file(pth, obj_name=fullname_with_prefix,
                    etag=local_etag, return_none=True)
                if verbose:
                    log.info("%s UPLOADED", fullname)
            else:
                if verbose:
                    log.info("%s NOT UPLOADED because it already exists",
                            fullname)
        if delete and not prefix:
            self._delete_objects_not_in_list(cont, object_prefix)


    def _delete_objects_not_in_list(self, cont, object_prefix=""):
        """
        Finds all the objects in the specified container that are not present
        in the self._local_files list, and deletes them.
        """
        objnames = set(cont.get_object_names(prefix=object_prefix,
                full_listing=True))
        localnames = set(self._local_files)
        to_delete = list(objnames.difference(localnames))
        # We don't need to wait around for this to complete. Store the thread
        # reference in case it is needed at some point.
        self._thread = self.bulk_delete(cont, to_delete, async=True)


    def _valid_upload_key(fnc):
        def wrapped(self, upload_key, *args, **kwargs):
            try:
                self.folder_upload_status[upload_key]
            except KeyError:
                raise exc.InvalidUploadID("There is no folder upload with the "
                        "key '%s'." % upload_key)
            return fnc(self, upload_key, *args, **kwargs)
        return wrapped


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


    @handle_swiftclient_exception
    def fetch_object(self, container, obj, include_meta=False,
            chunk_size=None, size=None, extra_info=None):
        """
        Fetches the object from storage.

        If 'include_meta' is False, only the bytes representing the
        file is returned.

        Note: if 'chunk_size' is defined, you must fully read the object's
        contents before making another request.

        If 'size' is specified, only the first 'size' bytes of the object will
        be returned. If the object if smaller than 'size', the entire object is
        returned.

        When 'include_meta' is True, what is returned from this method is a
        2-tuple:
            Element 0: a dictionary containing metadata about the file.
            Element 1: a stream of bytes representing the object's contents.

        'extra_info' is an optional dictionary which will be
        populated with 'status', 'reason', and 'headers' keys from the
        underlying swiftclient call.
        """
        cname = self._resolve_name(container)
        oname = self._resolve_name(obj)
        (meta, data) = self.connection.get_object(cname, oname,
                resp_chunk_size=chunk_size, response_dict=extra_info)
        if include_meta:
            return (meta, data)
        else:
            return data


    @handle_swiftclient_exception
    def fetch_partial(self, container, obj, size):
        """
        Returns the first 'size' bytes of an object. If the object is smaller
        than the specified 'size' value, the entire object is returned.
        """
        gen = self.fetch_object(container, obj, chunk_size=size)
        ret = gen.next()
        _close_swiftclient_conn(self.connection)
        return ret


    def fetch_dlo(self, cont, name, chunk_size=None):
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
            fetch_object() call and wraps them to behave as file-like objects for
            uploading.
            """
            def __init__(self, gen, verbose=False):
                self.gen = gen
                self.verbose = verbose
                self.processed = 0
                self.interval = 0

            def read(self, size=None):
                self.interval += 1
                if self.verbose:
                    if self.interval > 1024:
                        self.interval = 0
                        logit(".")
                ret = self.gen.next()
                self.processed += len(ret)
                return ret

        parts = self.get_container_objects(cont, prefix=name)
        fetches = [(part.name, self.fetch_object(cont, part.name,
                    chunk_size=chunk_size))
                for part in parts
                if part.name != name]
        job = [(fetch[0], FetchChunker(fetch[1], verbose=False))
                for fetch in fetches]
        return job


    @handle_swiftclient_exception
    def download_object(self, container, obj, directory, structure=True):
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
        obj_name = self._resolve_name(obj)
        path, fname = os.path.split(obj_name)
        if structure:
            fullpath = os.path.join(directory, path)
            if not os.path.exists(fullpath):
                os.makedirs(fullpath)
            target = os.path.join(fullpath, fname)
        else:
            target = os.path.join(directory, fname)
        with open(target, "wb") as dl:
            dl.write(self.fetch_object(container, obj))


    @handle_swiftclient_exception
    def get_all_containers(self, limit=None, marker=None, **parms):
        hdrs, conts = self.connection.get_container("", limit=limit,
                marker=marker)
        ret = [Container(self, name=cont["name"], object_count=cont["count"],
                total_bytes=cont["bytes"]) for cont in conts]
        return ret


    @handle_swiftclient_exception
    def get_container(self, container, cached=True):
        """
        Returns a reference to the specified container. By default, if a
        reference to that container has already been retrieved, a cached
        reference will be returned. If you need to get an updated version of
        the container, pass `cached=False` to the method call.
        """
        cname = self._resolve_name(container)
        if not cname:
            raise exc.MissingName("No container name specified")
        cont = None
        if cached:
            cont = self._container_cache.get(cname)
        if not cont:
            hdrs = self.connection.head_container(cname)
            cont = Container(self, name=cname,
                    object_count=hdrs.get("x-container-object-count"),
                    total_bytes=hdrs.get("x-container-bytes-used"))
            self._container_cache[cname] = cont
        return cont
    get = get_container


    @handle_swiftclient_exception
    def get_container_objects(self, container, marker=None, limit=None,
            prefix=None, delimiter=None, full_listing=False):
        """
        Return a list of StorageObjects representing the objects in the
        container. You can use the marker and limit params to handle pagination,
        and the prefix and delimiter params to filter the objects returned.
        Also, by default only the first 10,000 objects are returned; if you set
        full_listing to True, all objects in the container are returned.
        """
        cname = self._resolve_name(container)
        hdrs, objs = self.connection.get_container(cname, marker=marker,
                limit=limit, prefix=prefix, delimiter=delimiter,
                full_listing=full_listing)
        cont = self.get_container(cname)
        return [StorageObject(self,
                              container=cont,
                              attdict=_convert_list_last_modified_to_local(obj))
                for obj in objs
                if "name" in obj]
    list_container_objects = get_container_objects


    @handle_swiftclient_exception
    def get_container_object_names(self, container, marker=None, limit=None,
            prefix=None, delimiter=None, full_listing=False):
        cname = self._resolve_name(container)
        hdrs, objs = self.connection.get_container(cname, marker=marker,
                limit=limit, prefix=prefix, delimiter=delimiter,
                full_listing=full_listing)
        cont = self.get_container(cname)
        return [obj["name"] for obj in objs]
    list_container_object_names = get_container_object_names


    @handle_swiftclient_exception
    def list_container_subdirs(self, container, marker=None, limit=None,
            prefix=None, delimiter=None, full_listing=False):
        """
        Returns a list of StorageObjects representing the pseudo-subdirectories
        in the specified container. You can use the marker and limit params to
        handle pagination, and the prefix param to filter the objects returned.
        The 'delimiter' parameter is ignored, as the only meaningful value is
        '/'.
        """
        cname = self._resolve_name(container)
        hdrs, objs = self.connection.get_container(cname, marker=marker,
                limit=limit, prefix=prefix, delimiter="/",
                full_listing=full_listing)
        cont = self.get_container(cname)
        return [StorageObject(self, container=cont, attdict=obj) for obj in objs
                if "subdir" in obj]


    @handle_swiftclient_exception
    def get_info(self):
        """
        Returns a tuple for the number of containers and total bytes in
        the account.
        """
        hdrs = self.connection.head_container("")
        return (hdrs["x-account-container-count"], hdrs["x-account-bytes-used"])


    @handle_swiftclient_exception
    def list(self, limit=None, marker=None, **parms):
        """Returns a list of all container objects."""
        hdrs, conts = self.connection.get_container("", limit=limit,
                marker=marker)
        ret = [self.get_container(cont["name"]) for cont in conts]
        return ret
    get_all_containers = list


    @handle_swiftclient_exception
    def list_containers(self, limit=None, marker=None, **parms):
        """Returns a list of all container names as strings."""
        hdrs, conts = self.connection.get_container("", limit=limit,
                marker=marker)
        ret = [cont["name"] for cont in conts]
        return ret
    list_container_names = list_containers


    @handle_swiftclient_exception
    def list_containers_info(self, limit=None, marker=None, **parms):
        """Returns a list of info on Containers.

        For each container, a dict containing the following keys is returned:
        \code
            name - the name of the container
            count - the number of objects in the container
            bytes - the total bytes in the container
        """
        hdrs, conts = self.connection.get_container("", limit=limit,
                marker=marker)
        return conts


    @ensure_cdn
    @handle_swiftclient_exception
    def list_public_containers(self):
        """Returns a list of all CDN-enabled containers."""
        response = self.connection.cdn_request("GET", [""])
        status = response.status
        if not 200 <= status < 300:
            raise exc.CDNFailed("Bad response: (%s) %s" % (status,
                    response.reason))
        return response.read().splitlines()


    def make_container_public(self, container, ttl=None):
        """Enables CDN access for the specified container."""
        return self._cdn_set_access(container, ttl, True)


    def make_container_private(self, container):
        """
        Disables CDN access to a container. It may still appear public until
        its TTL expires.
        """
        return self._cdn_set_access(container, None, False)


    @ensure_cdn
    def _cdn_set_access(self, container, ttl, enabled):
        """Used to enable or disable CDN access on a container."""
        if ttl is None:
            ttl = self.default_cdn_ttl
        ct = self.get_container(container)
        mthd = "PUT"
        hdrs = {"X-CDN-Enabled": "%s" % enabled}
        if enabled:
            hdrs["X-TTL"] = str(ttl)
        response = self.connection.cdn_request(mthd, [ct.name], hdrs=hdrs)
        status = response.status
        if not 200 <= status < 300:
            raise exc.CDNFailed("Bad response: (%s) %s" % (status,
                    response.reason))
        ct.cdn_ttl = ttl
        for hdr in response.getheaders():
            if hdr[0].lower() == "x-cdn-uri":
                ct.cdn_uri = hdr[1]
                break
        self.remove_container_from_cache(container)
        # Read the response to force it to close for the next request.
        response.read()


    def set_cdn_log_retention(self, container, enabled):
        """
        Defer the logic to the container. It will end up calling
        _set_cdn_log_retention() to change it on Cloud Files.
        """
        cont = self.get_container(container)
        cont.cdn_log_retention = enabled


    @ensure_cdn
    def _set_cdn_log_retention(self, container, enabled):
        """This does the actual call to the Cloud Files API."""
        hdrs = {"X-Log-Retention": "%s" % enabled}
        cname = self._resolve_name(container)
        response = self.connection.cdn_request("POST", [cname], hdrs=hdrs)
        status = response.status
        if not 200 <= status < 300:
            raise exc.CDNFailed("Bad response: (%s) %s" % (status,
                    response.reason))
        # Read the response to force it to close for the next request.
        response.read()


    def get_container_streaming_uri(self, container):
        """
        Returns the URI for streaming content, or None if CDN is not enabled.
        """
        cont = self.get_container(container)
        return cont.cdn_streaming_uri


    def get_container_ios_uri(self, container):
        """Returns the iOS URI, or None if CDN is not enabled."""
        cont = self.get_container(container)
        return cont.cdn_ios_uri


    def set_container_web_index_page(self, container, page):
        """
        Sets the header indicating the index page in a container
        when creating a static website.

        Note: the container must be CDN-enabled for this to have
        any effect.
        """
        hdr = {"X-Container-Meta-Web-Index": page}
        return self.set_container_metadata(container, hdr, clear=False)


    def set_container_web_error_page(self, container, page):
        """
        Sets the header indicating the error page in a container
        when creating a static website.

        Note: the container must be CDN-enabled for this to have
        any effect.
        """
        hdr = {"X-Container-Meta-Web-Error": page}
        return self.set_container_metadata(container, hdr, clear=False)


    @ensure_cdn
    @handle_swiftclient_exception
    def purge_cdn_object(self, container, name, email_addresses=None):
        ct = self.get_container(container)
        oname = self._resolve_name(name)
        if not ct.cdn_enabled:
            raise exc.NotCDNEnabled("The object '%s' is not in a "
                    "CDN-enabled container." % oname)
        hdrs = {}
        if email_addresses:
            if not isinstance(email_addresses, (list, tuple)):
                email_addresses = [email_addresses]
            emls = ", ".join(email_addresses)
            hdrs = {"X-Purge-Email": emls}
        response = self.connection.cdn_request("DELETE", [ct.name, oname],
                hdrs=hdrs)
        # Read the response to force it to close for the next request.
        response.read()
        return True


    def _get_user_agent(self):
        return self.connection.user_agent

    def _set_user_agent(self, val):
        self.connection.user_agent = val

    user_agent = property(_get_user_agent, _set_user_agent)


    def _get_http_log_debug(self):
        return self._http_log_debug

    def _set_http_log_debug(self, val):
        self._http_log_debug = val
        if val:
            os.environ["SWIFTCLIENT_DEBUG"] = "True"
        else:
            os.environ.pop("SWIFTCLIENT_DEBUG", False)

    http_log_debug = property(_get_http_log_debug, _set_http_log_debug, None,
            "Determines if all http traffic is logged to the display "
            "for debugging.")



class Connection(_swift_client.Connection):
    """This class wraps the swiftclient connection, adding support for CDN"""
    def __init__(self, *args, **kwargs):
        self.http_log_debug = kwargs.pop("http_log_debug", False)
        self._http_log = _swift_client.http_log
        self.url = None
        super(Connection, self).__init__(*args, **kwargs)
        # Add the user_agent, if not defined
        try:
            self.user_agent
        except AttributeError:
            self.user_agent = "swiftclient"
        self.cdn_connection = None


    def _make_cdn_connection(self, cdn_url=None):
        if cdn_url is not None:
            self.cdn_url = cdn_url
        parsed = urlparse.urlparse(self.cdn_url)
        is_ssl = parsed.scheme == "https"

        # Verify hostnames are valid and parse a port spec (if any)
        match = re.match(r"([a-zA-Z0-9\-\.]+):?([0-9]{2,5})?", parsed.netloc)
        if match:
            (host, port) = match.groups()
        else:
            host = parsed.netloc
            port = None
        if not port:
            port = 443 if is_ssl else 80
        port = int(port)
        path = parsed.path.strip("/")
        conn_class = httplib.HTTPSConnection if is_ssl else httplib.HTTPConnection
        self.cdn_connection = conn_class(host, port, timeout=CONNECTION_TIMEOUT)
        self.cdn_connection.is_ssl = is_ssl


    def cdn_request(self, method, path=[], data="", hdrs=None):
        """
        Given a method (i.e. GET, PUT, POST, etc.), a path, data, header and
        metadata dicts, performs an http request against the CDN service.

        Taken directly from the cloudfiles library and modified for use here.
        """
        pth = "/".join([_quote(elem) for elem in path])
        uri_path = urlparse.urlparse(self.uri).path
        path = "%s/%s" % (uri_path.rstrip("/"), pth)
        headers = {"Content-Length": str(len(data)),
                "User-Agent": self.user_agent,
                "X-Auth-Token": self.token}
        if isinstance(hdrs, dict):
            headers.update(hdrs)

        attempt = 0
        response = None
        while attempt < CONNECTION_RETRIES:
            if attempt:
                # Last try failed; re-create the connection
                self._make_cdn_connection()
            try:
                self.cdn_connection.request(method, path, data, headers)
                response = self.cdn_connection.getresponse()
            except (socket.error, IOError, httplib.HTTPException) as e:
                response = None
            if response:
                if response.status == 401:
                    self.identity.authenticate()
                    headers["X-Auth-Token"] = self.identity.token
                else:
                    break
            attempt += 1
        if self.http_log_debug:
            self._http_log((path, method), {"headers": headers, "data": data},
                    response, "")
        return response


    @property
    def uri(self):
        return self.url



class FolderUploader(threading.Thread):
    """
    Threading class to allow for uploading multiple files in the background.
    """
    def __init__(self, root_folder, container, ignore, upload_key, client,
            ttl=None):
        self.root_folder = root_folder.rstrip("/")
        if container:
            self.container = client.create_container(container)
        else:
            self.container = None
        self.ignore = utils.coerce_string_to_list(ignore)
        self.upload_key = upload_key
        self.ttl = ttl
        self.client = client
        threading.Thread.__init__(self)

    def folder_name_from_path(self, pth):
        """Convenience method that first strips trailing path separators."""
        return os.path.basename(pth.rstrip(os.sep))

    def upload_files_in_folder(self, arg, dirname, fnames):
        """Handles the iteration across files within a folder."""
        if utils.match_pattern(dirname, self.ignore):
            return False
        for fname in (nm for nm in fnames
                if not utils.match_pattern(nm, self.ignore)):
            if self.client._should_abort_folder_upload(self.upload_key):
                return
            full_path = os.path.join(dirname, fname)
            if os.path.isdir(full_path):
                # Skip folders; os.walk will include them in the next pass.
                continue
            obj_name = os.path.relpath(full_path, self.base_path)
            obj_size = os.stat(full_path).st_size
            self.client.upload_file(self.container, full_path,
                    obj_name=obj_name, return_none=True, ttl=self.ttl)
            self.client._update_progress(self.upload_key, obj_size)

    def run(self):
        """Starts the uploading thread."""
        root_path, folder_name = os.path.split(self.root_folder)
        self.base_path = os.path.join(root_path, folder_name)
        os.path.walk(self.root_folder, self.upload_files_in_folder, None)



class BulkDeleter(threading.Thread):
    """
    Threading class to allow for bulk deletion of objects from a container.
    """
    completed = False
    results = None

    def __init__(self, client, container, object_names):
        self.client = client
        self.container = container
        self.object_names = object_names
        threading.Thread.__init__(self)


    def run(self):
        client = self.client
        container = self.container
        object_names = self.object_names
        self.results = {"deleted": 0, "not_found": 0, "status": "",
                "errors": ""}
        res_keys = {"Number Deleted": "deleted",
                "Number Not Found": "not_found",
                "Response Status": "status",
                "Errors": "errors",
                }
        cname = client._resolve_name(container)
        parsed, conn = client.connection.http_connection()
        method = "DELETE"
        headers = {"X-Auth-Token": self.client.identity.token,
                "Content-type": "text/plain",
                }
        while object_names:
            this_batch, object_names = (object_names[:MAX_BULK_DELETE],
                    object_names[MAX_BULK_DELETE:])
            obj_paths = ("%s/%s" % (cname, nm) for nm in this_batch)
            body = _quote("\n".join(obj_paths))
            pth = "%s/?bulk-delete=1" % parsed.path
            conn.request(method, pth, body, headers)
            resp = conn.getresponse()
            status = resp.status
            reason = resp.reason
            resp_body = resp.read()
            for resp_line in resp_body.splitlines():
                if not resp_line.strip():
                    continue
                resp_key, val = resp_line.split(":", 1)
                result_key = res_keys.get(resp_key)
                if not result_key:
                    continue
                if result_key in ("deleted", "not_found"):
                    self.results[result_key] += int(val.strip())
                else:
                    self.results[result_key] = val.strip()
        self.completed = True
