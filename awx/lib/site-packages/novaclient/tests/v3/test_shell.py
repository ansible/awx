# Copyright 2013 Cloudwatt
# Copyright 2010 Jacob Kaplan-Moss
# Copyright 2011 OpenStack Foundation
# Copyright 2012 IBM Corp.
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

import base64
import os

import fixtures
import mock
import six

from novaclient import exceptions
import novaclient.shell
from novaclient.tests import utils
from novaclient.tests.v3 import fakes


class ShellFixture(fixtures.Fixture):
    def setUp(self):
        super(ShellFixture, self).setUp()
        self.shell = novaclient.shell.OpenStackComputeShell()

    def tearDown(self):
        # For some method like test_image_meta_bad_action we are
        # testing a SystemExit to be thrown and object self.shell has
        # no time to get instantatiated which is OK in this case, so
        # we make sure the method is there before launching it.
        if hasattr(self.shell, 'cs'):
            self.shell.cs.clear_callstack()
        super(ShellFixture, self).tearDown()


class ShellTest(utils.TestCase):
    FAKE_ENV = {
        'NOVA_USERNAME': 'username',
        'NOVA_PASSWORD': 'password',
        'NOVA_PROJECT_ID': 'project_id',
        'OS_COMPUTE_API_VERSION': '3',
        'NOVA_URL': 'http://no.where',
    }

    def setUp(self):
        """Run before each test."""
        super(ShellTest, self).setUp()

        for var in self.FAKE_ENV:
            self.useFixture(fixtures.EnvironmentVariable(var,
                                                         self.FAKE_ENV[var]))
        self.shell = self.useFixture(ShellFixture()).shell

        self.useFixture(fixtures.MonkeyPatch(
            'novaclient.client.get_client_class',
            lambda *_: fakes.FakeClient))

    @mock.patch('sys.stdout', new_callable=six.StringIO)
    def run_command(self, cmd, mock_stdout):
        if isinstance(cmd, list):
            self.shell.main(cmd)
        else:
            self.shell.main(cmd.split())
        return mock_stdout.getvalue()

    def assert_called(self, method, url, body=None, **kwargs):
        return self.shell.cs.assert_called(method, url, body, **kwargs)

    def assert_called_anytime(self, method, url, body=None):
        return self.shell.cs.assert_called_anytime(method, url, body)

    def test_list_deleted(self):
        self.run_command('list --deleted')
        self.assert_called('GET', '/servers/detail?deleted=True')

    def test_aggregate_list(self):
        self.run_command('aggregate-list')
        self.assert_called('GET', '/os-aggregates')

    def test_aggregate_create(self):
        self.run_command('aggregate-create test_name nova1')
        body = {"aggregate": {"name": "test_name",
                              "availability_zone": "nova1"}}
        self.assert_called('POST', '/os-aggregates', body, pos=-2)
        self.assert_called('GET', '/os-aggregates/1', pos=-1)

    def test_aggregate_delete_by_id(self):
        self.run_command('aggregate-delete 1')
        self.assert_called('DELETE', '/os-aggregates/1')

    def test_aggregate_delete_by_name(self):
        self.run_command('aggregate-delete test')
        self.assert_called('DELETE', '/os-aggregates/1')

    def test_aggregate_update_by_id(self):
        self.run_command('aggregate-update 1 new_name')
        body = {"aggregate": {"name": "new_name"}}
        self.assert_called('PUT', '/os-aggregates/1', body, pos=-2)
        self.assert_called('GET', '/os-aggregates/1', pos=-1)

    def test_aggregate_update_by_name(self):
        self.run_command('aggregate-update test new_name')
        body = {"aggregate": {"name": "new_name"}}
        self.assert_called('PUT', '/os-aggregates/1', body, pos=-2)
        self.assert_called('GET', '/os-aggregates/1', pos=-1)

    def test_aggregate_update_with_availability_zone_by_id(self):
        self.run_command('aggregate-update 1 foo new_zone')
        body = {"aggregate": {"name": "foo", "availability_zone": "new_zone"}}
        self.assert_called('PUT', '/os-aggregates/1', body, pos=-2)
        self.assert_called('GET', '/os-aggregates/1', pos=-1)

    def test_aggregate_update_with_availability_zone_by_name(self):
        self.run_command('aggregate-update test foo new_zone')
        body = {"aggregate": {"name": "foo", "availability_zone": "new_zone"}}
        self.assert_called('PUT', '/os-aggregates/1', body, pos=-2)
        self.assert_called('GET', '/os-aggregates/1', pos=-1)

    def test_aggregate_set_metadata_add_by_id(self):
        self.run_command('aggregate-set-metadata 3 foo=bar')
        body = {"set_metadata": {"metadata": {"foo": "bar"}}}
        self.assert_called('POST', '/os-aggregates/3/action', body, pos=-2)
        self.assert_called('GET', '/os-aggregates/3', pos=-1)

    def test_aggregate_set_metadata_add_duplicate_by_id(self):
        cmd = 'aggregate-set-metadata 3 test=dup'
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_aggregate_set_metadata_delete_by_id(self):
        self.run_command('aggregate-set-metadata 3 none_key')
        body = {"set_metadata": {"metadata": {"none_key": None}}}
        self.assert_called('POST', '/os-aggregates/3/action', body, pos=-2)
        self.assert_called('GET', '/os-aggregates/3', pos=-1)

    def test_aggregate_set_metadata_delete_missing_by_id(self):
        cmd = 'aggregate-set-metadata 3 delete_key2'
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_aggregate_set_metadata_by_name(self):
        self.run_command('aggregate-set-metadata test foo=bar')
        body = {"set_metadata": {"metadata": {"foo": "bar"}}}
        self.assert_called('POST', '/os-aggregates/1/action', body, pos=-2)
        self.assert_called('GET', '/os-aggregates/1', pos=-1)

    def test_aggregate_add_host_by_id(self):
        self.run_command('aggregate-add-host 1 host1')
        body = {"add_host": {"host": "host1"}}
        self.assert_called('POST', '/os-aggregates/1/action', body, pos=-2)
        self.assert_called('GET', '/os-aggregates/1', pos=-1)

    def test_aggregate_add_host_by_name(self):
        self.run_command('aggregate-add-host test host1')
        body = {"add_host": {"host": "host1"}}
        self.assert_called('POST', '/os-aggregates/1/action', body, pos=-2)
        self.assert_called('GET', '/os-aggregates/1', pos=-1)

    def test_aggregate_remove_host_by_id(self):
        self.run_command('aggregate-remove-host 1 host1')
        body = {"remove_host": {"host": "host1"}}
        self.assert_called('POST', '/os-aggregates/1/action', body, pos=-2)
        self.assert_called('GET', '/os-aggregates/1', pos=-1)

    def test_aggregate_remove_host_by_name(self):
        self.run_command('aggregate-remove-host test host1')
        body = {"remove_host": {"host": "host1"}}
        self.assert_called('POST', '/os-aggregates/1/action', body, pos=-2)
        self.assert_called('GET', '/os-aggregates/1', pos=-1)

    def test_aggregate_details_by_id(self):
        self.run_command('aggregate-details 1')
        self.assert_called('GET', '/os-aggregates/1')

    def test_aggregate_details_by_name(self):
        self.run_command('aggregate-details test')
        self.assert_called('GET', '/os-aggregates')

    def test_boot(self):
        self.run_command('boot --flavor 1 --image 1 some-server')
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavor_ref': '1',
                'name': 'some-server',
                'image_ref': '1',
                'os-multiple-create:min_count': 1,
                'os-multiple-create:max_count': 1,
            }},
        )

    def test_boot_image_with(self):
        self.run_command("boot --flavor 1"
                         " --image-with test_key=test_value some-server")
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavor_ref': '1',
                'name': 'some-server',
                'image_ref': '1',
                'os-multiple-create:min_count': 1,
                'os-multiple-create:max_count': 1,
            }},
        )

    def test_boot_key(self):
        self.run_command('boot --flavor 1 --image 1 --key_name 1 some-server')
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavor_ref': '1',
                'name': 'some-server',
                'image_ref': '1',
                'key_name': '1',
                'os-multiple-create:min_count': 1,
                'os-multiple-create:max_count': 1,
            }},
        )

    def test_boot_user_data(self):
        file_text = 'text'

        with mock.patch('novaclient.v3.shell.open', create=True) as mock_open:
            mock_open.return_value = file_text
            testfile = 'some_dir/some_file.txt'

            self.run_command('boot --flavor 1 --image 1 --user_data %s '
                             'some-server' % testfile)

            mock_open.assert_called_once_with(testfile)

        user_data = base64.b64encode(file_text.encode('utf-8')).decode('utf-8')
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavor_ref': '1',
                'name': 'some-server',
                'image_ref': '1',
                'os-multiple-create:min_count': 1,
                'os-multiple-create:max_count': 1,
                'user_data': user_data}},
        )

    def test_boot_avzone(self):
        self.run_command(
            'boot --flavor 1 --image 1 --availability-zone avzone  '
            'some-server')
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavor_ref': '1',
                'name': 'some-server',
                'image_ref': '1',
                'os-availability-zone:availability_zone': 'avzone',
                'os-multiple-create:min_count': 1,
                'os-multiple-create:max_count': 1
            }},
        )

    def test_boot_secgroup(self):
        self.run_command(
            'boot --flavor 1 --image 1 --security-groups secgroup1,'
            'secgroup2  some-server')
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'security_groups': [{'name': 'secgroup1'},
                                    {'name': 'secgroup2'}],
                'flavor_ref': '1',
                'name': 'some-server',
                'image_ref': '1',
                'os-multiple-create:min_count': 1,
                'os-multiple-create:max_count': 1,
            }},
        )

    def test_boot_config_drive(self):
        self.run_command(
            'boot --flavor 1 --image 1 --config-drive 1 some-server')
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavor_ref': '1',
                'name': 'some-server',
                'image_ref': '1',
                'os-multiple-create:min_count': 1,
                'os-multiple-create:max_count': 1,
                'os-config-drive:config_drive': True
            }},
        )

    def test_boot_config_drive_custom(self):
        self.run_command(
            'boot --flavor 1 --image 1 --config-drive /dev/hda some-server')
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavor_ref': '1',
                'name': 'some-server',
                'image_ref': '1',
                'os-multiple-create:min_count': 1,
                'os-multiple-create:max_count': 1,
                'os-config-drive:config_drive': '/dev/hda'
            }},
        )

    def test_boot_invalid_user_data(self):
        invalid_file = os.path.join(os.path.dirname(__file__),
                                    'no_such_file')
        cmd = ('boot some-server --flavor 1 --image 1'
               ' --user_data %s' % invalid_file)
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_boot_no_image_no_bdms(self):
        cmd = 'boot --flavor 1 some-server'
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_boot_no_flavor(self):
        cmd = 'boot --image 1 some-server'
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_boot_no_image_bdms(self):
        self.run_command(
            'boot --flavor 1 --block_device_mapping vda=blah:::0 some-server'
        )
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavor_ref': '1',
                'name': 'some-server',
                'block_device_mapping': [
                    {
                        'volume_id': 'blah',
                        'delete_on_termination': '0',
                        'device_name': 'vda',
                        'boot_index': 0,
                        'uuid': 'blah',
                        'source_type': ''
                    }
                ],
                'image_ref': '',
                'os-multiple-create:min_count': 1,
                'os-multiple-create:max_count': 1,
            }},
        )

    def test_boot_image_bdms(self):
        self.run_command(
            'boot --flavor 1 --image 1 --block-device id=fake-id,'
            'source=volume,dest=volume,device=vda,size=1,format=ext4,'
            'type=disk,shutdown=preserve some-server'
        )
        id = ('fake-id,source=volume,dest=volume,device=vda,size=1,'
              'format=ext4,type=disk,shutdown=preserve')
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavor_ref': '1',
                'name': 'some-server',
                'block_device_mapping': [
                    {'device_name': 'id', 'volume_id': id,
                     'source_type': 'volume', 'boot_index': 0, 'uuid': id}],
                'image_ref': '1',
                'os-multiple-create:min_count': 1,
                'os-multiple-create:max_count': 1,
            }},
        )

    def test_boot_metadata(self):
        self.run_command('boot --image 1 --flavor 1 --meta foo=bar=pants'
                         ' --meta spam=eggs some-server ')
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavor_ref': '1',
                'name': 'some-server',
                'image_ref': '1',
                'metadata': {'foo': 'bar=pants', 'spam': 'eggs'},
                'os-multiple-create:min_count': 1,
                'os-multiple-create:max_count': 1,
            }},
        )

    def test_boot_hints(self):
        self.run_command('boot --image 1 --flavor 1 '
                         '--hint a=b1=c1 --hint a2=b2=c2 --hint a=b0=c0 '
                         'some-server')
        self.assert_called_anytime(
            'POST', '/servers',
            {
                'server': {
                    'flavor_ref': '1',
                    'name': 'some-server',
                    'image_ref': '1',
                    'os-multiple-create:min_count': 1,
                    'os-multiple-create:max_count': 1,
                    'os-scheduler-hints:scheduler_hints': {
                        'a': ['b1=c1', 'b0=c0'], 'a2': 'b2=c2'},
                },
            },
        )

    def test_boot_nics(self):
        cmd = ('boot --image 1 --flavor 1 '
               '--nic net-id=a=c,v4-fixed-ip=10.0.0.1 some-server')
        self.run_command(cmd)
        self.assert_called_anytime(
            'POST', '/servers',
            {
                'server': {
                    'flavor_ref': '1',
                    'name': 'some-server',
                    'image_ref': '1',
                    'os-multiple-create:min_count': 1,
                    'os-multiple-create:max_count': 1,
                    'networks': [
                        {'uuid': 'a=c', 'fixed_ip': '10.0.0.1'},
                    ],
                },
            },
        )

    def test_boot_nics_ipv6(self):
        cmd = ('boot --image 1 --flavor 1 '
               '--nic net-id=a=c,v6-fixed-ip=2001:db9:0:1::10 some-server')
        self.run_command(cmd)
        self.assert_called_anytime(
            'POST', '/servers',
            {
                'server': {
                    'flavor_ref': '1',
                    'name': 'some-server',
                    'image_ref': '1',
                    'os-multiple-create:min_count': 1,
                    'os-multiple-create:max_count': 1,
                    'networks': [
                        {'uuid': 'a=c', 'fixed_ip': '2001:db9:0:1::10'},
                    ],
                },
            },
        )

    def test_boot_nics_both_ipv4_and_ipv6(self):
        cmd = ('boot --image 1 --flavor 1 '
               '--nic net-id=a=c,v4-fixed-ip=10.0.0.1,'
               'v6-fixed-ip=2001:db9:0:1::10 some-server')
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_boot_nics_no_value(self):
        cmd = ('boot --image 1 --flavor 1 '
               '--nic net-id some-server')
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_boot_nics_random_key(self):
        cmd = ('boot --image 1 --flavor 1 '
               '--nic net-id=a=c,v4-fixed-ip=10.0.0.1,foo=bar some-server')
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_boot_nics_no_netid_or_portid(self):
        cmd = ('boot --image 1 --flavor 1 '
               '--nic v4-fixed-ip=10.0.0.1 some-server')
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_boot_nics_netid_and_portid(self):
        cmd = ('boot --image 1 --flavor 1 '
               '--nic port-id=some=port,net-id=some=net some-server')
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_boot_num_instances(self):
        self.run_command('boot --image 1 --flavor 1 --num-instances 3 server')
        self.assert_called_anytime(
            'POST', '/servers',
            {
                'server': {
                    'flavor_ref': '1',
                    'name': 'server',
                    'image_ref': '1',
                    'os-multiple-create:min_count': 1,
                    'os-multiple-create:max_count': 3,
                }
            })

    def test_boot_invalid_num_instances(self):
        cmd = 'boot --image 1 --flavor 1 --num-instances 0  server'
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_boot_num_instances_and_count(self):
        cmd = 'boot --image 1 --flavor 1 --num-instances 3 --min-count 3 serv'
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)
        cmd = 'boot --image 1 --flavor 1 --num-instances 3 --max-count 3 serv'
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_boot_min_max_count(self):
        self.run_command('boot --image 1 --flavor 1 --max-count 3 server')
        self.assert_called_anytime(
            'POST', '/servers',
            {
                'server': {
                    'flavor_ref': '1',
                    'name': 'server',
                    'image_ref': '1',
                    'os-multiple-create:min_count': 1,
                    'os-multiple-create:max_count': 3,
                }
            })
        self.run_command('boot --image 1 --flavor 1 --min-count 3 server')
        self.assert_called_anytime(
            'POST', '/servers',
            {
                'server': {
                    'flavor_ref': '1',
                    'name': 'server',
                    'image_ref': '1',
                    'os-multiple-create:min_count': 3,
                    'os-multiple-create:max_count': 3,
                }
            })
        self.run_command('boot --image 1 --flavor 1 '
                         '--min-count 3 --max-count 3 server')
        self.assert_called_anytime(
            'POST', '/servers',
            {
                'server': {
                    'flavor_ref': '1',
                    'name': 'server',
                    'image_ref': '1',
                    'os-multiple-create:min_count': 3,
                    'os-multiple-create:max_count': 3,
                }
            })
        self.run_command('boot --image 1 --flavor 1 '
                         '--min-count 3 --max-count 5 server')
        self.assert_called_anytime(
            'POST', '/servers',
            {
                'server': {
                    'flavor_ref': '1',
                    'name': 'server',
                    'image_ref': '1',
                    'os-multiple-create:min_count': 3,
                    'os-multiple-create:max_count': 5,
                }
            })
        cmd = 'boot --image 1 --flavor 1 --min-count 3 --max-count 1 serv'
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    @mock.patch('novaclient.v3.shell._poll_for_status')
    def test_boot_with_poll(self, poll_method):
        self.run_command('boot --flavor 1 --image 1 some-server --poll')
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavor_ref': '1',
                'name': 'some-server',
                'image_ref': '1',
                'os-multiple-create:min_count': 1,
                'os-multiple-create:max_count': 1,
            }},
        )
        self.assertEqual(1, poll_method.call_count)
        poll_method.assert_has_calls(
            [mock.call(self.shell.cs.servers.get, 1234, 'building',
                       ['active'])])

    def test_boot_with_poll_to_check_VM_state_error(self):
        self.assertRaises(exceptions.InstanceInErrorState, self.run_command,
                          'boot --flavor 1 --image 1 some-bad-server --poll')

    def test_evacuate(self):
        self.run_command('evacuate sample-server new_host')
        self.assert_called('POST', '/servers/1234/action',
                           {'evacuate': {'host': 'new_host',
                                         'on_shared_storage': False}})
        self.run_command('evacuate sample-server new_host '
                         '--password NewAdminPass')
        self.assert_called('POST', '/servers/1234/action',
                           {'evacuate': {'host': 'new_host',
                                         'on_shared_storage': False,
                                         'admin_password': 'NewAdminPass'}})
        self.run_command('evacuate sample-server new_host')
        self.assert_called('POST', '/servers/1234/action',
                           {'evacuate': {'host': 'new_host',
                                         'on_shared_storage': False}})
        self.run_command('evacuate sample-server new_host '
                         '--on-shared-storage')
        self.assert_called('POST', '/servers/1234/action',
                           {'evacuate': {'host': 'new_host',
                                         'on_shared_storage': True}})

    def test_evacuate_with_no_target_host(self):
        self.run_command('evacuate sample-server')
        self.assert_called('POST', '/servers/1234/action',
                           {'evacuate': {'on_shared_storage': False}})
        self.run_command('evacuate sample-server --password NewAdminPass')
        self.assert_called('POST', '/servers/1234/action',
                           {'evacuate': {'on_shared_storage': False,
                                         'admin_password': 'NewAdminPass'}})
        self.run_command('evacuate sample-server --on-shared-storage')
        self.assert_called('POST', '/servers/1234/action',
                           {'evacuate': {'on_shared_storage': True}})

    def test_boot_named_flavor(self):
        self.run_command(["boot", "--image", "1",
                          "--flavor", "512 MB Server",
                          "--max-count", "3", "server"])
        self.assert_called('GET', '/flavors/512 MB Server', pos=0)
        self.assert_called('GET', '/flavors?is_public=None', pos=1)
        self.assert_called('GET', '/flavors?is_public=None', pos=2)
        self.assert_called('GET', '/flavors/2', pos=3)
        self.assert_called(
            'POST', '/servers',
            {
                'server': {
                    'flavor_ref': '2',
                    'name': 'server',
                    'image_ref': '1',
                    'os-multiple-create:min_count': 1,
                    'os-multiple-create:max_count': 3,
                }
            }, pos=4)

    def test_flavor_show_by_name(self):
        self.run_command(['flavor-show', '128 MB Server'])
        self.assert_called('GET', '/flavors/128 MB Server', pos=0)
        self.assert_called('GET', '/flavors?is_public=None', pos=1)
        self.assert_called('GET', '/flavors?is_public=None', pos=2)
        self.assert_called('GET', '/flavors/aa1', pos=3)
        self.assert_called('GET', '/flavors/aa1/flavor-extra-specs', pos=4)

    def test_flavor_show_by_name_priv(self):
        self.run_command(['flavor-show', '512 MB Server'])
        self.assert_called('GET', '/flavors/512 MB Server', pos=0)
        self.assert_called('GET', '/flavors?is_public=None', pos=1)
        self.assert_called('GET', '/flavors?is_public=None', pos=2)
        self.assert_called('GET', '/flavors/2', pos=3)
        self.assert_called('GET', '/flavors/2/flavor-extra-specs', pos=4)

    def test_delete(self):
        self.run_command('delete 1234')
        self.assert_called('DELETE', '/servers/1234')
        self.run_command('delete sample-server')
        self.assert_called('DELETE', '/servers/1234')

    def test_delete_two_with_two_existent(self):
        self.run_command('delete 1234 5678')
        self.assert_called('DELETE', '/servers/1234', pos=-3)
        self.assert_called('DELETE', '/servers/5678', pos=-1)
        self.run_command('delete sample-server sample-server2')
        self.assert_called('GET', '/servers?name=sample-server', pos=-6)
        self.assert_called('GET', '/servers/1234', pos=-5)
        self.assert_called('DELETE', '/servers/1234', pos=-4)
        self.assert_called('GET', '/servers?name=sample-server2', pos=-3)
        self.assert_called('GET', '/servers/5678', pos=-2)
        self.assert_called('DELETE', '/servers/5678', pos=-1)

    def test_delete_two_with_one_nonexistent(self):
        cmd = 'delete 1234 123456789'
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)
        self.assert_called_anytime('DELETE', '/servers/1234')
        cmd = 'delete sample-server nonexistentserver'
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)
        self.assert_called_anytime('DELETE', '/servers/1234')

    def test_delete_one_with_one_nonexistent(self):
        cmd = 'delete 123456789'
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)
        cmd = 'delete nonexistent-server1'
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_delete_two_with_two_nonexistent(self):
        cmd = 'delete 123456789 987654321'
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)
        cmd = 'delete nonexistent-server1 nonexistent-server2'
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)


class GetFirstEndpointTest(utils.TestCase):
    def test_only_one_endpoint(self):
        """If there is only one endpoint, it is returned."""
        endpoint = {"url": "test"}
        result = novaclient.v3.shell._get_first_endpoint([endpoint], "XYZ")
        self.assertEqual(endpoint, result)

    def test_multiple_endpoints(self):
        """If there are multiple endpoints, the first one of the appropriate
        region is returned.

        """
        endpoints = [
            {"region": "XYZ"},
            {"region": "ORD", "number": 1},
            {"region": "ORD", "number": 2}
        ]
        result = novaclient.v3.shell._get_first_endpoint(endpoints, "ORD")
        self.assertEqual(endpoints[1], result)

    def test_multiple_endpoints_but_none_suitable(self):
        """If there are multiple endpoints but none of them are suitable, an
        exception is raised.

        """
        endpoints = [
            {"region": "XYZ"},
            {"region": "PQR"},
            {"region": "STU"}
        ]
        self.assertRaises(LookupError,
                          novaclient.v3.shell._get_first_endpoint,
                          endpoints, "ORD")

    def test_no_endpoints(self):
        """If there are no endpoints available, an exception is raised."""
        self.assertRaises(LookupError,
                          novaclient.v3.shell._get_first_endpoint,
                          [], "ORD")
