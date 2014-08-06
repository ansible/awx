# Copyright 2010 Jacob Kaplan-Moss

# Copyright 2011 OpenStack Foundation
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
import inspect

import six

from novaclient import exceptions
from novaclient.openstack.common.apiclient import base
from novaclient import utils

Resource = base.Resource


def getid(obj):
    """
    Abstracts the common pattern of allowing both an object or an object's ID
    as a parameter when dealing with relationships.
    """
    try:
        return obj.id
    except AttributeError:
        return obj


class Manager(utils.HookableMixin):
    """
    Managers interact with a particular type of API (servers, flavors, images,
    etc.) and provide CRUD operations for them.
    """
    resource_class = None

    def __init__(self, api):
        self.api = api

    def _write_object_to_completion_cache(self, obj):
        if hasattr(self.api, 'write_object_to_completion_cache'):
            self.api.write_object_to_completion_cache(obj)

    def _clear_completion_cache_for_class(self, obj_class):
        if hasattr(self.api, 'clear_completion_cache_for_class'):
            self.api.clear_completion_cache_for_class(obj_class)

    def _list(self, url, response_key, obj_class=None, body=None):
        if body:
            _resp, body = self.api.client.post(url, body=body)
        else:
            _resp, body = self.api.client.get(url)

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

        self._clear_completion_cache_for_class(obj_class)

        objs = []
        for res in data:
            if res:
                obj = obj_class(self, res, loaded=True)
                self._write_object_to_completion_cache(obj)
                objs.append(obj)

        return objs

    def _get(self, url, response_key):
        _resp, body = self.api.client.get(url)
        obj = self.resource_class(self, body[response_key], loaded=True)
        self._write_object_to_completion_cache(obj)
        return obj

    def _create(self, url, body, response_key, return_raw=False, **kwargs):
        self.run_hooks('modify_body_for_create', body, **kwargs)
        _resp, body = self.api.client.post(url, body=body)
        if return_raw:
            return body[response_key]

        obj = self.resource_class(self, body[response_key])
        self._write_object_to_completion_cache(obj)
        return obj

    def _delete(self, url):
        _resp, _body = self.api.client.delete(url)

    def _update(self, url, body, response_key=None, **kwargs):
        self.run_hooks('modify_body_for_update', body, **kwargs)
        _resp, body = self.api.client.put(url, body=body)
        if body:
            if response_key:
                return self.resource_class(self, body[response_key])
            else:
                return self.resource_class(self, body)


@six.add_metaclass(abc.ABCMeta)
class ManagerWithFind(Manager):
    """
    Like a `Manager`, but with additional `find()`/`findall()` methods.
    """

    @abc.abstractmethod
    def list(self):
        pass

    def find(self, **kwargs):
        """
        Find a single item with attributes matching ``**kwargs``.

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
        """
        Find all items with attributes matching ``**kwargs``.

        This isn't very efficient: it loads the entire list then filters on
        the Python side.
        """
        found = []
        searches = kwargs.items()

        detailed = True
        list_kwargs = {}

        list_argspec = inspect.getargspec(self.list)
        if 'detailed' in list_argspec.args:
            detailed = ("human_id" not in kwargs and
                        "name" not in kwargs and
                        "display_name" not in kwargs)
            list_kwargs['detailed'] = detailed

        if 'is_public' in list_argspec.args and 'is_public' in kwargs:
            is_public = kwargs['is_public']
            list_kwargs['is_public'] = is_public
            if is_public is None:
                tmp_kwargs = kwargs.copy()
                del tmp_kwargs['is_public']
                searches = tmp_kwargs.items()

        listing = self.list(**list_kwargs)

        for obj in listing:
            try:
                if all(getattr(obj, attr) == value
                        for (attr, value) in searches):
                    if detailed:
                        found.append(obj)
                    else:
                        found.append(self.get(obj.id))
            except AttributeError:
                continue

        return found


class BootingManagerWithFind(ManagerWithFind):
    """Like a `ManagerWithFind`, but has the ability to boot servers."""

    def _parse_block_device_mapping(self, block_device_mapping):
        bdm = []

        for device_name, mapping in six.iteritems(block_device_mapping):
            #
            # The mapping is in the format:
            # <id>:[<type>]:[<size(GB)>]:[<delete_on_terminate>]
            #
            bdm_dict = {'device_name': device_name}

            mapping_parts = mapping.split(':')
            source_id = mapping_parts[0]
            if len(mapping_parts) == 1:
                bdm_dict['volume_id'] = source_id

            elif len(mapping_parts) > 1:
                source_type = mapping_parts[1]
                if source_type.startswith('snap'):
                    bdm_dict['snapshot_id'] = source_id
                else:
                    bdm_dict['volume_id'] = source_id

            if len(mapping_parts) > 2 and mapping_parts[2]:
                bdm_dict['volume_size'] = str(int(mapping_parts[2]))

            if len(mapping_parts) > 3:
                bdm_dict['delete_on_termination'] = mapping_parts[3]

            bdm.append(bdm_dict)
        return bdm
