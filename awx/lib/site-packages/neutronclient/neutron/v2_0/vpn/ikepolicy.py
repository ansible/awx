#    (c) Copyright 2013 Hewlett-Packard Development Company, L.P.
#    All Rights Reserved.
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
# @author: Swaminathan Vasudevan, Hewlett-Packard.
#

from neutronclient.common import utils
from neutronclient.i18n import _
from neutronclient.neutron import v2_0 as neutronv20
from neutronclient.neutron.v2_0.vpn import utils as vpn_utils


class ListIKEPolicy(neutronv20.ListCommand):
    """List IKE policies that belong to a tenant."""

    resource = 'ikepolicy'
    list_columns = ['id', 'name', 'auth_algorithm',
                    'encryption_algorithm', 'ike_version', 'pfs']
    _formatters = {}
    pagination_support = True
    sorting_support = True


class ShowIKEPolicy(neutronv20.ShowCommand):
    """Show information of a given IKE policy."""

    resource = 'ikepolicy'


class CreateIKEPolicy(neutronv20.CreateCommand):
    """Create an IKE policy."""

    resource = 'ikepolicy'

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--description',
            help=_('Description of the IKE policy'))
        parser.add_argument(
            '--auth-algorithm',
            default='sha1', choices=['sha1'],
            help=_('Authentication algorithm in lowercase. '
                   'Default:sha1'))
        parser.add_argument(
            '--encryption-algorithm',
            default='aes-128',
            help=_('Encryption algorithm in lowercase, default:aes-128'))
        parser.add_argument(
            '--phase1-negotiation-mode',
            default='main', choices=['main'],
            help=_('IKE Phase1 negotiation mode in lowercase, default:main'))
        parser.add_argument(
            '--ike-version',
            default='v1', choices=['v1', 'v2'],
            help=_('IKE version in lowercase, default:v1'))
        parser.add_argument(
            '--pfs',
            default='group5', choices=['group2', 'group5', 'group14'],
            help=_('Perfect Forward Secrecy in lowercase, default:group5'))
        parser.add_argument(
            '--lifetime',
            metavar="units=UNITS,value=VALUE",
            type=utils.str2dict,
            help=vpn_utils.lifetime_help("IKE"))
        parser.add_argument(
            'name', metavar='NAME',
            help=_('Name of the IKE policy.'))

    def args2body(self, parsed_args):

        body = {'ikepolicy': {
            'auth_algorithm': parsed_args.auth_algorithm,
            'encryption_algorithm': parsed_args.encryption_algorithm,
            'phase1_negotiation_mode': parsed_args.phase1_negotiation_mode,
            'ike_version': parsed_args.ike_version,
            'pfs': parsed_args.pfs,
        }, }
        if parsed_args.name:
            body['ikepolicy'].update({'name': parsed_args.name})
        if parsed_args.description:
            body['ikepolicy'].update({'description': parsed_args.description})
        if parsed_args.tenant_id:
            body['ikepolicy'].update({'tenant_id': parsed_args.tenant_id})
        if parsed_args.lifetime:
            vpn_utils.validate_lifetime_dict(parsed_args.lifetime)
            body['ikepolicy'].update({'lifetime': parsed_args.lifetime})
        return body


class UpdateIKEPolicy(neutronv20.UpdateCommand):
    """Update a given IKE policy."""

    resource = 'ikepolicy'

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--lifetime',
            metavar="units=UNITS,value=VALUE",
            type=utils.str2dict,
            help=vpn_utils.lifetime_help("IKE"))

    def args2body(self, parsed_args):

        body = {'ikepolicy': {
        }, }
        if parsed_args.lifetime:
            vpn_utils.validate_lifetime_dict(parsed_args.lifetime)
            body['ikepolicy'].update({'lifetime': parsed_args.lifetime})
        return body


class DeleteIKEPolicy(neutronv20.DeleteCommand):
    """Delete a given IKE policy."""

    resource = 'ikepolicy'
