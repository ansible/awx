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

from neutronclient.neutron.v2_0.vpn import ipsecpolicy
from neutronclient.tests.unit import test_cli20


class CLITestV20VpnIpsecPolicyJSON(test_cli20.CLITestV20Base):

    def test_create_ipsecpolicy_all_params(self):
        """vpn-ipsecpolicy-create all params with dashes."""
        resource = 'ipsecpolicy'
        cmd = ipsecpolicy.CreateIPsecPolicy(test_cli20.MyApp(sys.stdout), None)
        name = 'ipsecpolicy1'
        description = 'first-ipsecpolicy1'
        auth_algorithm = 'sha1'
        encryption_algorithm = 'aes-256'
        encapsulation_mode = 'tunnel'
        pfs = 'group5'
        transform_protocol = 'ah'
        tenant_id = 'my-tenant'
        my_id = 'my-id'
        lifetime = 'units=seconds,value=20000'

        args = [name,
                '--description', description,
                '--tenant-id', tenant_id,
                '--auth-algorithm', auth_algorithm,
                '--encryption-algorithm', encryption_algorithm,
                '--transform-protocol', transform_protocol,
                '--encapsulation-mode', encapsulation_mode,
                '--lifetime', lifetime,
                '--pfs', pfs]

        position_names = ['name', 'auth_algorithm', 'encryption_algorithm',
                          'encapsulation_mode', 'description',
                          'transform_protocol', 'pfs',
                          'tenant_id']

        position_values = [name, auth_algorithm, encryption_algorithm,
                           encapsulation_mode, description,
                           transform_protocol, pfs,
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

    def test_create_ipsecpolicy_with_limited_params(self):
        """vpn-ipsecpolicy-create with limited params."""
        resource = 'ipsecpolicy'
        cmd = ipsecpolicy.CreateIPsecPolicy(test_cli20.MyApp(sys.stdout), None)
        name = 'ipsecpolicy1'
        auth_algorithm = 'sha1'
        encryption_algorithm = 'aes-128'
        encapsulation_mode = 'tunnel'
        pfs = 'group5'
        transform_protocol = 'esp'
        tenant_id = 'my-tenant'
        my_id = 'my-id'

        args = [name,
                '--tenant-id', tenant_id]

        position_names = ['name', 'auth_algorithm', 'encryption_algorithm',
                          'encapsulation_mode',
                          'transform_protocol', 'pfs',
                          'tenant_id']

        position_values = [name, auth_algorithm, encryption_algorithm,
                           encapsulation_mode,
                           transform_protocol, pfs,
                           tenant_id]

        self._test_create_resource(resource, cmd, name, my_id, args,
                                   position_names, position_values)

    def _test_lifetime_values(self, lifetime):
        resource = 'ipsecpolicy'
        cmd = ipsecpolicy.CreateIPsecPolicy(test_cli20.MyApp(sys.stdout), None)
        name = 'ipsecpolicy1'
        description = 'my-ipsec-policy'
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
        self.fail("IPsecPolicy Lifetime Error")

    def test_create_ipsecpolicy_with_invalid_lifetime_keys(self):
        lifetime = 'uts=seconds,val=20000'
        self._test_lifetime_values(lifetime)

    def test_create_ipsecpolicy_with_invalide_lifetime_values(self):
        lifetime = 'units=minutes,value=0'
        self._test_lifetime_values(lifetime)

    def test_list_ipsecpolicy(self):
        """vpn-ipsecpolicy-list."""
        resources = "ipsecpolicies"
        cmd = ipsecpolicy.ListIPsecPolicy(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd, True)

    def test_list_ipsecpolicy_pagination(self):
        """vpn-ipsecpolicy-list."""
        resources = "ipsecpolicies"
        cmd = ipsecpolicy.ListIPsecPolicy(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources_with_pagination(resources, cmd)

    def test_list_ipsecpolicy_sort(self):
        """vpn-ipsecpolicy-list --sort-key name --sort-key id --sort-key asc
        --sort-key desc
        """
        resources = "ipsecpolicies"
        cmd = ipsecpolicy.ListIPsecPolicy(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd,
                                  sort_key=["name", "id"],
                                  sort_dir=["asc", "desc"])

    def test_list_ipsecpolicy_limit(self):
        """vpn-ipsecpolicy-list -P."""
        resources = "ipsecpolicies"
        cmd = ipsecpolicy.ListIPsecPolicy(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd, page_size=1000)

    def test_show_ipsecpolicy_id(self):
        """vpn-ipsecpolicy-show ipsecpolicy_id."""
        resource = 'ipsecpolicy'
        cmd = ipsecpolicy.ShowIPsecPolicy(test_cli20.MyApp(sys.stdout), None)
        args = ['--fields', 'id', self.test_id]
        self._test_show_resource(resource, cmd, self.test_id, args, ['id'])

    def test_show_ipsecpolicy_id_name(self):
        """vpn-ipsecpolicy-show."""
        resource = 'ipsecpolicy'
        cmd = ipsecpolicy.ShowIPsecPolicy(test_cli20.MyApp(sys.stdout), None)
        args = ['--fields', 'id', '--fields', 'name', self.test_id]
        self._test_show_resource(resource, cmd, self.test_id,
                                 args, ['id', 'name'])

    def test_update_ipsecpolicy(self):
        """vpn-ipsecpolicy-update myid --name newname --tags a b."""
        resource = 'ipsecpolicy'
        cmd = ipsecpolicy.UpdateIPsecPolicy(test_cli20.MyApp(sys.stdout), None)
        self._test_update_resource(resource, cmd, 'myid',
                                   ['myid', '--name', 'newname'],
                                   {'name': 'newname', })

    def test_delete_ipsecpolicy(self):
        """vpn-ipsecpolicy-delete my-id."""
        resource = 'ipsecpolicy'
        cmd = ipsecpolicy.DeleteIPsecPolicy(test_cli20.MyApp(sys.stdout), None)
        my_id = 'my-id'
        args = [my_id]
        self._test_delete_resource(resource, cmd, my_id, args)


class CLITestV20VpnIpsecPolicyXML(CLITestV20VpnIpsecPolicyJSON):
    format = 'xml'
