# Copyright 2014 NEC Corporation.
# All Rights Reserved
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

from mox3 import mox

from neutronclient.common import exceptions
from neutronclient.neutron.v2_0.nec import packetfilter as pf
from neutronclient import shell
from neutronclient.tests.unit import test_cli20


class CLITestV20PacketFilterJSON(test_cli20.CLITestV20Base):
    def test_create_packetfilter_with_mandatory_params(self):
        """Create packetfilter: packetfilter1."""
        resource = 'packet_filter'
        cmd = pf.CreatePacketFilter(test_cli20.MyApp(sys.stdout), None)
        name = 'packetfilter1'
        myid = 'myid'
        args = ['--priority', '30000', '--action', 'allow', 'net1']
        position_names = ['network_id', 'action', 'priority']
        position_values = ['net1', 'allow', '30000']
        self._test_create_resource(resource, cmd, name, myid, args,
                                   position_names, position_values)

    def test_create_packetfilter_with_all_params(self):
        """Create packetfilter: packetfilter1."""
        resource = 'packet_filter'
        cmd = pf.CreatePacketFilter(test_cli20.MyApp(sys.stdout), None)
        name = 'packetfilter1'
        myid = 'myid'
        args = ['--name', name,
                '--admin-state-down',
                '--in-port', 'port1',
                '--src-mac', '00:11:22:33:44:55',
                '--dst-mac', 'aa:bb:cc:dd:ee:ff',
                '--eth-type', '0x0800',
                '--protocol', 'tcp',
                '--src-cidr', '10.1.1.0/24',
                '--dst-cidr', '10.2.2.0/24',
                '--src-port', '40001',
                '--dst-port', '4000',
                '--priority', '30000',
                '--action', 'drop', 'net1']
        params = {'network_id': 'net1',
                  'action': 'drop',
                  'priority': '30000',
                  'name': name,
                  'admin_state_up': False,
                  'in_port': 'port1',
                  'src_mac': '00:11:22:33:44:55',
                  'dst_mac': 'aa:bb:cc:dd:ee:ff',
                  'eth_type': '0x0800',
                  'protocol': 'tcp',
                  'src_cidr': '10.1.1.0/24',
                  'dst_cidr': '10.2.2.0/24',
                  'src_port': '40001',
                  'dst_port': '4000',
                  }
        position_names = sorted(params)
        position_values = [params[k] for k in sorted(params)]
        self._test_create_resource(resource, cmd, name, myid, args,
                                   position_names, position_values)

    def test_list_packetfilters_detail(self):
        """list packetfilters: -D."""
        resources = "packet_filters"
        cmd = pf.ListPacketFilter(test_cli20.MyApp(sys.stdout), None)
        response_contents = [{'id': 'myid1', 'network_id': 'net1'},
                             {'id': 'myid2', 'network_id': 'net2'}]
        self._test_list_resources(resources, cmd, True,
                                  response_contents=response_contents)

    def _stubout_extend_list(self):
        self.mox.StubOutWithMock(pf.ListPacketFilter, "extend_list")
        pf.ListPacketFilter.extend_list(mox.IsA(list), mox.IgnoreArg())

    def test_list_packetfilters_pagination(self):
        resources = "packet_filters"
        cmd = pf.ListPacketFilter(test_cli20.MyApp(sys.stdout), None)
        self._stubout_extend_list()
        self._test_list_resources_with_pagination(resources, cmd)

    def test_list_packetfilters_sort(self):
        """list packetfilters: --sort-key name --sort-key id --sort-key asc
        --sort-key desc
        """
        resources = "packet_filters"
        cmd = pf.ListPacketFilter(test_cli20.MyApp(sys.stdout), None)
        self._stubout_extend_list()
        self._test_list_resources(resources, cmd,
                                  sort_key=["name", "id"],
                                  sort_dir=["asc", "desc"])

    def test_list_packetfilters_limit(self):
        """list packetfilters: -P."""
        resources = "packet_filters"
        cmd = pf.ListPacketFilter(test_cli20.MyApp(sys.stdout), None)
        self._stubout_extend_list()
        self._test_list_resources(resources, cmd, page_size=1000)

    def test_update_packetfilter(self):
        """Update packetfilter: myid --name myname --tags a b."""
        resource = 'packet_filter'
        cmd = pf.UpdatePacketFilter(test_cli20.MyApp(sys.stdout), None)
        self._test_update_resource(resource, cmd, 'myid',
                                   ['myid', '--name', 'myname'],
                                   {'name': 'myname'}
                                   )

    def test_update_packetfilter_with_all_params(self):
        resource = 'packet_filter'
        cmd = pf.UpdatePacketFilter(test_cli20.MyApp(sys.stdout), None)
        name = 'packetfilter1'
        args = ['--name', name,
                '--admin-state', 'True',
                '--src-mac', '00:11:22:33:44:55',
                '--dst-mac', 'aa:bb:cc:dd:ee:ff',
                '--eth-type', '0x0800',
                '--protocol', 'tcp',
                '--src-cidr', '10.1.1.0/24',
                '--dst-cidr', '10.2.2.0/24',
                '--src-port', '40001',
                '--dst-port', '4000',
                '--priority', '30000',
                '--action', 'drop',
                'myid'
                ]
        params = {'action': 'drop',
                  'priority': '30000',
                  'name': name,
                  'admin_state_up': True,
                  'src_mac': '00:11:22:33:44:55',
                  'dst_mac': 'aa:bb:cc:dd:ee:ff',
                  'eth_type': '0x0800',
                  'protocol': 'tcp',
                  'src_cidr': '10.1.1.0/24',
                  'dst_cidr': '10.2.2.0/24',
                  'src_port': '40001',
                  'dst_port': '4000',
                  }
        # position_names = sorted(params)
        # position_values = [params[k] for k in sorted(params)]
        self._test_update_resource(resource, cmd, 'myid',
                                   args, params)

    def test_update_packetfilter_admin_state_false(self):
        resource = 'packet_filter'
        cmd = pf.UpdatePacketFilter(test_cli20.MyApp(sys.stdout), None)
        args = ['--admin-state', 'False', 'myid']
        params = {'admin_state_up': False}
        self._test_update_resource(resource, cmd, 'myid',
                                   args, params)

    def test_update_packetfilter_exception(self):
        """Update packetfilter: myid."""
        resource = 'packet_filter'
        cmd = pf.UpdatePacketFilter(test_cli20.MyApp(sys.stdout), None)
        exc = self.assertRaises(exceptions.CommandError,
                                self._test_update_resource,
                                resource, cmd, 'myid', ['myid'], {})
        self.assertEqual('Must specify new values to update packet_filter',
                         str(exc))

    def test_delete_packetfilter(self):
        """Delete packetfilter: myid."""
        resource = 'packet_filter'
        cmd = pf.DeletePacketFilter(test_cli20.MyApp(sys.stdout), None)
        myid = 'myid'
        args = [myid]
        self._test_delete_resource(resource, cmd, myid, args)

    def test_show_packetfilter(self):
        """Show packetfilter: myid."""
        resource = 'packet_filter'
        cmd = pf.ShowPacketFilter(test_cli20.MyApp(sys.stdout), None)
        args = ['--fields', 'id', '--fields', 'name', self.test_id]
        self._test_show_resource(resource, cmd, self.test_id, args,
                                 ['id', 'name'])


class CLITestV20PacketFilterXML(CLITestV20PacketFilterJSON):
    format = 'xml'


class CLITestV20PacketFilterValidateParam(test_cli20.CLITestV20Base):
    def _test_create_packetfilter_pass_validation(self, cmdline=None,
                                                  params=None, base_args=None):
        resource = 'packet_filter'
        cmd = pf.CreatePacketFilter(test_cli20.MyApp(sys.stdout), None)
        name = 'packetfilter1'
        myid = 'myid'
        if base_args is None:
            args = '--priority 30000 --action allow net1'.split()
        else:
            args = base_args.split()
        if cmdline:
            args += cmdline.split()
        _params = {'network_id': 'net1',
                   'action': 'allow',
                   'priority': '30000'}
        if params:
            _params.update(params)
        position_names = sorted(_params)
        position_values = [_params[k] for k in sorted(_params)]
        self._test_create_resource(resource, cmd, name, myid, args,
                                   position_names, position_values)

    def _test_create_packetfilter_negative_validation(self, cmdline):
        resource = 'packet_filter'
        cmd = pf.CreatePacketFilter(test_cli20.MyApp(sys.stdout), None)
        self.mox.StubOutWithMock(cmd, "get_client")
        self.mox.StubOutWithMock(self.client.httpclient, "request")
        cmd.get_client().MultipleTimes().AndReturn(self.client)
        cmd_parser = cmd.get_parser('create_' + resource)
        args = cmdline.split()
        self.assertRaises(exceptions.CommandError,
                          shell.run_command,
                          cmd, cmd_parser, args)

    def test_create_pf_hex_priority(self):
        self._test_create_packetfilter_pass_validation(
            base_args='--priority 0xffff --action allow net1',
            params={'priority': '0xffff'})

    def test_create_pf_hex_src_port(self):
        self._test_create_packetfilter_pass_validation(
            cmdline='--src-port 0xffff', params={'src_port': '0xffff'})

    def test_create_pf_hex_dst_port(self):
        self._test_create_packetfilter_pass_validation(
            cmdline='--dst-port 0xffff', params={'dst_port': '0xffff'})

    def test_create_pf_ip_proto_zero(self):
        self._test_create_packetfilter_pass_validation(
            cmdline='--protocol 0', params={'protocol': '0'})

    def test_create_pf_ip_proto_max_hex(self):
        self._test_create_packetfilter_pass_validation(
            cmdline='--protocol 0xff', params={'protocol': '0xff'})

    def test_create_pf_ip_proto_with_names(self):
        for proto in ['tcp', 'xxxx']:
            self._test_create_packetfilter_pass_validation(
                cmdline='--protocol ' + proto, params={'protocol': proto})

    def test_create_pf_negative_priority(self):
        self._test_create_packetfilter_negative_validation(
            '--priority -1 --action allow net1')

    def test_create_pf_too_big_priority(self):
        self._test_create_packetfilter_negative_validation(
            '--priority 65536 --action allow net1')

    def test_create_pf_negative_src_port(self):
        self._test_create_packetfilter_negative_validation(
            '--src-port -1 --priority 20000 --action allow net1')

    def test_create_pf_too_big_src_port(self):
        self._test_create_packetfilter_negative_validation(
            '--src-port 65536 --priority 20000 --action allow net1')

    def test_create_pf_negative_dst_port(self):
        self._test_create_packetfilter_negative_validation(
            '--dst-port -1 --priority 20000 --action allow net1')

    def test_create_pf_too_big_dst_port(self):
        self._test_create_packetfilter_negative_validation(
            '--dst-port 65536 --priority 20000 --action allow net1')

    def test_create_pf_negative_protocol(self):
        self._test_create_packetfilter_negative_validation(
            '--protocol -1 --priority 20000 --action allow net1')

    def test_create_pf_too_big_hex_protocol(self):
        self._test_create_packetfilter_negative_validation(
            '--protocol 0x100 --priority 20000 --action allow net1')

    def test_create_pf_invalid_src_cidr(self):
        self._test_create_packetfilter_negative_validation(
            '--src-cidr invalid --priority 20000 --action allow net1')

    def test_create_pf_invalid_dst_cidr(self):
        self._test_create_packetfilter_negative_validation(
            '--dst-cidr invalid --priority 20000 --action allow net1')
