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


class ListCredential(neutronV20.ListCommand):
    """List credentials that belong to a given tenant."""

    resource = 'credential'
    _formatters = {}
    list_columns = ['credential_id', 'credential_name', 'user_name',
                    'password', 'type']


class ShowCredential(neutronV20.ShowCommand):
    """Show information of a given credential."""

    resource = 'credential'
    allow_names = False


class CreateCredential(neutronV20.CreateCommand):
    """Creates a credential."""

    resource = 'credential'

    def add_known_arguments(self, parser):
        parser.add_argument(
            'credential_name',
            help=_('Name/IP address for credential.'))
        parser.add_argument(
            'credential_type',
            help=_('Type of the credential.'))
        parser.add_argument(
            '--username',
            help=_('Username for the credential.'))
        parser.add_argument(
            '--password',
            help=_('Password for the credential.'))

    def args2body(self, parsed_args):
        body = {'credential': {
            'credential_name': parsed_args.credential_name}}

        if parsed_args.credential_type:
            body['credential'].update({'type':
                                      parsed_args.credential_type})
        if parsed_args.username:
            body['credential'].update({'user_name':
                                      parsed_args.username})
        if parsed_args.password:
            body['credential'].update({'password':
                                      parsed_args.password})
        return body


class DeleteCredential(neutronV20.DeleteCommand):
    """Delete a  given credential."""

    resource = 'credential'
    allow_names = False
