# Copyright 2012 VMware, Inc
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
#

import sys

from mox3 import mox
import six

from neutronclient.neutron.v2_0.nsx import networkgateway as nwgw
from neutronclient.tests.unit import test_cli20


class CLITestV20NetworkGatewayJSON(test_cli20.CLITestV20Base):

    gw_resource = "network_gateway"
    dev_resource = "gateway_device"

    def setUp(self):
        super(CLITestV20NetworkGatewayJSON, self).setUp(
            plurals={'devices': 'device',
                     'network_gateways': 'network_gateway'})

    def test_create_gateway(self):
        cmd = nwgw.CreateNetworkGateway(test_cli20.MyApp(sys.stdout), None)
        name = 'gw-test'
        myid = 'myid'
        args = [name, ]
        position_names = ['name', ]
        position_values = [name, ]
        self._test_create_resource(self.gw_resource, cmd, name, myid, args,
                                   position_names, position_values)

    def test_create_gateway_with_tenant(self):
        cmd = nwgw.CreateNetworkGateway(test_cli20.MyApp(sys.stdout), None)
        name = 'gw-test'
        myid = 'myid'
        args = ['--tenant_id', 'tenantid', name]
        position_names = ['name', ]
        position_values = [name, ]
        self._test_create_resource(self.gw_resource, cmd, name, myid, args,
                                   position_names, position_values,
                                   tenant_id='tenantid')

    def test_create_gateway_with_device(self):
        cmd = nwgw.CreateNetworkGateway(test_cli20.MyApp(sys.stdout), None)
        name = 'gw-test'
        myid = 'myid'
        args = ['--device', 'device_id=test', name, ]
        position_names = ['name', ]
        position_values = [name, ]
        self._test_create_resource(self.gw_resource, cmd, name, myid, args,
                                   position_names, position_values,
                                   devices=[{'device_id': 'test'}])

    def test_list_gateways(self):
        resources = '%ss' % self.gw_resource
        cmd = nwgw.ListNetworkGateway(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd, True)

    def test_update_gateway(self):
        cmd = nwgw.UpdateNetworkGateway(test_cli20.MyApp(sys.stdout), None)
        self._test_update_resource(self.gw_resource, cmd, 'myid',
                                   ['myid', '--name', 'higuain'],
                                   {'name': 'higuain'})

    def test_delete_gateway(self):
        cmd = nwgw.DeleteNetworkGateway(test_cli20.MyApp(sys.stdout), None)
        myid = 'myid'
        args = [myid]
        self._test_delete_resource(self.gw_resource, cmd, myid, args)

    def test_show_gateway(self):
        cmd = nwgw.ShowNetworkGateway(test_cli20.MyApp(sys.stdout), None)
        args = ['--fields', 'id', '--fields', 'name', self.test_id]
        self._test_show_resource(self.gw_resource, cmd, self.test_id, args,
                                 ['id', 'name'])

    def test_connect_network_to_gateway(self):
        cmd = nwgw.ConnectNetworkGateway(test_cli20.MyApp(sys.stdout), None)
        args = ['gw_id', 'net_id',
                '--segmentation-type', 'edi',
                '--segmentation-id', '7']
        self._test_update_resource_action(self.gw_resource, cmd, 'gw_id',
                                          'connect_network',
                                          args,
                                          {'network_id': 'net_id',
                                           'segmentation_type': 'edi',
                                           'segmentation_id': '7'})

    def test_disconnect_network_from_gateway(self):
        cmd = nwgw.DisconnectNetworkGateway(test_cli20.MyApp(sys.stdout), None)
        args = ['gw_id', 'net_id',
                '--segmentation-type', 'edi',
                '--segmentation-id', '7']
        self._test_update_resource_action(self.gw_resource, cmd, 'gw_id',
                                          'disconnect_network',
                                          args,
                                          {'network_id': 'net_id',
                                           'segmentation_type': 'edi',
                                           'segmentation_id': '7'})

    def _test_create_gateway_device(self,
                                    name,
                                    connector_type,
                                    connector_ip,
                                    client_certificate=None,
                                    client_certificate_file=None,
                                    must_raise=False):
        cmd = nwgw.CreateGatewayDevice(test_cli20.MyApp(sys.stdout), None)
        myid = 'myid'
        extra_body = {'connector_type': connector_type,
                      'connector_ip': connector_ip,
                      'client_certificate': client_certificate}
        self.mox.StubOutWithMock(nwgw, 'read_cert_file')
        if client_certificate_file:
            nwgw.read_cert_file(mox.IgnoreArg()).AndReturn('xyz')
            extra_body['client_certificate'] = 'xyz'
        self.mox.ReplayAll()
        position_names = ['name', ]
        position_values = [name, ]
        args = []
        for (k, v) in six.iteritems(extra_body):
            if (k == 'client_certificate' and client_certificate_file):
                v = client_certificate_file
                k = 'client_certificate_file'
            # Append argument only if value for it was specified
            if v:
                args.extend(['--%s' % k.replace('_', '-'), v])
        # The following is just for verifying the call fails as expected when
        # both certificate and certificate file are specified. The extra
        # argument added is client-certificate since the loop above added
        # client-certificate-file
        if client_certificate_file and client_certificate:
            args.extend(['--client-certificate', client_certificate_file])
        args.append(name)
        if must_raise:
            with test_cli20.capture_std_streams():
                self.assertRaises(
                    SystemExit, self._test_create_resource,
                    self.dev_resource, cmd, name, myid, args,
                    position_names, position_values, extra_body=extra_body)
        else:
            self._test_create_resource(
                self.dev_resource, cmd, name, myid, args,
                position_names, position_values, extra_body=extra_body)
        self.mox.UnsetStubs()

    def test_create_gateway_device(self):
        self._test_create_gateway_device('dev_test', 'stt', '1.1.1.1', 'xyz')

    def test_create_gateway_device_with_certfile(self):
        self._test_create_gateway_device('dev_test', 'stt', '1.1.1.1',
                                         client_certificate_file='some_file')

    def test_create_gateway_device_invalid_connector_type_fails(self):
        self._test_create_gateway_device('dev_test', 'ciccio',
                                         '1.1.1.1', client_certificate='xyz',
                                         must_raise=True)

    def test_create_gateway_device_missing_connector_ip_fails(self):
        self._test_create_gateway_device('dev_test', 'stt',
                                         None, client_certificate='xyz',
                                         must_raise=True)

    def test_create_gateway_device_missing_certificates_fails(self):
        self._test_create_gateway_device('dev_test', 'stt', '1.1.1.1',
                                         must_raise=True)

    def test_create_gateway_device_with_cert_and_cert_file_fails(self):
        self._test_create_gateway_device('dev_test', 'stt', '1.1.1.1',
                                         client_certificate='xyz',
                                         client_certificate_file='some_file',
                                         must_raise=True)

    def _test_update_gateway_device(self,
                                    name=None,
                                    connector_type=None,
                                    connector_ip=None,
                                    client_certificate=None,
                                    client_certificate_file=None,
                                    must_raise=False):
        cmd = nwgw.UpdateGatewayDevice(test_cli20.MyApp(sys.stdout), None)
        myid = 'myid'
        extra_body = {}
        self.mox.StubOutWithMock(nwgw, 'read_cert_file')
        if client_certificate_file:
            nwgw.read_cert_file(mox.IgnoreArg()).AndReturn('xyz')
        self.mox.ReplayAll()
        args = [myid]

        def process_arg(argname, arg):
            if arg:
                extra_body[argname] = arg
                args.extend(['--%s' % argname.replace('_', '-'), arg])

        process_arg('name', name)
        process_arg('connector_type', connector_type)
        process_arg('connector_ip', connector_ip)
        process_arg('client_certificate', client_certificate)
        if client_certificate_file:
            extra_body['client_certificate'] = 'xyz'
            args.extend(['--client-certificate-file',
                         client_certificate_file])
        if must_raise:
            with test_cli20.capture_std_streams():
                self.assertRaises(
                    SystemExit, self._test_update_resource,
                    self.dev_resource, cmd, myid, args,
                    extrafields=extra_body)
        else:
            self._test_update_resource(
                self.dev_resource, cmd, myid, args,
                extrafields=extra_body)
        self.mox.UnsetStubs()

    def test_update_gateway_device(self):
        self._test_update_gateway_device('dev_test', 'stt', '1.1.1.1', 'xyz')

    def test_update_gateway_device_partial_body(self):
        self._test_update_gateway_device(name='dev_test',
                                         connector_type='stt')

    def test_update_gateway_device_with_certfile(self):
        self._test_update_gateway_device('dev_test', 'stt', '1.1.1.1',
                                         client_certificate_file='some_file')

    def test_update_gateway_device_invalid_connector_type_fails(self):
        self._test_update_gateway_device('dev_test', 'ciccio',
                                         '1.1.1.1', client_certificate='xyz',
                                         must_raise=True)

    def test_update_gateway_device_with_cert_and_cert_file_fails(self):
        self._test_update_gateway_device('dev_test', 'stt', '1.1.1.1',
                                         client_certificate='xyz',
                                         client_certificate_file='some_file',
                                         must_raise=True)

    def test_delete_gateway_device(self):
        cmd = nwgw.DeleteGatewayDevice(test_cli20.MyApp(sys.stdout), None)
        myid = 'myid'
        args = [myid]
        self._test_delete_resource(self.dev_resource, cmd, myid, args)

    def test_show_gateway_device(self):
        cmd = nwgw.ShowGatewayDevice(test_cli20.MyApp(sys.stdout), None)
        args = ['--fields', 'id', '--fields', 'name', self.test_id]
        self._test_show_resource(self.dev_resource, cmd, self.test_id, args,
                                 ['id', 'name'])


class CLITestV20NetworkGatewayXML(CLITestV20NetworkGatewayJSON):
    format = 'xml'
