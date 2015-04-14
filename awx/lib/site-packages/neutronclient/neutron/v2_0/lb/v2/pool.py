# Copyright 2013 Mirantis Inc.
# Copyright 2014 Blue Box Group, Inc.
# Copyright 2015 Hewlett-Packard Development Company, L.P.
# All Rights Reserved
#
# Author: Ilya Shakhat, Mirantis Inc.
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

from neutronclient.common import exceptions
from neutronclient.i18n import _
from neutronclient.neutron import v2_0 as neutronV20


def _parse_persistence(parsed_args):
    persistence = None
    if parsed_args.session_persistence:
        parts = parsed_args.session_persistence.split(':')
        if not len(parts) == 2:
            raise exceptions.CommandError('Incorrect --session-persistence'
                                          ' format. Format is <TYPE>:<VALUE>')
        persistence = {'type': parts[0], 'cookie_name': parts[1]}
    return persistence


class ListPool(neutronV20.ListCommand):
    """LBaaS v2 List pools that belong to a given tenant."""

    resource = 'pool'
    shadow_resource = 'lbaas_pool'
    list_columns = ['id', 'name', 'lb_method', 'protocol',
                    'admin_state_up']
    pagination_support = True
    sorting_support = True


class ShowPool(neutronV20.ShowCommand):
    """LBaaS v2 Show information of a given pool."""

    resource = 'pool'
    shadow_resource = 'lbaas_pool'

    def cleanup_output_data(self, data):
        if 'members' not in data['pool']:
            return []
        member_info = []
        for member in data['pool']['members']:
            member_info.append(member['id'])
        data['pool']['members'] = member_info


class CreatePool(neutronV20.CreateCommand):
    """LBaaS v2 Create a pool."""

    resource = 'pool'
    shadow_resource = 'lbaas_pool'

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--admin-state-down',
            dest='admin_state', action='store_false',
            help=_('Set admin state up to false.'))
        parser.add_argument(
            '--description',
            help=_('Description of the pool.'))
        parser.add_argument(
            '--healthmonitor-id',
            help=_('ID of the health monitor to use.'))
        parser.add_argument(
            '--session-persistence', metavar='TYPE:VALUE',
            help=_('The type of session persistence to use.'))
        parser.add_argument(
            '--lb-algorithm',
            required=True,
            choices=['ROUND_ROBIN', 'LEAST_CONNECTIONS', 'SOURCE_IP'],
            help=_('The algorithm used to distribute load between the members '
                   'of the pool.'))
        parser.add_argument(
            '--listener',
            required=True,
            help=_('The listener to associate with the pool'))
        parser.add_argument(
            '--protocol',
            required=True,
            choices=['HTTP', 'HTTPS', 'TCP'],
            help=_('Protocol for balancing.'))
        parser.add_argument(
            'name', metavar='NAME',
            help=_('The name of the pool.'))

    def args2body(self, parsed_args):
        if parsed_args.session_persistence:
            parsed_args.session_persistence = _parse_persistence(parsed_args)
        _listener_id = neutronV20.find_resourceid_by_name_or_id(
            self.get_client(), 'listener', parsed_args.listener)
        body = {
            self.resource: {
                'name': parsed_args.name,
                'admin_state_up': parsed_args.admin_state,
                'protocol': parsed_args.protocol,
                'lb_algorithm': parsed_args.lb_algorithm,
                'listener_id': _listener_id,
            },
        }
        neutronV20.update_dict(parsed_args, body[self.resource],
                               ['description', 'healthmonitor_id',
                                'session_persistence'])
        return body


class UpdatePool(neutronV20.UpdateCommand):
    """LBaaS v2 Update a given pool."""

    resource = 'pool'
    shadow_resource = 'lbaas_pool'


class DeletePool(neutronV20.DeleteCommand):
    """LBaaS v2 Delete a given pool."""

    resource = 'pool'
    shadow_resource = 'lbaas_pool'
