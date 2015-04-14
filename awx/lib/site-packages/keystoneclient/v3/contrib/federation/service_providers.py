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


class ServiceProvider(base.Resource):
    """Object representing Service Provider container

    Attributes:
        * id: user-defined unique string identifying Service Provider.
        * sp_url: the shibboleth endpoint of a Service Provider.
        * auth_url: the authentication url of Service Provider.

    """
    pass


class ServiceProviderManager(base.CrudManager):
    """Manager class for manipulating Service Providers."""

    resource_class = ServiceProvider
    collection_key = 'service_providers'
    key = 'service_provider'
    base_url = 'OS-FEDERATION'

    def _build_url_and_put(self, **kwargs):
        url = self.build_url(dict_args_in_out=kwargs)
        body = {self.key: kwargs}
        return self._update(url, body=body, response_key=self.key,
                            method='PUT')

    @utils.positional.method(0)
    def create(self, id, **kwargs):
        """Create Service Provider object.

        Utilize Keystone URI:
        ``PUT /OS-FEDERATION/service_providers/{id}``

        :param id: unique id of the service provider.

        """
        return self._build_url_and_put(service_provider_id=id,
                                       **kwargs)

    def get(self, service_provider):
        """Fetch Service Provider object

        Utilize Keystone URI:
        ``GET /OS-FEDERATION/service_providers/{id}``

        :param service_provider: an object with service_provider_id
                                 stored inside.

        """
        return super(ServiceProviderManager, self).get(
            service_provider_id=base.getid(service_provider))

    def list(self, **kwargs):
        """List all Service Providers.

        Utilize Keystone URI:
        ``GET /OS-FEDERATION/service_providers``

        """
        return super(ServiceProviderManager, self).list(**kwargs)

    def update(self, service_provider, **kwargs):
        """Update the existing Service Provider object on the server.

        Only properties provided to the function are being updated.

        Utilize Keystone URI:
        ``PATCH /OS-FEDERATION/service_providers/{id}``

        :param service_provider: an object with service_provider_id
                                 stored inside.

        """
        return super(ServiceProviderManager, self).update(
            service_provider_id=base.getid(service_provider), **kwargs)

    def delete(self, service_provider):
        """Delete Service Provider object.

        Utilize Keystone URI:
        ``DELETE /OS-FEDERATION/service_providers/{id}``

        :param service_provider: an object with service_provider_id
                                 stored inside.

        """
        return super(ServiceProviderManager, self).delete(
            service_provider_id=base.getid(service_provider))
