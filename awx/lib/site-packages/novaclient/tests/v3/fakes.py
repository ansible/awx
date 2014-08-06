# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2011 OpenStack Foundation
# Copyright 2013 IBM Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from datetime import datetime

from novaclient.openstack.common import strutils
from novaclient.tests import fakes
from novaclient.tests.v1_1 import fakes as fakes_v1_1
from novaclient.v3 import client


class FakeClient(fakes.FakeClient, client.Client):

    def __init__(self, *args, **kwargs):
        client.Client.__init__(self, 'username', 'password',
                               'project_id', 'auth_url',
                               extensions=kwargs.get('extensions'))
        self.client = FakeHTTPClient(**kwargs)


class FakeHTTPClient(fakes_v1_1.FakeHTTPClient):
    #
    # Hosts
    #
    def put_os_hosts_sample_host_1(self, body, **kw):
        return (200, {}, {'host': {'host': 'sample-host_1',
                      'status': 'enabled'}})

    def put_os_hosts_sample_host_2(self, body, **kw):
        return (200, {}, {'host': {'host': 'sample-host_2',
                      'maintenance_mode': 'on_maintenance'}})

    def put_os_hosts_sample_host_3(self, body, **kw):
        return (200, {}, {'host': {'host': 'sample-host_3',
                      'status': 'enabled',
                      'maintenance_mode': 'on_maintenance'}})

    def get_os_hosts_sample_host_reboot(self, **kw):
        return (200, {}, {'host': {'host': 'sample_host',
                          'power_action': 'reboot'}})

    def get_os_hosts_sample_host_startup(self, **kw):
        return (200, {}, {'host': {'host': 'sample_host',
                          'power_action': 'startup'}})

    def get_os_hosts_sample_host_shutdown(self, **kw):
        return (200, {}, {'host': {'host': 'sample_host',
                          'power_action': 'shutdown'}})

    #
    # Flavors
    #
    post_flavors_1_flavor_extra_specs = (
        fakes_v1_1.FakeHTTPClient.post_flavors_1_os_extra_specs)

    post_flavors_4_flavor_extra_specs = (
        fakes_v1_1.FakeHTTPClient.post_flavors_4_os_extra_specs)

    delete_flavors_1_flavor_extra_specs_k1 = (
        fakes_v1_1.FakeHTTPClient.delete_flavors_1_os_extra_specs_k1)

    def get_flavors_detail(self, **kw):
        flavors = {'flavors': [
            {'id': 1, 'name': '256 MB Server', 'ram': 256, 'disk': 10,
             'ephemeral': 10,
             'flavor-access:is_public': True,
             'links': {}},
            {'id': 2, 'name': '512 MB Server', 'ram': 512, 'disk': 20,
             'ephemeral': 20,
             'flavor-access:is_public': False,
             'links': {}},
            {'id': 4, 'name': '1024 MB Server', 'ram': 1024, 'disk': 10,
             'ephemeral': 10,
             'flavor-access:is_public': True,
             'links': {}},
            {'id': 'aa1', 'name': '128 MB Server', 'ram': 128, 'disk': 0,
             'ephemeral': 0,
             'flavor-access:is_public': True,
             'links': {}}
        ]}

        if 'is_public' not in kw:
            filter_is_public = True
        else:
            if kw['is_public'].lower() == 'none':
                filter_is_public = None
            else:
                filter_is_public = strutils.bool_from_string(kw['is_public'],
                                                             True)

        if filter_is_public is not None:
            if filter_is_public:
                flavors['flavors'] = [
                        v for v in flavors['flavors']
                            if v['flavor-access:is_public']
                        ]
            else:
                flavors['flavors'] = [
                        v for v in flavors['flavors']
                            if not v['flavor-access:is_public']
                        ]

        return (200, {}, flavors)

    #
    # Flavor access
    #
    get_flavors_2_flavor_access = (
        fakes_v1_1.FakeHTTPClient.get_flavors_2_os_flavor_access)
    get_flavors_2_flavor_extra_specs = (
        fakes_v1_1.FakeHTTPClient.get_flavors_2_os_extra_specs)
    get_flavors_aa1_flavor_extra_specs = (
        fakes_v1_1.FakeHTTPClient.get_flavors_aa1_os_extra_specs)

    #
    # Images
    #
    get_v1_images_detail = fakes_v1_1.FakeHTTPClient.get_images_detail
    get_v1_images = fakes_v1_1.FakeHTTPClient.get_images

    def head_v1_images_1(self, **kw):
        headers = {
            'x-image-meta-id': '1',
            'x-image-meta-name': 'CentOS 5.2',
            'x-image-meta-updated': '2010-10-10T12:00:00Z',
            'x-image-meta-created': '2010-10-10T12:00:00Z',
            'x-image-meta-status': 'ACTIVE',
            'x-image-meta-property-test_key': 'test_value'}
        return 200, headers, ''

    #
    # Servers
    #
    get_servers_1234_os_server_diagnostics = (
        fakes_v1_1.FakeHTTPClient.get_servers_1234_diagnostics)

    delete_servers_1234_os_attach_interfaces_port_id = (
        fakes_v1_1.FakeHTTPClient.delete_servers_1234_os_interface_port_id)

    def get_servers_1234_os_attach_interfaces(self, **kw):
        return (200, {}, {"interface_attachments": [
                             {"port_state": "ACTIVE",
                              "net_id": "net-id-1",
                              "port_id": "port-id-1",
                              "mac_address": "aa:bb:cc:dd:ee:ff",
                              "fixed_ips": [{"ip_address": "1.2.3.4"}],
                              },
                             {"port_state": "ACTIVE",
                              "net_id": "net-id-1",
                              "port_id": "port-id-1",
                              "mac_address": "aa:bb:cc:dd:ee:ff",
                              "fixed_ips": [{"ip_address": "1.2.3.4"}],
                              }]})

    def post_servers_1234_os_attach_interfaces(self, **kw):
        return (200, {}, {'interface_attachment': {}})

    def post_servers(self, body, **kw):
        assert set(body.keys()) <= set(['server'])
        fakes.assert_has_keys(body['server'],
                        required=['name', 'image_ref', 'flavor_ref'],
                        optional=['metadata', 'personality',
                                  'os-scheduler-hints:scheduler_hints'])
        if body['server']['name'] == 'some-bad-server':
            return (202, {}, self.get_servers_1235()[2])
        else:
            return (202, {}, self.get_servers_1234()[2])

    #
    # Server Actions
    #
    def post_servers_1234_action(self, body, **kw):
        _headers = None
        resp = 202
        body_is_none_list = [
            'revert_resize', 'migrate', 'stop', 'start', 'force_delete',
            'restore', 'pause', 'unpause', 'lock', 'unlock', 'unrescue',
            'resume', 'suspend', 'lock', 'unlock', 'shelve', 'shelve_offload',
            'unshelve', 'reset_network', 'rescue', 'confirm_resize']
        body_return_map = {
            'rescue': {'admin_password': 'RescuePassword'},
            'get_console_output': {'output': 'foo'},
            'rebuild': self.get_servers_1234()[2],
            }
        body_param_check_exists = {
            'rebuild': 'image_ref',
            'resize': 'flavor_ref'}
        body_params_check_exact = {
            'reboot': ['type'],
            'add_fixed_ip': ['network_id'],
            'evacuate': ['host', 'on_shared_storage'],
            'remove_fixed_ip': ['address'],
            'change_password': ['admin_password'],
            'get_console_output': ['length'],
            'get_vnc_console': ['type'],
            'get_spice_console': ['type'],
            'reset_state': ['state'],
            'create_image': ['name', 'metadata'],
            'migrate_live': ['host', 'block_migration', 'disk_over_commit'],
            'create_backup': ['name', 'backup_type', 'rotation'],
            'detach': ['volume_id'],
            'swap_volume_attachment': ['old_volume_id', 'new_volume_id']}
        body_params_check_superset = {
            'attach': ['volume_id', 'device']}

        assert len(body.keys()) == 1
        action = list(body)[0]
        _body = body_return_map.get(action)

        if action in body_is_none_list:
            assert body[action] is None

        if action in body_param_check_exists:
            assert body_param_check_exists[action] in body[action]

        if action == 'evacuate':
            body[action].pop('admin_password', None)

        if action in body_params_check_exact:
            assert set(body[action]) == set(body_params_check_exact[action])

        if action in body_params_check_superset:
            assert set(body[action]) >= set(body_params_check_superset[action])

        if action == 'reboot':
            assert body[action]['type'] in ['HARD', 'SOFT']
        elif action == 'confirm_resize':
            # This one method returns a different response code
            resp = 204
        elif action == 'create_image':
            _headers = dict(location="http://blah/images/456")

        if action not in set.union(set(body_is_none_list),
                                     set(body_params_check_exact.keys()),
                                     set(body_param_check_exists.keys()),
                                     set(body_params_check_superset.keys())):
            raise AssertionError("Unexpected server action: %s" % action)

        return (resp, _headers, _body)

    #
    # Server password
    #

    def get_servers_1234_os_server_password(self, **kw):
        return (200, {}, {'password': ''})

    def delete_servers_1234_os_server_password(self, **kw):
        return (202, {}, None)

    #
    # Availability Zones
    #
    def get_os_availability_zone(self, **kw):
        return (200, {}, {"availability_zone_info": [
                              {"zone_name": "zone-1",
                               "zone_state": {"available": True},
                               "hosts": None},
                              {"zone_name": "zone-2",
                               "zone_state": {"available": False},
                               "hosts": None}]})

    def get_os_availability_zone_detail(self, **kw):
        return (200, {}, {"availability_zone_info": [
                              {"zone_name": "zone-1",
                               "zone_state": {"available": True},
                               "hosts": {
                                   "fake_host-1": {
                                       "nova-compute": {"active": True,
                                           "available": True,
                                           "updated_at":
                                   datetime(2012, 12, 26, 14, 45, 25, 0)}}}},
                              {"zone_name": "internal",
                               "zone_state": {"available": True},
                               "hosts": {
                                   "fake_host-1": {
                                       "nova-sched": {
                                           "active": True,
                                           "available": True,
                                           "updated_at":
                                   datetime(2012, 12, 26, 14, 45, 25, 0)}},
                                   "fake_host-2": {
                                       "nova-network": {
                                           "active": True,
                                           "available": False,
                                           "updated_at":
                                   datetime(2012, 12, 26, 14, 45, 24, 0)}}}},
                              {"zone_name": "zone-2",
                               "zone_state": {"available": False},
                               "hosts": None}]})

    #
    # Quotas
    #
    def put_os_quota_sets_97f4c221bff44578b0300df4ef119353(self, body, **kw):
        assert list(body) == ['quota_set']
        return (200, {}, {'quota_set': {
                      'tenant_id': '97f4c221bff44578b0300df4ef119353',
                      'metadata_items': [],
                      'injected_file_content_bytes': 1,
                      'injected_file_path_bytes': 1,
                      'ram': 1,
                      'floating_ips': 1,
                      'instances': 1,
                      'injected_files': 1,
                      'cores': 1,
                      'keypairs': 1,
                      'security_groups': 1,
                      'security_group_rules': 1}})

    def get_os_quota_sets_test_detail(self, **kw):
        return (200, {}, {'quota_set': {
            'cores': {'reserved': 0, 'in_use': 0, 'limit': 10},
            'instances': {'reserved': 0, 'in_use': 4, 'limit': 50},
            'ram': {'reserved': 0, 'in_use': 1024, 'limit': 51200}}})

    #
    # Hypervisors
    #
    def get_os_hypervisors_search(self, **kw):
        return (200, {}, {'hypervisors': [
                    {'id': 1234, 'hypervisor_hostname': 'hyper1'},
                    {'id': 5678, 'hypervisor_hostname': 'hyper2'}
                    ]})

    def get_os_hypervisors_1234_servers(self, **kw):
        return (200, {}, {'hypervisor':
                    {'id': 1234,
                     'hypervisor_hostname': 'hyper1',
                     'servers': [
                            {'name': 'inst1', 'id': 'uuid1'},
                            {'name': 'inst2', 'id': 'uuid2'}
                            ]},
                    })

    #
    # Keypairs
    #
    get_keypairs_test = fakes_v1_1.FakeHTTPClient.get_os_keypairs_test
    get_keypairs = fakes_v1_1.FakeHTTPClient.get_os_keypairs
    delete_keypairs_test = fakes_v1_1.FakeHTTPClient.delete_os_keypairs_test
    post_keypairs = fakes_v1_1.FakeHTTPClient.post_os_keypairs

    #
    # List all extensions
    #
    def get_extensions(self, **kw):
        exts = [
            {
                "alias": "os-multinic",
                "description": "Multiple network support",
                "name": "Multinic",
                "version": 1,
            },
            {
                "alias": "os-extended-server-attributes",
                "description": "Extended Server Attributes support.",
                "name": "ExtendedServerAttributes",
                "version": 1,
            },
            {
                "alias": "os-extended-status",
                "description": "Extended Status support",
                "name": "ExtendedStatus",
                "version": 1,
            },
        ]
        return (200, {}, {
            "extensions": exts,
        })
