# Copyright 2012 OpenStack Foundation.
# All Rights Reserved
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
#

"""Manage access to the clients, including authenticating when needed.
"""

import logging

from neutronclient import client
from neutronclient.neutron import client as neutron_client


LOG = logging.getLogger(__name__)


class ClientCache(object):
    """Descriptor class for caching created client handles."""

    def __init__(self, factory):
        self.factory = factory
        self._handle = None

    def __get__(self, instance, owner):
        # Tell the ClientManager to login to keystone
        if self._handle is None:
            self._handle = self.factory(instance)
        return self._handle


class ClientManager(object):
    """Manages access to API clients, including authentication."""
    neutron = ClientCache(neutron_client.make_client)
    # Provide support for old quantum commands (for example
    # in stable versions)
    quantum = neutron

    def __init__(self, token=None, url=None,
                 auth_url=None,
                 endpoint_type=None,
                 tenant_name=None,
                 tenant_id=None,
                 username=None,
                 user_id=None,
                 password=None,
                 region_name=None,
                 api_version=None,
                 auth_strategy=None,
                 insecure=False,
                 ca_cert=None,
                 log_credentials=False,
                 service_type=None,
                 timeout=None,
                 retries=0,
                 raise_errors=True,
                 session=None,
                 auth=None,
                 ):
        self._token = token
        self._url = url
        self._auth_url = auth_url
        self._service_type = service_type
        self._endpoint_type = endpoint_type
        self._tenant_name = tenant_name
        self._tenant_id = tenant_id
        self._username = username
        self._user_id = user_id
        self._password = password
        self._region_name = region_name
        self._api_version = api_version
        self._service_catalog = None
        self._auth_strategy = auth_strategy
        self._insecure = insecure
        self._ca_cert = ca_cert
        self._log_credentials = log_credentials
        self._timeout = timeout
        self._retries = retries
        self._raise_errors = raise_errors
        self._session = session
        self._auth = auth
        return

    def initialize(self):
        if not self._url:
            httpclient = client.construct_http_client(
                username=self._username,
                user_id=self._user_id,
                tenant_name=self._tenant_name,
                tenant_id=self._tenant_id,
                password=self._password,
                region_name=self._region_name,
                auth_url=self._auth_url,
                service_type=self._service_type,
                endpoint_type=self._endpoint_type,
                insecure=self._insecure,
                ca_cert=self._ca_cert,
                timeout=self._timeout,
                session=self._session,
                auth=self._auth,
                log_credentials=self._log_credentials)
            httpclient.authenticate()
            # Populate other password flow attributes
            self._token = httpclient.auth_token
            self._url = httpclient.endpoint_url
