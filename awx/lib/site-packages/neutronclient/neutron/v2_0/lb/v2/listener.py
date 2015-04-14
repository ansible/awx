# Copyright 2014 Blue Box Group, Inc.
# Copyright 2015 Hewlett-Packard Development Company, L.P.
# All Rights Reserved
#
# Author: Craig Tracey <craigtracey@gmail.com>
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

from neutronclient.i18n import _
from neutronclient.neutron import v2_0 as neutronV20


def _get_loadbalancer_id(client, lb_id_or_name):
    return neutronV20.find_resourceid_by_name_or_id(
        client,
        'loadbalancer',
        lb_id_or_name,
        cmd_resource='lbaas_loadbalancer')


class ListListener(neutronV20.ListCommand):
    """LBaaS v2 List listeners that belong to a given tenant."""

    resource = 'listener'
    list_columns = ['id', 'default_pool_id', 'name', 'protocol',
                    'protocol_port', 'admin_state_up', 'status']
    pagination_support = True
    sorting_support = True


class ShowListener(neutronV20.ShowCommand):
    """LBaaS v2 Show information of a given listener."""

    resource = 'listener'


class CreateListener(neutronV20.CreateCommand):
    """LBaaS v2 Create a listener."""

    resource = 'listener'

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--admin-state-down',
            dest='admin_state', action='store_false',
            help=_('Set admin state up to false.'))
        parser.add_argument(
            '--connection-limit',
            help=_('The maximum number of connections per second allowed for '
                   'the vip. Positive integer or -1 for unlimited (default).'))
        parser.add_argument(
            '--description',
            help=_('Description of the listener.'))
        parser.add_argument(
            '--name',
            help=_('The name of the listener.'))
        parser.add_argument(
            '--loadbalancer',
            required=True,
            metavar='LOADBALANCER',
            help=_('ID or name of the load balancer.'))
        parser.add_argument(
            '--protocol',
            required=True,
            choices=['TCP', 'HTTP', 'HTTPS'],
            help=_('Protocol for the listener.'))
        parser.add_argument(
            '--protocol-port',
            dest='protocol_port', required=True,
            metavar='PORT',
            help=_('Protocol port for the listener.'))

    def args2body(self, parsed_args):
        if parsed_args.loadbalancer:
            parsed_args.loadbalancer = _get_loadbalancer_id(
                self.get_client(),
                parsed_args.loadbalancer)
        body = {
            self.resource: {
                'loadbalancer_id': parsed_args.loadbalancer,
                'protocol': parsed_args.protocol,
                'protocol_port': parsed_args.protocol_port,
                'admin_state_up': parsed_args.admin_state,
            },
        }

        neutronV20.update_dict(parsed_args, body[self.resource],
                               ['connection-limit', 'description',
                                'loadbalancer_id', 'name'])
        return body


class UpdateListener(neutronV20.UpdateCommand):
    """LBaaS v2 Update a given listener."""

    resource = 'listener'
    allow_names = False


class DeleteListener(neutronV20.DeleteCommand):
    """LBaaS v2 Delete a given listener."""

    resource = 'listener'
