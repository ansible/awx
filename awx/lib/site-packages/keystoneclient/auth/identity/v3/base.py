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
from keystoneclient.i18n import _
from keystoneclient import utils

_logger = logging.getLogger(__name__)

__all__ = ['Auth', 'AuthMethod', 'AuthConstructor', 'BaseAuth']


@six.add_metaclass(abc.ABCMeta)
class BaseAuth(base.BaseIdentityPlugin):
    """Identity V3 Authentication Plugin.

    :param string auth_url: Identity service endpoint for authentication.
    :param list auth_methods: A collection of methods to authenticate with.
    :param string trust_id: Trust ID for trust scoping.
    :param string domain_id: Domain ID for domain scoping.
    :param string domain_name: Domain name for domain scoping.
    :param string project_id: Project ID for project scoping.
    :param string project_name: Project name for project scoping.
    :param string project_domain_id: Project's domain ID for project.
    :param string project_domain_name: Project's domain name for project.
    :param bool reauthenticate: Allow fetching a new token if the current one
                                is going to expire. (optional) default True
    :param bool include_catalog: Include the service catalog in the returned
                                 token. (optional) default True.
    """

    @utils.positional()
    def __init__(self, auth_url,
                 trust_id=None,
                 domain_id=None,
                 domain_name=None,
                 project_id=None,
                 project_name=None,
                 project_domain_id=None,
                 project_domain_name=None,
                 reauthenticate=True,
                 include_catalog=True):
        super(BaseAuth, self).__init__(auth_url=auth_url,
                                       reauthenticate=reauthenticate)
        self.trust_id = trust_id
        self.domain_id = domain_id
        self.domain_name = domain_name
        self.project_id = project_id
        self.project_name = project_name
        self.project_domain_id = project_domain_id
        self.project_domain_name = project_domain_name
        self.include_catalog = include_catalog

    @property
    def token_url(self):
        """The full URL where we will send authentication data."""
        return '%s/auth/tokens' % self.auth_url.rstrip('/')

    @abc.abstractmethod
    def get_auth_ref(self, session, **kwargs):
        return None

    @classmethod
    def get_options(cls):
        options = super(BaseAuth, cls).get_options()

        options.extend([
            cfg.StrOpt('domain-id', help='Domain ID to scope to'),
            cfg.StrOpt('domain-name', help='Domain name to scope to'),
            cfg.StrOpt('project-id', help='Project ID to scope to'),
            cfg.StrOpt('project-name', help='Project name to scope to'),
            cfg.StrOpt('project-domain-id',
                       help='Domain ID containing project'),
            cfg.StrOpt('project-domain-name',
                       help='Domain name containing project'),
            cfg.StrOpt('trust-id', help='Trust ID'),
        ])

        return options


class Auth(BaseAuth):
    """Identity V3 Authentication Plugin.

    :param string auth_url: Identity service endpoint for authentication.
    :param list auth_methods: A collection of methods to authenticate with.
    :param string trust_id: Trust ID for trust scoping.
    :param string domain_id: Domain ID for domain scoping.
    :param string domain_name: Domain name for domain scoping.
    :param string project_id: Project ID for project scoping.
    :param string project_name: Project name for project scoping.
    :param string project_domain_id: Project's domain ID for project.
    :param string project_domain_name: Project's domain name for project.
    :param bool reauthenticate: Allow fetching a new token if the current one
                                is going to expire. (optional) default True
    :param bool include_catalog: Include the service catalog in the returned
                                 token. (optional) default True.
    """

    def __init__(self, auth_url, auth_methods, **kwargs):
        super(Auth, self).__init__(auth_url=auth_url, **kwargs)
        self.auth_methods = auth_methods

    def get_auth_ref(self, session, **kwargs):
        headers = {'Accept': 'application/json'}
        body = {'auth': {'identity': {}}}
        ident = body['auth']['identity']
        rkwargs = {}

        for method in self.auth_methods:
            name, auth_data = method.get_auth_data(session,
                                                   self,
                                                   headers,
                                                   request_kwargs=rkwargs)
            ident.setdefault('methods', []).append(name)
            ident[name] = auth_data

        if not ident:
            raise exceptions.AuthorizationFailure(
                _('Authentication method required (e.g. password)'))

        mutual_exclusion = [bool(self.domain_id or self.domain_name),
                            bool(self.project_id or self.project_name),
                            bool(self.trust_id)]

        if sum(mutual_exclusion) > 1:
            raise exceptions.AuthorizationFailure(
                _('Authentication cannot be scoped to multiple targets. Pick '
                  'one of: project, domain or trust'))

        if self.domain_id:
            body['auth']['scope'] = {'domain': {'id': self.domain_id}}
        elif self.domain_name:
            body['auth']['scope'] = {'domain': {'name': self.domain_name}}
        elif self.project_id:
            body['auth']['scope'] = {'project': {'id': self.project_id}}
        elif self.project_name:
            scope = body['auth']['scope'] = {'project': {}}
            scope['project']['name'] = self.project_name

            if self.project_domain_id:
                scope['project']['domain'] = {'id': self.project_domain_id}
            elif self.project_domain_name:
                scope['project']['domain'] = {'name': self.project_domain_name}
        elif self.trust_id:
            body['auth']['scope'] = {'OS-TRUST:trust': {'id': self.trust_id}}

        # NOTE(jamielennox): we add nocatalog here rather than in token_url
        # directly as some federation plugins require the base token_url
        token_url = self.token_url
        if not self.include_catalog:
            token_url += '?nocatalog'

        _logger.debug('Making authentication request to %s', token_url)
        resp = session.post(token_url, json=body, headers=headers,
                            authenticated=False, log=False, **rkwargs)

        try:
            resp_data = resp.json()['token']
        except (KeyError, ValueError):
            raise exceptions.InvalidResponse(response=resp)

        return access.AccessInfoV3(resp.headers['X-Subject-Token'],
                                   **resp_data)


@six.add_metaclass(abc.ABCMeta)
class AuthMethod(object):
    """One part of a V3 Authentication strategy.

    V3 Tokens allow multiple methods to be presented when authentication
    against the server. Each one of these methods is implemented by an
    AuthMethod.

    Note: When implementing an AuthMethod use the method_parameters
    and do not use positional arguments. Otherwise they can't be picked up by
    the factory method and don't work as well with AuthConstructors.
    """

    _method_parameters = []

    def __init__(self, **kwargs):
        for param in self._method_parameters:
            setattr(self, param, kwargs.pop(param, None))

        if kwargs:
            msg = _("Unexpected Attributes: %s") % ", ".join(kwargs.keys())
            raise AttributeError(msg)

    @classmethod
    def _extract_kwargs(cls, kwargs):
        """Remove parameters related to this method from other kwargs."""
        return dict([(p, kwargs.pop(p, None))
                     for p in cls._method_parameters])

    @abc.abstractmethod
    def get_auth_data(self, session, auth, headers, **kwargs):
        """Return the authentication section of an auth plugin.

        :param session: The communication session.
        :type session: keystoneclient.session.Session
        :param Auth auth: The auth plugin calling the method.
        :param dict headers: The headers that will be sent with the auth
                             request if a plugin needs to add to them.
        :return: The identifier of this plugin and a dict of authentication
                 data for the auth type.
        :rtype: tuple(string, dict)
        """


@six.add_metaclass(abc.ABCMeta)
class AuthConstructor(Auth):
    """AuthConstructor is a means of creating an Auth Plugin that contains
    only one authentication method. This is generally the required usage.

    An AuthConstructor creates an AuthMethod based on the method's
    arguments and the auth_method_class defined by the plugin. It then
    creates the auth plugin with only that authentication method.
    """

    _auth_method_class = None

    def __init__(self, auth_url, *args, **kwargs):
        method_kwargs = self._auth_method_class._extract_kwargs(kwargs)
        method = self._auth_method_class(*args, **method_kwargs)
        super(AuthConstructor, self).__init__(auth_url, [method], **kwargs)
