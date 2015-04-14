# Copyright 2011 Nebula, Inc.
# All Rights Reserved.
#
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

import logging

from oslo_serialization import jsonutils

from keystoneclient.auth.identity import v3 as v3_auth
from keystoneclient import exceptions
from keystoneclient import httpclient
from keystoneclient.i18n import _
from keystoneclient.v3.contrib import endpoint_filter
from keystoneclient.v3.contrib import endpoint_policy
from keystoneclient.v3.contrib import federation
from keystoneclient.v3.contrib import oauth1
from keystoneclient.v3.contrib import simple_cert
from keystoneclient.v3.contrib import trusts
from keystoneclient.v3 import credentials
from keystoneclient.v3 import domains
from keystoneclient.v3 import endpoints
from keystoneclient.v3 import groups
from keystoneclient.v3 import policies
from keystoneclient.v3 import projects
from keystoneclient.v3 import regions
from keystoneclient.v3 import role_assignments
from keystoneclient.v3 import roles
from keystoneclient.v3 import services
from keystoneclient.v3 import tokens
from keystoneclient.v3 import users


_logger = logging.getLogger(__name__)


class Client(httpclient.HTTPClient):
    """Client for the OpenStack Identity API v3.

    :param string user_id: User ID for authentication. (optional)
    :param string username: Username for authentication. (optional)
    :param string user_domain_id: User's domain ID for authentication.
                                  (optional)
    :param string user_domain_name: User's domain name for authentication.
                                    (optional)
    :param string password: Password for authentication. (optional)
    :param string token: Token for authentication. (optional)
    :param string domain_id: Domain ID for domain scoping. (optional)
    :param string domain_name: Domain name for domain scoping. (optional)
    :param string project_id: Project ID for project scoping. (optional)
    :param string project_name: Project name for project scoping. (optional)
    :param string project_domain_id: Project's domain ID for project
                                     scoping. (optional)
    :param string project_domain_name: Project's domain name for project
                                       scoping. (optional)
    :param string tenant_name: Tenant name. (optional)
                               The tenant_name keyword argument is deprecated,
                               use project_name instead.
    :param string tenant_id: Tenant id. (optional)
                             The tenant_id keyword argument is deprecated,
                             use project_id instead.
    :param string auth_url: Identity service endpoint for authorization.
    :param string region_name: Name of a region to select when choosing an
                               endpoint from the service catalog.
    :param string endpoint: A user-supplied endpoint URL for the identity
                            service.  Lazy-authentication is possible for API
                            service calls if endpoint is set at
                            instantiation. (optional)
    :param integer timeout: Allows customization of the timeout for client
                            http requests. (optional)

    Example::

        >>> from keystoneclient.v3 import client
        >>> keystone = client.Client(user_domain_name=DOMAIN_NAME,
        ...                          username=USER,
        ...                          password=PASS,
        ...                          project_domain_name=PROJECT_DOMAIN_NAME,
        ...                          project_name=PROJECT_NAME,
        ...                          auth_url=KEYSTONE_URL)
        ...
        >>> keystone.projects.list()
        ...
        >>> user = keystone.users.get(USER_ID)
        >>> user.delete()

    Instances of this class have the following managers:

    .. py:attribute:: credentials

        :py:class:`keystoneclient.v3.credentials.CredentialManager`

    .. py:attribute:: endpoint_filter

        :py:class:`keystoneclient.v3.contrib.endpoint_filter.\
EndpointFilterManager`

    .. py:attribute:: endpoint_policy

        :py:class:`keystoneclient.v3.contrib.endpoint_policy.\
EndpointPolicyManager`

    .. py:attribute:: endpoints

        :py:class:`keystoneclient.v3.endpoints.EndpointManager`

    .. py:attribute:: domains

        :py:class:`keystoneclient.v3.domains.DomainManager`

    .. py:attribute:: federation

        :py:class:`keystoneclient.v3.contrib.federation.core.FederationManager`

    .. py:attribute:: groups

        :py:class:`keystoneclient.v3.groups.GroupManager`

    .. py:attribute:: oauth1

        :py:class:`keystoneclient.v3.contrib.oauth1.core.OAuthManager`

    .. py:attribute:: policies

        :py:class:`keystoneclient.v3.policies.PolicyManager`

    .. py:attribute:: regions

        :py:class:`keystoneclient.v3.regions.RegionManager`

    .. py:attribute:: role_assignments

        :py:class:`keystoneclient.v3.role_assignments.RoleAssignmentManager`

    .. py:attribute:: roles

        :py:class:`keystoneclient.v3.roles.RoleManager`

    .. py:attribute:: simple_cert

        :py:class:`keystoneclient.v3.contrib.simple_cert.SimpleCertManager`

    .. py:attribute:: services

        :py:class:`keystoneclient.v3.services.ServiceManager`

    .. py:attribute:: tokens

        :py:class:`keystoneclient.v3.tokens.TokenManager`

    .. py:attribute:: trusts

        :py:class:`keystoneclient.v3.contrib.trusts.TrustManager`

    .. py:attribute:: users

        :py:class:`keystoneclient.v3.users.UserManager`

    """

    version = 'v3'

    def __init__(self, **kwargs):
        """Initialize a new client for the Keystone v3 API."""
        super(Client, self).__init__(**kwargs)

        self.credentials = credentials.CredentialManager(self._adapter)
        self.endpoint_filter = endpoint_filter.EndpointFilterManager(
            self._adapter)
        self.endpoint_policy = endpoint_policy.EndpointPolicyManager(
            self._adapter)
        self.endpoints = endpoints.EndpointManager(self._adapter)
        self.domains = domains.DomainManager(self._adapter)
        self.federation = federation.FederationManager(self._adapter)
        self.groups = groups.GroupManager(self._adapter)
        self.oauth1 = oauth1.create_oauth_manager(self._adapter)
        self.policies = policies.PolicyManager(self._adapter)
        self.projects = projects.ProjectManager(self._adapter)
        self.regions = regions.RegionManager(self._adapter)
        self.role_assignments = (
            role_assignments.RoleAssignmentManager(self._adapter))
        self.roles = roles.RoleManager(self._adapter)
        self.services = services.ServiceManager(self._adapter)
        self.simple_cert = simple_cert.SimpleCertManager(self._adapter)
        self.tokens = tokens.TokenManager(self._adapter)
        self.trusts = trusts.TrustManager(self._adapter)
        self.users = users.UserManager(self._adapter)

        # DEPRECATED: if session is passed then we go to the new behaviour of
        # authenticating on the first required call.
        if 'session' not in kwargs and self.management_url is None:
            self.authenticate()

    def serialize(self, entity):
        return jsonutils.dumps(entity, sort_keys=True)

    def process_token(self, **kwargs):
        """Extract and process information from the new auth_ref.

        And set the relevant authentication information.
        """
        super(Client, self).process_token(**kwargs)
        if self.auth_ref.domain_scoped:
            if not self.auth_ref.domain_id:
                raise exceptions.AuthorizationFailure(
                    _("Token didn't provide domain_id"))
            self._process_management_url(kwargs.get('region_name'))
            self.domain_name = self.auth_ref.domain_name
            self.domain_id = self.auth_ref.domain_id
        if self._management_url:
            self._management_url = self._management_url.replace('/v2.0', '/v3')

    def get_raw_token_from_identity_service(self, auth_url, user_id=None,
                                            username=None,
                                            user_domain_id=None,
                                            user_domain_name=None,
                                            password=None,
                                            domain_id=None, domain_name=None,
                                            project_id=None, project_name=None,
                                            project_domain_id=None,
                                            project_domain_name=None,
                                            token=None,
                                            trust_id=None,
                                            **kwargs):
        """Authenticate against the v3 Identity API.

        If password and token methods are both provided then both methods will
        be used in the request.

        :returns: access.AccessInfo if authentication was successful.
        :raises keystoneclient.exceptions.AuthorizationFailure: if unable to
            authenticate or validate the existing authorization token.
        :raises keystoneclient.exceptions.Unauthorized: if authentication fails
            due to invalid token.

        """
        try:
            if auth_url is None:
                raise ValueError(_("Cannot authenticate without an auth_url"))

            auth_methods = []

            if token:
                auth_methods.append(v3_auth.TokenMethod(token=token))

            if password:
                m = v3_auth.PasswordMethod(user_id=user_id,
                                           username=username,
                                           user_domain_id=user_domain_id,
                                           user_domain_name=user_domain_name,
                                           password=password)
                auth_methods.append(m)

            if not auth_methods:
                msg = _('A user and password or token is required.')
                raise exceptions.AuthorizationFailure(msg)

            plugin = v3_auth.Auth(auth_url, auth_methods,
                                  trust_id=trust_id,
                                  domain_id=domain_id,
                                  domain_name=domain_name,
                                  project_id=project_id,
                                  project_name=project_name,
                                  project_domain_id=project_domain_id,
                                  project_domain_name=project_domain_name)

            return plugin.get_auth_ref(self.session)
        except (exceptions.AuthorizationFailure, exceptions.Unauthorized):
            _logger.debug('Authorization failed.')
            raise
        except exceptions.EndpointNotFound:
            msg = _('There was no suitable authentication url for this'
                    ' request')
            raise exceptions.AuthorizationFailure(msg)
        except Exception as e:
            raise exceptions.AuthorizationFailure(
                _('Authorization failed: %s') % e)
