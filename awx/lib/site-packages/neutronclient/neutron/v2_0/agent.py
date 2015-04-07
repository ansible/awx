# Copyright 2013 OpenStack Foundation.
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

from neutronclient.i18n import _
from neutronclient.neutron import v2_0 as neutronV20


def _format_timestamp(component):
    try:
        return component['heartbeat_timestamp'].split(".", 2)[0]
    except (TypeError, KeyError):
        return ''


class ListAgent(neutronV20.ListCommand):
    """List agents."""

    resource = 'agent'
    list_columns = ['id', 'agent_type', 'host', 'alive', 'admin_state_up',
                    'binary']
    _formatters = {'heartbeat_timestamp': _format_timestamp}
    sorting_support = True

    def extend_list(self, data, parsed_args):
        for agent in data:
            if 'alive' in agent:
                agent['alive'] = ":-)" if agent['alive'] else 'xxx'


class ShowAgent(neutronV20.ShowCommand):
    """Show information of a given agent."""

    resource = 'agent'
    allow_names = False
    json_indent = 5


class DeleteAgent(neutronV20.DeleteCommand):
    """Delete a given agent."""

    resource = 'agent'
    allow_names = False


class UpdateAgent(neutronV20.UpdateCommand):
    """Updates the admin status and description for a specified agent."""

    resource = 'agent'
    allow_names = False

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--admin-state-down',
            dest='admin_state',
            action='store_false',
            help=_('Set admin state up of the agent to false.'))
        parser.add_argument(
            '--description',
            help=_('Description for the agent.'))

    def args2body(self, parsed_args):
        body = {
            self.resource: {
                'admin_state_up': parsed_args.admin_state, }, }
        neutronV20.update_dict(parsed_args, body[self.resource],
                               ['description'])
        return body
