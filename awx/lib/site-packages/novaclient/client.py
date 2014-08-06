# Copyright 2010 Jacob Kaplan-Moss
# Copyright 2011 OpenStack Foundation
# Copyright 2011 Piston Cloud Computing, Inc.

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

"""
OpenStack Client interface. Handles the REST calls and responses.
"""

import errno
import functools
import glob
import hashlib
import logging
import os
import time

import requests
from requests import adapters

try:
    import json
except ImportError:
    import simplejson as json

from six.moves.urllib import parse

from novaclient import exceptions
from novaclient.openstack.common.gettextutils import _
from novaclient.openstack.common import network_utils
from novaclient import service_catalog
from novaclient import utils

SENSITIVE_HEADERS = ('X-Auth-Token',)


class _ClientConnectionPool(object):

    def __init__(self):
        self._adapters = {}

    def get(self, url):
        """
        Store and reuse HTTP adapters per Service URL.
        """
        if url not in self._adapters:
            self._adapters[url] = adapters.HTTPAdapter()

        return self._adapters[url]


class CompletionCache(object):
    """The completion cache is how we support tab-completion with novaclient.

    The `Manager` writes object IDs and Human-IDs to the completion-cache on
    object-show, object-list, and object-create calls.

    The `nova.bash_completion` script then uses these files to provide the
    actual tab-completion.

    The cache directory layout is:

        ~/.novaclient/
            <hash-of-endpoint-and-username>/
                <resource>-id-cache
                <resource>-human-id-cache
    """
    def __init__(self, username, auth_url, attributes=('id', 'human_id')):
        self.directory = self._make_directory_name(username, auth_url)
        self.attributes = attributes

    def _make_directory_name(self, username, auth_url):
        """Creates a unique directory name based on the auth_url and username
        of the current user.
        """
        uniqifier = hashlib.md5(username.encode('utf-8') +
                                auth_url.encode('utf-8')).hexdigest()
        base_dir = utils.env('NOVACLIENT_UUID_CACHE_DIR',
                             default="~/.novaclient")
        return os.path.expanduser(os.path.join(base_dir, uniqifier))

    def _prepare_directory(self):
        try:
            os.makedirs(self.directory, 0o755)
        except OSError:
            # NOTE(kiall): This is typically either permission denied while
            #              attempting to create the directory, or the
            #              directory already exists. Either way, don't
            #              fail.
            pass

    def clear_class(self, obj_class):
        self._prepare_directory()

        resource = obj_class.__name__.lower()
        resource_glob = os.path.join(self.directory, "%s-*-cache" % resource)

        for filename in glob.iglob(resource_glob):
            try:
                os.unlink(filename)
            except OSError as e:
                if e.errno != errno.ENOENT:
                    raise

    def _write_attribute(self, resource, attribute, value):
        self._prepare_directory()

        filename = "%s-%s-cache" % (resource, attribute.replace('_', '-'))
        path = os.path.join(self.directory, filename)

        with open(path, 'a') as f:
            f.write("%s\n" % value)

    def write_object(self, obj):
        resource = obj.__class__.__name__.lower()

        for attribute in self.attributes:
            value = getattr(obj, attribute, None)
            if value:
                self._write_attribute(resource, attribute, value)


class SessionClient(object):

    def __init__(self, session, auth, interface, service_type, region_name):
        self.session = session
        self.auth = auth

        self.interface = interface
        self.service_type = service_type
        self.region_name = region_name

    def request(self, url, method, **kwargs):
        kwargs.setdefault('user_agent', 'python-novaclient')
        kwargs.setdefault('auth', self.auth)
        kwargs.setdefault('authenticated', False)

        try:
            kwargs['json'] = kwargs.pop('body')
        except KeyError:
            pass

        headers = kwargs.setdefault('headers', {})
        headers.setdefault('Accept', 'application/json')

        endpoint_filter = kwargs.setdefault('endpoint_filter', {})
        endpoint_filter.setdefault('interface', self.interface)
        endpoint_filter.setdefault('service_type', self.service_type)
        endpoint_filter.setdefault('region_name', self.region_name)

        resp = self.session.request(url, method, raise_exc=False, **kwargs)

        body = None
        if resp.text:
            try:
                body = resp.json()
            except ValueError:
                pass

        if resp.status_code >= 400:
            raise exceptions.from_response(resp, body, url, method)

        return resp, body

    def _cs_request(self, url, method, **kwargs):
        # this function is mostly redundant but makes compatibility easier
        kwargs.setdefault('authenticated', True)
        return self.request(url, method, **kwargs)

    def get(self, url, **kwargs):
        return self._cs_request(url, 'GET', **kwargs)

    def post(self, url, **kwargs):
        return self._cs_request(url, 'POST', **kwargs)

    def put(self, url, **kwargs):
        return self._cs_request(url, 'PUT', **kwargs)

    def delete(self, url, **kwargs):
        return self._cs_request(url, 'DELETE', **kwargs)


def _original_only(f):
    """Indicates and enforces that this function can only be used if we are
    using the original HTTPClient object.

    We use this to specify that if you use the newer Session HTTP client then
    you are aware that the way you use your client has been updated and certain
    functions are no longer allowed to be used.
    """
    @functools.wraps(f)
    def wrapper(self, *args, **kwargs):
        if isinstance(self.client, SessionClient):
            msg = ('This call is no longer available. The operation should '
                   'be performed on the session object instead.')
            raise exceptions.InvalidUsage(msg)

        return f(self, *args, **kwargs)

    return wrapper


class HTTPClient(object):
    USER_AGENT = 'python-novaclient'

    def __init__(self, user, password, projectid=None, auth_url=None,
                 insecure=False, timeout=None, proxy_tenant_id=None,
                 proxy_token=None, region_name=None,
                 endpoint_type='publicURL', service_type=None,
                 service_name=None, volume_service_name=None,
                 timings=False, bypass_url=None,
                 os_cache=False, no_cache=True,
                 http_log_debug=False, auth_system='keystone',
                 auth_plugin=None, auth_token=None,
                 cacert=None, tenant_id=None, user_id=None,
                 connection_pool=False):
        self.user = user
        self.user_id = user_id
        self.password = password
        self.projectid = projectid
        self.tenant_id = tenant_id

        self._connection_pool = (_ClientConnectionPool()
                                if connection_pool else None)

        # This will be called by #_get_password if self.password is None.
        # EG if a password can only be obtained by prompting the user, but a
        # token is available, you don't want to prompt until the token has
        # been proven invalid
        self.password_func = None

        if auth_system and auth_system != 'keystone' and not auth_plugin:
            raise exceptions.AuthSystemNotFound(auth_system)

        if not auth_url and auth_system and auth_system != 'keystone':
            auth_url = auth_plugin.get_auth_url()
            if not auth_url:
                raise exceptions.EndpointNotFound()
        self.auth_url = auth_url.rstrip('/') if auth_url else auth_url
        self.version = 'v1.1'
        self.region_name = region_name
        self.endpoint_type = endpoint_type
        self.service_type = service_type
        self.service_name = service_name
        self.volume_service_name = volume_service_name
        self.timings = timings
        self.bypass_url = bypass_url.rstrip('/') if bypass_url else bypass_url
        self.os_cache = os_cache or not no_cache
        self.http_log_debug = http_log_debug
        if timeout is not None:
            self.timeout = float(timeout)
        else:
            self.timeout = None

        self.times = []  # [("item", starttime, endtime), ...]

        self.management_url = self.bypass_url or None
        self.auth_token = auth_token
        self.proxy_token = proxy_token
        self.proxy_tenant_id = proxy_tenant_id
        self.keyring_saver = None
        self.keyring_saved = False

        if insecure:
            self.verify_cert = False
        else:
            if cacert:
                self.verify_cert = cacert
            else:
                self.verify_cert = True

        self.auth_system = auth_system
        self.auth_plugin = auth_plugin
        self._session = None
        self._current_url = None
        self._logger = logging.getLogger(__name__)

        if self.http_log_debug and not self._logger.handlers:
            # Logging level is already set on the root logger
            ch = logging.StreamHandler()
            self._logger.addHandler(ch)
            self._logger.propagate = False
            if hasattr(requests, 'logging'):
                rql = requests.logging.getLogger(requests.__name__)
                rql.addHandler(ch)
                # Since we have already setup the root logger on debug, we
                # have to set it up here on WARNING (its original level)
                # otherwise we will get all the requests logging messages
                rql.setLevel(logging.WARNING)

    def use_token_cache(self, use_it):
        self.os_cache = use_it

    def unauthenticate(self):
        """Forget all of our authentication information."""
        self.management_url = None
        self.auth_token = None

    def set_management_url(self, url):
        self.management_url = url

    def get_timings(self):
        return self.times

    def reset_timings(self):
        self.times = []

    def safe_header(self, name, value):
        if name in SENSITIVE_HEADERS:
            # because in python3 byte string handling is ... ug
            v = value.encode('utf-8')
            h = hashlib.sha1(v)
            d = h.hexdigest()
            return name, "{SHA1}%s" % d
        else:
            return name, value

    def http_log_req(self, method, url, kwargs):
        if not self.http_log_debug:
            return

        string_parts = ['curl -i']

        if not kwargs.get('verify', True):
            string_parts.append(' --insecure')

        string_parts.append(" '%s'" % url)
        string_parts.append(' -X %s' % method)

        # because dict ordering changes from 2 to 3
        keys = sorted(kwargs['headers'].keys())
        for name in keys:
            value = kwargs['headers'][name]
            header = ' -H "%s: %s"' % self.safe_header(name, value)
            string_parts.append(header)

        if 'data' in kwargs:
            string_parts.append(" -d '%s'" % (kwargs['data']))
        self._logger.debug("REQ: %s" % "".join(string_parts))

    def http_log_resp(self, resp):
        if not self.http_log_debug:
            return
        self._logger.debug("RESP: [%(status)s] %(headers)s\nRESP BODY: "
                           "%(text)s\n", {'status': resp.status_code,
                                          'headers': resp.headers,
                                          'text': resp.text})

    def open_session(self):
        if not self._connection_pool:
            self._session = requests.Session()

    def close_session(self):
        if self._session and not self._connection_pool:
            self._session.close()
            self._session = None

    def _get_session(self, url):
        if self._connection_pool:
            magic_tuple = parse.urlsplit(url)
            scheme, netloc, path, query, frag = magic_tuple
            service_url = '%s://%s' % (scheme, netloc)
            if self._current_url != service_url:
                # Invalidate Session object in case the url is somehow changed
                if self._session:
                    self._session.close()
                self._current_url = service_url
                self._logger.debug(
                        "New session created for: (%s)" % service_url)
                self._session = requests.Session()
                self._session.mount(service_url,
                        self._connection_pool.get(service_url))
            return self._session
        elif self._session:
            return self._session

    def request(self, url, method, **kwargs):
        kwargs.setdefault('headers', kwargs.get('headers', {}))
        kwargs['headers']['User-Agent'] = self.USER_AGENT
        kwargs['headers']['Accept'] = 'application/json'
        if 'body' in kwargs:
            kwargs['headers']['Content-Type'] = 'application/json'
            kwargs['data'] = json.dumps(kwargs['body'])
            del kwargs['body']
        if self.timeout is not None:
            kwargs.setdefault('timeout', self.timeout)
        kwargs['verify'] = self.verify_cert

        self.http_log_req(method, url, kwargs)

        request_func = requests.request
        session = self._get_session(url)
        if session:
            request_func = session.request

        resp = request_func(
            method,
            url,
            **kwargs)

        self.http_log_resp(resp)

        if resp.text:
            # TODO(dtroyer): verify the note below in a requests context
            # NOTE(alaski): Because force_exceptions_to_status_code=True
            # httplib2 returns a connection refused event as a 400 response.
            # To determine if it is a bad request or refused connection we need
            # to check the body.  httplib2 tests check for 'Connection refused'
            # or 'actively refused' in the body, so that's what we'll do.
            if resp.status_code == 400:
                if ('Connection refused' in resp.text or
                    'actively refused' in resp.text):
                    raise exceptions.ConnectionRefused(resp.text)
            try:
                body = json.loads(resp.text)
            except ValueError:
                body = None
        else:
            body = None

        if resp.status_code >= 400:
            raise exceptions.from_response(resp, body, url, method)

        return resp, body

    def _time_request(self, url, method, **kwargs):
        start_time = time.time()
        resp, body = self.request(url, method, **kwargs)
        self.times.append(("%s %s" % (method, url),
                           start_time, time.time()))
        return resp, body

    def _cs_request(self, url, method, **kwargs):
        if not self.management_url:
            self.authenticate()

        # Perform the request once. If we get a 401 back then it
        # might be because the auth token expired, so try to
        # re-authenticate and try again. If it still fails, bail.
        try:
            kwargs.setdefault('headers', {})['X-Auth-Token'] = self.auth_token
            if self.projectid:
                kwargs['headers']['X-Auth-Project-Id'] = self.projectid

            resp, body = self._time_request(self.management_url + url, method,
                                            **kwargs)
            return resp, body
        except exceptions.Unauthorized as e:
            try:
                # first discard auth token, to avoid the possibly expired
                # token being re-used in the re-authentication attempt
                self.unauthenticate()
                # overwrite bad token
                self.keyring_saved = False
                self.authenticate()
                kwargs['headers']['X-Auth-Token'] = self.auth_token
                resp, body = self._time_request(self.management_url + url,
                                                method, **kwargs)
                return resp, body
            except exceptions.Unauthorized:
                raise e

    def _get_password(self):
        if not self.password and self.password_func:
            self.password = self.password_func()
        return self.password

    def get(self, url, **kwargs):
        return self._cs_request(url, 'GET', **kwargs)

    def post(self, url, **kwargs):
        return self._cs_request(url, 'POST', **kwargs)

    def put(self, url, **kwargs):
        return self._cs_request(url, 'PUT', **kwargs)

    def delete(self, url, **kwargs):
        return self._cs_request(url, 'DELETE', **kwargs)

    def _extract_service_catalog(self, url, resp, body, extract_token=True):
        """See what the auth service told us and process the response.
        We may get redirected to another site, fail or actually get
        back a service catalog with a token and our endpoints.
        """

        # content must always present
        if resp.status_code == 200 or resp.status_code == 201:
            try:
                self.auth_url = url
                self.service_catalog = \
                    service_catalog.ServiceCatalog(body)
                if extract_token:
                    self.auth_token = self.service_catalog.get_token()
                    self.tenant_id = self.service_catalog.get_tenant_id()

                management_url = self.service_catalog.url_for(
                    attr='region',
                    filter_value=self.region_name,
                    endpoint_type=self.endpoint_type,
                    service_type=self.service_type,
                    service_name=self.service_name,
                    volume_service_name=self.volume_service_name,)
                self.management_url = management_url.rstrip('/')
                return None
            except exceptions.AmbiguousEndpoints:
                print(_("Found more than one valid endpoint. Use a more "
                      "restrictive filter"))
                raise
            except KeyError:
                raise exceptions.AuthorizationFailure()
            except exceptions.EndpointNotFound:
                print(_("Could not find any suitable endpoint. Correct "
                        "region?"))
                raise

        elif resp.status_code == 305:
            return resp.headers['location']
        else:
            raise exceptions.from_response(resp, body, url)

    def _fetch_endpoints_from_auth(self, url):
        """We have a token, but don't know the final endpoint for
        the region. We have to go back to the auth service and
        ask again. This request requires an admin-level token
        to work. The proxy token supplied could be from a low-level enduser.

        We can't get this from the keystone service endpoint, we have to use
        the admin endpoint.

        This will overwrite our admin token with the user token.
        """

        # GET ...:5001/v2.0/tokens/#####/endpoints
        url = '/'.join([url, 'tokens', '%s?belongsTo=%s'
                        % (self.proxy_token, self.proxy_tenant_id)])
        self._logger.debug("Using Endpoint URL: %s" % url)
        resp, body = self._time_request(
            url, "GET", headers={'X-Auth-Token': self.auth_token})
        return self._extract_service_catalog(url, resp, body,
                                             extract_token=False)

    def authenticate(self):
        magic_tuple = network_utils.urlsplit(self.auth_url)
        scheme, netloc, path, query, frag = magic_tuple
        port = magic_tuple.port
        if port is None:
            port = 80
        path_parts = path.split('/')
        for part in path_parts:
            if len(part) > 0 and part[0] == 'v':
                self.version = part
                break

        if self.auth_token and self.management_url:
            self._save_keys()
            return

        # TODO(sandy): Assume admin endpoint is 35357 for now.
        # Ideally this is going to have to be provided by the service catalog.
        new_netloc = netloc.replace(':%d' % port, ':%d' % (35357,))
        admin_url = parse.urlunsplit(
            (scheme, new_netloc, path, query, frag))

        auth_url = self.auth_url
        if self.version == "v2.0":  # FIXME(chris): This should be better.
            while auth_url:
                if not self.auth_system or self.auth_system == 'keystone':
                    auth_url = self._v2_auth(auth_url)
                else:
                    auth_url = self._plugin_auth(auth_url)

            # Are we acting on behalf of another user via an
            # existing token? If so, our actual endpoints may
            # be different than that of the admin token.
            if self.proxy_token:
                if self.bypass_url:
                    self.set_management_url(self.bypass_url)
                else:
                    self._fetch_endpoints_from_auth(admin_url)
                # Since keystone no longer returns the user token
                # with the endpoints any more, we need to replace
                # our service account token with the user token.
                self.auth_token = self.proxy_token
        else:
            try:
                while auth_url:
                    auth_url = self._v1_auth(auth_url)
            # In some configurations nova makes redirection to
            # v2.0 keystone endpoint. Also, new location does not contain
            # real endpoint, only hostname and port.
            except exceptions.AuthorizationFailure:
                if auth_url.find('v2.0') < 0:
                    auth_url = auth_url + '/v2.0'
                self._v2_auth(auth_url)

        if self.bypass_url:
            self.set_management_url(self.bypass_url)
        elif not self.management_url:
            raise exceptions.Unauthorized('Nova Client')

        self._save_keys()

    def _save_keys(self):
        # Store the token/mgmt url in the keyring for later requests.
        if (self.keyring_saver and self.os_cache and not self.keyring_saved
                and self.auth_token and self.management_url
                and self.tenant_id):
            self.keyring_saver.save(self.auth_token,
                                    self.management_url,
                                    self.tenant_id)
            # Don't save it again
            self.keyring_saved = True

    def _v1_auth(self, url):
        if self.proxy_token:
            raise exceptions.NoTokenLookupException()

        headers = {'X-Auth-User': self.user,
                   'X-Auth-Key': self._get_password()}
        if self.projectid:
            headers['X-Auth-Project-Id'] = self.projectid

        resp, body = self._time_request(url, 'GET', headers=headers)
        if resp.status_code in (200, 204):  # in some cases we get No Content
            try:
                mgmt_header = 'x-server-management-url'
                self.management_url = resp.headers[mgmt_header].rstrip('/')
                self.auth_token = resp.headers['x-auth-token']
                self.auth_url = url
            except (KeyError, TypeError):
                raise exceptions.AuthorizationFailure()
        elif resp.status_code == 305:
            return resp.headers['location']
        else:
            raise exceptions.from_response(resp, body, url)

    def _plugin_auth(self, auth_url):
        return self.auth_plugin.authenticate(self, auth_url)

    def _v2_auth(self, url):
        """Authenticate against a v2.0 auth service."""
        if self.auth_token:
            body = {"auth": {
                    "token": {"id": self.auth_token}}}
        elif self.user_id:
            body = {"auth": {
                    "passwordCredentials": {"userId": self.user_id,
                                            "password": self._get_password()}}}
        else:
            body = {"auth": {
                    "passwordCredentials": {"username": self.user,
                                            "password": self._get_password()}}}

        if self.tenant_id:
            body['auth']['tenantId'] = self.tenant_id
        elif self.projectid:
            body['auth']['tenantName'] = self.projectid

        return self._authenticate(url, body)

    def _authenticate(self, url, body, **kwargs):
        """Authenticate and extract the service catalog."""
        method = "POST"
        token_url = url + "/tokens"

        # Make sure we follow redirects when trying to reach Keystone
        resp, respbody = self._time_request(
            token_url,
            method,
            body=body,
            allow_redirects=True,
            **kwargs)

        return self._extract_service_catalog(url, resp, respbody)


def _construct_http_client(username=None, password=None, project_id=None,
                           auth_url=None, insecure=False, timeout=None,
                           proxy_tenant_id=None, proxy_token=None,
                           region_name=None, endpoint_type='publicURL',
                           extensions=None, service_type='compute',
                           service_name=None, volume_service_name=None,
                           timings=False, bypass_url=None, os_cache=False,
                           no_cache=True, http_log_debug=False,
                           auth_system='keystone', auth_plugin=None,
                           auth_token=None, cacert=None, tenant_id=None,
                           user_id=None, connection_pool=False, session=None,
                           auth=None):
    if session:
        return SessionClient(session=session,
                             auth=auth,
                             interface=endpoint_type,
                             service_type=service_type,
                             region_name=region_name)
    else:
        # FIXME(jamielennox): username and password are now optional. Need
        # to test that they were provided in this mode.
        return HTTPClient(username,
                          password,
                          user_id=user_id,
                          projectid=project_id,
                          tenant_id=tenant_id,
                          auth_url=auth_url,
                          auth_token=auth_token,
                          insecure=insecure,
                          timeout=timeout,
                          auth_system=auth_system,
                          auth_plugin=auth_plugin,
                          proxy_token=proxy_token,
                          proxy_tenant_id=proxy_tenant_id,
                          region_name=region_name,
                          endpoint_type=endpoint_type,
                          service_type=service_type,
                          service_name=service_name,
                          volume_service_name=volume_service_name,
                          timings=timings,
                          bypass_url=bypass_url,
                          os_cache=os_cache,
                          http_log_debug=http_log_debug,
                          cacert=cacert,
                          connection_pool=connection_pool)


def get_client_class(version):
    version_map = {
        '1.1': 'novaclient.v1_1.client.Client',
        '2': 'novaclient.v1_1.client.Client',
        '3': 'novaclient.v3.client.Client',
    }
    try:
        client_path = version_map[str(version)]
    except (KeyError, ValueError):
        msg = _("Invalid client version '%(version)s'. must be one of: "
                "%(keys)s") % {'version': version,
                               'keys': ', '.join(version_map.keys())}
        raise exceptions.UnsupportedVersion(msg)

    return utils.import_class(client_path)


def Client(version, *args, **kwargs):
    client_class = get_client_class(version)
    return client_class(*args, **kwargs)
