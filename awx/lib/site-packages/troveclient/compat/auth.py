#    Copyright 2012 OpenStack Foundation
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

from __future__ import print_function
import six
from troveclient.compat import exceptions


def get_authenticator_cls(cls_or_name):
    """Factory method to retrieve Authenticator class."""
    if isinstance(cls_or_name, type):
        return cls_or_name
    elif isinstance(cls_or_name, six.string_types):
        if cls_or_name == "keystone":
            return KeyStoneV2Authenticator
        elif cls_or_name == "rax":
            return RaxAuthenticator
        elif cls_or_name == "rax2":
            return RaxAuthenticator2
        elif cls_or_name == "auth1.1":
            return Auth1_1
        elif cls_or_name == "fake":
            return FakeAuth

    raise ValueError("Could not determine authenticator class from the given "
                     "value %r." % cls_or_name)


class Authenticator(object):
    """Helper class to perform Keystone or other miscellaneous authentication.

    The "authenticate" method returns a ServiceCatalog, which can be used
    to obtain a token.

    """

    URL_REQUIRED = True

    def __init__(self, client, type, url, username, password, tenant,
                 region=None, service_type=None, service_name=None,
                 service_url=None):
        self.client = client
        self.type = type
        self.url = url
        self.username = username
        self.password = password
        self.tenant = tenant
        self.region = region
        self.service_type = service_type
        self.service_name = service_name
        self.service_url = service_url

    def _authenticate(self, url, body, root_key='access'):
        """Authenticate and extract the service catalog."""
        # Make sure we follow redirects when trying to reach Keystone
        tmp_follow_all_redirects = self.client.follow_all_redirects
        self.client.follow_all_redirects = True

        try:
            resp, body = self.client._time_request(url, "POST", body=body)
        finally:
            self.client.follow_all_redirects = tmp_follow_all_redirects

        if resp.status == 200:  # content must always present
            try:
                return ServiceCatalog(body, region=self.region,
                                      service_type=self.service_type,
                                      service_name=self.service_name,
                                      service_url=self.service_url,
                                      root_key=root_key)
            except exceptions.AmbiguousEndpoints:
                print("Found more than one valid endpoint. Use a more "
                      "restrictive filter")
                raise
            except KeyError:
                raise exceptions.AuthorizationFailure()
            except exceptions.EndpointNotFound:
                print("Could not find any suitable endpoint. Correct region?")
                raise

        elif resp.status == 305:
            return resp['location']
        else:
            raise exceptions.from_response(resp, body)

    def authenticate(self):
        raise NotImplementedError("Missing authenticate method.")


class KeyStoneV2Authenticator(Authenticator):
    def authenticate(self):
        if self.url is None:
            raise exceptions.AuthUrlNotGiven()
        return self._v2_auth(self.url)

    def _v2_auth(self, url):
        """Authenticate against a v2.0 auth service."""
        body = {"auth": {
            "passwordCredentials": {
                "username": self.username,
                "password": self.password}
        }
        }

        if self.tenant:
            body['auth']['tenantName'] = self.tenant

        return self._authenticate(url, body)


class Auth1_1(Authenticator):
    def authenticate(self):
        """Authenticate against a v2.0 auth service."""
        if self.url is None:
            raise exceptions.AuthUrlNotGiven()
        auth_url = self.url
        body = {
            "credentials": {
                "username": self.username,
                "key": self.password
            }}
        return self._authenticate(auth_url, body, root_key='auth')


class RaxAuthenticator(Authenticator):
    def authenticate(self):
        if self.url is None:
            raise exceptions.AuthUrlNotGiven()
        return self._rax_auth(self.url)

    def _rax_auth(self, url):
        """Authenticate against the Rackspace auth service."""
        body = {'auth': {
            'RAX-KSKEY:apiKeyCredentials': {
                'username': self.username,
                'apiKey': self.password,
                'tenantName': self.tenant}
        }
        }

        return self._authenticate(self.url, body)


class RaxAuthenticator2(RaxAuthenticator):
    """Rax specific authenticator.

    Necessary to be able to call using the same auth url as the new client
    uses for Rax auth.
    """

    def __init__(self, *args, **kwargs):
        super(RaxAuthenticator2, self).__init__(*args, **kwargs)
        self.url = "%s/tokens" % self.url


class FakeAuth(Authenticator):
    """Useful for faking auth."""

    def authenticate(self):
        class FakeCatalog(object):
            def __init__(self, auth):
                self.auth = auth

            def get_public_url(self):
                return "%s/%s" % ('http://localhost:8779/v1.0',
                                  self.auth.tenant)

            def get_token(self):
                return self.auth.tenant

        return FakeCatalog(self)


class ServiceCatalog(object):
    """Represents a Keystone Service Catalog which describes a service.

    This class has methods to obtain a valid token as well as a public service
    url and a management url.

    """

    def __init__(self, resource_dict, region=None, service_type=None,
                 service_name=None, service_url=None, root_key='access'):
        self.catalog = resource_dict
        self.region = region
        self.service_type = service_type
        self.service_name = service_name
        self.service_url = service_url
        self.management_url = None
        self.public_url = None
        self.root_key = root_key
        self._load()

    def _load(self):
        if not self.service_url:
            self.public_url = self._url_for(attr='region',
                                            filter_value=self.region,
                                            endpoint_type="publicURL")
            self.management_url = self._url_for(attr='region',
                                                filter_value=self.region,
                                                endpoint_type="adminURL")
        else:
            self.public_url = self.service_url
            self.management_url = self.service_url

    def get_token(self):
        return self.catalog[self.root_key]['token']['id']

    def get_management_url(self):
        return self.management_url

    def get_public_url(self):
        return self.public_url

    def _url_for(self, attr=None, filter_value=None,
                 endpoint_type='publicURL'):
        """Fetch requested URL.

        Fetch the public URL from the Trove service for a particular
        endpoint attribute. If none given, return the first.
        """
        matching_endpoints = []
        if 'endpoints' in self.catalog:
            # We have a bastardized service catalog. Treat it special. :/
            for endpoint in self.catalog['endpoints']:
                if not filter_value or endpoint[attr] == filter_value:
                    matching_endpoints.append(endpoint)
            if not matching_endpoints:
                raise exceptions.EndpointNotFound()

        # We don't always get a service catalog back ...
        if 'serviceCatalog' not in self.catalog[self.root_key]:
            raise exceptions.EndpointNotFound()

        # Full catalog ...
        catalog = self.catalog[self.root_key]['serviceCatalog']

        for service in catalog:
            if service.get("type") != self.service_type:
                continue

            if (self.service_name and self.service_type == 'database' and
                    service.get('name') != self.service_name):
                continue

            endpoints = service['endpoints']
            for endpoint in endpoints:
                if not filter_value or endpoint.get(attr) == filter_value:
                    endpoint["serviceName"] = service.get("name")
                    matching_endpoints.append(endpoint)

        if not matching_endpoints:
            raise exceptions.EndpointNotFound()
        elif len(matching_endpoints) > 1:
            raise exceptions.AmbiguousEndpoints(endpoints=matching_endpoints)
        else:
            return matching_endpoints[0].get(endpoint_type, None)
