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

import six

from keystoneclient import fixture
from keystoneclient.tests.unit import utils


class V2TokenTests(utils.TestCase):

    def test_unscoped(self):
        token_id = uuid.uuid4().hex
        user_id = uuid.uuid4().hex
        user_name = uuid.uuid4().hex

        token = fixture.V2Token(token_id=token_id,
                                user_id=user_id,
                                user_name=user_name)

        self.assertEqual(token_id, token.token_id)
        self.assertEqual(token_id, token['access']['token']['id'])
        self.assertEqual(user_id, token.user_id)
        self.assertEqual(user_id, token['access']['user']['id'])
        self.assertEqual(user_name, token.user_name)
        self.assertEqual(user_name, token['access']['user']['name'])

    def test_tenant_scoped(self):
        tenant_id = uuid.uuid4().hex
        tenant_name = uuid.uuid4().hex

        token = fixture.V2Token(tenant_id=tenant_id,
                                tenant_name=tenant_name)

        self.assertEqual(tenant_id, token.tenant_id)
        self.assertEqual(tenant_id, token['access']['token']['tenant']['id'])
        self.assertEqual(tenant_name, token.tenant_name)
        tn = token['access']['token']['tenant']['name']
        self.assertEqual(tenant_name, tn)

    def test_trust_scoped(self):
        trust_id = uuid.uuid4().hex
        trustee_user_id = uuid.uuid4().hex

        token = fixture.V2Token(trust_id=trust_id,
                                trustee_user_id=trustee_user_id)
        trust = token['access']['trust']

        self.assertEqual(trust_id, token.trust_id)
        self.assertEqual(trust_id, trust['id'])
        self.assertEqual(trustee_user_id, token.trustee_user_id)
        self.assertEqual(trustee_user_id, trust['trustee_user_id'])

    def test_roles(self):
        role_id1 = uuid.uuid4().hex
        role_name1 = uuid.uuid4().hex
        role_id2 = uuid.uuid4().hex
        role_name2 = uuid.uuid4().hex

        token = fixture.V2Token()
        token.add_role(id=role_id1, name=role_name1)
        token.add_role(id=role_id2, name=role_name2)

        role_names = token['access']['user']['roles']
        role_ids = token['access']['metadata']['roles']

        self.assertEqual(set([role_id1, role_id2]), set(role_ids))
        for r in (role_name1, role_name2):
            self.assertIn({'name': r}, role_names)

    def test_services(self):
        service_type = uuid.uuid4().hex
        service_name = uuid.uuid4().hex
        region = uuid.uuid4().hex

        public = uuid.uuid4().hex
        admin = uuid.uuid4().hex
        internal = uuid.uuid4().hex

        token = fixture.V2Token()
        svc = token.add_service(type=service_type, name=service_name)

        svc.add_endpoint(public=public,
                         admin=admin,
                         internal=internal,
                         region=region)

        self.assertEqual(1, len(token['access']['serviceCatalog']))
        service = token['access']['serviceCatalog'][0]['endpoints'][0]

        self.assertEqual(public, service['publicURL'])
        self.assertEqual(internal, service['internalURL'])
        self.assertEqual(admin, service['adminURL'])
        self.assertEqual(region, service['region'])


class V3TokenTests(utils.TestCase):

    def test_unscoped(self):
        user_id = uuid.uuid4().hex
        user_name = uuid.uuid4().hex
        user_domain_id = uuid.uuid4().hex
        user_domain_name = uuid.uuid4().hex

        token = fixture.V3Token(user_id=user_id,
                                user_name=user_name,
                                user_domain_id=user_domain_id,
                                user_domain_name=user_domain_name)

        self.assertEqual(user_id, token.user_id)
        self.assertEqual(user_id, token['token']['user']['id'])
        self.assertEqual(user_name, token.user_name)
        self.assertEqual(user_name, token['token']['user']['name'])

        user_domain = token['token']['user']['domain']

        self.assertEqual(user_domain_id, token.user_domain_id)
        self.assertEqual(user_domain_id, user_domain['id'])
        self.assertEqual(user_domain_name, token.user_domain_name)
        self.assertEqual(user_domain_name, user_domain['name'])

    def test_project_scoped(self):
        project_id = uuid.uuid4().hex
        project_name = uuid.uuid4().hex
        project_domain_id = uuid.uuid4().hex
        project_domain_name = uuid.uuid4().hex

        token = fixture.V3Token(project_id=project_id,
                                project_name=project_name,
                                project_domain_id=project_domain_id,
                                project_domain_name=project_domain_name)

        self.assertEqual(project_id, token.project_id)
        self.assertEqual(project_id, token['token']['project']['id'])
        self.assertEqual(project_name, token.project_name)
        self.assertEqual(project_name, token['token']['project']['name'])

        project_domain = token['token']['project']['domain']

        self.assertEqual(project_domain_id, token.project_domain_id)
        self.assertEqual(project_domain_id, project_domain['id'])
        self.assertEqual(project_domain_name, token.project_domain_name)
        self.assertEqual(project_domain_name, project_domain['name'])

    def test_domain_scoped(self):
        domain_id = uuid.uuid4().hex
        domain_name = uuid.uuid4().hex

        token = fixture.V3Token(domain_id=domain_id,
                                domain_name=domain_name)

        self.assertEqual(domain_id, token.domain_id)
        self.assertEqual(domain_id, token['token']['domain']['id'])
        self.assertEqual(domain_name, token.domain_name)
        self.assertEqual(domain_name, token['token']['domain']['name'])

    def test_roles(self):
        role1 = {'id': uuid.uuid4().hex, 'name': uuid.uuid4().hex}
        role2 = {'id': uuid.uuid4().hex, 'name': uuid.uuid4().hex}

        token = fixture.V3Token()
        token.add_role(**role1)
        token.add_role(**role2)

        self.assertEqual(2, len(token['token']['roles']))

        self.assertIn(role1, token['token']['roles'])
        self.assertIn(role2, token['token']['roles'])

    def test_trust_scoped(self):
        trust_id = uuid.uuid4().hex
        trustee_user_id = uuid.uuid4().hex
        trustor_user_id = uuid.uuid4().hex
        impersonation = True

        token = fixture.V3Token(trust_id=trust_id,
                                trustee_user_id=trustee_user_id,
                                trustor_user_id=trustor_user_id,
                                trust_impersonation=impersonation)

        trust = token['token']['OS-TRUST:trust']
        self.assertEqual(trust_id, token.trust_id)
        self.assertEqual(trust_id, trust['id'])
        self.assertEqual(trustee_user_id, token.trustee_user_id)
        self.assertEqual(trustee_user_id, trust['trustee_user']['id'])
        self.assertEqual(trustor_user_id, token.trustor_user_id)
        self.assertEqual(trustor_user_id, trust['trustor_user']['id'])
        self.assertEqual(impersonation, token.trust_impersonation)
        self.assertEqual(impersonation, trust['impersonation'])

    def test_oauth_scoped(self):
        access_id = uuid.uuid4().hex
        consumer_id = uuid.uuid4().hex

        token = fixture.V3Token(oauth_access_token_id=access_id,
                                oauth_consumer_id=consumer_id)

        oauth = token['token']['OS-OAUTH1']

        self.assertEqual(access_id, token.oauth_access_token_id)
        self.assertEqual(access_id, oauth['access_token_id'])
        self.assertEqual(consumer_id, token.oauth_consumer_id)
        self.assertEqual(consumer_id, oauth['consumer_id'])

    def test_catalog(self):
        service_type = uuid.uuid4().hex
        service_name = uuid.uuid4().hex
        region = uuid.uuid4().hex
        endpoints = {'public': uuid.uuid4().hex,
                     'internal': uuid.uuid4().hex,
                     'admin': uuid.uuid4().hex}

        token = fixture.V3Token()
        svc = token.add_service(type=service_type, name=service_name)
        svc.add_standard_endpoints(region=region, **endpoints)

        self.assertEqual(1, len(token['token']['catalog']))
        service = token['token']['catalog'][0]
        self.assertEqual(3, len(service['endpoints']))

        self.assertEqual(service_name, service['name'])
        self.assertEqual(service_type, service['type'])

        for interface, url in six.iteritems(endpoints):
            endpoint = {'interface': interface, 'url': url,
                        'region': region, 'region_id': region}
            self.assertIn(endpoint, service['endpoints'])
