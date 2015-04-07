# -*- coding: utf-8 -*-
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

from keystoneclient.v2_0 import client as ksclient

from ironicclient.common.i18n import _
from ironicclient.common import utils
from ironicclient import exc


def _get_ksclient(**kwargs):
    """Get an endpoint and auth token from Keystone.

    :param kwargs: keyword args containing credentials:
            * username: name of user
            * password: user's password
            * auth_url: endpoint to authenticate against
            * insecure: allow insecure SSL (no cert verification)
            * tenant_{name|id}: name or ID of tenant
    """
    return ksclient.Client(username=kwargs.get('username'),
                           password=kwargs.get('password'),
                           tenant_id=kwargs.get('tenant_id'),
                           tenant_name=kwargs.get('tenant_name'),
                           auth_url=kwargs.get('auth_url'),
                           insecure=kwargs.get('insecure'))


def _get_endpoint(client, **kwargs):
    """Get an endpoint using the provided keystone client."""
    attr = None
    filter_value = None
    if kwargs.get('region_name'):
        attr = 'region'
        filter_value = kwargs.get('region_name')
    return client.service_catalog.url_for(
        service_type=kwargs.get('service_type') or 'baremetal',
        attr=attr,
        filter_value=filter_value,
        endpoint_type=kwargs.get('endpoint_type') or 'publicURL')


def get_client(api_version, **kwargs):
    """Get an authenticated client, based on the credentials in args.

    :param api_version: the API version to use. Valid value: '1'.
    :param kwargs: keyword args containing credentials, either:
            * os_auth_token: pre-existing token to re-use
            * ironic_url: ironic API endpoint
            or:
            * os_username: name of user
            * os_password: user's password
            * os_auth_url: endpoint to authenticate against
            * insecure: allow insecure SSL (no cert verification)
            * os_tenant_{name|id}: name or ID of tenant
    """

    if kwargs.get('os_auth_token') and kwargs.get('ironic_url'):
        token = kwargs.get('os_auth_token')
        endpoint = kwargs.get('ironic_url')
        auth_ref = None
    elif (kwargs.get('os_username') and
          kwargs.get('os_password') and
          kwargs.get('os_auth_url') and
          (kwargs.get('os_tenant_id') or kwargs.get('os_tenant_name'))):

        ks_kwargs = {
            'username': kwargs.get('os_username'),
            'password': kwargs.get('os_password'),
            'tenant_id': kwargs.get('os_tenant_id'),
            'tenant_name': kwargs.get('os_tenant_name'),
            'auth_url': kwargs.get('os_auth_url'),
            'service_type': kwargs.get('os_service_type'),
            'endpoint_type': kwargs.get('os_endpoint_type'),
            'insecure': kwargs.get('insecure'),
        }
        _ksclient = _get_ksclient(**ks_kwargs)
        token = (kwargs.get('os_auth_token')
                 if kwargs.get('os_auth_token')
                 else _ksclient.auth_token)

        ks_kwargs['region_name'] = kwargs.get('os_region_name')
        endpoint = (kwargs.get('ironic_url') or
                    _get_endpoint(_ksclient, **ks_kwargs))

        auth_ref = _ksclient.auth_ref

    else:
        e = (_('Must provide Keystone credentials or user-defined endpoint '
               'and token'))
        raise exc.AmbiguousAuthSystem(e)

    cli_kwargs = {
        'token': token,
        'insecure': kwargs.get('insecure'),
        'timeout': kwargs.get('timeout'),
        'ca_file': kwargs.get('ca_file'),
        'cert_file': kwargs.get('cert_file'),
        'key_file': kwargs.get('key_file'),
        'auth_ref': auth_ref,
        'os_ironic_api_version': kwargs.get('os_ironic_api_version'),
    }

    return Client(api_version, endpoint, **cli_kwargs)


def Client(version, *args, **kwargs):
    module = utils.import_versioned_module(version, 'client')
    client_class = getattr(module, 'Client')
    return client_class(*args, **kwargs)
