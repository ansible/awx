# Copyright 2010-2012 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
TOKEN-BASED AUTH MIDDLEWARE

.. warning::

  This module is DEPRECATED. The auth_token middleware has been moved to the
  `keystonemiddleware repository
  <http://docs.openstack.org/developer/keystonemiddleware/>`_.

This WSGI component:

* Verifies that incoming client requests have valid tokens by validating
  tokens with the auth service.
* Rejects unauthenticated requests UNLESS it is in 'delay_auth_decision'
  mode, which means the final decision is delegated to the downstream WSGI
  component (usually the OpenStack service)
* Collects and forwards identity information based on a valid token
  such as user name, tenant, etc

HEADERS
-------

* Headers starting with HTTP\_ is a standard http header
* Headers starting with HTTP_X is an extended http header

Coming in from initial call from client or customer
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

HTTP_X_AUTH_TOKEN
    The client token being passed in.

HTTP_X_STORAGE_TOKEN
    The client token being passed in (legacy Rackspace use) to support
    swift/cloud files

Used for communication between components
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

WWW-Authenticate
    HTTP header returned to a user indicating which endpoint to use
    to retrieve a new token

What we add to the request for use by the OpenStack service
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

HTTP_X_IDENTITY_STATUS
    'Confirmed' or 'Invalid'
    The underlying service will only see a value of 'Invalid' if the Middleware
    is configured to run in 'delay_auth_decision' mode

HTTP_X_DOMAIN_ID
    Identity service managed unique identifier, string. Only present if
    this is a domain-scoped v3 token.

HTTP_X_DOMAIN_NAME
    Unique domain name, string. Only present if this is a domain-scoped
    v3 token.

HTTP_X_PROJECT_ID
    Identity service managed unique identifier, string. Only present if
    this is a project-scoped v3 token, or a tenant-scoped v2 token.

HTTP_X_PROJECT_NAME
    Project name, unique within owning domain, string. Only present if
    this is a project-scoped v3 token, or a tenant-scoped v2 token.

HTTP_X_PROJECT_DOMAIN_ID
    Identity service managed unique identifier of owning domain of
    project, string.  Only present if this is a project-scoped v3 token. If
    this variable is set, this indicates that the PROJECT_NAME can only
    be assumed to be unique within this domain.

HTTP_X_PROJECT_DOMAIN_NAME
    Name of owning domain of project, string. Only present if this is a
    project-scoped v3 token. If this variable is set, this indicates that
    the PROJECT_NAME can only be assumed to be unique within this domain.

HTTP_X_USER_ID
    Identity-service managed unique identifier, string

HTTP_X_USER_NAME
    User identifier, unique within owning domain, string

HTTP_X_USER_DOMAIN_ID
    Identity service managed unique identifier of owning domain of
    user, string. If this variable is set, this indicates that the USER_NAME
    can only be assumed to be unique within this domain.

HTTP_X_USER_DOMAIN_NAME
    Name of owning domain of user, string. If this variable is set, this
    indicates that the USER_NAME can only be assumed to be unique within
    this domain.

HTTP_X_ROLES
    Comma delimited list of case-sensitive role names

HTTP_X_SERVICE_CATALOG
    json encoded keystone service catalog (optional).
    For compatibility reasons this catalog will always be in the V2 catalog
    format even if it is a v3 token.

HTTP_X_TENANT_ID
    *Deprecated* in favor of HTTP_X_PROJECT_ID
    Identity service managed unique identifier, string. For v3 tokens, this
    will be set to the same value as HTTP_X_PROJECT_ID

HTTP_X_TENANT_NAME
    *Deprecated* in favor of HTTP_X_PROJECT_NAME
    Project identifier, unique within owning domain, string. For v3 tokens,
    this will be set to the same value as HTTP_X_PROJECT_NAME

HTTP_X_TENANT
    *Deprecated* in favor of HTTP_X_TENANT_ID and HTTP_X_TENANT_NAME
    Keystone-assigned unique identifier, string. For v3 tokens, this
    will be set to the same value as HTTP_X_PROJECT_ID

HTTP_X_USER
    *Deprecated* in favor of HTTP_X_USER_ID and HTTP_X_USER_NAME
    User name, unique within owning domain, string

HTTP_X_ROLE
    *Deprecated* in favor of HTTP_X_ROLES
    Will contain the same values as HTTP_X_ROLES.

OTHER ENVIRONMENT VARIABLES
---------------------------

keystone.token_info
    Information about the token discovered in the process of
    validation.  This may include extended information returned by the
    Keystone token validation call, as well as basic information about
    the tenant and user.

"""

import contextlib
import datetime
import logging
import os
import stat
import tempfile
import time

import netaddr
from oslo_config import cfg
from oslo_serialization import jsonutils
from oslo_utils import timeutils
import requests
import six
from six.moves import urllib

from keystoneclient import access
from keystoneclient.common import cms
from keystoneclient import exceptions
from keystoneclient.middleware import memcache_crypt
from keystoneclient.openstack.common import memorycache


# alternative middleware configuration in the main application's
# configuration file e.g. in nova.conf
# [keystone_authtoken]
# auth_host = 127.0.0.1
# auth_port = 35357
# auth_protocol = http
# admin_tenant_name = admin
# admin_user = admin
# admin_password = badpassword

# when deploy Keystone auth_token middleware with Swift, user may elect
# to use Swift memcache instead of the local Keystone memcache. Swift memcache
# is passed in from the request environment and its identified by the
# 'swift.cache' key. However it could be different, depending on deployment.
# To use Swift memcache, you must set the 'cache' option to the environment
# key where the Swift cache object is stored.


# NOTE(jamielennox): A number of options below are deprecated however are left
# in the list and only mentioned as deprecated in the help string. This is
# because we have to provide the same deprecation functionality for arguments
# passed in via the conf in __init__ (from paste) and there is no way to test
# that the default value was set or not in CONF.
# Also if we were to remove the options from the CONF list (as typical CONF
# deprecation works) then other projects will not be able to override the
# options via CONF.

opts = [
    cfg.StrOpt('auth_admin_prefix',
               default='',
               help='Prefix to prepend at the beginning of the path. '
                    'Deprecated, use identity_uri.'),
    cfg.StrOpt('auth_host',
               default='127.0.0.1',
               help='Host providing the admin Identity API endpoint. '
                    'Deprecated, use identity_uri.'),
    cfg.IntOpt('auth_port',
               default=35357,
               help='Port of the admin Identity API endpoint. '
                    'Deprecated, use identity_uri.'),
    cfg.StrOpt('auth_protocol',
               default='https',
               help='Protocol of the admin Identity API endpoint '
                    '(http or https). Deprecated, use identity_uri.'),
    cfg.StrOpt('auth_uri',
               default=None,
               # FIXME(dolph): should be default='http://127.0.0.1:5000/v2.0/',
               # or (depending on client support) an unversioned, publicly
               # accessible identity endpoint (see bug 1207517)
               help='Complete public Identity API endpoint'),
    cfg.StrOpt('identity_uri',
               default=None,
               help='Complete admin Identity API endpoint. This should '
                    'specify the unversioned root endpoint '
                    'e.g. https://localhost:35357/'),
    cfg.StrOpt('auth_version',
               default=None,
               help='API version of the admin Identity API endpoint'),
    cfg.BoolOpt('delay_auth_decision',
                default=False,
                help='Do not handle authorization requests within the'
                ' middleware, but delegate the authorization decision to'
                ' downstream WSGI components'),
    cfg.BoolOpt('http_connect_timeout',
                default=None,
                help='Request timeout value for communicating with Identity'
                ' API server.'),
    cfg.IntOpt('http_request_max_retries',
               default=3,
               help='How many times are we trying to reconnect when'
               ' communicating with Identity API Server.'),
    cfg.StrOpt('admin_token',
               secret=True,
               help='This option is deprecated and may be removed in a future'
               ' release. Single shared secret with the Keystone configuration'
               ' used for bootstrapping a Keystone installation, or otherwise'
               ' bypassing the normal authentication process. This option'
               ' should not be used, use `admin_user` and `admin_password`'
               ' instead.'),
    cfg.StrOpt('admin_user',
               help='Keystone account username'),
    cfg.StrOpt('admin_password',
               secret=True,
               help='Keystone account password'),
    cfg.StrOpt('admin_tenant_name',
               default='admin',
               help='Keystone service account tenant name to validate'
               ' user tokens'),
    cfg.StrOpt('cache',
               default=None,
               help='Env key for the swift cache'),
    cfg.StrOpt('certfile',
               help='Required if Keystone server requires client certificate'),
    cfg.StrOpt('keyfile',
               help='Required if Keystone server requires client certificate'),
    cfg.StrOpt('cafile', default=None,
               help='A PEM encoded Certificate Authority to use when '
                    'verifying HTTPs connections. Defaults to system CAs.'),
    cfg.BoolOpt('insecure', default=False, help='Verify HTTPS connections.'),
    cfg.StrOpt('signing_dir',
               help='Directory used to cache files related to PKI tokens'),
    cfg.ListOpt('memcached_servers',
                deprecated_name='memcache_servers',
                help='Optionally specify a list of memcached server(s) to'
                ' use for caching. If left undefined, tokens will instead be'
                ' cached in-process.'),
    cfg.IntOpt('token_cache_time',
               default=300,
               help='In order to prevent excessive effort spent validating'
               ' tokens, the middleware caches previously-seen tokens for a'
               ' configurable duration (in seconds). Set to -1 to disable'
               ' caching completely.'),
    cfg.IntOpt('revocation_cache_time',
               default=10,
               help='Determines the frequency at which the list of revoked'
               ' tokens is retrieved from the Identity service (in seconds). A'
               ' high number of revocation events combined with a low cache'
               ' duration may significantly reduce performance.'),
    cfg.StrOpt('memcache_security_strategy',
               default=None,
               help='(optional) if defined, indicate whether token data'
               ' should be authenticated or authenticated and encrypted.'
               ' Acceptable values are MAC or ENCRYPT.  If MAC, token data is'
               ' authenticated (with HMAC) in the cache. If ENCRYPT, token'
               ' data is encrypted and authenticated in the cache. If the'
               ' value is not one of these options or empty, auth_token will'
               ' raise an exception on initialization.'),
    cfg.StrOpt('memcache_secret_key',
               default=None,
               secret=True,
               help='(optional, mandatory if memcache_security_strategy is'
               ' defined) this string is used for key derivation.'),
    cfg.BoolOpt('include_service_catalog',
                default=True,
                help='(optional) indicate whether to set the X-Service-Catalog'
                ' header. If False, middleware will not ask for service'
                ' catalog on token validation and will not set the'
                ' X-Service-Catalog header.'),
    cfg.StrOpt('enforce_token_bind',
               default='permissive',
               help='Used to control the use and type of token binding. Can'
               ' be set to: "disabled" to not check token binding.'
               ' "permissive" (default) to validate binding information if the'
               ' bind type is of a form known to the server and ignore it if'
               ' not. "strict" like "permissive" but if the bind type is'
               ' unknown the token will be rejected. "required" any form of'
               ' token binding is needed to be allowed. Finally the name of a'
               ' binding method that must be present in tokens.'),
    cfg.BoolOpt('check_revocations_for_cached', default=False,
                help='If true, the revocation list will be checked for cached'
                ' tokens. This requires that PKI tokens are configured on the'
                ' Keystone server.'),
    cfg.ListOpt('hash_algorithms', default=['md5'],
                help='Hash algorithms to use for hashing PKI tokens. This may'
                ' be a single algorithm or multiple. The algorithms are those'
                ' supported by Python standard hashlib.new(). The hashes will'
                ' be tried in the order given, so put the preferred one first'
                ' for performance. The result of the first hash will be stored'
                ' in the cache. This will typically be set to multiple values'
                ' only while migrating from a less secure algorithm to a more'
                ' secure one. Once all the old tokens are expired this option'
                ' should be set to a single value for better performance.'),
]

CONF = cfg.CONF
CONF.register_opts(opts, group='keystone_authtoken')

LIST_OF_VERSIONS_TO_ATTEMPT = ['v2.0', 'v3.0']
CACHE_KEY_TEMPLATE = 'tokens/%s'


class BIND_MODE(object):
    DISABLED = 'disabled'
    PERMISSIVE = 'permissive'
    STRICT = 'strict'
    REQUIRED = 'required'
    KERBEROS = 'kerberos'


def will_expire_soon(expiry):
    """Determines if expiration is about to occur.

    :param expiry: a datetime of the expected expiration
    :returns: boolean : true if expiration is within 30 seconds
    """
    soon = (timeutils.utcnow() + datetime.timedelta(seconds=30))
    return expiry < soon


def _token_is_v2(token_info):
    return ('access' in token_info)


def _token_is_v3(token_info):
    return ('token' in token_info)


def confirm_token_not_expired(data):
    if not data:
        raise InvalidUserToken('Token authorization failed')
    if _token_is_v2(data):
        timestamp = data['access']['token']['expires']
    elif _token_is_v3(data):
        timestamp = data['token']['expires_at']
    else:
        raise InvalidUserToken('Token authorization failed')
    expires = timeutils.parse_isotime(timestamp)
    expires = timeutils.normalize_time(expires)
    utcnow = timeutils.utcnow()
    if utcnow >= expires:
        raise InvalidUserToken('Token authorization failed')
    return timeutils.isotime(at=expires, subsecond=True)


def _v3_to_v2_catalog(catalog):
    """Convert a catalog to v2 format.

    X_SERVICE_CATALOG must be specified in v2 format. If you get a token
    that is in v3 convert it.
    """
    v2_services = []
    for v3_service in catalog:
        # first copy over the entries we allow for the service
        v2_service = {'type': v3_service['type']}
        try:
            v2_service['name'] = v3_service['name']
        except KeyError:
            pass

        # now convert the endpoints. Because in v3 we specify region per
        # URL not per group we have to collect all the entries of the same
        # region together before adding it to the new service.
        regions = {}
        for v3_endpoint in v3_service.get('endpoints', []):
            region_name = v3_endpoint.get('region')
            try:
                region = regions[region_name]
            except KeyError:
                region = {'region': region_name} if region_name else {}
                regions[region_name] = region

            interface_name = v3_endpoint['interface'].lower() + 'URL'
            region[interface_name] = v3_endpoint['url']

        v2_service['endpoints'] = list(regions.values())
        v2_services.append(v2_service)

    return v2_services


def safe_quote(s):
    """URL-encode strings that are not already URL-encoded."""
    return urllib.parse.quote(s) if s == urllib.parse.unquote(s) else s


def _conf_values_type_convert(conf):
    """Convert conf values into correct type."""
    if not conf:
        return {}
    _opts = {}
    opt_types = dict((o.dest, getattr(o, 'type', str)) for o in opts)
    for k, v in six.iteritems(conf):
        try:
            if v is None:
                _opts[k] = v
            else:
                _opts[k] = opt_types[k](v)
        except KeyError:
            _opts[k] = v
        except ValueError as e:
            raise ConfigurationError(
                'Unable to convert the value of %s option into correct '
                'type: %s' % (k, e))
    return _opts


class InvalidUserToken(Exception):
    pass


class ServiceError(Exception):
    pass


class ConfigurationError(Exception):
    pass


class NetworkError(Exception):
    pass


class MiniResp(object):
    def __init__(self, error_message, env, headers=[]):
        # The HEAD method is unique: it must never return a body, even if
        # it reports an error (RFC-2616 clause 9.4). We relieve callers
        # from varying the error responses depending on the method.
        if env['REQUEST_METHOD'] == 'HEAD':
            self.body = ['']
        else:
            self.body = [error_message]
        self.headers = list(headers)
        self.headers.append(('Content-type', 'text/plain'))


class AuthProtocol(object):
    """Auth Middleware that handles authenticating client calls."""

    def __init__(self, app, conf):
        self.LOG = logging.getLogger(conf.get('log_name', __name__))
        self.LOG.info('Starting keystone auth_token middleware')
        self.LOG.warning(
            'This middleware module is deprecated as of v0.10.0 in favor of '
            'keystonemiddleware.auth_token - please update your WSGI pipeline '
            'to reference the new middleware package.')
        # NOTE(wanghong): If options are set in paste file, all the option
        # values passed into conf are string type. So, we should convert the
        # conf value into correct type.
        self.conf = _conf_values_type_convert(conf)
        self.app = app

        # delay_auth_decision means we still allow unauthenticated requests
        # through and we let the downstream service make the final decision
        self.delay_auth_decision = (self._conf_get('delay_auth_decision') in
                                    (True, 'true', 't', '1', 'on', 'yes', 'y'))

        # where to find the auth service (we use this to validate tokens)
        self.identity_uri = self._conf_get('identity_uri')
        self.auth_uri = self._conf_get('auth_uri')

        # NOTE(jamielennox): it does appear here that our defaults arguments
        # are backwards. We need to do it this way so that we can handle the
        # same deprecation strategy for CONF and the conf variable.
        if not self.identity_uri:
            self.LOG.warning('Configuring admin URI using auth fragments. '
                             'This is deprecated, use \'identity_uri\''
                             ' instead.')

            auth_host = self._conf_get('auth_host')
            auth_port = int(self._conf_get('auth_port'))
            auth_protocol = self._conf_get('auth_protocol')
            auth_admin_prefix = self._conf_get('auth_admin_prefix')

            if netaddr.valid_ipv6(auth_host):
                # Note(dzyu) it is an IPv6 address, so it needs to be wrapped
                # with '[]' to generate a valid IPv6 URL, based on
                # http://www.ietf.org/rfc/rfc2732.txt
                auth_host = '[%s]' % auth_host

            self.identity_uri = '%s://%s:%s' % (auth_protocol, auth_host,
                                                auth_port)
            if auth_admin_prefix:
                self.identity_uri = '%s/%s' % (self.identity_uri,
                                               auth_admin_prefix.strip('/'))
        else:
            self.identity_uri = self.identity_uri.rstrip('/')

        if self.auth_uri is None:
            self.LOG.warning(
                'Configuring auth_uri to point to the public identity '
                'endpoint is required; clients may not be able to '
                'authenticate against an admin endpoint')

            # FIXME(dolph): drop support for this fallback behavior as
            # documented in bug 1207517.
            # NOTE(jamielennox): we urljoin '/' to get just the base URI as
            # this is the original behaviour.
            self.auth_uri = urllib.parse.urljoin(self.identity_uri, '/')
            self.auth_uri = self.auth_uri.rstrip('/')

        # SSL
        self.cert_file = self._conf_get('certfile')
        self.key_file = self._conf_get('keyfile')
        self.ssl_ca_file = self._conf_get('cafile')
        self.ssl_insecure = self._conf_get('insecure')

        # signing
        self.signing_dirname = self._conf_get('signing_dir')
        if self.signing_dirname is None:
            self.signing_dirname = tempfile.mkdtemp(prefix='keystone-signing-')
        self.LOG.info('Using %s as cache directory for signing certificate',
                      self.signing_dirname)
        self.verify_signing_dir()

        val = '%s/signing_cert.pem' % self.signing_dirname
        self.signing_cert_file_name = val
        val = '%s/cacert.pem' % self.signing_dirname
        self.signing_ca_file_name = val
        val = '%s/revoked.pem' % self.signing_dirname
        self.revoked_file_name = val

        # Credentials used to verify this component with the Auth service since
        # validating tokens is a privileged call
        self.admin_token = self._conf_get('admin_token')
        if self.admin_token:
            self.LOG.warning(
                "The admin_token option in the auth_token middleware is "
                "deprecated and should not be used. The admin_user and "
                "admin_password options should be used instead. The "
                "admin_token option may be removed in a future release.")
        self.admin_token_expiry = None
        self.admin_user = self._conf_get('admin_user')
        self.admin_password = self._conf_get('admin_password')
        self.admin_tenant_name = self._conf_get('admin_tenant_name')

        memcache_security_strategy = (
            self._conf_get('memcache_security_strategy'))

        self._token_cache = TokenCache(
            self.LOG,
            cache_time=int(self._conf_get('token_cache_time')),
            hash_algorithms=self._conf_get('hash_algorithms'),
            env_cache_name=self._conf_get('cache'),
            memcached_servers=self._conf_get('memcached_servers'),
            memcache_security_strategy=memcache_security_strategy,
            memcache_secret_key=self._conf_get('memcache_secret_key'))

        self._token_revocation_list = None
        self._token_revocation_list_fetched_time = None
        self.token_revocation_list_cache_timeout = datetime.timedelta(
            seconds=self._conf_get('revocation_cache_time'))
        http_connect_timeout_cfg = self._conf_get('http_connect_timeout')
        self.http_connect_timeout = (http_connect_timeout_cfg and
                                     int(http_connect_timeout_cfg))
        self.auth_version = None
        self.http_request_max_retries = (
            self._conf_get('http_request_max_retries'))

        self.include_service_catalog = self._conf_get(
            'include_service_catalog')

        self.check_revocations_for_cached = self._conf_get(
            'check_revocations_for_cached')

    def _conf_get(self, name):
        # try config from paste-deploy first
        if name in self.conf:
            return self.conf[name]
        else:
            return CONF.keystone_authtoken[name]

    def _choose_api_version(self):
        """Determine the api version that we should use."""

        # If the configuration specifies an auth_version we will just
        # assume that is correct and use it.  We could, of course, check
        # that this version is supported by the server, but in case
        # there are some problems in the field, we want as little code
        # as possible in the way of letting auth_token talk to the
        # server.
        if self._conf_get('auth_version'):
            version_to_use = self._conf_get('auth_version')
            self.LOG.info('Auth Token proceeding with requested %s apis',
                          version_to_use)
        else:
            version_to_use = None
            versions_supported_by_server = self._get_supported_versions()
            if versions_supported_by_server:
                for version in LIST_OF_VERSIONS_TO_ATTEMPT:
                    if version in versions_supported_by_server:
                        version_to_use = version
                        break
            if version_to_use:
                self.LOG.info('Auth Token confirmed use of %s apis',
                              version_to_use)
            else:
                self.LOG.error(
                    'Attempted versions [%s] not in list supported by '
                    'server [%s]',
                    ', '.join(LIST_OF_VERSIONS_TO_ATTEMPT),
                    ', '.join(versions_supported_by_server))
                raise ServiceError('No compatible apis supported by server')
        return version_to_use

    def _get_supported_versions(self):
        versions = []
        response, data = self._json_request('GET', '/')
        if response.status_code == 501:
            self.LOG.warning('Old keystone installation found...assuming v2.0')
            versions.append('v2.0')
        elif response.status_code != 300:
            self.LOG.error('Unable to get version info from keystone: %s',
                           response.status_code)
            raise ServiceError('Unable to get version info from keystone')
        else:
            try:
                for version in data['versions']['values']:
                    versions.append(version['id'])
            except KeyError:
                self.LOG.error(
                    'Invalid version response format from server')
                raise ServiceError('Unable to parse version response '
                                   'from keystone')

        self.LOG.debug('Server reports support for api versions: %s',
                       ', '.join(versions))
        return versions

    def __call__(self, env, start_response):
        """Handle incoming request.

        Authenticate send downstream on success. Reject request if
        we can't authenticate.

        """
        self.LOG.debug('Authenticating user token')

        self._token_cache.initialize(env)

        try:
            self._remove_auth_headers(env)
            user_token = self._get_user_token_from_header(env)
            token_info = self._validate_user_token(user_token, env)
            env['keystone.token_info'] = token_info
            user_headers = self._build_user_headers(token_info)
            self._add_headers(env, user_headers)
            return self.app(env, start_response)

        except InvalidUserToken:
            if self.delay_auth_decision:
                self.LOG.info(
                    'Invalid user token - deferring reject downstream')
                self._add_headers(env, {'X-Identity-Status': 'Invalid'})
                return self.app(env, start_response)
            else:
                self.LOG.info('Invalid user token - rejecting request')
                return self._reject_request(env, start_response)

        except ServiceError as e:
            self.LOG.critical('Unable to obtain admin token: %s', e)
            resp = MiniResp('Service unavailable', env)
            start_response('503 Service Unavailable', resp.headers)
            return resp.body

    def _remove_auth_headers(self, env):
        """Remove headers so a user can't fake authentication.

        :param env: wsgi request environment

        """
        auth_headers = (
            'X-Identity-Status',
            'X-Domain-Id',
            'X-Domain-Name',
            'X-Project-Id',
            'X-Project-Name',
            'X-Project-Domain-Id',
            'X-Project-Domain-Name',
            'X-User-Id',
            'X-User-Name',
            'X-User-Domain-Id',
            'X-User-Domain-Name',
            'X-Roles',
            'X-Service-Catalog',
            # Deprecated
            'X-User',
            'X-Tenant-Id',
            'X-Tenant-Name',
            'X-Tenant',
            'X-Role',
        )
        self.LOG.debug('Removing headers from request environment: %s',
                       ','.join(auth_headers))
        self._remove_headers(env, auth_headers)

    def _get_user_token_from_header(self, env):
        """Get token id from request.

        :param env: wsgi request environment
        :return token id
        :raises InvalidUserToken if no token is provided in request

        """
        token = self._get_header(env, 'X-Auth-Token',
                                 self._get_header(env, 'X-Storage-Token'))
        if token:
            return token
        else:
            if not self.delay_auth_decision:
                self.LOG.warn('Unable to find authentication token'
                              ' in headers')
                self.LOG.debug('Headers: %s', env)
            raise InvalidUserToken('Unable to find token in headers')

    def _reject_request(self, env, start_response):
        """Redirect client to auth server.

        :param env: wsgi request environment
        :param start_response: wsgi response callback
        :returns HTTPUnauthorized http response

        """
        headers = [('WWW-Authenticate', 'Keystone uri=\'%s\'' % self.auth_uri)]
        resp = MiniResp('Authentication required', env, headers)
        start_response('401 Unauthorized', resp.headers)
        return resp.body

    def get_admin_token(self):
        """Return admin token, possibly fetching a new one.

        if self.admin_token_expiry is set from fetching an admin token, check
        it for expiration, and request a new token is the existing token
        is about to expire.

        :return admin token id
        :raise ServiceError when unable to retrieve token from keystone

        """
        if self.admin_token_expiry:
            if will_expire_soon(self.admin_token_expiry):
                self.admin_token = None

        if not self.admin_token:
            (self.admin_token,
             self.admin_token_expiry) = self._request_admin_token()

        return self.admin_token

    def _http_request(self, method, path, **kwargs):
        """HTTP request helper used to make unspecified content type requests.

        :param method: http method
        :param path: relative request url
        :return (http response object, response body)
        :raise ServerError when unable to communicate with keystone

        """
        url = '%s/%s' % (self.identity_uri, path.lstrip('/'))

        kwargs.setdefault('timeout', self.http_connect_timeout)
        if self.cert_file and self.key_file:
            kwargs['cert'] = (self.cert_file, self.key_file)
        elif self.cert_file or self.key_file:
            self.LOG.warn('Cannot use only a cert or key file. '
                          'Please provide both. Ignoring.')

        kwargs['verify'] = self.ssl_ca_file or True
        if self.ssl_insecure:
            kwargs['verify'] = False

        RETRIES = self.http_request_max_retries
        retry = 0
        while True:
            try:
                response = requests.request(method, url, **kwargs)
                break
            except Exception as e:
                if retry >= RETRIES:
                    self.LOG.error('HTTP connection exception: %s', e)
                    raise NetworkError('Unable to communicate with keystone')
                # NOTE(vish): sleep 0.5, 1, 2
                self.LOG.warn('Retrying on HTTP connection exception: %s', e)
                time.sleep(2.0 ** retry / 2)
                retry += 1

        return response

    def _json_request(self, method, path, body=None, additional_headers=None):
        """HTTP request helper used to make json requests.

        :param method: http method
        :param path: relative request url
        :param body: dict to encode to json as request body. Optional.
        :param additional_headers: dict of additional headers to send with
                                   http request. Optional.
        :return (http response object, response body parsed as json)
        :raise ServerError when unable to communicate with keystone

        """
        kwargs = {
            'headers': {
                'Content-type': 'application/json',
                'Accept': 'application/json',
            },
        }

        if additional_headers:
            kwargs['headers'].update(additional_headers)

        if body:
            kwargs['data'] = jsonutils.dumps(body)

        response = self._http_request(method, path, **kwargs)

        try:
            data = jsonutils.loads(response.text)
        except ValueError:
            self.LOG.debug('Keystone did not return json-encoded body')
            data = {}

        return response, data

    def _request_admin_token(self):
        """Retrieve new token as admin user from keystone.

        :return token id upon success
        :raises ServerError when unable to communicate with keystone

        Irrespective of the auth version we are going to use for the
        user token, for simplicity we always use a v2 admin token to
        validate the user token.

        """
        params = {
            'auth': {
                'passwordCredentials': {
                    'username': self.admin_user,
                    'password': self.admin_password,
                },
                'tenantName': self.admin_tenant_name,
            }
        }

        response, data = self._json_request('POST',
                                            '/v2.0/tokens',
                                            body=params)

        try:
            token = data['access']['token']['id']
            expiry = data['access']['token']['expires']
            if not (token and expiry):
                raise AssertionError('invalid token or expire')
            datetime_expiry = timeutils.parse_isotime(expiry)
            return (token, timeutils.normalize_time(datetime_expiry))
        except (AssertionError, KeyError):
            self.LOG.warn(
                'Unexpected response from keystone service: %s', data)
            raise ServiceError('invalid json response')
        except (ValueError):
            data['access']['token']['id'] = '<SANITIZED>'
            self.LOG.warn(
                'Unable to parse expiration time from token: %s', data)
            raise ServiceError('invalid json response')

    def _validate_user_token(self, user_token, env, retry=True):
        """Authenticate user token

        :param user_token: user's token id
        :param retry: Ignored, as it is not longer relevant
        :return uncrypted body of the token if the token is valid
        :raise InvalidUserToken if token is rejected
        :no longer raises ServiceError since it no longer makes RPC

        """
        token_id = None

        try:
            token_ids, cached = self._token_cache.get(user_token)
            token_id = token_ids[0]
            if cached:
                data = cached

                if self.check_revocations_for_cached:
                    # A token stored in Memcached might have been revoked
                    # regardless of initial mechanism used to validate it,
                    # and needs to be checked.
                    for tid in token_ids:
                        is_revoked = self._is_token_id_in_revoked_list(tid)
                        if is_revoked:
                            self.LOG.debug(
                                'Token is marked as having been revoked')
                            raise InvalidUserToken(
                                'Token authorization failed')
            elif cms.is_pkiz(user_token):
                verified = self.verify_pkiz_token(user_token, token_ids)
                data = jsonutils.loads(verified)
            elif cms.is_asn1_token(user_token):
                verified = self.verify_signed_token(user_token, token_ids)
                data = jsonutils.loads(verified)
            else:
                data = self.verify_uuid_token(user_token, retry)
            expires = confirm_token_not_expired(data)
            self._confirm_token_bind(data, env)
            self._token_cache.store(token_id, data, expires)
            return data
        except NetworkError:
            self.LOG.debug('Token validation failure.', exc_info=True)
            self.LOG.warn('Authorization failed for token')
            raise InvalidUserToken('Token authorization failed')
        except Exception:
            self.LOG.debug('Token validation failure.', exc_info=True)
            if token_id:
                self._token_cache.store_invalid(token_id)
            self.LOG.warn('Authorization failed for token')
            raise InvalidUserToken('Token authorization failed')

    def _build_user_headers(self, token_info):
        """Convert token object into headers.

        Build headers that represent authenticated user - see main
        doc info at start of file for details of headers to be defined.

        :param token_info: token object returned by keystone on authentication
        :raise InvalidUserToken when unable to parse token object

        """
        auth_ref = access.AccessInfo.factory(body=token_info)
        roles = ','.join(auth_ref.role_names)

        if _token_is_v2(token_info) and not auth_ref.project_id:
            raise InvalidUserToken('Unable to determine tenancy.')

        rval = {
            'X-Identity-Status': 'Confirmed',
            'X-Domain-Id': auth_ref.domain_id,
            'X-Domain-Name': auth_ref.domain_name,
            'X-Project-Id': auth_ref.project_id,
            'X-Project-Name': auth_ref.project_name,
            'X-Project-Domain-Id': auth_ref.project_domain_id,
            'X-Project-Domain-Name': auth_ref.project_domain_name,
            'X-User-Id': auth_ref.user_id,
            'X-User-Name': auth_ref.username,
            'X-User-Domain-Id': auth_ref.user_domain_id,
            'X-User-Domain-Name': auth_ref.user_domain_name,
            'X-Roles': roles,
            # Deprecated
            'X-User': auth_ref.username,
            'X-Tenant-Id': auth_ref.project_id,
            'X-Tenant-Name': auth_ref.project_name,
            'X-Tenant': auth_ref.project_name,
            'X-Role': roles,
        }

        self.LOG.debug('Received request from user: %s with project_id : %s'
                       ' and roles: %s ',
                       auth_ref.user_id, auth_ref.project_id, roles)

        if self.include_service_catalog and auth_ref.has_service_catalog():
            catalog = auth_ref.service_catalog.get_data()
            if _token_is_v3(token_info):
                catalog = _v3_to_v2_catalog(catalog)
            rval['X-Service-Catalog'] = jsonutils.dumps(catalog)

        return rval

    def _header_to_env_var(self, key):
        """Convert header to wsgi env variable.

        :param key: http header name (ex. 'X-Auth-Token')
        :return wsgi env variable name (ex. 'HTTP_X_AUTH_TOKEN')

        """
        return 'HTTP_%s' % key.replace('-', '_').upper()

    def _add_headers(self, env, headers):
        """Add http headers to environment."""
        for (k, v) in six.iteritems(headers):
            env_key = self._header_to_env_var(k)
            env[env_key] = v

    def _remove_headers(self, env, keys):
        """Remove http headers from environment."""
        for k in keys:
            env_key = self._header_to_env_var(k)
            try:
                del env[env_key]
            except KeyError:
                pass

    def _get_header(self, env, key, default=None):
        """Get http header from environment."""
        env_key = self._header_to_env_var(key)
        return env.get(env_key, default)

    def _invalid_user_token(self, msg=False):
        # NOTE(jamielennox): use False as the default so that None is valid
        if msg is False:
            msg = 'Token authorization failed'

        raise InvalidUserToken(msg)

    def _confirm_token_bind(self, data, env):
        bind_mode = self._conf_get('enforce_token_bind')

        if bind_mode == BIND_MODE.DISABLED:
            return

        try:
            if _token_is_v2(data):
                bind = data['access']['token']['bind']
            elif _token_is_v3(data):
                bind = data['token']['bind']
            else:
                self._invalid_user_token()
        except KeyError:
            bind = {}

        # permissive and strict modes don't require there to be a bind
        permissive = bind_mode in (BIND_MODE.PERMISSIVE, BIND_MODE.STRICT)

        if not bind:
            if permissive:
                # no bind provided and none required
                return
            else:
                self.LOG.info('No bind information present in token.')
                self._invalid_user_token()

        # get the named mode if bind_mode is not one of the predefined
        if permissive or bind_mode == BIND_MODE.REQUIRED:
            name = None
        else:
            name = bind_mode

        if name and name not in bind:
            self.LOG.info('Named bind mode %s not in bind information', name)
            self._invalid_user_token()

        for bind_type, identifier in six.iteritems(bind):
            if bind_type == BIND_MODE.KERBEROS:
                if not env.get('AUTH_TYPE', '').lower() == 'negotiate':
                    self.LOG.info('Kerberos credentials required and '
                                  'not present.')
                    self._invalid_user_token()

                if not env.get('REMOTE_USER') == identifier:
                    self.LOG.info('Kerberos credentials do not match '
                                  'those in bind.')
                    self._invalid_user_token()

                self.LOG.debug('Kerberos bind authentication successful.')

            elif bind_mode == BIND_MODE.PERMISSIVE:
                self.LOG.debug('Ignoring Unknown bind for permissive mode: '
                               '%(bind_type)s: %(identifier)s.',
                               {'bind_type': bind_type,
                                'identifier': identifier})

            else:
                self.LOG.info('Couldn`t verify unknown bind: %(bind_type)s: '
                              '%(identifier)s.',
                              {'bind_type': bind_type,
                               'identifier': identifier})
                self._invalid_user_token()

    def verify_uuid_token(self, user_token, retry=True):
        """Authenticate user token with keystone.

        :param user_token: user's token id
        :param retry: flag that forces the middleware to retry
                      user authentication when an indeterminate
                      response is received. Optional.
        :returns: token object received from keystone on success
        :raise InvalidUserToken: if token is rejected
        :raise ServiceError: if unable to authenticate token

        """
        # Determine the highest api version we can use.
        if not self.auth_version:
            self.auth_version = self._choose_api_version()

        if self.auth_version == 'v3.0':
            headers = {'X-Auth-Token': self.get_admin_token(),
                       'X-Subject-Token': safe_quote(user_token)}
            path = '/v3/auth/tokens'
            if not self.include_service_catalog:
                # NOTE(gyee): only v3 API support this option
                path = path + '?nocatalog'
            response, data = self._json_request(
                'GET',
                path,
                additional_headers=headers)
        else:
            headers = {'X-Auth-Token': self.get_admin_token()}
            response, data = self._json_request(
                'GET',
                '/v2.0/tokens/%s' % safe_quote(user_token),
                additional_headers=headers)

        if response.status_code == 200:
            return data
        if response.status_code == 404:
            self.LOG.warn('Authorization failed for token')
            raise InvalidUserToken('Token authorization failed')
        if response.status_code == 401:
            self.LOG.info(
                'Keystone rejected admin token, resetting')
            self.admin_token = None
        else:
            self.LOG.error('Bad response code while validating token: %s',
                           response.status_code)
        if retry:
            self.LOG.info('Retrying validation')
            return self.verify_uuid_token(user_token, False)
        else:
            self.LOG.warn('Invalid user token. Keystone response: %s', data)

            raise InvalidUserToken()

    def is_signed_token_revoked(self, token_ids):
        """Indicate whether the token appears in the revocation list."""
        for token_id in token_ids:
            if self._is_token_id_in_revoked_list(token_id):
                self.LOG.debug('Token is marked as having been revoked')
                return True
        return False

    def _is_token_id_in_revoked_list(self, token_id):
        """Indicate whether the token_id appears in the revocation list."""
        revocation_list = self.token_revocation_list
        revoked_tokens = revocation_list.get('revoked', None)
        if not revoked_tokens:
            return False

        revoked_ids = (x['id'] for x in revoked_tokens)
        return token_id in revoked_ids

    def cms_verify(self, data, inform=cms.PKI_ASN1_FORM):
        """Verifies the signature of the provided data's IAW CMS syntax.

        If either of the certificate files might be missing, fetch them and
        retry.
        """
        def verify():
            try:
                return cms.cms_verify(data, self.signing_cert_file_name,
                                      self.signing_ca_file_name,
                                      inform=inform).decode('utf-8')
            except cms.subprocess.CalledProcessError as err:
                self.LOG.warning('Verify error: %s', err)
                raise

        try:
            return verify()
        except exceptions.CertificateConfigError:
            # the certs might be missing; unconditionally fetch to avoid racing
            self.fetch_signing_cert()
            self.fetch_ca_cert()

            try:
                # retry with certs in place
                return verify()
            except exceptions.CertificateConfigError as err:
                # if this is still occurring, something else is wrong and we
                # need err.output to identify the problem
                self.LOG.error('CMS Verify output: %s', err.output)
                raise

    def verify_signed_token(self, signed_text, token_ids):
        """Check that the token is unrevoked and has a valid signature."""
        if self.is_signed_token_revoked(token_ids):
            raise InvalidUserToken('Token has been revoked')

        formatted = cms.token_to_cms(signed_text)
        verified = self.cms_verify(formatted)
        return verified

    def verify_pkiz_token(self, signed_text, token_ids):
        if self.is_signed_token_revoked(token_ids):
            raise InvalidUserToken('Token has been revoked')
        try:
            uncompressed = cms.pkiz_uncompress(signed_text)
            verified = self.cms_verify(uncompressed, inform=cms.PKIZ_CMS_FORM)
            return verified
        # TypeError If the signed_text is not zlib compressed
        except TypeError:
            raise InvalidUserToken(signed_text)

    def verify_signing_dir(self):
        if os.path.exists(self.signing_dirname):
            if not os.access(self.signing_dirname, os.W_OK):
                raise ConfigurationError(
                    'unable to access signing_dir %s' % self.signing_dirname)
            uid = os.getuid()
            if os.stat(self.signing_dirname).st_uid != uid:
                self.LOG.warning(
                    'signing_dir is not owned by %s', uid)
            current_mode = stat.S_IMODE(os.stat(self.signing_dirname).st_mode)
            if current_mode != stat.S_IRWXU:
                self.LOG.warning(
                    'signing_dir mode is %s instead of %s',
                    oct(current_mode), oct(stat.S_IRWXU))
        else:
            os.makedirs(self.signing_dirname, stat.S_IRWXU)

    @property
    def token_revocation_list_fetched_time(self):
        if not self._token_revocation_list_fetched_time:
            # If the fetched list has been written to disk, use its
            # modification time.
            if os.path.exists(self.revoked_file_name):
                mtime = os.path.getmtime(self.revoked_file_name)
                fetched_time = datetime.datetime.utcfromtimestamp(mtime)
            # Otherwise the list will need to be fetched.
            else:
                fetched_time = datetime.datetime.min
            self._token_revocation_list_fetched_time = fetched_time
        return self._token_revocation_list_fetched_time

    @token_revocation_list_fetched_time.setter
    def token_revocation_list_fetched_time(self, value):
        self._token_revocation_list_fetched_time = value

    @property
    def token_revocation_list(self):
        timeout = (self.token_revocation_list_fetched_time +
                   self.token_revocation_list_cache_timeout)
        list_is_current = timeutils.utcnow() < timeout

        if list_is_current:
            # Load the list from disk if required
            if not self._token_revocation_list:
                open_kwargs = {'encoding': 'utf-8'} if six.PY3 else {}
                with open(self.revoked_file_name, 'r', **open_kwargs) as f:
                    self._token_revocation_list = jsonutils.loads(f.read())
        else:
            self.token_revocation_list = self.fetch_revocation_list()
        return self._token_revocation_list

    def _atomic_write_to_signing_dir(self, file_name, value):
        # In Python2, encoding is slow so the following check avoids it if it
        # is not absolutely necessary.
        if isinstance(value, six.text_type):
            value = value.encode('utf-8')

        def _atomic_write(destination, data):
            with tempfile.NamedTemporaryFile(dir=self.signing_dirname,
                                             delete=False) as f:
                f.write(data)
            os.rename(f.name, destination)

        try:
            _atomic_write(file_name, value)
        except (OSError, IOError):
            self.verify_signing_dir()
            _atomic_write(file_name, value)

    @token_revocation_list.setter
    def token_revocation_list(self, value):
        """Save a revocation list to memory and to disk.

        :param value: A json-encoded revocation list

        """
        self._token_revocation_list = jsonutils.loads(value)
        self.token_revocation_list_fetched_time = timeutils.utcnow()
        self._atomic_write_to_signing_dir(self.revoked_file_name, value)

    def fetch_revocation_list(self, retry=True):
        headers = {'X-Auth-Token': self.get_admin_token()}
        response, data = self._json_request('GET', '/v2.0/tokens/revoked',
                                            additional_headers=headers)
        if response.status_code == 401:
            if retry:
                self.LOG.info(
                    'Keystone rejected admin token, resetting admin token')
                self.admin_token = None
                return self.fetch_revocation_list(retry=False)
        if response.status_code != 200:
            raise ServiceError('Unable to fetch token revocation list.')
        if 'signed' not in data:
            raise ServiceError('Revocation list improperly formatted.')
        return self.cms_verify(data['signed'])

    def _fetch_cert_file(self, cert_file_name, cert_type):
        if not self.auth_version:
            self.auth_version = self._choose_api_version()

        if self.auth_version == 'v3.0':
            if cert_type == 'signing':
                cert_type = 'certificates'
            path = '/v3/OS-SIMPLE-CERT/' + cert_type
        else:
            path = '/v2.0/certificates/' + cert_type
        response = self._http_request('GET', path)
        if response.status_code != 200:
            raise exceptions.CertificateConfigError(response.text)
        self._atomic_write_to_signing_dir(cert_file_name, response.text)

    def fetch_signing_cert(self):
        self._fetch_cert_file(self.signing_cert_file_name, 'signing')

    def fetch_ca_cert(self):
        self._fetch_cert_file(self.signing_ca_file_name, 'ca')


class CachePool(list):
    """A lazy pool of cache references."""

    def __init__(self, cache, memcached_servers):
        self._environment_cache = cache
        self._memcached_servers = memcached_servers

    @contextlib.contextmanager
    def reserve(self):
        """Context manager to manage a pooled cache reference."""
        if self._environment_cache is not None:
            # skip pooling and just use the cache from the upstream filter
            yield self._environment_cache
            return  # otherwise the context manager will continue!

        try:
            c = self.pop()
        except IndexError:
            # the pool is empty, so we need to create a new client
            c = memorycache.get_client(self._memcached_servers)

        try:
            yield c
        finally:
            self.append(c)


class TokenCache(object):
    """Encapsulates the auth_token token cache functionality.

    auth_token caches tokens that it's seen so that when a token is re-used the
    middleware doesn't have to do a more expensive operation (like going to the
    identity server) to validate the token.

    initialize() must be called before calling the other methods.

    Store a valid token in the cache using store(); mark a token as invalid in
    the cache using store_invalid().

    Check if a token is in the cache and retrieve it using get().

    """

    _INVALID_INDICATOR = 'invalid'

    def __init__(self, log, cache_time=None, hash_algorithms=None,
                 env_cache_name=None, memcached_servers=None,
                 memcache_security_strategy=None, memcache_secret_key=None):
        self.LOG = log
        self._cache_time = cache_time
        self._hash_algorithms = hash_algorithms
        self._env_cache_name = env_cache_name
        self._memcached_servers = memcached_servers

        # memcache value treatment, ENCRYPT or MAC
        self._memcache_security_strategy = memcache_security_strategy
        if self._memcache_security_strategy is not None:
            self._memcache_security_strategy = (
                self._memcache_security_strategy.upper())
        self._memcache_secret_key = memcache_secret_key

        self._cache_pool = None
        self._initialized = False

        self._assert_valid_memcache_protection_config()

    def initialize(self, env):
        if self._initialized:
            return

        self._cache_pool = CachePool(env.get(self._env_cache_name),
                                     self._memcached_servers)
        self._initialized = True

    def get(self, user_token):
        """Check if the token is cached already.

        Returns a tuple. The first element is a list of token IDs, where the
        first one is the preferred hash.

        The second element is the token data from the cache if the token was
        cached, otherwise ``None``.

        :raises InvalidUserToken: if the token is invalid

        """

        if cms.is_asn1_token(user_token) or cms.is_pkiz(user_token):
            # user_token is a PKI token that's not hashed.

            token_hashes = list(cms.cms_hash_token(user_token, mode=algo)
                                for algo in self._hash_algorithms)

            for token_hash in token_hashes:
                cached = self._cache_get(token_hash)
                if cached:
                    return (token_hashes, cached)

            # The token wasn't found using any hash algorithm.
            return (token_hashes, None)

        # user_token is either a UUID token or a hashed PKI token.
        token_id = user_token
        cached = self._cache_get(token_id)
        return ([token_id], cached)

    def store(self, token_id, data, expires):
        """Put token data into the cache.

        Stores the parsed expire date in cache allowing
        quick check of token freshness on retrieval.

        """
        self.LOG.debug('Storing token in cache')
        self._cache_store(token_id, (data, expires))

    def store_invalid(self, token_id):
        """Store invalid token in cache."""
        self.LOG.debug('Marking token as unauthorized in cache')
        self._cache_store(token_id, self._INVALID_INDICATOR)

    def _assert_valid_memcache_protection_config(self):
        if self._memcache_security_strategy:
            if self._memcache_security_strategy not in ('MAC', 'ENCRYPT'):
                raise ConfigurationError('memcache_security_strategy must be '
                                         'ENCRYPT or MAC')
            if not self._memcache_secret_key:
                raise ConfigurationError('memcache_secret_key must be defined '
                                         'when a memcache_security_strategy '
                                         'is defined')

    def _cache_get(self, token_id):
        """Return token information from cache.

        If token is invalid raise InvalidUserToken
        return token only if fresh (not expired).
        """

        if not token_id:
            # Nothing to do
            return

        if self._memcache_security_strategy is None:
            key = CACHE_KEY_TEMPLATE % token_id
            with self._cache_pool.reserve() as cache:
                serialized = cache.get(key)
        else:
            secret_key = self._memcache_secret_key
            if isinstance(secret_key, six.string_types):
                secret_key = secret_key.encode('utf-8')
            security_strategy = self._memcache_security_strategy
            if isinstance(security_strategy, six.string_types):
                security_strategy = security_strategy.encode('utf-8')
            keys = memcache_crypt.derive_keys(
                token_id,
                secret_key,
                security_strategy)
            cache_key = CACHE_KEY_TEMPLATE % (
                memcache_crypt.get_cache_key(keys))
            with self._cache_pool.reserve() as cache:
                raw_cached = cache.get(cache_key)
            try:
                # unprotect_data will return None if raw_cached is None
                serialized = memcache_crypt.unprotect_data(keys,
                                                           raw_cached)
            except Exception:
                msg = 'Failed to decrypt/verify cache data'
                self.LOG.exception(msg)
                # this should have the same effect as data not
                # found in cache
                serialized = None

        if serialized is None:
            return None

        # Note that _INVALID_INDICATOR and (data, expires) are the only
        # valid types of serialized cache entries, so there is not
        # a collision with jsonutils.loads(serialized) == None.
        if not isinstance(serialized, six.string_types):
            serialized = serialized.decode('utf-8')
        cached = jsonutils.loads(serialized)
        if cached == self._INVALID_INDICATOR:
            self.LOG.debug('Cached Token is marked unauthorized')
            raise InvalidUserToken('Token authorization failed')

        data, expires = cached

        try:
            expires = timeutils.parse_isotime(expires)
        except ValueError:
            # Gracefully handle upgrade of expiration times from *nix
            # timestamps to ISO 8601 formatted dates by ignoring old cached
            # values.
            return

        expires = timeutils.normalize_time(expires)
        utcnow = timeutils.utcnow()
        if utcnow < expires:
            self.LOG.debug('Returning cached token')
            return data
        else:
            self.LOG.debug('Cached Token seems expired')
            raise InvalidUserToken('Token authorization failed')

    def _cache_store(self, token_id, data):
        """Store value into memcache.

        data may be _INVALID_INDICATOR or a tuple like (data, expires)

        """
        serialized_data = jsonutils.dumps(data)
        if isinstance(serialized_data, six.text_type):
            serialized_data = serialized_data.encode('utf-8')
        if self._memcache_security_strategy is None:
            cache_key = CACHE_KEY_TEMPLATE % token_id
            data_to_store = serialized_data
        else:
            secret_key = self._memcache_secret_key
            if isinstance(secret_key, six.string_types):
                secret_key = secret_key.encode('utf-8')
            security_strategy = self._memcache_security_strategy
            if isinstance(security_strategy, six.string_types):
                security_strategy = security_strategy.encode('utf-8')
            keys = memcache_crypt.derive_keys(
                token_id, secret_key, security_strategy)
            cache_key = CACHE_KEY_TEMPLATE % memcache_crypt.get_cache_key(keys)
            data_to_store = memcache_crypt.protect_data(keys, serialized_data)

        with self._cache_pool.reserve() as cache:
            cache.set(cache_key, data_to_store, time=self._cache_time)


def filter_factory(global_conf, **local_conf):
    """Returns a WSGI filter app for use with paste.deploy."""
    conf = global_conf.copy()
    conf.update(local_conf)

    def auth_filter(app):
        return AuthProtocol(app, conf)
    return auth_filter


def app_factory(global_conf, **local_conf):
    conf = global_conf.copy()
    conf.update(local_conf)
    return AuthProtocol(None, conf)


if __name__ == '__main__':
    """Run this module directly to start a protected echo service::

        $ python -m keystoneclient.middleware.auth_token

    When the ``auth_token`` module authenticates a request, the echo service
    will respond with all the environment variables presented to it by this
    module.

    """
    def echo_app(environ, start_response):
        """A WSGI application that echoes the CGI environment to the user."""
        start_response('200 OK', [('Content-Type', 'application/json')])
        environment = dict((k, v) for k, v in six.iteritems(environ)
                           if k.startswith('HTTP_X_'))
        yield jsonutils.dumps(environment)

    from wsgiref import simple_server

    # hardcode any non-default configuration here
    conf = {'auth_protocol': 'http', 'admin_token': 'ADMIN'}
    app = AuthProtocol(echo_app, conf)
    server = simple_server.make_server('', 8000, app)
    print('Serving on port 8000 (Ctrl+C to end)...')
    server.serve_forever()
