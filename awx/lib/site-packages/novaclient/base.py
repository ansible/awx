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
import base64
import contextlib
import hashlib
import inspect
import os

import six

from novaclient import exceptions
from novaclient.openstack.common import strutils
from novaclient import utils


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

        with self.completion_cache('human_id', obj_class, mode="w"):
            with self.completion_cache('uuid', obj_class, mode="w"):
                return [obj_class(self, res, loaded=True)
                        for res in data if res]

    @contextlib.contextmanager
    def completion_cache(self, cache_type, obj_class, mode):
        """
        The completion cache store items that can be used for bash
        autocompletion, like UUIDs or human-friendly IDs.

        A resource listing will clear and repopulate the cache.

        A resource create will append to the cache.

        Delete is not handled because listings are assumed to be performed
        often enough to keep the cache reasonably up-to-date.
        """
        base_dir = utils.env('NOVACLIENT_UUID_CACHE_DIR',
                             default="~/.novaclient")

        # NOTE(sirp): Keep separate UUID caches for each username + endpoint
        # pair
        username = utils.env('OS_USERNAME', 'NOVA_USERNAME')
        url = utils.env('OS_URL', 'NOVA_URL')
        uniqifier = hashlib.md5(username.encode('utf-8') +
                                url.encode('utf-8')).hexdigest()

        cache_dir = os.path.expanduser(os.path.join(base_dir, uniqifier))

        try:
            os.makedirs(cache_dir, 0o755)
        except OSError:
            # NOTE(kiall): This is typicaly either permission denied while
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
            # NOTE(kiall): This is typicaly a permission denied while
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

    def _get(self, url, response_key):
        _resp, body = self.api.client.get(url)
        return self.resource_class(self, body[response_key], loaded=True)

    def _create(self, url, body, response_key, return_raw=False, **kwargs):
        self.run_hooks('modify_body_for_create', body, **kwargs)
        _resp, body = self.api.client.post(url, body=body)
        if return_raw:
            return body[response_key]

        with self.completion_cache('human_id', self.resource_class, mode="a"):
            with self.completion_cache('uuid', self.resource_class, mode="a"):
                return self.resource_class(self, body[response_key])

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


class ManagerWithFind(Manager):
    """
    Like a `Manager`, but with additional `find()`/`findall()` methods.
    """

    __metaclass__ = abc.ABCMeta

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

    def _boot(self, resource_url, response_key, name, image, flavor,
              meta=None, files=None, userdata=None,
              reservation_id=None, return_raw=False, min_count=None,
              max_count=None, security_groups=None, key_name=None,
              availability_zone=None, block_device_mapping=None,
              block_device_mapping_v2=None, nics=None, scheduler_hints=None,
              config_drive=None, admin_pass=None, disk_config=None, **kwargs):
        """
        Create (boot) a new server.

        :param name: Something to name the server.
        :param image: The :class:`Image` to boot with.
        :param flavor: The :class:`Flavor` to boot onto.
        :param meta: A dict of arbitrary key/value metadata to store for this
                     server. A maximum of five entries is allowed, and both
                     keys and values must be 255 characters or less.
        :param files: A dict of files to overrwrite on the server upon boot.
                      Keys are file names (i.e. ``/etc/passwd``) and values
                      are the file contents (either as a string or as a
                      file-like object). A maximum of five entries is allowed,
                      and each file must be 10k or less.
        :param reservation_id: a UUID for the set of servers being requested.
        :param return_raw: If True, don't try to coearse the result into
                           a Resource object.
        :param security_groups: list of security group names
        :param key_name: (optional extension) name of keypair to inject into
                         the instance
        :param availability_zone: Name of the availability zone for instance
                                  placement.
        :param block_device_mapping: A dict of block device mappings for this
                                     server.
        :param block_device_mapping_v2: A dict of block device mappings V2 for
                                        this server.
        :param nics:  (optional extension) an ordered list of nics to be
                      added to this server, with information about
                      connected networks, fixed ips, etc.
        :param scheduler_hints: (optional extension) arbitrary key-value pairs
                              specified by the client to help boot an instance.
        :param config_drive: (optional extension) value for config drive
                            either boolean, or volume-id
        :param admin_pass: admin password for the server.
        :param disk_config: (optional extension) control how the disk is
                            partitioned when the server is created.
        """
        body = {"server": {
            "name": name,
            "imageRef": str(getid(image)) if image else '',
            "flavorRef": str(getid(flavor)),
        }}
        if userdata:
            if hasattr(userdata, 'read'):
                userdata = userdata.read()

            userdata = strutils.safe_encode(userdata)
            body["server"]["user_data"] = base64.b64encode(userdata)
        if meta:
            body["server"]["metadata"] = meta
        if reservation_id:
            body["server"]["reservation_id"] = reservation_id
        if key_name:
            body["server"]["key_name"] = key_name
        if scheduler_hints:
            body['os:scheduler_hints'] = scheduler_hints
        if config_drive:
            body["server"]["config_drive"] = config_drive
        if admin_pass:
            body["server"]["adminPass"] = admin_pass
        if not min_count:
            min_count = 1
        if not max_count:
            max_count = min_count
        body["server"]["min_count"] = min_count
        body["server"]["max_count"] = max_count

        if security_groups:
            body["server"]["security_groups"] =\
             [{'name': sg} for sg in security_groups]

        # Files are a slight bit tricky. They're passed in a "personality"
        # list to the POST. Each item is a dict giving a file name and the
        # base64-encoded contents of the file. We want to allow passing
        # either an open file *or* some contents as files here.
        if files:
            personality = body['server']['personality'] = []
            for filepath, file_or_string in files.items():
                if hasattr(file_or_string, 'read'):
                    data = file_or_string.read()
                else:
                    data = file_or_string
                personality.append({
                    'path': filepath,
                    'contents': data.encode('base64'),
                })

        if availability_zone:
            body["server"]["availability_zone"] = availability_zone

        # Block device mappings are passed as a list of dictionaries
        if block_device_mapping:
            body['server']['block_device_mapping'] = \
                    self._parse_block_device_mapping(block_device_mapping)
        elif block_device_mapping_v2:
            # Append the image to the list only if we have new style BDMs
            if image:
                bdm_dict = {'uuid': image.id, 'source_type': 'image',
                            'destination_type': 'local', 'boot_index': 0,
                            'delete_on_termination': True}
                block_device_mapping_v2.insert(0, bdm_dict)

            body['server']['block_device_mapping_v2'] = block_device_mapping_v2

        if nics is not None:
            # NOTE(tr3buchet): nics can be an empty list
            all_net_data = []
            for nic_info in nics:
                net_data = {}
                # if value is empty string, do not send value in body
                if nic_info.get('net-id'):
                    net_data['uuid'] = nic_info['net-id']
                if nic_info.get('v4-fixed-ip'):
                    net_data['fixed_ip'] = nic_info['v4-fixed-ip']
                if nic_info.get('port-id'):
                    net_data['port'] = nic_info['port-id']
                all_net_data.append(net_data)
            body['server']['networks'] = all_net_data

        if disk_config is not None:
            body['server']['OS-DCF:diskConfig'] = disk_config

        return self._create(resource_url, body, response_key,
                            return_raw=return_raw, **kwargs)


class Resource(object):
    """
    A resource represents a particular instance of an object (server, flavor,
    etc). This is pretty much just a bag for attributes.

    :param manager: Manager object
    :param info: dictionary representing resource attributes
    :param loaded: prevent lazy-loading if set to True
    """
    HUMAN_ID = False
    NAME_ATTR = 'name'

    def __init__(self, manager, info, loaded=False):
        self.manager = manager
        self._info = info
        self._add_details(info)
        self._loaded = loaded

        # NOTE(sirp): ensure `id` is already present because if it isn't we'll
        # enter an infinite loop of __getattr__ -> get -> __init__ ->
        # __getattr__ -> ...
        if 'id' in self.__dict__ and len(str(self.id)) == 36:
            self.manager.write_to_completion_cache('uuid', self.id)

        human_id = self.human_id
        if human_id:
            self.manager.write_to_completion_cache('human_id', human_id)

    @property
    def human_id(self):
        """Subclasses may override this provide a pretty ID which can be used
        for bash completion.
        """
        if self.NAME_ATTR in self.__dict__ and self.HUMAN_ID:
            return utils.slugify(getattr(self, self.NAME_ATTR))
        return None

    def _add_details(self, info):
        for (k, v) in six.iteritems(info):
            try:
                setattr(self, k, v)
                self._info[k] = v
            except AttributeError:
                # In this case we already defined the attribute on the class
                pass

    def __getattr__(self, k):
        if k not in self.__dict__:
            #NOTE(bcwaldon): disallow lazy-loading if already loaded once
            if not self.is_loaded():
                self.get()
                return self.__getattr__(k)

            raise AttributeError(k)
        else:
            return self.__dict__[k]

    def __repr__(self):
        reprkeys = sorted(k for k in self.__dict__.keys() if k[0] != '_' and
                                                                k != 'manager')
        info = ", ".join("%s=%s" % (k, getattr(self, k)) for k in reprkeys)
        return "<%s %s>" % (self.__class__.__name__, info)

    def get(self):
        # set_loaded() first ... so if we have to bail, we know we tried.
        self.set_loaded(True)
        if not hasattr(self.manager, 'get'):
            return

        new = self.manager.get(self.id)
        if new:
            self._add_details(new._info)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        if hasattr(self, 'id') and hasattr(other, 'id'):
            return self.id == other.id
        return self._info == other._info

    def is_loaded(self):
        return self._loaded

    def set_loaded(self, val):
        self._loaded = val
