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

import json
import uuid

import six

from keystoneclient.auth import token_endpoint
from keystoneclient import exceptions
from keystoneclient import fixture
from keystoneclient import session
from keystoneclient.tests.unit.v2_0 import client_fixtures
from keystoneclient.tests.unit.v2_0 import utils
from keystoneclient.v2_0 import client


class KeystoneClientTest(utils.TestCase):

    def test_unscoped_init(self):
        token = client_fixtures.unscoped_token()
        self.stub_auth(json=token)

        c = client.Client(username='exampleuser',
                          password='password',
                          auth_url=self.TEST_URL)
        self.assertIsNotNone(c.auth_ref)
        self.assertFalse(c.auth_ref.scoped)
        self.assertFalse(c.auth_ref.domain_scoped)
        self.assertFalse(c.auth_ref.project_scoped)
        self.assertIsNone(c.auth_ref.trust_id)
        self.assertFalse(c.auth_ref.trust_scoped)
        self.assertIsNone(c.get_project_id(session=None))
        self.assertEqual(token.user_id, c.get_user_id(session=None))

    def test_scoped_init(self):
        token = client_fixtures.project_scoped_token()
        self.stub_auth(json=token)

        c = client.Client(username='exampleuser',
                          password='password',
                          tenant_name='exampleproject',
                          auth_url=self.TEST_URL)
        self.assertIsNotNone(c.auth_ref)
        self.assertTrue(c.auth_ref.scoped)
        self.assertTrue(c.auth_ref.project_scoped)
        self.assertFalse(c.auth_ref.domain_scoped)
        self.assertIsNone(c.auth_ref.trust_id)
        self.assertFalse(c.auth_ref.trust_scoped)

        self.assertEqual(token.tenant_id, c.get_project_id(session=None))
        self.assertEqual(token.user_id, c.get_user_id(session=None))

    def test_auth_ref_load(self):
        self.stub_auth(json=client_fixtures.project_scoped_token())

        cl = client.Client(username='exampleuser',
                           password='password',
                           tenant_name='exampleproject',
                           auth_url=self.TEST_URL)
        cache = json.dumps(cl.auth_ref)
        new_client = client.Client(auth_ref=json.loads(cache))
        self.assertIsNotNone(new_client.auth_ref)
        self.assertTrue(new_client.auth_ref.scoped)
        self.assertTrue(new_client.auth_ref.project_scoped)
        self.assertFalse(new_client.auth_ref.domain_scoped)
        self.assertIsNone(new_client.auth_ref.trust_id)
        self.assertFalse(new_client.auth_ref.trust_scoped)
        self.assertEqual(new_client.username, 'exampleuser')
        self.assertIsNone(new_client.password)
        self.assertEqual(new_client.management_url,
                         'http://admin:35357/v2.0')

    def test_auth_ref_load_with_overridden_arguments(self):
        self.stub_auth(json=client_fixtures.project_scoped_token())

        cl = client.Client(username='exampleuser',
                           password='password',
                           tenant_name='exampleproject',
                           auth_url=self.TEST_URL)
        cache = json.dumps(cl.auth_ref)
        new_auth_url = "http://new-public:5000/v2.0"
        new_client = client.Client(auth_ref=json.loads(cache),
                                   auth_url=new_auth_url)
        self.assertIsNotNone(new_client.auth_ref)
        self.assertTrue(new_client.auth_ref.scoped)
        self.assertTrue(new_client.auth_ref.scoped)
        self.assertTrue(new_client.auth_ref.project_scoped)
        self.assertFalse(new_client.auth_ref.domain_scoped)
        self.assertIsNone(new_client.auth_ref.trust_id)
        self.assertFalse(new_client.auth_ref.trust_scoped)
        self.assertEqual(new_client.auth_url, new_auth_url)
        self.assertEqual(new_client.username, 'exampleuser')
        self.assertIsNone(new_client.password)
        self.assertEqual(new_client.management_url,
                         'http://admin:35357/v2.0')

    def test_init_err_no_auth_url(self):
        self.assertRaises(exceptions.AuthorizationFailure,
                          client.Client,
                          username='exampleuser',
                          password='password')

    def test_management_url_is_updated(self):
        first = fixture.V2Token()
        first.set_scope()
        admin_url = 'http://admin:35357/v2.0'
        second_url = 'http://secondurl:35357/v2.0'

        s = first.add_service('identity')
        s.add_endpoint(public='http://public.com:5000/v2.0',
                       admin=admin_url)

        second = fixture.V2Token()
        second.set_scope()
        s = second.add_service('identity')
        s.add_endpoint(public='http://secondurl:5000/v2.0',
                       admin=second_url)

        self.stub_auth(response_list=[{'json': first}, {'json': second}])

        cl = client.Client(username='exampleuser',
                           password='password',
                           tenant_name='exampleproject',
                           auth_url=self.TEST_URL)
        self.assertEqual(cl.management_url, admin_url)

        cl.authenticate()
        self.assertEqual(cl.management_url, second_url)

    def test_client_with_region_name_passes_to_service_catalog(self):
        # NOTE(jamielennox): this is deprecated behaviour that should be
        # removed ASAP, however must remain compatible.
        self.stub_auth(json=client_fixtures.auth_response_body())

        cl = client.Client(username='exampleuser',
                           password='password',
                           tenant_name='exampleproject',
                           auth_url=self.TEST_URL,
                           region_name='North')
        self.assertEqual(cl.service_catalog.url_for(service_type='image'),
                         'https://image.north.host/v1/')

        cl = client.Client(username='exampleuser',
                           password='password',
                           tenant_name='exampleproject',
                           auth_url=self.TEST_URL,
                           region_name='South')
        self.assertEqual(cl.service_catalog.url_for(service_type='image'),
                         'https://image.south.host/v1/')

    def test_client_without_auth_params(self):
        self.assertRaises(exceptions.AuthorizationFailure,
                          client.Client,
                          tenant_name='exampleproject',
                          auth_url=self.TEST_URL)

    def test_client_params(self):
        opts = {'auth': token_endpoint.Token('a', 'b'),
                'connect_retries': 50,
                'endpoint_override': uuid.uuid4().hex,
                'interface': uuid.uuid4().hex,
                'region_name': uuid.uuid4().hex,
                'service_name': uuid.uuid4().hex,
                'user_agent': uuid.uuid4().hex,
                }

        sess = session.Session()
        cl = client.Client(session=sess, **opts)

        for k, v in six.iteritems(opts):
            self.assertEqual(v, getattr(cl._adapter, k))

        self.assertEqual('identity', cl._adapter.service_type)
        self.assertEqual('v2.0', cl._adapter.version)
