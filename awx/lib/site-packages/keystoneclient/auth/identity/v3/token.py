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

from oslo_config import cfg

from keystoneclient.auth.identity.v3 import base


__all__ = ['TokenMethod', 'Token']


class TokenMethod(base.AuthMethod):
    """Construct an Auth plugin to fetch a token from a token.

    :param string token: Token for authentication.
    """

    _method_parameters = ['token']

    def get_auth_data(self, session, auth, headers, **kwargs):
        headers['X-Auth-Token'] = self.token
        return 'token', {'id': self.token}


class Token(base.AuthConstructor):
    """A plugin for authenticating with an existing Token.

    :param string auth_url: Identity service endpoint for authentication.
    :param string token: Token for authentication.
    :param string trust_id: Trust ID for trust scoping.
    :param string domain_id: Domain ID for domain scoping.
    :param string domain_name: Domain name for domain scoping.
    :param string project_id: Project ID for project scoping.
    :param string project_name: Project name for project scoping.
    :param string project_domain_id: Project's domain ID for project.
    :param string project_domain_name: Project's domain name for project.
    :param bool reauthenticate: Allow fetching a new token if the current one
                                is going to expire. (optional) default True
    """

    _auth_method_class = TokenMethod

    def __init__(self, auth_url, token, **kwargs):
        super(Token, self).__init__(auth_url, token=token, **kwargs)

    @classmethod
    def get_options(cls):
        options = super(Token, cls).get_options()

        options.extend([
            cfg.StrOpt('token',
                       secret=True,
                       help='Token to authenticate with'),
        ])

        return options
