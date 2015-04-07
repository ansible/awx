# Copyright 2012 OpenStack Foundation.
# Copyright 2015 Hewlett-Packard Development Company, L.P.
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

import logging
import time

import requests
import six.moves.urllib.parse as urlparse

from neutronclient import client
from neutronclient.common import constants
from neutronclient.common import exceptions
from neutronclient.common import serializer
from neutronclient.common import utils
from neutronclient.i18n import _


_logger = logging.getLogger(__name__)


def exception_handler_v20(status_code, error_content):
    """Exception handler for API v2.0 client.

    This routine generates the appropriate Neutron exception according to
    the contents of the response body.

    :param status_code: HTTP error status code
    :param error_content: deserialized body of error response
    """
    error_dict = None
    if isinstance(error_content, dict):
        error_dict = error_content.get('NeutronError')
    # Find real error type
    bad_neutron_error_flag = False
    if error_dict:
        # If Neutron key is found, it will definitely contain
        # a 'message' and 'type' keys?
        try:
            error_type = error_dict['type']
            error_message = error_dict['message']
            if error_dict['detail']:
                error_message += "\n" + error_dict['detail']
        except Exception:
            bad_neutron_error_flag = True
        if not bad_neutron_error_flag:
            # If corresponding exception is defined, use it.
            client_exc = getattr(exceptions, '%sClient' % error_type, None)
            # Otherwise look up per status-code client exception
            if not client_exc:
                client_exc = exceptions.HTTP_EXCEPTION_MAP.get(status_code)
            if client_exc:
                raise client_exc(message=error_message,
                                 status_code=status_code)
            else:
                raise exceptions.NeutronClientException(
                    status_code=status_code, message=error_message)
        else:
            raise exceptions.NeutronClientException(status_code=status_code,
                                                    message=error_dict)
    else:
        message = None
        if isinstance(error_content, dict):
            message = error_content.get('message')
        if message:
            raise exceptions.NeutronClientException(status_code=status_code,
                                                    message=message)

    # If we end up here the exception was not a neutron error
    msg = "%s-%s" % (status_code, error_content)
    raise exceptions.NeutronClientException(status_code=status_code,
                                            message=msg)


class APIParamsCall(object):
    """A Decorator to add support for format and tenant overriding and filters.
    """
    def __init__(self, function):
        self.function = function

    def __get__(self, instance, owner):
        def with_params(*args, **kwargs):
            _format = instance.format
            if 'format' in kwargs:
                instance.format = kwargs['format']
            ret = self.function(instance, *args, **kwargs)
            instance.format = _format
            return ret
        return with_params


class ClientBase(object):
    """Client for the OpenStack Neutron v2.0 API.

    :param string username: Username for authentication. (optional)
    :param string user_id: User ID for authentication. (optional)
    :param string password: Password for authentication. (optional)
    :param string token: Token for authentication. (optional)
    :param string tenant_name: Tenant name. (optional)
    :param string tenant_id: Tenant id. (optional)
    :param string auth_strategy: 'keystone' by default, 'noauth' for no
                                 authentication against keystone. (optional)
    :param string auth_url: Keystone service endpoint for authorization.
    :param string service_type: Network service type to pull from the
                                keystone catalog (e.g. 'network') (optional)
    :param string endpoint_type: Network service endpoint type to pull from the
                                 keystone catalog (e.g. 'publicURL',
                                 'internalURL', or 'adminURL') (optional)
    :param string region_name: Name of a region to select when choosing an
                               endpoint from the service catalog.
    :param string endpoint_url: A user-supplied endpoint URL for the neutron
                            service.  Lazy-authentication is possible for API
                            service calls if endpoint is set at
                            instantiation.(optional)
    :param integer timeout: Allows customization of the timeout for client
                            http requests. (optional)
    :param bool insecure: SSL certificate validation. (optional)
    :param bool log_credentials: Allow for logging of passwords or not.
                                 Defaults to False. (optional)
    :param string ca_cert: SSL CA bundle file to use. (optional)
    :param integer retries: How many times idempotent (GET, PUT, DELETE)
                            requests to Neutron server should be retried if
                            they fail (default: 0).
    :param bool raise_errors: If True then exceptions caused by connection
                              failure are propagated to the caller.
                              (default: True)
    :param session: Keystone client auth session to use. (optional)
    :param auth: Keystone auth plugin to use. (optional)

    Example::

        from neutronclient.v2_0 import client
        neutron = client.Client(username=USER,
                                password=PASS,
                                tenant_name=TENANT_NAME,
                                auth_url=KEYSTONE_URL)

        nets = neutron.list_networks()
        ...

    """

    # API has no way to report plurals, so we have to hard code them
    # This variable should be overridden by a child class.
    EXTED_PLURALS = {}

    def __init__(self, **kwargs):
        """Initialize a new client for the Neutron v2.0 API."""
        super(ClientBase, self).__init__()
        self.retries = kwargs.pop('retries', 0)
        self.raise_errors = kwargs.pop('raise_errors', True)
        self.httpclient = client.construct_http_client(**kwargs)
        self.version = '2.0'
        self.format = 'json'
        self.action_prefix = "/v%s" % (self.version)
        self.retry_interval = 1

    def _handle_fault_response(self, status_code, response_body):
        # Create exception with HTTP status code and message
        _logger.debug("Error message: %s", response_body)
        # Add deserialized error message to exception arguments
        try:
            des_error_body = self.deserialize(response_body, status_code)
        except Exception:
            # If unable to deserialized body it is probably not a
            # Neutron error
            des_error_body = {'message': response_body}
        # Raise the appropriate exception
        exception_handler_v20(status_code, des_error_body)

    def do_request(self, method, action, body=None, headers=None, params=None):
        # Add format and tenant_id
        action += ".%s" % self.format
        action = self.action_prefix + action
        if type(params) is dict and params:
            params = utils.safe_encode_dict(params)
            action += '?' + urlparse.urlencode(params, doseq=1)

        if body:
            body = self.serialize(body)

        resp, replybody = self.httpclient.do_request(
            action, method, body=body,
            content_type=self.content_type())

        status_code = resp.status_code
        if status_code in (requests.codes.ok,
                           requests.codes.created,
                           requests.codes.accepted,
                           requests.codes.no_content):
            return self.deserialize(replybody, status_code)
        else:
            if not replybody:
                replybody = resp.reason
            self._handle_fault_response(status_code, replybody)

    def get_auth_info(self):
        return self.httpclient.get_auth_info()

    def serialize(self, data):
        """Serializes a dictionary into either XML or JSON.

        A dictionary with a single key can be passed and it can contain any
        structure.
        """
        if data is None:
            return None
        elif type(data) is dict:
            return serializer.Serializer(
                self.get_attr_metadata()).serialize(data, self.content_type())
        else:
            raise Exception(_("Unable to serialize object of type = '%s'") %
                            type(data))

    def deserialize(self, data, status_code):
        """Deserializes an XML or JSON string into a dictionary."""
        if status_code == 204:
            return data
        return serializer.Serializer(self.get_attr_metadata()).deserialize(
            data, self.content_type())['body']

    def get_attr_metadata(self):
        if self.format == 'json':
            return {}
        old_request_format = self.format
        self.format = 'json'
        exts = self.list_extensions()['extensions']
        self.format = old_request_format
        ns = dict([(ext['alias'], ext['namespace']) for ext in exts])
        self.EXTED_PLURALS.update(constants.PLURALS)
        return {'plurals': self.EXTED_PLURALS,
                'xmlns': constants.XML_NS_V20,
                constants.EXT_NS: ns}

    def content_type(self, _format=None):
        """Returns the mime-type for either 'xml' or 'json'.

        Defaults to the currently set format.
        """
        _format = _format or self.format
        return "application/%s" % (_format)

    def retry_request(self, method, action, body=None,
                      headers=None, params=None):
        """Call do_request with the default retry configuration.

        Only idempotent requests should retry failed connection attempts.
        :raises: ConnectionFailed if the maximum # of retries is exceeded
        """
        max_attempts = self.retries + 1
        for i in range(max_attempts):
            try:
                return self.do_request(method, action, body=body,
                                       headers=headers, params=params)
            except exceptions.ConnectionFailed:
                # Exception has already been logged by do_request()
                if i < self.retries:
                    _logger.debug('Retrying connection to Neutron service')
                    time.sleep(self.retry_interval)
                elif self.raise_errors:
                    raise

        if self.retries:
            msg = (_("Failed to connect to Neutron server after %d attempts")
                   % max_attempts)
        else:
            msg = _("Failed to connect Neutron server")

        raise exceptions.ConnectionFailed(reason=msg)

    def delete(self, action, body=None, headers=None, params=None):
        return self.retry_request("DELETE", action, body=body,
                                  headers=headers, params=params)

    def get(self, action, body=None, headers=None, params=None):
        return self.retry_request("GET", action, body=body,
                                  headers=headers, params=params)

    def post(self, action, body=None, headers=None, params=None):
        # Do not retry POST requests to avoid the orphan objects problem.
        return self.do_request("POST", action, body=body,
                               headers=headers, params=params)

    def put(self, action, body=None, headers=None, params=None):
        return self.retry_request("PUT", action, body=body,
                                  headers=headers, params=params)

    def list(self, collection, path, retrieve_all=True, **params):
        if retrieve_all:
            res = []
            for r in self._pagination(collection, path, **params):
                res.extend(r[collection])
            return {collection: res}
        else:
            return self._pagination(collection, path, **params)

    def _pagination(self, collection, path, **params):
        if params.get('page_reverse', False):
            linkrel = 'previous'
        else:
            linkrel = 'next'
        next = True
        while next:
            res = self.get(path, params=params)
            yield res
            next = False
            try:
                for link in res['%s_links' % collection]:
                    if link['rel'] == linkrel:
                        query_str = urlparse.urlparse(link['href']).query
                        params = urlparse.parse_qs(query_str)
                        next = True
                        break
            except KeyError:
                break


class Client(ClientBase):

    networks_path = "/networks"
    network_path = "/networks/%s"
    ports_path = "/ports"
    port_path = "/ports/%s"
    subnets_path = "/subnets"
    subnet_path = "/subnets/%s"
    quotas_path = "/quotas"
    quota_path = "/quotas/%s"
    extensions_path = "/extensions"
    extension_path = "/extensions/%s"
    routers_path = "/routers"
    router_path = "/routers/%s"
    floatingips_path = "/floatingips"
    floatingip_path = "/floatingips/%s"
    security_groups_path = "/security-groups"
    security_group_path = "/security-groups/%s"
    security_group_rules_path = "/security-group-rules"
    security_group_rule_path = "/security-group-rules/%s"
    vpnservices_path = "/vpn/vpnservices"
    vpnservice_path = "/vpn/vpnservices/%s"
    ipsecpolicies_path = "/vpn/ipsecpolicies"
    ipsecpolicy_path = "/vpn/ipsecpolicies/%s"
    ikepolicies_path = "/vpn/ikepolicies"
    ikepolicy_path = "/vpn/ikepolicies/%s"
    ipsec_site_connections_path = "/vpn/ipsec-site-connections"
    ipsec_site_connection_path = "/vpn/ipsec-site-connections/%s"

    lbaas_loadbalancers_path = "/lbaas/loadbalancers"
    lbaas_loadbalancer_path = "/lbaas/loadbalancers/%s"
    lbaas_listeners_path = "/lbaas/listeners"
    lbaas_listener_path = "/lbaas/listeners/%s"
    lbaas_pools_path = "/lbaas/pools"
    lbaas_pool_path = "/lbaas/pools/%s"
    lbaas_healthmonitors_path = "/lbaas/healthmonitors"
    lbaas_healthmonitor_path = "/lbaas/healthmonitors/%s"
    lbaas_members_path = lbaas_pool_path + "/members"
    lbaas_member_path = lbaas_pool_path + "/members/%s"

    vips_path = "/lb/vips"
    vip_path = "/lb/vips/%s"
    pools_path = "/lb/pools"
    pool_path = "/lb/pools/%s"
    pool_path_stats = "/lb/pools/%s/stats"
    members_path = "/lb/members"
    member_path = "/lb/members/%s"
    health_monitors_path = "/lb/health_monitors"
    health_monitor_path = "/lb/health_monitors/%s"
    associate_pool_health_monitors_path = "/lb/pools/%s/health_monitors"
    disassociate_pool_health_monitors_path = (
        "/lb/pools/%(pool)s/health_monitors/%(health_monitor)s")
    qos_queues_path = "/qos-queues"
    qos_queue_path = "/qos-queues/%s"
    agents_path = "/agents"
    agent_path = "/agents/%s"
    network_gateways_path = "/network-gateways"
    network_gateway_path = "/network-gateways/%s"
    gateway_devices_path = "/gateway-devices"
    gateway_device_path = "/gateway-devices/%s"
    service_providers_path = "/service-providers"
    credentials_path = "/credentials"
    credential_path = "/credentials/%s"
    network_profiles_path = "/network_profiles"
    network_profile_path = "/network_profiles/%s"
    network_profile_bindings_path = "/network_profile_bindings"
    policy_profiles_path = "/policy_profiles"
    policy_profile_path = "/policy_profiles/%s"
    policy_profile_bindings_path = "/policy_profile_bindings"
    metering_labels_path = "/metering/metering-labels"
    metering_label_path = "/metering/metering-labels/%s"
    metering_label_rules_path = "/metering/metering-label-rules"
    metering_label_rule_path = "/metering/metering-label-rules/%s"
    packet_filters_path = "/packet_filters"
    packet_filter_path = "/packet_filters/%s"

    DHCP_NETS = '/dhcp-networks'
    DHCP_AGENTS = '/dhcp-agents'
    L3_ROUTERS = '/l3-routers'
    L3_AGENTS = '/l3-agents'
    LOADBALANCER_POOLS = '/loadbalancer-pools'
    LOADBALANCER_AGENT = '/loadbalancer-agent'
    firewall_rules_path = "/fw/firewall_rules"
    firewall_rule_path = "/fw/firewall_rules/%s"
    firewall_policies_path = "/fw/firewall_policies"
    firewall_policy_path = "/fw/firewall_policies/%s"
    firewall_policy_insert_path = "/fw/firewall_policies/%s/insert_rule"
    firewall_policy_remove_path = "/fw/firewall_policies/%s/remove_rule"
    firewalls_path = "/fw/firewalls"
    firewall_path = "/fw/firewalls/%s"
    net_partitions_path = "/net-partitions"
    net_partition_path = "/net-partitions/%s"

    # API has no way to report plurals, so we have to hard code them
    EXTED_PLURALS = {'routers': 'router',
                     'floatingips': 'floatingip',
                     'service_types': 'service_type',
                     'service_definitions': 'service_definition',
                     'security_groups': 'security_group',
                     'security_group_rules': 'security_group_rule',
                     'ipsecpolicies': 'ipsecpolicy',
                     'ikepolicies': 'ikepolicy',
                     'ipsec_site_connections': 'ipsec_site_connection',
                     'vpnservices': 'vpnservice',
                     'vips': 'vip',
                     'pools': 'pool',
                     'members': 'member',
                     'health_monitors': 'health_monitor',
                     'quotas': 'quota',
                     'service_providers': 'service_provider',
                     'firewall_rules': 'firewall_rule',
                     'firewall_policies': 'firewall_policy',
                     'firewalls': 'firewall',
                     'metering_labels': 'metering_label',
                     'metering_label_rules': 'metering_label_rule',
                     'net_partitions': 'net_partition',
                     'packet_filters': 'packet_filter',
                     'loadbalancers': 'loadbalancer',
                     'listeners': 'listener',
                     'lbaas_pools': 'lbaas_pool',
                     'lbaas_healthmonitors': 'lbaas_healthmonitor',
                     'lbaas_members': 'lbaas_member',
                     'healthmonitors': 'healthmonitor',
                     }

    @APIParamsCall
    def get_quotas_tenant(self, **_params):
        """Fetch tenant info in server's context for following quota operation.
        """
        return self.get(self.quota_path % 'tenant', params=_params)

    @APIParamsCall
    def list_quotas(self, **_params):
        """Fetch all tenants' quotas."""
        return self.get(self.quotas_path, params=_params)

    @APIParamsCall
    def show_quota(self, tenant_id, **_params):
        """Fetch information of a certain tenant's quotas."""
        return self.get(self.quota_path % (tenant_id), params=_params)

    @APIParamsCall
    def update_quota(self, tenant_id, body=None):
        """Update a tenant's quotas."""
        return self.put(self.quota_path % (tenant_id), body=body)

    @APIParamsCall
    def delete_quota(self, tenant_id):
        """Delete the specified tenant's quota values."""
        return self.delete(self.quota_path % (tenant_id))

    @APIParamsCall
    def list_extensions(self, **_params):
        """Fetch a list of all exts on server side."""
        return self.get(self.extensions_path, params=_params)

    @APIParamsCall
    def show_extension(self, ext_alias, **_params):
        """Fetch a list of all exts on server side."""
        return self.get(self.extension_path % ext_alias, params=_params)

    @APIParamsCall
    def list_ports(self, retrieve_all=True, **_params):
        """Fetches a list of all networks for a tenant."""
        # Pass filters in "params" argument to do_request
        return self.list('ports', self.ports_path, retrieve_all,
                         **_params)

    @APIParamsCall
    def show_port(self, port, **_params):
        """Fetches information of a certain network."""
        return self.get(self.port_path % (port), params=_params)

    @APIParamsCall
    def create_port(self, body=None):
        """Creates a new port."""
        return self.post(self.ports_path, body=body)

    @APIParamsCall
    def update_port(self, port, body=None):
        """Updates a port."""
        return self.put(self.port_path % (port), body=body)

    @APIParamsCall
    def delete_port(self, port):
        """Deletes the specified port."""
        return self.delete(self.port_path % (port))

    @APIParamsCall
    def list_networks(self, retrieve_all=True, **_params):
        """Fetches a list of all networks for a tenant."""
        # Pass filters in "params" argument to do_request
        return self.list('networks', self.networks_path, retrieve_all,
                         **_params)

    @APIParamsCall
    def show_network(self, network, **_params):
        """Fetches information of a certain network."""
        return self.get(self.network_path % (network), params=_params)

    @APIParamsCall
    def create_network(self, body=None):
        """Creates a new network."""
        return self.post(self.networks_path, body=body)

    @APIParamsCall
    def update_network(self, network, body=None):
        """Updates a network."""
        return self.put(self.network_path % (network), body=body)

    @APIParamsCall
    def delete_network(self, network):
        """Deletes the specified network."""
        return self.delete(self.network_path % (network))

    @APIParamsCall
    def list_subnets(self, retrieve_all=True, **_params):
        """Fetches a list of all networks for a tenant."""
        return self.list('subnets', self.subnets_path, retrieve_all,
                         **_params)

    @APIParamsCall
    def show_subnet(self, subnet, **_params):
        """Fetches information of a certain subnet."""
        return self.get(self.subnet_path % (subnet), params=_params)

    @APIParamsCall
    def create_subnet(self, body=None):
        """Creates a new subnet."""
        return self.post(self.subnets_path, body=body)

    @APIParamsCall
    def update_subnet(self, subnet, body=None):
        """Updates a subnet."""
        return self.put(self.subnet_path % (subnet), body=body)

    @APIParamsCall
    def delete_subnet(self, subnet):
        """Deletes the specified subnet."""
        return self.delete(self.subnet_path % (subnet))

    @APIParamsCall
    def list_routers(self, retrieve_all=True, **_params):
        """Fetches a list of all routers for a tenant."""
        # Pass filters in "params" argument to do_request
        return self.list('routers', self.routers_path, retrieve_all,
                         **_params)

    @APIParamsCall
    def show_router(self, router, **_params):
        """Fetches information of a certain router."""
        return self.get(self.router_path % (router), params=_params)

    @APIParamsCall
    def create_router(self, body=None):
        """Creates a new router."""
        return self.post(self.routers_path, body=body)

    @APIParamsCall
    def update_router(self, router, body=None):
        """Updates a router."""
        return self.put(self.router_path % (router), body=body)

    @APIParamsCall
    def delete_router(self, router):
        """Deletes the specified router."""
        return self.delete(self.router_path % (router))

    @APIParamsCall
    def add_interface_router(self, router, body=None):
        """Adds an internal network interface to the specified router."""
        return self.put((self.router_path % router) + "/add_router_interface",
                        body=body)

    @APIParamsCall
    def remove_interface_router(self, router, body=None):
        """Removes an internal network interface from the specified router."""
        return self.put((self.router_path % router) +
                        "/remove_router_interface", body=body)

    @APIParamsCall
    def add_gateway_router(self, router, body=None):
        """Adds an external network gateway to the specified router."""
        return self.put((self.router_path % router),
                        body={'router': {'external_gateway_info': body}})

    @APIParamsCall
    def remove_gateway_router(self, router):
        """Removes an external network gateway from the specified router."""
        return self.put((self.router_path % router),
                        body={'router': {'external_gateway_info': {}}})

    @APIParamsCall
    def list_floatingips(self, retrieve_all=True, **_params):
        """Fetches a list of all floatingips for a tenant."""
        # Pass filters in "params" argument to do_request
        return self.list('floatingips', self.floatingips_path, retrieve_all,
                         **_params)

    @APIParamsCall
    def show_floatingip(self, floatingip, **_params):
        """Fetches information of a certain floatingip."""
        return self.get(self.floatingip_path % (floatingip), params=_params)

    @APIParamsCall
    def create_floatingip(self, body=None):
        """Creates a new floatingip."""
        return self.post(self.floatingips_path, body=body)

    @APIParamsCall
    def update_floatingip(self, floatingip, body=None):
        """Updates a floatingip."""
        return self.put(self.floatingip_path % (floatingip), body=body)

    @APIParamsCall
    def delete_floatingip(self, floatingip):
        """Deletes the specified floatingip."""
        return self.delete(self.floatingip_path % (floatingip))

    @APIParamsCall
    def create_security_group(self, body=None):
        """Creates a new security group."""
        return self.post(self.security_groups_path, body=body)

    @APIParamsCall
    def update_security_group(self, security_group, body=None):
        """Updates a security group."""
        return self.put(self.security_group_path %
                        security_group, body=body)

    @APIParamsCall
    def list_security_groups(self, retrieve_all=True, **_params):
        """Fetches a list of all security groups for a tenant."""
        return self.list('security_groups', self.security_groups_path,
                         retrieve_all, **_params)

    @APIParamsCall
    def show_security_group(self, security_group, **_params):
        """Fetches information of a certain security group."""
        return self.get(self.security_group_path % (security_group),
                        params=_params)

    @APIParamsCall
    def delete_security_group(self, security_group):
        """Deletes the specified security group."""
        return self.delete(self.security_group_path % (security_group))

    @APIParamsCall
    def create_security_group_rule(self, body=None):
        """Creates a new security group rule."""
        return self.post(self.security_group_rules_path, body=body)

    @APIParamsCall
    def delete_security_group_rule(self, security_group_rule):
        """Deletes the specified security group rule."""
        return self.delete(self.security_group_rule_path %
                           (security_group_rule))

    @APIParamsCall
    def list_security_group_rules(self, retrieve_all=True, **_params):
        """Fetches a list of all security group rules for a tenant."""
        return self.list('security_group_rules',
                         self.security_group_rules_path,
                         retrieve_all, **_params)

    @APIParamsCall
    def show_security_group_rule(self, security_group_rule, **_params):
        """Fetches information of a certain security group rule."""
        return self.get(self.security_group_rule_path % (security_group_rule),
                        params=_params)

    @APIParamsCall
    def list_vpnservices(self, retrieve_all=True, **_params):
        """Fetches a list of all configured VPN services for a tenant."""
        return self.list('vpnservices', self.vpnservices_path, retrieve_all,
                         **_params)

    @APIParamsCall
    def show_vpnservice(self, vpnservice, **_params):
        """Fetches information of a specific VPN service."""
        return self.get(self.vpnservice_path % (vpnservice), params=_params)

    @APIParamsCall
    def create_vpnservice(self, body=None):
        """Creates a new VPN service."""
        return self.post(self.vpnservices_path, body=body)

    @APIParamsCall
    def update_vpnservice(self, vpnservice, body=None):
        """Updates a VPN service."""
        return self.put(self.vpnservice_path % (vpnservice), body=body)

    @APIParamsCall
    def delete_vpnservice(self, vpnservice):
        """Deletes the specified VPN service."""
        return self.delete(self.vpnservice_path % (vpnservice))

    @APIParamsCall
    def list_ipsec_site_connections(self, retrieve_all=True, **_params):
        """Fetches all configured IPsecSiteConnections for a tenant."""
        return self.list('ipsec_site_connections',
                         self.ipsec_site_connections_path,
                         retrieve_all,
                         **_params)

    @APIParamsCall
    def show_ipsec_site_connection(self, ipsecsite_conn, **_params):
        """Fetches information of a specific IPsecSiteConnection."""
        return self.get(
            self.ipsec_site_connection_path % (ipsecsite_conn), params=_params
        )

    @APIParamsCall
    def create_ipsec_site_connection(self, body=None):
        """Creates a new IPsecSiteConnection."""
        return self.post(self.ipsec_site_connections_path, body=body)

    @APIParamsCall
    def update_ipsec_site_connection(self, ipsecsite_conn, body=None):
        """Updates an IPsecSiteConnection."""
        return self.put(
            self.ipsec_site_connection_path % (ipsecsite_conn), body=body
        )

    @APIParamsCall
    def delete_ipsec_site_connection(self, ipsecsite_conn):
        """Deletes the specified IPsecSiteConnection."""
        return self.delete(self.ipsec_site_connection_path % (ipsecsite_conn))

    @APIParamsCall
    def list_ikepolicies(self, retrieve_all=True, **_params):
        """Fetches a list of all configured IKEPolicies for a tenant."""
        return self.list('ikepolicies', self.ikepolicies_path, retrieve_all,
                         **_params)

    @APIParamsCall
    def show_ikepolicy(self, ikepolicy, **_params):
        """Fetches information of a specific IKEPolicy."""
        return self.get(self.ikepolicy_path % (ikepolicy), params=_params)

    @APIParamsCall
    def create_ikepolicy(self, body=None):
        """Creates a new IKEPolicy."""
        return self.post(self.ikepolicies_path, body=body)

    @APIParamsCall
    def update_ikepolicy(self, ikepolicy, body=None):
        """Updates an IKEPolicy."""
        return self.put(self.ikepolicy_path % (ikepolicy), body=body)

    @APIParamsCall
    def delete_ikepolicy(self, ikepolicy):
        """Deletes the specified IKEPolicy."""
        return self.delete(self.ikepolicy_path % (ikepolicy))

    @APIParamsCall
    def list_ipsecpolicies(self, retrieve_all=True, **_params):
        """Fetches a list of all configured IPsecPolicies for a tenant."""
        return self.list('ipsecpolicies',
                         self.ipsecpolicies_path,
                         retrieve_all,
                         **_params)

    @APIParamsCall
    def show_ipsecpolicy(self, ipsecpolicy, **_params):
        """Fetches information of a specific IPsecPolicy."""
        return self.get(self.ipsecpolicy_path % (ipsecpolicy), params=_params)

    @APIParamsCall
    def create_ipsecpolicy(self, body=None):
        """Creates a new IPsecPolicy."""
        return self.post(self.ipsecpolicies_path, body=body)

    @APIParamsCall
    def update_ipsecpolicy(self, ipsecpolicy, body=None):
        """Updates an IPsecPolicy."""
        return self.put(self.ipsecpolicy_path % (ipsecpolicy), body=body)

    @APIParamsCall
    def delete_ipsecpolicy(self, ipsecpolicy):
        """Deletes the specified IPsecPolicy."""
        return self.delete(self.ipsecpolicy_path % (ipsecpolicy))

    @APIParamsCall
    def list_loadbalancers(self, retrieve_all=True, **_params):
        """Fetches a list of all loadbalancers for a tenant."""
        return self.list('loadbalancers', self.lbaas_loadbalancers_path,
                         retrieve_all, **_params)

    @APIParamsCall
    def show_loadbalancer(self, lbaas_loadbalancer, **_params):
        """Fetches information for a load balancer."""
        return self.get(self.lbaas_loadbalancer_path % (lbaas_loadbalancer),
                        params=_params)

    @APIParamsCall
    def create_loadbalancer(self, body=None):
        """Creates a new load balancer."""
        return self.post(self.lbaas_loadbalancers_path, body=body)

    @APIParamsCall
    def update_loadbalancer(self, lbaas_loadbalancer, body=None):
        """Updates a load balancer."""
        return self.put(self.lbaas_loadbalancer_path % (lbaas_loadbalancer),
                        body=body)

    @APIParamsCall
    def delete_loadbalancer(self, lbaas_loadbalancer):
        """Deletes the specified load balancer."""
        return self.delete(self.lbaas_loadbalancer_path %
                           (lbaas_loadbalancer))

    @APIParamsCall
    def list_listeners(self, retrieve_all=True, **_params):
        """Fetches a list of all lbaas_listeners for a tenant."""
        return self.list('listeners', self.lbaas_listeners_path,
                         retrieve_all, **_params)

    @APIParamsCall
    def show_listener(self, lbaas_listener, **_params):
        """Fetches information for a lbaas_listener."""
        return self.get(self.lbaas_listener_path % (lbaas_listener),
                        params=_params)

    @APIParamsCall
    def create_listener(self, body=None):
        """Creates a new lbaas_listener."""
        return self.post(self.lbaas_listeners_path, body=body)

    @APIParamsCall
    def update_listener(self, lbaas_listener, body=None):
        """Updates a lbaas_listener."""
        return self.put(self.lbaas_listener_path % (lbaas_listener),
                        body=body)

    @APIParamsCall
    def delete_listener(self, lbaas_listener):
        """Deletes the specified lbaas_listener."""
        return self.delete(self.lbaas_listener_path % (lbaas_listener))

    @APIParamsCall
    def list_lbaas_pools(self, retrieve_all=True, **_params):
        """Fetches a list of all lbaas_pools for a tenant."""
        return self.list('pools', self.lbaas_pools_path,
                         retrieve_all, **_params)

    @APIParamsCall
    def show_lbaas_pool(self, lbaas_pool, **_params):
        """Fetches information for a lbaas_pool."""
        return self.get(self.lbaas_pool_path % (lbaas_pool),
                        params=_params)

    @APIParamsCall
    def create_lbaas_pool(self, body=None):
        """Creates a new lbaas_pool."""
        return self.post(self.lbaas_pools_path, body=body)

    @APIParamsCall
    def update_lbaas_pool(self, lbaas_pool, body=None):
        """Updates a lbaas_pool."""
        return self.put(self.lbaas_pool_path % (lbaas_pool),
                        body=body)

    @APIParamsCall
    def delete_lbaas_pool(self, lbaas_pool):
        """Deletes the specified lbaas_pool."""
        return self.delete(self.lbaas_pool_path % (lbaas_pool))

    @APIParamsCall
    def list_lbaas_healthmonitors(self, retrieve_all=True, **_params):
        """Fetches a list of all lbaas_healthmonitors for a tenant."""
        return self.list('healthmonitors', self.lbaas_healthmonitors_path,
                         retrieve_all, **_params)

    @APIParamsCall
    def show_lbaas_healthmonitor(self, lbaas_healthmonitor, **_params):
        """Fetches information for a lbaas_healthmonitor."""
        return self.get(self.lbaas_healthmonitor_path % (lbaas_healthmonitor),
                        params=_params)

    @APIParamsCall
    def create_lbaas_healthmonitor(self, body=None):
        """Creates a new lbaas_healthmonitor."""
        return self.post(self.lbaas_healthmonitors_path, body=body)

    @APIParamsCall
    def update_lbaas_healthmonitor(self, lbaas_healthmonitor, body=None):
        """Updates a lbaas_healthmonitor."""
        return self.put(self.lbaas_healthmonitor_path % (lbaas_healthmonitor),
                        body=body)

    @APIParamsCall
    def delete_lbaas_healthmonitor(self, lbaas_healthmonitor):
        """Deletes the specified lbaas_healthmonitor."""
        return self.delete(self.lbaas_healthmonitor_path %
                           (lbaas_healthmonitor))

    @APIParamsCall
    def list_lbaas_loadbalancers(self, retrieve_all=True, **_params):
        """Fetches a list of all lbaas_loadbalancers for a tenant."""
        return self.list('loadbalancers', self.lbaas_loadbalancers_path,
                         retrieve_all, **_params)

    @APIParamsCall
    def list_lbaas_members(self, lbaas_pool, retrieve_all=True, **_params):
        """Fetches a list of all lbaas_members for a tenant."""
        return self.list('members', self.lbaas_members_path % lbaas_pool,
                         retrieve_all, **_params)

    @APIParamsCall
    def show_lbaas_member(self, lbaas_member, lbaas_pool, **_params):
        """Fetches information of a certain lbaas_member."""
        return self.get(self.lbaas_member_path % (lbaas_pool, lbaas_member),
                        params=_params)

    @APIParamsCall
    def create_lbaas_member(self, lbaas_pool, body=None):
        """Creates an lbaas_member."""
        return self.post(self.lbaas_members_path % lbaas_pool, body=body)

    @APIParamsCall
    def update_lbaas_member(self, lbaas_member, lbaas_pool, body=None):
        """Updates a lbaas_healthmonitor."""
        return self.put(self.lbaas_member_path % (lbaas_pool, lbaas_member),
                        body=body)

    @APIParamsCall
    def delete_lbaas_member(self, lbaas_member, lbaas_pool):
        """Deletes the specified lbaas_member."""
        return self.delete(self.lbaas_member_path % (lbaas_pool, lbaas_member))

    @APIParamsCall
    def list_vips(self, retrieve_all=True, **_params):
        """Fetches a list of all load balancer vips for a tenant."""
        # Pass filters in "params" argument to do_request
        return self.list('vips', self.vips_path, retrieve_all,
                         **_params)

    @APIParamsCall
    def show_vip(self, vip, **_params):
        """Fetches information of a certain load balancer vip."""
        return self.get(self.vip_path % (vip), params=_params)

    @APIParamsCall
    def create_vip(self, body=None):
        """Creates a new load balancer vip."""
        return self.post(self.vips_path, body=body)

    @APIParamsCall
    def update_vip(self, vip, body=None):
        """Updates a load balancer vip."""
        return self.put(self.vip_path % (vip), body=body)

    @APIParamsCall
    def delete_vip(self, vip):
        """Deletes the specified load balancer vip."""
        return self.delete(self.vip_path % (vip))

    @APIParamsCall
    def list_pools(self, retrieve_all=True, **_params):
        """Fetches a list of all load balancer pools for a tenant."""
        # Pass filters in "params" argument to do_request
        return self.list('pools', self.pools_path, retrieve_all,
                         **_params)

    @APIParamsCall
    def show_pool(self, pool, **_params):
        """Fetches information of a certain load balancer pool."""
        return self.get(self.pool_path % (pool), params=_params)

    @APIParamsCall
    def create_pool(self, body=None):
        """Creates a new load balancer pool."""
        return self.post(self.pools_path, body=body)

    @APIParamsCall
    def update_pool(self, pool, body=None):
        """Updates a load balancer pool."""
        return self.put(self.pool_path % (pool), body=body)

    @APIParamsCall
    def delete_pool(self, pool):
        """Deletes the specified load balancer pool."""
        return self.delete(self.pool_path % (pool))

    @APIParamsCall
    def retrieve_pool_stats(self, pool, **_params):
        """Retrieves stats for a certain load balancer pool."""
        return self.get(self.pool_path_stats % (pool), params=_params)

    @APIParamsCall
    def list_members(self, retrieve_all=True, **_params):
        """Fetches a list of all load balancer members for a tenant."""
        # Pass filters in "params" argument to do_request
        return self.list('members', self.members_path, retrieve_all,
                         **_params)

    @APIParamsCall
    def show_member(self, member, **_params):
        """Fetches information of a certain load balancer member."""
        return self.get(self.member_path % (member), params=_params)

    @APIParamsCall
    def create_member(self, body=None):
        """Creates a new load balancer member."""
        return self.post(self.members_path, body=body)

    @APIParamsCall
    def update_member(self, member, body=None):
        """Updates a load balancer member."""
        return self.put(self.member_path % (member), body=body)

    @APIParamsCall
    def delete_member(self, member):
        """Deletes the specified load balancer member."""
        return self.delete(self.member_path % (member))

    @APIParamsCall
    def list_health_monitors(self, retrieve_all=True, **_params):
        """Fetches a list of all load balancer health monitors for a tenant."""
        # Pass filters in "params" argument to do_request
        return self.list('health_monitors', self.health_monitors_path,
                         retrieve_all, **_params)

    @APIParamsCall
    def show_health_monitor(self, health_monitor, **_params):
        """Fetches information of a certain load balancer health monitor."""
        return self.get(self.health_monitor_path % (health_monitor),
                        params=_params)

    @APIParamsCall
    def create_health_monitor(self, body=None):
        """Creates a new load balancer health monitor."""
        return self.post(self.health_monitors_path, body=body)

    @APIParamsCall
    def update_health_monitor(self, health_monitor, body=None):
        """Updates a load balancer health monitor."""
        return self.put(self.health_monitor_path % (health_monitor), body=body)

    @APIParamsCall
    def delete_health_monitor(self, health_monitor):
        """Deletes the specified load balancer health monitor."""
        return self.delete(self.health_monitor_path % (health_monitor))

    @APIParamsCall
    def associate_health_monitor(self, pool, body):
        """Associate  specified load balancer health monitor and pool."""
        return self.post(self.associate_pool_health_monitors_path % (pool),
                         body=body)

    @APIParamsCall
    def disassociate_health_monitor(self, pool, health_monitor):
        """Disassociate specified load balancer health monitor and pool."""
        path = (self.disassociate_pool_health_monitors_path %
                {'pool': pool, 'health_monitor': health_monitor})
        return self.delete(path)

    @APIParamsCall
    def create_qos_queue(self, body=None):
        """Creates a new queue."""
        return self.post(self.qos_queues_path, body=body)

    @APIParamsCall
    def list_qos_queues(self, **_params):
        """Fetches a list of all queues for a tenant."""
        return self.get(self.qos_queues_path, params=_params)

    @APIParamsCall
    def show_qos_queue(self, queue, **_params):
        """Fetches information of a certain queue."""
        return self.get(self.qos_queue_path % (queue),
                        params=_params)

    @APIParamsCall
    def delete_qos_queue(self, queue):
        """Deletes the specified queue."""
        return self.delete(self.qos_queue_path % (queue))

    @APIParamsCall
    def list_agents(self, **_params):
        """Fetches agents."""
        # Pass filters in "params" argument to do_request
        return self.get(self.agents_path, params=_params)

    @APIParamsCall
    def show_agent(self, agent, **_params):
        """Fetches information of a certain agent."""
        return self.get(self.agent_path % (agent), params=_params)

    @APIParamsCall
    def update_agent(self, agent, body=None):
        """Updates an agent."""
        return self.put(self.agent_path % (agent), body=body)

    @APIParamsCall
    def delete_agent(self, agent):
        """Deletes the specified agent."""
        return self.delete(self.agent_path % (agent))

    @APIParamsCall
    def list_network_gateways(self, **_params):
        """Retrieve network gateways."""
        return self.get(self.network_gateways_path, params=_params)

    @APIParamsCall
    def show_network_gateway(self, gateway_id, **_params):
        """Fetch a network gateway."""
        return self.get(self.network_gateway_path % gateway_id, params=_params)

    @APIParamsCall
    def create_network_gateway(self, body=None):
        """Create a new network gateway."""
        return self.post(self.network_gateways_path, body=body)

    @APIParamsCall
    def update_network_gateway(self, gateway_id, body=None):
        """Update a network gateway."""
        return self.put(self.network_gateway_path % gateway_id, body=body)

    @APIParamsCall
    def delete_network_gateway(self, gateway_id):
        """Delete the specified network gateway."""
        return self.delete(self.network_gateway_path % gateway_id)

    @APIParamsCall
    def connect_network_gateway(self, gateway_id, body=None):
        """Connect a network gateway to the specified network."""
        base_uri = self.network_gateway_path % gateway_id
        return self.put("%s/connect_network" % base_uri, body=body)

    @APIParamsCall
    def disconnect_network_gateway(self, gateway_id, body=None):
        """Disconnect a network from the specified gateway."""
        base_uri = self.network_gateway_path % gateway_id
        return self.put("%s/disconnect_network" % base_uri, body=body)

    @APIParamsCall
    def list_gateway_devices(self, **_params):
        """Retrieve gateway devices."""
        return self.get(self.gateway_devices_path, params=_params)

    @APIParamsCall
    def show_gateway_device(self, gateway_device_id, **_params):
        """Fetch a gateway device."""
        return self.get(self.gateway_device_path % gateway_device_id,
                        params=_params)

    @APIParamsCall
    def create_gateway_device(self, body=None):
        """Create a new gateway device."""
        return self.post(self.gateway_devices_path, body=body)

    @APIParamsCall
    def update_gateway_device(self, gateway_device_id, body=None):
        """Updates a new gateway device."""
        return self.put(self.gateway_device_path % gateway_device_id,
                        body=body)

    @APIParamsCall
    def delete_gateway_device(self, gateway_device_id):
        """Delete the specified gateway device."""
        return self.delete(self.gateway_device_path % gateway_device_id)

    @APIParamsCall
    def list_dhcp_agent_hosting_networks(self, network, **_params):
        """Fetches a list of dhcp agents hosting a network."""
        return self.get((self.network_path + self.DHCP_AGENTS) % network,
                        params=_params)

    @APIParamsCall
    def list_networks_on_dhcp_agent(self, dhcp_agent, **_params):
        """Fetches a list of dhcp agents hosting a network."""
        return self.get((self.agent_path + self.DHCP_NETS) % dhcp_agent,
                        params=_params)

    @APIParamsCall
    def add_network_to_dhcp_agent(self, dhcp_agent, body=None):
        """Adds a network to dhcp agent."""
        return self.post((self.agent_path + self.DHCP_NETS) % dhcp_agent,
                         body=body)

    @APIParamsCall
    def remove_network_from_dhcp_agent(self, dhcp_agent, network_id):
        """Remove a network from dhcp agent."""
        return self.delete((self.agent_path + self.DHCP_NETS + "/%s") % (
            dhcp_agent, network_id))

    @APIParamsCall
    def list_l3_agent_hosting_routers(self, router, **_params):
        """Fetches a list of L3 agents hosting a router."""
        return self.get((self.router_path + self.L3_AGENTS) % router,
                        params=_params)

    @APIParamsCall
    def list_routers_on_l3_agent(self, l3_agent, **_params):
        """Fetches a list of L3 agents hosting a router."""
        return self.get((self.agent_path + self.L3_ROUTERS) % l3_agent,
                        params=_params)

    @APIParamsCall
    def add_router_to_l3_agent(self, l3_agent, body):
        """Adds a router to L3 agent."""
        return self.post((self.agent_path + self.L3_ROUTERS) % l3_agent,
                         body=body)

    @APIParamsCall
    def list_firewall_rules(self, retrieve_all=True, **_params):
        """Fetches a list of all firewall rules for a tenant."""
        # Pass filters in "params" argument to do_request

        return self.list('firewall_rules', self.firewall_rules_path,
                         retrieve_all, **_params)

    @APIParamsCall
    def show_firewall_rule(self, firewall_rule, **_params):
        """Fetches information of a certain firewall rule."""
        return self.get(self.firewall_rule_path % (firewall_rule),
                        params=_params)

    @APIParamsCall
    def create_firewall_rule(self, body=None):
        """Creates a new firewall rule."""
        return self.post(self.firewall_rules_path, body=body)

    @APIParamsCall
    def update_firewall_rule(self, firewall_rule, body=None):
        """Updates a firewall rule."""
        return self.put(self.firewall_rule_path % (firewall_rule), body=body)

    @APIParamsCall
    def delete_firewall_rule(self, firewall_rule):
        """Deletes the specified firewall rule."""
        return self.delete(self.firewall_rule_path % (firewall_rule))

    @APIParamsCall
    def list_firewall_policies(self, retrieve_all=True, **_params):
        """Fetches a list of all firewall policies for a tenant."""
        # Pass filters in "params" argument to do_request

        return self.list('firewall_policies', self.firewall_policies_path,
                         retrieve_all, **_params)

    @APIParamsCall
    def show_firewall_policy(self, firewall_policy, **_params):
        """Fetches information of a certain firewall policy."""
        return self.get(self.firewall_policy_path % (firewall_policy),
                        params=_params)

    @APIParamsCall
    def create_firewall_policy(self, body=None):
        """Creates a new firewall policy."""
        return self.post(self.firewall_policies_path, body=body)

    @APIParamsCall
    def update_firewall_policy(self, firewall_policy, body=None):
        """Updates a firewall policy."""
        return self.put(self.firewall_policy_path % (firewall_policy),
                        body=body)

    @APIParamsCall
    def delete_firewall_policy(self, firewall_policy):
        """Deletes the specified firewall policy."""
        return self.delete(self.firewall_policy_path % (firewall_policy))

    @APIParamsCall
    def firewall_policy_insert_rule(self, firewall_policy, body=None):
        """Inserts specified rule into firewall policy."""
        return self.put(self.firewall_policy_insert_path % (firewall_policy),
                        body=body)

    @APIParamsCall
    def firewall_policy_remove_rule(self, firewall_policy, body=None):
        """Removes specified rule from firewall policy."""
        return self.put(self.firewall_policy_remove_path % (firewall_policy),
                        body=body)

    @APIParamsCall
    def list_firewalls(self, retrieve_all=True, **_params):
        """Fetches a list of all firewals for a tenant."""
        # Pass filters in "params" argument to do_request

        return self.list('firewalls', self.firewalls_path, retrieve_all,
                         **_params)

    @APIParamsCall
    def show_firewall(self, firewall, **_params):
        """Fetches information of a certain firewall."""
        return self.get(self.firewall_path % (firewall), params=_params)

    @APIParamsCall
    def create_firewall(self, body=None):
        """Creates a new firewall."""
        return self.post(self.firewalls_path, body=body)

    @APIParamsCall
    def update_firewall(self, firewall, body=None):
        """Updates a firewall."""
        return self.put(self.firewall_path % (firewall), body=body)

    @APIParamsCall
    def delete_firewall(self, firewall):
        """Deletes the specified firewall."""
        return self.delete(self.firewall_path % (firewall))

    @APIParamsCall
    def remove_router_from_l3_agent(self, l3_agent, router_id):
        """Remove a router from l3 agent."""
        return self.delete((self.agent_path + self.L3_ROUTERS + "/%s") % (
            l3_agent, router_id))

    @APIParamsCall
    def get_lbaas_agent_hosting_pool(self, pool, **_params):
        """Fetches a loadbalancer agent hosting a pool."""
        return self.get((self.pool_path + self.LOADBALANCER_AGENT) % pool,
                        params=_params)

    @APIParamsCall
    def list_pools_on_lbaas_agent(self, lbaas_agent, **_params):
        """Fetches a list of pools hosted by the loadbalancer agent."""
        return self.get((self.agent_path + self.LOADBALANCER_POOLS) %
                        lbaas_agent, params=_params)

    @APIParamsCall
    def list_service_providers(self, retrieve_all=True, **_params):
        """Fetches service providers."""
        # Pass filters in "params" argument to do_request
        return self.list('service_providers', self.service_providers_path,
                         retrieve_all, **_params)

    def list_credentials(self, **_params):
        """Fetch a list of all credentials for a tenant."""
        return self.get(self.credentials_path, params=_params)

    @APIParamsCall
    def show_credential(self, credential, **_params):
        """Fetch a credential."""
        return self.get(self.credential_path % (credential), params=_params)

    @APIParamsCall
    def create_credential(self, body=None):
        """Create a new credential."""
        return self.post(self.credentials_path, body=body)

    @APIParamsCall
    def update_credential(self, credential, body=None):
        """Update a credential."""
        return self.put(self.credential_path % (credential), body=body)

    @APIParamsCall
    def delete_credential(self, credential):
        """Delete the specified credential."""
        return self.delete(self.credential_path % (credential))

    def list_network_profile_bindings(self, **params):
        """Fetch a list of all tenants associated for a network profile."""
        return self.get(self.network_profile_bindings_path, params=params)

    @APIParamsCall
    def list_network_profiles(self, **params):
        """Fetch a list of all network profiles for a tenant."""
        return self.get(self.network_profiles_path, params=params)

    @APIParamsCall
    def show_network_profile(self, profile, **params):
        """Fetch a network profile."""
        return self.get(self.network_profile_path % (profile), params=params)

    @APIParamsCall
    def create_network_profile(self, body=None):
        """Create a network profile."""
        return self.post(self.network_profiles_path, body=body)

    @APIParamsCall
    def update_network_profile(self, profile, body=None):
        """Update a network profile."""
        return self.put(self.network_profile_path % (profile), body=body)

    @APIParamsCall
    def delete_network_profile(self, profile):
        """Delete the network profile."""
        return self.delete(self.network_profile_path % profile)

    @APIParamsCall
    def list_policy_profile_bindings(self, **params):
        """Fetch a list of all tenants associated for a policy profile."""
        return self.get(self.policy_profile_bindings_path, params=params)

    @APIParamsCall
    def list_policy_profiles(self, **params):
        """Fetch a list of all network profiles for a tenant."""
        return self.get(self.policy_profiles_path, params=params)

    @APIParamsCall
    def show_policy_profile(self, profile, **params):
        """Fetch a network profile."""
        return self.get(self.policy_profile_path % (profile), params=params)

    @APIParamsCall
    def update_policy_profile(self, profile, body=None):
        """Update a policy profile."""
        return self.put(self.policy_profile_path % (profile), body=body)

    @APIParamsCall
    def create_metering_label(self, body=None):
        """Creates a metering label."""
        return self.post(self.metering_labels_path, body=body)

    @APIParamsCall
    def delete_metering_label(self, label):
        """Deletes the specified metering label."""
        return self.delete(self.metering_label_path % (label))

    @APIParamsCall
    def list_metering_labels(self, retrieve_all=True, **_params):
        """Fetches a list of all metering labels for a tenant."""
        return self.list('metering_labels', self.metering_labels_path,
                         retrieve_all, **_params)

    @APIParamsCall
    def show_metering_label(self, metering_label, **_params):
        """Fetches information of a certain metering label."""
        return self.get(self.metering_label_path %
                        (metering_label), params=_params)

    @APIParamsCall
    def create_metering_label_rule(self, body=None):
        """Creates a metering label rule."""
        return self.post(self.metering_label_rules_path, body=body)

    @APIParamsCall
    def delete_metering_label_rule(self, rule):
        """Deletes the specified metering label rule."""
        return self.delete(self.metering_label_rule_path % (rule))

    @APIParamsCall
    def list_metering_label_rules(self, retrieve_all=True, **_params):
        """Fetches a list of all metering label rules for a label."""
        return self.list('metering_label_rules',
                         self.metering_label_rules_path, retrieve_all,
                         **_params)

    @APIParamsCall
    def show_metering_label_rule(self, metering_label_rule, **_params):
        """Fetches information of a certain metering label rule."""
        return self.get(self.metering_label_rule_path %
                        (metering_label_rule), params=_params)

    @APIParamsCall
    def list_net_partitions(self, **params):
        """Fetch a list of all network partitions for a tenant."""
        return self.get(self.net_partitions_path, params=params)

    @APIParamsCall
    def show_net_partition(self, netpartition, **params):
        """Fetch a network partition."""
        return self.get(self.net_partition_path % (netpartition),
                        params=params)

    @APIParamsCall
    def create_net_partition(self, body=None):
        """Create a network partition."""
        return self.post(self.net_partitions_path, body=body)

    @APIParamsCall
    def delete_net_partition(self, netpartition):
        """Delete the network partition."""
        return self.delete(self.net_partition_path % netpartition)

    @APIParamsCall
    def create_packet_filter(self, body=None):
        """Create a new packet filter."""
        return self.post(self.packet_filters_path, body=body)

    @APIParamsCall
    def update_packet_filter(self, packet_filter_id, body=None):
        """Update a packet filter."""
        return self.put(self.packet_filter_path % packet_filter_id, body=body)

    @APIParamsCall
    def list_packet_filters(self, retrieve_all=True, **_params):
        """Fetch a list of all packet filters for a tenant."""
        return self.list('packet_filters', self.packet_filters_path,
                         retrieve_all, **_params)

    @APIParamsCall
    def show_packet_filter(self, packet_filter_id, **_params):
        """Fetch information of a certain packet filter."""
        return self.get(self.packet_filter_path % packet_filter_id,
                        params=_params)

    @APIParamsCall
    def delete_packet_filter(self, packet_filter_id):
        """Delete the specified packet filter."""
        return self.delete(self.packet_filter_path % packet_filter_id)
