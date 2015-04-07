# -*- coding: utf-8 -*-
#
# Copyright 2013 Hewlett-Packard Development Company, L.P.
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

import copy
import tempfile

import mock
import testtools
from testtools.matchers import HasLength

from ironicclient.common import utils as common_utils
from ironicclient import exc
from ironicclient.tests.unit import utils
from ironicclient.v1 import node

NODE1 = {'id': 123,
         'uuid': '66666666-7777-8888-9999-000000000000',
         'chassis_uuid': 'aaaaaaaa-1111-bbbb-2222-cccccccccccc',
         'maintenance': False,
         'driver': 'fake',
         'driver_info': {'user': 'foo', 'password': 'bar'},
         'properties': {'num_cpu': 4},
         'name': 'fake-node-1',
         'extra': {}}
NODE2 = {'id': 456,
         'uuid': '66666666-7777-8888-9999-111111111111',
         'instance_uuid': '66666666-7777-8888-9999-222222222222',
         'chassis_uuid': 'aaaaaaaa-1111-bbbb-2222-cccccccccccc',
         'maintenance': True,
         'driver': 'fake too',
         'driver_info': {'user': 'foo', 'password': 'bar'},
         'properties': {'num_cpu': 4},
         'extra': {}}
PORT = {'id': 456,
        'uuid': '11111111-2222-3333-4444-555555555555',
        'node_id': 123,
        'address': 'AA:AA:AA:AA:AA:AA',
        'extra': {}}

POWER_STATE = {'power_state': 'power off',
               'target_power_state': 'power on'}

DRIVER_IFACES = {'deploy': {'result': True},
                 'power': {'result': False, 'reason': 'Invalid IPMI username'},
                 'console': {'result': None, 'reason': 'not supported'},
                 'rescue': {'result': None, 'reason': 'not supported'}}

NODE_STATES = {"last_error": None,
               "power_state": "power on",
               "provision_state": "active",
               "target_power_state": None,
               "target_provision_state": None}

CONSOLE_DATA_ENABLED = {'console_enabled': True,
                        'console_info': {'test-console': 'test-console-data'}}
CONSOLE_DATA_DISABLED = {'console_enabled': False, 'console_info': None}

BOOT_DEVICE = {'boot_device': 'pxe', 'persistent': False}
SUPPORTED_BOOT_DEVICE = {'supported_boot_devices': ['pxe']}

CREATE_NODE = copy.deepcopy(NODE1)
del CREATE_NODE['id']
del CREATE_NODE['uuid']
del CREATE_NODE['maintenance']

UPDATED_NODE = copy.deepcopy(NODE1)
NEW_DRIVER = 'new-driver'
UPDATED_NODE['driver'] = NEW_DRIVER

CREATE_WITH_UUID = copy.deepcopy(NODE1)
del CREATE_WITH_UUID['id']
del CREATE_WITH_UUID['maintenance']

fake_responses = {
    '/v1/nodes':
    {
        'GET': (
            {},
            {"nodes": [NODE1, NODE2]}
        ),
        'POST': (
            {},
            CREATE_NODE,
        ),
    },
    '/v1/nodes/detail':
    {
        'GET': (
            {},
            {"nodes": [NODE1, NODE2]}
        ),
    },
    '/v1/nodes/?associated=False':
    {
        'GET': (
            {},
            {"nodes": [NODE1]},
        )
    },
    '/v1/nodes/?associated=True':
    {
        'GET': (
            {},
            {"nodes": [NODE2]},
        )
    },
    '/v1/nodes/?maintenance=False':
    {
        'GET': (
            {},
            {"nodes": [NODE1]},
        )
    },
    '/v1/nodes/?maintenance=True':
    {
        'GET': (
            {},
            {"nodes": [NODE2]},
        )
    },
    '/v1/nodes/?associated=True&maintenance=True':
    {
        'GET': (
            {},
            {"nodes": [NODE2]},
        )
    },
    '/v1/nodes/detail?instance_uuid=%s' % NODE2['instance_uuid']:
    {
        'GET': (
            {},
            {"nodes": [NODE2]},
        )
    },
    '/v1/nodes/%s' % NODE1['uuid']:
    {
        'GET': (
            {},
            NODE1,
        ),
        'DELETE': (
            {},
            None,
        ),
        'PATCH': (
            {},
            UPDATED_NODE,
        ),
    },
    '/v1/nodes/%s' % NODE2['uuid']:
    {
        'GET': (
            {},
            NODE2,
        ),
    },
    '/v1/nodes/%s' % NODE1['name']:
    {
        'GET': (
            {},
            NODE1,
        ),
    },
    '/v1/nodes/%s/ports' % NODE1['uuid']:
    {
        'GET': (
            {},
            {"ports": [PORT]},
        ),
    },
    '/v1/nodes/%s/ports/detail' % NODE1['uuid']:
    {
        'GET': (
            {},
            {"ports": [PORT]},
        ),
    },
    '/v1/nodes/%s/maintenance' % NODE1['uuid']:
    {
        'PUT': (
            {},
            None,
        ),
        'DELETE': (
            {},
            None,
        ),
    },
    '/v1/nodes/%s/states/power' % NODE1['uuid']:
    {
        'PUT': (
            {},
            POWER_STATE,
        ),
    },
    '/v1/nodes/%s/validate' % NODE1['uuid']:
    {
        'GET': (
            {},
            DRIVER_IFACES,
        ),
    },
    '/v1/nodes/%s/states/provision' % NODE1['uuid']:
    {
        'PUT': (
            {},
            None,
        ),
    },
    '/v1/nodes/%s/states' % NODE1['uuid']:
    {
        'GET': (
            {},
            NODE_STATES,
        ),
    },
    '/v1/nodes/%s/states/console' % NODE1['uuid']:
    {
        'GET': (
            {},
            CONSOLE_DATA_ENABLED,
        ),
        'PUT': (
            {'enabled': 'true'},
            None,
        ),
    },
    '/v1/nodes/%s/states/console' % NODE2['uuid']:
    {
        'GET': (
            {},
            CONSOLE_DATA_DISABLED,
        ),
    },
    '/v1/nodes/%s/management/boot_device' % NODE1['uuid']:
    {
        'GET': (
            {},
            BOOT_DEVICE,
        ),
        'PUT': (
            {},
            None,
        ),
    },
    '/v1/nodes/%s/management/boot_device/supported' % NODE1['uuid']:
    {
        'GET': (
            {},
            SUPPORTED_BOOT_DEVICE,
        ),
    },
}

fake_responses_pagination = {
    '/v1/nodes':
    {
        'GET': (
            {},
            {"nodes": [NODE1],
             "next": "http://127.0.0.1:6385/v1/nodes/?limit=1"}
        ),
    },
    '/v1/nodes/?limit=1':
    {
        'GET': (
            {},
            {"nodes": [NODE2]}
        ),
    },
    '/v1/nodes/?marker=%s' % NODE1['uuid']:
    {
        'GET': (
            {},
            {"nodes": [NODE2]}
        ),
    },
    '/v1/nodes/%s/ports?limit=1' % NODE1['uuid']:
    {
        'GET': (
            {},
            {"ports": [PORT]},
        ),
    },
    '/v1/nodes/%s/ports?marker=%s' % (NODE1['uuid'], PORT['uuid']):
    {
        'GET': (
            {},
            {"ports": [PORT]},
        ),
    },
}

fake_responses_sorting = {
    '/v1/nodes/?sort_key=updated_at':
    {
        'GET': (
            {},
            {"nodes": [NODE2, NODE1]}
        ),
    },
    '/v1/nodes/?sort_dir=desc':
    {
        'GET': (
            {},
            {"nodes": [NODE2, NODE1]}
        ),
    },
    '/v1/nodes/%s/ports?sort_key=updated_at' % NODE1['uuid']:
    {
        'GET': (
            {},
            {"ports": [PORT]},
        ),
    },
    '/v1/nodes/%s/ports?sort_dir=desc' % NODE1['uuid']:
    {
        'GET': (
            {},
            {"ports": [PORT]},
        ),
    },
}


class NodeManagerTest(testtools.TestCase):

    def setUp(self):
        super(NodeManagerTest, self).setUp()
        self.api = utils.FakeAPI(fake_responses)
        self.mgr = node.NodeManager(self.api)

    def test_node_list(self):
        nodes = self.mgr.list()
        expect = [
            ('GET', '/v1/nodes', {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(2, len(nodes))

    def test_node_list_shows_name(self):
        nodes = self.mgr.list()
        self.assertIsNotNone(getattr(nodes[0], 'name'))

    def test_node_list_limit(self):
        self.api = utils.FakeAPI(fake_responses_pagination)
        self.mgr = node.NodeManager(self.api)
        nodes = self.mgr.list(limit=1)
        expect = [
            ('GET', '/v1/nodes/?limit=1', {}, None)
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertThat(nodes, HasLength(1))

    def test_node_list_marker(self):
        self.api = utils.FakeAPI(fake_responses_pagination)
        self.mgr = node.NodeManager(self.api)
        nodes = self.mgr.list(marker=NODE1['uuid'])
        expect = [
            ('GET', '/v1/nodes/?marker=%s' % NODE1['uuid'], {}, None)
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertThat(nodes, HasLength(1))

    def test_node_list_pagination_no_limit(self):
        self.api = utils.FakeAPI(fake_responses_pagination)
        self.mgr = node.NodeManager(self.api)
        nodes = self.mgr.list(limit=0)
        expect = [
            ('GET', '/v1/nodes', {}, None),
            ('GET', '/v1/nodes/?limit=1', {}, None)
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(2, len(nodes))

    def test_node_list_sort_key(self):
        self.api = utils.FakeAPI(fake_responses_sorting)
        self.mgr = node.NodeManager(self.api)
        nodes = self.mgr.list(sort_key='updated_at')
        expect = [
            ('GET', '/v1/nodes/?sort_key=updated_at', {}, None)
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(2, len(nodes))

    def test_node_list_sort_dir(self):
        self.api = utils.FakeAPI(fake_responses_sorting)
        self.mgr = node.NodeManager(self.api)
        nodes = self.mgr.list(sort_dir='desc')
        expect = [
            ('GET', '/v1/nodes/?sort_dir=desc', {}, None)
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(2, len(nodes))

    def test_node_list_associated(self):
        nodes = self.mgr.list(associated=True)
        expect = [
            ('GET', '/v1/nodes/?associated=True', {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertThat(nodes, HasLength(1))
        self.assertEqual(NODE2['uuid'], getattr(nodes[0], 'uuid'))

    def test_node_list_unassociated(self):
        nodes = self.mgr.list(associated=False)
        expect = [
            ('GET', '/v1/nodes/?associated=False', {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertThat(nodes, HasLength(1))
        self.assertEqual(NODE1['uuid'], getattr(nodes[0], 'uuid'))

    def test_node_list_maintenance(self):
        nodes = self.mgr.list(maintenance=True)
        expect = [
            ('GET', '/v1/nodes/?maintenance=True', {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertThat(nodes, HasLength(1))
        self.assertEqual(NODE2['uuid'], getattr(nodes[0], 'uuid'))

    def test_node_list_no_maintenance(self):
        nodes = self.mgr.list(maintenance=False)
        expect = [
            ('GET', '/v1/nodes/?maintenance=False', {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertThat(nodes, HasLength(1))
        self.assertEqual(NODE1['uuid'], getattr(nodes[0], 'uuid'))

    def test_node_list_associated_and_maintenance(self):
        nodes = self.mgr.list(associated=True, maintenance=True)
        expect = [
            ('GET', '/v1/nodes/?associated=True&maintenance=True', {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertThat(nodes, HasLength(1))
        self.assertEqual(NODE2['uuid'], getattr(nodes[0], 'uuid'))

    def test_node_list_detail(self):
        nodes = self.mgr.list(detail=True)
        expect = [
            ('GET', '/v1/nodes/detail', {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(2, len(nodes))
        self.assertEqual(nodes[0].extra, {})

    def test_node_show(self):
        node = self.mgr.get(NODE1['uuid'])
        expect = [
            ('GET', '/v1/nodes/%s' % NODE1['uuid'], {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(NODE1['uuid'], node.uuid)

    def test_node_show_by_instance(self):
        node = self.mgr.get_by_instance_uuid(NODE2['instance_uuid'])
        expect = [
            ('GET', '/v1/nodes/detail?instance_uuid=%s' %
             NODE2['instance_uuid'], {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(NODE2['uuid'], node.uuid)

    def test_node_show_by_name(self):
        node = self.mgr.get(NODE1['name'])
        expect = [
            ('GET', '/v1/nodes/%s' % NODE1['name'], {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(NODE1['uuid'], node.uuid)

    def test_create(self):
        node = self.mgr.create(**CREATE_NODE)
        expect = [
            ('POST', '/v1/nodes', {}, CREATE_NODE),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertTrue(node)

    def test_create_with_uuid(self):
        node = self.mgr.create(**CREATE_WITH_UUID)
        expect = [
            ('POST', '/v1/nodes', {}, CREATE_WITH_UUID),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertTrue(node)

    def test_delete(self):
        node = self.mgr.delete(node_id=NODE1['uuid'])
        expect = [
            ('DELETE', '/v1/nodes/%s' % NODE1['uuid'], {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertIsNone(node)

    def test_update(self):
        patch = {'op': 'replace',
                 'value': NEW_DRIVER,
                 'path': '/driver'}
        node = self.mgr.update(node_id=NODE1['uuid'], patch=patch)
        expect = [
            ('PATCH', '/v1/nodes/%s' % NODE1['uuid'], {}, patch),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(NEW_DRIVER, node.driver)

    def test_node_port_list(self):
        ports = self.mgr.list_ports(NODE1['uuid'])
        expect = [
            ('GET', '/v1/nodes/%s/ports' % NODE1['uuid'], {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(1, len(ports))
        self.assertEqual(PORT['uuid'], ports[0].uuid)
        self.assertEqual(PORT['address'], ports[0].address)

    def test_node_port_list_limit(self):
        self.api = utils.FakeAPI(fake_responses_pagination)
        self.mgr = node.NodeManager(self.api)
        ports = self.mgr.list_ports(NODE1['uuid'], limit=1)
        expect = [
            ('GET', '/v1/nodes/%s/ports?limit=1' % NODE1['uuid'], {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertThat(ports, HasLength(1))
        self.assertEqual(PORT['uuid'], ports[0].uuid)
        self.assertEqual(PORT['address'], ports[0].address)

    def test_node_port_list_marker(self):
        self.api = utils.FakeAPI(fake_responses_pagination)
        self.mgr = node.NodeManager(self.api)
        ports = self.mgr.list_ports(NODE1['uuid'], marker=PORT['uuid'])
        expect = [
            ('GET', '/v1/nodes/%s/ports?marker=%s' % (NODE1['uuid'],
                                                      PORT['uuid']), {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertThat(ports, HasLength(1))

    def test_node_port_list_sort_key(self):
        self.api = utils.FakeAPI(fake_responses_sorting)
        self.mgr = node.NodeManager(self.api)
        ports = self.mgr.list_ports(NODE1['uuid'], sort_key='updated_at')
        expect = [
            ('GET', '/v1/nodes/%s/ports?sort_key=updated_at' % NODE1['uuid'],
             {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertThat(ports, HasLength(1))
        self.assertEqual(PORT['uuid'], ports[0].uuid)
        self.assertEqual(PORT['address'], ports[0].address)

    def test_node_port_list_sort_dir(self):
        self.api = utils.FakeAPI(fake_responses_sorting)
        self.mgr = node.NodeManager(self.api)
        ports = self.mgr.list_ports(NODE1['uuid'], sort_dir='desc')
        expect = [
            ('GET', '/v1/nodes/%s/ports?sort_dir=desc' % NODE1['uuid'],
             {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertThat(ports, HasLength(1))
        self.assertEqual(PORT['uuid'], ports[0].uuid)
        self.assertEqual(PORT['address'], ports[0].address)

    def test_node_port_list_detail(self):
        ports = self.mgr.list_ports(NODE1['uuid'], detail=True)
        expect = [
            ('GET', '/v1/nodes/%s/ports/detail' % NODE1['uuid'], {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(1, len(ports))

    def test_node_set_maintenance_true(self):
        maintenance = self.mgr.set_maintenance(NODE1['uuid'], 'true',
                                               maint_reason='reason')
        body = {'reason': 'reason'}
        expect = [
            ('PUT', '/v1/nodes/%s/maintenance' % NODE1['uuid'], {}, body),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(None, maintenance)

    def test_node_set_maintenance_false(self):
        maintenance = self.mgr.set_maintenance(NODE1['uuid'], 'false')
        expect = [
            ('DELETE', '/v1/nodes/%s/maintenance' % NODE1['uuid'], {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(None, maintenance)

    def test_node_set_maintenance_on(self):
        maintenance = self.mgr.set_maintenance(NODE1['uuid'], 'on',
                                               maint_reason='reason')
        body = {'reason': 'reason'}
        expect = [
            ('PUT', '/v1/nodes/%s/maintenance' % NODE1['uuid'], {}, body),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(None, maintenance)

    def test_node_set_maintenance_off(self):
        maintenance = self.mgr.set_maintenance(NODE1['uuid'], 'off')
        expect = [
            ('DELETE', '/v1/nodes/%s/maintenance' % NODE1['uuid'], {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(None, maintenance)

    def test_node_set_power_state(self):
        power_state = self.mgr.set_power_state(NODE1['uuid'], "on")
        body = {'target': 'power on'}
        expect = [
            ('PUT', '/v1/nodes/%s/states/power' % NODE1['uuid'], {}, body),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual('power on', power_state.target_power_state)

    def test_node_validate(self):
        ifaces = self.mgr.validate(NODE1['uuid'])
        expect = [
            ('GET', '/v1/nodes/%s/validate' % NODE1['uuid'], {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(DRIVER_IFACES['power'], ifaces.power)
        self.assertEqual(DRIVER_IFACES['deploy'], ifaces.deploy)
        self.assertEqual(DRIVER_IFACES['rescue'], ifaces.rescue)
        self.assertEqual(DRIVER_IFACES['console'], ifaces.console)

    def test_node_set_provision_state(self):
        target_state = 'active'
        self.mgr.set_provision_state(NODE1['uuid'], target_state)
        body = {'target': target_state}
        expect = [
            ('PUT', '/v1/nodes/%s/states/provision' % NODE1['uuid'], {}, body),
        ]
        self.assertEqual(expect, self.api.calls)

    def test_node_set_provision_state_with_configdrive(self):
        target_state = 'active'
        self.mgr.set_provision_state(NODE1['uuid'], target_state,
                                     configdrive='foo')
        body = {'target': target_state, 'configdrive': 'foo'}
        expect = [
            ('PUT', '/v1/nodes/%s/states/provision' % NODE1['uuid'], {}, body),
        ]
        self.assertEqual(expect, self.api.calls)

    def test_node_set_provision_state_with_configdrive_file(self):
        target_state = 'active'
        file_content = b'foo bar cat meow dog bark'

        with tempfile.NamedTemporaryFile() as f:
            f.write(file_content)
            f.flush()
            self.mgr.set_provision_state(NODE1['uuid'], target_state,
                                         configdrive=f.name)

        body = {'target': target_state, 'configdrive': file_content}
        expect = [
            ('PUT', '/v1/nodes/%s/states/provision' % NODE1['uuid'], {}, body),
        ]
        self.assertEqual(expect, self.api.calls)

    @mock.patch.object(common_utils, 'make_configdrive')
    def test_node_set_provision_state_with_configdrive_dir(self,
                                                           mock_configdrive):
        mock_configdrive.return_value = 'fake-configdrive'
        target_state = 'active'

        with common_utils.tempdir() as dirname:
            self.mgr.set_provision_state(NODE1['uuid'], target_state,
                                         configdrive=dirname)
            mock_configdrive.assert_called_once_with(dirname)

        body = {'target': target_state, 'configdrive': 'fake-configdrive'}
        expect = [
            ('PUT', '/v1/nodes/%s/states/provision' % NODE1['uuid'], {}, body),
        ]
        self.assertEqual(expect, self.api.calls)

    def test_node_states(self):
        states = self.mgr.states(NODE1['uuid'])
        expect = [
            ('GET', '/v1/nodes/%s/states' % NODE1['uuid'], {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        expected_fields = ['last_error', 'power_state', 'provision_state',
                           'target_power_state', 'target_provision_state']
        self.assertEqual(sorted(expected_fields),
                         sorted(states.to_dict().keys()))

    def test_node_set_console_mode(self):
        enabled = 'true'
        self.mgr.set_console_mode(NODE1['uuid'], enabled)
        body = {'enabled': enabled}
        expect = [
            ('PUT', '/v1/nodes/%s/states/console' % NODE1['uuid'], {}, body),
        ]
        self.assertEqual(expect, self.api.calls)

    def test_node_get_console(self):
        info = self.mgr.get_console(NODE1['uuid'])
        expect = [
            ('GET', '/v1/nodes/%s/states/console' % NODE1['uuid'], {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(CONSOLE_DATA_ENABLED, info)

    def test_node_get_console_disabled(self):
        info = self.mgr.get_console(NODE2['uuid'])
        expect = [
            ('GET', '/v1/nodes/%s/states/console' % NODE2['uuid'], {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(CONSOLE_DATA_DISABLED, info)

    @mock.patch.object(node.NodeManager, 'update')
    def test_vendor_passthru_update(self, update_mock):
        # For now just mock the tests because vendor-passthru doesn't return
        # anything to verify.
        vendor_passthru_args = {'arg1': 'val1'}
        kwargs = {
            'node_id': 'node_uuid',
            'method': 'method',
            'args': vendor_passthru_args
            }

        final_path = 'node_uuid/vendor_passthru/method'
        for http_method in ('POST', 'PUT', 'PATCH'):
            kwargs['http_method'] = http_method
            self.mgr.vendor_passthru(**kwargs)
            update_mock.assert_called_once_with(final_path,
                                                vendor_passthru_args,
                                                http_method=http_method)
            update_mock.reset_mock()

    @mock.patch.object(node.NodeManager, 'get')
    def test_vendor_passthru_get(self, get_mock):
        kwargs = {
            'node_id': 'node_uuid',
            'method': 'method',
            'http_method': 'GET',
            }

        final_path = 'node_uuid/vendor_passthru/method'
        self.mgr.vendor_passthru(**kwargs)
        get_mock.assert_called_once_with(final_path)

    @mock.patch.object(node.NodeManager, 'delete')
    def test_vendor_passthru_delete(self, delete_mock):
        kwargs = {
            'node_id': 'node_uuid',
            'method': 'method',
            'http_method': 'DELETE',
            }

        final_path = 'node_uuid/vendor_passthru/method'
        self.mgr.vendor_passthru(**kwargs)
        delete_mock.assert_called_once_with(final_path)

    @mock.patch.object(node.NodeManager, 'delete')
    def test_vendor_passthru_unknown_http_method(self, delete_mock):
        kwargs = {
            'node_id': 'node_uuid',
            'method': 'method',
            'http_method': 'UNKNOWN',
            }
        self.assertRaises(exc.InvalidAttribute, self.mgr.vendor_passthru,
                          **kwargs)

    def _test_node_set_boot_device(self, boot_device, persistent=False):
        self.mgr.set_boot_device(NODE1['uuid'], boot_device, persistent)
        body = {'boot_device': boot_device, 'persistent': persistent}
        expect = [
            ('PUT', '/v1/nodes/%s/management/boot_device' % NODE1['uuid'],
             {}, body),
        ]
        self.assertEqual(expect, self.api.calls)

    def test_node_set_boot_device(self):
        self._test_node_set_boot_device('pxe')

    def test_node_set_boot_device_persistent(self):
        self._test_node_set_boot_device('pxe', persistent=True)

    def test_node_get_boot_device(self):
        boot_device = self.mgr.get_boot_device(NODE1['uuid'])
        expect = [
            ('GET', '/v1/nodes/%s/management/boot_device' % NODE1['uuid'],
             {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(BOOT_DEVICE, boot_device)

    def test_node_get_supported_boot_devices(self):
        boot_device = self.mgr.get_supported_boot_devices(NODE1['uuid'])
        expect = [
            ('GET', '/v1/nodes/%s/management/boot_device/supported' %
             NODE1['uuid'], {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(SUPPORTED_BOOT_DEVICE, boot_device)
