# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import tempfile

import extras
import fixtures
import testtools
import yaml

from os_client_config import cloud_config
from os_client_config import config

VENDOR_CONF = {
    'public-clouds': {
        '_test_cloud_in_our_cloud': {
            'auth': {
                'username': 'testotheruser',
                'project_name': 'testproject',
            },
        },
    }
}
USER_CONF = {
    'clouds': {
        '_test_cloud_': {
            'cloud': '_test_cloud_in_our_cloud',
            'auth': {
                'username': 'testuser',
                'password': 'testpass',
            },
            'region_name': 'test-region',
        },
        '_test_cloud_no_vendor': {
            'cloud': '_test_non_existant_cloud',
            'auth': {
                'username': 'testuser',
                'password': 'testpass',
                'project_name': 'testproject',
            },
            'region_name': 'test-region',
        },
    },
    'cache': {'max_age': 1},
}


def _write_yaml(obj):
    # Assume NestedTempfile so we don't have to cleanup
    with tempfile.NamedTemporaryFile(delete=False) as obj_yaml:
        obj_yaml.write(yaml.safe_dump(obj).encode('utf-8'))
        return obj_yaml.name


class TestConfig(testtools.TestCase):
    def setUp(self):
        super(TestConfig, self).setUp()
        self.useFixture(fixtures.NestedTempfile())
        conf = dict(USER_CONF)
        tdir = self.useFixture(fixtures.TempDir())
        conf['cache']['path'] = tdir.path
        self.cloud_yaml = _write_yaml(conf)
        self.vendor_yaml = _write_yaml(VENDOR_CONF)

    def test_get_one_cloud(self):
        c = config.OpenStackConfig(config_files=[self.cloud_yaml],
                                   vendor_files=[self.vendor_yaml])
        self.assertIsInstance(c.get_one_cloud(), cloud_config.CloudConfig)

    def test_get_one_cloud_with_config_files(self):
        c = config.OpenStackConfig(config_files=[self.cloud_yaml],
                                   vendor_files=[self.vendor_yaml])
        self.assertIsInstance(c.cloud_config, dict)
        self.assertIn('cache', c.cloud_config)
        self.assertIsInstance(c.cloud_config['cache'], dict)
        self.assertIn('max_age', c.cloud_config['cache'])
        self.assertIn('path', c.cloud_config['cache'])
        cc = c.get_one_cloud('_test_cloud_')
        self._assert_cloud_details(cc)
        cc = c.get_one_cloud('_test_cloud_no_vendor')
        self._assert_cloud_details(cc)

    def _assert_cloud_details(self, cc):
        self.assertIsInstance(cc, cloud_config.CloudConfig)
        self.assertTrue(extras.safe_hasattr(cc, 'auth'))
        self.assertIsInstance(cc.auth, dict)
        self.assertIsNone(cc.cloud)
        self.assertIn('username', cc.auth)
        self.assertEqual('testuser', cc.auth['username'])
        self.assertEqual('testproject', cc.auth['project_name'])
