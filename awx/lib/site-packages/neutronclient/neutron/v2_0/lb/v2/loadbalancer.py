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


class ListLoadBalancer(neutronV20.ListCommand):
    """LBaaS v2 List loadbalancers that belong to a given tenant."""

    resource = 'loadbalancer'
    list_columns = ['id', 'name', 'vip_address',
                    'provisioning_status', 'provider']
    pagination_support = True
    sorting_support = True


class ShowLoadBalancer(neutronV20.ShowCommand):
    """LBaaS v2 Show information of a given loadbalancer."""

    resource = 'loadbalancer'


class CreateLoadBalancer(neutronV20.CreateCommand):
    """LBaaS v2 Create a loadbalancer."""

    resource = 'loadbalancer'
    allow_names = True

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--description',
            help=_('Description of the load balancer.'))
        parser.add_argument(
            '--admin-state-down',
            dest='admin_state', action='store_false',
            help=_('Set admin state up to false.'))
        parser.add_argument(
            '--name', metavar='NAME',
            help=_('Name of the load balancer.'))
        parser.add_argument(
            '--provider',
            help=_('Provider name of load balancer service.'))
        parser.add_argument(
            '--vip-address',
            help=_('VIP address for the load balancer.'))
        parser.add_argument(
            'vip_subnet', metavar='VIP_SUBNET',
            help=_('Load balancer VIP subnet.'))

    def args2body(self, parsed_args):
        _subnet_id = neutronV20.find_resourceid_by_name_or_id(
            self.get_client(), 'subnet', parsed_args.vip_subnet)
        body = {
            self.resource: {
                'name': parsed_args.name,
                'vip_subnet_id': _subnet_id,
                'admin_state_up': parsed_args.admin_state,
            },
        }
        neutronV20.update_dict(parsed_args, body[self.resource],
                               ['description', 'provider', 'vip_address'])
        return body


class UpdateLoadBalancer(neutronV20.UpdateCommand):
    """LBaaS v2 Update a given loadbalancer."""

    resource = 'loadbalancer'
    allow_names = True


class DeleteLoadBalancer(neutronV20.DeleteCommand):
    """LBaaS v2 Delete a given loadbalancer."""

    resource = 'loadbalancer'
    allow_names = True
