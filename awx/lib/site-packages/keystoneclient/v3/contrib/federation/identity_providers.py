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

from keystoneclient import base
from keystoneclient import utils


class IdentityProvider(base.Resource):
    """Object representing Identity Provider container

    Attributes:
        * id: user-defined unique string identifying Identity Provider.

    """
    pass


class IdentityProviderManager(base.CrudManager):
    """Manager class for manipulating Identity Providers."""

    resource_class = IdentityProvider
    collection_key = 'identity_providers'
    key = 'identity_provider'
    base_url = 'OS-FEDERATION'

    def _build_url_and_put(self, **kwargs):
        url = self.build_url(dict_args_in_out=kwargs)
        body = {self.key: kwargs}
        return self._update(url, body=body, response_key=self.key,
                            method='PUT')

    @utils.positional.method(0)
    def create(self, id, **kwargs):
        """Create Identity Provider object.

        Utilize Keystone URI:
        PUT /OS-FEDERATION/identity_providers/$identity_provider

        :param id: unique id of the identity provider.

        """
        return self._build_url_and_put(identity_provider_id=id,
                                       **kwargs)

    def get(self, identity_provider):
        """Fetch Identity Provider object

        Utilize Keystone URI:
        GET /OS-FEDERATION/identity_providers/$identity_provider

        :param identity_provider: an object with identity_provider_id
                                  stored inside.

        """
        return super(IdentityProviderManager, self).get(
            identity_provider_id=base.getid(identity_provider))

    def list(self, **kwargs):
        """List all Identity Providers.

        Utilize Keystone URI:
        GET /OS-FEDERATION/identity_providers

        """
        return super(IdentityProviderManager, self).list(**kwargs)

    def update(self, identity_provider, **kwargs):
        """Update Identity Provider object.

        Utilize Keystone URI:
        PATCH /OS-FEDERATION/identity_providers/$identity_provider

        :param identity_provider: an object with identity_provider_id
                                  stored inside.

        """
        return super(IdentityProviderManager, self).update(
            identity_provider_id=base.getid(identity_provider), **kwargs)

    def delete(self, identity_provider):
        """Delete Identity Provider object.

        Utilize Keystone URI:
        DELETE /OS-FEDERATION/identity_providers/$identity_provider

        :param identity_provider: an object with identity_provider_id
                                  stored inside.

        """
        return super(IdentityProviderManager, self).delete(
            identity_provider_id=base.getid(identity_provider))
