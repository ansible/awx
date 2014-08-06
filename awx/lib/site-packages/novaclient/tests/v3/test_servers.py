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
from novaclient.tests import utils
from novaclient.tests.v3 import fakes
from novaclient.v3 import servers


cs = fakes.FakeClient()


class ServersTest(utils.TestCase):

    def test_list_servers(self):
        sl = cs.servers.list()
        cs.assert_called('GET', '/servers/detail')
        for s in sl:
            self.assertIsInstance(s, servers.Server)

    def test_list_servers_undetailed(self):
        sl = cs.servers.list(detailed=False)
        cs.assert_called('GET', '/servers')
        for s in sl:
            self.assertIsInstance(s, servers.Server)

    def test_list_servers_with_marker_limit(self):
        sl = cs.servers.list(marker=1234, limit=2)
        cs.assert_called('GET', '/servers/detail?limit=2&marker=1234')
        for s in sl:
            self.assertIsInstance(s, servers.Server)

    def test_get_server_details(self):
        s = cs.servers.get(1234)
        cs.assert_called('GET', '/servers/1234')
        self.assertIsInstance(s, servers.Server)
        self.assertEqual(s.id, 1234)
        self.assertEqual(s.status, 'BUILD')

    def test_get_server_promote_details(self):
        s1 = cs.servers.list(detailed=False)[0]
        s2 = cs.servers.list(detailed=True)[0]
        self.assertNotEqual(s1._info, s2._info)
        s1.get()
        self.assertEqual(s1._info, s2._info)

    def test_create_server(self):
        s = cs.servers.create(
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
        cs.assert_called('POST', '/servers')
        self.assertIsInstance(s, servers.Server)

    def test_create_server_boot_with_nics_ipv4(self):
        old_boot = cs.servers._boot
        nics = [{'net-id': '11111111-1111-1111-1111-111111111111',
                'v4-fixed-ip': '10.10.0.7'}]

        def wrapped_boot(url, key, *boot_args, **boot_kwargs):
            self.assertEqual(boot_kwargs['nics'], nics)
            return old_boot(url, key, *boot_args, **boot_kwargs)

        with mock.patch.object(cs.servers, '_boot', wrapped_boot):
            s = cs.servers.create(
                name="My server",
                image=1,
                flavor=1,
                meta={'foo': 'bar'},
                userdata="hello moto",
                key_name="fakekey",
                nics=nics
            )
            cs.assert_called('POST', '/servers')
            self.assertIsInstance(s, servers.Server)

    def test_create_server_boot_with_nics_ipv6(self):
        old_boot = cs.servers._boot
        nics = [{'net-id': '11111111-1111-1111-1111-111111111111',
                'v6-fixed-ip': '2001:db9:0:1::10'}]

        def wrapped_boot(url, key, *boot_args, **boot_kwargs):
            self.assertEqual(boot_kwargs['nics'], nics)
            return old_boot(url, key, *boot_args, **boot_kwargs)

        with mock.patch.object(cs.servers, '_boot', wrapped_boot):
            s = cs.servers.create(
                name="My server",
                image=1,
                flavor=1,
                meta={'foo': 'bar'},
                userdata="hello moto",
                key_name="fakekey",
                nics=nics
            )
            cs.assert_called('POST', '/servers')
            self.assertIsInstance(s, servers.Server)

    def test_create_server_userdata_file_object(self):
        s = cs.servers.create(
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
        cs.assert_called('POST', '/servers')
        self.assertIsInstance(s, servers.Server)

    def test_create_server_userdata_unicode(self):
        s = cs.servers.create(
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
        cs.assert_called('POST', '/servers')
        self.assertIsInstance(s, servers.Server)

    def test_create_server_userdata_utf8(self):
        s = cs.servers.create(
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
        cs.assert_called('POST', '/servers')
        self.assertIsInstance(s, servers.Server)

    def test_create_server_return_reservation_id(self):
        s = cs.servers.create(
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
        cs.assert_called('POST', '/servers', expected_body)
        self.assertIsInstance(s, servers.Server)

    def test_update_server(self):
        s = cs.servers.get(1234)

        # Update via instance
        s.update(name='hi')
        cs.assert_called('PUT', '/servers/1234')
        s.update(name='hi')
        cs.assert_called('PUT', '/servers/1234')

        # Silly, but not an error
        s.update()

        # Update via manager
        cs.servers.update(s, name='hi')
        cs.assert_called('PUT', '/servers/1234')

    def test_delete_server(self):
        s = cs.servers.get(1234)
        s.delete()
        cs.assert_called('DELETE', '/servers/1234')
        cs.servers.delete(1234)
        cs.assert_called('DELETE', '/servers/1234')
        cs.servers.delete(s)
        cs.assert_called('DELETE', '/servers/1234')

    def test_delete_server_meta(self):
        cs.servers.delete_meta(1234, ['test_key'])
        cs.assert_called('DELETE', '/servers/1234/metadata/test_key')

    def test_set_server_meta(self):
        cs.servers.set_meta(1234, {'test_key': 'test_value'})
        cs.assert_called('POST', '/servers/1234/metadata',
                         {'metadata': {'test_key': 'test_value'}})

    def test_find(self):
        server = cs.servers.find(name='sample-server')
        cs.assert_called('GET', '/servers', pos=-2)
        cs.assert_called('GET', '/servers/1234', pos=-1)
        self.assertEqual(server.name, 'sample-server')

        self.assertRaises(exceptions.NoUniqueMatch, cs.servers.find,
                          flavor={"id": 1, "name": "256 MB Server"})

        sl = cs.servers.findall(flavor={"id": 1, "name": "256 MB Server"})
        self.assertEqual([s.id for s in sl], [1234, 5678, 9012])

    def test_reboot_server(self):
        s = cs.servers.get(1234)
        s.reboot()
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.reboot(s, reboot_type='HARD')
        cs.assert_called('POST', '/servers/1234/action')

    def test_rebuild_server(self):
        s = cs.servers.get(1234)
        s.rebuild(image=1)
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.rebuild(s, image=1)
        cs.assert_called('POST', '/servers/1234/action')
        s.rebuild(image=1, password='5678')
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.rebuild(s, image=1, password='5678')
        cs.assert_called('POST', '/servers/1234/action')

    def test_resize_server(self):
        s = cs.servers.get(1234)
        s.resize(flavor=1)
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.resize(s, flavor=1)
        cs.assert_called('POST', '/servers/1234/action')

    def test_confirm_resized_server(self):
        s = cs.servers.get(1234)
        s.confirm_resize()
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.confirm_resize(s)
        cs.assert_called('POST', '/servers/1234/action')

    def test_revert_resized_server(self):
        s = cs.servers.get(1234)
        s.revert_resize()
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.revert_resize(s)
        cs.assert_called('POST', '/servers/1234/action')

    def test_migrate_server(self):
        s = cs.servers.get(1234)
        s.migrate()
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.migrate(s)
        cs.assert_called('POST', '/servers/1234/action')

    def test_add_fixed_ip(self):
        s = cs.servers.get(1234)
        s.add_fixed_ip(1)
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.add_fixed_ip(s, 1)
        cs.assert_called('POST', '/servers/1234/action')

    def test_remove_fixed_ip(self):
        s = cs.servers.get(1234)
        s.remove_fixed_ip('10.0.0.1')
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.remove_fixed_ip(s, '10.0.0.1')
        cs.assert_called('POST', '/servers/1234/action')

    def test_stop(self):
        s = cs.servers.get(1234)
        s.stop()
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.stop(s)
        cs.assert_called('POST', '/servers/1234/action')

    def test_force_delete(self):
        s = cs.servers.get(1234)
        s.force_delete()
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.force_delete(s)
        cs.assert_called('POST', '/servers/1234/action')

    def test_restore(self):
        s = cs.servers.get(1234)
        s.restore()
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.restore(s)
        cs.assert_called('POST', '/servers/1234/action')

    def test_start(self):
        s = cs.servers.get(1234)
        s.start()
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.start(s)
        cs.assert_called('POST', '/servers/1234/action')

    def test_rescue(self):
        s = cs.servers.get(1234)
        s.rescue()
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.rescue(s)
        cs.assert_called('POST', '/servers/1234/action')

    def test_unrescue(self):
        s = cs.servers.get(1234)
        s.unrescue()
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.unrescue(s)
        cs.assert_called('POST', '/servers/1234/action')

    def test_lock(self):
        s = cs.servers.get(1234)
        s.lock()
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.lock(s)
        cs.assert_called('POST', '/servers/1234/action')

    def test_unlock(self):
        s = cs.servers.get(1234)
        s.unlock()
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.unlock(s)
        cs.assert_called('POST', '/servers/1234/action')

    def test_backup(self):
        s = cs.servers.get(1234)
        s.backup('back1', 'daily', 1)
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.backup(s, 'back1', 'daily', 2)
        cs.assert_called('POST', '/servers/1234/action')

    def test_get_console_output_without_length(self):
        success = 'foo'
        s = cs.servers.get(1234)
        s.get_console_output()
        self.assertEqual(s.get_console_output(), success)
        cs.assert_called('POST', '/servers/1234/action')

        cs.servers.get_console_output(s)
        self.assertEqual(cs.servers.get_console_output(s), success)
        cs.assert_called('POST', '/servers/1234/action',
                         {'get_console_output': {'length': -1}})

    def test_get_console_output_with_length(self):
        success = 'foo'

        s = cs.servers.get(1234)
        s.get_console_output(length=50)
        self.assertEqual(s.get_console_output(length=50), success)
        cs.assert_called('POST', '/servers/1234/action',
                         {'get_console_output': {'length': 50}})

        cs.servers.get_console_output(s, length=50)
        self.assertEqual(cs.servers.get_console_output(s, length=50), success)
        cs.assert_called('POST', '/servers/1234/action',
                         {'get_console_output': {'length': 50}})

    def test_get_password(self):
        s = cs.servers.get(1234)
        self.assertEqual(s.get_password('/foo/id_rsa'), '')
        cs.assert_called('GET', '/servers/1234/os-server-password')

    def test_clear_password(self):
        s = cs.servers.get(1234)
        s.clear_password()
        cs.assert_called('DELETE', '/servers/1234/os-server-password')

    def test_get_server_diagnostics(self):
        s = cs.servers.get(1234)
        diagnostics = s.diagnostics()
        self.assertTrue(diagnostics is not None)
        cs.assert_called('GET', '/servers/1234/os-server-diagnostics')

        diagnostics_from_manager = cs.servers.diagnostics(1234)
        self.assertTrue(diagnostics_from_manager is not None)
        cs.assert_called('GET', '/servers/1234/os-server-diagnostics')

        self.assertEqual(diagnostics, diagnostics_from_manager)

    def test_get_vnc_console(self):
        s = cs.servers.get(1234)
        s.get_vnc_console('fake')
        cs.assert_called('POST', '/servers/1234/action')

        cs.servers.get_vnc_console(s, 'fake')
        cs.assert_called('POST', '/servers/1234/action')

    def test_get_spice_console(self):
        s = cs.servers.get(1234)
        s.get_spice_console('fake')
        cs.assert_called('POST', '/servers/1234/action')

        cs.servers.get_spice_console(s, 'fake')
        cs.assert_called('POST', '/servers/1234/action')

    def test_create_image(self):
        s = cs.servers.get(1234)
        s.create_image('123')
        cs.assert_called('POST', '/servers/1234/action')
        s.create_image('123', {})
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.create_image(s, '123')
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.create_image(s, '123', {})

    def test_live_migrate_server(self):
        s = cs.servers.get(1234)
        s.live_migrate(host='hostname', block_migration=False,
                       disk_over_commit=False)
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.live_migrate(s, host='hostname', block_migration=False,
                                disk_over_commit=False)
        cs.assert_called('POST', '/servers/1234/action')

    def test_reset_state(self):
        s = cs.servers.get(1234)
        s.reset_state('newstate')
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.reset_state(s, 'newstate')
        cs.assert_called('POST', '/servers/1234/action')

    def test_reset_network(self):
        s = cs.servers.get(1234)
        s.reset_network()
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.reset_network(s)
        cs.assert_called('POST', '/servers/1234/action')

    def test_evacuate(self):
        s = cs.servers.get(1234)
        s.evacuate('fake_target_host', 'True')
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.evacuate(s, 'fake_target_host', 'False', 'NewAdminPassword')
        cs.assert_called('POST', '/servers/1234/action')

    def test_interface_list(self):
        s = cs.servers.get(1234)
        s.interface_list()
        cs.assert_called('GET', '/servers/1234/os-attach-interfaces')

    def test_interface_attach(self):
        s = cs.servers.get(1234)
        s.interface_attach(None, None, None)
        cs.assert_called('POST', '/servers/1234/os-attach-interfaces')

    def test_interface_detach(self):
        s = cs.servers.get(1234)
        s.interface_detach('port-id')
        cs.assert_called('DELETE',
                         '/servers/1234/os-attach-interfaces/port-id')
