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

from neutronclient.common import utils
from neutronclient.i18n import _
from neutronclient.neutron import v2_0 as neutronv20
from neutronclient.neutron.v2_0.vpn import utils as vpn_utils


class ListIPsecPolicy(neutronv20.ListCommand):
    """List IPsec policies that belong to a given tenant connection."""

    resource = 'ipsecpolicy'
    list_columns = ['id', 'name', 'auth_algorithm',
                    'encryption_algorithm', 'pfs']
    _formatters = {}
    pagination_support = True
    sorting_support = True


class ShowIPsecPolicy(neutronv20.ShowCommand):
    """Show information of a given IPsec policy."""

    resource = 'ipsecpolicy'


class CreateIPsecPolicy(neutronv20.CreateCommand):
    """Create an IPsec policy."""

    resource = 'ipsecpolicy'

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--description',
            help=_('Description of the IPsec policy.'))
        parser.add_argument(
            '--transform-protocol',
            default='esp', choices=['esp', 'ah', 'ah-esp'],
            help=_('Transform protocol in lowercase, default:esp'))
        parser.add_argument(
            '--auth-algorithm',
            default='sha1', choices=['sha1'],
            help=_('Authentication algorithm in lowercase, default:sha1'))
        parser.add_argument(
            '--encryption-algorithm',
            default='aes-128',
            help=_('Encryption algorithm in lowercase, default:aes-128'))
        parser.add_argument(
            '--encapsulation-mode',
            default='tunnel', choices=['tunnel', 'transport'],
            help=_('Encapsulation mode in lowercase, default:tunnel'))
        parser.add_argument(
            '--pfs',
            default='group5', choices=['group2', 'group5', 'group14'],
            help=_('Perfect Forward Secrecy in lowercase, default:group5'))
        parser.add_argument(
            '--lifetime',
            metavar="units=UNITS,value=VALUE",
            type=utils.str2dict,
            help=vpn_utils.lifetime_help("IPsec"))
        parser.add_argument(
            'name', metavar='NAME',
            help=_('Name of the IPsec policy.'))

    def args2body(self, parsed_args):

        body = {'ipsecpolicy': {
            'auth_algorithm': parsed_args.auth_algorithm,
            'encryption_algorithm': parsed_args.encryption_algorithm,
            'encapsulation_mode': parsed_args.encapsulation_mode,
            'transform_protocol': parsed_args.transform_protocol,
            'pfs': parsed_args.pfs,
        }, }
        if parsed_args.name:
            body['ipsecpolicy'].update({'name': parsed_args.name})
        if parsed_args.description:
            body['ipsecpolicy'].update(
                {'description': parsed_args.description}
            )
        if parsed_args.tenant_id:
            body['ipsecpolicy'].update({'tenant_id': parsed_args.tenant_id})
        if parsed_args.lifetime:
            vpn_utils.validate_lifetime_dict(parsed_args.lifetime)
            body['ipsecpolicy'].update({'lifetime': parsed_args.lifetime})
        return body


class UpdateIPsecPolicy(neutronv20.UpdateCommand):
    """Update a given IPsec policy."""

    resource = 'ipsecpolicy'

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--lifetime',
            metavar="units=UNITS,value=VALUE",
            type=utils.str2dict,
            help=vpn_utils.lifetime_help("IPsec"))

    def args2body(self, parsed_args):

        body = {'ipsecpolicy': {
        }, }
        if parsed_args.lifetime:
            vpn_utils.validate_lifetime_dict(parsed_args.lifetime)
            body['ipsecpolicy'].update({'lifetime': parsed_args.lifetime})
        return body


class DeleteIPsecPolicy(neutronv20.DeleteCommand):
    """Delete a given IPsec policy."""

    resource = 'ipsecpolicy'
