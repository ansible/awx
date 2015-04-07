# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os

import fixtures
import requests
from requests_mock.contrib import fixture as requests_mock_fixture
import six
import testtools


class TestCase(testtools.TestCase):
    TEST_REQUEST_BASE = {
        'verify': True,
    }

    def setUp(self):
        super(TestCase, self).setUp()
        if (os.environ.get('OS_STDOUT_CAPTURE') == 'True' or
                os.environ.get('OS_STDOUT_CAPTURE') == '1'):
            stdout = self.useFixture(fixtures.StringStream('stdout')).stream
            self.useFixture(fixtures.MonkeyPatch('sys.stdout', stdout))
        if (os.environ.get('OS_STDERR_CAPTURE') == 'True' or
                os.environ.get('OS_STDERR_CAPTURE') == '1'):
            stderr = self.useFixture(fixtures.StringStream('stderr')).stream
            self.useFixture(fixtures.MonkeyPatch('sys.stderr', stderr))


class FixturedTestCase(TestCase):

    client_fixture_class = None
    data_fixture_class = None

    def setUp(self):
        super(FixturedTestCase, self).setUp()

        self.requests = self.useFixture(requests_mock_fixture.Fixture())
        self.data_fixture = None
        self.client_fixture = None
        self.cs = None

        if self.client_fixture_class:
            fix = self.client_fixture_class(self.requests)
            self.client_fixture = self.useFixture(fix)
            self.cs = self.client_fixture.new_client()

        if self.data_fixture_class:
            fix = self.data_fixture_class(self.requests)
            self.data_fixture = self.useFixture(fix)

    def assert_called(self, method, path, body=None):
        self.assertEqual(self.requests.last_request.method, method)
        self.assertEqual(self.requests.last_request.path_url, path)

        if body:
            req_data = self.requests.last_request.body
            if isinstance(req_data, six.binary_type):
                req_data = req_data.decode('utf-8')
            if not isinstance(body, six.string_types):
                # json load if the input body to match against is not a string
                req_data = json.loads(req_data)
            self.assertEqual(req_data, body)


class TestResponse(requests.Response):
    """Class used to wrap requests.Response and provide some
       convenience to initialize with a dict.
    """

    def __init__(self, data):
        self._text = None
        super(TestResponse, self)
        if isinstance(data, dict):
            self.status_code = data.get('status_code', None)
            self.headers = data.get('headers', None)
            self.reason = data.get('reason', '')
            # Fake the text attribute to streamline Response creation
            self._text = data.get('text', None)
        else:
            self.status_code = data

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    @property
    def text(self):
        return self._text
