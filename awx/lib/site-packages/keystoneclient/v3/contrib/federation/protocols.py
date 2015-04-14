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


class Protocol(base.Resource):
    """An object representing federation protocol container.

    Attributes:
        * id: user-defined unique per Identity Provider string identifying
              federation protocol.

    """
    pass


class ProtocolManager(base.CrudManager):
    """Manager class for manipulating federation protocols."""

    resource_class = Protocol
    collection_key = 'protocols'
    key = 'protocol'
    base_url = 'OS-FEDERATION/identity_providers'

    def build_url(self, dict_args_in_out=None):
        """Build URL for federation protocols."""

        if dict_args_in_out is None:
            dict_args_in_out = {}

        identity_provider_id = dict_args_in_out.pop('identity_provider_id',
                                                    None)
        if identity_provider_id:
            base_url = '/'.join([self.base_url, identity_provider_id])
        else:
            base_url = self.base_url

        dict_args_in_out.setdefault('base_url', base_url)
        return super(ProtocolManager, self).build_url(dict_args_in_out)

    def _build_url_and_put(self, request_body=None, **kwargs):
        url = self.build_url(dict_args_in_out=kwargs)
        body = {self.key: request_body}
        return self._update(url, body=body,
                            response_key=self.key,
                            method='PUT')

    @utils.positional.method(3)
    def create(self, protocol_id, identity_provider, mapping, **kwargs):
        """Create federation protocol object and tie to the Identity Provider.

        Utilize Identity API operation:
        PUT /OS-FEDERATION/identity_providers/
        $identity_provider/protocols/$protocol

        :param protocol_id: a string type parameter identifying a federation
            protocol
        :param identity_provider: a string type parameter identifying an
            Identity Provider
        :param mapping: a base.Resource object with federation mapping id

        """
        return self._build_url_and_put(
            request_body={'mapping_id': base.getid(mapping)},
            identity_provider_id=base.getid(identity_provider),
            protocol_id=protocol_id, **kwargs)

    def get(self, identity_provider, protocol, **kwargs):
        """Fetch federation protocol object tied to the Identity Provider.

        Utilize Identity API operation:
        GET /OS-FEDERATION/identity_providers/
        $identity_provider/protocols/$protocol

        :param identity_provider: a base.Resource type object with Identity
                                  Provider id stored inside
        :param protocol: a base.Resource type object with federation protocol
                         id stored inside

        """
        return super(ProtocolManager, self).get(
            identity_provider_id=base.getid(identity_provider),
            protocol_id=base.getid(protocol), **kwargs)

    def list(self, identity_provider, **kwargs):
        """List all federation protocol objects tied to the Identity Provider.

        Utilize Identity API operation:
        GET /OS-FEDERATION/identity_providers/
        $identity_provider/protocols

        :param identity_provider: a base.Resource type object with Identity
            Provider id stored inside

        """
        return super(ProtocolManager, self).list(
            identity_provider_id=base.getid(identity_provider), **kwargs)

    def update(self, identity_provider, protocol, mapping, **kwargs):
        """Update Protocol object tied to the Identity Provider.

        Utilize Identity API operation:
        PATCH /OS-FEDERATION/identity_providers/
        $identity_provider/protocols/$protocol

        :param identity_provider: a base.Resource type object with Identity
            Provider id stored inside
        :param protocol: a base.Resource type object with federation protocol
            id stored inside
        :param mapping: a base.Resource object with federation mapping id


        """
        return super(ProtocolManager, self).update(
            identity_provider_id=base.getid(identity_provider),
            protocol_id=base.getid(protocol), mapping_id=base.getid(mapping),
            **kwargs)

    def delete(self, identity_provider, protocol):
        """Delete Protocol object tied to the Identity Provider.

        Utilize Identity API operation:
        DELETE /OS-FEDERATION/identity_providers/
        $identity_provider/protocols/$protocol

        :param identity_provider: a base.Resource type object with
            Identity Provider id stored inside
        :param protocol: a base.Resource type object with federation
            protocol id stored inside

        """
        return super(ProtocolManager, self).delete(
            identity_provider_id=base.getid(identity_provider),
            protocol_id=base.getid(protocol))
