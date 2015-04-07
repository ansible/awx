# -*- coding: utf-8 -*-
#
# Copyright 2015 Hewlett-Packard Development Company, L.P.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import ConfigParser
import os

import testtools

import ironicclient
from ironicclient import exc

DEFAULT_CONFIG = os.path.join(os.path.dirname(__file__), 'test.conf')


class TestIronicClient(testtools.TestCase):
    def setUp(self):
        super(TestIronicClient, self).setUp()
        self.client = ironicclient.client.get_client(**self._get_config())

    def _get_config(self):
        config_file = os.environ.get('IRONICCLIENT_TEST_CONFIG',
                                     DEFAULT_CONFIG)
        config = ConfigParser.SafeConfigParser()
        if not config.read(config_file):
            self.skipTest('Skipping, no test config found @ %s' % config_file)
        try:
            auth_strategy = config.get('functional', 'auth_strategy')
        except ConfigParser.NoOptionError:
            auth_strategy = 'keystone'
        if auth_strategy not in ['keystone', 'noauth']:
            raise self.fail(
                'Invalid auth type specified in functional must be one of: '
                'keystone, noauth')
        out = {}
        conf_settings = ['api_version']
        if auth_strategy == 'keystone':
            conf_settings += ['os_auth_url', 'os_username',
                              'os_password', 'os_tenant_name']

        else:
            conf_settings += ['os_auth_token', 'ironic_url']

        for c in conf_settings:
            try:
                out[c] = config.get('functional', c)
            except ConfigParser.NoOptionError:
                out[c] = None
        missing = [k for k, v in out.items() if not v]
        if missing:
                self.fail('Missing required setting in test.conf (%s) for '
                          'auth_strategy=%s: %s' %
                          (config_file, auth_strategy, ','.join(missing)))
        return out

    def _try_delete_resource(self, resource, id):
        mgr = getattr(self.client, resource)
        try:
            mgr.delete(id)
        except exc.NotFound:
            pass

    def _create_node(self, **kwargs):
        if 'driver' not in kwargs:
            kwargs['driver'] = 'fake'
        node = self.client.node.create(**kwargs)
        self.addCleanup(self._try_delete_resource, 'node', node.uuid)
        return node

    def test_node_list(self):
        self.assertTrue(isinstance(self.client.node.list(), list))

    def test_node_create_get_delete(self):
        node = self._create_node()
        self.assertTrue(isinstance(node, ironicclient.v1.node.Node))
        got = self.client.node.get(node.uuid)
        self.assertTrue(isinstance(got, ironicclient.v1.node.Node))
        self.client.node.delete(node.uuid)
        self.assertRaises(exc.NotFound, self.client.node.get, node.uuid)
