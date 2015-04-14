# Copyright 2012 OpenStack Foundation
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

import errno
import hashlib
import json
import os
import re
import sys
import threading
import uuid

from oslo_utils import importutils
import six

if os.name == 'nt':
    import msvcrt
else:
    msvcrt = None

from oslo_utils import encodeutils
from oslo_utils import strutils
import prettytable

from glanceclient import exc

_memoized_property_lock = threading.Lock()

SENSITIVE_HEADERS = ('X-Auth-Token', )


# Decorator for cli-args
def arg(*args, **kwargs):
    def _decorator(func):
        # Because of the sematics of decorator composition if we just append
        # to the options list positional options will appear to be backwards.
        func.__dict__.setdefault('arguments', []).insert(0, (args, kwargs))
        return func
    return _decorator


def schema_args(schema_getter, omit=None):
    omit = omit or []
    typemap = {
        'string': str,
        'integer': int,
        'boolean': strutils.bool_from_string,
        'array': list
    }

    def _decorator(func):
        schema = schema_getter()
        if schema is None:
            param = '<unavailable>'
            kwargs = {
                'help': ("Please run with connection parameters set to "
                         "retrieve the schema for generating help for this "
                         "command")
            }
            func.__dict__.setdefault('arguments', []).insert(0, ((param, ),
                                                                 kwargs))
        else:
            properties = schema.get('properties', {})
            for name, property in six.iteritems(properties):
                if name in omit:
                    continue
                param = '--' + name.replace('_', '-')
                kwargs = {}

                type_str = property.get('type', 'string')

                if isinstance(type_str, list):
                    # NOTE(flaper87): This means the server has
                    # returned something like `['null', 'string']`,
                    # therfore we use the first non-`null` type as
                    # the valid type.
                    for t in type_str:
                        if t != 'null':
                            type_str = t
                            break

                if type_str == 'array':
                    items = property.get('items')
                    kwargs['type'] = typemap.get(items.get('type'))
                    kwargs['nargs'] = '+'
                else:
                    kwargs['type'] = typemap.get(type_str)

                if type_str == 'boolean':
                    kwargs['metavar'] = '[True|False]'
                else:
                    kwargs['metavar'] = '<%s>' % name.upper()

                description = property.get('description', "")
                if 'enum' in property:
                    if len(description):
                        description += " "

                    # NOTE(flaper87): Make sure all values are `str/unicode`
                    # for the `join` to succeed. Enum types can also be `None`
                    # therfore, join's call would fail without the following
                    # list comprehension
                    vals = [six.text_type(val) for val in property.get('enum')]
                    description += ('Valid values: ' + ', '.join(vals))
                kwargs['help'] = description

                func.__dict__.setdefault('arguments',
                                         []).insert(0, ((param, ), kwargs))
        return func

    return _decorator


def pretty_choice_list(l):
    return ', '.join("'%s'" % i for i in l)


def print_list(objs, fields, formatters=None, field_settings=None):
    formatters = formatters or {}
    field_settings = field_settings or {}
    pt = prettytable.PrettyTable([f for f in fields], caching=False)
    pt.align = 'l'

    for o in objs:
        row = []
        for field in fields:
            if field in field_settings:
                for setting, value in six.iteritems(field_settings[field]):
                    setting_dict = getattr(pt, setting)
                    setting_dict[field] = value

            if field in formatters:
                row.append(formatters[field](o))
            else:
                field_name = field.lower().replace(' ', '_')
                data = getattr(o, field_name, None) or ''
                row.append(data)
        pt.add_row(row)

    print(encodeutils.safe_decode(pt.get_string()))


def print_dict(d, max_column_width=80):
    pt = prettytable.PrettyTable(['Property', 'Value'], caching=False)
    pt.align = 'l'
    pt.max_width = max_column_width
    for k, v in six.iteritems(d):
        if isinstance(v, (dict, list)):
            v = json.dumps(v)
        pt.add_row([k, v])
    print(encodeutils.safe_decode(pt.get_string(sortby='Property')))


def find_resource(manager, name_or_id):
    """Helper for the _find_* methods."""
    # first try to get entity as integer id
    try:
        if isinstance(name_or_id, int) or name_or_id.isdigit():
            return manager.get(int(name_or_id))
    except exc.NotFound:
        pass

    # now try to get entity as uuid
    try:
        # This must be unicode for Python 3 compatibility.
        # If you pass a bytestring to uuid.UUID, you will get a TypeError
        uuid.UUID(encodeutils.safe_decode(name_or_id))
        return manager.get(name_or_id)
    except (ValueError, exc.NotFound):
        pass

    # finally try to find entity by name
    matches = list(manager.list(filters={'name': name_or_id}))
    num_matches = len(matches)
    if num_matches == 0:
        msg = "No %s with a name or ID of '%s' exists." % \
              (manager.resource_class.__name__.lower(), name_or_id)
        raise exc.CommandError(msg)
    elif num_matches > 1:
        msg = ("Multiple %s matches found for '%s', use an ID to be more"
               " specific." % (manager.resource_class.__name__.lower(),
                               name_or_id))
        raise exc.CommandError(msg)
    else:
        return matches[0]


def skip_authentication(f):
    """Function decorator used to indicate a caller may be unauthenticated."""
    f.require_authentication = False
    return f


def is_authentication_required(f):
    """Checks to see if the function requires authentication.

    Use the skip_authentication decorator to indicate a caller may
    skip the authentication step.
    """
    return getattr(f, 'require_authentication', True)


def env(*vars, **kwargs):
    """Search for the first defined of possibly many env vars

    Returns the first environment variable defined in vars, or
    returns the default defined in kwargs.
    """
    for v in vars:
        value = os.environ.get(v, None)
        if value:
            return value
    return kwargs.get('default', '')


def import_versioned_module(version, submodule=None):
    module = 'glanceclient.v%s' % version
    if submodule:
        module = '.'.join((module, submodule))
    return importutils.import_module(module)


def exit(msg='', exit_code=1):
    if msg:
        print(encodeutils.safe_decode(msg), file=sys.stderr)
    sys.exit(exit_code)


def save_image(data, path):
    """
    Save an image to the specified path.

    :param data: binary data of the image
    :param path: path to save the image to
    """
    if path is None:
        image = sys.stdout
    else:
        image = open(path, 'wb')
    try:
        for chunk in data:
            image.write(chunk)
    finally:
        if path is not None:
            image.close()


def make_size_human_readable(size):
    suffix = ['B', 'kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB']
    base = 1024.0

    index = 0
    while size >= base:
        index = index + 1
        size = size / base

    padded = '%.1f' % size
    stripped = padded.rstrip('0').rstrip('.')

    return '%s%s' % (stripped, suffix[index])


def getsockopt(self, *args, **kwargs):
    """
    A function which allows us to monkey patch eventlet's
    GreenSocket, adding a required 'getsockopt' method.
    TODO: (mclaren) we can remove this once the eventlet fix
    (https://bitbucket.org/eventlet/eventlet/commits/609f230)
    lands in mainstream packages.
    """
    return self.fd.getsockopt(*args, **kwargs)


def exception_to_str(exc):
    try:
        error = six.text_type(exc)
    except UnicodeError:
        try:
            error = str(exc)
        except UnicodeError:
            error = ("Caught '%(exception)s' exception." %
                     {"exception": exc.__class__.__name__})
    return encodeutils.safe_decode(error, errors='ignore')


def get_file_size(file_obj):
    """
    Analyze file-like object and attempt to determine its size.

    :param file_obj: file-like object.
    :retval The file's size or None if it cannot be determined.
    """
    if (hasattr(file_obj, 'seek') and hasattr(file_obj, 'tell') and
            (six.PY2 or six.PY3 and file_obj.seekable())):
        try:
            curr = file_obj.tell()
            file_obj.seek(0, os.SEEK_END)
            size = file_obj.tell()
            file_obj.seek(curr)
            return size
        except IOError as e:
            if e.errno == errno.ESPIPE:
                # Illegal seek. This means the file object
                # is a pipe (e.g. the user is trying
                # to pipe image data to the client,
                # echo testdata | bin/glance add blah...), or
                # that file object is empty, or that a file-like
                # object which doesn't support 'seek/tell' has
                # been supplied.
                return
            else:
                raise


def get_data_file(args):
    if args.file:
        return open(args.file, 'rb')
    else:
        # distinguish cases where:
        # (1) stdin is not valid (as in cron jobs):
        #     glance ... <&-
        # (2) image data is provided through standard input:
        #     glance ... < /tmp/file or cat /tmp/file | glance ...
        # (3) no image data provided:
        #     glance ...
        try:
            os.fstat(0)
        except OSError:
            # (1) stdin is not valid (closed...)
            return None
        if not sys.stdin.isatty():
            # (2) image data is provided through standard input
            if msvcrt:
                msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
            return sys.stdin
        else:
            # (3) no image data provided
            return None


def strip_version(endpoint):
    """Strip version from the last component of endpoint if present."""
    # NOTE(flaper87): This shouldn't be necessary if
    # we make endpoint the first argument. However, we
    # can't do that just yet because we need to keep
    # backwards compatibility.
    if not isinstance(endpoint, six.string_types):
        raise ValueError("Expected endpoint")

    version = None
    # Get rid of trailing '/' if present
    endpoint = endpoint.rstrip('/')
    url_bits = endpoint.split('/')
    # regex to match 'v1' or 'v2.0' etc
    if re.match('v\d+\.?\d*', url_bits[-1]):
        version = float(url_bits[-1].lstrip('v'))
        endpoint = '/'.join(url_bits[:-1])
    return endpoint, version


def print_image(image_obj, max_col_width=None):
    ignore = ['self', 'access', 'file', 'schema']
    image = dict([item for item in six.iteritems(image_obj)
                  if item[0] not in ignore])
    if str(max_col_width).isdigit():
        print_dict(image, max_column_width=max_col_width)
    else:
        print_dict(image)


def integrity_iter(iter, checksum):
    """
    Check image data integrity.

    :raises: IOError
    """
    md5sum = hashlib.md5()
    for chunk in iter:
        yield chunk
        if isinstance(chunk, six.string_types):
            chunk = six.b(chunk)
        md5sum.update(chunk)
    md5sum = md5sum.hexdigest()
    if md5sum != checksum:
        raise IOError(errno.EPIPE,
                      'Corrupt image download. Checksum was %s expected %s' %
                      (md5sum, checksum))


def memoized_property(fn):
    attr_name = '_lazy_once_' + fn.__name__

    @property
    def _memoized_property(self):
        if hasattr(self, attr_name):
            return getattr(self, attr_name)
        else:
            with _memoized_property_lock:
                if not hasattr(self, attr_name):
                    setattr(self, attr_name, fn(self))
            return getattr(self, attr_name)
    return _memoized_property


def safe_header(name, value):
    if name in SENSITIVE_HEADERS:
        v = value.encode('utf-8')
        h = hashlib.sha1(v)
        d = h.hexdigest()
        return name, "{SHA1}%s" % d
    else:
        return name, value


class IterableWithLength(object):
    def __init__(self, iterable, length):
        self.iterable = iterable
        self.length = length

    def __iter__(self):
        return self.iterable

    def next(self):
        return next(self.iterable)

    def __len__(self):
        return self.length
