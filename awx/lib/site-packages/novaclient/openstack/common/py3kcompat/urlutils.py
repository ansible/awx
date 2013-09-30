# vim: tabstop=4 shiftwidth=4 softtabstop=4
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
    import urllib.parse

    urlencode = urllib.parse.urlencode
    urljoin = urllib.parse.urljoin
    quote = urllib.parse.quote
    parse_qsl = urllib.parse.parse_qsl
    urlparse = urllib.parse.urlparse
    urlsplit = urllib.parse.urlsplit
    urlunsplit = urllib.parse.urlunsplit
else:
    # python2
    import urllib
    import urlparse

    urlencode = urllib.urlencode
    quote = urllib.quote

    parse = urlparse
    parse_qsl = parse.parse_qsl
    urljoin = parse.urljoin
    urlparse = parse.urlparse
    urlsplit = parse.urlsplit
    urlunsplit = parse.urlunsplit
