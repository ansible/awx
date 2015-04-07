#    Copyright (C) 2015 Yahoo! Inc. All Rights Reserved.
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

import datetime
import itertools
import sys
import uuid

import msgpack
from oslo_utils import importutils
from pytz import timezone
import six
import six.moves.xmlrpc_client as xmlrpclib

netaddr = importutils.try_import("netaddr")

# NOTE(harlowja): itertools.count only started to take a step value
# in python 2.7+ so we can't use it in 2.6...
if sys.version_info[0:2] == (2, 6):
    _PY26 = True
else:
    _PY26 = False


def _serialize_datetime(dt):
    dct = {
        'day': dt.day,
        'month': dt.month,
        'year': dt.year,
        'hour': dt.hour,
        'minute': dt.minute,
        'second': dt.second,
        'microsecond': dt.microsecond,
    }
    if dt.tzinfo:
        dct['tz'] = dt.tzinfo.tzname(None)
    return dumps(dct)


def _deserialize_datetime(blob):
    dct = loads(blob)
    dt = datetime.datetime(day=dct['day'],
                           month=dct['month'],
                           year=dct['year'],
                           hour=dct['hour'],
                           minute=dct['minute'],
                           second=dct['second'],
                           microsecond=dct['microsecond'])
    if 'tz' in dct:
        tzinfo = timezone(dct['tz'])
        dt = tzinfo.localize(dt)
    return dt


def _serialize_date(d):
    dct = {
        'year': d.year,
        'month': d.month,
        'day': d.day,
    }
    return dumps(dct)


def _deserialize_date(blob):
    dct = loads(blob)
    return datetime.date(year=dct['year'],
                         month=dct['month'],
                         day=dct['day'])


def _serializer(obj):
    # Applications can assign 0 to 127 to store
    # application-specific type information...
    if isinstance(obj, uuid.UUID):
        return msgpack.ExtType(0, six.text_type(obj.hex).encode('ascii'))
    if isinstance(obj, datetime.datetime):
        return msgpack.ExtType(1, _serialize_datetime(obj))
    if type(obj) == itertools.count:
        # FIXME(harlowja): figure out a better way to avoid hacking into
        # the string representation of count to get at the right numbers...
        obj = six.text_type(obj)
        start = obj.find("(") + 1
        end = obj.rfind(")")
        pieces = obj[start:end].split(",")
        if len(pieces) == 1:
            start = int(pieces[0])
            step = 1
        else:
            start = int(pieces[0])
            step = int(pieces[1])
        return msgpack.ExtType(2, msgpack.packb([start, step]))
    if netaddr and isinstance(obj, netaddr.IPAddress):
        return msgpack.ExtType(3, msgpack.packb(obj.value))
    if isinstance(obj, (set, frozenset)):
        value = dumps(list(obj))
        if isinstance(obj, set):
            ident = 4
        else:
            ident = 5
        return msgpack.ExtType(ident, value)
    if isinstance(obj, xmlrpclib.DateTime):
        dt = datetime.datetime(*tuple(obj.timetuple())[:6])
        return msgpack.ExtType(6, _serialize_datetime(dt))
    if isinstance(obj, datetime.date):
        return msgpack.ExtType(7, _serialize_date(obj))
    raise TypeError("Unknown type: %r" % (obj,))


def _unserializer(code, data):
    if code == 0:
        return uuid.UUID(hex=six.text_type(data, encoding='ascii'))
    if code == 1:
        return _deserialize_datetime(data)
    if code == 2:
        value = msgpack.unpackb(data)
        if not _PY26:
            return itertools.count(value[0], value[1])
        else:
            return itertools.count(value[0])
    if netaddr and code == 3:
        value = msgpack.unpackb(data)
        return netaddr.IPAddress(value)
    if code in (4, 5):
        value = loads(data)
        if code == 4:
            return set(value)
        else:
            return frozenset(value)
    if code == 6:
        dt = _deserialize_datetime(data)
        return xmlrpclib.DateTime(dt.timetuple())
    if code == 7:
        return _deserialize_date(data)
    return msgpack.ExtType(code, data)


def load(fp):
    """Deserialize ``fp`` into a Python object."""
    # NOTE(harlowja): the reason we can't use the more native msgpack functions
    # here is that the unpack() function (oddly) doesn't seem to take a
    # 'ext_hook' parameter..
    return msgpack.Unpacker(fp, ext_hook=_unserializer,
                            encoding='utf-8').unpack()


def dump(obj, fp):
    """Serialize ``obj`` as a messagepack formatted stream to ``fp``."""
    return msgpack.pack(obj, fp, default=_serializer, use_bin_type=True)


def dumps(obj):
    """Serialize ``obj`` to a messagepack formatted ``str``."""
    return msgpack.packb(obj, default=_serializer, use_bin_type=True)


def loads(s):
    """Deserialize ``s`` messagepack ``str`` into a Python object."""
    return msgpack.unpackb(s, ext_hook=_unserializer, encoding='utf-8')
