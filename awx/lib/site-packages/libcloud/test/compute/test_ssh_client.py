# -*- coding: utf-8 -*-
# Licensed to the Apache Software Foundation (ASF) under one or more§
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from __future__ import with_statement

import os
import sys
import tempfile

from libcloud import _init_once
from libcloud.test import LibcloudTestCase
from libcloud.test import unittest
from libcloud.compute.ssh import ParamikoSSHClient
from libcloud.compute.ssh import ShellOutSSHClient
from libcloud.compute.ssh import have_paramiko

from libcloud.utils.py3 import StringIO

from mock import patch, Mock

if not have_paramiko:
    ParamikoSSHClient = None  # NOQA
else:
    import paramiko


class ParamikoSSHClientTests(LibcloudTestCase):

    @patch('paramiko.SSHClient', Mock)
    def setUp(self):
        """
        Creates the object patching the actual connection.
        """
        conn_params = {'hostname': 'dummy.host.org',
                       'port': 8822,
                       'username': 'ubuntu',
                       'key': '~/.ssh/ubuntu_ssh',
                       'timeout': '600'}
        _, self.tmp_file = tempfile.mkstemp()
        os.environ['LIBCLOUD_DEBUG'] = self.tmp_file
        _init_once()
        self.ssh_cli = ParamikoSSHClient(**conn_params)

    @patch('paramiko.SSHClient', Mock)
    def test_create_with_password(self):
        conn_params = {'hostname': 'dummy.host.org',
                       'username': 'ubuntu',
                       'password': 'ubuntu'}
        mock = ParamikoSSHClient(**conn_params)
        mock.connect()

        expected_conn = {'username': 'ubuntu',
                         'password': 'ubuntu',
                         'allow_agent': False,
                         'hostname': 'dummy.host.org',
                         'look_for_keys': False,
                         'port': 22}
        mock.client.connect.assert_called_once_with(**expected_conn)
        self.assertLogMsg('Connecting to server')

    @patch('paramiko.SSHClient', Mock)
    def test_deprecated_key_argument(self):
        conn_params = {'hostname': 'dummy.host.org',
                       'username': 'ubuntu',
                       'key': 'id_rsa'}
        mock = ParamikoSSHClient(**conn_params)
        mock.connect()

        expected_conn = {'username': 'ubuntu',
                         'allow_agent': False,
                         'hostname': 'dummy.host.org',
                         'look_for_keys': False,
                         'key_filename': 'id_rsa',
                         'port': 22}
        mock.client.connect.assert_called_once_with(**expected_conn)
        self.assertLogMsg('Connecting to server')

    def test_key_files_and_key_material_arguments_are_mutual_exclusive(self):
        conn_params = {'hostname': 'dummy.host.org',
                       'username': 'ubuntu',
                       'key_files': 'id_rsa',
                       'key_material': 'key'}

        expected_msg = ('key_files and key_material arguments are mutually '
                        'exclusive')
        self.assertRaisesRegexp(ValueError, expected_msg,
                                ParamikoSSHClient, **conn_params)

    @patch('paramiko.SSHClient', Mock)
    def test_key_material_argument(self):
        path = os.path.join(os.path.dirname(__file__),
                            'fixtures', 'misc', 'dummy_rsa')

        with open(path, 'r') as fp:
            private_key = fp.read()

        conn_params = {'hostname': 'dummy.host.org',
                       'username': 'ubuntu',
                       'key_material': private_key}
        mock = ParamikoSSHClient(**conn_params)
        mock.connect()

        pkey = paramiko.RSAKey.from_private_key(StringIO(private_key))
        expected_conn = {'username': 'ubuntu',
                         'allow_agent': False,
                         'hostname': 'dummy.host.org',
                         'look_for_keys': False,
                         'pkey': pkey,
                         'port': 22}
        mock.client.connect.assert_called_once_with(**expected_conn)
        self.assertLogMsg('Connecting to server')

    @patch('paramiko.SSHClient', Mock)
    def test_key_material_argument_invalid_key(self):
        conn_params = {'hostname': 'dummy.host.org',
                       'username': 'ubuntu',
                       'key_material': 'id_rsa'}

        mock = ParamikoSSHClient(**conn_params)

        expected_msg = 'Invalid or unsupported key type'
        self.assertRaisesRegexp(paramiko.ssh_exception.SSHException,
                                expected_msg, mock.connect)

    @patch('paramiko.SSHClient', Mock)
    def test_create_with_key(self):
        conn_params = {'hostname': 'dummy.host.org',
                       'username': 'ubuntu',
                       'key_files': 'id_rsa'}
        mock = ParamikoSSHClient(**conn_params)
        mock.connect()

        expected_conn = {'username': 'ubuntu',
                         'allow_agent': False,
                         'hostname': 'dummy.host.org',
                         'look_for_keys': False,
                         'key_filename': 'id_rsa',
                         'port': 22}
        mock.client.connect.assert_called_once_with(**expected_conn)
        self.assertLogMsg('Connecting to server')

    @patch('paramiko.SSHClient', Mock)
    def test_create_with_password_and_key(self):
        conn_params = {'hostname': 'dummy.host.org',
                       'username': 'ubuntu',
                       'password': 'ubuntu',
                       'key': 'id_rsa'}
        mock = ParamikoSSHClient(**conn_params)
        mock.connect()

        expected_conn = {'username': 'ubuntu',
                         'password': 'ubuntu',
                         'allow_agent': False,
                         'hostname': 'dummy.host.org',
                         'look_for_keys': False,
                         'key_filename': 'id_rsa',
                         'port': 22}
        mock.client.connect.assert_called_once_with(**expected_conn)
        self.assertLogMsg('Connecting to server')

    @patch('paramiko.SSHClient', Mock)
    def test_create_without_credentials(self):
        """
        Initialize object with no credentials.

        Just to have better coverage, initialize the object
        without 'password' neither 'key'.
        """
        conn_params = {'hostname': 'dummy.host.org',
                       'username': 'ubuntu'}
        mock = ParamikoSSHClient(**conn_params)
        mock.connect()

        expected_conn = {'username': 'ubuntu',
                         'hostname': 'dummy.host.org',
                         'allow_agent': True,
                         'look_for_keys': True,
                         'port': 22}
        mock.client.connect.assert_called_once_with(**expected_conn)

    def test_basic_usage_absolute_path(self):
        """
        Basic execution.
        """
        mock = self.ssh_cli
        # script to execute
        sd = "/root/random_script.sh"

        # Connect behavior
        mock.connect()
        mock_cli = mock.client  # The actual mocked object: SSHClient
        expected_conn = {'username': 'ubuntu',
                         'key_filename': '~/.ssh/ubuntu_ssh',
                         'allow_agent': False,
                         'hostname': 'dummy.host.org',
                         'look_for_keys': False,
                         'timeout': '600',
                         'port': 8822}
        mock_cli.connect.assert_called_once_with(**expected_conn)

        mock.put(sd)
        # Make assertions over 'put' method
        mock_cli.open_sftp().chdir.assert_called_with('root')
        mock_cli.open_sftp().file.assert_called_once_with('random_script.sh',
                                                          mode='w')

        mock.run(sd)

        # Make assertions over 'run' method
        mock_cli.get_transport().open_session().exec_command \
                .assert_called_once_with(sd)
        self.assertLogMsg('Executing command (cmd=/root/random_script.sh)')
        self.assertLogMsg('Command finished')

        mock.close()

    def test_delete_script(self):
        """
        Provide a basic test with 'delete' action.
        """
        mock = self.ssh_cli
        # script to execute
        sd = '/root/random_script.sh'

        mock.connect()

        mock.delete(sd)
        # Make assertions over the 'delete' method
        mock.client.open_sftp().unlink.assert_called_with(sd)
        self.assertLogMsg('Deleting file')

        mock.close()
        self.assertLogMsg('Closing server connection')

    def assertLogMsg(self, expected_msg):
        with open(self.tmp_file, 'r') as fp:
            content = fp.read()

        self.assertTrue(content.find(expected_msg) != -1)


if not ParamikoSSHClient:
    class ParamikoSSHClientTests(LibcloudTestCase):  # NOQA
        pass


class ShellOutSSHClientTests(LibcloudTestCase):

    def test_password_auth_not_supported(self):
        try:
            ShellOutSSHClient(hostname='localhost', username='foo',
                              password='bar')
        except ValueError:
            e = sys.exc_info()[1]
            msg = str(e)
            self.assertTrue('ShellOutSSHClient only supports key auth' in msg)
        else:
            self.fail('Exception was not thrown')

    def test_ssh_executable_not_available(self):
        class MockChild(object):
            returncode = 127

            def communicate(*args, **kwargs):
                pass

        def mock_popen(*args, **kwargs):
            return MockChild()

        with patch('subprocess.Popen', mock_popen):
            try:
                ShellOutSSHClient(hostname='localhost', username='foo')
            except ValueError:
                e = sys.exc_info()[1]
                msg = str(e)
                self.assertTrue('ssh client is not available' in msg)
            else:
                self.fail('Exception was not thrown')

    def test_connect_success(self):
        client = ShellOutSSHClient(hostname='localhost', username='root')
        self.assertTrue(client.connect())

    def test_close_success(self):
        client = ShellOutSSHClient(hostname='localhost', username='root')
        self.assertTrue(client.close())

    def test_get_base_ssh_command(self):
        client1 = ShellOutSSHClient(hostname='localhost', username='root')
        client2 = ShellOutSSHClient(hostname='localhost', username='root',
                                    key='/home/my.key')
        client3 = ShellOutSSHClient(hostname='localhost', username='root',
                                    key='/home/my.key', timeout=5)

        cmd1 = client1._get_base_ssh_command()
        cmd2 = client2._get_base_ssh_command()
        cmd3 = client3._get_base_ssh_command()

        self.assertEqual(cmd1, ['ssh', 'root@localhost'])
        self.assertEqual(cmd2, ['ssh', '-i', '/home/my.key',
                                'root@localhost'])
        self.assertEqual(cmd3, ['ssh', '-i', '/home/my.key',
                                '-oConnectTimeout=5', 'root@localhost'])


if __name__ == '__main__':
    sys.exit(unittest.main())
