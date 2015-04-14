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
#@author Abhishek Raut, Cisco Systems
#@author Sergey Sudakovich, Cisco Systems

from __future__ import print_function

from neutronclient.i18n import _
from neutronclient.neutron import v2_0 as neutronV20
from neutronclient.neutron.v2_0 import parse_args_to_dict

RESOURCE = 'policy_profile'


class ListPolicyProfile(neutronV20.ListCommand):
    """List policy profiles that belong to a given tenant."""

    resource = RESOURCE
    _formatters = {}
    list_columns = ['id', 'name']


class ShowPolicyProfile(neutronV20.ShowCommand):
    """Show information of a given policy profile."""

    resource = RESOURCE
    allow_names = True


class UpdatePolicyProfile(neutronV20.UpdateCommand):
    """Update policy profile's information."""

    resource = RESOURCE


class UpdatePolicyProfileV2(neutronV20.UpdateCommand):
    """Update policy profile's information."""

    api = 'network'
    resource = RESOURCE

    def get_parser(self, prog_name):
        parser = super(UpdatePolicyProfileV2, self).get_parser(prog_name)
        parser.add_argument("--add-tenant",
                            help=_("Add tenant to the policy profile."))
        parser.add_argument("--remove-tenant",
                            help=_("Remove tenant from the policy profile."))
        return parser

    def run(self, parsed_args):
        self.log.debug('run(%s)' % parsed_args)
        neutron_client = self.get_client()
        neutron_client.format = parsed_args.request_format
        data = {self.resource: parse_args_to_dict(parsed_args)}
        if parsed_args.add_tenant:
            data[self.resource]['add_tenant'] = parsed_args.add_tenant
        if parsed_args.remove_tenant:
            data[self.resource]['remove_tenant'] = parsed_args.remove_tenant
        neutron_client.update_policy_profile(parsed_args.id,
                                             {self.resource: data})
        print((_('Updated %(resource)s: %(id)s') %
               {'id': parsed_args.id, 'resource': self.resource}),
              file=self.app.stdout)
        return
