# Copyright 2013 Mirantis Inc.
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
# @author: Ilya Shakhat, Mirantis Inc.
#

from __future__ import print_function

from neutronclient.i18n import _
from neutronclient.neutron import v2_0 as neutronV20


class ListHealthMonitor(neutronV20.ListCommand):
    """List health monitors that belong to a given tenant."""

    resource = 'health_monitor'
    list_columns = ['id', 'type', 'admin_state_up']
    pagination_support = True
    sorting_support = True


class ShowHealthMonitor(neutronV20.ShowCommand):
    """Show information of a given health monitor."""

    resource = 'health_monitor'
    allow_names = False


class CreateHealthMonitor(neutronV20.CreateCommand):
    """Create a health monitor."""

    resource = 'health_monitor'

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--admin-state-down',
            dest='admin_state', action='store_false',
            help=_('Set admin state up to false.'))
        parser.add_argument(
            '--expected-codes',
            help=_('The list of HTTP status codes expected in '
                   'response from the member to declare it healthy. This '
                   'attribute can contain one value, '
                   'or a list of values separated by comma, '
                   'or a range of values (e.g. "200-299"). If this attribute '
                   'is not specified, it defaults to "200".'))
        parser.add_argument(
            '--http-method',
            help=_('The HTTP method used for requests by the monitor of type '
                   'HTTP.'))
        parser.add_argument(
            '--url-path',
            help=_('The HTTP path used in the HTTP request used by the monitor'
                   ' to test a member health. This must be a string '
                   'beginning with a / (forward slash).'))
        parser.add_argument(
            '--delay',
            required=True,
            help=_('The time in seconds between sending probes to members.'))
        parser.add_argument(
            '--max-retries',
            required=True,
            help=_('Number of permissible connection failures before changing '
                   'the member status to INACTIVE. [1..10]'))
        parser.add_argument(
            '--timeout',
            required=True,
            help=_('Maximum number of seconds for a monitor to wait for a '
                   'connection to be established before it times out. The '
                   'value must be less than the delay value.'))
        parser.add_argument(
            '--type',
            required=True, choices=['PING', 'TCP', 'HTTP', 'HTTPS'],
            help=_('One of the predefined health monitor types.'))

    def args2body(self, parsed_args):
        body = {
            self.resource: {
                'admin_state_up': parsed_args.admin_state,
                'delay': parsed_args.delay,
                'max_retries': parsed_args.max_retries,
                'timeout': parsed_args.timeout,
                'type': parsed_args.type,
            },
        }
        neutronV20.update_dict(parsed_args, body[self.resource],
                               ['expected_codes', 'http_method', 'url_path',
                                'tenant_id'])
        return body


class UpdateHealthMonitor(neutronV20.UpdateCommand):
    """Update a given health monitor."""

    resource = 'health_monitor'
    allow_names = False


class DeleteHealthMonitor(neutronV20.DeleteCommand):
    """Delete a given health monitor."""

    resource = 'health_monitor'
    allow_names = False


class AssociateHealthMonitor(neutronV20.NeutronCommand):
    """Create a mapping between a health monitor and a pool."""

    resource = 'health_monitor'

    def get_parser(self, prog_name):
        parser = super(AssociateHealthMonitor, self).get_parser(prog_name)
        parser.add_argument(
            'health_monitor_id', metavar='HEALTH_MONITOR_ID',
            help=_('Health monitor to associate.'))
        parser.add_argument(
            'pool_id', metavar='POOL',
            help=_('ID of the pool to be associated with the health monitor.'))
        return parser

    def run(self, parsed_args):
        neutron_client = self.get_client()
        neutron_client.format = parsed_args.request_format
        body = {'health_monitor': {'id': parsed_args.health_monitor_id}}
        pool_id = neutronV20.find_resourceid_by_name_or_id(
            neutron_client, 'pool', parsed_args.pool_id)
        neutron_client.associate_health_monitor(pool_id, body)
        print((_('Associated health monitor '
                 '%s') % parsed_args.health_monitor_id),
              file=self.app.stdout)


class DisassociateHealthMonitor(neutronV20.NeutronCommand):
    """Remove a mapping from a health monitor to a pool."""

    resource = 'health_monitor'

    def get_parser(self, prog_name):
        parser = super(DisassociateHealthMonitor, self).get_parser(prog_name)
        parser.add_argument(
            'health_monitor_id', metavar='HEALTH_MONITOR_ID',
            help=_('Health monitor to associate.'))
        parser.add_argument(
            'pool_id', metavar='POOL',
            help=_('ID of the pool to be associated with the health monitor.'))
        return parser

    def run(self, parsed_args):
        neutron_client = self.get_client()
        neutron_client.format = parsed_args.request_format
        pool_id = neutronV20.find_resourceid_by_name_or_id(
            neutron_client, 'pool', parsed_args.pool_id)
        neutron_client.disassociate_health_monitor(pool_id,
                                                   parsed_args
                                                   .health_monitor_id)
        print((_('Disassociated health monitor '
                 '%s') % parsed_args.health_monitor_id),
              file=self.app.stdout)
