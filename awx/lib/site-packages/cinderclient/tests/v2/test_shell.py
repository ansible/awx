# Copyright (c) 2013 OpenStack Foundation
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
from cinderclient.tests import utils
from cinderclient.tests.v2 import fakes
from cinderclient.tests.fixture_data import keystone_client


class ShellTest(utils.TestCase):

    FAKE_ENV = {
        'CINDER_USERNAME': 'username',
        'CINDER_PASSWORD': 'password',
        'CINDER_PROJECT_ID': 'project_id',
        'OS_VOLUME_API_VERSION': '2',
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

    def assert_called(self, method, url, body=None,
                      partial_body=None, **kwargs):
        return self.shell.cs.assert_called(method, url, body,
                                           partial_body, **kwargs)

    def assert_called_anytime(self, method, url, body=None,
                              partial_body=None):
        return self.shell.cs.assert_called_anytime(method, url, body,
                                                   partial_body)

    def test_list(self):
        self.run_command('list')
        # NOTE(jdg): we default to detail currently
        self.assert_called('GET', '/volumes/detail')

    def test_list_filter_status(self):
        self.run_command('list --status=available')
        self.assert_called('GET', '/volumes/detail?status=available')

    def test_list_filter_name(self):
        self.run_command('list --name=1234')
        self.assert_called('GET', '/volumes/detail?name=1234')

    def test_list_all_tenants(self):
        self.run_command('list --all-tenants=1')
        self.assert_called('GET', '/volumes/detail?all_tenants=1')

    def test_list_marker(self):
        self.run_command('list --marker=1234')
        self.assert_called('GET', '/volumes/detail?marker=1234')

    def test_list_limit(self):
        self.run_command('list --limit=10')
        self.assert_called('GET', '/volumes/detail?limit=10')

    def test_list_sort(self):
        self.run_command('list --sort_key=name --sort_dir=asc')
        self.assert_called('GET', '/volumes/detail?sort_dir=asc&sort_key=name')

    def test_list_availability_zone(self):
        self.run_command('availability-zone-list')
        self.assert_called('GET', '/os-availability-zone')

    def test_create_volume_from_snapshot(self):
        expected = {'volume': {'size': None}}

        expected['volume']['snapshot_id'] = '1234'
        self.run_command('create --snapshot-id=1234')
        self.assert_called_anytime('POST', '/volumes', partial_body=expected)
        self.assert_called('GET', '/volumes/1234')

        expected['volume']['size'] = 2
        self.run_command('create --snapshot-id=1234 2')
        self.assert_called_anytime('POST', '/volumes', partial_body=expected)
        self.assert_called('GET', '/volumes/1234')

    def test_create_volume_from_volume(self):
        expected = {'volume': {'size': None}}

        expected['volume']['source_volid'] = '1234'
        self.run_command('create --source-volid=1234')
        self.assert_called_anytime('POST', '/volumes', partial_body=expected)
        self.assert_called('GET', '/volumes/1234')

        expected['volume']['size'] = 2
        self.run_command('create --source-volid=1234 2')
        self.assert_called_anytime('POST', '/volumes', partial_body=expected)
        self.assert_called('GET', '/volumes/1234')

    def test_create_volume_from_replica(self):
        expected = {'volume': {'size': None}}

        expected['volume']['source_replica'] = '1234'
        self.run_command('create --source-replica=1234')
        self.assert_called_anytime('POST', '/volumes', partial_body=expected)
        self.assert_called('GET', '/volumes/1234')

    def test_create_size_required_if_not_snapshot_or_clone(self):
        self.assertRaises(SystemExit, self.run_command, 'create')

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

    def test_record_export(self):
        self.run_command('backup-export 1234')
        self.assert_called('GET', '/backups/1234/export_record')

    def test_record_import(self):
        self.run_command('backup-import fake.driver URL_STRING')
        expected = {'backup-record': {'backup_service': 'fake.driver',
                                      'backup_url': 'URL_STRING'}}
        self.assert_called('POST', '/backups/import_record', expected)

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
        expected = {'volume': {'name': 'new-name'}}
        self.assert_called('PUT', '/volumes/1234', body=expected)
        # change description only
        self.run_command('rename 1234 --description=new-description')
        expected = {'volume': {'description': 'new-description'}}
        self.assert_called('PUT', '/volumes/1234', body=expected)
        # rename and change description
        self.run_command('rename 1234 new-name '
                         '--description=new-description')
        expected = {'volume': {
            'name': 'new-name',
            'description': 'new-description',
        }}
        self.assert_called('PUT', '/volumes/1234', body=expected)

        # Call rename with no arguments
        self.assertRaises(SystemExit, self.run_command, 'rename')

    def test_rename_snapshot(self):
        # basic rename with positional arguments
        self.run_command('snapshot-rename 1234 new-name')
        expected = {'snapshot': {'name': 'new-name'}}
        self.assert_called('PUT', '/snapshots/1234', body=expected)
        # change description only
        self.run_command('snapshot-rename 1234 '
                         '--description=new-description')
        expected = {'snapshot': {'description': 'new-description'}}
        self.assert_called('PUT', '/snapshots/1234', body=expected)
        # snapshot-rename and change description
        self.run_command('snapshot-rename 1234 new-name '
                         '--description=new-description')
        expected = {'snapshot': {
            'name': 'new-name',
            'description': 'new-description',
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
        self.run_command('metadata-update-all 1234  key1=val1 key2=val2')
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

    def test_retype_with_policy(self):
        self.run_command('retype 1234 foo --migration-policy=on-demand')
        expected = {'os-retype': {'new_type': 'foo',
                                  'migration_policy': 'on-demand'}}
        self.assert_called('POST', '/volumes/1234/action', body=expected)

    def test_retype_default_policy(self):
        self.run_command('retype 1234 foo')
        expected = {'os-retype': {'new_type': 'foo',
                                  'migration_policy': 'never'}}
        self.assert_called('POST', '/volumes/1234/action', body=expected)

    def test_snapshot_delete(self):
        self.run_command('snapshot-delete 1234')
        self.assert_called('DELETE', '/snapshots/1234')

    def test_quota_delete(self):
        self.run_command('quota-delete 1234')
        self.assert_called('DELETE', '/os-quota-sets/1234')

    def test_snapshot_delete_multiple(self):
        self.run_command('snapshot-delete 5678')
        self.assert_called('DELETE', '/snapshots/5678')

    def test_volume_manage(self):
        self.run_command('manage host1 key1=val1 key2=val2 '
                         '--name foo --description bar '
                         '--volume-type baz --availability-zone az '
                         '--metadata k1=v1 k2=v2')
        expected = {'volume': {'host': 'host1',
                               'ref': {'key1': 'val1', 'key2': 'val2'},
                               'name': 'foo',
                               'description': 'bar',
                               'volume_type': 'baz',
                               'availability_zone': 'az',
                               'metadata': {'k1': 'v1', 'k2': 'v2'},
                               'bootable': False}}
        self.assert_called_anytime('POST', '/os-volume-manage', body=expected)

    def test_volume_manage_bootable(self):
        """
        Tests the --bootable option

        If this flag is specified, then the resulting POST should contain
        bootable: True.
        """
        self.run_command('manage host1 key1=val1 key2=val2 '
                         '--name foo --description bar --bootable '
                         '--volume-type baz --availability-zone az '
                         '--metadata k1=v1 k2=v2')
        expected = {'volume': {'host': 'host1',
                               'ref': {'key1': 'val1', 'key2': 'val2'},
                               'name': 'foo',
                               'description': 'bar',
                               'volume_type': 'baz',
                               'availability_zone': 'az',
                               'metadata': {'k1': 'v1', 'k2': 'v2'},
                               'bootable': True}}
        self.assert_called_anytime('POST', '/os-volume-manage', body=expected)

    def test_volume_manage_source_name(self):
        """
        Tests the --source-name option.

        Checks that the --source-name option correctly updates the
        ref structure that is passed in the HTTP POST
        """
        self.run_command('manage host1 key1=val1 key2=val2 '
                         '--source-name VolName '
                         '--name foo --description bar '
                         '--volume-type baz --availability-zone az '
                         '--metadata k1=v1 k2=v2')
        expected = {'volume': {'host': 'host1',
                               'ref': {'source-name': 'VolName',
                                       'key1': 'val1', 'key2': 'val2'},
                               'name': 'foo',
                               'description': 'bar',
                               'volume_type': 'baz',
                               'availability_zone': 'az',
                               'metadata': {'k1': 'v1', 'k2': 'v2'},
                               'bootable': False}}
        self.assert_called_anytime('POST', '/os-volume-manage', body=expected)

    def test_volume_manage_source_id(self):
        """
        Tests the --source-id option.

        Checks that the --source-id option correctly updates the
        ref structure that is passed in the HTTP POST
        """
        self.run_command('manage host1 key1=val1 key2=val2 '
                         '--source-id 1234 '
                         '--name foo --description bar '
                         '--volume-type baz --availability-zone az '
                         '--metadata k1=v1 k2=v2')
        expected = {'volume': {'host': 'host1',
                               'ref': {'source-id': '1234',
                                       'key1': 'val1', 'key2': 'val2'},
                               'name': 'foo',
                               'description': 'bar',
                               'volume_type': 'baz',
                               'availability_zone': 'az',
                               'metadata': {'k1': 'v1', 'k2': 'v2'},
                               'bootable': False}}
        self.assert_called_anytime('POST', '/os-volume-manage', body=expected)

    def test_volume_unmanage(self):
        self.run_command('unmanage 1234')
        self.assert_called('POST', '/volumes/1234/action',
                           body={'os-unmanage': None})

    def test_replication_promote(self):
        self.run_command('replication-promote 1234')
        self.assert_called('POST', '/volumes/1234/action',
                           body={'os-promote-replica': None})

    def test_replication_reenable(self):
        self.run_command('replication-reenable 1234')
        self.assert_called('POST', '/volumes/1234/action',
                           body={'os-reenable-replica': None})
