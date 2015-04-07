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
# @author: Swaminathan Vasudevan, Hewlett Packard.

import sys

from neutronclient.neutron.v2_0.vpn import ikepolicy
from neutronclient.tests.unit import test_cli20


class CLITestV20VpnIkePolicyJSON(test_cli20.CLITestV20Base):

    def test_create_ikepolicy_all_params(self):
        """vpn-ikepolicy-create all params."""
        resource = 'ikepolicy'
        cmd = ikepolicy.CreateIKEPolicy(test_cli20.MyApp(sys.stdout), None)
        name = 'ikepolicy1'
        description = 'my-ike-policy'
        auth_algorithm = 'sha1'
        encryption_algorithm = 'aes-256'
        ike_version = 'v1'
        phase1_negotiation_mode = 'main'
        pfs = 'group5'
        tenant_id = 'my-tenant'
        my_id = 'my-id'
        lifetime = 'units=seconds,value=20000'

        args = [name,
                '--description', description,
                '--tenant-id', tenant_id,
                '--auth-algorithm', auth_algorithm,
                '--encryption-algorithm', encryption_algorithm,
                '--ike-version', ike_version,
                '--phase1-negotiation-mode', phase1_negotiation_mode,
                '--lifetime', lifetime,
                '--pfs', pfs]

        position_names = ['name', 'description',
                          'auth_algorithm', 'encryption_algorithm',
                          'phase1_negotiation_mode',
                          'ike_version', 'pfs',
                          'tenant_id']

        position_values = [name, description,
                           auth_algorithm, encryption_algorithm,
                           phase1_negotiation_mode, ike_version, pfs,
                           tenant_id]
        extra_body = {
            'lifetime': {
                'units': 'seconds',
                'value': 20000,
            },
        }

        self._test_create_resource(resource, cmd, name, my_id, args,
                                   position_names, position_values,
                                   extra_body=extra_body)

    def test_create_ikepolicy_with_limited_params(self):
        """vpn-ikepolicy-create with limited params."""
        resource = 'ikepolicy'
        cmd = ikepolicy.CreateIKEPolicy(test_cli20.MyApp(sys.stdout), None)
        name = 'ikepolicy1'
        auth_algorithm = 'sha1'
        encryption_algorithm = 'aes-128'
        ike_version = 'v1'
        phase1_negotiation_mode = 'main'
        pfs = 'group5'
        tenant_id = 'my-tenant'
        my_id = 'my-id'

        args = [name,
                '--tenant-id', tenant_id]

        position_names = ['name',
                          'auth_algorithm', 'encryption_algorithm',
                          'phase1_negotiation_mode',
                          'ike_version', 'pfs',
                          'tenant_id']

        position_values = [name,
                           auth_algorithm, encryption_algorithm,
                           phase1_negotiation_mode,
                           ike_version, pfs,
                           tenant_id]

        self._test_create_resource(resource, cmd, name, my_id, args,
                                   position_names, position_values)

    def _test_lifetime_values(self, lifetime):
        resource = 'ikepolicy'
        cmd = ikepolicy.CreateIKEPolicy(test_cli20.MyApp(sys.stdout), None)
        name = 'ikepolicy1'
        description = 'my-ike-policy'
        auth_algorithm = 'sha1'
        encryption_algorithm = 'aes-256'
        ike_version = 'v1'
        phase1_negotiation_mode = 'main'
        pfs = 'group5'
        tenant_id = 'my-tenant'
        my_id = 'my-id'

        args = [name,
                '--description', description,
                '--tenant-id', tenant_id,
                '--auth-algorithm', auth_algorithm,
                '--encryption-algorithm', encryption_algorithm,
                '--ike-version', ike_version,
                '--phase1-negotiation-mode', phase1_negotiation_mode,
                '--lifetime', lifetime,
                '--pfs', pfs]

        position_names = ['name', 'description',
                          'auth_algorithm', 'encryption_algorithm',
                          'phase1_negotiation_mode',
                          'ike_version', 'pfs',
                          'tenant_id']

        position_values = [name, description,
                           auth_algorithm, encryption_algorithm,
                           phase1_negotiation_mode, ike_version, pfs,
                           tenant_id]
        try:
            self._test_create_resource(resource, cmd, name, my_id, args,
                                       position_names, position_values)
        except Exception:
            return
        self.fail("IKEPolicy Lifetime Error")

    def test_create_ikepolicy_with_invalid_lifetime_keys(self):
        lifetime = 'uts=seconds,val=20000'
        self._test_lifetime_values(lifetime)

    def test_create_ikepolicy_with_invalid_lifetime_value(self):
        lifetime = 'units=seconds,value=-1'
        self._test_lifetime_values(lifetime)

    def test_list_ikepolicy(self):
        """vpn-ikepolicy-list."""
        resources = "ikepolicies"
        cmd = ikepolicy.ListIKEPolicy(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd, True)

    def test_list_ikepolicy_pagination(self):
        """vpn-ikepolicy-list."""
        resources = "ikepolicies"
        cmd = ikepolicy.ListIKEPolicy(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources_with_pagination(resources, cmd)

    def test_list_ikepolicy_sort(self):
        """vpn-ikepolicy-list --sort-key name --sort-key id --sort-key asc
        --sort-key desc
        """
        resources = "ikepolicies"
        cmd = ikepolicy.ListIKEPolicy(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd,
                                  sort_key=["name", "id"],
                                  sort_dir=["asc", "desc"])

    def test_list_ikepolicy_limit(self):
        """vpn-ikepolicy-list -P."""
        resources = "ikepolicies"
        cmd = ikepolicy.ListIKEPolicy(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd, page_size=1000)

    def test_show_ikepolicy_id(self):
        """vpn-ikepolicy-show ikepolicy_id."""
        resource = 'ikepolicy'
        cmd = ikepolicy.ShowIKEPolicy(test_cli20.MyApp(sys.stdout), None)
        args = ['--fields', 'id', self.test_id]
        self._test_show_resource(resource, cmd, self.test_id, args, ['id'])

    def test_show_ikepolicy_id_name(self):
        """vpn-ikepolicy-show."""
        resource = 'ikepolicy'
        cmd = ikepolicy.ShowIKEPolicy(test_cli20.MyApp(sys.stdout), None)
        args = ['--fields', 'id', '--fields', 'name', self.test_id]
        self._test_show_resource(resource, cmd, self.test_id,
                                 args, ['id', 'name'])

    def test_update_ikepolicy(self):
        """vpn-ikepolicy-update myid --name newname --tags a b."""
        resource = 'ikepolicy'
        cmd = ikepolicy.UpdateIKEPolicy(test_cli20.MyApp(sys.stdout), None)
        self._test_update_resource(resource, cmd, 'myid',
                                   ['myid', '--name', 'newname'],
                                   {'name': 'newname', })

    def test_delete_ikepolicy(self):
        """vpn-ikepolicy-delete my-id."""
        resource = 'ikepolicy'
        cmd = ikepolicy.DeleteIKEPolicy(test_cli20.MyApp(sys.stdout), None)
        my_id = 'my-id'
        args = [my_id]
        self._test_delete_resource(resource, cmd, my_id, args)


class CLITestV20VpnIkePolicyXML(CLITestV20VpnIkePolicyJSON):
    format = 'xml'
