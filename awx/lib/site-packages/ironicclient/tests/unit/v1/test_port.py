# -*- coding: utf-8 -*-

# Copyright 2013 Red Hat, Inc.
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

import copy

import testtools
from testtools.matchers import HasLength

from ironicclient.tests.unit import utils
import ironicclient.v1.port

PORT = {'id': 987,
        'uuid': '11111111-2222-3333-4444-555555555555',
        'node_uuid': '55555555-4444-3333-2222-111111111111',
        'address': 'AA:BB:CC:DD:EE:FF',
        'extra': {}}

PORT2 = {'id': 988,
         'uuid': '55555555-4444-3333-2222-111111111111',
         'node_uuid': '55555555-4444-3333-2222-111111111111',
         'address': 'AA:AA:AA:BB:BB:BB',
         'extra': {}}

CREATE_PORT = copy.deepcopy(PORT)
del CREATE_PORT['id']
del CREATE_PORT['uuid']

UPDATED_PORT = copy.deepcopy(PORT)
NEW_ADDR = 'AA:AA:AA:AA:AA:AA'
UPDATED_PORT['address'] = NEW_ADDR

fake_responses = {
    '/v1/ports':
    {
        'GET': (
            {},
            {"ports": [PORT]},
        ),
        'POST': (
            {},
            CREATE_PORT,
        ),
    },
    '/v1/ports/detail':
    {
        'GET': (
            {},
            {"ports": [PORT]},
        ),
    },
    '/v1/ports/%s' % PORT['uuid']:
    {
        'GET': (
            {},
            PORT,
        ),
        'DELETE': (
            {},
            None,
        ),
        'PATCH': (
            {},
            UPDATED_PORT,
        ),
    },
    '/v1/ports/detail?address=%s' % PORT['address']:
    {
        'GET': (
            {},
            {"ports": [PORT]},
        ),
    },
    '/v1/ports/?address=%s' % PORT['address']:
    {
        'GET': (
            {},
            {"ports": [PORT]},
        ),
    }
}

fake_responses_pagination = {
    '/v1/ports':
    {
        'GET': (
            {},
            {"ports": [PORT],
             "next": "http://127.0.0.1:6385/v1/ports/?limit=1"}
        ),
    },
    '/v1/ports/?limit=1':
    {
        'GET': (
            {},
            {"ports": [PORT2]}
        ),
    },
    '/v1/ports/?marker=%s' % PORT['uuid']:
    {
        'GET': (
            {},
            {"ports": [PORT2]}
        ),
    },
}

fake_responses_sorting = {
    '/v1/ports/?sort_key=updated_at':
    {
        'GET': (
            {},
            {"ports": [PORT2, PORT]}
        ),
    },
    '/v1/ports/?sort_dir=desc':
    {
        'GET': (
            {},
            {"ports": [PORT2, PORT]}
        ),
    },
}


class PortManagerTest(testtools.TestCase):

    def setUp(self):
        super(PortManagerTest, self).setUp()
        self.api = utils.FakeAPI(fake_responses)
        self.mgr = ironicclient.v1.port.PortManager(self.api)

    def test_ports_list(self):
        ports = self.mgr.list()
        expect = [
            ('GET', '/v1/ports', {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(1, len(ports))

    def test_ports_list_by_address(self):
        ports = self.mgr.list(address=PORT['address'])
        expect = [
            ('GET', '/v1/ports/?address=%s' % PORT['address'], {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(1, len(ports))

    def test_ports_list_by_address_detail(self):
        ports = self.mgr.list(address=PORT['address'], detail=True)
        expect = [
            ('GET', '/v1/ports/detail?address=%s' % PORT['address'], {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(1, len(ports))

    def test_ports_list_detail(self):
        ports = self.mgr.list(detail=True)
        expect = [
            ('GET', '/v1/ports/detail', {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(1, len(ports))

    def test_ports_list_limit(self):
        self.api = utils.FakeAPI(fake_responses_pagination)
        self.mgr = ironicclient.v1.port.PortManager(self.api)
        ports = self.mgr.list(limit=1)
        expect = [
            ('GET', '/v1/ports/?limit=1', {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertThat(ports, HasLength(1))

    def test_ports_list_marker(self):
        self.api = utils.FakeAPI(fake_responses_pagination)
        self.mgr = ironicclient.v1.port.PortManager(self.api)
        ports = self.mgr.list(marker=PORT['uuid'])
        expect = [
            ('GET', '/v1/ports/?marker=%s' % PORT['uuid'], {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertThat(ports, HasLength(1))

    def test_ports_list_pagination_no_limit(self):
        self.api = utils.FakeAPI(fake_responses_pagination)
        self.mgr = ironicclient.v1.port.PortManager(self.api)
        ports = self.mgr.list(limit=0)
        expect = [
            ('GET', '/v1/ports', {}, None),
            ('GET', '/v1/ports/?limit=1', {}, None)
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertThat(ports, HasLength(2))

    def test_ports_list_sort_key(self):
        self.api = utils.FakeAPI(fake_responses_sorting)
        self.mgr = ironicclient.v1.port.PortManager(self.api)
        ports = self.mgr.list(sort_key='updated_at')
        expect = [
            ('GET', '/v1/ports/?sort_key=updated_at', {}, None)
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(2, len(ports))

    def test_ports_list_sort_dir(self):
        self.api = utils.FakeAPI(fake_responses_sorting)
        self.mgr = ironicclient.v1.port.PortManager(self.api)
        ports = self.mgr.list(sort_dir='desc')
        expect = [
            ('GET', '/v1/ports/?sort_dir=desc', {}, None)
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(2, len(ports))

    def test_ports_show(self):
        port = self.mgr.get(PORT['uuid'])
        expect = [
            ('GET', '/v1/ports/%s' % PORT['uuid'], {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(PORT['uuid'], port.uuid)
        self.assertEqual(PORT['address'], port.address)
        self.assertEqual(PORT['node_uuid'], port.node_uuid)

    def test_ports_show_by_address(self):
        port = self.mgr.get_by_address(PORT['address'])
        expect = [
            ('GET', '/v1/ports/detail?address=%s' % PORT['address'],
             {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(PORT['uuid'], port.uuid)
        self.assertEqual(PORT['address'], port.address)
        self.assertEqual(PORT['node_uuid'], port.node_uuid)

    def test_create(self):
        port = self.mgr.create(**CREATE_PORT)
        expect = [
            ('POST', '/v1/ports', {}, CREATE_PORT),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertTrue(port)

    def test_delete(self):
        port = self.mgr.delete(port_id=PORT['uuid'])
        expect = [
            ('DELETE', '/v1/ports/%s' % PORT['uuid'], {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertIsNone(port)

    def test_update(self):
        patch = {'op': 'replace',
                 'value': NEW_ADDR,
                 'path': '/address'}
        port = self.mgr.update(port_id=PORT['uuid'], patch=patch)
        expect = [
            ('PATCH', '/v1/ports/%s' % PORT['uuid'], {}, patch),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(NEW_ADDR, port.address)
