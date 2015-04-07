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

import uuid

from keystoneclient import access
from keystoneclient import auth
from keystoneclient.auth.identity import access as access_plugin
from keystoneclient import fixture
from keystoneclient import session
from keystoneclient.tests.unit import utils


class AccessInfoPluginTests(utils.TestCase):

    def setUp(self):
        super(AccessInfoPluginTests, self).setUp()
        self.session = session.Session()
        self.auth_token = uuid.uuid4().hex

    def _plugin(self, **kwargs):
        token = fixture.V3Token()
        s = token.add_service('identity')
        s.add_standard_endpoints(public=self.TEST_ROOT_URL)

        auth_ref = access.AccessInfo.factory(body=token,
                                             auth_token=self.auth_token)
        return access_plugin.AccessInfoPlugin(auth_ref, **kwargs)

    def test_auth_ref(self):
        plugin = self._plugin()
        self.assertEqual(self.TEST_ROOT_URL,
                         plugin.get_endpoint(self.session,
                                             service_type='identity',
                                             interface='public'))
        self.assertEqual(self.auth_token, plugin.get_token(session))

    def test_auth_url(self):
        auth_url = 'http://keystone.test.url'
        plugin = self._plugin(auth_url=auth_url)

        self.assertEqual(auth_url,
                         plugin.get_endpoint(self.session,
                                             interface=auth.AUTH_INTERFACE))

    def test_invalidate(self):
        plugin = self._plugin()
        auth_ref = plugin.auth_ref

        self.assertIsInstance(auth_ref, access.AccessInfo)
        self.assertFalse(plugin.invalidate())
        self.assertIs(auth_ref, plugin.auth_ref)
