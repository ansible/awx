# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Libcloud Python 2.x and 3.x compatibility layer
# Some methods below are taken from Django PYK3 port which is licensed under 3
# clause BSD license
# https://bitbucket.org/loewis/django-3k

from __future__ import absolute_import

import sys
import types

try:
    from lxml import etree as ET
except ImportError:
    from xml.etree import ElementTree as ET

PY2 = False
PY25 = False
PY27 = False
PY3 = False
PY32 = False

if sys.version_info >= (2, 0) and sys.version_info < (3, 0):
    PY2 = True

if sys.version_info >= (2, 5) and sys.version_info <= (2, 6):
    PY25 = True

if sys.version_info >= (2, 7) and sys.version_info <= (2, 8):
    PY27 = True

if sys.version_info >= (3, 0):
    PY3 = True

if sys.version_info >= (3, 2) and sys.version_info < (3, 3):
    PY32 = True

if PY3:
    import http.client as httplib
    from io import StringIO
    import urllib
    import urllib as urllib2
    import urllib.parse as urlparse
    import xmlrpc.client as xmlrpclib

    from urllib.parse import quote as urlquote
    from urllib.parse import unquote as urlunquote
    from urllib.parse import urlencode as urlencode
    from os.path import relpath

    from imp import reload

    from builtins import bytes
    from builtins import next

    parse_qs = urlparse.parse_qs
    parse_qsl = urlparse.parse_qsl

    basestring = str

    def method_type(callable, instance, klass):
        return types.MethodType(callable, instance or klass())

    def b(s):
        if isinstance(s, str):
            return s.encode('utf-8')
        elif isinstance(s, bytes):
            return s
        else:
            raise TypeError("Invalid argument %r for b()" % (s,))

    def ensure_string(s):
        if isinstance(s, str):
            return s
        elif isinstance(s, bytes):
            return s.decode('utf-8')
        else:
            raise TypeError("Invalid argument %r for ensure_string()" % (s,))

    def byte(n):
        # assume n is a Latin-1 string of length 1
        return ord(n)
    u = str

    def bchr(s):
        """Take an integer and make a 1-character byte string."""
        return bytes([s])

    def dictvalues(d):
        return list(d.values())

    def tostring(node):
        return ET.tostring(node, encoding='unicode')

    def hexadigits(s):
        # s needs to be a byte string.
        return [format(x, "x") for x in s]

else:
    import httplib  # NOQA
    from StringIO import StringIO  # NOQA
    import urllib  # NOQA
    import urllib2  # NOQA
    import urlparse  # NOQA
    import xmlrpclib  # NOQA
    from urllib import quote as _urlquote  # NOQA
    from urllib import unquote as urlunquote  # NOQA
    from urllib import urlencode as urlencode  # NOQA

    from __builtin__ import reload  # NOQA

    if PY25:
        import cgi

        parse_qs = cgi.parse_qs
        parse_qsl = cgi.parse_qsl
    else:
        parse_qs = urlparse.parse_qs
        parse_qsl = urlparse.parse_qsl

    if not PY25:
        from os.path import relpath  # NOQA

    # Save the real value of unicode because urlquote needs it to tell the
    # difference between a unicode string and a byte string.
    _real_unicode = unicode
    basestring = unicode = str

    method_type = types.MethodType

    b = bytes = ensure_string = str

    def byte(n):
        return n

    u = unicode

    def bchr(s):
        """Take an integer and make a 1-character byte string."""
        return chr(s)

    def next(i):
        return i.next()

    def dictvalues(d):
        return d.values()

    tostring = ET.tostring

    def urlquote(s, safe='/'):
        if isinstance(s, _real_unicode):
            # Pretend to be py3 by encoding the URI automatically.
            s = s.encode('utf8')
        return _urlquote(s, safe)

    def hexadigits(s):
        # s needs to be a string.
        return [x.encode("hex") for x in s]

if PY25:
    import posixpath

    # Taken from http://jimmyg.org/work/code/barenecessities/index.html
    # (MIT license)
    def relpath(path, start=posixpath.curdir):   # NOQA
        """Return a relative version of a path"""
        if not path:
            raise ValueError("no path specified")
        start_list = posixpath.abspath(start).split(posixpath.sep)
        path_list = posixpath.abspath(path).split(posixpath.sep)
        # Work out how much of the filepath is shared by start and path.
        i = len(posixpath.commonprefix([start_list, path_list]))
        rel_list = [posixpath.pardir] * (len(start_list) - i) + path_list[i:]
        if not rel_list:
            return posixpath.curdir
        return posixpath.join(*rel_list)

if PY27 or PY3:
    unittest2_required = False
else:
    unittest2_required = True
