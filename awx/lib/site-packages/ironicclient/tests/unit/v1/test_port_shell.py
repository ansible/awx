# -*- coding: utf-8 -*-
#
# Copyright 2013 IBM Corp
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.

import mock

from ironicclient.common import utils as commonutils
from ironicclient.openstack.common import cliutils
from ironicclient.tests.unit import utils
import ironicclient.v1.port_shell as p_shell


class PortShellTest(utils.BaseTestCase):

    def test_port_show(self):
        actual = {}
        fake_print_dict = lambda data, *args, **kwargs: actual.update(data)
        with mock.patch.object(cliutils, 'print_dict', fake_print_dict):
            port = object()
            p_shell._print_port_show(port)
        exp = ['address', 'created_at', 'extra', 'node_uuid', 'updated_at',
               'uuid']
        act = actual.keys()
        self.assertEqual(sorted(exp), sorted(act))

    def test_do_port_show(self):
        client_mock = mock.MagicMock()
        args = mock.MagicMock()
        args.port = 'port_uuid'
        args.address = False

        p_shell.do_port_show(client_mock, args)
        client_mock.port.get.assert_called_once_with('port_uuid')
        # assert get_by_address() wasn't called
        self.assertFalse(client_mock.port.get_by_address.called)

    def test_do_port_show_by_address(self):
        client_mock = mock.MagicMock()
        args = mock.MagicMock()
        args.port = 'port_address'
        args.address = True

        p_shell.do_port_show(client_mock, args)
        client_mock.port.get_by_address.assert_called_once_with('port_address')
        # assert get() wasn't called
        self.assertFalse(client_mock.port.get.called)

    def test_do_port_update(self):
        client_mock = mock.MagicMock()
        args = mock.MagicMock()
        args.port = 'port_uuid'
        args.op = 'add'
        args.attributes = [['arg1=val1', 'arg2=val2']]

        p_shell.do_port_update(client_mock, args)
        patch = commonutils.args_array_to_patch(args.op, args.attributes[0])
        client_mock.port.update.assert_called_once_with('port_uuid', patch)
