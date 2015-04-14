# Copyright (c) 2013 OpenStack Foundation
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

import os
import pkg_resources
import re
import sys
import uuid

import six
import prettytable

from cinderclient import exceptions
from cinderclient.openstack.common import strutils


def arg(*args, **kwargs):
    """Decorator for CLI args."""
    def _decorator(func):
        add_arg(func, *args, **kwargs)
        return func
    return _decorator


def env(*vars, **kwargs):
    """
    returns the first environment variable set
    if none are non-empty, defaults to '' or keyword arg default
    """
    for v in vars:
        value = os.environ.get(v, None)
        if value:
            return value
    return kwargs.get('default', '')


def add_arg(f, *args, **kwargs):
    """Bind CLI arguments to a shell.py `do_foo` function."""

    if not hasattr(f, 'arguments'):
        f.arguments = []

    # NOTE(sirp): avoid dups that can occur when the module is shared across
    # tests.
    if (args, kwargs) not in f.arguments:
        # Because of the semantics of decorator composition if we just append
        # to the options list positional options will appear to be backwards.
        f.arguments.insert(0, (args, kwargs))


def add_resource_manager_extra_kwargs_hook(f, hook):
    """Adds hook to bind CLI arguments to ResourceManager calls.

    The `do_foo` calls in shell.py will receive CLI args and then in turn pass
    them through to the ResourceManager. Before passing through the args, the
    hooks registered here will be called, giving us a chance to add extra
    kwargs (taken from the command-line) to what's passed to the
    ResourceManager.
    """
    if not hasattr(f, 'resource_manager_kwargs_hooks'):
        f.resource_manager_kwargs_hooks = []

    names = [h.__name__ for h in f.resource_manager_kwargs_hooks]
    if hook.__name__ not in names:
        f.resource_manager_kwargs_hooks.append(hook)


def get_resource_manager_extra_kwargs(f, args, allow_conflicts=False):
    """Return extra_kwargs by calling resource manager kwargs hooks."""
    hooks = getattr(f, "resource_manager_kwargs_hooks", [])
    extra_kwargs = {}
    for hook in hooks:
        hook_name = hook.__name__
        hook_kwargs = hook(args)

        conflicting_keys = set(hook_kwargs.keys()) & set(extra_kwargs.keys())
        if conflicting_keys and not allow_conflicts:
            msg = ("Hook '%(hook_name)s' is attempting to redefine attributes "
                   "'%(conflicting_keys)s'" % {
                       'hook_name': hook_name,
                       'conflicting_keys': conflicting_keys
                   })
            raise Exception(msg)

        extra_kwargs.update(hook_kwargs)

    return extra_kwargs


def unauthenticated(f):
    """
    Adds 'unauthenticated' attribute to decorated function.
    Usage:
        @unauthenticated
        def mymethod(f):
            ...
    """
    f.unauthenticated = True
    return f


def isunauthenticated(f):
    """
    Checks to see if the function is marked as not requiring authentication
    with the @unauthenticated decorator. Returns True if decorator is
    set to True, False otherwise.
    """
    return getattr(f, 'unauthenticated', False)


def service_type(stype):
    """
    Adds 'service_type' attribute to decorated function.
    Usage:
        @service_type('volume')
        def mymethod(f):
            ...
    """
    def inner(f):
        f.service_type = stype
        return f
    return inner


def get_service_type(f):
    """
    Retrieves service type from function
    """
    return getattr(f, 'service_type', None)


def pretty_choice_list(l):
    return ', '.join("'%s'" % i for i in l)


def _print(pt, order):
    if sys.version_info >= (3, 0):
        print(pt.get_string(sortby=order))
    else:
        print(strutils.safe_encode(pt.get_string(sortby=order)))


def print_list(objs, fields, formatters={}, order_by=None):
    mixed_case_fields = ['serverId']
    pt = prettytable.PrettyTable([f for f in fields], caching=False)
    pt.aligns = ['l' for f in fields]

    for o in objs:
        row = []
        for field in fields:
            if field in formatters:
                row.append(formatters[field](o))
            else:
                if field in mixed_case_fields:
                    field_name = field.replace(' ', '_')
                else:
                    field_name = field.lower().replace(' ', '_')
                if type(o) == dict and field in o:
                    data = o[field]
                else:
                    data = getattr(o, field_name, '')
                row.append(data)
        pt.add_row(row)

    if order_by is None:
        order_by = fields[0]
    _print(pt, order_by)


def print_dict(d, property="Property"):
    pt = prettytable.PrettyTable([property, 'Value'], caching=False)
    pt.aligns = ['l', 'l']
    [pt.add_row(list(r)) for r in six.iteritems(d)]
    _print(pt, property)


def find_resource(manager, name_or_id):
    """Helper for the _find_* methods."""
    # first try to get entity as integer id
    try:
        if isinstance(name_or_id, int) or name_or_id.isdigit():
            return manager.get(int(name_or_id))
    except exceptions.NotFound:
        pass

    if sys.version_info <= (3, 0):
        name_or_id = strutils.safe_decode(name_or_id)

    # now try to get entity as uuid
    try:
        uuid.UUID(name_or_id)
        return manager.get(name_or_id)
    except (ValueError, exceptions.NotFound):
        pass

    try:
        try:
            return manager.find(human_id=name_or_id)
        except exceptions.NotFound:
            pass

        # finally try to find entity by name
        try:
            return manager.find(name=name_or_id)
        except exceptions.NotFound:
            try:
                return manager.find(display_name=name_or_id)
            except (UnicodeDecodeError, exceptions.NotFound):
                try:
                    # Volumes does not have name, but display_name
                    return manager.find(display_name=name_or_id)
                except exceptions.NotFound:
                    msg = "No %s with a name or ID of '%s' exists." % \
                        (manager.resource_class.__name__.lower(), name_or_id)
                    raise exceptions.CommandError(msg)
    except exceptions.NoUniqueMatch:
        msg = ("Multiple %s matches found for '%s', use an ID to be more"
               " specific." % (manager.resource_class.__name__.lower(),
                               name_or_id))
        raise exceptions.CommandError(msg)


def find_volume(cs, volume):
    """Get a volume by name or ID."""
    return find_resource(cs.volumes, volume)


def _format_servers_list_networks(server):
    output = []
    for (network, addresses) in list(server.networks.items()):
        if len(addresses) == 0:
            continue
        addresses_csv = ', '.join(addresses)
        group = "%s=%s" % (network, addresses_csv)
        output.append(group)

    return '; '.join(output)


class HookableMixin(object):
    """Mixin so classes can register and run hooks."""
    _hooks_map = {}

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


def safe_issubclass(*args):
    """Like issubclass, but will just return False if not a class."""

    try:
        if issubclass(*args):
            return True
    except TypeError:
        pass

    return False


def import_class(import_str):
    """Returns a class from a string including module and class."""
    mod_str, _sep, class_str = import_str.rpartition('.')
    __import__(mod_str)
    return getattr(sys.modules[mod_str], class_str)


def _load_entry_point(ep_name, name=None):
    """Try to load the entry point ep_name that matches name."""
    for ep in pkg_resources.iter_entry_points(ep_name, name=name):
        try:
            return ep.load()
        except (ImportError, pkg_resources.UnknownExtra, AttributeError):
            continue

_slugify_strip_re = re.compile(r'[^\w\s-]')
_slugify_hyphenate_re = re.compile(r'[-\s]+')


# http://code.activestate.com/recipes/
#   577257-slugify-make-a-string-usable-in-a-url-or-filename/
def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.

    From Django's "django/template/defaultfilters.py".
    """
    import unicodedata
    if not isinstance(value, six.text_type):
        value = six.text_type(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = six.text_type(_slugify_strip_re.sub('', value).strip().lower())
    return _slugify_hyphenate_re.sub('-', value)
