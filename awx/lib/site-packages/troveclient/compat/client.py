# Copyright (c) 2011 OpenStack Foundation
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

import httplib2
import logging
import os
import sys
import time

try:
    import json
except ImportError:
    import simplejson as json


from troveclient.compat import auth
from troveclient.compat import exceptions


_logger = logging.getLogger(__name__)
RDC_PP = os.environ.get("RDC_PP", "False") == "True"


expected_errors = (400, 401, 403, 404, 408, 409, 413, 422, 500, 501)


def log_to_streamhandler(stream=None):
    stream = stream or sys.stderr
    ch = logging.StreamHandler(stream)
    _logger.setLevel(logging.DEBUG)
    _logger.addHandler(ch)


if 'REDDWARFCLIENT_DEBUG' in os.environ and os.environ['REDDWARFCLIENT_DEBUG']:
    log_to_streamhandler()


class TroveHTTPClient(httplib2.Http):

    USER_AGENT = 'python-troveclient'

    def __init__(self, user, password, tenant, auth_url, service_name,
                 service_url=None,
                 auth_strategy=None, insecure=False,
                 timeout=None, proxy_tenant_id=None,
                 proxy_token=None, region_name=None,
                 endpoint_type='publicURL', service_type=None,
                 timings=False):

        super(TroveHTTPClient, self).__init__(timeout=timeout)

        self.username = user
        self.password = password
        self.tenant = tenant
        if auth_url:
            self.auth_url = auth_url.rstrip('/')
        else:
            self.auth_url = None
        self.region_name = region_name
        self.endpoint_type = endpoint_type
        self.service_url = service_url
        self.service_type = service_type
        self.service_name = service_name
        self.timings = timings

        self.times = []  # [("item", starttime, endtime), ...]

        self.auth_token = None
        self.proxy_token = proxy_token
        self.proxy_tenant_id = proxy_tenant_id

        # httplib2 overrides
        self.force_exception_to_status_code = True
        self.disable_ssl_certificate_validation = insecure

        auth_cls = auth.get_authenticator_cls(auth_strategy)

        self.authenticator = auth_cls(self, auth_strategy,
                                      self.auth_url, self.username,
                                      self.password, self.tenant,
                                      region=region_name,
                                      service_type=service_type,
                                      service_name=service_name,
                                      service_url=service_url)

    def get_timings(self):
        return self.times

    def http_log(self, args, kwargs, resp, body):
        if not RDC_PP:
            self.simple_log(args, kwargs, resp, body)
        else:
            self.pretty_log(args, kwargs, resp, body)

    def simple_log(self, args, kwargs, resp, body):
        if not _logger.isEnabledFor(logging.DEBUG):
            return

        string_parts = ['curl -i']
        for element in args:
            if element in ('GET', 'POST'):
                string_parts.append(' -X %s' % element)
            else:
                string_parts.append(' %s' % element)

        for element in kwargs['headers']:
            header = ' -H "%s: %s"' % (element, kwargs['headers'][element])
            string_parts.append(header)

        _logger.debug("REQ: %s\n" % "".join(string_parts))
        if 'body' in kwargs:
            _logger.debug("REQ BODY: %s\n" % (kwargs['body']))
        _logger.debug("RESP:%s %s\n", resp, body)

    def pretty_log(self, args, kwargs, resp, body):
        if not _logger.isEnabledFor(logging.DEBUG):
            return

        string_parts = ['curl -i']
        for element in args:
            if element in ('GET', 'POST'):
                string_parts.append(' -X %s' % element)
            else:
                string_parts.append(' %s' % element)

        for element in kwargs['headers']:
            header = ' -H "%s: %s"' % (element, kwargs['headers'][element])
            string_parts.append(header)

        curl_cmd = "".join(string_parts)
        _logger.debug("REQUEST:")
        if 'body' in kwargs:
            _logger.debug("%s -d '%s'" % (curl_cmd, kwargs['body']))
            try:
                req_body = json.dumps(json.loads(kwargs['body']),
                                      sort_keys=True, indent=4)
            except Exception:
                req_body = kwargs['body']
            _logger.debug("BODY: %s\n" % (req_body))
        else:
            _logger.debug(curl_cmd)

        try:
            resp_body = json.dumps(json.loads(body), sort_keys=True, indent=4)
        except Exception:
            resp_body = body
        _logger.debug("RESPONSE HEADERS: %s" % resp)
        _logger.debug("RESPONSE BODY   : %s" % resp_body)

    def request(self, *args, **kwargs):
        kwargs.setdefault('headers', kwargs.get('headers', {}))
        kwargs['headers']['User-Agent'] = self.USER_AGENT
        self.morph_request(kwargs)

        resp, body = super(TroveHTTPClient, self).request(*args, **kwargs)
        # compat between requests and httplib2
        resp.status_code = resp.status

        # Save this in case anyone wants it.
        self.last_response = (resp, body)
        self.http_log(args, kwargs, resp, body)

        if body:
            try:
                body = self.morph_response_body(body)
            except exceptions.ResponseFormatError:
                # Acceptable only if the response status is an error code.
                # Otherwise its the API or client misbehaving.
                self.raise_error_from_status(resp, None)
                raise  # Not accepted!
        else:
            body = None

        if resp.status in expected_errors:
            raise exceptions.from_response(resp, body)

        return resp, body

    def raise_error_from_status(self, resp, body):
        if resp.status in expected_errors:
            raise exceptions.from_response(resp, body)

    def morph_request(self, kwargs):
        kwargs['headers']['Accept'] = 'application/json'
        kwargs['headers']['Content-Type'] = 'application/json'
        if 'body' in kwargs:
            kwargs['body'] = json.dumps(kwargs['body'])

    def morph_response_body(self, body_string):
        try:
            return json.loads(body_string)
        except ValueError:
            raise exceptions.ResponseFormatError()

    def _time_request(self, url, method, **kwargs):
        start_time = time.time()
        resp, body = self.request(url, method, **kwargs)
        self.times.append(("%s %s" % (method, url),
                           start_time, time.time()))
        return resp, body

    def _cs_request(self, url, method, **kwargs):
        def request():
            kwargs.setdefault('headers', {})['X-Auth-Token'] = self.auth_token
            if self.tenant:
                kwargs['headers']['X-Auth-Project-Id'] = self.tenant

            resp, body = self._time_request(self.service_url + url, method,
                                            **kwargs)
            return resp, body

        if not self.auth_token or not self.service_url:
            self.authenticate()

        # Perform the request once. If we get a 401 back then it
        # might be because the auth token expired, so try to
        # re-authenticate and try again. If it still fails, bail.
        try:
            return request()
        except exceptions.Unauthorized:
            self.authenticate()
            return request()

    def get(self, url, **kwargs):
        return self._cs_request(url, 'GET', **kwargs)

    def patch(self, url, **kwargs):
        return self._cs_request(url, 'PATCH', **kwargs)

    def post(self, url, **kwargs):
        return self._cs_request(url, 'POST', **kwargs)

    def put(self, url, **kwargs):
        return self._cs_request(url, 'PUT', **kwargs)

    def delete(self, url, **kwargs):
        return self._cs_request(url, 'DELETE', **kwargs)

    def authenticate(self):
        """Auths the client and gets a token. May optionally set a service url.

        The client will get auth errors until the authentication step
        occurs. Additionally, if a service_url was not explicitly given in
        the clients __init__ method, one will be obtained from the auth
        service.

        """
        catalog = self.authenticator.authenticate()
        if self.service_url:
            possible_service_url = None
        else:
            if self.endpoint_type == "publicURL":
                possible_service_url = catalog.get_public_url()
            elif self.endpoint_type == "adminURL":
                possible_service_url = catalog.get_management_url()
        self.authenticate_with_token(catalog.get_token(), possible_service_url)

    def authenticate_with_token(self, token, service_url=None):
        self.auth_token = token
        if not self.service_url:
            if not service_url:
                raise exceptions.ServiceUrlNotGiven()
            else:
                self.service_url = service_url


class Dbaas(object):
    """Top-level object to access the Rackspace Database as a Service API.

    Create an instance with your creds::

        >> red = Dbaas(USERNAME, API_KEY, TENANT, AUTH_URL, SERVICE_NAME, \
                        SERVICE_URL)

    Then call methods on its managers::

        >> red.instances.list()
        ...
        >> red.flavors.list()
        ...

    &c.
    """

    def __init__(self, username, api_key, tenant=None, auth_url=None,
                 service_type='database', service_name=None,
                 service_url=None, insecure=False, auth_strategy='keystone',
                 region_name=None, client_cls=TroveHTTPClient):

        from troveclient.compat import versions
        from troveclient.v1 import accounts
        from troveclient.v1 import backups
        from troveclient.v1 import clusters
        from troveclient.v1 import configurations
        from troveclient.v1 import databases
        from troveclient.v1 import datastores
        from troveclient.v1 import diagnostics
        from troveclient.v1 import flavors
        from troveclient.v1 import hosts
        from troveclient.v1 import instances
        from troveclient.v1 import limits
        from troveclient.v1 import management
        from troveclient.v1 import metadata
        from troveclient.v1 import quota
        from troveclient.v1 import root
        from troveclient.v1 import security_groups
        from troveclient.v1 import storage
        from troveclient.v1 import users

        self.client = client_cls(username, api_key, tenant, auth_url,
                                 service_type=service_type,
                                 service_name=service_name,
                                 service_url=service_url,
                                 insecure=insecure,
                                 auth_strategy=auth_strategy,
                                 region_name=region_name)
        self.versions = versions.Versions(self)
        self.databases = databases.Databases(self)
        self.flavors = flavors.Flavors(self)
        self.instances = instances.Instances(self)
        self.limits = limits.Limits(self)
        self.users = users.Users(self)
        self.root = root.Root(self)
        self.hosts = hosts.Hosts(self)
        self.quota = quota.Quotas(self)
        self.backups = backups.Backups(self)
        self.clusters = clusters.Clusters(self)
        self.security_groups = security_groups.SecurityGroups(self)
        self.security_group_rules = security_groups.SecurityGroupRules(self)
        self.datastores = datastores.Datastores(self)
        self.datastore_versions = datastores.DatastoreVersions(self)
        self.datastore_version_members = (datastores.
                                          DatastoreVersionMembers(self))
        self.storage = storage.StorageInfo(self)
        self.management = management.Management(self)
        self.mgmt_cluster = management.MgmtClusters(self)
        self.mgmt_flavor = management.MgmtFlavors(self)
        self.accounts = accounts.Accounts(self)
        self.diagnostics = diagnostics.DiagnosticsInterrogator(self)
        self.hwinfo = diagnostics.HwInfoInterrogator(self)
        self.configurations = configurations.Configurations(self)
        config_parameters = configurations.ConfigurationParameters(self)
        self.configuration_parameters = config_parameters
        self.metadata = metadata.Metadata(self)
        self.mgmt_configs = management.MgmtConfigurationParameters(self)

        class Mgmt(object):
            def __init__(self, dbaas):
                self.instances = dbaas.management
                self.hosts = dbaas.hosts
                self.accounts = dbaas.accounts
                self.storage = dbaas.storage

        self.mgmt = Mgmt(self)

    def set_management_url(self, url):
        self.client.management_url = url

    def get_timings(self):
        return self.client.get_timings()

    def authenticate(self):
        """Authenticate against the server.

        This is called to perform an authentication to retrieve a token.

        Returns on success; raises :exc:`exceptions.Unauthorized` if the
        credentials are wrong.
        """
        self.client.authenticate()
