# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from testtools import matchers

from keystoneclient.auth import token_endpoint
from keystoneclient import session
from keystoneclient.tests.unit import utils


class TokenEndpointTest(utils.TestCase):

    TEST_TOKEN = 'aToken'
    TEST_URL = 'http://server/prefix'

    def test_basic_case(self):
        self.requests_mock.get(self.TEST_URL, text='body')

        a = token_endpoint.Token(self.TEST_URL, self.TEST_TOKEN)
        s = session.Session(auth=a)

        data = s.get(self.TEST_URL, authenticated=True)

        self.assertEqual(data.text, 'body')
        self.assertRequestHeaderEqual('X-Auth-Token', self.TEST_TOKEN)

    def test_basic_endpoint_case(self):
        self.stub_url('GET', ['p'], text='body')
        a = token_endpoint.Token(self.TEST_URL, self.TEST_TOKEN)
        s = session.Session(auth=a)

        data = s.get('/p',
                     authenticated=True,
                     endpoint_filter={'service': 'identity'})

        self.assertEqual(self.TEST_URL, a.get_endpoint(s))
        self.assertEqual('body', data.text)
        self.assertRequestHeaderEqual('X-Auth-Token', self.TEST_TOKEN)

    def test_token_endpoint_options(self):
        opt_names = [opt.name for opt in token_endpoint.Token.get_options()]

        self.assertThat(opt_names, matchers.HasLength(2))

        self.assertIn('token', opt_names)
        self.assertIn('endpoint', opt_names)

    def test_token_endpoint_user_id(self):
        a = token_endpoint.Token(self.TEST_URL, self.TEST_TOKEN)
        s = session.Session()

        # we can't know this information about this sort of plugin
        self.assertIsNone(a.get_user_id(s))
        self.assertIsNone(a.get_project_id(s))
