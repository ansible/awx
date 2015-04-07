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

import logging
import sys
import time
import uuid

import fixtures
import mock
from mox3 import mox
from oslo_serialization import jsonutils
import requests
from requests_mock.contrib import fixture
import six
from six.moves.urllib import parse as urlparse
import testtools


class TestCase(testtools.TestCase):

    TEST_DOMAIN_ID = '1'
    TEST_DOMAIN_NAME = 'aDomain'
    TEST_GROUP_ID = uuid.uuid4().hex
    TEST_ROLE_ID = uuid.uuid4().hex
    TEST_TENANT_ID = '1'
    TEST_TENANT_NAME = 'aTenant'
    TEST_TOKEN = 'aToken'
    TEST_TRUST_ID = 'aTrust'
    TEST_USER = 'test'
    TEST_USER_ID = uuid.uuid4().hex

    TEST_ROOT_URL = 'http://127.0.0.1:5000/'

    def setUp(self):
        super(TestCase, self).setUp()
        self.mox = mox.Mox()
        self.logger = self.useFixture(fixtures.FakeLogger(level=logging.DEBUG))
        self.time_patcher = mock.patch.object(time, 'time', lambda: 1234)
        self.time_patcher.start()

        self.requests_mock = self.useFixture(fixture.Fixture())

    def tearDown(self):
        self.time_patcher.stop()
        self.mox.UnsetStubs()
        self.mox.VerifyAll()
        super(TestCase, self).tearDown()

    def stub_url(self, method, parts=None, base_url=None, json=None, **kwargs):
        if not base_url:
            base_url = self.TEST_URL

        if json:
            kwargs['text'] = jsonutils.dumps(json)
            headers = kwargs.setdefault('headers', {})
            headers['Content-Type'] = 'application/json'

        if parts:
            url = '/'.join([p.strip('/') for p in [base_url] + parts])
        else:
            url = base_url

        url = url.replace("/?", "?")
        self.requests_mock.register_uri(method, url, **kwargs)

    def assertRequestBodyIs(self, body=None, json=None):
        last_request_body = self.requests_mock.last_request.body
        if json:
            val = jsonutils.loads(last_request_body)
            self.assertEqual(json, val)
        elif body:
            self.assertEqual(body, last_request_body)

    def assertQueryStringIs(self, qs=''):
        """Verify the QueryString matches what is expected.

        The qs parameter should be of the format \'foo=bar&abc=xyz\'
        """
        expected = urlparse.parse_qs(qs, keep_blank_values=True)
        parts = urlparse.urlparse(self.requests_mock.last_request.url)
        querystring = urlparse.parse_qs(parts.query, keep_blank_values=True)
        self.assertEqual(expected, querystring)

    def assertQueryStringContains(self, **kwargs):
        """Verify the query string contains the expected parameters.

        This method is used to verify that the query string for the most recent
        request made contains all the parameters provided as ``kwargs``, and
        that the value of each parameter contains the value for the kwarg. If
        the value for the kwarg is an empty string (''), then all that's
        verified is that the parameter is present.

        """
        parts = urlparse.urlparse(self.requests_mock.last_request.url)
        qs = urlparse.parse_qs(parts.query, keep_blank_values=True)

        for k, v in six.iteritems(kwargs):
            self.assertIn(k, qs)
            self.assertIn(v, qs[k])

    def assertRequestHeaderEqual(self, name, val):
        """Verify that the last request made contains a header and its value

        The request must have already been made.
        """
        headers = self.requests_mock.last_request.headers
        self.assertEqual(headers.get(name), val)


if tuple(sys.version_info)[0:2] < (2, 7):

    def assertDictEqual(self, d1, d2, msg=None):
        # Simple version taken from 2.7
        self.assertIsInstance(d1, dict,
                              'First argument is not a dictionary')
        self.assertIsInstance(d2, dict,
                              'Second argument is not a dictionary')
        if d1 != d2:
            if msg:
                self.fail(msg)
            else:
                standardMsg = '%r != %r' % (d1, d2)
                self.fail(standardMsg)

    TestCase.assertDictEqual = assertDictEqual


class TestResponse(requests.Response):
    """Class used to wrap requests.Response and provide some
       convenience to initialize with a dict.
    """

    def __init__(self, data):
        self._text = None
        super(TestResponse, self).__init__()
        if isinstance(data, dict):
            self.status_code = data.get('status_code', 200)
            headers = data.get('headers')
            if headers:
                self.headers.update(headers)
            # Fake the text attribute to streamline Response creation
            # _content is defined by requests.Response
            self._content = data.get('text')
        else:
            self.status_code = data

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    @property
    def text(self):
        return self.content


class DisableModuleFixture(fixtures.Fixture):
    """A fixture to provide support for unloading/disabling modules."""

    def __init__(self, module, *args, **kw):
        super(DisableModuleFixture, self).__init__(*args, **kw)
        self.module = module
        self._finders = []
        self._cleared_modules = {}

    def tearDown(self):
        super(DisableModuleFixture, self).tearDown()
        for finder in self._finders:
            sys.meta_path.remove(finder)
        sys.modules.update(self._cleared_modules)

    def clear_module(self):
        cleared_modules = {}
        for fullname in sys.modules.keys():
            if (fullname == self.module or
                    fullname.startswith(self.module + '.')):
                cleared_modules[fullname] = sys.modules.pop(fullname)
        return cleared_modules

    def setUp(self):
        """Ensure ImportError for the specified module."""

        super(DisableModuleFixture, self).setUp()

        # Clear 'module' references in sys.modules
        self._cleared_modules.update(self.clear_module())

        finder = NoModuleFinder(self.module)
        self._finders.append(finder)
        sys.meta_path.insert(0, finder)


class NoModuleFinder(object):
    """Disallow further imports of 'module'."""

    def __init__(self, module):
        self.module = module

    def find_module(self, fullname, path):
        if fullname == self.module or fullname.startswith(self.module + '.'):
            raise ImportError
