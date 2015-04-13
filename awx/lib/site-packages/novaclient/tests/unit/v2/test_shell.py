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
import datetime
import os

import fixtures
import mock
from oslo.utils import timeutils
import six
from six.moves import builtins

import novaclient.client
from novaclient import exceptions
import novaclient.shell
from novaclient.tests.unit import utils
from novaclient.tests.unit.v2 import fakes
import novaclient.v2.shell


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
        'OS_COMPUTE_API_VERSION': '2',
        'NOVA_URL': 'http://no.where',
        'OS_AUTH_URL': 'http://no.where/v2.0',
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

    def test_agents_list_with_hypervisor(self):
        self.run_command('agent-list --hypervisor xen')
        self.assert_called('GET', '/os-agents?hypervisor=xen')

    def test_agents_create(self):
        self.run_command('agent-create win x86 7.0 '
                         '/xxx/xxx/xxx '
                         'add6bb58e139be103324d04d82d8f546 '
                         'kvm')
        self.assert_called(
            'POST', '/os-agents',
            {'agent': {
                'hypervisor': 'kvm',
                'os': 'win',
                'architecture': 'x86',
                'version': '7.0',
                'url': '/xxx/xxx/xxx',
                'md5hash': 'add6bb58e139be103324d04d82d8f546'}})

    def test_agents_delete(self):
        self.run_command('agent-delete 1')
        self.assert_called('DELETE', '/os-agents/1')

    def test_agents_modify(self):
        self.run_command('agent-modify 1 8.0 /yyy/yyyy/yyyy '
                         'add6bb58e139be103324d04d82d8f546')
        self.assert_called('PUT', '/os-agents/1',
                           {"para": {
                               "url": "/yyy/yyyy/yyyy",
                               "version": "8.0",
                               "md5hash": "add6bb58e139be103324d04d82d8f546"}})

    def test_boot(self):
        self.run_command('boot --flavor 1 --image 1 some-server')
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'imageRef': '1',
                'min_count': 1,
                'max_count': 1,
            }},
        )

    def test_boot_image_with(self):
        self.run_command("boot --flavor 1"
                         " --image-with test_key=test_value some-server")
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'imageRef': '1',
                'min_count': 1,
                'max_count': 1,
            }},
        )

    def test_boot_key(self):
        self.run_command('boot --flavor 1 --image 1 --key_name 1 some-server')
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'imageRef': '1',
                'key_name': '1',
                'min_count': 1,
                'max_count': 1,
            }},
        )

    def test_boot_user_data(self):
        testfile = os.path.join(os.path.dirname(__file__), 'testfile.txt')
        data = open(testfile).read().encode('utf-8')
        expected_file_data = base64.b64encode(data).decode('utf-8')
        self.run_command(
            'boot --flavor 1 --image 1 --user_data %s some-server' % testfile)
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'imageRef': '1',
                'min_count': 1,
                'max_count': 1,
                'user_data': expected_file_data
            }},
        )

    def test_boot_avzone(self):
        self.run_command(
            'boot --flavor 1 --image 1 --availability-zone avzone  '
            'some-server')
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'imageRef': '1',
                'availability_zone': 'avzone',
                'min_count': 1,
                'max_count': 1
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
                'flavorRef': '1',
                'name': 'some-server',
                'imageRef': '1',
                'min_count': 1,
                'max_count': 1,
            }},
        )

    def test_boot_config_drive(self):
        self.run_command(
            'boot --flavor 1 --image 1 --config-drive 1 some-server')
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'imageRef': '1',
                'min_count': 1,
                'max_count': 1,
                'config_drive': True
            }},
        )

    def test_boot_config_drive_custom(self):
        self.run_command(
            'boot --flavor 1 --image 1 --config-drive /dev/hda some-server')
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'imageRef': '1',
                'min_count': 1,
                'max_count': 1,
                'config_drive': '/dev/hda'
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
            'POST', '/os-volumes_boot',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'block_device_mapping': [
                    {
                        'volume_id': 'blah',
                        'delete_on_termination': '0',
                        'device_name': 'vda',
                        'uuid': 'blah',
                        'boot_index': 0,
                        'source_type': ''
                    }
                ],
                'imageRef': '',
                'min_count': 1,
                'max_count': 1,
            }},
        )

    def test_boot_image_bdms_v2(self):
        self.run_command(
            'boot --flavor 1 --image 1 --block-device id=fake-id,'
            'source=volume,dest=volume,device=vda,size=1,format=ext4,'
            'type=disk,shutdown=preserve some-server'
        )
        self.assert_called_anytime(
            'POST', '/os-volumes_boot',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'block_device_mapping_v2': [
                    {
                        'uuid': 'fake-id',
                        'source_type': 'volume',
                        'destination_type': 'volume',
                        'device_name': 'vda',
                        'volume_size': '1',
                        'guest_format': 'ext4',
                        'device_type': 'disk',
                        'delete_on_termination': False,
                    },
                ],
                'imageRef': '1',
                'min_count': 1,
                'max_count': 1,
            }},
        )

    def test_boot_no_image_bdms_v2(self):
        self.run_command(
            'boot --flavor 1 --block-device id=fake-id,source=volume,'
            'dest=volume,bus=virtio,device=vda,size=1,format=ext4,bootindex=0,'
            'type=disk,shutdown=preserve some-server'
        )
        self.assert_called_anytime(
            'POST', '/os-volumes_boot',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'block_device_mapping_v2': [
                    {
                        'uuid': 'fake-id',
                        'source_type': 'volume',
                        'destination_type': 'volume',
                        'disk_bus': 'virtio',
                        'device_name': 'vda',
                        'volume_size': '1',
                        'guest_format': 'ext4',
                        'boot_index': '0',
                        'device_type': 'disk',
                        'delete_on_termination': False,
                    }
                ],
                'imageRef': '',
                'min_count': 1,
                'max_count': 1,
            }},
        )

        cmd = 'boot --flavor 1 --boot-volume fake-id some-server'
        self.run_command(cmd)
        self.assert_called_anytime(
            'POST', '/os-volumes_boot',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'block_device_mapping_v2': [
                    {
                        'uuid': 'fake-id',
                        'source_type': 'volume',
                        'destination_type': 'volume',
                        'boot_index': 0,
                        'delete_on_termination': False,
                    }
                ],
                'imageRef': '',
                'min_count': 1,
                'max_count': 1,
            }},
        )

        cmd = 'boot --flavor 1 --snapshot fake-id some-server'
        self.run_command(cmd)
        self.assert_called_anytime(
            'POST', '/os-volumes_boot',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'block_device_mapping_v2': [
                    {
                        'uuid': 'fake-id',
                        'source_type': 'snapshot',
                        'destination_type': 'volume',
                        'boot_index': 0,
                        'delete_on_termination': False,
                    }
                ],
                'imageRef': '',
                'min_count': 1,
                'max_count': 1,
            }},
        )

        self.run_command('boot --flavor 1 --swap 1 some-server')
        self.assert_called_anytime(
            'POST', '/os-volumes_boot',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'block_device_mapping_v2': [
                    {
                        'source_type': 'blank',
                        'destination_type': 'local',
                        'boot_index': -1,
                        'guest_format': 'swap',
                        'volume_size': '1',
                        'delete_on_termination': True,
                    }
                ],
                'imageRef': '',
                'min_count': 1,
                'max_count': 1,
            }},
        )

        self.run_command(
            'boot --flavor 1 --ephemeral size=1,format=ext4 some-server'
        )
        self.assert_called_anytime(
            'POST', '/os-volumes_boot',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'block_device_mapping_v2': [
                    {
                        'source_type': 'blank',
                        'destination_type': 'local',
                        'boot_index': -1,
                        'guest_format': 'ext4',
                        'volume_size': '1',
                        'delete_on_termination': True,
                    }
                ],
                'imageRef': '',
                'min_count': 1,
                'max_count': 1,
            }},
        )

    def test_boot_metadata(self):
        self.run_command('boot --image 1 --flavor 1 --meta foo=bar=pants'
                         ' --meta spam=eggs some-server ')
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'imageRef': '1',
                'metadata': {'foo': 'bar=pants', 'spam': 'eggs'},
                'min_count': 1,
                'max_count': 1,
            }},
        )

    def test_boot_hints(self):
        self.run_command('boot --image 1 --flavor 1 '
                         '--hint a=b0=c0 --hint a=b1=c1 some-server ')
        self.assert_called_anytime(
            'POST', '/servers',
            {
                'server': {
                    'flavorRef': '1',
                    'name': 'some-server',
                    'imageRef': '1',
                    'min_count': 1,
                    'max_count': 1,
                },
                'os:scheduler_hints': {'a': ['b0=c0', 'b1=c1']},
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
                    'flavorRef': '1',
                    'name': 'some-server',
                    'imageRef': '1',
                    'min_count': 1,
                    'max_count': 1,
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
                    'flavorRef': '1',
                    'name': 'some-server',
                    'imageRef': '1',
                    'min_count': 1,
                    'max_count': 1,
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

    def test_boot_files(self):
        testfile = os.path.join(os.path.dirname(__file__), 'testfile.txt')
        data = open(testfile).read()
        expected = base64.b64encode(data.encode('utf-8')).decode('utf-8')

        cmd = ('boot some-server --flavor 1 --image 1'
               ' --file /tmp/foo=%s --file /tmp/bar=%s')
        self.run_command(cmd % (testfile, testfile))

        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'imageRef': '1',
                'min_count': 1,
                'max_count': 1,
                'personality': [
                    {'path': '/tmp/bar', 'contents': expected},
                    {'path': '/tmp/foo', 'contents': expected},
                ]
            }},
        )

    def test_boot_invalid_files(self):
        invalid_file = os.path.join(os.path.dirname(__file__),
                                    'asdfasdfasdfasdf')
        cmd = ('boot some-server --flavor 1 --image 1'
               ' --file /foo=%s' % invalid_file)
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_boot_num_instances(self):
        self.run_command('boot --image 1 --flavor 1 --num-instances 3 server')
        self.assert_called_anytime(
            'POST', '/servers',
            {
                'server': {
                    'flavorRef': '1',
                    'name': 'server',
                    'imageRef': '1',
                    'min_count': 1,
                    'max_count': 3,
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
                    'flavorRef': '1',
                    'name': 'server',
                    'imageRef': '1',
                    'min_count': 1,
                    'max_count': 3,
                }
            })
        self.run_command('boot --image 1 --flavor 1 --min-count 3 server')
        self.assert_called_anytime(
            'POST', '/servers',
            {
                'server': {
                    'flavorRef': '1',
                    'name': 'server',
                    'imageRef': '1',
                    'min_count': 3,
                    'max_count': 3,
                }
            })
        self.run_command('boot --image 1 --flavor 1 '
                         '--min-count 3 --max-count 3 server')
        self.assert_called_anytime(
            'POST', '/servers',
            {
                'server': {
                    'flavorRef': '1',
                    'name': 'server',
                    'imageRef': '1',
                    'min_count': 3,
                    'max_count': 3,
                }
            })
        self.run_command('boot --image 1 --flavor 1 '
                         '--min-count 3 --max-count 5 server')
        self.assert_called_anytime(
            'POST', '/servers',
            {
                'server': {
                    'flavorRef': '1',
                    'name': 'server',
                    'imageRef': '1',
                    'min_count': 3,
                    'max_count': 5,
                }
            })
        cmd = 'boot --image 1 --flavor 1 --min-count 3 --max-count 1 serv'
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    @mock.patch('novaclient.v2.shell._poll_for_status')
    def test_boot_with_poll(self, poll_method):
        self.run_command('boot --flavor 1 --image 1 some-server --poll')
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'imageRef': '1',
                'min_count': 1,
                'max_count': 1,
            }},
        )
        self.assertEqual(1, poll_method.call_count)
        poll_method.assert_has_calls(
            [mock.call(self.shell.cs.servers.get, 1234, 'building',
                       ['active'])])

    def test_boot_with_poll_to_check_VM_state_error(self):
        self.assertRaises(exceptions.InstanceInErrorState, self.run_command,
                          'boot --flavor 1 --image 1 some-bad-server --poll')

    def test_boot_named_flavor(self):
        self.run_command(["boot", "--image", "1",
                          "--flavor", "512 mb server",
                          "--max-count", "3", "server"])
        self.assert_called('GET', '/images/1', pos=0)
        self.assert_called('GET', '/flavors/512 mb server', pos=1)
        self.assert_called('GET', '/flavors?is_public=None', pos=2)
        self.assert_called('GET', '/flavors/2', pos=3)
        self.assert_called(
            'POST', '/servers',
            {
                'server': {
                    'flavorRef': '2',
                    'name': 'server',
                    'imageRef': '1',
                    'min_count': 1,
                    'max_count': 3,
                }
            }, pos=4)

    def test_flavor_list(self):
        self.run_command('flavor-list')
        self.assert_called_anytime('GET', '/flavors/detail')

    def test_flavor_list_with_extra_specs(self):
        self.run_command('flavor-list --extra-specs')
        self.assert_called('GET', '/flavors/aa1/os-extra_specs')
        self.assert_called_anytime('GET', '/flavors/detail')

    def test_flavor_list_with_all(self):
        self.run_command('flavor-list --all')
        self.assert_called('GET', '/flavors/detail?is_public=None')

    def test_flavor_show(self):
        self.run_command('flavor-show 1')
        self.assert_called_anytime('GET', '/flavors/1')

    def test_flavor_show_with_alphanum_id(self):
        self.run_command('flavor-show aa1')
        self.assert_called_anytime('GET', '/flavors/aa1')

    def test_flavor_show_by_name(self):
        self.run_command(['flavor-show', '128 mb server'])
        self.assert_called('GET', '/flavors/128 mb server', pos=0)
        self.assert_called('GET', '/flavors?is_public=None', pos=1)
        self.assert_called('GET', '/flavors/aa1', pos=2)
        self.assert_called('GET', '/flavors/aa1/os-extra_specs', pos=3)

    def test_flavor_show_by_name_priv(self):
        self.run_command(['flavor-show', '512 mb server'])
        self.assert_called('GET', '/flavors/512 mb server', pos=0)
        self.assert_called('GET', '/flavors?is_public=None', pos=1)
        self.assert_called('GET', '/flavors/2', pos=2)
        self.assert_called('GET', '/flavors/2/os-extra_specs', pos=3)

    def test_flavor_key_set(self):
        self.run_command('flavor-key 1 set k1=v1')
        self.assert_called('POST', '/flavors/1/os-extra_specs',
                           {'extra_specs': {'k1': 'v1'}})

    def test_flavor_key_unset(self):
        self.run_command('flavor-key 1 unset k1')
        self.assert_called('DELETE', '/flavors/1/os-extra_specs/k1')

    def test_flavor_access_list_flavor(self):
        self.run_command('flavor-access-list --flavor 2')
        self.assert_called('GET', '/flavors/2/os-flavor-access')

    # FIXME: flavor-access-list is not implemented yet
    #    def test_flavor_access_list_tenant(self):
    #        self.run_command('flavor-access-list --tenant proj2')
    #        self.assert_called('GET', '/flavors/2/os-flavor-access')

    def test_flavor_access_list_bad_filter(self):
        cmd = 'flavor-access-list --flavor 2 --tenant proj2'
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_flavor_access_list_no_filter(self):
        cmd = 'flavor-access-list'
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_flavor_access_add_by_id(self):
        self.run_command('flavor-access-add 2 proj2')
        self.assert_called('POST', '/flavors/2/action',
                           {'addTenantAccess': {'tenant': 'proj2'}})

    def test_flavor_access_add_by_name(self):
        self.run_command(['flavor-access-add', '512 mb server', 'proj2'])
        self.assert_called('POST', '/flavors/2/action',
                           {'addTenantAccess': {'tenant': 'proj2'}})

    def test_flavor_access_remove_by_id(self):
        self.run_command('flavor-access-remove 2 proj2')
        self.assert_called('POST', '/flavors/2/action',
                           {'removeTenantAccess': {'tenant': 'proj2'}})

    def test_flavor_access_remove_by_name(self):
        self.run_command(['flavor-access-remove', '512 mb server', 'proj2'])
        self.assert_called('POST', '/flavors/2/action',
                           {'removeTenantAccess': {'tenant': 'proj2'}})

    def test_image_show(self):
        self.run_command('image-show 1')
        self.assert_called('GET', '/images/1')

    def test_image_meta_set(self):
        self.run_command('image-meta 1 set test_key=test_value')
        self.assert_called('POST', '/images/1/metadata',
                           {'metadata': {'test_key': 'test_value'}})

    def test_image_meta_del(self):
        self.run_command('image-meta 1 delete test_key=test_value')
        self.assert_called('DELETE', '/images/1/metadata/test_key')

    @mock.patch('sys.stdout', six.StringIO())
    @mock.patch('sys.stderr', six.StringIO())
    def test_image_meta_bad_action(self):
        self.assertRaises(SystemExit, self.run_command,
                          'image-meta 1 BAD_ACTION test_key=test_value')

    def test_image_list(self):
        self.run_command('image-list')
        self.assert_called('GET', '/images/detail')

    def test_create_image(self):
        self.run_command('image-create sample-server mysnapshot')
        self.assert_called(
            'POST', '/servers/1234/action',
            {'createImage': {'name': 'mysnapshot', 'metadata': {}}},
        )

    def test_create_image_show(self):
        output = self.run_command(
            'image-create sample-server mysnapshot --show')
        self.assert_called_anytime(
            'POST', '/servers/1234/action',
            {'createImage': {'name': 'mysnapshot', 'metadata': {}}},
        )
        self.assertIn('My Server Backup', output)
        self.assertIn('SAVING', output)

    def test_image_delete(self):
        self.run_command('image-delete 1')
        self.assert_called('DELETE', '/images/1')

    def test_image_delete_multiple(self):
        self.run_command('image-delete 1 2')
        self.assert_called('DELETE', '/images/1', pos=-3)
        self.assert_called('DELETE', '/images/2', pos=-1)

    def test_list(self):
        self.run_command('list')
        self.assert_called('GET', '/servers/detail')

    def test_list_minimal(self):
        self.run_command('list --minimal')
        self.assert_called('GET', '/servers')

    def test_list_deleted(self):
        self.run_command('list --deleted')
        self.assert_called('GET', '/servers/detail?deleted=True')

    def test_list_with_images(self):
        self.run_command('list --image 1')
        self.assert_called('GET', '/servers/detail?image=1')

    def test_list_with_flavors(self):
        self.run_command('list --flavor 1')
        self.assert_called('GET', '/servers/detail?flavor=1')

    def test_list_by_tenant(self):
        self.run_command('list --tenant fake_tenant')
        self.assert_called(
            'GET',
            '/servers/detail?all_tenants=1&tenant_id=fake_tenant')

    def test_list_by_user(self):
        self.run_command('list --user fake_user')
        self.assert_called(
            'GET',
            '/servers/detail?all_tenants=1&user_id=fake_user')

    def test_list_with_single_sort_key_no_dir(self):
        self.run_command('list --sort 1')
        self.assert_called(
            'GET', ('/servers/detail?sort_dir=desc&sort_key=1'))

    def test_list_with_single_sort_key_and_dir(self):
        self.run_command('list --sort 1:asc')
        self.assert_called(
            'GET', ('/servers/detail?sort_dir=asc&sort_key=1'))

    def test_list_with_sort_keys_no_dir(self):
        self.run_command('list --sort 1,2')
        self.assert_called(
            'GET', ('/servers/detail?sort_dir=desc&sort_dir=desc&'
                    'sort_key=1&sort_key=2'))

    def test_list_with_sort_keys_and_dirs(self):
        self.run_command('list --sort 1:asc,2:desc')
        self.assert_called(
            'GET', ('/servers/detail?sort_dir=asc&sort_dir=desc&'
                    'sort_key=1&sort_key=2'))

    def test_list_with_sort_keys_and_some_dirs(self):
        self.run_command('list --sort 1,2:asc')
        self.assert_called(
            'GET', ('/servers/detail?sort_dir=desc&sort_dir=asc&'
                    'sort_key=1&sort_key=2'))

    def test_list_with_invalid_sort_dir_one(self):
        cmd = 'list --sort 1:foo'
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_list_with_invalid_sort_dir_two(self):
        cmd = 'list --sort 1:asc,2:foo'
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_list_sortby_index_with_sort(self):
        # sortby_index is None if there is sort information
        for cmd in ['list --sort key',
                    'list --sort key:desc',
                    'list --sort key1,key2:asc']:
            with mock.patch('novaclient.utils.print_list') as mock_print_list:
                self.run_command(cmd)
                mock_print_list.assert_called_once_with(
                    mock.ANY, mock.ANY, mock.ANY, sortby_index=None)

    def test_list_sortby_index_without_sort(self):
        # sortby_index is 1 without sort information
        for cmd in ['list', 'list --minimal', 'list --deleted']:
            with mock.patch('novaclient.utils.print_list') as mock_print_list:
                self.run_command(cmd)
                mock_print_list.assert_called_once_with(
                    mock.ANY, mock.ANY, mock.ANY, sortby_index=1)

    def test_list_fields(self):
        output = self.run_command(
            'list --fields '
            'host,security_groups,OS-EXT-MOD:some_thing')
        self.assert_called('GET', '/servers/detail')
        self.assertIn('computenode1', output)
        self.assertIn('securitygroup1', output)
        self.assertIn('OS-EXT-MOD: Some Thing', output)
        self.assertIn('mod_some_thing_value', output)

    def test_reboot(self):
        self.run_command('reboot sample-server')
        self.assert_called('POST', '/servers/1234/action',
                           {'reboot': {'type': 'SOFT'}})
        self.run_command('reboot sample-server --hard')
        self.assert_called('POST', '/servers/1234/action',
                           {'reboot': {'type': 'HARD'}})

    def test_rebuild(self):
        output = self.run_command('rebuild sample-server 1')
        self.assert_called('GET', '/servers?name=sample-server', pos=-6)
        self.assert_called('GET', '/servers/1234', pos=-5)
        self.assert_called('GET', '/images/1', pos=-4)
        self.assert_called('POST', '/servers/1234/action',
                           {'rebuild': {'imageRef': 1}}, pos=-3)
        self.assert_called('GET', '/flavors/1', pos=-2)
        self.assert_called('GET', '/images/2')
        self.assertIn('adminPass', output)

    def test_rebuild_password(self):
        output = self.run_command('rebuild sample-server 1'
                                  ' --rebuild-password asdf')
        self.assert_called('GET', '/servers?name=sample-server', pos=-6)
        self.assert_called('GET', '/servers/1234', pos=-5)
        self.assert_called('GET', '/images/1', pos=-4)
        self.assert_called('POST', '/servers/1234/action',
                           {'rebuild': {'imageRef': 1, 'adminPass': 'asdf'}},
                           pos=-3)
        self.assert_called('GET', '/flavors/1', pos=-2)
        self.assert_called('GET', '/images/2')
        self.assertIn('adminPass', output)

    def test_rebuild_preserve_ephemeral(self):
        self.run_command('rebuild sample-server 1 --preserve-ephemeral')
        self.assert_called('GET', '/servers?name=sample-server', pos=-6)
        self.assert_called('GET', '/servers/1234', pos=-5)
        self.assert_called('GET', '/images/1', pos=-4)
        self.assert_called('POST', '/servers/1234/action',
                           {'rebuild': {'imageRef': 1,
                                        'preserve_ephemeral': True}}, pos=-3)
        self.assert_called('GET', '/flavors/1', pos=-2)
        self.assert_called('GET', '/images/2')

    def test_rebuild_name_meta(self):
        self.run_command('rebuild sample-server 1 --name asdf --meta '
                         'foo=bar')
        self.assert_called('GET', '/servers?name=sample-server', pos=-6)
        self.assert_called('GET', '/servers/1234', pos=-5)
        self.assert_called('GET', '/images/1', pos=-4)
        self.assert_called('POST', '/servers/1234/action',
                           {'rebuild': {'imageRef': 1,
                                        'name': 'asdf',
                                        'metadata': {'foo': 'bar'}}}, pos=-3)
        self.assert_called('GET', '/flavors/1', pos=-2)
        self.assert_called('GET', '/images/2')

    def test_start(self):
        self.run_command('start sample-server')
        self.assert_called('POST', '/servers/1234/action', {'os-start': None})

    def test_stop(self):
        self.run_command('stop sample-server')
        self.assert_called('POST', '/servers/1234/action', {'os-stop': None})

    def test_pause(self):
        self.run_command('pause sample-server')
        self.assert_called('POST', '/servers/1234/action', {'pause': None})

    def test_unpause(self):
        self.run_command('unpause sample-server')
        self.assert_called('POST', '/servers/1234/action', {'unpause': None})

    def test_lock(self):
        self.run_command('lock sample-server')
        self.assert_called('POST', '/servers/1234/action', {'lock': None})

    def test_unlock(self):
        self.run_command('unlock sample-server')
        self.assert_called('POST', '/servers/1234/action', {'unlock': None})

    def test_suspend(self):
        self.run_command('suspend sample-server')
        self.assert_called('POST', '/servers/1234/action', {'suspend': None})

    def test_resume(self):
        self.run_command('resume sample-server')
        self.assert_called('POST', '/servers/1234/action', {'resume': None})

    def test_rescue(self):
        self.run_command('rescue sample-server')
        self.assert_called('POST', '/servers/1234/action', {'rescue': None})

    def test_rescue_password(self):
        self.run_command('rescue sample-server --password asdf')
        self.assert_called('POST', '/servers/1234/action',
                           {'rescue': {'adminPass': 'asdf'}})

    def test_rescue_image(self):
        self.run_command('rescue sample-server --image 1')
        self.assert_called('POST', '/servers/1234/action',
                           {'rescue': {'rescue_image_ref': 1}})

    def test_unrescue(self):
        self.run_command('unrescue sample-server')
        self.assert_called('POST', '/servers/1234/action', {'unrescue': None})

    def test_shelve(self):
        self.run_command('shelve sample-server')
        self.assert_called('POST', '/servers/1234/action', {'shelve': None})

    def test_shelve_offload(self):
        self.run_command('shelve-offload sample-server')
        self.assert_called('POST', '/servers/1234/action',
                           {'shelveOffload': None})

    def test_unshelve(self):
        self.run_command('unshelve sample-server')
        self.assert_called('POST', '/servers/1234/action', {'unshelve': None})

    def test_migrate(self):
        self.run_command('migrate sample-server')
        self.assert_called('POST', '/servers/1234/action', {'migrate': None})

    def test_rename(self):
        self.run_command('rename sample-server newname')
        self.assert_called('PUT', '/servers/1234',
                           {'server': {'name': 'newname'}})

    def test_resize(self):
        self.run_command('resize sample-server 1')
        self.assert_called('POST', '/servers/1234/action',
                           {'resize': {'flavorRef': 1}})

    def test_resize_confirm(self):
        self.run_command('resize-confirm sample-server')
        self.assert_called('POST', '/servers/1234/action',
                           {'confirmResize': None})

    def test_resize_revert(self):
        self.run_command('resize-revert sample-server')
        self.assert_called('POST', '/servers/1234/action',
                           {'revertResize': None})

    @mock.patch('getpass.getpass', mock.Mock(return_value='p'))
    def test_root_password(self):
        self.run_command('root-password sample-server')
        self.assert_called('POST', '/servers/1234/action',
                           {'changePassword': {'adminPass': 'p'}})

    def test_scrub(self):
        self.run_command('scrub 4ffc664c198e435e9853f2538fbcd7a7')
        self.assert_called('GET', '/os-networks', pos=-4)
        self.assert_called('GET', '/os-security-groups?all_tenants=1',
                           pos=-3)
        self.assert_called('POST', '/os-networks/1/action',
                           {"disassociate": None}, pos=-2)
        self.assert_called('DELETE', '/os-security-groups/1')

    def test_show(self):
        self.run_command('show 1234')
        self.assert_called('GET', '/servers/1234', pos=-3)
        self.assert_called('GET', '/flavors/1', pos=-2)
        self.assert_called('GET', '/images/2')

    def test_show_no_image(self):
        self.run_command('show 9012')
        self.assert_called('GET', '/servers/9012', pos=-2)
        self.assert_called('GET', '/flavors/1', pos=-1)

    def test_show_bad_id(self):
        self.assertRaises(exceptions.CommandError,
                          self.run_command, 'show xxx')

    @mock.patch('novaclient.v2.shell.utils.print_dict')
    def test_print_server(self, mock_print_dict):
        self.run_command('show 5678')
        args, kwargs = mock_print_dict.call_args
        parsed_server = args[0]
        self.assertEqual('securitygroup1, securitygroup2',
                         parsed_server['security_groups'])

    def test_delete(self):
        self.run_command('delete 1234')
        self.assert_called('DELETE', '/servers/1234')
        self.run_command('delete sample-server')
        self.assert_called('DELETE', '/servers/1234')

    def test_force_delete(self):
        self.run_command('force-delete 1234')
        self.assert_called('POST', '/servers/1234/action',
                           {'forceDelete': None})
        self.run_command('force-delete sample-server')
        self.assert_called('POST', '/servers/1234/action',
                           {'forceDelete': None})

    def test_restore(self):
        self.run_command('restore 1234')
        self.assert_called('POST', '/servers/1234/action', {'restore': None})
        self.run_command('restore sample-server')
        self.assert_called('POST', '/servers/1234/action', {'restore': None})

    def test_delete_two_with_two_existent(self):
        self.run_command('delete 1234 5678')
        self.assert_called('DELETE', '/servers/1234', pos=-3)
        self.assert_called('DELETE', '/servers/5678', pos=-1)
        self.run_command('delete sample-server sample-server2')
        self.assert_called('GET',
                           '/servers?all_tenants=1&name=sample-server', pos=-6)
        self.assert_called('GET', '/servers/1234', pos=-5)
        self.assert_called('DELETE', '/servers/1234', pos=-4)
        self.assert_called('GET',
                           '/servers?all_tenants=1&name=sample-server2',
                           pos=-3)
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

    def test_diagnostics(self):
        self.run_command('diagnostics 1234')
        self.assert_called('GET', '/servers/1234/diagnostics')
        self.run_command('diagnostics sample-server')
        self.assert_called('GET', '/servers/1234/diagnostics')

    def test_refresh_network(self):
        self.run_command('refresh-network 1234')
        self.assert_called('POST', '/os-server-external-events',
                           {'events': [{'name': 'network-changed',
                                        'server_uuid': 1234}]})

    def test_set_meta_set(self):
        self.run_command('meta 1234 set key1=val1 key2=val2')
        self.assert_called('POST', '/servers/1234/metadata',
                           {'metadata': {'key1': 'val1', 'key2': 'val2'}})

    def test_set_meta_delete_dict(self):
        self.run_command('meta 1234 delete key1=val1 key2=val2')
        self.assert_called('DELETE', '/servers/1234/metadata/key1')
        self.assert_called('DELETE', '/servers/1234/metadata/key2', pos=-2)

    def test_set_meta_delete_keys(self):
        self.run_command('meta 1234 delete key1 key2')
        self.assert_called('DELETE', '/servers/1234/metadata/key1')
        self.assert_called('DELETE', '/servers/1234/metadata/key2', pos=-2)

    def test_set_host_meta(self):
        self.run_command('host-meta hyper set key1=val1 key2=val2')
        self.assert_called('GET', '/os-hypervisors/hyper/servers', pos=0)
        self.assert_called('POST', '/servers/uuid1/metadata',
                           {'metadata': {'key1': 'val1', 'key2': 'val2'}},
                           pos=1)
        self.assert_called('POST', '/servers/uuid2/metadata',
                           {'metadata': {'key1': 'val1', 'key2': 'val2'}},
                           pos=2)
        self.assert_called('POST', '/servers/uuid3/metadata',
                           {'metadata': {'key1': 'val1', 'key2': 'val2'}},
                           pos=3)
        self.assert_called('POST', '/servers/uuid4/metadata',
                           {'metadata': {'key1': 'val1', 'key2': 'val2'}},
                           pos=4)

    def test_set_host_meta_with_no_servers(self):
        self.run_command('host-meta hyper_no_servers set key1=val1 key2=val2')
        self.assert_called('GET', '/os-hypervisors/hyper_no_servers/servers')

    def test_delete_host_meta(self):
        self.run_command('host-meta hyper delete key1')
        self.assert_called('GET', '/os-hypervisors/hyper/servers', pos=0)
        self.assert_called('DELETE', '/servers/uuid1/metadata/key1', pos=1)
        self.assert_called('DELETE', '/servers/uuid2/metadata/key1', pos=2)

    def test_dns_create(self):
        self.run_command('dns-create 192.168.1.1 testname testdomain')
        self.assert_called('PUT',
                           '/os-floating-ip-dns/testdomain/entries/testname')

        self.run_command('dns-create 192.168.1.1 testname testdomain --type A')
        self.assert_called('PUT',
                           '/os-floating-ip-dns/testdomain/entries/testname')

    def test_dns_create_public_domain(self):
        self.run_command('dns-create-public-domain testdomain '
                         '--project test_project')
        self.assert_called('PUT', '/os-floating-ip-dns/testdomain')

    def test_dns_create_private_domain(self):
        self.run_command('dns-create-private-domain testdomain '
                         '--availability-zone av_zone')
        self.assert_called('PUT', '/os-floating-ip-dns/testdomain')

    def test_dns_delete(self):
        self.run_command('dns-delete testdomain testname')
        self.assert_called('DELETE',
                           '/os-floating-ip-dns/testdomain/entries/testname')

    def test_dns_delete_domain(self):
        self.run_command('dns-delete-domain testdomain')
        self.assert_called('DELETE', '/os-floating-ip-dns/testdomain')

    def test_dns_list(self):
        self.run_command('dns-list testdomain --ip 192.168.1.1')
        self.assert_called('GET',
                           '/os-floating-ip-dns/testdomain/entries?'
                           'ip=192.168.1.1')

        self.run_command('dns-list testdomain --name testname')
        self.assert_called('GET',
                           '/os-floating-ip-dns/testdomain/entries/testname')

    def test_dns_domains(self):
        self.run_command('dns-domains')
        self.assert_called('GET', '/os-floating-ip-dns')

    def test_floating_ip_list(self):
        self.run_command('floating-ip-list')
        self.assert_called('GET', '/os-floating-ips')

    def test_floating_ip_list_all_tenants(self):
        self.run_command('floating-ip-list --all-tenants')
        self.assert_called('GET', '/os-floating-ips?all_tenants=1')

    def test_floating_ip_create(self):
        self.run_command('floating-ip-create')
        self.assert_called('GET', '/os-floating-ips/1')

    def test_floating_ip_delete(self):
        self.run_command('floating-ip-delete 11.0.0.1')
        self.assert_called('DELETE', '/os-floating-ips/1')

    def test_floating_ip_bulk_list(self):
        self.run_command('floating-ip-bulk-list')
        self.assert_called('GET', '/os-floating-ips-bulk')

    def test_floating_ip_bulk_create(self):
        self.run_command('floating-ip-bulk-create 10.0.0.1/24')
        self.assert_called('POST', '/os-floating-ips-bulk',
                           {'floating_ips_bulk_create':
                               {'ip_range': '10.0.0.1/24'}})

    def test_floating_ip_bulk_create_host_and_interface(self):
        self.run_command('floating-ip-bulk-create 10.0.0.1/24 --pool testPool'
                         ' --interface ethX')
        self.assert_called('POST', '/os-floating-ips-bulk',
                           {'floating_ips_bulk_create':
                               {'ip_range': '10.0.0.1/24',
                                'pool': 'testPool',
                                'interface': 'ethX'}})

    def test_floating_ip_bulk_delete(self):
        self.run_command('floating-ip-bulk-delete 10.0.0.1/24')
        self.assert_called('PUT', '/os-floating-ips-bulk/delete',
                           {'ip_range': '10.0.0.1/24'})

    def test_server_floating_ip_add(self):
        self.run_command('add-floating-ip sample-server 11.0.0.1')
        self.assert_called('POST', '/servers/1234/action',
                           {'addFloatingIp': {'address': '11.0.0.1'}})

    def test_server_floating_ip_remove(self):
        self.run_command('remove-floating-ip sample-server 11.0.0.1')
        self.assert_called('POST', '/servers/1234/action',
                           {'removeFloatingIp': {'address': '11.0.0.1'}})

    def test_server_floating_ip_associate(self):
        self.run_command('floating-ip-associate sample-server 11.0.0.1')
        self.assert_called('POST', '/servers/1234/action',
                           {'addFloatingIp': {'address': '11.0.0.1'}})

    def test_server_floating_ip_disassociate(self):
        self.run_command('floating-ip-disassociate sample-server 11.0.0.1')
        self.assert_called('POST', '/servers/1234/action',
                           {'removeFloatingIp': {'address': '11.0.0.1'}})

    def test_usage_list(self):
        self.run_command('usage-list --start 2000-01-20 --end 2005-02-01')
        self.assert_called('GET',
                           '/os-simple-tenant-usage?' +
                           'start=2000-01-20T00:00:00&' +
                           'end=2005-02-01T00:00:00&' +
                           'detailed=1')

    def test_usage_list_no_args(self):
        timeutils.set_time_override(datetime.datetime(2005, 2, 1, 0, 0))
        self.addCleanup(timeutils.clear_time_override)
        self.run_command('usage-list')
        self.assert_called('GET',
                           '/os-simple-tenant-usage?' +
                           'start=2005-01-04T00:00:00&' +
                           'end=2005-02-02T00:00:00&' +
                           'detailed=1')

    def test_usage(self):
        self.run_command('usage --start 2000-01-20 --end 2005-02-01 '
                         '--tenant test')
        self.assert_called('GET',
                           '/os-simple-tenant-usage/test?' +
                           'start=2000-01-20T00:00:00&' +
                           'end=2005-02-01T00:00:00')

    def test_usage_no_tenant(self):
        self.run_command('usage --start 2000-01-20 --end 2005-02-01')
        self.assert_called('GET',
                           '/os-simple-tenant-usage/tenant_id?' +
                           'start=2000-01-20T00:00:00&' +
                           'end=2005-02-01T00:00:00')

    def test_flavor_delete(self):
        self.run_command("flavor-delete 2")
        self.assert_called('DELETE', '/flavors/2')

    def test_flavor_create(self):
        self.run_command("flavor-create flavorcreate "
                         "1234 512 10 1 --swap 1024 --ephemeral 10 "
                         "--is-public true")
        self.assert_called('POST', '/flavors', pos=-2)
        self.assert_called('GET', '/flavors/1', pos=-1)

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

    def test_live_migration(self):
        self.run_command('live-migration sample-server hostname')
        self.assert_called('POST', '/servers/1234/action',
                           {'os-migrateLive': {'host': 'hostname',
                                               'block_migration': False,
                                               'disk_over_commit': False}})
        self.run_command('live-migration sample-server hostname'
                         ' --block-migrate')
        self.assert_called('POST', '/servers/1234/action',
                           {'os-migrateLive': {'host': 'hostname',
                                               'block_migration': True,
                                               'disk_over_commit': False}})
        self.run_command('live-migration sample-server hostname'
                         ' --block-migrate --disk-over-commit')
        self.assert_called('POST', '/servers/1234/action',
                           {'os-migrateLive': {'host': 'hostname',
                                               'block_migration': True,
                                               'disk_over_commit': True}})

    def test_host_evacuate_live_with_no_target_host(self):
        self.run_command('host-evacuate-live hyper')
        self.assert_called('GET', '/os-hypervisors/hyper/servers', pos=0)
        body = {'os-migrateLive': {'host': None,
                                   'block_migration': False,
                                   'disk_over_commit': False}}
        self.assert_called('POST', '/servers/uuid1/action', body, pos=1)
        self.assert_called('POST', '/servers/uuid2/action', body, pos=2)
        self.assert_called('POST', '/servers/uuid3/action', body, pos=3)
        self.assert_called('POST', '/servers/uuid4/action', body, pos=4)

    def test_host_evacuate_live_with_target_host(self):
        self.run_command('host-evacuate-live hyper '
                         '--target-host hostname')
        self.assert_called('GET', '/os-hypervisors/hyper/servers', pos=0)
        body = {'os-migrateLive': {'host': 'hostname',
                                   'block_migration': False,
                                   'disk_over_commit': False}}
        self.assert_called('POST', '/servers/uuid1/action', body, pos=1)
        self.assert_called('POST', '/servers/uuid2/action', body, pos=2)
        self.assert_called('POST', '/servers/uuid3/action', body, pos=3)
        self.assert_called('POST', '/servers/uuid4/action', body, pos=4)

    def test_host_evacuate_live_with_block_migration(self):
        self.run_command('host-evacuate-live --block-migrate hyper')
        self.assert_called('GET', '/os-hypervisors/hyper/servers', pos=0)
        body = {'os-migrateLive': {'host': None,
                                   'block_migration': True,
                                   'disk_over_commit': False}}
        self.assert_called('POST', '/servers/uuid1/action', body, pos=1)
        self.assert_called('POST', '/servers/uuid2/action', body, pos=2)
        self.assert_called('POST', '/servers/uuid3/action', body, pos=3)
        self.assert_called('POST', '/servers/uuid4/action', body, pos=4)

    def test_host_evacuate_live_with_disk_over_commit(self):
        self.run_command('host-evacuate-live --disk-over-commit hyper')
        self.assert_called('GET', '/os-hypervisors/hyper/servers', pos=0)
        body = {'os-migrateLive': {'host': None,
                                   'block_migration': False,
                                   'disk_over_commit': True}}
        self.assert_called('POST', '/servers/uuid1/action', body, pos=1)
        self.assert_called('POST', '/servers/uuid2/action', body, pos=2)
        self.assert_called('POST', '/servers/uuid3/action', body, pos=3)
        self.assert_called('POST', '/servers/uuid4/action', body, pos=4)

    def test_reset_state(self):
        self.run_command('reset-state sample-server')
        self.assert_called('POST', '/servers/1234/action',
                           {'os-resetState': {'state': 'error'}})
        self.run_command('reset-state sample-server --active')
        self.assert_called('POST', '/servers/1234/action',
                           {'os-resetState': {'state': 'active'}})

    def test_reset_state_multiple(self):
        self.run_command('reset-state sample-server sample-server2')
        self.assert_called('POST', '/servers/1234/action',
                           {'os-resetState': {'state': 'error'}}, pos=-4)
        self.assert_called('POST', '/servers/5678/action',
                           {'os-resetState': {'state': 'error'}}, pos=-1)

    def test_reset_state_active_multiple(self):
        self.run_command('reset-state --active sample-server sample-server2')
        self.assert_called('POST', '/servers/1234/action',
                           {'os-resetState': {'state': 'active'}}, pos=-4)
        self.assert_called('POST', '/servers/5678/action',
                           {'os-resetState': {'state': 'active'}}, pos=-1)

    def test_reset_network(self):
        self.run_command('reset-network sample-server')
        self.assert_called('POST', '/servers/1234/action',
                           {'resetNetwork': None})

    def test_services_list(self):
        self.run_command('service-list')
        self.assert_called('GET', '/os-services')

    def test_services_list_with_host(self):
        self.run_command('service-list --host host1')
        self.assert_called('GET', '/os-services?host=host1')

    def test_services_list_with_binary(self):
        self.run_command('service-list --binary nova-cert')
        self.assert_called('GET', '/os-services?binary=nova-cert')

    def test_services_list_with_host_binary(self):
        self.run_command('service-list --host host1 --binary nova-cert')
        self.assert_called('GET', '/os-services?host=host1&binary=nova-cert')

    def test_services_enable(self):
        self.run_command('service-enable host1 nova-cert')
        body = {'host': 'host1', 'binary': 'nova-cert'}
        self.assert_called('PUT', '/os-services/enable', body)

    def test_services_disable(self):
        self.run_command('service-disable host1 nova-cert')
        body = {'host': 'host1', 'binary': 'nova-cert'}
        self.assert_called('PUT', '/os-services/disable', body)

    def test_services_disable_with_reason(self):
        self.run_command('service-disable host1 nova-cert --reason no_reason')
        body = {'host': 'host1', 'binary': 'nova-cert',
                'disabled_reason': 'no_reason'}
        self.assert_called('PUT', '/os-services/disable-log-reason', body)

    def test_services_delete(self):
        self.run_command('service-delete 1')
        self.assert_called('DELETE', '/os-services/1')

    def test_fixed_ips_get(self):
        self.run_command('fixed-ip-get 192.168.1.1')
        self.assert_called('GET', '/os-fixed-ips/192.168.1.1')

    def test_fixed_ips_reserve(self):
        self.run_command('fixed-ip-reserve 192.168.1.1')
        body = {'reserve': None}
        self.assert_called('POST', '/os-fixed-ips/192.168.1.1/action', body)

    def test_fixed_ips_unreserve(self):
        self.run_command('fixed-ip-unreserve 192.168.1.1')
        body = {'unreserve': None}
        self.assert_called('POST', '/os-fixed-ips/192.168.1.1/action', body)

    def test_host_list(self):
        self.run_command('host-list')
        self.assert_called('GET', '/os-hosts')

    def test_host_list_with_zone(self):
        self.run_command('host-list --zone nova')
        self.assert_called('GET', '/os-hosts?zone=nova')

    def test_host_update_status(self):
        self.run_command('host-update sample-host_1 --status enabled')
        body = {'status': 'enabled'}
        self.assert_called('PUT', '/os-hosts/sample-host_1', body)

    def test_host_update_maintenance(self):
        self.run_command('host-update sample-host_2 --maintenance enable')
        body = {'maintenance_mode': 'enable'}
        self.assert_called('PUT', '/os-hosts/sample-host_2', body)

    def test_host_update_multiple_settings(self):
        self.run_command('host-update sample-host_3 '
                         '--status disabled --maintenance enable')
        body = {'status': 'disabled', 'maintenance_mode': 'enable'}
        self.assert_called('PUT', '/os-hosts/sample-host_3', body)

    def test_host_startup(self):
        self.run_command('host-action sample-host --action startup')
        self.assert_called(
            'GET', '/os-hosts/sample-host/startup')

    def test_host_shutdown(self):
        self.run_command('host-action sample-host --action shutdown')
        self.assert_called(
            'GET', '/os-hosts/sample-host/shutdown')

    def test_host_reboot(self):
        self.run_command('host-action sample-host --action reboot')
        self.assert_called(
            'GET', '/os-hosts/sample-host/reboot')

    def test_host_evacuate(self):
        self.run_command('host-evacuate hyper --target target_hyper')
        self.assert_called('GET', '/os-hypervisors/hyper/servers', pos=0)
        self.assert_called('POST', '/servers/uuid1/action',
                           {'evacuate': {'host': 'target_hyper',
                                         'onSharedStorage': False}}, pos=1)
        self.assert_called('POST', '/servers/uuid2/action',
                           {'evacuate': {'host': 'target_hyper',
                                         'onSharedStorage': False}}, pos=2)
        self.assert_called('POST', '/servers/uuid3/action',
                           {'evacuate': {'host': 'target_hyper',
                                         'onSharedStorage': False}}, pos=3)
        self.assert_called('POST', '/servers/uuid4/action',
                           {'evacuate': {'host': 'target_hyper',
                                         'onSharedStorage': False}}, pos=4)

    def test_host_evacuate_with_shared_storage(self):
        self.run_command(
            'host-evacuate --on-shared-storage hyper --target target_hyper')
        self.assert_called('GET', '/os-hypervisors/hyper/servers', pos=0)
        self.assert_called('POST', '/servers/uuid1/action',
                           {'evacuate': {'host': 'target_hyper',
                                         'onSharedStorage': True}}, pos=1)
        self.assert_called('POST', '/servers/uuid2/action',
                           {'evacuate': {'host': 'target_hyper',
                                         'onSharedStorage': True}}, pos=2)
        self.assert_called('POST', '/servers/uuid3/action',
                           {'evacuate': {'host': 'target_hyper',
                                         'onSharedStorage': True}}, pos=3)
        self.assert_called('POST', '/servers/uuid4/action',
                           {'evacuate': {'host': 'target_hyper',
                                         'onSharedStorage': True}}, pos=4)

    def test_host_evacuate_with_no_target_host(self):
        self.run_command('host-evacuate --on-shared-storage hyper')
        self.assert_called('GET', '/os-hypervisors/hyper/servers', pos=0)
        self.assert_called('POST', '/servers/uuid1/action',
                           {'evacuate': {'onSharedStorage': True}}, pos=1)
        self.assert_called('POST', '/servers/uuid2/action',
                           {'evacuate': {'onSharedStorage': True}}, pos=2)
        self.assert_called('POST', '/servers/uuid3/action',
                           {'evacuate': {'onSharedStorage': True}}, pos=3)
        self.assert_called('POST', '/servers/uuid4/action',
                           {'evacuate': {'onSharedStorage': True}}, pos=4)

    def test_host_servers_migrate(self):
        self.run_command('host-servers-migrate hyper')
        self.assert_called('GET', '/os-hypervisors/hyper/servers', pos=0)
        self.assert_called('POST',
                           '/servers/uuid1/action', {'migrate': None}, pos=1)
        self.assert_called('POST',
                           '/servers/uuid2/action', {'migrate': None}, pos=2)
        self.assert_called('POST',
                           '/servers/uuid3/action', {'migrate': None}, pos=3)
        self.assert_called('POST',
                           '/servers/uuid4/action', {'migrate': None}, pos=4)

    def test_hypervisor_list(self):
        self.run_command('hypervisor-list')
        self.assert_called('GET', '/os-hypervisors')

    def test_hypervisor_list_matching(self):
        self.run_command('hypervisor-list --matching hyper')
        self.assert_called('GET', '/os-hypervisors/hyper/search')

    def test_hypervisor_servers(self):
        self.run_command('hypervisor-servers hyper')
        self.assert_called('GET', '/os-hypervisors/hyper/servers')

    def test_hypervisor_show_by_id(self):
        self.run_command('hypervisor-show 1234')
        self.assert_called('GET', '/os-hypervisors/1234')

    def test_hypervisor_show_by_name(self):
        self.run_command('hypervisor-show hyper1')
        self.assert_called('GET', '/os-hypervisors/detail')

    def test_hypervisor_uptime_by_id(self):
        self.run_command('hypervisor-uptime 1234')
        self.assert_called('GET', '/os-hypervisors/1234/uptime')

    def test_hypervisor_uptime_by_name(self):
        self.run_command('hypervisor-uptime hyper1')
        self.assert_called('GET', '/os-hypervisors/1234/uptime')

    def test_hypervisor_stats(self):
        self.run_command('hypervisor-stats')
        self.assert_called('GET', '/os-hypervisors/statistics')

    def test_quota_show(self):
        self.run_command(
            'quota-show --tenant '
            '97f4c221bff44578b0300df4ef119353')
        self.assert_called(
            'GET',
            '/os-quota-sets/97f4c221bff44578b0300df4ef119353')

    def test_user_quota_show(self):
        self.run_command(
            'quota-show --tenant '
            '97f4c221bff44578b0300df4ef119353 --user u1')
        self.assert_called(
            'GET',
            '/os-quota-sets/97f4c221bff44578b0300df4ef119353?user_id=u1')

    def test_quota_show_no_tenant(self):
        self.run_command('quota-show')
        self.assert_called('GET', '/os-quota-sets/tenant_id')

    def test_quota_defaults(self):
        self.run_command(
            'quota-defaults --tenant '
            '97f4c221bff44578b0300df4ef119353')
        self.assert_called(
            'GET',
            '/os-quota-sets/97f4c221bff44578b0300df4ef119353/defaults')

    def test_quota_defaults_no_tenant(self):
        self.run_command('quota-defaults')
        self.assert_called('GET', '/os-quota-sets/tenant_id/defaults')

    def test_quota_update(self):
        self.run_command(
            'quota-update 97f4c221bff44578b0300df4ef119353'
            ' --instances=5')
        self.assert_called(
            'PUT',
            '/os-quota-sets/97f4c221bff44578b0300df4ef119353',
            {'quota_set': {'instances': 5,
                           'tenant_id': '97f4c221bff44578b0300df4ef119353'}})

    def test_user_quota_update(self):
        self.run_command(
            'quota-update 97f4c221bff44578b0300df4ef119353'
            ' --user=u1'
            ' --instances=5')
        self.assert_called(
            'PUT',
            '/os-quota-sets/97f4c221bff44578b0300df4ef119353?user_id=u1',
            {'quota_set': {'instances': 5,
                           'tenant_id': '97f4c221bff44578b0300df4ef119353'}})

    def test_quota_force_update(self):
        self.run_command(
            'quota-update 97f4c221bff44578b0300df4ef119353'
            ' --instances=5 --force')
        self.assert_called(
            'PUT', '/os-quota-sets/97f4c221bff44578b0300df4ef119353',
            {'quota_set': {'force': True,
                           'instances': 5,
                           'tenant_id': '97f4c221bff44578b0300df4ef119353'}})

    def test_quota_update_fixed_ip(self):
        self.run_command(
            'quota-update 97f4c221bff44578b0300df4ef119353'
            ' --fixed-ips=5')
        self.assert_called(
            'PUT', '/os-quota-sets/97f4c221bff44578b0300df4ef119353',
            {'quota_set': {'fixed_ips': 5,
                           'tenant_id': '97f4c221bff44578b0300df4ef119353'}})

    def test_quota_delete(self):
        self.run_command('quota-delete --tenant '
                         '97f4c221bff44578b0300df4ef119353')
        self.assert_called('DELETE',
                           '/os-quota-sets/97f4c221bff44578b0300df4ef119353')

    def test_user_quota_delete(self):
        self.run_command('quota-delete --tenant '
                         '97f4c221bff44578b0300df4ef119353 '
                         '--user u1')
        self.assert_called(
            'DELETE',
            '/os-quota-sets/97f4c221bff44578b0300df4ef119353?user_id=u1')

    def test_quota_class_show(self):
        self.run_command('quota-class-show test')
        self.assert_called('GET', '/os-quota-class-sets/test')

    def test_quota_class_update(self):
        # The list of args we can update.
        args = (
            '--instances', '--cores', '--ram', '--floating-ips', '--fixed-ips',
            '--metadata-items', '--injected-files',
            '--injected-file-content-bytes', '--injected-file-path-bytes',
            '--key-pairs', '--security-groups', '--security-group-rules',
            '--server-groups', '--server-group-members'
        )
        for arg in args:
            self.run_command('quota-class-update '
                             '97f4c221bff44578b0300df4ef119353 '
                             '%s=5' % arg)
            request_param = arg[2:].replace('-', '_')
            body = {'quota_class_set': {request_param: 5}}
            self.assert_called(
                'PUT', '/os-quota-class-sets/97f4c221bff44578b0300df4ef119353',
                body)

    def test_network_list(self):
        self.run_command('network-list')
        self.assert_called('GET', '/os-networks')

    def test_network_list_fields(self):
        output = self.run_command(
            'network-list --fields '
            'vlan,project_id')
        self.assert_called('GET', '/os-networks')
        self.assertIn('1234', output)
        self.assertIn('4ffc664c198e435e9853f2538fbcd7a7', output)

    def test_network_show(self):
        self.run_command('network-show 1')
        self.assert_called('GET', '/os-networks/1')

    def test_cloudpipe_list(self):
        self.run_command('cloudpipe-list')
        self.assert_called('GET', '/os-cloudpipe')

    def test_cloudpipe_create(self):
        self.run_command('cloudpipe-create myproject')
        body = {'cloudpipe': {'project_id': "myproject"}}
        self.assert_called('POST', '/os-cloudpipe', body)

    def test_cloudpipe_configure(self):
        self.run_command('cloudpipe-configure 192.168.1.1 1234')
        body = {'configure_project': {'vpn_ip': "192.168.1.1",
                                      'vpn_port': '1234'}}
        self.assert_called('PUT', '/os-cloudpipe/configure-project', body)

    def test_network_associate_host(self):
        self.run_command('network-associate-host 1 testHost')
        body = {'associate_host': 'testHost'}
        self.assert_called('POST', '/os-networks/1/action', body)

    def test_network_associate_project(self):
        self.run_command('network-associate-project 1')
        body = {'id': "1"}
        self.assert_called('POST', '/os-networks/add', body)

    def test_network_disassociate_host(self):
        self.run_command('network-disassociate --host-only 1 2')
        body = {'disassociate_host': None}
        self.assert_called('POST', '/os-networks/2/action', body)

    def test_network_disassociate_project(self):
        self.run_command('network-disassociate --project-only 1 2')
        body = {'disassociate_project': None}
        self.assert_called('POST', '/os-networks/2/action', body)

    def test_network_create_v4(self):
        self.run_command('network-create --fixed-range-v4 10.0.1.0/24'
                         ' --dns1 10.0.1.254 new_network')
        body = {'network': {'cidr': '10.0.1.0/24', 'label': 'new_network',
                            'dns1': '10.0.1.254'}}
        self.assert_called('POST', '/os-networks', body)

    def test_network_create_v6(self):
        self.run_command('network-create --fixed-range-v6 2001::/64'
                         ' new_network')
        body = {'network': {'cidr_v6': '2001::/64', 'label': 'new_network'}}
        self.assert_called('POST', '/os-networks', body)

    def test_network_create_invalid(self):
        cmd = 'network-create 10.0.1.0'
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_network_create_multi_host(self):
        self.run_command('network-create --fixed-range-v4 192.168.0.0/24'
                         ' --multi-host=T new_network')
        body = {'network': {'cidr': '192.168.0.0/24', 'label': 'new_network',
                            'multi_host': True}}
        self.assert_called('POST', '/os-networks', body)

        self.run_command('network-create --fixed-range-v4 192.168.0.0/24'
                         ' --multi-host=True new_network')
        body = {'network': {'cidr': '192.168.0.0/24', 'label': 'new_network',
                            'multi_host': True}}
        self.assert_called('POST', '/os-networks', body)

        self.run_command('network-create --fixed-range-v4 192.168.0.0/24'
                         ' --multi-host=1 new_network')
        body = {'network': {'cidr': '192.168.0.0/24', 'label': 'new_network',
                            'multi_host': True}}
        self.assert_called('POST', '/os-networks', body)

        self.run_command('network-create --fixed-range-v4 192.168.1.0/24'
                         ' --multi-host=F new_network')
        body = {'network': {'cidr': '192.168.1.0/24', 'label': 'new_network',
                            'multi_host': False}}
        self.assert_called('POST', '/os-networks', body)

    def test_network_create_vlan(self):
        self.run_command('network-create --fixed-range-v4 192.168.0.0/24'
                         ' --vlan=200 new_network')
        body = {'network': {'cidr': '192.168.0.0/24', 'label': 'new_network',
                            'vlan': 200}}
        self.assert_called('POST', '/os-networks', body)

    def test_network_create_vlan_start(self):
        self.run_command('network-create --fixed-range-v4 192.168.0.0/24'
                         ' --vlan-start=100 new_network')
        body = {'network': {'cidr': '192.168.0.0/24', 'label': 'new_network',
                            'vlan_start': 100}}
        self.assert_called('POST', '/os-networks', body)

    def test_network_create_extra_args(self):
        self.run_command('network-create --fixed-range-v4 192.168.0.0/24'
                         ' --enable-dhcp F --dhcp-server 192.168.0.2'
                         ' --share-address T --allowed-start 192.168.0.10'
                         ' --allowed-end 192.168.0.20 --mtu 9000 new_network')
        body = {'network': {'cidr': '192.168.0.0/24', 'label': 'new_network',
                            'enable_dhcp': False, 'dhcp_server': '192.168.0.2',
                            'share_address': True, 'mtu': 9000,
                            'allowed_start': '192.168.0.10',
                            'allowed_end': '192.168.0.20'}}
        self.assert_called('POST', '/os-networks', body)

    def test_network_delete(self):
        self.run_command('network-delete 1')
        self.assert_called('DELETE', '/os-networks/1')

    def test_tenant_network_list(self):
        self.run_command('tenant-network-list')
        self.assert_called('GET', '/os-tenant-networks')

    def test_tenant_network_show(self):
        self.run_command('tenant-network-show 1')
        self.assert_called('GET', '/os-tenant-networks/1')

    def test_tenant_network_create(self):
        self.run_command('tenant-network-create new_network 10.0.1.0/24')
        body = {'network': {'cidr': '10.0.1.0/24', 'label': 'new_network'}}
        self.assert_called('POST', '/os-tenant-networks', body)

    def test_tenant_network_delete(self):
        self.run_command('tenant-network-delete 1')
        self.assert_called('DELETE', '/os-tenant-networks/1')

    def test_add_fixed_ip(self):
        self.run_command('add-fixed-ip sample-server 1')
        self.assert_called('POST', '/servers/1234/action',
                           {'addFixedIp': {'networkId': '1'}})

    def test_remove_fixed_ip(self):
        self.run_command('remove-fixed-ip sample-server 10.0.0.10')
        self.assert_called('POST', '/servers/1234/action',
                           {'removeFixedIp': {'address': '10.0.0.10'}})

    def test_backup(self):
        self.run_command('backup sample-server back1 daily 1')
        self.assert_called('POST', '/servers/1234/action',
                           {'createBackup': {'name': 'back1',
                                             'backup_type': 'daily',
                                             'rotation': '1'}})
        self.run_command('backup 1234 back1 daily 1')
        self.assert_called('POST', '/servers/1234/action',
                           {'createBackup': {'name': 'back1',
                                             'backup_type': 'daily',
                                             'rotation': '1'}})

    def test_absolute_limits(self):
        self.run_command('absolute-limits')
        self.assert_called('GET', '/limits')

        self.run_command('absolute-limits --reserved')
        self.assert_called('GET', '/limits?reserved=1')

        self.run_command('absolute-limits --tenant 1234')
        self.assert_called('GET', '/limits?tenant_id=1234')

    def test_evacuate(self):
        self.run_command('evacuate sample-server new_host')
        self.assert_called('POST', '/servers/1234/action',
                           {'evacuate': {'host': 'new_host',
                                         'onSharedStorage': False}})
        self.run_command('evacuate sample-server new_host '
                         '--password NewAdminPass')
        self.assert_called('POST', '/servers/1234/action',
                           {'evacuate': {'host': 'new_host',
                                         'onSharedStorage': False,
                                         'adminPass': 'NewAdminPass'}})
        self.run_command('evacuate sample-server new_host '
                         '--on-shared-storage')
        self.assert_called('POST', '/servers/1234/action',
                           {'evacuate': {'host': 'new_host',
                                         'onSharedStorage': True}})

    def test_evacuate_with_no_target_host(self):
        self.run_command('evacuate sample-server')
        self.assert_called('POST', '/servers/1234/action',
                           {'evacuate': {'onSharedStorage': False}})
        self.run_command('evacuate sample-server --password NewAdminPass')
        self.assert_called('POST', '/servers/1234/action',
                           {'evacuate': {'onSharedStorage': False,
                                         'adminPass': 'NewAdminPass'}})
        self.run_command('evacuate sample-server --on-shared-storage')
        self.assert_called('POST', '/servers/1234/action',
                           {'evacuate': {'onSharedStorage': True}})

    def test_get_password(self):
        self.run_command('get-password sample-server /foo/id_rsa')
        self.assert_called('GET', '/servers/1234/os-server-password')

    def test_get_password_without_key(self):
        self.run_command('get-password sample-server')
        self.assert_called('GET', '/servers/1234/os-server-password')

    def test_clear_password(self):
        self.run_command('clear-password sample-server')
        self.assert_called('DELETE', '/servers/1234/os-server-password')

    def test_availability_zone_list(self):
        self.run_command('availability-zone-list')
        self.assert_called('GET', '/os-availability-zone/detail')

    def test_security_group_create(self):
        self.run_command('secgroup-create test FAKE_SECURITY_GROUP')
        self.assert_called('POST', '/os-security-groups',
                           {'security_group':
                               {'name': 'test',
                                'description': 'FAKE_SECURITY_GROUP'}})

    def test_security_group_update(self):
        self.run_command('secgroup-update test te FAKE_SECURITY_GROUP')
        self.assert_called('PUT', '/os-security-groups/1',
                           {'security_group':
                               {'name': 'te',
                                'description': 'FAKE_SECURITY_GROUP'}})

    def test_security_group_list(self):
        self.run_command('secgroup-list')
        self.assert_called('GET', '/os-security-groups')

    def test_security_group_add_rule(self):
        self.run_command('secgroup-add-rule test tcp 22 22 10.0.0.0/8')
        self.assert_called('POST', '/os-security-group-rules',
                           {'security_group_rule':
                               {'from_port': 22,
                                'ip_protocol': 'tcp',
                                'to_port': 22,
                                'parent_group_id': 1,
                                'cidr': '10.0.0.0/8',
                                'group_id': None}})

    def test_security_group_delete_rule(self):
        self.run_command('secgroup-delete-rule test TCP 22 22 10.0.0.0/8')
        self.assert_called('DELETE', '/os-security-group-rules/11')

    def test_security_group_delete_rule_protocol_case(self):
        self.run_command('secgroup-delete-rule test tcp 22 22 10.0.0.0/8')
        self.assert_called('DELETE', '/os-security-group-rules/11')

    def test_security_group_add_group_rule(self):
        self.run_command('secgroup-add-group-rule test test2 tcp 22 22')
        self.assert_called('POST', '/os-security-group-rules',
                           {'security_group_rule':
                               {'from_port': 22,
                                'ip_protocol': 'TCP',
                                'to_port': 22,
                                'parent_group_id': 1,
                                'cidr': None,
                                'group_id': 2}})

    def test_security_group_delete_valid_group_rule(self):
        self.run_command('secgroup-delete-group-rule test test2 TCP 222 222')
        self.assert_called('DELETE', '/os-security-group-rules/12')

    def test_security_group_delete_valid_group_rule_protocol_case(self):
        self.run_command('secgroup-delete-group-rule test test2 tcp 222 222')
        self.assert_called('DELETE', '/os-security-group-rules/12')

    def test_security_group_delete_invalid_group_rule(self):
        self.run_command('secgroup-delete-group-rule test test4 TCP -1 -1')
        self.assert_called('DELETE', '/os-security-group-rules/14')

    def test_security_group_delete_invalid_group_rule_protocol_case(self):
        self.run_command('secgroup-delete-group-rule test test4 tcp -1 -1')
        self.assert_called('DELETE', '/os-security-group-rules/14')

    def test_security_group_list_rules(self):
        self.run_command('secgroup-list-rules test')
        self.assert_called('GET', '/os-security-groups')

    def test_security_group_list_all_tenants(self):
        self.run_command('secgroup-list --all-tenants 1')
        self.assert_called('GET', '/os-security-groups?all_tenants=1')

    def test_security_group_delete(self):
        self.run_command('secgroup-delete test')
        self.assert_called('DELETE', '/os-security-groups/1')

    def test_server_security_group_add(self):
        self.run_command('add-secgroup sample-server testgroup')
        self.assert_called('POST', '/servers/1234/action',
                           {'addSecurityGroup': {'name': 'testgroup'}})

    def test_server_security_group_remove(self):
        self.run_command('remove-secgroup sample-server testgroup')
        self.assert_called('POST', '/servers/1234/action',
                           {'removeSecurityGroup': {'name': 'testgroup'}})

    def test_server_security_group_list(self):
        self.run_command('list-secgroup 1234')
        self.assert_called('GET', '/servers/1234/os-security-groups')

    def test_interface_list(self):
        self.run_command('interface-list 1234')
        self.assert_called('GET', '/servers/1234/os-interface')

    def test_interface_attach(self):
        self.run_command('interface-attach --port-id port_id 1234')
        self.assert_called('POST', '/servers/1234/os-interface',
                           {'interfaceAttachment': {'port_id': 'port_id'}})

    def test_interface_detach(self):
        self.run_command('interface-detach 1234 port_id')
        self.assert_called('DELETE', '/servers/1234/os-interface/port_id')

    def test_volume_list(self):
        self.run_command('volume-list')
        self.assert_called('GET', '/volumes/detail')

    def test_volume_show(self):
        self.run_command('volume-show Work')
        self.assert_called('GET', '/volumes?display_name=Work', pos=-2)
        self.assert_called(
            'GET',
            '/volumes/15e59938-07d5-11e1-90e3-e3dffe0c5983',
            pos=-1
        )

    def test_volume_create(self):
        self.run_command('volume-create 2 --display-name Work')
        self.assert_called('POST', '/volumes',
                           {'volume':
                               {'display_name': 'Work',
                                'imageRef': None,
                                'availability_zone': None,
                                'volume_type': None,
                                'display_description': None,
                                'snapshot_id': None,
                                'size': 2}})

    def test_volume_delete(self):
        self.run_command('volume-delete Work')
        self.assert_called('DELETE',
                           '/volumes/15e59938-07d5-11e1-90e3-e3dffe0c5983')

    def test_volume_delete_multiple(self):
        self.run_command('volume-delete Work Work2')
        self.assert_called('DELETE',
                           '/volumes/15e59938-07d5-11e1-90e3-e3dffe0c5983',
                           pos=-4)
        self.assert_called('DELETE',
                           '/volumes/15e59938-07d5-11e1-90e3-ee32ba30feaa',
                           pos=-1)

    def test_volume_attach(self):
        self.run_command('volume-attach sample-server Work /dev/vdb')
        self.assert_called('POST', '/servers/1234/os-volume_attachments',
                           {'volumeAttachment':
                               {'device': '/dev/vdb',
                                'volumeId': 'Work'}})

    def test_volume_attach_without_device(self):
        self.run_command('volume-attach sample-server Work')
        self.assert_called('POST', '/servers/1234/os-volume_attachments',
                           {'volumeAttachment':
                               {'device': None,
                                'volumeId': 'Work'}})

    def test_volume_update(self):
        self.run_command('volume-update sample-server Work Work')
        self.assert_called('PUT', '/servers/1234/os-volume_attachments/Work',
                           {'volumeAttachment': {'volumeId': 'Work'}})

    def test_volume_detach(self):
        self.run_command('volume-detach sample-server Work')
        self.assert_called('DELETE',
                           '/servers/1234/os-volume_attachments/Work')

    def test_instance_action_list(self):
        self.run_command('instance-action-list sample-server')
        self.assert_called('GET', '/servers/1234/os-instance-actions')

    def test_instance_action_get(self):
        self.run_command('instance-action sample-server req-abcde12345')
        self.assert_called(
            'GET',
            '/servers/1234/os-instance-actions/req-abcde12345')

    def test_cell_show(self):
        self.run_command('cell-show child_cell')
        self.assert_called('GET', '/os-cells/child_cell')

    def test_cell_capacities_with_cell_name(self):
        self.run_command('cell-capacities --cell child_cell')
        self.assert_called('GET', '/os-cells/child_cell/capacities')

    def test_cell_capacities_without_cell_name(self):
        self.run_command('cell-capacities')
        self.assert_called('GET', '/os-cells/capacities')

    def test_migration_list(self):
        self.run_command('migration-list')
        self.assert_called('GET', '/os-migrations')

    def test_migration_list_with_filters(self):
        self.run_command('migration-list --host host1 --cell_name child1 '
                         '--status finished')
        self.assert_called('GET',
                           '/os-migrations?cell_name=child1&host=host1'
                           '&status=finished')

    @mock.patch('novaclient.v2.shell._find_server')
    @mock.patch('os.system')
    def test_ssh(self, mock_system, mock_find_server):
        class FakeResources(object):
            addresses = {
                "skynet": [
                    {'version': 4, 'addr': "1.1.1.1",
                     "OS-EXT-IPS:type": 'fixed'},
                    {'version': 4, 'addr': "2.2.2.2",
                     "OS-EXT-IPS:type": 'floating'},
                    {'version': 6, 'addr': "2607:f0d0:1002::4",
                     "OS-EXT-IPS:type": 'fixed'},
                    {'version': 6, 'addr': "7612:a1b2:2004::6"}
                ]
            }
        mock_find_server.return_value = FakeResources()

        self.run_command("ssh --login bob server")
        mock_system.assert_called_with("ssh -4 -p22  bob@2.2.2.2 ")
        self.run_command("ssh alice@server")
        mock_system.assert_called_with("ssh -4 -p22  alice@2.2.2.2 ")
        self.run_command("ssh --port 202 server")
        mock_system.assert_called_with("ssh -4 -p202  root@2.2.2.2 ")
        self.run_command("ssh --private server")
        mock_system.assert_called_with("ssh -4 -p22  root@1.1.1.1 ")
        self.run_command("ssh -i ~/my_rsa_key server --private")
        mock_system.assert_called_with("ssh -4 -p22 -i ~/my_rsa_key "
                                       "root@1.1.1.1 ")
        self.run_command("ssh --extra-opts -1 server")
        mock_system.assert_called_with("ssh -4 -p22  root@2.2.2.2 -1")

        self.run_command("ssh --ipv6 --login carol server")
        mock_system.assert_called_with("ssh -6 -p22  carol@7612:a1b2:2004::6 ")
        self.run_command("ssh --ipv6 dan@server")
        mock_system.assert_called_with("ssh -6 -p22  dan@7612:a1b2:2004::6 ")
        self.run_command("ssh --ipv6 --port 2022 server")
        mock_system.assert_called_with("ssh -6 -p2022  "
                                       "root@7612:a1b2:2004::6 ")
        self.run_command("ssh --ipv6 --private server")
        mock_system.assert_called_with("ssh -6 -p22  root@2607:f0d0:1002::4 ")
        self.run_command("ssh --ipv6 --identity /home/me/my_dsa_key "
                         "--private server")
        mock_system.assert_called_with("ssh -6 -p22 -i /home/me/my_dsa_key "
                                       "root@2607:f0d0:1002::4 ")
        self.run_command("ssh --ipv6 --private --extra-opts -1 server")
        mock_system.assert_called_with("ssh -6 -p22  "
                                       "root@2607:f0d0:1002::4 -1")

    @mock.patch('novaclient.v2.shell._find_server')
    @mock.patch('os.system')
    def test_ssh_multinet(self, mock_system, mock_find_server):
        class FakeResources(object):
            addresses = {
                "skynet": [
                    {'version': 4, 'addr': "1.1.1.1",
                     "OS-EXT-IPS:type": 'fixed'},
                    {'version': 4, 'addr': "2.2.2.2"},
                    {'version': 6, 'addr': "2607:f0d0:1002::4",
                     "OS-EXT-IPS:type": 'fixed'}
                ],
                "other": [
                    {'version': 4, 'addr': "2.3.4.5"},
                    {'version': 6, 'addr': "7612:a1b2:2004::6"}
                ]
            }
        mock_find_server.return_value = FakeResources()

        self.run_command("ssh --network other server")
        mock_system.assert_called_with("ssh -4 -p22  root@2.3.4.5 ")
        self.run_command("ssh --ipv6 --network other server")
        mock_system.assert_called_with("ssh -6 -p22  root@7612:a1b2:2004::6 ")
        self.assertRaises(exceptions.ResourceNotFound,
                          self.run_command,
                          "ssh --ipv6 --network nonexistent server")

    def test_keypair_add(self):
        self.run_command('keypair-add test')
        self.assert_called('POST', '/os-keypairs',
                           {'keypair':
                               {'name': 'test'}})

    @mock.patch.object(builtins, 'open',
                       mock.mock_open(read_data='FAKE_PUBLIC_KEY'))
    def test_keypair_import(self):
        self.run_command('keypair-add --pub-key test.pub test')
        self.assert_called(
            'POST', '/os-keypairs', {
                'keypair': {'public_key': 'FAKE_PUBLIC_KEY', 'name': 'test'}})

    def test_keypair_stdin(self):
        with mock.patch('sys.stdin', six.StringIO('FAKE_PUBLIC_KEY')):
            self.run_command('keypair-add --pub-key - test')
            self.assert_called(
                'POST', '/os-keypairs', {
                    'keypair':
                        {'public_key': 'FAKE_PUBLIC_KEY', 'name': 'test'}})

    def test_keypair_list(self):
        self.run_command('keypair-list')
        self.assert_called('GET', '/os-keypairs')

    def test_keypair_show(self):
        self.run_command('keypair-show test')
        self.assert_called('GET', '/os-keypairs/test')

    def test_keypair_delete(self):
        self.run_command('keypair-delete test')
        self.assert_called('DELETE', '/os-keypairs/test')

    def test_create_server_group(self):
        self.run_command('server-group-create wjsg affinity')
        self.assert_called('POST', '/os-server-groups',
                           {'server_group': {'name': 'wjsg',
                                             'policies': ['affinity']}})

    def test_delete_multi_server_groups(self):
        self.run_command('server-group-delete 12345 56789')
        self.assert_called('DELETE', '/os-server-groups/56789')
        self.assert_called('DELETE', '/os-server-groups/12345', pos=-2)


class ShellTestV11(ShellTest):
    FAKE_ENV = {
        'NOVA_USERNAME': 'username',
        'NOVA_PASSWORD': 'password',
        'NOVA_PROJECT_ID': 'project_id',
        'OS_COMPUTE_API_VERSION': '1.1',
        'NOVA_URL': 'http://no.where',
        'OS_AUTH_URL': 'http://no.where/v2.0',
    }


class ShellTestV3(ShellTest):
    FAKE_ENV = {
        'NOVA_USERNAME': 'username',
        'NOVA_PASSWORD': 'password',
        'NOVA_PROJECT_ID': 'project_id',
        'OS_COMPUTE_API_VERSION': '3',
        'NOVA_URL': 'http://no.where',
        'OS_AUTH_URL': 'http://no.where/v2.0',
    }


class ShellWithSessionClientTest(ShellTest):

    def setUp(self):
        """Run before each test."""
        super(ShellWithSessionClientTest, self).setUp()
        self.useFixture(fixtures.MonkeyPatch(
            'novaclient.client.get_client_class',
            lambda *_: fakes.FakeSessionClient))


class GetSecgroupTest(utils.TestCase):
    def test_with_integer(self):
        cs = mock.Mock(**{
            'security_groups.get.return_value': 'sec_group',
            'security_groups.list.return_value': [],
        })
        result = novaclient.v2.shell._get_secgroup(cs, '1')
        self.assertEqual('sec_group', result)
        cs.security_groups.get.assert_called_once_with('1')

    def test_with_uuid(self):
        cs = mock.Mock(**{
            'security_groups.get.return_value': 'sec_group',
            'security_groups.list.return_value': [],
        })
        result = novaclient.v2.shell._get_secgroup(
            cs, 'c0c32459-dc5f-44dc-9a0a-473b28bac831')
        self.assertEqual('sec_group', result)
        cs.security_groups.get.assert_called_once_with(
            'c0c32459-dc5f-44dc-9a0a-473b28bac831')

    def test_with_an_nonexisting_name(self):
        cs = mock.Mock(**{
            'security_groups.get.return_value': 'sec_group',
            'security_groups.list.return_value': [],
        })
        self.assertRaises(exceptions.CommandError,
                          novaclient.v2.shell._get_secgroup,
                          cs,
                          'abc')

    def test_with_non_unique_name(self):
        group_one = mock.MagicMock()
        group_one.name = 'group_one'
        cs = mock.Mock(**{
            'security_groups.get.return_value': 'sec_group',
            'security_groups.list.return_value': [group_one, group_one],
        })
        self.assertRaises(exceptions.NoUniqueMatch,
                          novaclient.v2.shell._get_secgroup,
                          cs,
                          'group_one')


class GetFirstEndpointTest(utils.TestCase):
    def test_only_one_endpoint(self):
        """If there is only one endpoint, it is returned."""
        endpoint = {"url": "test"}
        result = novaclient.v2.shell._get_first_endpoint([endpoint], "XYZ")
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
        result = novaclient.v2.shell._get_first_endpoint(endpoints, "ORD")
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
                          novaclient.v2.shell._get_first_endpoint,
                          endpoints, "ORD")

    def test_no_endpoints(self):
        """If there are no endpoints available, an exception is raised."""
        self.assertRaises(LookupError,
                          novaclient.v2.shell._get_first_endpoint,
                          [], "ORD")
