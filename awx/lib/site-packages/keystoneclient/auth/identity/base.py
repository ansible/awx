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

from keystoneclient import _discover
from keystoneclient.auth import base
from keystoneclient import exceptions
from keystoneclient.i18n import _LW
from keystoneclient import utils

LOG = logging.getLogger(__name__)


def get_options():
    return [
        cfg.StrOpt('auth-url', help='Authentication URL'),
    ]


@six.add_metaclass(abc.ABCMeta)
class BaseIdentityPlugin(base.BaseAuthPlugin):

    # we count a token as valid if it is valid for at least this many seconds
    MIN_TOKEN_LIFE_SECONDS = 1

    def __init__(self,
                 auth_url=None,
                 username=None,
                 password=None,
                 token=None,
                 trust_id=None,
                 reauthenticate=True):

        super(BaseIdentityPlugin, self).__init__()

        self.auth_url = auth_url
        self.auth_ref = None
        self.reauthenticate = reauthenticate

        self._endpoint_cache = {}

        # NOTE(jamielennox): DEPRECATED. The following should not really be set
        # here but handled by the individual auth plugin.
        self.username = username
        self.password = password
        self.token = token
        self.trust_id = trust_id

    @abc.abstractmethod
    def get_auth_ref(self, session, **kwargs):
        """Obtain a token from an OpenStack Identity Service.

        This method is overridden by the various token version plugins.

        This function should not be called independently and is expected to be
        invoked via the do_authenticate function.

        This function will be invoked if the AcessInfo object cached by the
        plugin is not valid. Thus plugins should always fetch a new AccessInfo
        when invoked. If you are looking to just retrieve the current auth
        data then you should use get_access.

        :param session: A session object that can be used for communication.
        :type session: keystoneclient.session.Session

        :raises keystoneclient.exceptions.InvalidResponse: The response
                                                           returned wasn't
                                                           appropriate.
        :raises keystoneclient.exceptions.HttpError: An error from an invalid
                                                     HTTP response.

        :returns: Token access information.
        :rtype: :py:class:`keystoneclient.access.AccessInfo`
        """

    def get_token(self, session, **kwargs):
        """Return a valid auth token.

        If a valid token is not present then a new one will be fetched.

        :param session: A session object that can be used for communication.
        :type session: keystoneclient.session.Session

        :raises keystoneclient.exceptions.HttpError: An error from an invalid
                                                     HTTP response.

        :return: A valid token.
        :rtype: string
        """
        return self.get_access(session).auth_token

    def _needs_reauthenticate(self):
        """Return if the existing token needs to be re-authenticated.

        The token should be refreshed if it is about to expire.

        :returns: True if the plugin should fetch a new token. False otherwise.
        """
        if not self.auth_ref:
            # authentication was never fetched.
            return True

        if not self.reauthenticate:
            # don't re-authenticate if it has been disallowed.
            return False

        if self.auth_ref.will_expire_soon(self.MIN_TOKEN_LIFE_SECONDS):
            # if it's about to expire we should re-authenticate now.
            return True

        # otherwise it's fine and use the existing one.
        return False

    def get_access(self, session, **kwargs):
        """Fetch or return a current AccessInfo object.

        If a valid AccessInfo is present then it is returned otherwise a new
        one will be fetched.

        :param session: A session object that can be used for communication.
        :type session: keystoneclient.session.Session

        :raises keystoneclient.exceptions.HttpError: An error from an invalid
                                                     HTTP response.

        :returns: Valid AccessInfo
        :rtype: :py:class:`keystoneclient.access.AccessInfo`
        """
        if self._needs_reauthenticate():
            self.auth_ref = self.get_auth_ref(session)

        return self.auth_ref

    def invalidate(self):
        """Invalidate the current authentication data.

        This should result in fetching a new token on next call.

        A plugin may be invalidated if an Unauthorized HTTP response is
        returned to indicate that the token may have been revoked or is
        otherwise now invalid.

        :returns: True if there was something that the plugin did to
                  invalidate. This means that it makes sense to try again. If
                  nothing happens returns False to indicate give up.
        :rtype: bool
        """
        if self.auth_ref:
            self.auth_ref = None
            return True

        return False

    def get_endpoint(self, session, service_type=None, interface=None,
                     region_name=None, service_name=None, version=None,
                     **kwargs):
        """Return a valid endpoint for a service.

        If a valid token is not present then a new one will be fetched using
        the session and kwargs.

        :param session: A session object that can be used for communication.
        :type session: keystoneclient.session.Session
        :param string service_type: The type of service to lookup the endpoint
                                    for. This plugin will return None (failure)
                                    if service_type is not provided.
        :param string interface: The exposure of the endpoint. Should be
                                 `public`, `internal`, `admin`, or `auth`.
                                 `auth` is special here to use the `auth_url`
                                 rather than a URL extracted from the service
                                 catalog. Defaults to `public`.
        :param string region_name: The region the endpoint should exist in.
                                   (optional)
        :param string service_name: The name of the service in the catalog.
                                   (optional)
        :param tuple version: The minimum version number required for this
                              endpoint. (optional)

        :raises keystoneclient.exceptions.HttpError: An error from an invalid
                                                     HTTP response.

        :return: A valid endpoint URL or None if not available.
        :rtype: string or None
        """
        # NOTE(jamielennox): if you specifically ask for requests to be sent to
        # the auth url then we can ignore the rest of the checks. Typically if
        # you are asking for the auth endpoint it means that there is no
        # catalog to query anyway.
        if interface is base.AUTH_INTERFACE:
            return self.auth_url

        if not service_type:
            LOG.warn(_LW('Plugin cannot return an endpoint without knowing '
                         'the service type that is required. Add service_type '
                         'to endpoint filtering data.'))
            return None

        if not interface:
            interface = 'public'

        service_catalog = self.get_access(session).service_catalog
        url = service_catalog.url_for(service_type=service_type,
                                      endpoint_type=interface,
                                      region_name=region_name,
                                      service_name=service_name)

        if not version:
            # NOTE(jamielennox): This may not be the best thing to default to
            # but is here for backwards compatibility. It may be worth
            # defaulting to the most recent version.
            return url

        # NOTE(jamielennox): For backwards compatibility people might have a
        # versioned endpoint in their catalog even though they want to use
        # other endpoint versions. So we support a list of client defined
        # situations where we can strip the version component from a URL before
        # doing discovery.
        hacked_url = _discover.get_catalog_discover_hack(service_type, url)

        try:
            disc = self.get_discovery(session, hacked_url, authenticated=False)
        except (exceptions.DiscoveryFailure,
                exceptions.HTTPError,
                exceptions.ConnectionError):
            # NOTE(jamielennox): Again if we can't contact the server we fall
            # back to just returning the URL from the catalog. This may not be
            # the best default but we need it for now.
            LOG.warn(_LW('Failed to contact the endpoint at %s for discovery. '
                         'Fallback to using that endpoint as the base url.'),
                     url)
        else:
            url = disc.url_for(version)

        return url

    def get_user_id(self, session, **kwargs):
        return self.get_access(session).user_id

    def get_project_id(self, session, **kwargs):
        return self.get_access(session).project_id

    @utils.positional()
    def get_discovery(self, session, url, authenticated=None):
        """Return the discovery object for a URL.

        Check the session and the plugin cache to see if we have already
        performed discovery on the URL and if so return it, otherwise create
        a new discovery object, cache it and return it.

        This function is expected to be used by subclasses and should not
        be needed by users.

        :param session: A session object to discover with.
        :type session: keystoneclient.session.Session
        :param str url: The url to lookup.
        :param bool authenticated: Include a token in the discovery call.
                                   (optional) Defaults to None (use a token
                                   if a plugin is installed).

        :raises keystoneclient.exceptions.DiscoveryFailure: if for some reason
                                                            the lookup fails.
        :raises keystoneclient.exceptions.HttpError: An error from an invalid
                                                     HTTP response.

        :returns: A discovery object with the results of looking up that URL.
        """
        # NOTE(jamielennox): we want to cache endpoints on the session as well
        # so that they maintain sharing between auth plugins. Create a cache on
        # the session if it doesn't exist already.
        try:
            session_endpoint_cache = session._identity_endpoint_cache
        except AttributeError:
            session_endpoint_cache = session._identity_endpoint_cache = {}

        # NOTE(jamielennox): There is a cache located on both the session
        # object and the auth plugin object so that they can be shared and the
        # cache is still usable
        for cache in (self._endpoint_cache, session_endpoint_cache):
            disc = cache.get(url)

            if disc:
                break
        else:
            disc = _discover.Discover(session, url,
                                      authenticated=authenticated)
            self._endpoint_cache[url] = disc
            session_endpoint_cache[url] = disc

        return disc

    @classmethod
    def get_options(cls):
        options = super(BaseIdentityPlugin, cls).get_options()
        options.extend(get_options())
        return options
