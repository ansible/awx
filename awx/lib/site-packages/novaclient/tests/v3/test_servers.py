# -*- coding: utf-8 -*-
# Copyright 2013 IBM Corp.
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

import mock
import six

from novaclient import exceptions
from novaclient.tests.fixture_data import client
from novaclient.tests.fixture_data import servers as data
from novaclient.tests import utils
from novaclient.v3 import servers


class ServersTest(utils.FixturedTestCase):

    client_fixture_class = client.V3
    data_fixture_class = data.V3

    def test_list_servers(self):
        sl = self.cs.servers.list()
        self.assert_called('GET', '/servers/detail')
        for s in sl:
            self.assertIsInstance(s, servers.Server)

    def test_list_servers_undetailed(self):
        sl = self.cs.servers.list(detailed=False)
        self.assert_called('GET', '/servers')
        for s in sl:
            self.assertIsInstance(s, servers.Server)

    def test_list_servers_with_marker_limit(self):
        sl = self.cs.servers.list(marker=1234, limit=2)
        self.assert_called('GET', '/servers/detail?limit=2&marker=1234')
        for s in sl:
            self.assertIsInstance(s, servers.Server)

    def test_get_server_details(self):
        s = self.cs.servers.get(1234)
        self.assert_called('GET', '/servers/1234')
        self.assertIsInstance(s, servers.Server)
        self.assertEqual(1234, s.id)
        self.assertEqual('BUILD', s.status)

    def test_get_server_promote_details(self):
        s1 = self.cs.servers.list(detailed=False)[0]
        s2 = self.cs.servers.list(detailed=True)[0]
        self.assertNotEqual(s1._info, s2._info)
        s1.get()
        self.assertEqual(s1._info, s2._info)

    def test_create_server(self):
        s = self.cs.servers.create(
            name="My server",
            image=1,
            flavor=1,
            meta={'foo': 'bar'},
            userdata="hello moto",
            key_name="fakekey",
            files={
                '/etc/passwd': 'some data',                 # a file
                '/tmp/foo.txt': six.StringIO('data'),   # a stream
            }
        )
        self.assert_called('POST', '/servers')
        self.assertIsInstance(s, servers.Server)

    def test_create_server_boot_with_nics_ipv4(self):
        old_boot = self.cs.servers._boot
        nics = [{'net-id': '11111111-1111-1111-1111-111111111111',
                'v4-fixed-ip': '10.10.0.7'}]

        def wrapped_boot(url, key, *boot_args, **boot_kwargs):
            self.assertEqual(boot_kwargs['nics'], nics)
            return old_boot(url, key, *boot_args, **boot_kwargs)

        with mock.patch.object(self.cs.servers, '_boot', wrapped_boot):
            s = self.cs.servers.create(
                name="My server",
                image=1,
                flavor=1,
                meta={'foo': 'bar'},
                userdata="hello moto",
                key_name="fakekey",
                nics=nics
            )
            self.assert_called('POST', '/servers')
            self.assertIsInstance(s, servers.Server)

    def test_create_server_boot_with_nics_ipv6(self):
        old_boot = self.cs.servers._boot
        nics = [{'net-id': '11111111-1111-1111-1111-111111111111',
                'v6-fixed-ip': '2001:db9:0:1::10'}]

        def wrapped_boot(url, key, *boot_args, **boot_kwargs):
            self.assertEqual(nics, boot_kwargs['nics'])
            return old_boot(url, key, *boot_args, **boot_kwargs)

        with mock.patch.object(self.cs.servers, '_boot', wrapped_boot):
            s = self.cs.servers.create(
                name="My server",
                image=1,
                flavor=1,
                meta={'foo': 'bar'},
                userdata="hello moto",
                key_name="fakekey",
                nics=nics
            )
            self.assert_called('POST', '/servers')
            self.assertIsInstance(s, servers.Server)

    def test_create_server_userdata_file_object(self):
        s = self.cs.servers.create(
            name="My server",
            image=1,
            flavor=1,
            meta={'foo': 'bar'},
            userdata=six.StringIO('hello moto'),
            files={
                '/etc/passwd': 'some data',                 # a file
                '/tmp/foo.txt': six.StringIO('data'),   # a stream
            },
        )
        self.assert_called('POST', '/servers')
        self.assertIsInstance(s, servers.Server)

    def test_create_server_userdata_unicode(self):
        s = self.cs.servers.create(
            name="My server",
            image=1,
            flavor=1,
            meta={'foo': 'bar'},
            userdata=six.u('こんにちは'),
            key_name="fakekey",
            files={
                '/etc/passwd': 'some data',                 # a file
                '/tmp/foo.txt': six.StringIO('data'),   # a stream
            },
        )
        self.assert_called('POST', '/servers')
        self.assertIsInstance(s, servers.Server)

    def test_create_server_userdata_utf8(self):
        s = self.cs.servers.create(
            name="My server",
            image=1,
            flavor=1,
            meta={'foo': 'bar'},
            userdata='こんにちは',
            key_name="fakekey",
            files={
                '/etc/passwd': 'some data',                 # a file
                '/tmp/foo.txt': six.StringIO('data'),   # a stream
            },
        )
        self.assert_called('POST', '/servers')
        self.assertIsInstance(s, servers.Server)

    def test_create_server_return_reservation_id(self):
        s = self.cs.servers.create(
            name="My server",
            image=1,
            flavor=1,
            reservation_id=True
        )
        expected_body = {
            'server': {
                'name': 'My server',
                'image_ref': '1',
                'flavor_ref': '1',
                'os-multiple-create:min_count': 1,
                'os-multiple-create:max_count': 1,
                'os-multiple-create:return_reservation_id': True,
            }
        }
        self.assert_called('POST', '/servers', expected_body)
        self.assertIsInstance(s, servers.Server)

    def test_update_server(self):
        s = self.cs.servers.get(1234)

        # Update via instance
        s.update(name='hi')
        self.assert_called('PUT', '/servers/1234')
        s.update(name='hi')
        self.assert_called('PUT', '/servers/1234')

        # Silly, but not an error
        s.update()

        # Update via manager
        self.cs.servers.update(s, name='hi')
        self.assert_called('PUT', '/servers/1234')

    def test_delete_server(self):
        s = self.cs.servers.get(1234)
        s.delete()
        self.assert_called('DELETE', '/servers/1234')
        self.cs.servers.delete(1234)
        self.assert_called('DELETE', '/servers/1234')
        self.cs.servers.delete(s)
        self.assert_called('DELETE', '/servers/1234')

    def test_delete_server_meta(self):
        self.cs.servers.delete_meta(1234, ['test_key'])
        self.assert_called('DELETE', '/servers/1234/metadata/test_key')

    def test_set_server_meta(self):
        self.cs.servers.set_meta(1234, {'test_key': 'test_value'})
        self.assert_called('POST', '/servers/1234/metadata',
                           {'metadata': {'test_key': 'test_value'}})

    def test_find(self):
        server = self.cs.servers.find(name='sample-server')
        self.assert_called('GET', '/servers/1234')
        self.assertEqual('sample-server', server.name)

        self.assertRaises(exceptions.NoUniqueMatch, self.cs.servers.find,
                          flavor={"id": 1, "name": "256 MB Server"})

        sl = self.cs.servers.findall(flavor={"id": 1, "name": "256 MB Server"})
        self.assertEqual([1234, 5678, 9012], [s.id for s in sl])

    def test_reboot_server(self):
        s = self.cs.servers.get(1234)
        s.reboot()
        self.assert_called('POST', '/servers/1234/action')
        self.cs.servers.reboot(s, reboot_type='HARD')
        self.assert_called('POST', '/servers/1234/action')

    def test_rebuild_server(self):
        s = self.cs.servers.get(1234)
        s.rebuild(image=1)
        self.assert_called('POST', '/servers/1234/action')
        self.cs.servers.rebuild(s, image=1)
        self.assert_called('POST', '/servers/1234/action')
        s.rebuild(image=1, password='5678')
        self.assert_called('POST', '/servers/1234/action')
        self.cs.servers.rebuild(s, image=1, password='5678')
        self.assert_called('POST', '/servers/1234/action')

    def test_resize_server(self):
        s = self.cs.servers.get(1234)
        s.resize(flavor=1)
        self.assert_called('POST', '/servers/1234/action')
        self.cs.servers.resize(s, flavor=1)
        self.assert_called('POST', '/servers/1234/action')

    def test_confirm_resized_server(self):
        s = self.cs.servers.get(1234)
        s.confirm_resize()
        self.assert_called('POST', '/servers/1234/action')
        self.cs.servers.confirm_resize(s)
        self.assert_called('POST', '/servers/1234/action')

    def test_revert_resized_server(self):
        s = self.cs.servers.get(1234)
        s.revert_resize()
        self.assert_called('POST', '/servers/1234/action')
        self.cs.servers.revert_resize(s)
        self.assert_called('POST', '/servers/1234/action')

    def test_migrate_server(self):
        s = self.cs.servers.get(1234)
        s.migrate()
        self.assert_called('POST', '/servers/1234/action')
        self.cs.servers.migrate(s)
        self.assert_called('POST', '/servers/1234/action')

    def test_add_fixed_ip(self):
        s = self.cs.servers.get(1234)
        s.add_fixed_ip(1)
        self.assert_called('POST', '/servers/1234/action')
        self.cs.servers.add_fixed_ip(s, 1)
        self.assert_called('POST', '/servers/1234/action')

    def test_remove_fixed_ip(self):
        s = self.cs.servers.get(1234)
        s.remove_fixed_ip('10.0.0.1')
        self.assert_called('POST', '/servers/1234/action')
        self.cs.servers.remove_fixed_ip(s, '10.0.0.1')
        self.assert_called('POST', '/servers/1234/action')

    def test_stop(self):
        s = self.cs.servers.get(1234)
        s.stop()
        self.assert_called('POST', '/servers/1234/action')
        self.cs.servers.stop(s)
        self.assert_called('POST', '/servers/1234/action')

    def test_force_delete(self):
        s = self.cs.servers.get(1234)
        s.force_delete()
        self.assert_called('POST', '/servers/1234/action')
        self.cs.servers.force_delete(s)
        self.assert_called('POST', '/servers/1234/action')

    def test_restore(self):
        s = self.cs.servers.get(1234)
        s.restore()
        self.assert_called('POST', '/servers/1234/action')
        self.cs.servers.restore(s)
        self.assert_called('POST', '/servers/1234/action')

    def test_start(self):
        s = self.cs.servers.get(1234)
        s.start()
        self.assert_called('POST', '/servers/1234/action')
        self.cs.servers.start(s)
        self.assert_called('POST', '/servers/1234/action')

    def test_rescue(self):
        s = self.cs.servers.get(1234)
        s.rescue()
        self.assert_called('POST', '/servers/1234/action')
        self.cs.servers.rescue(s)
        self.assert_called('POST', '/servers/1234/action')

    def test_unrescue(self):
        s = self.cs.servers.get(1234)
        s.unrescue()
        self.assert_called('POST', '/servers/1234/action')
        self.cs.servers.unrescue(s)
        self.assert_called('POST', '/servers/1234/action')

    def test_lock(self):
        s = self.cs.servers.get(1234)
        s.lock()
        self.assert_called('POST', '/servers/1234/action')
        self.cs.servers.lock(s)
        self.assert_called('POST', '/servers/1234/action')

    def test_unlock(self):
        s = self.cs.servers.get(1234)
        s.unlock()
        self.assert_called('POST', '/servers/1234/action')
        self.cs.servers.unlock(s)
        self.assert_called('POST', '/servers/1234/action')

    def test_backup(self):
        s = self.cs.servers.get(1234)
        s.backup('back1', 'daily', 1)
        self.assert_called('POST', '/servers/1234/action')
        self.cs.servers.backup(s, 'back1', 'daily', 2)
        self.assert_called('POST', '/servers/1234/action')

    def test_get_console_output_without_length(self):
        success = 'foo'
        s = self.cs.servers.get(1234)
        s.get_console_output()
        self.assertEqual(success, s.get_console_output())
        self.assert_called('POST', '/servers/1234/action')

        self.cs.servers.get_console_output(s)
        self.assertEqual(success, self.cs.servers.get_console_output(s))
        self.assert_called('POST', '/servers/1234/action',
                           {'get_console_output': {'length': -1}})

    def test_get_console_output_with_length(self):
        success = 'foo'

        s = self.cs.servers.get(1234)
        s.get_console_output(length=50)
        self.assertEqual(success, s.get_console_output(length=50))
        self.assert_called('POST', '/servers/1234/action',
                           {'get_console_output': {'length': 50}})

        self.cs.servers.get_console_output(s, length=50)
        self.assertEqual(success,
                         self.cs.servers.get_console_output(s, length=50))
        self.assert_called('POST', '/servers/1234/action',
                           {'get_console_output': {'length': 50}})

    def test_get_password(self):
        s = self.cs.servers.get(1234)
        self.assertEqual('', s.get_password('/foo/id_rsa'))
        self.assert_called('GET', '/servers/1234/os-server-password')

    def test_clear_password(self):
        s = self.cs.servers.get(1234)
        s.clear_password()
        self.assert_called('DELETE', '/servers/1234/os-server-password')

    def test_get_server_diagnostics(self):
        s = self.cs.servers.get(1234)
        diagnostics = s.diagnostics()
        self.assertTrue(diagnostics is not None)
        self.assert_called('GET', '/servers/1234/os-server-diagnostics')

        diagnostics_from_manager = self.cs.servers.diagnostics(1234)
        self.assertTrue(diagnostics_from_manager is not None)
        self.assert_called('GET', '/servers/1234/os-server-diagnostics')

        self.assertEqual(diagnostics_from_manager[1], diagnostics[1])

    def test_get_vnc_console(self):
        s = self.cs.servers.get(1234)
        s.get_vnc_console('fake')
        self.assert_called('POST', '/servers/1234/action')

        self.cs.servers.get_vnc_console(s, 'fake')
        self.assert_called('POST', '/servers/1234/action')

    def test_get_spice_console(self):
        s = self.cs.servers.get(1234)
        s.get_spice_console('fake')
        self.assert_called('POST', '/servers/1234/action')

        self.cs.servers.get_spice_console(s, 'fake')
        self.assert_called('POST', '/servers/1234/action')

    def test_create_image(self):
        s = self.cs.servers.get(1234)
        s.create_image('123')
        self.assert_called('POST', '/servers/1234/action')
        s.create_image('123', {})
        self.assert_called('POST', '/servers/1234/action')
        self.cs.servers.create_image(s, '123')
        self.assert_called('POST', '/servers/1234/action')
        self.cs.servers.create_image(s, '123', {})

    def test_live_migrate_server(self):
        s = self.cs.servers.get(1234)
        s.live_migrate(host='hostname', block_migration=False,
                       disk_over_commit=False)
        self.assert_called('POST', '/servers/1234/action')
        self.cs.servers.live_migrate(s, host='hostname', block_migration=False,
                                     disk_over_commit=False)
        self.assert_called('POST', '/servers/1234/action')

    def test_reset_state(self):
        s = self.cs.servers.get(1234)
        s.reset_state('newstate')
        self.assert_called('POST', '/servers/1234/action')
        self.cs.servers.reset_state(s, 'newstate')
        self.assert_called('POST', '/servers/1234/action')

    def test_reset_network(self):
        s = self.cs.servers.get(1234)
        s.reset_network()
        self.assert_called('POST', '/servers/1234/action')
        self.cs.servers.reset_network(s)
        self.assert_called('POST', '/servers/1234/action')

    def test_evacuate(self):
        s = self.cs.servers.get(1234)
        s.evacuate('fake_target_host', 'True')
        self.assert_called('POST', '/servers/1234/action')
        self.cs.servers.evacuate(s, 'fake_target_host',
                                 'False', 'NewAdminPassword')
        self.assert_called('POST', '/servers/1234/action')

    def test_interface_list(self):
        s = self.cs.servers.get(1234)
        s.interface_list()
        self.assert_called('GET', '/servers/1234/os-attach-interfaces')

    def test_interface_attach(self):
        s = self.cs.servers.get(1234)
        s.interface_attach(None, None, None)
        self.assert_called('POST', '/servers/1234/os-attach-interfaces')

    def test_interface_detach(self):
        s = self.cs.servers.get(1234)
        s.interface_detach('port-id')
        self.assert_called('DELETE',
                           '/servers/1234/os-attach-interfaces/port-id')
