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

    def add_endpoint(self, public, admin=None, internal=None,
                     tenant_id=None, region=None):
        data = {'tenantId': tenant_id or uuid.uuid4().hex,
                'publicURL': public,
                'adminURL': admin or public,
                'internalURL': internal or public,
                'region': region}

        self.setdefault('endpoints', []).append(data)
        return data


class Token(dict):
    """A V2 Keystone token that can be used for testing.

    This object is designed to allow clients to generate a correct V2 token for
    use in there test code. It should prevent clients from having to know the
    correct token format and allow them to test the portions of token handling
    that matter to them and not copy and paste sample.
    """

    def __init__(self, token_id=None, expires=None, issued=None,
                 tenant_id=None, tenant_name=None, user_id=None,
                 user_name=None, trust_id=None, trustee_user_id=None):
        super(Token, self).__init__()

        self.token_id = token_id or uuid.uuid4().hex
        self.user_id = user_id or uuid.uuid4().hex
        self.user_name = user_name or uuid.uuid4().hex

        if not issued:
            issued = timeutils.utcnow() - datetime.timedelta(minutes=2)
        if not expires:
            expires = issued + datetime.timedelta(hours=1)

        try:
            self.issued = issued
        except (TypeError, AttributeError):
            # issued should be able to be passed as a string so ignore
            self.issued_str = issued

        try:
            self.expires = expires
        except (TypeError, AttributeError):
            # expires should be able to be passed as a string so ignore
            self.expires_str = expires

        if tenant_id or tenant_name:
            self.set_scope(tenant_id, tenant_name)

        if trust_id or trustee_user_id:
            # the trustee_user_id will generally be the same as the user_id as
            # the token is being issued to the trustee
            self.set_trust(id=trust_id,
                           trustee_user_id=trustee_user_id or user_id)

    @property
    def root(self):
        return self.setdefault('access', {})

    @property
    def _token(self):
        return self.root.setdefault('token', {})

    @property
    def token_id(self):
        return self._token['id']

    @token_id.setter
    def token_id(self, value):
        self._token['id'] = value

    @property
    def expires_str(self):
        return self._token['expires']

    @expires_str.setter
    def expires_str(self, value):
        self._token['expires'] = value

    @property
    def expires(self):
        return timeutils.parse_isotime(self.expires_str)

    @expires.setter
    def expires(self, value):
        self.expires_str = timeutils.isotime(value)

    @property
    def issued_str(self):
        return self._token['issued_at']

    @issued_str.setter
    def issued_str(self, value):
        self._token['issued_at'] = value

    @property
    def issued(self):
        return timeutils.parse_isotime(self.issued_str)

    @issued.setter
    def issued(self, value):
        self.issued_str = timeutils.isotime(value)

    @property
    def _user(self):
        return self.root.setdefault('user', {})

    @property
    def user_id(self):
        return self._user['id']

    @user_id.setter
    def user_id(self, value):
        self._user['id'] = value

    @property
    def user_name(self):
        return self._user['name']

    @user_name.setter
    def user_name(self, value):
        self._user['name'] = value

    @property
    def tenant_id(self):
        return self._token.get('tenant', {}).get('id')

    @tenant_id.setter
    def tenant_id(self, value):
        self._token.setdefault('tenant', {})['id'] = value

    @property
    def tenant_name(self):
        return self._token.get('tenant', {}).get('name')

    @tenant_name.setter
    def tenant_name(self, value):
        self._token.setdefault('tenant', {})['name'] = value

    @property
    def _metadata(self):
        return self.root.setdefault('metadata', {})

    @property
    def trust_id(self):
        return self.root.setdefault('trust', {})['id']

    @trust_id.setter
    def trust_id(self, value):
        self.root.setdefault('trust', {})['id'] = value

    @property
    def trustee_user_id(self):
        return self.root.setdefault('trust', {}).get('trustee_user_id')

    @trustee_user_id.setter
    def trustee_user_id(self, value):
        self.root.setdefault('trust', {})['trustee_user_id'] = value

    def validate(self):
        scoped = 'tenant' in self.token
        catalog = self.root.get('serviceCatalog')

        if catalog and not scoped:
            msg = 'You cannot have a service catalog on an unscoped token'
            raise exception.FixtureValidationError(msg)

        if scoped and not self.user.get('roles'):
            msg = 'You must have roles on a token to scope it'
            raise exception.FixtureValidationError(msg)

    def add_role(self, name=None, id=None):
        id = id or uuid.uuid4().hex
        name = name or uuid.uuid4().hex
        roles = self._user.setdefault('roles', [])
        roles.append({'name': name})
        self._metadata.setdefault('roles', []).append(id)
        return {'id': id, 'name': name}

    def add_service(self, type, name=None):
        name = name or uuid.uuid4().hex
        service = _Service(name=name, type=type)
        self.root.setdefault('serviceCatalog', []).append(service)
        return service

    def set_scope(self, id=None, name=None):
        self.tenant_id = id or uuid.uuid4().hex
        self.tenant_name = name or uuid.uuid4().hex

    def set_trust(self, id=None, trustee_user_id=None):
        self.trust_id = id or uuid.uuid4().hex
        self.trustee_user_id = trustee_user_id or uuid.uuid4().hex
