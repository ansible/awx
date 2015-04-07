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

import datetime
import uuid

from oslo_utils import timeutils

from keystoneclient.fixture import exception


class _Service(dict):
    """One of the services that exist in the catalog.

    You use this by adding a service to a token which returns an instance of
    this object and then you can add_endpoints to the service.
    """

    def add_endpoint(self, interface, url, region=None):
        data = {'interface': interface,
                'url': url,
                'region': region,
                'region_id': region}
        self.setdefault('endpoints', []).append(data)
        return data

    def add_standard_endpoints(self, public=None, admin=None, internal=None,
                               region=None):
        ret = []

        if public:
            ret.append(self.add_endpoint('public', public, region=region))
        if admin:
            ret.append(self.add_endpoint('admin', admin, region=region))
        if internal:
            ret.append(self.add_endpoint('internal', internal, region=region))

        return ret


class Token(dict):
    """A V3 Keystone token that can be used for testing.

    This object is designed to allow clients to generate a correct V3 token for
    use in there test code. It should prevent clients from having to know the
    correct token format and allow them to test the portions of token handling
    that matter to them and not copy and paste sample.
    """

    def __init__(self, expires=None, issued=None, user_id=None, user_name=None,
                 user_domain_id=None, user_domain_name=None, methods=None,
                 project_id=None, project_name=None, project_domain_id=None,
                 project_domain_name=None, domain_id=None, domain_name=None,
                 trust_id=None, trust_impersonation=None, trustee_user_id=None,
                 trustor_user_id=None, oauth_access_token_id=None,
                 oauth_consumer_id=None):
        super(Token, self).__init__()

        self.user_id = user_id or uuid.uuid4().hex
        self.user_name = user_name or uuid.uuid4().hex
        self.user_domain_id = user_domain_id or uuid.uuid4().hex
        self.user_domain_name = user_domain_name or uuid.uuid4().hex

        if not methods:
            methods = ['password']
        self.methods.extend(methods)

        if not issued:
            issued = timeutils.utcnow() - datetime.timedelta(minutes=2)

        try:
            self.issued = issued
        except (TypeError, AttributeError):
            # issued should be able to be passed as a string so ignore
            self.issued_str = issued

        if not expires:
            expires = self.issued + datetime.timedelta(hours=1)

        try:
            self.expires = expires
        except (TypeError, AttributeError):
            # expires should be able to be passed as a string so ignore
            self.expires_str = expires

        if (project_id or project_name or
                project_domain_id or project_domain_name):
            self.set_project_scope(id=project_id,
                                   name=project_name,
                                   domain_id=project_domain_id,
                                   domain_name=project_domain_name)

        if domain_id or domain_name:
            self.set_domain_scope(id=domain_id, name=domain_name)

        if (trust_id or (trust_impersonation is not None) or
                trustee_user_id or trustor_user_id):
            self.set_trust_scope(id=trust_id,
                                 impersonation=trust_impersonation,
                                 trustee_user_id=trustee_user_id,
                                 trustor_user_id=trustor_user_id)

        if oauth_access_token_id or oauth_consumer_id:
            self.set_oauth(access_token_id=oauth_access_token_id,
                           consumer_id=oauth_consumer_id)

    @property
    def root(self):
        return self.setdefault('token', {})

    @property
    def expires_str(self):
        return self.root.get('expires_at')

    @expires_str.setter
    def expires_str(self, value):
        self.root['expires_at'] = value

    @property
    def expires(self):
        return timeutils.parse_isotime(self.expires_str)

    @expires.setter
    def expires(self, value):
        self.expires_str = timeutils.isotime(value, subsecond=True)

    @property
    def issued_str(self):
        return self.root.get('issued_at')

    @issued_str.setter
    def issued_str(self, value):
        self.root['issued_at'] = value

    @property
    def issued(self):
        return timeutils.parse_isotime(self.issued_str)

    @issued.setter
    def issued(self, value):
        self.issued_str = timeutils.isotime(value, subsecond=True)

    @property
    def _user(self):
        return self.root.setdefault('user', {})

    @property
    def user_id(self):
        return self._user.get('id')

    @user_id.setter
    def user_id(self, value):
        self._user['id'] = value

    @property
    def user_name(self):
        return self._user.get('name')

    @user_name.setter
    def user_name(self, value):
        self._user['name'] = value

    @property
    def _user_domain(self):
        return self._user.setdefault('domain', {})

    @property
    def user_domain_id(self):
        return self._user_domain.get('id')

    @user_domain_id.setter
    def user_domain_id(self, value):
        self._user_domain['id'] = value

    @property
    def user_domain_name(self):
        return self._user_domain.get('name')

    @user_domain_name.setter
    def user_domain_name(self, value):
        self._user_domain['name'] = value

    @property
    def methods(self):
        return self.root.setdefault('methods', [])

    @property
    def project_id(self):
        return self.root.get('project', {}).get('id')

    @project_id.setter
    def project_id(self, value):
        self.root.setdefault('project', {})['id'] = value

    @property
    def project_name(self):
        return self.root.get('project', {}).get('name')

    @project_name.setter
    def project_name(self, value):
        self.root.setdefault('project', {})['name'] = value

    @property
    def project_domain_id(self):
        return self.root.get('project', {}).get('domain', {}).get('id')

    @project_domain_id.setter
    def project_domain_id(self, value):
        project = self.root.setdefault('project', {})
        project.setdefault('domain', {})['id'] = value

    @property
    def project_domain_name(self):
        return self.root.get('project', {}).get('domain', {}).get('name')

    @project_domain_name.setter
    def project_domain_name(self, value):
        project = self.root.setdefault('project', {})
        project.setdefault('domain', {})['name'] = value

    @property
    def domain_id(self):
        return self.root.get('domain', {}).get('id')

    @domain_id.setter
    def domain_id(self, value):
        self.root.setdefault('domain', {})['id'] = value

    @property
    def domain_name(self):
        return self.root.get('domain', {}).get('name')

    @domain_name.setter
    def domain_name(self, value):
        self.root.setdefault('domain', {})['name'] = value

    @property
    def trust_id(self):
        return self.root.get('OS-TRUST:trust', {}).get('id')

    @trust_id.setter
    def trust_id(self, value):
        self.root.setdefault('OS-TRUST:trust', {})['id'] = value

    @property
    def trust_impersonation(self):
        return self.root.get('OS-TRUST:trust', {}).get('impersonation')

    @trust_impersonation.setter
    def trust_impersonation(self, value):
        self.root.setdefault('OS-TRUST:trust', {})['impersonation'] = value

    @property
    def trustee_user_id(self):
        trust = self.root.get('OS-TRUST:trust', {})
        return trust.get('trustee_user', {}).get('id')

    @trustee_user_id.setter
    def trustee_user_id(self, value):
        trust = self.root.setdefault('OS-TRUST:trust', {})
        trust.setdefault('trustee_user', {})['id'] = value

    @property
    def trustor_user_id(self):
        trust = self.root.get('OS-TRUST:trust', {})
        return trust.get('trustor_user', {}).get('id')

    @trustor_user_id.setter
    def trustor_user_id(self, value):
        trust = self.root.setdefault('OS-TRUST:trust', {})
        trust.setdefault('trustor_user', {})['id'] = value

    @property
    def oauth_access_token_id(self):
        return self.root.get('OS-OAUTH1', {}).get('access_token_id')

    @oauth_access_token_id.setter
    def oauth_access_token_id(self, value):
        self.root.setdefault('OS-OAUTH1', {})['access_token_id'] = value

    @property
    def oauth_consumer_id(self):
        return self.root.get('OS-OAUTH1', {}).get('consumer_id')

    @oauth_consumer_id.setter
    def oauth_consumer_id(self, value):
        self.root.setdefault('OS-OAUTH1', {})['consumer_id'] = value

    def validate(self):
        project = self.root.get('project')
        domain = self.root.get('domain')
        trust = self.root.get('OS-TRUST:trust')
        catalog = self.root.get('catalog')
        roles = self.root.get('roles')
        scoped = project or domain or trust

        if sum((bool(project), bool(domain), bool(trust))) > 1:
            msg = 'You cannot scope to multiple targets'
            raise exception.FixtureValidationError(msg)

        if catalog and not scoped:
            msg = 'You cannot have a service catalog on an unscoped token'
            raise exception.FixtureValidationError(msg)

        if scoped and not self.user.get('roles'):
            msg = 'You must have roles on a token to scope it'
            raise exception.FixtureValidationError(msg)

        if bool(scoped) != bool(roles):
            msg = 'You must be scoped to have roles and vice-versa'
            raise exception.FixtureValidationError(msg)

    def add_role(self, name=None, id=None):
        roles = self.root.setdefault('roles', [])
        data = {'id': id or uuid.uuid4().hex,
                'name': name or uuid.uuid4().hex}
        roles.append(data)
        return data

    def add_service(self, type, name=None):
        service = _Service(type=type)
        if name:
            service['name'] = name
        self.root.setdefault('catalog', []).append(service)
        return service

    def set_project_scope(self, id=None, name=None, domain_id=None,
                          domain_name=None):
        self.project_id = id or uuid.uuid4().hex
        self.project_name = name or uuid.uuid4().hex
        self.project_domain_id = domain_id or uuid.uuid4().hex
        self.project_domain_name = domain_name or uuid.uuid4().hex

    def set_domain_scope(self, id=None, name=None):
        self.domain_id = id or uuid.uuid4().hex
        self.domain_name = name or uuid.uuid4().hex

    def set_trust_scope(self, id=None, impersonation=False,
                        trustee_user_id=None, trustor_user_id=None):
        self.trust_id = id or uuid.uuid4().hex
        self.trust_impersonation = impersonation
        self.trustee_user_id = trustee_user_id or uuid.uuid4().hex
        self.trustor_user_id = trustor_user_id or uuid.uuid4().hex

    def set_oauth(self, access_token_id=None, consumer_id=None):
        self.oauth_access_token_id = access_token_id or uuid.uuid4().hex
        self.oauth_consumer_id = consumer_id or uuid.uuid4().hex


class V3FederationToken(Token):
    """A V3 Keystone Federation token that can be used for testing.

    Similar to V3Token, this object is designed to allow clients to generate
    a correct V3 federation token for use in test code.
    """

    def __init__(self, methods=None, identity_provider=None, protocol=None,
                 groups=None):
        methods = methods or ['saml2']
        super(V3FederationToken, self).__init__(methods=methods)
        # NOTE(stevemar): Federated tokens do not have a domain for the user
        del self._user['domain']
        self.add_federation_info_to_user(identity_provider, protocol, groups)

    def add_federation_info_to_user(self, identity_provider=None,
                                    protocol=None, groups=None):
        data = {
            "OS-FEDERATION": {
                "identity_provider": identity_provider or uuid.uuid4().hex,
                "protocol": protocol or uuid.uuid4().hex,
                "groups": groups or [{"id": uuid.uuid4().hex}]
            }
        }
        self._user.update(data)
        return data
