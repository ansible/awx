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

"""
Command-line interface to the Neutron APIs
"""

from __future__ import print_function

import argparse
import getpass
import logging
import os
import sys

from keystoneclient.auth.identity import v2 as v2_auth
from keystoneclient.auth.identity import v3 as v3_auth
from keystoneclient import discover
from keystoneclient.openstack.common.apiclient import exceptions as ks_exc
from keystoneclient import session
from oslo.utils import encodeutils
import six.moves.urllib.parse as urlparse

from cliff import app
from cliff import commandmanager

from neutronclient.common import clientmanager
from neutronclient.common import command as openstack_command
from neutronclient.common import exceptions as exc
from neutronclient.common import utils
from neutronclient.i18n import _
from neutronclient.neutron.v2_0 import agent
from neutronclient.neutron.v2_0 import agentscheduler
from neutronclient.neutron.v2_0 import credential
from neutronclient.neutron.v2_0 import extension
from neutronclient.neutron.v2_0 import floatingip
from neutronclient.neutron.v2_0.fw import firewall
from neutronclient.neutron.v2_0.fw import firewallpolicy
from neutronclient.neutron.v2_0.fw import firewallrule
from neutronclient.neutron.v2_0.lb import healthmonitor as lb_healthmonitor
from neutronclient.neutron.v2_0.lb import member as lb_member
from neutronclient.neutron.v2_0.lb import pool as lb_pool
from neutronclient.neutron.v2_0.lb.v2 import healthmonitor as lbaas_healthmon
from neutronclient.neutron.v2_0.lb.v2 import listener as lbaas_listener
from neutronclient.neutron.v2_0.lb.v2 import loadbalancer as lbaas_loadbalancer
from neutronclient.neutron.v2_0.lb.v2 import member as lbaas_member
from neutronclient.neutron.v2_0.lb.v2 import pool as lbaas_pool
from neutronclient.neutron.v2_0.lb import vip as lb_vip
from neutronclient.neutron.v2_0 import metering
from neutronclient.neutron.v2_0.nec import packetfilter
from neutronclient.neutron.v2_0 import netpartition
from neutronclient.neutron.v2_0 import network
from neutronclient.neutron.v2_0 import networkprofile
from neutronclient.neutron.v2_0.nsx import networkgateway
from neutronclient.neutron.v2_0.nsx import qos_queue
from neutronclient.neutron.v2_0 import policyprofile
from neutronclient.neutron.v2_0 import port
from neutronclient.neutron.v2_0 import quota
from neutronclient.neutron.v2_0 import router
from neutronclient.neutron.v2_0 import securitygroup
from neutronclient.neutron.v2_0 import servicetype
from neutronclient.neutron.v2_0 import subnet
from neutronclient.neutron.v2_0.vpn import ikepolicy
from neutronclient.neutron.v2_0.vpn import ipsec_site_connection
from neutronclient.neutron.v2_0.vpn import ipsecpolicy
from neutronclient.neutron.v2_0.vpn import vpnservice
from neutronclient.version import __version__


VERSION = '2.0'
NEUTRON_API_VERSION = '2.0'


def run_command(cmd, cmd_parser, sub_argv):
    _argv = sub_argv
    index = -1
    values_specs = []
    if '--' in sub_argv:
        index = sub_argv.index('--')
        _argv = sub_argv[:index]
        values_specs = sub_argv[index:]
    known_args, _values_specs = cmd_parser.parse_known_args(_argv)
    cmd.values_specs = (index == -1 and _values_specs or values_specs)
    return cmd.run(known_args)


def env(*_vars, **kwargs):
    """Search for the first defined of possibly many env vars.

    Returns the first environment variable defined in vars, or
    returns the default defined in kwargs.

    """
    for v in _vars:
        value = os.environ.get(v, None)
        if value:
            return value
    return kwargs.get('default', '')


def check_non_negative_int(value):
    try:
        value = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(_("invalid int value: %r") % value)
    if value < 0:
        raise argparse.ArgumentTypeError(_("input value %d is negative") %
                                         value)
    return value


class BashCompletionCommand(openstack_command.OpenStackCommand):
    """Prints all of the commands and options for bash-completion."""
    resource = "bash_completion"

COMMAND_V2 = {
    'bash-completion': BashCompletionCommand,
    'net-list': network.ListNetwork,
    'net-external-list': network.ListExternalNetwork,
    'net-show': network.ShowNetwork,
    'net-create': network.CreateNetwork,
    'net-delete': network.DeleteNetwork,
    'net-update': network.UpdateNetwork,
    'subnet-list': subnet.ListSubnet,
    'subnet-show': subnet.ShowSubnet,
    'subnet-create': subnet.CreateSubnet,
    'subnet-delete': subnet.DeleteSubnet,
    'subnet-update': subnet.UpdateSubnet,
    'port-list': port.ListPort,
    'port-show': port.ShowPort,
    'port-create': port.CreatePort,
    'port-delete': port.DeletePort,
    'port-update': port.UpdatePort,
    'quota-list': quota.ListQuota,
    'quota-show': quota.ShowQuota,
    'quota-delete': quota.DeleteQuota,
    'quota-update': quota.UpdateQuota,
    'ext-list': extension.ListExt,
    'ext-show': extension.ShowExt,
    'router-list': router.ListRouter,
    'router-port-list': port.ListRouterPort,
    'router-show': router.ShowRouter,
    'router-create': router.CreateRouter,
    'router-delete': router.DeleteRouter,
    'router-update': router.UpdateRouter,
    'router-interface-add': router.AddInterfaceRouter,
    'router-interface-delete': router.RemoveInterfaceRouter,
    'router-gateway-set': router.SetGatewayRouter,
    'router-gateway-clear': router.RemoveGatewayRouter,
    'floatingip-list': floatingip.ListFloatingIP,
    'floatingip-show': floatingip.ShowFloatingIP,
    'floatingip-create': floatingip.CreateFloatingIP,
    'floatingip-delete': floatingip.DeleteFloatingIP,
    'floatingip-associate': floatingip.AssociateFloatingIP,
    'floatingip-disassociate': floatingip.DisassociateFloatingIP,
    'security-group-list': securitygroup.ListSecurityGroup,
    'security-group-show': securitygroup.ShowSecurityGroup,
    'security-group-create': securitygroup.CreateSecurityGroup,
    'security-group-delete': securitygroup.DeleteSecurityGroup,
    'security-group-update': securitygroup.UpdateSecurityGroup,
    'security-group-rule-list': securitygroup.ListSecurityGroupRule,
    'security-group-rule-show': securitygroup.ShowSecurityGroupRule,
    'security-group-rule-create': securitygroup.CreateSecurityGroupRule,
    'security-group-rule-delete': securitygroup.DeleteSecurityGroupRule,
    'lbaas-loadbalancer-list': lbaas_loadbalancer.ListLoadBalancer,
    'lbaas-loadbalancer-show': lbaas_loadbalancer.ShowLoadBalancer,
    'lbaas-loadbalancer-create': lbaas_loadbalancer.CreateLoadBalancer,
    'lbaas-loadbalancer-update': lbaas_loadbalancer.UpdateLoadBalancer,
    'lbaas-loadbalancer-delete': lbaas_loadbalancer.DeleteLoadBalancer,
    'lbaas-listener-list': lbaas_listener.ListListener,
    'lbaas-listener-show': lbaas_listener.ShowListener,
    'lbaas-listener-create': lbaas_listener.CreateListener,
    'lbaas-listener-update': lbaas_listener.UpdateListener,
    'lbaas-listener-delete': lbaas_listener.DeleteListener,
    'lbaas-pool-list': lbaas_pool.ListPool,
    'lbaas-pool-show': lbaas_pool.ShowPool,
    'lbaas-pool-create': lbaas_pool.CreatePool,
    'lbaas-pool-update': lbaas_pool.UpdatePool,
    'lbaas-pool-delete': lbaas_pool.DeletePool,
    'lbaas-healthmonitor-list': lbaas_healthmon.ListHealthMonitor,
    'lbaas-healthmonitor-show': lbaas_healthmon.ShowHealthMonitor,
    'lbaas-healthmonitor-create': lbaas_healthmon.CreateHealthMonitor,
    'lbaas-healthmonitor-update': lbaas_healthmon.UpdateHealthMonitor,
    'lbaas-healthmonitor-delete': lbaas_healthmon.DeleteHealthMonitor,
    'lbaas-member-list': lbaas_member.ListMember,
    'lbaas-member-show': lbaas_member.ShowMember,
    'lbaas-member-create': lbaas_member.CreateMember,
    'lbaas-member-update': lbaas_member.UpdateMember,
    'lbaas-member-delete': lbaas_member.DeleteMember,
    'lb-vip-list': lb_vip.ListVip,
    'lb-vip-show': lb_vip.ShowVip,
    'lb-vip-create': lb_vip.CreateVip,
    'lb-vip-update': lb_vip.UpdateVip,
    'lb-vip-delete': lb_vip.DeleteVip,
    'lb-pool-list': lb_pool.ListPool,
    'lb-pool-show': lb_pool.ShowPool,
    'lb-pool-create': lb_pool.CreatePool,
    'lb-pool-update': lb_pool.UpdatePool,
    'lb-pool-delete': lb_pool.DeletePool,
    'lb-pool-stats': lb_pool.RetrievePoolStats,
    'lb-member-list': lb_member.ListMember,
    'lb-member-show': lb_member.ShowMember,
    'lb-member-create': lb_member.CreateMember,
    'lb-member-update': lb_member.UpdateMember,
    'lb-member-delete': lb_member.DeleteMember,
    'lb-healthmonitor-list': lb_healthmonitor.ListHealthMonitor,
    'lb-healthmonitor-show': lb_healthmonitor.ShowHealthMonitor,
    'lb-healthmonitor-create': lb_healthmonitor.CreateHealthMonitor,
    'lb-healthmonitor-update': lb_healthmonitor.UpdateHealthMonitor,
    'lb-healthmonitor-delete': lb_healthmonitor.DeleteHealthMonitor,
    'lb-healthmonitor-associate': lb_healthmonitor.AssociateHealthMonitor,
    'lb-healthmonitor-disassociate': (
        lb_healthmonitor.DisassociateHealthMonitor
    ),
    'queue-create': qos_queue.CreateQoSQueue,
    'queue-delete': qos_queue.DeleteQoSQueue,
    'queue-show': qos_queue.ShowQoSQueue,
    'queue-list': qos_queue.ListQoSQueue,
    'agent-list': agent.ListAgent,
    'agent-show': agent.ShowAgent,
    'agent-delete': agent.DeleteAgent,
    'agent-update': agent.UpdateAgent,
    'net-gateway-create': networkgateway.CreateNetworkGateway,
    'net-gateway-update': networkgateway.UpdateNetworkGateway,
    'net-gateway-delete': networkgateway.DeleteNetworkGateway,
    'net-gateway-show': networkgateway.ShowNetworkGateway,
    'net-gateway-list': networkgateway.ListNetworkGateway,
    'net-gateway-connect': networkgateway.ConnectNetworkGateway,
    'net-gateway-disconnect': networkgateway.DisconnectNetworkGateway,
    'gateway-device-create': networkgateway.CreateGatewayDevice,
    'gateway-device-update': networkgateway.UpdateGatewayDevice,
    'gateway-device-delete': networkgateway.DeleteGatewayDevice,
    'gateway-device-show': networkgateway.ShowGatewayDevice,
    'gateway-device-list': networkgateway.ListGatewayDevice,
    'dhcp-agent-network-add': agentscheduler.AddNetworkToDhcpAgent,
    'dhcp-agent-network-remove': agentscheduler.RemoveNetworkFromDhcpAgent,
    'net-list-on-dhcp-agent': agentscheduler.ListNetworksOnDhcpAgent,
    'dhcp-agent-list-hosting-net': agentscheduler.ListDhcpAgentsHostingNetwork,
    'l3-agent-router-add': agentscheduler.AddRouterToL3Agent,
    'l3-agent-router-remove': agentscheduler.RemoveRouterFromL3Agent,
    'router-list-on-l3-agent': agentscheduler.ListRoutersOnL3Agent,
    'l3-agent-list-hosting-router': agentscheduler.ListL3AgentsHostingRouter,
    'lb-pool-list-on-agent': agentscheduler.ListPoolsOnLbaasAgent,
    'lb-agent-hosting-pool': agentscheduler.GetLbaasAgentHostingPool,
    'service-provider-list': servicetype.ListServiceProvider,
    'firewall-rule-list': firewallrule.ListFirewallRule,
    'firewall-rule-show': firewallrule.ShowFirewallRule,
    'firewall-rule-create': firewallrule.CreateFirewallRule,
    'firewall-rule-update': firewallrule.UpdateFirewallRule,
    'firewall-rule-delete': firewallrule.DeleteFirewallRule,
    'firewall-policy-list': firewallpolicy.ListFirewallPolicy,
    'firewall-policy-show': firewallpolicy.ShowFirewallPolicy,
    'firewall-policy-create': firewallpolicy.CreateFirewallPolicy,
    'firewall-policy-update': firewallpolicy.UpdateFirewallPolicy,
    'firewall-policy-delete': firewallpolicy.DeleteFirewallPolicy,
    'firewall-policy-insert-rule': firewallpolicy.FirewallPolicyInsertRule,
    'firewall-policy-remove-rule': firewallpolicy.FirewallPolicyRemoveRule,
    'firewall-list': firewall.ListFirewall,
    'firewall-show': firewall.ShowFirewall,
    'firewall-create': firewall.CreateFirewall,
    'firewall-update': firewall.UpdateFirewall,
    'firewall-delete': firewall.DeleteFirewall,
    'cisco-credential-list': credential.ListCredential,
    'cisco-credential-show': credential.ShowCredential,
    'cisco-credential-create': credential.CreateCredential,
    'cisco-credential-delete': credential.DeleteCredential,
    'cisco-network-profile-list': networkprofile.ListNetworkProfile,
    'cisco-network-profile-show': networkprofile.ShowNetworkProfile,
    'cisco-network-profile-create': networkprofile.CreateNetworkProfile,
    'cisco-network-profile-delete': networkprofile.DeleteNetworkProfile,
    'cisco-network-profile-update': networkprofile.UpdateNetworkProfile,
    'cisco-policy-profile-list': policyprofile.ListPolicyProfile,
    'cisco-policy-profile-show': policyprofile.ShowPolicyProfile,
    'cisco-policy-profile-update': policyprofile.UpdatePolicyProfile,
    'ipsec-site-connection-list': (
        ipsec_site_connection.ListIPsecSiteConnection
    ),
    'ipsec-site-connection-show': (
        ipsec_site_connection.ShowIPsecSiteConnection
    ),
    'ipsec-site-connection-create': (
        ipsec_site_connection.CreateIPsecSiteConnection
    ),
    'ipsec-site-connection-update': (
        ipsec_site_connection.UpdateIPsecSiteConnection
    ),
    'ipsec-site-connection-delete': (
        ipsec_site_connection.DeleteIPsecSiteConnection
    ),
    'vpn-service-list': vpnservice.ListVPNService,
    'vpn-service-show': vpnservice.ShowVPNService,
    'vpn-service-create': vpnservice.CreateVPNService,
    'vpn-service-update': vpnservice.UpdateVPNService,
    'vpn-service-delete': vpnservice.DeleteVPNService,
    'vpn-ipsecpolicy-list': ipsecpolicy.ListIPsecPolicy,
    'vpn-ipsecpolicy-show': ipsecpolicy.ShowIPsecPolicy,
    'vpn-ipsecpolicy-create': ipsecpolicy.CreateIPsecPolicy,
    'vpn-ipsecpolicy-update': ipsecpolicy.UpdateIPsecPolicy,
    'vpn-ipsecpolicy-delete': ipsecpolicy.DeleteIPsecPolicy,
    'vpn-ikepolicy-list': ikepolicy.ListIKEPolicy,
    'vpn-ikepolicy-show': ikepolicy.ShowIKEPolicy,
    'vpn-ikepolicy-create': ikepolicy.CreateIKEPolicy,
    'vpn-ikepolicy-update': ikepolicy.UpdateIKEPolicy,
    'vpn-ikepolicy-delete': ikepolicy.DeleteIKEPolicy,
    'meter-label-create': metering.CreateMeteringLabel,
    'meter-label-list': metering.ListMeteringLabel,
    'meter-label-show': metering.ShowMeteringLabel,
    'meter-label-delete': metering.DeleteMeteringLabel,
    'meter-label-rule-create': metering.CreateMeteringLabelRule,
    'meter-label-rule-list': metering.ListMeteringLabelRule,
    'meter-label-rule-show': metering.ShowMeteringLabelRule,
    'meter-label-rule-delete': metering.DeleteMeteringLabelRule,
    'nuage-netpartition-list': netpartition.ListNetPartition,
    'nuage-netpartition-show': netpartition.ShowNetPartition,
    'nuage-netpartition-create': netpartition.CreateNetPartition,
    'nuage-netpartition-delete': netpartition.DeleteNetPartition,
    'nec-packet-filter-list': packetfilter.ListPacketFilter,
    'nec-packet-filter-show': packetfilter.ShowPacketFilter,
    'nec-packet-filter-create': packetfilter.CreatePacketFilter,
    'nec-packet-filter-update': packetfilter.UpdatePacketFilter,
    'nec-packet-filter-delete': packetfilter.DeletePacketFilter,
}

COMMANDS = {'2.0': COMMAND_V2}


class HelpAction(argparse.Action):
    """Provide a custom action so the -h and --help options
    to the main app will print a list of the commands.

    The commands are determined by checking the CommandManager
    instance, passed in as the "default" value for the action.
    """
    def __call__(self, parser, namespace, values, option_string=None):
        outputs = []
        max_len = 0
        app = self.default
        parser.print_help(app.stdout)
        app.stdout.write(_('\nCommands for API v%s:\n') % app.api_version)
        command_manager = app.command_manager
        for name, ep in sorted(command_manager):
            factory = ep.load()
            cmd = factory(self, None)
            one_liner = cmd.get_description().split('\n')[0]
            outputs.append((name, one_liner))
            max_len = max(len(name), max_len)
        for (name, one_liner) in outputs:
            app.stdout.write('  %s  %s\n' % (name.ljust(max_len), one_liner))
        sys.exit(0)


class NeutronShell(app.App):

    # verbose logging levels
    WARNING_LEVEL = 0
    INFO_LEVEL = 1
    DEBUG_LEVEL = 2
    CONSOLE_MESSAGE_FORMAT = '%(message)s'
    DEBUG_MESSAGE_FORMAT = '%(levelname)s: %(name)s %(message)s'
    log = logging.getLogger(__name__)

    def __init__(self, apiversion):
        super(NeutronShell, self).__init__(
            description=__doc__.strip(),
            version=VERSION,
            command_manager=commandmanager.CommandManager('neutron.cli'), )
        self.commands = COMMANDS
        for k, v in self.commands[apiversion].items():
            self.command_manager.add_command(k, v)

        # Pop the 'complete' to correct the outputs of 'neutron help'.
        self.command_manager.commands.pop('complete')

        # This is instantiated in initialize_app() only when using
        # password flow auth
        self.auth_client = None
        self.api_version = apiversion

    def build_option_parser(self, description, version):
        """Return an argparse option parser for this application.

        Subclasses may override this method to extend
        the parser with more global options.

        :param description: full description of the application
        :paramtype description: str
        :param version: version number for the application
        :paramtype version: str
        """
        parser = argparse.ArgumentParser(
            description=description,
            add_help=False, )
        parser.add_argument(
            '--version',
            action='version',
            version=__version__, )
        parser.add_argument(
            '-v', '--verbose', '--debug',
            action='count',
            dest='verbose_level',
            default=self.DEFAULT_VERBOSE_LEVEL,
            help=_('Increase verbosity of output and show tracebacks on'
                   ' errors. You can repeat this option.'))
        parser.add_argument(
            '-q', '--quiet',
            action='store_const',
            dest='verbose_level',
            const=0,
            help=_('Suppress output except warnings and errors.'))
        parser.add_argument(
            '-h', '--help',
            action=HelpAction,
            nargs=0,
            default=self,  # tricky
            help=_("Show this help message and exit."))
        parser.add_argument(
            '-r', '--retries',
            metavar="NUM",
            type=check_non_negative_int,
            default=0,
            help=_("How many times the request to the Neutron server should "
                   "be retried if it fails."))
        # FIXME(bklei): this method should come from python-keystoneclient
        self._append_global_identity_args(parser)

        return parser

    def _append_global_identity_args(self, parser):
        # FIXME(bklei): these are global identity (Keystone) arguments which
        # should be consistent and shared by all service clients. Therefore,
        # they should be provided by python-keystoneclient. We will need to
        # refactor this code once this functionality is available in
        # python-keystoneclient.
        #
        # Note: At that time we'll need to decide if we can just abandon
        #       the deprecated args (--service-type and --endpoint-type).

        parser.add_argument(
            '--os-service-type', metavar='<os-service-type>',
            default=env('OS_NETWORK_SERVICE_TYPE', default='network'),
            help=_('Defaults to env[OS_NETWORK_SERVICE_TYPE] or network.'))

        parser.add_argument(
            '--os-endpoint-type', metavar='<os-endpoint-type>',
            default=env('OS_ENDPOINT_TYPE', default='publicURL'),
            help=_('Defaults to env[OS_ENDPOINT_TYPE] or publicURL.'))

        # FIXME(bklei): --service-type is deprecated but kept in for
        # backward compatibility.
        parser.add_argument(
            '--service-type', metavar='<service-type>',
            default=env('OS_NETWORK_SERVICE_TYPE', default='network'),
            help=_('DEPRECATED! Use --os-service-type.'))

        # FIXME(bklei): --endpoint-type is deprecated but kept in for
        # backward compatibility.
        parser.add_argument(
            '--endpoint-type', metavar='<endpoint-type>',
            default=env('OS_ENDPOINT_TYPE', default='publicURL'),
            help=_('DEPRECATED! Use --os-endpoint-type.'))

        parser.add_argument(
            '--os-auth-strategy', metavar='<auth-strategy>',
            default=env('OS_AUTH_STRATEGY', default='keystone'),
            help=_('DEPRECATED! Only keystone is supported.'))

        parser.add_argument(
            '--os_auth_strategy',
            help=argparse.SUPPRESS)

        parser.add_argument(
            '--os-auth-url', metavar='<auth-url>',
            default=env('OS_AUTH_URL'),
            help=_('Authentication URL, defaults to env[OS_AUTH_URL].'))
        parser.add_argument(
            '--os_auth_url',
            help=argparse.SUPPRESS)

        project_name_group = parser.add_mutually_exclusive_group()
        project_name_group.add_argument(
            '--os-tenant-name', metavar='<auth-tenant-name>',
            default=env('OS_TENANT_NAME'),
            help=_('Authentication tenant name, defaults to '
                   'env[OS_TENANT_NAME].'))
        project_name_group.add_argument(
            '--os-project-name',
            metavar='<auth-project-name>',
            default=utils.env('OS_PROJECT_NAME'),
            help='Another way to specify tenant name. '
                 'This option is mutually exclusive with '
                 ' --os-tenant-name. '
                 'Defaults to env[OS_PROJECT_NAME].')

        parser.add_argument(
            '--os_tenant_name',
            help=argparse.SUPPRESS)

        project_id_group = parser.add_mutually_exclusive_group()
        project_id_group.add_argument(
            '--os-tenant-id', metavar='<auth-tenant-id>',
            default=env('OS_TENANT_ID'),
            help=_('Authentication tenant ID, defaults to '
                   'env[OS_TENANT_ID].'))
        project_id_group.add_argument(
            '--os-project-id',
            metavar='<auth-project-id>',
            default=utils.env('OS_PROJECT_ID'),
            help='Another way to specify tenant ID. '
            'This option is mutually exclusive with '
            ' --os-tenant-id. '
            'Defaults to env[OS_PROJECT_ID].')

        parser.add_argument(
            '--os-username', metavar='<auth-username>',
            default=utils.env('OS_USERNAME'),
            help=_('Authentication username, defaults to env[OS_USERNAME].'))
        parser.add_argument(
            '--os_username',
            help=argparse.SUPPRESS)

        parser.add_argument(
            '--os-user-id', metavar='<auth-user-id>',
            default=env('OS_USER_ID'),
            help=_('Authentication user ID (Env: OS_USER_ID)'))

        parser.add_argument(
            '--os_user_id',
            help=argparse.SUPPRESS)

        parser.add_argument(
            '--os-user-domain-id',
            metavar='<auth-user-domain-id>',
            default=utils.env('OS_USER_DOMAIN_ID'),
            help='OpenStack user domain ID. '
            'Defaults to env[OS_USER_DOMAIN_ID].')

        parser.add_argument(
            '--os_user_domain_id',
            help=argparse.SUPPRESS)

        parser.add_argument(
            '--os-user-domain-name',
            metavar='<auth-user-domain-name>',
            default=utils.env('OS_USER_DOMAIN_NAME'),
            help='OpenStack user domain name. '
                 'Defaults to env[OS_USER_DOMAIN_NAME].')

        parser.add_argument(
            '--os_user_domain_name',
            help=argparse.SUPPRESS)

        parser.add_argument(
            '--os_project_id',
            help=argparse.SUPPRESS)

        parser.add_argument(
            '--os_project_name',
            help=argparse.SUPPRESS)

        parser.add_argument(
            '--os-project-domain-id',
            metavar='<auth-project-domain-id>',
            default=utils.env('OS_PROJECT_DOMAIN_ID'),
            help='Defaults to env[OS_PROJECT_DOMAIN_ID].')

        parser.add_argument(
            '--os-project-domain-name',
            metavar='<auth-project-domain-name>',
            default=utils.env('OS_PROJECT_DOMAIN_NAME'),
            help='Defaults to env[OS_PROJECT_DOMAIN_NAME].')

        parser.add_argument(
            '--os-cert',
            metavar='<certificate>',
            default=utils.env('OS_CERT'),
            help=_("Path of certificate file to use in SSL "
                   "connection. This file can optionally be "
                   "prepended with the private key. Defaults "
                   "to env[OS_CERT]."))

        parser.add_argument(
            '--os-cacert',
            metavar='<ca-certificate>',
            default=env('OS_CACERT', default=None),
            help=_("Specify a CA bundle file to use in "
                   "verifying a TLS (https) server certificate. "
                   "Defaults to env[OS_CACERT]."))

        parser.add_argument(
            '--os-key',
            metavar='<key>',
            default=utils.env('OS_KEY'),
            help=_("Path of client key to use in SSL "
                   "connection. This option is not necessary "
                   "if your key is prepended to your certificate "
                   "file. Defaults to env[OS_KEY]."))

        parser.add_argument(
            '--os-password', metavar='<auth-password>',
            default=utils.env('OS_PASSWORD'),
            help=_('Authentication password, defaults to env[OS_PASSWORD].'))
        parser.add_argument(
            '--os_password',
            help=argparse.SUPPRESS)

        parser.add_argument(
            '--os-region-name', metavar='<auth-region-name>',
            default=env('OS_REGION_NAME'),
            help=_('Authentication region name, defaults to '
                   'env[OS_REGION_NAME].'))
        parser.add_argument(
            '--os_region_name',
            help=argparse.SUPPRESS)

        parser.add_argument(
            '--os-token', metavar='<token>',
            default=env('OS_TOKEN'),
            help=_('Authentication token, defaults to env[OS_TOKEN].'))
        parser.add_argument(
            '--os_token',
            help=argparse.SUPPRESS)

        parser.add_argument(
            '--http-timeout', metavar='<seconds>',
            default=env('OS_NETWORK_TIMEOUT', default=None), type=float,
            help=_('Timeout in seconds to wait for an HTTP response. Defaults '
                   'to env[OS_NETWORK_TIMEOUT] or None if not specified.'))

        parser.add_argument(
            '--os-url', metavar='<url>',
            default=env('OS_URL'),
            help=_('Defaults to env[OS_URL].'))
        parser.add_argument(
            '--os_url',
            help=argparse.SUPPRESS)

        parser.add_argument(
            '--insecure',
            action='store_true',
            default=env('NEUTRONCLIENT_INSECURE', default=False),
            help=_("Explicitly allow neutronclient to perform \"insecure\" "
                   "SSL (https) requests. The server's certificate will "
                   "not be verified against any certificate authorities. "
                   "This option should be used with caution."))

    def _bash_completion(self):
        """Prints all of the commands and options for bash-completion."""
        commands = set()
        options = set()
        for option, _action in self.parser._option_string_actions.items():
            options.add(option)
        for command_name, command in self.command_manager:
            commands.add(command_name)
            cmd_factory = command.load()
            cmd = cmd_factory(self, None)
            cmd_parser = cmd.get_parser('')
            for option, _action in cmd_parser._option_string_actions.items():
                options.add(option)
        print(' '.join(commands | options))

    def run(self, argv):
        """Equivalent to the main program for the application.

        :param argv: input arguments and options
        :paramtype argv: list of str
        """
        try:
            index = 0
            command_pos = -1
            help_pos = -1
            help_command_pos = -1
            for arg in argv:
                if arg == 'bash-completion' and help_command_pos == -1:
                    self._bash_completion()
                    return 0
                if arg in self.commands[self.api_version]:
                    if command_pos == -1:
                        command_pos = index
                elif arg in ('-h', '--help'):
                    if help_pos == -1:
                        help_pos = index
                elif arg == 'help':
                    if help_command_pos == -1:
                        help_command_pos = index
                index = index + 1
            if command_pos > -1 and help_pos > command_pos:
                argv = ['help', argv[command_pos]]
            if help_command_pos > -1 and command_pos == -1:
                argv[help_command_pos] = '--help'
            self.options, remainder = self.parser.parse_known_args(argv)
            self.configure_logging()
            self.interactive_mode = not remainder
            self.initialize_app(remainder)
        except Exception as err:
            if self.options.verbose_level >= self.DEBUG_LEVEL:
                self.log.exception(err)
                raise
            else:
                self.log.error(err)
            return 1
        if self.interactive_mode:
            _argv = [sys.argv[0]]
            sys.argv = _argv
            return self.interact()
        return self.run_subcommand(remainder)

    def run_subcommand(self, argv):
        subcommand = self.command_manager.find_command(argv)
        cmd_factory, cmd_name, sub_argv = subcommand
        cmd = cmd_factory(self, self.options)
        try:
            self.prepare_to_run_command(cmd)
            full_name = (cmd_name
                         if self.interactive_mode
                         else ' '.join([self.NAME, cmd_name])
                         )
            cmd_parser = cmd.get_parser(full_name)
            return run_command(cmd, cmd_parser, sub_argv)
        except Exception as e:
            if self.options.verbose_level >= self.DEBUG_LEVEL:
                self.log.exception("%s", e)
                raise
            self.log.error("%s", e)
        return 1

    def authenticate_user(self):
        """Make sure the user has provided all of the authentication
        info we need.
        """
        if self.options.os_auth_strategy == 'keystone':
            if self.options.os_token or self.options.os_url:
                # Token flow auth takes priority
                if not self.options.os_token:
                    raise exc.CommandError(
                        _("You must provide a token via"
                          " either --os-token or env[OS_TOKEN]"))

                if not self.options.os_url:
                    raise exc.CommandError(
                        _("You must provide a service URL via"
                          " either --os-url or env[OS_URL]"))

            else:
                # Validate password flow auth
                project_info = (self.options.os_tenant_name or
                                self.options.os_tenant_id or
                                (self.options.os_project_name and
                                    (self.options.os_project_domain_name or
                                     self.options.os_project_domain_id)) or
                                self.options.os_project_id)

                if (not self.options.os_username
                        and not self.options.os_user_id):
                    raise exc.CommandError(
                        _("You must provide a username or user ID via"
                          "  --os-username, env[OS_USERNAME] or"
                          "  --os-user-id, env[OS_USER_ID]"))

                if not self.options.os_password:
                    # No password, If we've got a tty, try prompting for it
                    if hasattr(sys.stdin, 'isatty') and sys.stdin.isatty():
                        # Check for Ctl-D
                        try:
                            self.options.os_password = getpass.getpass(
                                'OS Password: ')
                        except EOFError:
                            pass
                    # No password because we didn't have a tty or the
                    # user Ctl-D when prompted.
                    if not self.options.os_password:
                        raise exc.CommandError(
                            _("You must provide a password via"
                              " either --os-password or env[OS_PASSWORD]"))

                if (not project_info):
                    # tenent is deprecated in Keystone v3. Use the latest
                    # terminology instead.
                    raise exc.CommandError(
                        _("You must provide a project_id or project_name ("
                          "with project_domain_name or project_domain_id) "
                          "via "
                          "  --os-project-id (env[OS_PROJECT_ID])"
                          "  --os-project-name (env[OS_PROJECT_NAME]),"
                          "  --os-project-domain-id "
                          "(env[OS_PROJECT_DOMAIN_ID])"
                          "  --os-project-domain-name "
                          "(env[OS_PROJECT_DOMAIN_NAME])"))

                if not self.options.os_auth_url:
                    raise exc.CommandError(
                        _("You must provide an auth url via"
                          " either --os-auth-url or via env[OS_AUTH_URL]"))
            auth_session = self._get_keystone_session()
            auth = auth_session.auth
        else:   # not keystone
            if not self.options.os_url:
                raise exc.CommandError(
                    _("You must provide a service URL via"
                      " either --os-url or env[OS_URL]"))
            auth_session = None
            auth = None

        self.client_manager = clientmanager.ClientManager(
            token=self.options.os_token,
            url=self.options.os_url,
            auth_url=self.options.os_auth_url,
            tenant_name=self.options.os_tenant_name,
            tenant_id=self.options.os_tenant_id,
            username=self.options.os_username,
            user_id=self.options.os_user_id,
            password=self.options.os_password,
            region_name=self.options.os_region_name,
            api_version=self.api_version,
            auth_strategy=self.options.os_auth_strategy,
            # FIXME (bklei) honor deprecated service_type and
            # endpoint type until they are removed
            service_type=self.options.os_service_type or
            self.options.service_type,
            endpoint_type=self.options.os_endpoint_type or self.endpoint_type,
            insecure=self.options.insecure,
            ca_cert=self.options.os_cacert,
            timeout=self.options.http_timeout,
            retries=self.options.retries,
            raise_errors=False,
            session=auth_session,
            auth=auth,
            log_credentials=True)
        return

    def initialize_app(self, argv):
        """Global app init bits:

        * set up API versions
        * validate authentication info
        """

        super(NeutronShell, self).initialize_app(argv)

        self.api_version = {'network': self.api_version}

        # If the user is not asking for help, make sure they
        # have given us auth.
        cmd_name = None
        if argv:
            cmd_info = self.command_manager.find_command(argv)
            cmd_factory, cmd_name, sub_argv = cmd_info
        if self.interactive_mode or cmd_name != 'help':
            self.authenticate_user()

    def configure_logging(self):
        """Create logging handlers for any log output."""
        root_logger = logging.getLogger('')

        # Set up logging to a file
        root_logger.setLevel(logging.DEBUG)

        # Send higher-level messages to the console via stderr
        console = logging.StreamHandler(self.stderr)
        console_level = {self.WARNING_LEVEL: logging.WARNING,
                         self.INFO_LEVEL: logging.INFO,
                         self.DEBUG_LEVEL: logging.DEBUG,
                         }.get(self.options.verbose_level, logging.DEBUG)
        # The default log level is INFO, in this situation, set the
        # log level of the console to WARNING, to avoid displaying
        # useless messages. This equals using "--quiet"
        if console_level == logging.INFO:
            console.setLevel(logging.WARNING)
        else:
            console.setLevel(console_level)
        if logging.DEBUG == console_level:
            formatter = logging.Formatter(self.DEBUG_MESSAGE_FORMAT)
        else:
            formatter = logging.Formatter(self.CONSOLE_MESSAGE_FORMAT)
        logging.getLogger('iso8601.iso8601').setLevel(logging.WARNING)
        logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)
        console.setFormatter(formatter)
        root_logger.addHandler(console)
        return

    def get_v2_auth(self, v2_auth_url):
        return v2_auth.Password(
            v2_auth_url,
            username=self.options.os_username,
            password=self.options.os_password,
            tenant_id=self.options.os_tenant_id,
            tenant_name=self.options.os_tenant_name)

    def get_v3_auth(self, v3_auth_url):
        project_id = self.options.os_project_id or self.options.os_tenant_id
        project_name = (self.options.os_project_name or
                        self.options.os_tenant_name)

        return v3_auth.Password(
            v3_auth_url,
            username=self.options.os_username,
            password=self.options.os_password,
            user_id=self.options.os_user_id,
            user_domain_name=self.options.os_user_domain_name,
            user_domain_id=self.options.os_user_domain_id,
            project_id=project_id,
            project_name=project_name,
            project_domain_name=self.options.os_project_domain_name,
            project_domain_id=self.options.os_project_domain_id
        )

    def _discover_auth_versions(self, session, auth_url):
        # discover the API versions the server is supporting base on the
        # given URL
        try:
            ks_discover = discover.Discover(session=session, auth_url=auth_url)
            return (ks_discover.url_for('2.0'), ks_discover.url_for('3.0'))
        except ks_exc.ClientException:
            # Identity service may not support discover API version.
            # Lets try to figure out the API version from the original URL.
            url_parts = urlparse.urlparse(auth_url)
            (scheme, netloc, path, params, query, fragment) = url_parts
            path = path.lower()
            if path.startswith('/v3'):
                return (None, auth_url)
            elif path.startswith('/v2'):
                return (auth_url, None)
            else:
                # not enough information to determine the auth version
                msg = _('Unable to determine the Keystone version '
                        'to authenticate with using the given '
                        'auth_url. Identity service may not support API '
                        'version discovery. Please provide a versioned '
                        'auth_url instead.')
                raise exc.CommandError(msg)

    def _get_keystone_session(self):
        # first create a Keystone session
        cacert = self.options.os_cacert or None
        cert = self.options.os_cert or None
        key = self.options.os_key or None
        insecure = self.options.insecure or False
        ks_session = session.Session.construct(dict(cacert=cacert,
                                                    cert=cert,
                                                    key=key,
                                                    insecure=insecure))
        # discover the supported keystone versions using the given url
        (v2_auth_url, v3_auth_url) = self._discover_auth_versions(
            session=ks_session,
            auth_url=self.options.os_auth_url)

        # Determine which authentication plugin to use. First inspect the
        # auth_url to see the supported version. If both v3 and v2 are
        # supported, then use the highest version if possible.
        user_domain_name = self.options.os_user_domain_name or None
        user_domain_id = self.options.os_user_domain_id or None
        project_domain_name = self.options.os_project_domain_name or None
        project_domain_id = self.options.os_project_domain_id or None
        domain_info = (user_domain_name or user_domain_id or
                       project_domain_name or project_domain_id)

        if (v2_auth_url and not domain_info) or not v3_auth_url:
            ks_session.auth = self.get_v2_auth(v2_auth_url)
        else:
            ks_session.auth = self.get_v3_auth(v3_auth_url)

        return ks_session


def main(argv=sys.argv[1:]):
    try:
        return NeutronShell(NEUTRON_API_VERSION).run(
            list(map(encodeutils.safe_decode, argv)))
    except KeyboardInterrupt:
        print("... terminating neutron client", file=sys.stderr)
        return 130
    except exc.NeutronClientException:
        return 1
    except Exception as e:
        print(e)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
