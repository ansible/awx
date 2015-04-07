# Copyright (C) 2013 eNovance SAS <licensing@enovance.com>
#
# Author: Sylvain Afchain <sylvain.afchain@enovance.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from neutronclient.i18n import _
from neutronclient.neutron import v2_0 as neutronv20


class ListMeteringLabel(neutronv20.ListCommand):
    """List metering labels that belong to a given tenant."""

    resource = 'metering_label'
    list_columns = ['id', 'name', 'description', 'shared']
    pagination_support = True
    sorting_support = True


class ShowMeteringLabel(neutronv20.ShowCommand):
    """Show information of a given metering label."""

    resource = 'metering_label'
    allow_names = True


class CreateMeteringLabel(neutronv20.CreateCommand):
    """Create a metering label for a given tenant."""

    resource = 'metering_label'

    def add_known_arguments(self, parser):
        parser.add_argument(
            'name', metavar='NAME',
            help=_('Name of metering label to create.'))
        parser.add_argument(
            '--description',
            help=_('Description of metering label to create.'))
        parser.add_argument(
            '--shared',
            action='store_true',
            help=_('Set the label as shared.'))

    def args2body(self, parsed_args):
        body = {'metering_label': {
            'name': parsed_args.name}, }

        if parsed_args.tenant_id:
            body['metering_label'].update({'tenant_id': parsed_args.tenant_id})
        if parsed_args.description:
            body['metering_label'].update(
                {'description': parsed_args.description})
        if parsed_args.shared:
            body['metering_label'].update(
                {'shared': True})
        return body


class DeleteMeteringLabel(neutronv20.DeleteCommand):
    """Delete a given metering label."""

    resource = 'metering_label'
    allow_names = True


class ListMeteringLabelRule(neutronv20.ListCommand):
    """List metering labels that belong to a given label."""

    resource = 'metering_label_rule'
    list_columns = ['id', 'excluded', 'direction', 'remote_ip_prefix']
    pagination_support = True
    sorting_support = True


class ShowMeteringLabelRule(neutronv20.ShowCommand):
    """Show information of a given metering label rule."""

    resource = 'metering_label_rule'


class CreateMeteringLabelRule(neutronv20.CreateCommand):
    """Create a metering label rule for a given label."""

    resource = 'metering_label_rule'

    def add_known_arguments(self, parser):
        parser.add_argument(
            'label_id', metavar='LABEL',
            help=_('Id or Name of the label.'))
        parser.add_argument(
            'remote_ip_prefix', metavar='REMOTE_IP_PREFIX',
            help=_('CIDR to match on.'))
        parser.add_argument(
            '--direction',
            default='ingress', choices=['ingress', 'egress'],
            help=_('Direction of traffic, default: ingress.'))
        parser.add_argument(
            '--excluded',
            action='store_true',
            help=_('Exclude this CIDR from the label, default: not excluded.'))

    def args2body(self, parsed_args):
        neutron_client = self.get_client()
        neutron_client.format = parsed_args.request_format
        label_id = neutronv20.find_resourceid_by_name_or_id(
            neutron_client, 'metering_label', parsed_args.label_id)

        body = {'metering_label_rule': {
            'metering_label_id': label_id,
            'remote_ip_prefix': parsed_args.remote_ip_prefix
        }}

        if parsed_args.direction:
            body['metering_label_rule'].update(
                {'direction': parsed_args.direction})
        if parsed_args.excluded:
            body['metering_label_rule'].update(
                {'excluded': True})
        return body


class DeleteMeteringLabelRule(neutronv20.DeleteCommand):
    """Delete a given metering label."""

    resource = 'metering_label_rule'
