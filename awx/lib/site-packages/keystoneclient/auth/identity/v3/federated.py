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

import abc

from oslo_config import cfg
import six

from keystoneclient.auth.identity.v3 import base
from keystoneclient.auth.identity.v3 import token

__all__ = ['FederatedBaseAuth']


@six.add_metaclass(abc.ABCMeta)
class FederatedBaseAuth(base.BaseAuth):

    rescoping_plugin = token.Token

    def __init__(self, auth_url, identity_provider, protocol, **kwargs):
        """Class constructor accepting following parameters:

        :param auth_url: URL of the Identity Service
        :type auth_url: string
        :param identity_provider: name of the Identity Provider the client
                                  will authenticate against. This parameter
                                  will be used to build a dynamic URL used to
                                  obtain unscoped OpenStack token.
        :type identity_provider: string

        """
        super(FederatedBaseAuth, self).__init__(auth_url=auth_url, **kwargs)
        self.identity_provider = identity_provider
        self.protocol = protocol

    @classmethod
    def get_options(cls):
        options = super(FederatedBaseAuth, cls).get_options()

        options.extend([
            cfg.StrOpt('identity-provider',
                       help="Identity Provider's name"),
            cfg.StrOpt('protocol',
                       help='Protocol for federated plugin'),
        ])

        return options

    @property
    def federated_token_url(self):
        """Full URL where authorization data is sent."""
        values = {
            'host': self.auth_url.rstrip('/'),
            'identity_provider': self.identity_provider,
            'protocol': self.protocol
        }
        url = ("%(host)s/OS-FEDERATION/identity_providers/"
               "%(identity_provider)s/protocols/%(protocol)s/auth")
        url = url % values

        return url

    def _get_scoping_data(self):
        return {'trust_id': self.trust_id,
                'domain_id': self.domain_id,
                'domain_name': self.domain_name,
                'project_id': self.project_id,
                'project_name': self.project_name,
                'project_domain_id': self.project_domain_id,
                'project_domain_name': self.project_domain_name}

    def get_auth_ref(self, session, **kwargs):
        """Authenticate retrieve token information.

        This is a multi-step process where a client does federated authn
        receives an unscoped token.

        If an unscoped token is successfully received and scoping information
        is present then the token is rescoped to that target.

        :param session: a session object to send out HTTP requests.
        :type session: keystoneclient.session.Session

        :returns: a token data representation
        :rtype: :py:class:`keystoneclient.access.AccessInfo`

        """
        auth_ref = self.get_unscoped_auth_ref(session)
        scoping = self._get_scoping_data()

        if any(scoping.values()):
            token_plugin = self.rescoping_plugin(self.auth_url,
                                                 token=auth_ref.auth_token,
                                                 **scoping)

            auth_ref = token_plugin.get_auth_ref(session)

        return auth_ref

    @abc.abstractmethod
    def get_unscoped_auth_ref(self, session, **kwargs):
        """Fetch unscoped federated token."""
