# -*- coding: utf-8 -*-
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
from novaclient.openstack.common import jsonutils
from novaclient.tests.fixture_data import client
from novaclient.tests.fixture_data import floatingips
from novaclient.tests.fixture_data import servers as data
from novaclient.tests import utils
from novaclient.v1_1 import servers


class ServersTest(utils.FixturedTestCase):

    client_fixture_class = client.V1
    data_fixture_class = data.V1

    def setUp(self):
        super(ServersTest, self).setUp()
        self.useFixture(floatingips.FloatingFixture(self.requests))

    def test_list_servers(self):
        sl = self.cs.servers.list()
        self.assert_called('GET', '/servers/detail')
        [self.assertIsInstance(s, servers.Server) for s in sl]

    def test_list_servers_undetailed(self):
        sl = self.cs.servers.list(detailed=False)
        self.assert_called('GET', '/servers')
        [self.assertIsInstance(s, servers.Server) for s in sl]

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

    def test_create_server_boot_from_volume_with_nics(self):
        old_boot = self.cs.servers._boot

        nics = [{'net-id': '11111111-1111-1111-1111-111111111111',
                 'v4-fixed-ip': '10.0.0.7'}]
        bdm = {"volume_size": "1",
               "volume_id": "11111111-1111-1111-1111-111111111111",
               "delete_on_termination": "0",
               "device_name": "vda"}

        def wrapped_boot(url, key, *boot_args, **boot_kwargs):
            self.assertEqual(boot_kwargs['block_device_mapping'], bdm)
            self.assertEqual(boot_kwargs['nics'], nics)
            return old_boot(url, key, *boot_args, **boot_kwargs)

        @mock.patch.object(self.cs.servers, '_boot', wrapped_boot)
        def test_create_server_from_volume():
            s = self.cs.servers.create(
                name="My server",
                image=1,
                flavor=1,
                meta={'foo': 'bar'},
                userdata="hello moto",
                key_name="fakekey",
                block_device_mapping=bdm,
                nics=nics
            )
            self.assert_called('POST', '/os-volumes_boot')
            self.assertIsInstance(s, servers.Server)

        test_create_server_from_volume()

    def test_create_server_boot_with_nics_ipv6(self):
        old_boot = self.cs.servers._boot
        nics = [{'net-id': '11111111-1111-1111-1111-111111111111',
                'v6-fixed-ip': '2001:db9:0:1::10'}]

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

    def _create_disk_config(self, disk_config):
        s = self.cs.servers.create(
            name="My server",
            image=1,
            flavor=1,
            disk_config=disk_config
        )
        self.assert_called('POST', '/servers')
        self.assertIsInstance(s, servers.Server)

        # verify disk config param was used in the request:
        body = jsonutils.loads(self.requests.last_request.body)
        server = body['server']
        self.assertTrue('OS-DCF:diskConfig' in server)
        self.assertEqual(disk_config, server['OS-DCF:diskConfig'])

    def test_create_server_disk_config_auto(self):
        self._create_disk_config('AUTO')

    def test_create_server_disk_config_manual(self):
        self._create_disk_config('MANUAL')

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

    def test_set_server_meta_item(self):
        self.cs.servers.set_meta_item(1234, 'test_key', 'test_value')
        self.assert_called('PUT', '/servers/1234/metadata/test_key',
                           {'meta': {'test_key': 'test_value'}})

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

    def _rebuild_resize_disk_config(self, disk_config, operation="rebuild"):
        s = self.cs.servers.get(1234)

        if operation == "rebuild":
            s.rebuild(image=1, disk_config=disk_config)
        elif operation == "resize":
            s.resize(flavor=1, disk_config=disk_config)
        self.assert_called('POST', '/servers/1234/action')

        # verify disk config param was used in the request:
        body = jsonutils.loads(self.requests.last_request.body)

        d = body[operation]
        self.assertTrue('OS-DCF:diskConfig' in d)
        self.assertEqual(disk_config, d['OS-DCF:diskConfig'])

    def test_rebuild_server_disk_config_auto(self):
        self._rebuild_resize_disk_config('AUTO')

    def test_rebuild_server_disk_config_manual(self):
        self._rebuild_resize_disk_config('MANUAL')

    def test_rebuild_server_preserve_ephemeral(self):
        s = self.cs.servers.get(1234)
        s.rebuild(image=1, preserve_ephemeral=True)
        self.assert_called('POST', '/servers/1234/action')
        body = jsonutils.loads(self.requests.last_request.body)
        d = body['rebuild']
        self.assertIn('preserve_ephemeral', d)
        self.assertEqual(True, d['preserve_ephemeral'])

    def test_rebuild_server_name_meta_files(self):
        files = {'/etc/passwd': 'some data'}
        s = self.cs.servers.get(1234)
        s.rebuild(image=1, name='new', meta={'foo': 'bar'}, files=files)
        body = jsonutils.loads(self.requests.last_request.body)
        d = body['rebuild']
        self.assertEqual('new', d['name'])
        self.assertEqual({'foo': 'bar'}, d['metadata'])
        self.assertEqual('/etc/passwd',
                         d['personality'][0]['path'])

    def test_resize_server(self):
        s = self.cs.servers.get(1234)
        s.resize(flavor=1)
        self.assert_called('POST', '/servers/1234/action')
        self.cs.servers.resize(s, flavor=1)
        self.assert_called('POST', '/servers/1234/action')

    def test_resize_server_disk_config_auto(self):
        self._rebuild_resize_disk_config('AUTO', 'resize')

    def test_resize_server_disk_config_manual(self):
        self._rebuild_resize_disk_config('MANUAL', 'resize')

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

    def test_add_floating_ip(self):
        s = self.cs.servers.get(1234)
        s.add_floating_ip('11.0.0.1')
        self.assert_called('POST', '/servers/1234/action')
        self.cs.servers.add_floating_ip(s, '11.0.0.1')
        self.assert_called('POST', '/servers/1234/action')
        f = self.cs.floating_ips.list()[0]
        self.cs.servers.add_floating_ip(s, f)
        self.assert_called('POST', '/servers/1234/action')
        s.add_floating_ip(f)
        self.assert_called('POST', '/servers/1234/action')

    def test_add_floating_ip_to_fixed(self):
        s = self.cs.servers.get(1234)
        s.add_floating_ip('11.0.0.1', fixed_address='12.0.0.1')
        self.assert_called('POST', '/servers/1234/action')
        self.cs.servers.add_floating_ip(s, '11.0.0.1',
                                   fixed_address='12.0.0.1')
        self.assert_called('POST', '/servers/1234/action')
        f = self.cs.floating_ips.list()[0]
        self.cs.servers.add_floating_ip(s, f)
        self.assert_called('POST', '/servers/1234/action')
        s.add_floating_ip(f)
        self.assert_called('POST', '/servers/1234/action')

    def test_remove_floating_ip(self):
        s = self.cs.servers.get(1234)
        s.remove_floating_ip('11.0.0.1')
        self.assert_called('POST', '/servers/1234/action')
        self.cs.servers.remove_floating_ip(s, '11.0.0.1')
        self.assert_called('POST', '/servers/1234/action')
        f = self.cs.floating_ips.list()[0]
        self.cs.servers.remove_floating_ip(s, f)
        self.assert_called('POST', '/servers/1234/action')
        s.remove_floating_ip(f)
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
        self.assert_called('POST', '/servers/1234/action')

    def test_get_console_output_with_length(self):
        success = 'foo'

        s = self.cs.servers.get(1234)
        s.get_console_output(length=50)
        self.assertEqual(success, s.get_console_output(length=50))
        self.assert_called('POST', '/servers/1234/action')

        self.cs.servers.get_console_output(s, length=50)
        self.assertEqual(success,
                         self.cs.servers.get_console_output(s, length=50))
        self.assert_called('POST', '/servers/1234/action')

    # Testing password methods with the following password and key
    #
    # Clear password: FooBar123
    #
    # RSA Private Key: novaclient/tests/idfake.pem
    #
    # Encrypted password
    # OIuEuQttO8Rk93BcKlwHQsziDAnkAm/V6V8VPToA8ZeUaUBWwS0gwo2K6Y61Z96r
    # qG447iRz0uTEEYq3RAYJk1mh3mMIRVl27t8MtIecR5ggVVbz1S9AwXJQypDKl0ho
    # QFvhCBcMWPohyGewDJOhDbtuN1IoFI9G55ZvFwCm5y7m7B2aVcoLeIsJZE4PLsIw
    # /y5a6Z3/AoJZYGG7IH5WN88UROU3B9JZGFB2qtPLQTOvDMZLUhoPRIJeHiVSlo1N
    # tI2/++UsXVg3ow6ItqCJGgdNuGG5JB+bslDHWPxROpesEIHdczk46HCpHQN8f1sk
    # Hi/fmZZNQQqj1Ijq0caOIw==

    def test_get_password(self):
        s = self.cs.servers.get(1234)
        self.assertEqual(b'FooBar123',
                         s.get_password('novaclient/tests/idfake.pem'))
        self.assert_called('GET', '/servers/1234/os-server-password')

    def test_get_password_without_key(self):
        s = self.cs.servers.get(1234)
        self.assertEqual(
            'OIuEuQttO8Rk93BcKlwHQsziDAnkAm/V6V8VPToA8ZeUaUBWwS0gwo2K6Y61Z96r'
            'qG447iRz0uTEEYq3RAYJk1mh3mMIRVl27t8MtIecR5ggVVbz1S9AwXJQypDKl0ho'
            'QFvhCBcMWPohyGewDJOhDbtuN1IoFI9G55ZvFwCm5y7m7B2aVcoLeIsJZE4PLsIw'
            '/y5a6Z3/AoJZYGG7IH5WN88UROU3B9JZGFB2qtPLQTOvDMZLUhoPRIJeHiVSlo1N'
            'tI2/++UsXVg3ow6ItqCJGgdNuGG5JB+bslDHWPxROpesEIHdczk46HCpHQN8f1sk'
            'Hi/fmZZNQQqj1Ijq0caOIw==', s.get_password())
        self.assert_called('GET', '/servers/1234/os-server-password')

    def test_clear_password(self):
        s = self.cs.servers.get(1234)
        s.clear_password()
        self.assert_called('DELETE', '/servers/1234/os-server-password')

    def test_get_server_diagnostics(self):
        s = self.cs.servers.get(1234)
        diagnostics = s.diagnostics()
        self.assertTrue(diagnostics is not None)
        self.assert_called('GET', '/servers/1234/diagnostics')

        diagnostics_from_manager = self.cs.servers.diagnostics(1234)
        self.assertTrue(diagnostics_from_manager is not None)
        self.assert_called('GET', '/servers/1234/diagnostics')

        self.assertEqual(diagnostics[1], diagnostics_from_manager[1])

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

    def test_get_serial_console(self):
        s = self.cs.servers.get(1234)
        s.get_serial_console('fake')
        self.assert_called('POST', '/servers/1234/action')

        self.cs.servers.get_serial_console(s, 'fake')
        self.assert_called('POST', '/servers/1234/action')

    def test_get_rdp_console(self):
        s = self.cs.servers.get(1234)
        s.get_rdp_console('fake')
        self.assert_called('POST', '/servers/1234/action')

        self.cs.servers.get_rdp_console(s, 'fake')
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

    def test_add_security_group(self):
        s = self.cs.servers.get(1234)
        s.add_security_group('newsg')
        self.assert_called('POST', '/servers/1234/action')
        self.cs.servers.add_security_group(s, 'newsg')
        self.assert_called('POST', '/servers/1234/action')

    def test_remove_security_group(self):
        s = self.cs.servers.get(1234)
        s.remove_security_group('oldsg')
        self.assert_called('POST', '/servers/1234/action')
        self.cs.servers.remove_security_group(s, 'oldsg')
        self.assert_called('POST', '/servers/1234/action')

    def test_list_security_group(self):
        s = self.cs.servers.get(1234)
        s.list_security_group()
        self.assert_called('GET', '/servers/1234/os-security-groups')

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
        self.assert_called('GET', '/servers/1234/os-interface')

    def test_interface_list_result_string_representable(self):
        """Test for bugs.launchpad.net/python-novaclient/+bug/1280453."""
        # According to https://github.com/openstack/nova/blob/master/
        # nova/api/openstack/compute/contrib/attach_interfaces.py#L33,
        # the attach_interface extension get method will return a json
        # object partly like this:
        interface_list = [{
            'net_id': 'd7745cf5-63f9-4883-b0ae-983f061e4f23',
            'port_id': 'f35079da-36d5-4513-8ec1-0298d703f70e',
            'mac_addr': 'fa:16:3e:4c:37:c8',
            'port_state': 'ACTIVE',
            'fixed_ips': [{
                'subnet_id': 'f1ad93ad-2967-46ba-b403-e8cbbe65f7fa',
                'ip_address': '10.2.0.96'
                }]
            }]
        # If server is not string representable, it will raise an exception,
        # because attribute named 'name' cannot be found.
        # Parameter 'loaded' must be True or it will try to get attribute
        # 'id' then fails (lazy load detail), this is exactly same as
        # novaclient.base.Manager._list()
        s = servers.Server(servers.ServerManager, interface_list[0],
                           loaded=True)
        # Trigger the __repr__ magic method
        self.assertEqual('<Server: unknown-name>', '%r' % s)

    def test_interface_attach(self):
        s = self.cs.servers.get(1234)
        s.interface_attach(None, None, None)
        self.assert_called('POST', '/servers/1234/os-interface')

    def test_interface_detach(self):
        s = self.cs.servers.get(1234)
        s.interface_detach('port-id')
        self.assert_called('DELETE', '/servers/1234/os-interface/port-id')
