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
import logging

from oslo_config import cfg
import six

from keystoneclient import access
from keystoneclient.auth.identity import base
from keystoneclient import exceptions
from keystoneclient import utils

_logger = logging.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class Auth(base.BaseIdentityPlugin):
    """Identity V2 Authentication Plugin.

    :param string auth_url: Identity service endpoint for authorization.
    :param string trust_id: Trust ID for trust scoping.
    :param string tenant_id: Tenant ID for project scoping.
    :param string tenant_name: Tenant name for project scoping.
    :param bool reauthenticate: Allow fetching a new token if the current one
                                is going to expire. (optional) default True
    """

    @classmethod
    def get_options(cls):
        options = super(Auth, cls).get_options()

        options.extend([
            cfg.StrOpt('tenant-id', help='Tenant ID'),
            cfg.StrOpt('tenant-name', help='Tenant Name'),
            cfg.StrOpt('trust-id', help='Trust ID'),
        ])

        return options

    @utils.positional()
    def __init__(self, auth_url,
                 trust_id=None,
                 tenant_id=None,
                 tenant_name=None,
                 reauthenticate=True):
        super(Auth, self).__init__(auth_url=auth_url,
                                   reauthenticate=reauthenticate)

        self.trust_id = trust_id
        self.tenant_id = tenant_id
        self.tenant_name = tenant_name

    def get_auth_ref(self, session, **kwargs):
        headers = {'Accept': 'application/json'}
        url = self.auth_url.rstrip('/') + '/tokens'
        params = {'auth': self.get_auth_data(headers)}

        if self.tenant_id:
            params['auth']['tenantId'] = self.tenant_id
        elif self.tenant_name:
            params['auth']['tenantName'] = self.tenant_name
        if self.trust_id:
            params['auth']['trust_id'] = self.trust_id

        _logger.debug('Making authentication request to %s', url)
        resp = session.post(url, json=params, headers=headers,
                            authenticated=False, log=False)

        try:
            resp_data = resp.json()['access']
        except (KeyError, ValueError):
            raise exceptions.InvalidResponse(response=resp)

        return access.AccessInfoV2(**resp_data)

    @abc.abstractmethod
    def get_auth_data(self, headers=None):
        """Return the authentication section of an auth plugin.

        :param dict headers: The headers that will be sent with the auth
                             request if a plugin needs to add to them.
        :return: A dict of authentication data for the auth type.
        :rtype: dict
        """


_NOT_PASSED = object()


class Password(Auth):
    """A plugin for authenticating with a username and password.

    A username or user_id must be provided.

    :param string auth_url: Identity service endpoint for authorization.
    :param string username: Username for authentication.
    :param string password: Password for authentication.
    :param string user_id: User ID for authentication.
    :param string trust_id: Trust ID for trust scoping.
    :param string tenant_id: Tenant ID for tenant scoping.
    :param string tenant_name: Tenant name for tenant scoping.
    :param bool reauthenticate: Allow fetching a new token if the current one
                                is going to expire. (optional) default True

    :raises TypeError: if a user_id or username is not provided.
    """

    @utils.positional(4)
    def __init__(self, auth_url, username=_NOT_PASSED, password=None,
                 user_id=_NOT_PASSED, **kwargs):
        super(Password, self).__init__(auth_url, **kwargs)

        if username is _NOT_PASSED and user_id is _NOT_PASSED:
            msg = 'You need to specify either a username or user_id'
            raise TypeError(msg)

        if username is _NOT_PASSED:
            username = None
        if user_id is _NOT_PASSED:
            user_id = None

        self.user_id = user_id
        self.username = username
        self.password = password

    def get_auth_data(self, headers=None):
        auth = {'password': self.password}

        if self.username:
            auth['username'] = self.username
        elif self.user_id:
            auth['userId'] = self.user_id

        return {'passwordCredentials': auth}

    @classmethod
    def get_options(cls):
        options = super(Password, cls).get_options()

        options.extend([
            cfg.StrOpt('user-name',
                       dest='username',
                       deprecated_name='username',
                       help='Username to login with'),
            cfg.StrOpt('user-id', help='User ID to longin with'),
            cfg.StrOpt('password', secret=True, help='Password to use'),
        ])

        return options


class Token(Auth):
    """A plugin for authenticating with an existing token.

    :param string auth_url: Identity service endpoint for authorization.
    :param string token: Existing token for authentication.
    :param string tenant_id: Tenant ID for tenant scoping.
    :param string tenant_name: Tenant name for tenant scoping.
    :param string trust_id: Trust ID for trust scoping.
    :param bool reauthenticate: Allow fetching a new token if the current one
                                is going to expire. (optional) default True
    """

    def __init__(self, auth_url, token, **kwargs):
        super(Token, self).__init__(auth_url, **kwargs)
        self.token = token

    def get_auth_data(self, headers=None):
        if headers is not None:
            headers['X-Auth-Token'] = self.token
        return {'token': {'id': self.token}}

    @classmethod
    def get_options(cls):
        options = super(Token, cls).get_options()

        options.extend([
            cfg.StrOpt('token', secret=True, help='Token'),
        ])

        return options
