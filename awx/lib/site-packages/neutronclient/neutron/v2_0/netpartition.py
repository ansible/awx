# Copyright 2014 Alcatel-Lucent USA Inc.
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
# @author: Ronak Shah, Nuage Networks, Alcatel-Lucent USA Inc.

from neutronclient.neutron.v2_0 import CreateCommand
from neutronclient.neutron.v2_0 import DeleteCommand
from neutronclient.neutron.v2_0 import ListCommand
from neutronclient.neutron.v2_0 import ShowCommand


class ListNetPartition(ListCommand):
    """List netpartitions that belong to a given tenant."""
    resource = 'net_partition'
    list_columns = ['id', 'name']


class ShowNetPartition(ShowCommand):
    """Show information of a given netpartition."""

    resource = 'net_partition'


class CreateNetPartition(CreateCommand):
    """Create a netpartition for a given tenant."""

    resource = 'net_partition'

    def add_known_arguments(self, parser):
        parser.add_argument(
            'name', metavar='name',
            help='Name of netpartition to create.')

    def args2body(self, parsed_args):
        body = {'net_partition': {'name': parsed_args.name}, }
        return body


class DeleteNetPartition(DeleteCommand):
    """Delete a given netpartition."""

    resource = 'net_partition'
