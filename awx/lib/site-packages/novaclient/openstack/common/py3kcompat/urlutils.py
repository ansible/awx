#
# Copyright 2013 Canonical Ltd.
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
#

"""
Python2/Python3 compatibility layer for OpenStack
"""

import six

if six.PY3:
    # python3
    import urllib.error
    import urllib.parse
    import urllib.request

    urlencode = urllib.parse.urlencode
    urljoin = urllib.parse.urljoin
    quote = urllib.parse.quote
    quote_plus = urllib.parse.quote_plus
    parse_qsl = urllib.parse.parse_qsl
    unquote = urllib.parse.unquote
    unquote_plus = urllib.parse.unquote_plus
    urlparse = urllib.parse.urlparse
    urlsplit = urllib.parse.urlsplit
    urlunsplit = urllib.parse.urlunsplit
    SplitResult = urllib.parse.SplitResult

    urlopen = urllib.request.urlopen
    URLError = urllib.error.URLError
    pathname2url = urllib.request.pathname2url
else:
    # python2
    import urllib
    import urllib2
    import urlparse

    urlencode = urllib.urlencode
    quote = urllib.quote
    quote_plus = urllib.quote_plus
    unquote = urllib.unquote
    unquote_plus = urllib.unquote_plus

    parse = urlparse
    parse_qsl = parse.parse_qsl
    urljoin = parse.urljoin
    urlparse = parse.urlparse
    urlsplit = parse.urlsplit
    urlunsplit = parse.urlunsplit
    SplitResult = parse.SplitResult

    urlopen = urllib2.urlopen
    URLError = urllib2.URLError
    pathname2url = urllib.pathname2url
