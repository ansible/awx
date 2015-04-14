#
# Copyright 2013 Mirantis, Inc.
# Copyright 2013 OpenStack Foundation
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

from oslotest import base

from oslo_config import cfg
from oslo_config import fixture as config

conf = cfg.CONF


class ConfigTestCase(base.BaseTestCase):
    def setUp(self):
        super(ConfigTestCase, self).setUp()
        self.config_fixture = self.useFixture(config.Config(conf))
        self.config = self.config_fixture.config
        self.config_fixture.register_opt(cfg.StrOpt(
            'testing_option', default='initial_value'))

    def test_overridden_value(self):
        self.assertEqual(conf.get('testing_option'), 'initial_value')
        self.config(testing_option='changed_value')
        self.assertEqual(conf.get('testing_option'),
                         self.config_fixture.conf.get('testing_option'))

    def test_cleanup(self):
        self.config(testing_option='changed_value')
        self.assertEqual(self.config_fixture.conf.get('testing_option'),
                         'changed_value')
        self.config_fixture.conf.reset()
        self.assertEqual(conf.get('testing_option'), 'initial_value')

    def test_register_option(self):
        opt = cfg.StrOpt('new_test_opt', default='initial_value')
        self.config_fixture.register_opt(opt)
        self.assertEqual(conf.get('new_test_opt'),
                         opt.default)

    def test_register_options(self):
        opt1 = cfg.StrOpt('first_test_opt', default='initial_value_1')
        opt2 = cfg.StrOpt('second_test_opt', default='initial_value_2')
        self.config_fixture.register_opts([opt1, opt2])
        self.assertEqual(conf.get('first_test_opt'), opt1.default)
        self.assertEqual(conf.get('second_test_opt'), opt2.default)

    def test_cleanup_unregister_option(self):
        opt = cfg.StrOpt('new_test_opt', default='initial_value')
        self.config_fixture.register_opt(opt)
        self.assertEqual(conf.get('new_test_opt'),
                         opt.default)
        self.config_fixture.cleanUp()
        self.assertRaises(cfg.NoSuchOptError, conf.get, 'new_test_opt')

    def test_register_cli_option(self):
        opt = cfg.StrOpt('new_test_opt', default='initial_value')
        self.config_fixture.register_cli_opt(opt)
        self.assertEqual(conf.get('new_test_opt'),
                         opt.default)

    def test_register_cli_options(self):
        opt1 = cfg.StrOpt('first_test_opt', default='initial_value_1')
        opt2 = cfg.StrOpt('second_test_opt', default='initial_value_2')
        self.config_fixture.register_cli_opts([opt1, opt2])
        self.assertEqual(conf.get('first_test_opt'), opt1.default)
        self.assertEqual(conf.get('second_test_opt'), opt2.default)

    def test_cleanup_unregister_cli_option(self):
        opt = cfg.StrOpt('new_test_opt', default='initial_value')
        self.config_fixture.register_cli_opt(opt)
        self.assertEqual(conf.get('new_test_opt'),
                         opt.default)
        self.config_fixture.cleanUp()
        self.assertRaises(cfg.NoSuchOptError, conf.get, 'new_test_opt')
