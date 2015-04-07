# Copyright 2010 Jacob Kaplan-Moss
# Copyright 2012 OpenStack Foundation
# Copyright 2013 Rackspace Hosting
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
import abc
import contextlib
import hashlib
import os

import six
from six.moves.urllib import parse

from troveclient import common
from troveclient.openstack.common.apiclient import base
from troveclient.openstack.common.apiclient import exceptions
from troveclient import utils

# Python 2.4 compat
try:
    all
except NameError:
    def all(iterable):
        return True not in (not x for x in iterable)


def getid(obj):
    """Retrieves an id from object or integer.

    Abstracts the common pattern of allowing both an object or an object's
    ID as a parameter when dealing with relationships.
    """
    try:
        return obj.id
    except AttributeError:
        return obj


class Manager(utils.HookableMixin):
    """Manager defining CRUD operations for API.

    Managers interact with a particular type of API (servers, flavors,
    images, etc.) and provide CRUD operations for them.
    """
    resource_class = None

    def __init__(self, api):
        self.api = api

    def _paginated(self, url, response_key, limit=None, marker=None,
                   query_strings=None):
        query_strings = query_strings or {}
        url = common.append_query_strings(url, limit=limit, marker=marker,
                                          **query_strings)
        resp, body = self.api.client.get(url)
        if not body:
            raise Exception("Call to " + url + " did not return a body.")
        links = body.get('links', [])
        next_links = [link['href'] for link in links if link['rel'] == 'next']
        next_marker = None
        for link in next_links:
            # Extract the marker from the url.
            parsed_url = parse.urlparse(link)
            query_dict = dict(parse.parse_qsl(parsed_url.query))
            next_marker = query_dict.get('marker')
        data = [self.resource_class(self, res) for res in body[response_key]]
        return common.Paginated(data, next_marker=next_marker, links=links)

    def _list(self, url, response_key, obj_class=None, body=None):
        resp = None
        if body:
            resp, body = self.api.client.post(url, body=body)
        else:
            resp, body = self.api.client.get(url)

        if obj_class is None:
            obj_class = self.resource_class

        data = body[response_key]
        # NOTE(ja): keystone returns values as list as {'values': [ ... ]}
        #           unlike other services which just return the list...
        if isinstance(data, dict):
            try:
                data = data['values']
            except KeyError:
                pass

        with self.completion_cache('human_id', obj_class, mode="w"):
            with self.completion_cache('uuid', obj_class, mode="w"):
                return [obj_class(self, res, loaded=True)
                        for res in data if res]

    @contextlib.contextmanager
    def completion_cache(self, cache_type, obj_class, mode):
        """Bash-completion cache.

        The completion cache store items that can be used for bash
        autocompletion, like UUIDs or human-friendly IDs.

        A resource listing will clear and repopulate the cache.

        A resource create will append to the cache.

        Delete is not handled because listings are assumed to be performed
        often enough to keep the cache reasonably up-to-date.
        """
        base_dir = utils.env('TROVECLIENT_UUID_CACHE_DIR',
                             default="~/.troveclient")

        # NOTE(sirp): Keep separate UUID caches for each username + endpoint
        # pair
        username = utils.env('OS_USERNAME', 'TROVE_USERNAME')
        url = utils.env('OS_URL', 'NOVA_URL')
        uniqifier = hashlib.md5(username.encode('utf-8') +
                                url.encode('utf-8')).hexdigest()

        cache_dir = os.path.expanduser(os.path.join(base_dir, uniqifier))

        try:
            os.makedirs(cache_dir, 0o755)
        except OSError:
            # NOTE(kiall): This is typically either permission denied while
            #              attempting to create the directory, or the directory
            #              already exists. Either way, don't fail.
            pass

        resource = obj_class.__name__.lower()
        filename = "%s-%s-cache" % (resource, cache_type.replace('_', '-'))
        path = os.path.join(cache_dir, filename)

        cache_attr = "_%s_cache" % cache_type

        try:
            setattr(self, cache_attr, open(path, mode))
        except IOError:
            # NOTE(kiall): This is typically a permission denied while
            #              attempting to write the cache file.
            pass

        try:
            yield
        finally:
            cache = getattr(self, cache_attr, None)
            if cache:
                cache.close()
                delattr(self, cache_attr)

    def write_to_completion_cache(self, cache_type, val):
        cache = getattr(self, "_%s_cache" % cache_type, None)
        if cache:
            cache.write("%s\n" % val)

    def _get(self, url, response_key=None):
        resp, body = self.api.client.get(url)
        if response_key:
            return self.resource_class(self, body[response_key], loaded=True)
        else:
            return self.resource_class(self, body, loaded=True)

    def _create(self, url, body, response_key, return_raw=False, **kwargs):
        self.run_hooks('modify_body_for_create', body, **kwargs)
        resp, body = self.api.client.post(url, body=body)
        if return_raw:
            return body[response_key]

        with self.completion_cache('human_id', self.resource_class, mode="a"):
            with self.completion_cache('uuid', self.resource_class, mode="a"):
                return self.resource_class(self, body[response_key])

    def _delete(self, url):
        resp, body = self.api.client.delete(url)

    def _update(self, url, body, **kwargs):
        self.run_hooks('modify_body_for_update', body, **kwargs)
        resp, body = self.api.client.put(url, body=body)
        return body

    def _edit(self, url, body):
        resp, body = self.api.client.patch(url, body=body)
        return body


class ManagerWithFind(six.with_metaclass(abc.ABCMeta, Manager)):
    """Like a `Manager`, but with additional `find()`/`findall()` methods."""

    @abc.abstractmethod
    def list(self):
        pass

    def find(self, **kwargs):
        """Find a single item with attributes matching ``**kwargs``.

        This isn't very efficient: it loads the entire list then filters on
        the Python side.
        """
        matches = self.findall(**kwargs)
        num_matches = len(matches)
        if num_matches == 0:
            msg = "No %s matching %s." % (self.resource_class.__name__, kwargs)
            raise exceptions.NotFound(404, msg)
        elif num_matches > 1:
            raise exceptions.NoUniqueMatch
        else:
            return matches[0]

    def findall(self, **kwargs):
        """Find all items with attributes matching ``**kwargs``.

        This isn't very efficient: it loads the entire list then filters on
        the Python side.
        """
        found = []
        searches = list(kwargs.items())

        for obj in self.list():
            try:
                if all(getattr(obj, attr) == value
                       for (attr, value) in searches):
                    found.append(self.get(obj.id))
            except AttributeError:
                continue

        return found


class Resource(base.Resource):
    """A resource represents a particular instance of an object like server.

    This is pretty much just a bag for attributes.
    :param manager: Manager object
    :param info: dictionary representing resource attributes
    :param loaded: prevent lazy-loading if set to True
    """
    HUMAN_ID = False

    def __init__(self, manager, info, loaded=False):
        super(Resource, self).__init__(manager, info, loaded)

        # NOTE(sirp): ensure `id` is already present because if it isn't we'll
        # enter an infinite loop of __getattr__ -> get -> __init__ ->
        # __getattr__ -> ...
        if 'id' in self.__dict__ and len(str(self.id)) == 36:
            self.manager.write_to_completion_cache('uuid', self.id)

        human_id = self.human_id
        if human_id:
            self.manager.write_to_completion_cache('human_id', human_id)
