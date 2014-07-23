# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Common utilities for OpenStack
"""
import sys
import datetime

from libcloud.utils.py3 import httplib
from libcloud.utils.iso8601 import parse_date

from libcloud.common.base import ConnectionUserAndKey, Response
from libcloud.compute.types import (LibcloudError, InvalidCredsError,
                                    MalformedResponseError)

try:
    import simplejson as json
except ImportError:
    import json

AUTH_API_VERSION = '1.1'

# Auth versions which contain token expiration information.
AUTH_VERSIONS_WITH_EXPIRES = [
    '1.1',
    '2.0',
    '2.0_apikey',
    '2.0_password'
]

# How many seconds to substract from the auth token expiration time before
# testing if the token is still valid.
# The time is subtracted to account for the HTTP request latency and prevent
# user from getting "InvalidCredsError" if token is about to expire.
AUTH_TOKEN_EXPIRES_GRACE_SECONDS = 5

__all__ = [
    'OpenStackBaseConnection',
    'OpenStackAuthConnection',
    'OpenStackServiceCatalog',
    'OpenStackDriverMixin',

    'AUTH_TOKEN_EXPIRES_GRACE_SECONDS'
]


# @TODO: Refactor for re-use by other openstack drivers
class OpenStackAuthResponse(Response):
    def success(self):
        return True

    def parse_body(self):
        if not self.body:
            return None

        if 'content-type' in self.headers:
            key = 'content-type'
        elif 'Content-Type' in self.headers:
            key = 'Content-Type'
        else:
            raise LibcloudError('Missing content-type header',
                                driver=OpenStackAuthConnection)

        content_type = self.headers[key]
        if content_type.find(';') != -1:
            content_type = content_type.split(';')[0]

        if content_type == 'application/json':
            try:
                data = json.loads(self.body)
            except:
                raise MalformedResponseError('Failed to parse JSON',
                                             body=self.body,
                                             driver=OpenStackAuthConnection)
        elif content_type == 'text/plain':
            data = self.body
        else:
            data = self.body

        return data


class OpenStackAuthConnection(ConnectionUserAndKey):

    responseCls = OpenStackAuthResponse
    name = 'OpenStack Auth'
    timeout = None

    def __init__(self, parent_conn, auth_url, auth_version, user_id, key,
                 tenant_name=None, timeout=None):
        self.parent_conn = parent_conn
        # enable tests to use the same mock connection classes.
        self.conn_classes = parent_conn.conn_classes

        super(OpenStackAuthConnection, self).__init__(
            user_id, key, url=auth_url, timeout=timeout)

        self.auth_version = auth_version
        self.auth_url = auth_url
        self.driver = self.parent_conn.driver
        self.tenant_name = tenant_name
        self.timeout = timeout

        self.urls = {}
        self.auth_token = None
        self.auth_token_expires = None
        self.auth_user_info = None

    def morph_action_hook(self, action):
        (_, _, _, request_path) = self._tuple_from_url(self.auth_url)

        if request_path == '':
            # No path is provided in the auth_url, use action passed to this
            # method.
            return action

        return request_path

    def add_default_headers(self, headers):
        headers['Accept'] = 'application/json'
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        return headers

    def authenticate(self, force=False):
        """
        Authenticate against the keystone api.

        :param force: Forcefully update the token even if it's already cached
                      and still valid.
        :type force: ``bool``
        """
        if not force and self.auth_version in AUTH_VERSIONS_WITH_EXPIRES \
           and self.is_token_valid():
            # If token is still valid, there is no need to re-authenticate
            return self

        if self.auth_version == "1.0":
            return self.authenticate_1_0()
        elif self.auth_version == "1.1":
            return self.authenticate_1_1()
        elif self.auth_version == "2.0" or self.auth_version == "2.0_apikey":
            return self.authenticate_2_0_with_apikey()
        elif self.auth_version == "2.0_password":
            return self.authenticate_2_0_with_password()
        else:
            raise LibcloudError('Unsupported Auth Version requested')

    def authenticate_1_0(self):
        headers = {
            'X-Auth-User': self.user_id,
            'X-Auth-Key': self.key,
        }

        resp = self.request('/v1.0', headers=headers, method='GET')

        if resp.status == httplib.UNAUTHORIZED:
            # HTTP UNAUTHORIZED (401): auth failed
            raise InvalidCredsError()
        elif resp.status not in [httplib.NO_CONTENT, httplib.OK]:
            body = 'code: %s body:%s headers:%s' % (resp.status,
                                                    resp.body,
                                                    resp.headers)
            raise MalformedResponseError('Malformed response', body=body,
                                         driver=self.driver)
        else:
            headers = resp.headers
            # emulate the auth 1.1 URL list
            self.urls = {}
            self.urls['cloudServers'] = \
                [{'publicURL': headers.get('x-server-management-url', None)}]
            self.urls['cloudFilesCDN'] = \
                [{'publicURL': headers.get('x-cdn-management-url', None)}]
            self.urls['cloudFiles'] = \
                [{'publicURL': headers.get('x-storage-url', None)}]
            self.auth_token = headers.get('x-auth-token', None)
            self.auth_user_info = None

            if not self.auth_token:
                raise MalformedResponseError('Missing X-Auth-Token in \
                                              response headers')

        return self

    def authenticate_1_1(self):
        reqbody = json.dumps({'credentials': {'username': self.user_id,
                                              'key': self.key}})
        resp = self.request('/v1.1/auth', data=reqbody, headers={},
                            method='POST')

        if resp.status == httplib.UNAUTHORIZED:
            # HTTP UNAUTHORIZED (401): auth failed
            raise InvalidCredsError()
        elif resp.status != httplib.OK:
            body = 'code: %s body:%s' % (resp.status, resp.body)
            raise MalformedResponseError('Malformed response', body=body,
                                         driver=self.driver)
        else:
            try:
                body = json.loads(resp.body)
            except Exception:
                e = sys.exc_info()[1]
                raise MalformedResponseError('Failed to parse JSON', e)

            try:
                expires = body['auth']['token']['expires']

                self.auth_token = body['auth']['token']['id']
                self.auth_token_expires = parse_date(expires)
                self.urls = body['auth']['serviceCatalog']
                self.auth_user_info = None
            except KeyError:
                e = sys.exc_info()[1]
                raise MalformedResponseError('Auth JSON response is \
                                             missing required elements', e)

        return self

    def authenticate_2_0_with_apikey(self):
        # API Key based authentication uses the RAX-KSKEY extension.
        # http://s.apache.org/oAi
        data = {'auth':
                {'RAX-KSKEY:apiKeyCredentials':
                 {'username': self.user_id, 'apiKey': self.key}}}
        if self.tenant_name:
            data['auth']['tenantName'] = self.tenant_name
        reqbody = json.dumps(data)
        return self.authenticate_2_0_with_body(reqbody)

    def authenticate_2_0_with_password(self):
        # Password based authentication is the only 'core' authentication
        # method in Keystone at this time.
        # 'keystone' - http://s.apache.org/e8h
        data = {'auth':
                {'passwordCredentials':
                 {'username': self.user_id, 'password': self.key}}}
        if self.tenant_name:
            data['auth']['tenantName'] = self.tenant_name
        reqbody = json.dumps(data)
        return self.authenticate_2_0_with_body(reqbody)

    def authenticate_2_0_with_body(self, reqbody):
        resp = self.request('/v2.0/tokens', data=reqbody,
                            headers={'Content-Type': 'application/json'},
                            method='POST')
        if resp.status == httplib.UNAUTHORIZED:
            raise InvalidCredsError()
        elif resp.status not in [httplib.OK,
                                 httplib.NON_AUTHORITATIVE_INFORMATION]:
            body = 'code: %s body: %s' % (resp.status, resp.body)
            raise MalformedResponseError('Malformed response', body=body,
                                         driver=self.driver)
        else:
            try:
                body = json.loads(resp.body)
            except Exception:
                e = sys.exc_info()[1]
                raise MalformedResponseError('Failed to parse JSON', e)

            try:
                access = body['access']
                expires = access['token']['expires']

                self.auth_token = access['token']['id']
                self.auth_token_expires = parse_date(expires)
                self.urls = access['serviceCatalog']
                self.auth_user_info = access.get('user', {})
            except KeyError:
                e = sys.exc_info()[1]
                raise MalformedResponseError('Auth JSON response is \
                                             missing required elements', e)

        return self

    def is_token_valid(self):
        """
        Return True if the current auth token is already cached and hasn't
        expired yet.

        :return: ``True`` if the token is still valid, ``False`` otherwise.
        :rtype: ``bool``
        """
        if not self.auth_token:
            return False

        if not self.auth_token_expires:
            return False

        expires = self.auth_token_expires - \
            datetime.timedelta(seconds=AUTH_TOKEN_EXPIRES_GRACE_SECONDS)

        time_tuple_expires = expires.utctimetuple()
        time_tuple_now = datetime.datetime.utcnow().utctimetuple()

        if time_tuple_now < time_tuple_expires:
            return True

        return False


class OpenStackServiceCatalog(object):
    """
    http://docs.openstack.org/api/openstack-identity-service/2.0/content/

    This class should be instanciated with the contents of the
    'serviceCatalog' in the auth response. This will do the work of figuring
    out which services actually exist in the catalog as well as split them up
    by type, name, and region if available
    """

    _auth_version = None
    _service_catalog = None

    def __init__(self, service_catalog, ex_force_auth_version=None):
        self._auth_version = ex_force_auth_version or AUTH_API_VERSION
        self._service_catalog = {}

        # Check this way because there are a couple of different 2.0_*
        # auth types.
        if '2.0' in self._auth_version:
            self._parse_auth_v2(service_catalog)
        elif ('1.1' in self._auth_version) or ('1.0' in self._auth_version):
            self._parse_auth_v1(service_catalog)
        else:
            raise LibcloudError('auth version "%s" not supported'
                                % (self._auth_version))

    def get_catalog(self):
        return self._service_catalog

    def get_public_urls(self, service_type=None, name=None):
        endpoints = self.get_endpoints(service_type=service_type,
                                       name=name)

        result = []
        for endpoint in endpoints:
            if 'publicURL' in endpoint:
                result.append(endpoint['publicURL'])

        return result

    def get_endpoints(self, service_type=None, name=None):
        eps = []

        if '2.0' in self._auth_version:
            endpoints = self._service_catalog.get(service_type, {}) \
                                             .get(name, {})
        elif ('1.1' in self._auth_version) or ('1.0' in self._auth_version):
            endpoints = self._service_catalog.get(name, {})

        for regionName, values in endpoints.items():
            eps.append(values[0])

        return eps

    def get_endpoint(self, service_type=None, name=None, region=None):
        if '2.0' in self._auth_version:
            endpoint = self._service_catalog.get(service_type, {}) \
                                            .get(name, {}).get(region, [])
        elif ('1.1' in self._auth_version) or ('1.0' in self._auth_version):
            endpoint = self._service_catalog.get(name, {}).get(region, [])

        # ideally an endpoint either isn't found or only one match is found.
        if len(endpoint) == 1:
            return endpoint[0]
        else:
            return {}

    def _parse_auth_v1(self, service_catalog):
        for service, endpoints in service_catalog.items():

            self._service_catalog[service] = {}

            for endpoint in endpoints:
                region = endpoint.get('region')

                if region not in self._service_catalog[service]:
                    self._service_catalog[service][region] = []

                self._service_catalog[service][region].append(endpoint)

    def _parse_auth_v2(self, service_catalog):
        for service in service_catalog:
            service_type = service['type']
            service_name = service.get('name', None)

            if service_type not in self._service_catalog:
                self._service_catalog[service_type] = {}

            if service_name not in self._service_catalog[service_type]:
                self._service_catalog[service_type][service_name] = {}

            for endpoint in service.get('endpoints', []):
                region = endpoint.get('region', None)

                catalog = self._service_catalog[service_type][service_name]
                if region not in catalog:
                    catalog[region] = []

                catalog[region].append(endpoint)


class OpenStackBaseConnection(ConnectionUserAndKey):

    """
    Base class for OpenStack connections.

    :param user_id: User name to use when authenticating
    :type user_id: ``str``

    :param key: Secret to use when authenticating.
    :type key: ``str``

    :param secure: Use HTTPS?  (True by default.)
    :type secure: ``bool``

    :param ex_force_base_url: Base URL for connection requests.  If
    not specified, this will be determined by authenticating.
    :type ex_force_base_url: ``str``

    :param ex_force_auth_url: Base URL for authentication requests.
    :type ex_force_auth_url: ``str``

    :param ex_force_auth_version: Authentication version to use.  If
    not specified, defaults to AUTH_API_VERSION.
    :type ex_force_auth_version: ``str``

    :param ex_force_auth_token: Authentication token to use for
    connection requests.  If specified, the connection will not attempt
    to authenticate, and the value of ex_force_base_url will be used to
    determine the base request URL.  If ex_force_auth_token is passed in,
    ex_force_base_url must also be provided.
    :type ex_force_auth_token: ``str``

    :param ex_tenant_name: When authenticating, provide this tenant
    name to the identity service.  A scoped token will be returned.
    Some cloud providers require the tenant name to be provided at
    authentication time.  Others will use a default tenant if none
    is provided.
    :type ex_tenant_name: ``str``

    :param ex_force_service_type: Service type to use when selecting an
    service.  If not specified, a provider specific default will be used.
    :type ex_force_service_type: ``str``

    :param ex_force_service_name: Service name to use when selecting an
    service.  If not specified, a provider specific default will be used.
    :type ex_force_service_name: ``str``

    :param ex_force_service_region: Region to use when selecting an
    service.  If not specified, a provider specific default will be used.
    :type ex_force_service_region: ``str``
    """

    auth_url = None
    auth_token = None
    auth_token_expires = None
    auth_user_info = None
    service_catalog = None
    service_type = None
    service_name = None
    service_region = None
    _auth_version = None

    def __init__(self, user_id, key, secure=True,
                 host=None, port=None, timeout=None,
                 ex_force_base_url=None,
                 ex_force_auth_url=None,
                 ex_force_auth_version=None,
                 ex_force_auth_token=None,
                 ex_tenant_name=None,
                 ex_force_service_type=None,
                 ex_force_service_name=None,
                 ex_force_service_region=None):
        super(OpenStackBaseConnection, self).__init__(
            user_id, key, secure=secure, timeout=timeout)

        if ex_force_auth_version:
            self._auth_version = ex_force_auth_version

        self._ex_force_base_url = ex_force_base_url
        self._ex_force_auth_url = ex_force_auth_url
        self._ex_force_auth_token = ex_force_auth_token
        self._ex_tenant_name = ex_tenant_name
        self._ex_force_service_type = ex_force_service_type
        self._ex_force_service_name = ex_force_service_name
        self._ex_force_service_region = ex_force_service_region

        if ex_force_auth_token and not ex_force_base_url:
            raise LibcloudError(
                'Must also provide ex_force_base_url when specifying '
                'ex_force_auth_token.')

        if ex_force_auth_token:
            self.auth_token = ex_force_auth_token

        if not self._auth_version:
            self._auth_version = AUTH_API_VERSION

        auth_url = self._get_auth_url()

        if not auth_url:
            raise LibcloudError('OpenStack instance must ' +
                                'have auth_url set')

        osa = OpenStackAuthConnection(self, auth_url, self._auth_version,
                                      self.user_id, self.key,
                                      tenant_name=self._ex_tenant_name,
                                      timeout=self.timeout)
        self._osa = osa

    def _get_auth_url(self):
        """
        Retrieve auth url for this instance using either "ex_force_auth_url"
        constructor kwarg of "auth_url" class variable.
        """
        auth_url = self.auth_url

        if self._ex_force_auth_url is not None:
            auth_url = self._ex_force_auth_url

        return auth_url

    def get_service_catalog(self):
        if self.service_catalog is None:
            self._populate_hosts_and_request_paths()

        return self.service_catalog

    def get_endpoint(self):
        """
        Selects the endpoint to use based on provider specific values,
        or overrides passed in by the user when setting up the driver.

        :returns: url of the relevant endpoint for the driver
        """
        service_type = self.service_type
        service_name = self.service_name
        service_region = self.service_region
        if self._ex_force_service_type:
            service_type = self._ex_force_service_type
        if self._ex_force_service_name:
            service_name = self._ex_force_service_name
        if self._ex_force_service_region:
            service_region = self._ex_force_service_region

        ep = self.service_catalog.get_endpoint(service_type=service_type,
                                               name=service_name,
                                               region=service_region)
        if 'publicURL' in ep:
            return ep['publicURL']

        raise LibcloudError('Could not find specified endpoint')

    def add_default_headers(self, headers):
        headers['X-Auth-Token'] = self.auth_token
        headers['Accept'] = self.accept_format
        return headers

    def morph_action_hook(self, action):
        self._populate_hosts_and_request_paths()
        return super(OpenStackBaseConnection, self).morph_action_hook(action)

    def request(self, **kwargs):
        return super(OpenStackBaseConnection, self).request(**kwargs)

    def _set_up_connection_info(self, url):
        result = self._tuple_from_url(url)
        (self.host, self.port, self.secure, self.request_path) = result

    def _populate_hosts_and_request_paths(self):
        """
        OpenStack uses a separate host for API calls which is only provided
        after an initial authentication request.
        """
        osa = self._osa

        if self._ex_force_auth_token:
            # If ex_force_auth_token is provided we always hit the api directly
            # and never try to authenticate.
            #
            # Note: When ex_force_auth_token is provided, ex_force_base_url
            # must be provided as well.
            self._set_up_connection_info(url=self._ex_force_base_url)
            return

        if not osa.is_token_valid():
            # Token is not available or it has expired. Need to retrieve a
            # new one.
            osa.authenticate()  # may throw InvalidCreds

            self.auth_token = osa.auth_token
            self.auth_token_expires = osa.auth_token_expires
            self.auth_user_info = osa.auth_user_info

            # Pull out and parse the service catalog
            osc = OpenStackServiceCatalog(
                osa.urls, ex_force_auth_version=self._auth_version)
            self.service_catalog = osc

        url = self._ex_force_base_url or self.get_endpoint()
        self._set_up_connection_info(url=url)


class OpenStackDriverMixin(object):

    def __init__(self, *args, **kwargs):
        self._ex_force_base_url = kwargs.get('ex_force_base_url', None)
        self._ex_force_auth_url = kwargs.get('ex_force_auth_url', None)
        self._ex_force_auth_version = kwargs.get('ex_force_auth_version', None)
        self._ex_force_auth_token = kwargs.get('ex_force_auth_token', None)
        self._ex_tenant_name = kwargs.get('ex_tenant_name', None)
        self._ex_force_service_type = kwargs.get('ex_force_service_type', None)
        self._ex_force_service_name = kwargs.get('ex_force_service_name', None)
        self._ex_force_service_region = kwargs.get('ex_force_service_region',
                                                   None)

    def openstack_connection_kwargs(self):
        """

        :rtype: ``dict``
        """
        rv = {}
        if self._ex_force_base_url:
            rv['ex_force_base_url'] = self._ex_force_base_url
        if self._ex_force_auth_token:
            rv['ex_force_auth_token'] = self._ex_force_auth_token
        if self._ex_force_auth_url:
            rv['ex_force_auth_url'] = self._ex_force_auth_url
        if self._ex_force_auth_version:
            rv['ex_force_auth_version'] = self._ex_force_auth_version
        if self._ex_tenant_name:
            rv['ex_tenant_name'] = self._ex_tenant_name
        if self._ex_force_service_type:
            rv['ex_force_service_type'] = self._ex_force_service_type
        if self._ex_force_service_name:
            rv['ex_force_service_name'] = self._ex_force_service_name
        if self._ex_force_service_region:
            rv['ex_force_service_region'] = self._ex_force_service_region
        return rv
