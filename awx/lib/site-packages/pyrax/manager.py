# Copyright 2010 Jacob Kaplan-Moss

# Copyright 2011 OpenStack LLC.
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

"""
Base utilities to build API operation managers and objects on top of.
"""

import pyrax.exceptions as exc
import pyrax.utils as utils


# Python 2.4 compat
try:
    all
except NameError:
    def all(iterable):
        return True not in (not x for x in iterable)



class BaseManager(object):
    """
    Managers interact with a particular type of API (servers, databases, dns,
    etc.) and provide CRUD operations for them.
    """
    resource_class = None
    response_key = None
    plural_response_key = None
    uri_base = None
    _hooks_map = {}


    def __init__(self, api, resource_class=None, response_key=None,
            plural_response_key=None, uri_base=None):
        self.api = api
        self.resource_class = resource_class
        self.response_key = response_key
        self.plural_response_key = plural_response_key
        if plural_response_key is None and response_key is not None:
            # Default to adding 's'
            self.plural_response_key = "%ss" % response_key
        self.uri_base = uri_base


    def list(self, limit=None, marker=None, return_raw=False):
        """
        Returns a list of resource objects. Pagination is supported through the
        optional 'marker' and 'limit' parameters.

        Some APIs do not follow the typical pattern in their responses, and the
        BaseManager subclasses will have to parse the raw response to get the
        desired information. For those cases, pass 'return_raw=True', and the
        response and response_body will be returned unprocessed.
        """
        uri = "/%s" % self.uri_base
        pagination_items = []
        if limit is not None:
            pagination_items.append("limit=%s" % limit)
        if marker is not None:
            pagination_items.append("marker=%s" % marker)
        pagination = "&".join(pagination_items)
        if pagination:
            uri = "%s?%s" % (uri, pagination)
        return self._list(uri, return_raw=return_raw)


    def head(self, item):
        """Makes a HEAD request on a specific item."""
        uri = "/%s/%s" % (self.uri_base, utils.get_id(item))
        return self._head(uri)


    def get(self, item):
        """Gets a specific item."""
        uri = "/%s/%s" % (self.uri_base, utils.get_id(item))
        return self._get(uri)


    def create(self, name, *args, **kwargs):
        """
        Subclasses need to implement the _create_body() method to return a dict
        that will be used for the API request body.

        For cases where no response is returned from the API on creation, pass
        `return_none=True` so that the _create method doesn't expect one.

        For cases where you do not want the _create method to attempt to parse
        the response, but instead have it returned directly, pass
        `return_raw=True`.

        For cases where the API returns information in the response and not the
        response_body, pass `return_response=True`.
        """
        return_none = kwargs.pop("return_none", False)
        return_raw = kwargs.pop("return_raw", False)
        return_response = kwargs.pop("return_response", False)
        body = self._create_body(name, *args, **kwargs)
        return self._create("/%s" % self.uri_base, body,
                return_none=return_none, return_raw=return_raw,
                return_response=return_response)


    def _create_body(self, name, *args, **kwargs):
        """
        Creates the dictionary that is passed in the POST call to create a new
        resource. Must be defined in each subclass.
        """
        raise NotImplementedError("Managers must define their _create_body() "
                "method.")


    def delete(self, item):
        """Deletes the specified item."""
        uri = "/%s/%s" % (self.uri_base, utils.get_id(item))
        return self._delete(uri)


    def _list(self, uri, obj_class=None, body=None, return_raw=False):
        """
        Handles the communication with the API when getting
        a full listing of the resources managed by this class.
        """
        if body:
            resp, resp_body = self.api.method_post(uri, body=body)
        else:
            resp, resp_body = self.api.method_get(uri)
        if return_raw:
            return (resp, resp_body)
        if obj_class is None:
            obj_class = self.resource_class

        data = self._data_from_response(resp_body)
        return [obj_class(self, res, loaded=False)
                for res in data if res]


    def _data_from_response(self, resp_body):
        """
        This works for most API responses, but some don't structure their
        listing responses the same way, so overriding this method allows
        subclasses to handle extraction for those outliers.
        """
        data = resp_body.get(self.plural_response_key, resp_body)
        # NOTE(ja): keystone returns values as list as {"values": [ ... ]}
        #           unlike other services which just return the list...
        if isinstance(data, dict):
            try:
                data = data["values"]
            except KeyError:
                pass
        return data


    def _head(self, uri):
        """
        Handles the communication with the API when performing a HEAD request
        on a specific resource managed by this class. Returns the headers
        contained in the response.
        """
        resp, resp_body = self.api.method_head(uri)
        return resp


    def _get(self, uri):
        """
        Handles the communication with the API when getting
        a specific resource managed by this class.
        """
        resp, resp_body = self.api.method_get(uri)
        return self.resource_class(self, resp_body, self.response_key,
                loaded=True)


    def _create(self, uri, body, return_none=False, return_raw=False,
            return_response=None, **kwargs):
        """
        Handles the communication with the API when creating a new
        resource managed by this class.
        """
        self.run_hooks("modify_body_for_create", body, **kwargs)
        resp, resp_body = self.api.method_post(uri, body=body)
        if return_none:
            # No response body
            return
        elif return_response:
            return resp
        elif return_raw:
            if self.response_key:
                return resp_body[self.response_key]
            else:
                return resp_body
        return self.resource_class(self, resp_body, self.response_key)


    def _delete(self, uri):
        """
        Handles the communication with the API when deleting
        a specific resource managed by this class.
        """
        _resp, _body = self.api.method_delete(uri)


    def _update(self, uri, body, **kwargs):
        """
        Handles the communication with the API when updating
        a specific resource managed by this class.
        """
        self.run_hooks("modify_body_for_update", body, **kwargs)
        resp, resp_body = self.api.method_put(uri, body=body)
        return resp_body


    def action(self, item, action_type, body={}):
        """
        Several API calls are lumped under the 'action' API. This
        is the generic handler for such calls.
        """
        uri = "/%s/%s/action" % (self.uri_base, utils.get_id(item))
        action_body = {action_type: body}
        return self.api.method_post(uri, body=action_body)


    def find(self, **kwargs):
        """
        Finds a single item with attributes matching ``**kwargs``.

        This isn't very efficient: it loads the entire list then filters on
        the Python side.
        """
        matches = self.findall(**kwargs)
        num_matches = len(matches)
        if not num_matches:
            msg = "No %s matching: %s." % (self.resource_class.__name__, kwargs)
            raise exc.NotFound(404, msg)
        if num_matches > 1:
            msg = "More than one %s matching: %s." % (
                    self.resource_class.__name__, kwargs)
            raise exc.NoUniqueMatch(400, msg)
        else:
            return matches[0]


    def findall(self, **kwargs):
        """
        Finds all items with attributes matching ``**kwargs``.

        This isn't very efficient: it loads the entire list then filters on
        the Python side.
        """
        found = []
        searches = kwargs.items()

        for obj in self.list():
            try:
                if all(getattr(obj, attr) == value
                        for (attr, value) in searches):
                    found.append(obj)
            except AttributeError:
                continue
        return found


    @classmethod
    def add_hook(cls, hook_type, hook_func):
        if hook_type not in cls._hooks_map:
            cls._hooks_map[hook_type] = []

        cls._hooks_map[hook_type].append(hook_func)


    @classmethod
    def run_hooks(cls, hook_type, *args, **kwargs):
        hook_funcs = cls._hooks_map.get(hook_type) or []
        for hook_func in hook_funcs:
            hook_func(*args, **kwargs)
