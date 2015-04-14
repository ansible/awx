# Copyright 2013 OpenStack Foundation
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
A fake server that "responds" to API methods with pre-canned responses.

All of these responses come from the spec, so if for some reason the spec's
wrong the tests might raise AssertionError. I've indicated in comments the
places where actual behavior differs from the spec.
"""

# W0102: Dangerous default value %s as argument
# pylint: disable=W0102

import json

import requests
import six
from six.moves.urllib import parse

from keystoneclient.openstack.common.apiclient import client


def assert_has_keys(dct, required=None, optional=None):
    required = required or []
    optional = optional or []
    for k in required:
        try:
            assert k in dct
        except AssertionError:
            extra_keys = set(dct.keys()).difference(set(required + optional))
            raise AssertionError("found unexpected keys: %s" %
                                 list(extra_keys))


class TestResponse(requests.Response):
    """Wrap requests.Response and provide a convenient initialization.
    """

    def __init__(self, data):
        super(TestResponse, self).__init__()
        self._content_consumed = True
        if isinstance(data, dict):
            self.status_code = data.get('status_code', 200)
            # Fake the text attribute to streamline Response creation
            text = data.get('text', "")
            if isinstance(text, (dict, list)):
                self._content = json.dumps(text)
                default_headers = {
                    "Content-Type": "application/json",
                }
            else:
                self._content = text
                default_headers = {}
            if six.PY3 and isinstance(self._content, six.string_types):
                self._content = self._content.encode('utf-8', 'strict')
            self.headers = data.get('headers') or default_headers
        else:
            self.status_code = data

    def __eq__(self, other):
        return (self.status_code == other.status_code and
                self.headers == other.headers and
                self._content == other._content)


class FakeHTTPClient(client.HTTPClient):

    def __init__(self, *args, **kwargs):
        self.callstack = []
        self.fixtures = kwargs.pop("fixtures", None) or {}
        if not args and "auth_plugin" not in kwargs:
            args = (None, )
        super(FakeHTTPClient, self).__init__(*args, **kwargs)

    def assert_called(self, method, url, body=None, pos=-1):
        """Assert than an API method was just called.
        """
        expected = (method, url)
        called = self.callstack[pos][0:2]
        assert self.callstack, \
            "Expected %s %s but no calls were made." % expected

        assert expected == called, 'Expected %s %s; got %s %s' % \
            (expected + called)

        if body is not None:
            if self.callstack[pos][3] != body:
                raise AssertionError('%r != %r' %
                                     (self.callstack[pos][3], body))

    def assert_called_anytime(self, method, url, body=None):
        """Assert than an API method was called anytime in the test.
        """
        expected = (method, url)

        assert self.callstack, \
            "Expected %s %s but no calls were made." % expected

        found = False
        entry = None
        for entry in self.callstack:
            if expected == entry[0:2]:
                found = True
                break

        assert found, 'Expected %s %s; got %s' % \
            (method, url, self.callstack)
        if body is not None:
            assert entry[3] == body, "%s != %s" % (entry[3], body)

        self.callstack = []

    def clear_callstack(self):
        self.callstack = []

    def authenticate(self):
        pass

    def client_request(self, client, method, url, **kwargs):
        # Check that certain things are called correctly
        if method in ["GET", "DELETE"]:
            assert "json" not in kwargs

        # Note the call
        self.callstack.append(
            (method,
             url,
             kwargs.get("headers") or {},
             kwargs.get("json") or kwargs.get("data")))
        try:
            fixture = self.fixtures[url][method]
        except KeyError:
            pass
        else:
            return TestResponse({"headers": fixture[0],
                                 "text": fixture[1]})

        # Call the method
        args = parse.parse_qsl(parse.urlparse(url)[4])
        kwargs.update(args)
        munged_url = url.rsplit('?', 1)[0]
        munged_url = munged_url.strip('/').replace('/', '_').replace('.', '_')
        munged_url = munged_url.replace('-', '_')

        callback = "%s_%s" % (method.lower(), munged_url)

        if not hasattr(self, callback):
            raise AssertionError('Called unknown API method: %s %s, '
                                 'expected fakes method name: %s' %
                                 (method, url, callback))

        resp = getattr(self, callback)(**kwargs)
        if len(resp) == 3:
            status, headers, body = resp
        else:
            status, body = resp
            headers = {}
        self.last_request_id = headers.get('x-openstack-request-id',
                                           'req-test')
        return TestResponse({
            "status_code": status,
            "text": body,
            "headers": headers,
        })
