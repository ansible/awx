#!/usr/bin/env python
# Copyright 2012 Red Hat
# All Rights Reserved.
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

import sys

from neutronclient.neutron.v2_0 import floatingip as fip
from neutronclient.tests.unit import test_cli20


class CLITestV20FloatingIpsJSON(test_cli20.CLITestV20Base):
    def test_create_floatingip(self):
        """Create floatingip: fip1."""
        resource = 'floatingip'
        cmd = fip.CreateFloatingIP(test_cli20.MyApp(sys.stdout), None)
        name = 'fip1'
        myid = 'myid'
        args = [name]
        position_names = ['floating_network_id']
        position_values = [name]
        self._test_create_resource(resource, cmd, name, myid, args,
                                   position_names, position_values)

    def test_create_floatingip_and_port(self):
        """Create floatingip: fip1."""
        resource = 'floatingip'
        cmd = fip.CreateFloatingIP(test_cli20.MyApp(sys.stdout), None)
        name = 'fip1'
        myid = 'myid'
        pid = 'mypid'
        args = [name, '--port_id', pid]
        position_names = ['floating_network_id', 'port_id']
        position_values = [name, pid]
        self._test_create_resource(resource, cmd, name, myid, args,
                                   position_names, position_values)

        # Test dashed options
        args = [name, '--port-id', pid]
        position_names = ['floating_network_id', 'port_id']
        self._test_create_resource(resource, cmd, name, myid, args,
                                   position_names, position_values)

    def test_create_floatingip_and_port_and_address(self):
        """Create floatingip: fip1 with a given port and address."""
        resource = 'floatingip'
        cmd = fip.CreateFloatingIP(test_cli20.MyApp(sys.stdout), None)
        name = 'fip1'
        myid = 'myid'
        pid = 'mypid'
        addr = '10.0.0.99'
        args = [name, '--port_id', pid, '--fixed_ip_address', addr]
        position_names = ['floating_network_id', 'port_id', 'fixed_ip_address']
        position_values = [name, pid, addr]
        self._test_create_resource(resource, cmd, name, myid, args,
                                   position_names, position_values)
        # Test dashed options
        args = [name, '--port-id', pid, '--fixed-ip-address', addr]
        position_names = ['floating_network_id', 'port_id', 'fixed_ip_address']
        self._test_create_resource(resource, cmd, name, myid, args,
                                   position_names, position_values)

    def test_create_floatingip_with_ip_address_of_floating_ip(self):
        """Create floatingip: fip1 with a given IP address of floating IP."""
        resource = 'floatingip'
        cmd = fip.CreateFloatingIP(test_cli20.MyApp(sys.stdout), None)
        name = 'fip1'
        myid = 'myid'
        addr = '10.0.0.99'

        args = [name, '--floating-ip-address', addr]
        position_values = [name, addr]
        position_names = ['floating_network_id', 'floating_ip_address']
        self._test_create_resource(resource, cmd, name, myid, args,
                                   position_names, position_values)

    def test_list_floatingips(self):
        """list floatingips: -D."""
        resources = 'floatingips'
        cmd = fip.ListFloatingIP(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd, True)

    def test_list_floatingips_pagination(self):
        resources = 'floatingips'
        cmd = fip.ListFloatingIP(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources_with_pagination(resources, cmd)

    def test_list_floatingips_sort(self):
        """list floatingips: --sort-key name --sort-key id --sort-key asc
        --sort-key desc
        """
        resources = 'floatingips'
        cmd = fip.ListFloatingIP(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd,
                                  sort_key=["name", "id"],
                                  sort_dir=["asc", "desc"])

    def test_list_floatingips_limit(self):
        """list floatingips: -P."""
        resources = 'floatingips'
        cmd = fip.ListFloatingIP(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd, page_size=1000)

    def test_delete_floatingip(self):
        """Delete floatingip: fip1."""
        resource = 'floatingip'
        cmd = fip.DeleteFloatingIP(test_cli20.MyApp(sys.stdout), None)
        myid = 'myid'
        args = [myid]
        self._test_delete_resource(resource, cmd, myid, args)

    def test_show_floatingip(self):
        """Show floatingip: --fields id."""
        resource = 'floatingip'
        cmd = fip.ShowFloatingIP(test_cli20.MyApp(sys.stdout), None)
        args = ['--fields', 'id', self.test_id]
        self._test_show_resource(resource, cmd, self.test_id,
                                 args, ['id'])

    def test_disassociate_ip(self):
        """Disassociate floating IP: myid."""
        resource = 'floatingip'
        cmd = fip.DisassociateFloatingIP(test_cli20.MyApp(sys.stdout), None)
        args = ['myid']
        self._test_update_resource(resource, cmd, 'myid',
                                   args, {"port_id": None}
                                   )

    def test_associate_ip(self):
        """Associate floating IP: myid portid."""
        resource = 'floatingip'
        cmd = fip.AssociateFloatingIP(test_cli20.MyApp(sys.stdout), None)
        args = ['myid', 'portid']
        self._test_update_resource(resource, cmd, 'myid',
                                   args, {"port_id": "portid"}
                                   )


class CLITestV20FloatingIpsXML(CLITestV20FloatingIpsJSON):
    format = 'xml'
