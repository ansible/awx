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
import uuid

from oslo_utils import timeutils
import testresources

from keystoneclient import access
from keystoneclient import fixture
from keystoneclient.tests.unit import client_fixtures as token_data
from keystoneclient.tests.unit.v2_0 import client_fixtures
from keystoneclient.tests.unit.v2_0 import utils


class AccessInfoTest(utils.TestCase, testresources.ResourcedTestCase):

    resources = [('examples', token_data.EXAMPLES_RESOURCE)]

    def test_building_unscoped_accessinfo(self):
        token = client_fixtures.unscoped_token()
        auth_ref = access.AccessInfo.factory(body=token)

        self.assertTrue(auth_ref)
        self.assertIn('token', auth_ref)

        self.assertEqual(auth_ref.auth_token,
                         '3e2813b7ba0b4006840c3825860b86ed')
        self.assertEqual(auth_ref.username, 'exampleuser')
        self.assertEqual(auth_ref.user_id, 'c4da488862bd435c9e6c0275a0d0e49a')

        self.assertEqual(auth_ref.role_ids, [])
        self.assertEqual(auth_ref.role_names, [])

        self.assertIsNone(auth_ref.tenant_name)
        self.assertIsNone(auth_ref.tenant_id)

        self.assertIsNone(auth_ref.auth_url)
        self.assertIsNone(auth_ref.management_url)

        self.assertFalse(auth_ref.scoped)
        self.assertFalse(auth_ref.domain_scoped)
        self.assertFalse(auth_ref.project_scoped)
        self.assertFalse(auth_ref.trust_scoped)

        self.assertIsNone(auth_ref.project_domain_id)
        self.assertIsNone(auth_ref.project_domain_name)
        self.assertEqual(auth_ref.user_domain_id, 'default')
        self.assertEqual(auth_ref.user_domain_name, 'Default')

        self.assertEqual(auth_ref.expires, token.expires)
        self.assertEqual(auth_ref.issued, token.issued)

    def test_will_expire_soon(self):
        token = client_fixtures.unscoped_token()
        expires = timeutils.utcnow() + datetime.timedelta(minutes=5)
        token.expires = expires
        auth_ref = access.AccessInfo.factory(body=token)
        self.assertFalse(auth_ref.will_expire_soon(stale_duration=120))
        self.assertTrue(auth_ref.will_expire_soon(stale_duration=300))
        self.assertFalse(auth_ref.will_expire_soon())

    def test_building_scoped_accessinfo(self):
        token = client_fixtures.project_scoped_token()
        auth_ref = access.AccessInfo.factory(body=token)

        self.assertTrue(auth_ref)
        self.assertIn('token', auth_ref)
        self.assertIn('serviceCatalog', auth_ref)
        self.assertTrue(auth_ref['serviceCatalog'])

        self.assertEqual(auth_ref.auth_token,
                         '04c7d5ffaeef485f9dc69c06db285bdb')
        self.assertEqual(auth_ref.username, 'exampleuser')
        self.assertEqual(auth_ref.user_id, 'c4da488862bd435c9e6c0275a0d0e49a')

        self.assertEqual(auth_ref.role_ids, ['member_id'])
        self.assertEqual(auth_ref.role_names, ['Member'])

        self.assertEqual(auth_ref.tenant_name, 'exampleproject')
        self.assertEqual(auth_ref.tenant_id,
                         '225da22d3ce34b15877ea70b2a575f58')

        self.assertEqual(auth_ref.tenant_name, auth_ref.project_name)
        self.assertEqual(auth_ref.tenant_id, auth_ref.project_id)

        self.assertEqual(auth_ref.auth_url, ('http://public.com:5000/v2.0',))
        self.assertEqual(auth_ref.management_url, ('http://admin:35357/v2.0',))

        self.assertEqual(auth_ref.project_domain_id, 'default')
        self.assertEqual(auth_ref.project_domain_name, 'Default')
        self.assertEqual(auth_ref.user_domain_id, 'default')
        self.assertEqual(auth_ref.user_domain_name, 'Default')

        self.assertTrue(auth_ref.scoped)
        self.assertTrue(auth_ref.project_scoped)
        self.assertFalse(auth_ref.domain_scoped)

    def test_diablo_token(self):
        diablo_token = self.examples.TOKEN_RESPONSES[
            self.examples.VALID_DIABLO_TOKEN]
        auth_ref = access.AccessInfo.factory(body=diablo_token)

        self.assertTrue(auth_ref)
        self.assertEqual(auth_ref.username, 'user_name1')
        self.assertEqual(auth_ref.project_id, 'tenant_id1')
        self.assertEqual(auth_ref.project_name, 'tenant_id1')
        self.assertEqual(auth_ref.project_domain_id, 'default')
        self.assertEqual(auth_ref.project_domain_name, 'Default')
        self.assertEqual(auth_ref.user_domain_id, 'default')
        self.assertEqual(auth_ref.user_domain_name, 'Default')
        self.assertEqual(auth_ref.role_names, ['role1', 'role2'])
        self.assertFalse(auth_ref.scoped)

    def test_grizzly_token(self):
        grizzly_token = self.examples.TOKEN_RESPONSES[
            self.examples.SIGNED_TOKEN_SCOPED_KEY]
        auth_ref = access.AccessInfo.factory(body=grizzly_token)

        self.assertEqual(auth_ref.project_id, 'tenant_id1')
        self.assertEqual(auth_ref.project_name, 'tenant_name1')
        self.assertEqual(auth_ref.project_domain_id, 'default')
        self.assertEqual(auth_ref.project_domain_name, 'Default')
        self.assertEqual(auth_ref.user_domain_id, 'default')
        self.assertEqual(auth_ref.user_domain_name, 'Default')
        self.assertEqual(auth_ref.role_names, ['role1', 'role2'])

    def test_v2_roles(self):
        role_id = 'a'
        role_name = 'b'

        token = fixture.V2Token()
        token.set_scope()
        token.add_role(id=role_id, name=role_name)

        auth_ref = access.AccessInfo.factory(body=token)

        self.assertEqual([role_id], auth_ref.role_ids)
        self.assertEqual([role_id], auth_ref['metadata']['roles'])
        self.assertEqual([role_name], auth_ref.role_names)
        self.assertEqual([{'name': role_name}], auth_ref['user']['roles'])

    def test_trusts(self):
        user_id = uuid.uuid4().hex
        trust_id = uuid.uuid4().hex

        token = fixture.V2Token(user_id=user_id, trust_id=trust_id)
        token.set_scope()
        token.add_role()

        auth_ref = access.AccessInfo.factory(body=token)

        self.assertEqual(trust_id, auth_ref.trust_id)
        self.assertEqual(user_id, auth_ref.trustee_user_id)

        self.assertEqual(trust_id, token['access']['trust']['id'])

    def test_override_auth_token(self):
        token = fixture.V2Token()
        token.set_scope()
        token.add_role()

        new_auth_token = uuid.uuid4().hex

        auth_ref = access.AccessInfo.factory(body=token)

        self.assertEqual(token.token_id, auth_ref.auth_token)

        auth_ref.auth_token = new_auth_token
        self.assertEqual(new_auth_token, auth_ref.auth_token)

        del auth_ref.auth_token
        self.assertEqual(token.token_id, auth_ref.auth_token)

    def test_override_auth_token_in_factory(self):
        token = fixture.V2Token()
        token.set_scope()
        token.add_role()

        new_auth_token = uuid.uuid4().hex

        auth_ref = access.AccessInfo.factory(body=token,
                                             auth_token=new_auth_token)

        self.assertEqual(new_auth_token, auth_ref.auth_token)
        del auth_ref.auth_token
        self.assertEqual(token.token_id, auth_ref.auth_token)


def load_tests(loader, tests, pattern):
    return testresources.OptimisingTestSuite(tests)
