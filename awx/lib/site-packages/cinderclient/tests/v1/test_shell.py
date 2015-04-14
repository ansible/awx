# Copyright 2010 Jacob Kaplan-Moss

# Copyright (c) 2011 OpenStack Foundation
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

import fixtures
from requests_mock.contrib import fixture as requests_mock_fixture

from cinderclient import client
from cinderclient import exceptions
from cinderclient import shell
from cinderclient.v1 import shell as shell_v1
from cinderclient.tests.v1 import fakes
from cinderclient.tests import utils
from cinderclient.tests.fixture_data import keystone_client


class ShellTest(utils.TestCase):

    FAKE_ENV = {
        'CINDER_USERNAME': 'username',
        'CINDER_PASSWORD': 'password',
        'CINDER_PROJECT_ID': 'project_id',
        'OS_VOLUME_API_VERSION': '1',
        'CINDER_URL': keystone_client.BASE_URL,
    }

    # Patch os.environ to avoid required auth info.
    def setUp(self):
        """Run before each test."""
        super(ShellTest, self).setUp()
        for var in self.FAKE_ENV:
            self.useFixture(fixtures.EnvironmentVariable(var,
                                                         self.FAKE_ENV[var]))

        self.shell = shell.OpenStackCinderShell()

        # HACK(bcwaldon): replace this when we start using stubs
        self.old_get_client_class = client.get_client_class
        client.get_client_class = lambda *_: fakes.FakeClient

        self.requests = self.useFixture(requests_mock_fixture.Fixture())
        self.requests.register_uri(
            'GET', keystone_client.BASE_URL,
            text=keystone_client.keystone_request_callback)

    def tearDown(self):
        # For some method like test_image_meta_bad_action we are
        # testing a SystemExit to be thrown and object self.shell has
        # no time to get instantatiated which is OK in this case, so
        # we make sure the method is there before launching it.
        if hasattr(self.shell, 'cs'):
            self.shell.cs.clear_callstack()

        # HACK(bcwaldon): replace this when we start using stubs
        client.get_client_class = self.old_get_client_class
        super(ShellTest, self).tearDown()

    def run_command(self, cmd):
        self.shell.main(cmd.split())

    def assert_called(self, method, url, body=None, **kwargs):
        return self.shell.cs.assert_called(method, url, body, **kwargs)

    def assert_called_anytime(self, method, url, body=None):
        return self.shell.cs.assert_called_anytime(method, url, body)

    def test_extract_metadata(self):
        # mimic the result of argparse's parse_args() method
        class Arguments:

            def __init__(self, metadata=[]):
                self.metadata = metadata

        inputs = [
            ([], {}),
            (["key=value"], {"key": "value"}),
            (["key"], {"key": None}),
            (["k1=v1", "k2=v2"], {"k1": "v1", "k2": "v2"}),
            (["k1=v1", "k2"], {"k1": "v1", "k2": None}),
            (["k1", "k2=v2"], {"k1": None, "k2": "v2"})
        ]

        for input in inputs:
            args = Arguments(metadata=input[0])
            self.assertEqual(input[1], shell_v1._extract_metadata(args))

    def test_translate_volume_keys(self):
        cs = fakes.FakeClient()
        v = cs.volumes.list()[0]
        setattr(v, 'os-vol-tenant-attr:tenant_id', 'fake_tenant')
        setattr(v, '_info', {'attachments': [{'server_id': 1234}],
                'id': 1234, 'name': 'sample-volume',
                'os-vol-tenant-attr:tenant_id': 'fake_tenant'})
        shell_v1._translate_volume_keys([v])
        self.assertEqual(v.tenant_id, 'fake_tenant')

    def test_list(self):
        self.run_command('list')
        # NOTE(jdg): we default to detail currently
        self.assert_called('GET', '/volumes/detail')

    def test_list_filter_status(self):
        self.run_command('list --status=available')
        self.assert_called('GET', '/volumes/detail?status=available')

    def test_list_filter_display_name(self):
        self.run_command('list --display-name=1234')
        self.assert_called('GET', '/volumes/detail?display_name=1234')

    def test_list_all_tenants(self):
        self.run_command('list --all-tenants=1')
        self.assert_called('GET', '/volumes/detail?all_tenants=1')

    def test_list_availability_zone(self):
        self.run_command('availability-zone-list')
        self.assert_called('GET', '/os-availability-zone')

    def test_show(self):
        self.run_command('show 1234')
        self.assert_called('GET', '/volumes/1234')

    def test_delete(self):
        self.run_command('delete 1234')
        self.assert_called('DELETE', '/volumes/1234')

    def test_delete_by_name(self):
        self.run_command('delete sample-volume')
        self.assert_called_anytime('GET', '/volumes/detail?all_tenants=1')
        self.assert_called('DELETE', '/volumes/1234')

    def test_delete_multiple(self):
        self.run_command('delete 1234 5678')
        self.assert_called_anytime('DELETE', '/volumes/1234')
        self.assert_called('DELETE', '/volumes/5678')

    def test_backup(self):
        self.run_command('backup-create 1234')
        self.assert_called('POST', '/backups')

    def test_restore(self):
        self.run_command('backup-restore 1234')
        self.assert_called('POST', '/backups/1234/restore')

    def test_snapshot_list_filter_volume_id(self):
        self.run_command('snapshot-list --volume-id=1234')
        self.assert_called('GET', '/snapshots/detail?volume_id=1234')

    def test_snapshot_list_filter_status_and_volume_id(self):
        self.run_command('snapshot-list --status=available --volume-id=1234')
        self.assert_called('GET', '/snapshots/detail?'
                           'status=available&volume_id=1234')

    def test_rename(self):
        # basic rename with positional arguments
        self.run_command('rename 1234 new-name')
        expected = {'volume': {'display_name': 'new-name'}}
        self.assert_called('PUT', '/volumes/1234', body=expected)
        # change description only
        self.run_command('rename 1234 --display-description=new-description')
        expected = {'volume': {'display_description': 'new-description'}}
        self.assert_called('PUT', '/volumes/1234', body=expected)
        # rename and change description
        self.run_command('rename 1234 new-name '
                         '--display-description=new-description')
        expected = {'volume': {
            'display_name': 'new-name',
            'display_description': 'new-description',
        }}
        self.assert_called('PUT', '/volumes/1234', body=expected)

        # Call rename with no arguments
        self.assertRaises(SystemExit, self.run_command, 'rename')

    def test_rename_snapshot(self):
        # basic rename with positional arguments
        self.run_command('snapshot-rename 1234 new-name')
        expected = {'snapshot': {'display_name': 'new-name'}}
        self.assert_called('PUT', '/snapshots/1234', body=expected)
        # change description only
        self.run_command('snapshot-rename 1234 '
                         '--display-description=new-description')
        expected = {'snapshot': {'display_description': 'new-description'}}
        self.assert_called('PUT', '/snapshots/1234', body=expected)
        # snapshot-rename and change description
        self.run_command('snapshot-rename 1234 new-name '
                         '--display-description=new-description')
        expected = {'snapshot': {
            'display_name': 'new-name',
            'display_description': 'new-description',
        }}
        self.assert_called('PUT', '/snapshots/1234', body=expected)

        # Call snapshot-rename with no arguments
        self.assertRaises(SystemExit, self.run_command, 'snapshot-rename')

    def test_set_metadata_set(self):
        self.run_command('metadata 1234 set key1=val1 key2=val2')
        self.assert_called('POST', '/volumes/1234/metadata',
                           {'metadata': {'key1': 'val1', 'key2': 'val2'}})

    def test_set_metadata_delete_dict(self):
        self.run_command('metadata 1234 unset key1=val1 key2=val2')
        self.assert_called('DELETE', '/volumes/1234/metadata/key1')
        self.assert_called('DELETE', '/volumes/1234/metadata/key2', pos=-2)

    def test_set_metadata_delete_keys(self):
        self.run_command('metadata 1234 unset key1 key2')
        self.assert_called('DELETE', '/volumes/1234/metadata/key1')
        self.assert_called('DELETE', '/volumes/1234/metadata/key2', pos=-2)

    def test_reset_state(self):
        self.run_command('reset-state 1234')
        expected = {'os-reset_status': {'status': 'available'}}
        self.assert_called('POST', '/volumes/1234/action', body=expected)

    def test_reset_state_with_flag(self):
        self.run_command('reset-state --state error 1234')
        expected = {'os-reset_status': {'status': 'error'}}
        self.assert_called('POST', '/volumes/1234/action', body=expected)

    def test_reset_state_multiple(self):
        self.run_command('reset-state 1234 5678 --state error')
        expected = {'os-reset_status': {'status': 'error'}}
        self.assert_called_anytime('POST', '/volumes/1234/action',
                                   body=expected)
        self.assert_called_anytime('POST', '/volumes/5678/action',
                                   body=expected)

    def test_reset_state_two_with_one_nonexistent(self):
        cmd = 'reset-state 1234 123456789'
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)
        expected = {'os-reset_status': {'status': 'available'}}
        self.assert_called_anytime('POST', '/volumes/1234/action',
                                   body=expected)

    def test_reset_state_one_with_one_nonexistent(self):
        cmd = 'reset-state 123456789'
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_snapshot_reset_state(self):
        self.run_command('snapshot-reset-state 1234')
        expected = {'os-reset_status': {'status': 'available'}}
        self.assert_called('POST', '/snapshots/1234/action', body=expected)

    def test_snapshot_reset_state_with_flag(self):
        self.run_command('snapshot-reset-state --state error 1234')
        expected = {'os-reset_status': {'status': 'error'}}
        self.assert_called('POST', '/snapshots/1234/action', body=expected)

    def test_snapshot_reset_state_multiple(self):
        self.run_command('snapshot-reset-state 1234 5678')
        expected = {'os-reset_status': {'status': 'available'}}
        self.assert_called_anytime('POST', '/snapshots/1234/action',
                                   body=expected)
        self.assert_called_anytime('POST', '/snapshots/5678/action',
                                   body=expected)

    def test_encryption_type_list(self):
        """
        Test encryption-type-list shell command.

        Verify a series of GET requests are made:
        - one to get the volume type list information
        - one per volume type to retrieve the encryption type information
        """
        self.run_command('encryption-type-list')
        self.assert_called_anytime('GET', '/types')
        self.assert_called_anytime('GET', '/types/1/encryption')
        self.assert_called_anytime('GET', '/types/2/encryption')

    def test_encryption_type_show(self):
        """
        Test encryption-type-show shell command.

        Verify two GET requests are made per command invocation:
        - one to get the volume type information
        - one to get the encryption type information
        """
        self.run_command('encryption-type-show 1')
        self.assert_called('GET', '/types/1/encryption')
        self.assert_called_anytime('GET', '/types/1')

    def test_encryption_type_create(self):
        """
        Test encryption-type-create shell command.

        Verify GET and POST requests are made per command invocation:
        - one GET request to retrieve the relevant volume type information
        - one POST request to create the new encryption type
        """
        expected = {'encryption': {'cipher': None, 'key_size': None,
                                   'provider': 'TestProvider',
                                   'control_location': 'front-end'}}
        self.run_command('encryption-type-create 2 TestProvider')
        self.assert_called('POST', '/types/2/encryption', body=expected)
        self.assert_called_anytime('GET', '/types/2')

    def test_encryption_type_update(self):
        """
        Test encryption-type-update shell command.

        Verify two GETs/one PUT requests are made per command invocation:
        - one GET request to retrieve the relevant volume type information
        - one GET request to retrieve the relevant encryption type information
        - one PUT request to update the encryption type information
        """
        self.skipTest("Not implemented")

    def test_encryption_type_delete(self):
        """
        Test encryption-type-delete shell command.

        Verify one GET/one DELETE requests are made per command invocation:
        - one GET request to retrieve the relevant volume type information
        - one DELETE request to delete the encryption type information
        """
        self.run_command('encryption-type-delete 1')
        self.assert_called('DELETE', '/types/1/encryption/provider')
        self.assert_called_anytime('GET', '/types/1')

    def test_migrate_volume(self):
        self.run_command('migrate 1234 fakehost --force-host-copy=True')
        expected = {'os-migrate_volume': {'force_host_copy': 'True',
                                          'host': 'fakehost'}}
        self.assert_called('POST', '/volumes/1234/action', body=expected)

    def test_snapshot_metadata_set(self):
        self.run_command('snapshot-metadata 1234 set key1=val1 key2=val2')
        self.assert_called('POST', '/snapshots/1234/metadata',
                           {'metadata': {'key1': 'val1', 'key2': 'val2'}})

    def test_snapshot_metadata_unset_dict(self):
        self.run_command('snapshot-metadata 1234 unset key1=val1 key2=val2')
        self.assert_called_anytime('DELETE', '/snapshots/1234/metadata/key1')
        self.assert_called_anytime('DELETE', '/snapshots/1234/metadata/key2')

    def test_snapshot_metadata_unset_keys(self):
        self.run_command('snapshot-metadata 1234 unset key1 key2')
        self.assert_called_anytime('DELETE', '/snapshots/1234/metadata/key1')
        self.assert_called_anytime('DELETE', '/snapshots/1234/metadata/key2')

    def test_volume_metadata_update_all(self):
        self.run_command('metadata-update-all 1234 key1=val1 key2=val2')
        self.assert_called('PUT', '/volumes/1234/metadata',
                           {'metadata': {'key1': 'val1', 'key2': 'val2'}})

    def test_snapshot_metadata_update_all(self):
        self.run_command('snapshot-metadata-update-all\
                         1234 key1=val1 key2=val2')
        self.assert_called('PUT', '/snapshots/1234/metadata',
                           {'metadata': {'key1': 'val1', 'key2': 'val2'}})

    def test_readonly_mode_update(self):
        self.run_command('readonly-mode-update 1234 True')
        expected = {'os-update_readonly_flag': {'readonly': True}}
        self.assert_called('POST', '/volumes/1234/action', body=expected)

        self.run_command('readonly-mode-update 1234 False')
        expected = {'os-update_readonly_flag': {'readonly': False}}
        self.assert_called('POST', '/volumes/1234/action', body=expected)

    def test_service_disable(self):
        self.run_command('service-disable host cinder-volume')
        self.assert_called('PUT', '/os-services/disable',
                           {"binary": "cinder-volume", "host": "host"})

    def test_services_disable_with_reason(self):
        cmd = 'service-disable host cinder-volume --reason no_reason'
        self.run_command(cmd)
        body = {'host': 'host', 'binary': 'cinder-volume',
                'disabled_reason': 'no_reason'}
        self.assert_called('PUT', '/os-services/disable-log-reason', body)

    def test_service_enable(self):
        self.run_command('service-enable host cinder-volume')
        self.assert_called('PUT', '/os-services/enable',
                           {"binary": "cinder-volume", "host": "host"})

    def test_snapshot_delete(self):
        self.run_command('snapshot-delete 1234')
        self.assert_called('DELETE', '/snapshots/1234')

    def test_quota_delete(self):
        self.run_command('quota-delete 1234')
        self.assert_called('DELETE', '/os-quota-sets/1234')

    def test_snapshot_delete_multiple(self):
        self.run_command('snapshot-delete 1234 5678')
        self.assert_called('DELETE', '/snapshots/5678')
