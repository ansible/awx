# Copyright 2014 Red Hat, Inc.
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

from oslotest import base as test_base

from oslo_config import cfg
from oslo_config import cfgfilter


class BaseTestCase(test_base.BaseTestCase):

    def setUp(self, conf=None):
        super(BaseTestCase, self).setUp()
        if conf is None:
            self.conf = cfg.ConfigOpts()
        else:
            self.conf = conf
        self.fconf = cfgfilter.ConfigFilter(self.conf)


class RegisterTestCase(BaseTestCase):

    def test_register_opt_default(self):
        self.fconf.register_opt(cfg.StrOpt('foo', default='bar'))

        self.assertEqual('bar', self.fconf.foo)
        self.assertEqual('bar', self.fconf['foo'])
        self.assertIn('foo', self.fconf)
        self.assertEqual(['foo'], list(self.fconf))
        self.assertEqual(1, len(self.fconf))

        self.assertNotIn('foo', self.conf)
        self.assertEqual(0, len(self.conf))
        self.assertRaises(cfg.NoSuchOptError, getattr, self.conf, 'foo')

    def test_register_opt_none_default(self):
        self.fconf.register_opt(cfg.StrOpt('foo'))

        self.assertIsNone(self.fconf.foo)
        self.assertIsNone(self.fconf['foo'])
        self.assertIn('foo', self.fconf)
        self.assertEqual(['foo'], list(self.fconf))
        self.assertEqual(1, len(self.fconf))

        self.assertNotIn('foo', self.conf)
        self.assertEqual(0, len(self.conf))
        self.assertRaises(cfg.NoSuchOptError, getattr, self.conf, 'foo')

    def test_register_grouped_opt_default(self):
        self.fconf.register_opt(cfg.StrOpt('foo', default='bar'),
                                group='blaa')

        self.assertEqual('bar', self.fconf.blaa.foo)
        self.assertEqual('bar', self.fconf['blaa']['foo'])
        self.assertIn('blaa', self.fconf)
        self.assertIn('foo', self.fconf.blaa)
        self.assertEqual(['blaa'], list(self.fconf))
        self.assertEqual(['foo'], list(self.fconf.blaa))
        self.assertEqual(1, len(self.fconf))
        self.assertEqual(1, len(self.fconf.blaa))

        self.assertNotIn('blaa', self.conf)
        self.assertEqual(0, len(self.conf))
        self.assertRaises(cfg.NoSuchOptError, getattr, self.conf, 'blaa')

    def test_register_grouped_opt_none_default(self):
        self.fconf.register_opt(cfg.StrOpt('foo'), group='blaa')

        self.assertIsNone(self.fconf.blaa.foo)
        self.assertIsNone(self.fconf['blaa']['foo'])
        self.assertIn('blaa', self.fconf)
        self.assertIn('foo', self.fconf.blaa)
        self.assertEqual(['blaa'], list(self.fconf))
        self.assertEqual(['foo'], list(self.fconf.blaa))
        self.assertEqual(1, len(self.fconf))
        self.assertEqual(1, len(self.fconf.blaa))

        self.assertNotIn('blaa', self.conf)
        self.assertEqual(0, len(self.conf))
        self.assertRaises(cfg.NoSuchOptError, getattr, self.conf, 'blaa')

    def test_register_group(self):
        group = cfg.OptGroup('blaa')
        self.fconf.register_group(group)
        self.fconf.register_opt(cfg.StrOpt('foo'), group=group)

        self.assertIsNone(self.fconf.blaa.foo)
        self.assertIsNone(self.fconf['blaa']['foo'])
        self.assertIn('blaa', self.fconf)
        self.assertIn('foo', self.fconf.blaa)
        self.assertEqual(['blaa'], list(self.fconf))
        self.assertEqual(['foo'], list(self.fconf.blaa))
        self.assertEqual(1, len(self.fconf))
        self.assertEqual(1, len(self.fconf.blaa))

        self.assertNotIn('blaa', self.conf)
        self.assertEqual(0, len(self.conf))
        self.assertRaises(cfg.NoSuchOptError, getattr, self.conf, 'blaa')

    def test_register_opts(self):
        self.fconf.register_opts([cfg.StrOpt('foo'),
                                  cfg.StrOpt('bar')])
        self.assertIn('foo', self.fconf)
        self.assertIn('bar', self.fconf)
        self.assertNotIn('foo', self.conf)
        self.assertNotIn('bar', self.conf)

    def test_register_cli_opt(self):
        self.fconf.register_cli_opt(cfg.StrOpt('foo'))
        self.assertIn('foo', self.fconf)
        self.assertNotIn('foo', self.conf)

    def test_register_cli_opts(self):
        self.fconf.register_cli_opts([cfg.StrOpt('foo'), cfg.StrOpt('bar')])
        self.assertIn('foo', self.fconf)
        self.assertIn('bar', self.fconf)
        self.assertNotIn('foo', self.conf)
        self.assertNotIn('bar', self.conf)

    def test_register_opts_grouped(self):
        self.fconf.register_opts([cfg.StrOpt('foo'), cfg.StrOpt('bar')],
                                 group='blaa')
        self.assertIn('foo', self.fconf.blaa)
        self.assertIn('bar', self.fconf.blaa)
        self.assertNotIn('blaa', self.conf)

    def test_register_cli_opt_grouped(self):
        self.fconf.register_cli_opt(cfg.StrOpt('foo'), group='blaa')
        self.assertIn('foo', self.fconf.blaa)
        self.assertNotIn('blaa', self.conf)

    def test_register_cli_opts_grouped(self):
        self.fconf.register_cli_opts([cfg.StrOpt('foo'), cfg.StrOpt('bar')],
                                     group='blaa')
        self.assertIn('foo', self.fconf.blaa)
        self.assertIn('bar', self.fconf.blaa)
        self.assertNotIn('blaa', self.conf)

    def test_unknown_opt(self):
        self.assertNotIn('foo', self.fconf)
        self.assertEqual(0, len(self.fconf))
        self.assertRaises(cfg.NoSuchOptError, getattr, self.fconf, 'foo')
        self.assertNotIn('blaa', self.conf)

    def test_blocked_opt(self):
        self.conf.register_opt(cfg.StrOpt('foo'))

        self.assertIn('foo', self.conf)
        self.assertEqual(1, len(self.conf))
        self.assertIsNone(self.conf.foo)
        self.assertNotIn('foo', self.fconf)
        self.assertEqual(0, len(self.fconf))
        self.assertRaises(cfg.NoSuchOptError, getattr, self.fconf, 'foo')

    def test_already_registered_opt(self):
        self.conf.register_opt(cfg.StrOpt('foo'))
        self.fconf.register_opt(cfg.StrOpt('foo'))

        self.assertIn('foo', self.conf)
        self.assertEqual(1, len(self.conf))
        self.assertIsNone(self.conf.foo)
        self.assertIn('foo', self.fconf)
        self.assertEqual(1, len(self.fconf))
        self.assertIsNone(self.fconf.foo)

        self.conf.set_override('foo', 'bar')

        self.assertEqual('bar', self.conf.foo)
        self.assertEqual('bar', self.fconf.foo)

    def test_already_registered_opts(self):
        self.conf.register_opts([cfg.StrOpt('foo'),
                                 cfg.StrOpt('fu')])
        self.fconf.register_opts([cfg.StrOpt('foo'),
                                  cfg.StrOpt('bu')])

        self.assertIn('foo', self.conf)
        self.assertIn('fu', self.conf)
        self.assertNotIn('bu', self.conf)
        self.assertEqual(2, len(self.conf))
        self.assertIsNone(self.conf.foo)
        self.assertIsNone(self.conf.fu)
        self.assertIn('foo', self.fconf)
        self.assertIn('bu', self.fconf)
        self.assertNotIn('fu', self.fconf)
        self.assertEqual(2, len(self.fconf))
        self.assertIsNone(self.fconf.foo)
        self.assertIsNone(self.fconf.bu)

        self.conf.set_override('foo', 'bar')

        self.assertEqual('bar', self.conf.foo)
        self.assertEqual('bar', self.fconf.foo)

    def test_already_registered_cli_opt(self):
        self.conf.register_cli_opt(cfg.StrOpt('foo'))
        self.fconf.register_cli_opt(cfg.StrOpt('foo'))

        self.assertIn('foo', self.conf)
        self.assertEqual(1, len(self.conf))
        self.assertIsNone(self.conf.foo)
        self.assertIn('foo', self.fconf)
        self.assertEqual(1, len(self.fconf))
        self.assertIsNone(self.fconf.foo)

        self.conf.set_override('foo', 'bar')

        self.assertEqual('bar', self.conf.foo)
        self.assertEqual('bar', self.fconf.foo)

    def test_already_registered_cli_opts(self):
        self.conf.register_cli_opts([cfg.StrOpt('foo'),
                                     cfg.StrOpt('fu')])
        self.fconf.register_cli_opts([cfg.StrOpt('foo'),
                                      cfg.StrOpt('bu')])

        self.assertIn('foo', self.conf)
        self.assertIn('fu', self.conf)
        self.assertNotIn('bu', self.conf)
        self.assertEqual(2, len(self.conf))
        self.assertIsNone(self.conf.foo)
        self.assertIsNone(self.conf.fu)
        self.assertIn('foo', self.fconf)
        self.assertIn('bu', self.fconf)
        self.assertNotIn('fu', self.fconf)
        self.assertEqual(2, len(self.fconf))
        self.assertIsNone(self.fconf.foo)
        self.assertIsNone(self.fconf.bu)

        self.conf.set_override('foo', 'bar')

        self.assertEqual('bar', self.conf.foo)
        self.assertEqual('bar', self.fconf.foo)


class ImportTestCase(BaseTestCase):

    def setUp(self):
        super(ImportTestCase, self).setUp(cfg.CONF)

    def test_import_opt(self):
        self.assertFalse(hasattr(self.conf, 'fblaa'))
        self.conf.import_opt('fblaa', 'tests.testmods.fblaa_opt')
        self.assertTrue(hasattr(self.conf, 'fblaa'))
        self.assertFalse(hasattr(self.fconf, 'fblaa'))
        self.fconf.import_opt('fblaa', 'tests.testmods.fblaa_opt')
        self.assertTrue(hasattr(self.fconf, 'fblaa'))

    def test_import_opt_in_group(self):
        self.assertFalse(hasattr(self.conf, 'fbar'))
        self.conf.import_opt('foo', 'tests.testmods.fbar_foo_opt',
                             group='fbar')
        self.assertTrue(hasattr(self.conf, 'fbar'))
        self.assertTrue(hasattr(self.conf.fbar, 'foo'))
        self.assertFalse(hasattr(self.fconf, 'fbar'))
        self.fconf.import_opt('foo', 'tests.testmods.fbar_foo_opt',
                              group='fbar')
        self.assertTrue(hasattr(self.fconf, 'fbar'))
        self.assertTrue(hasattr(self.fconf.fbar, 'foo'))

    def test_import_group(self):
        self.assertFalse(hasattr(self.conf, 'fbaar'))
        self.conf.import_group('fbaar', 'tests.testmods.fbaar_baa_opt')
        self.assertTrue(hasattr(self.conf, 'fbaar'))
        self.assertTrue(hasattr(self.conf.fbaar, 'baa'))
        self.assertFalse(hasattr(self.fconf, 'fbaar'))
        self.fconf.import_group('fbaar', 'tests.testmods.fbaar_baa_opt')
        self.assertTrue(hasattr(self.fconf, 'fbaar'))
        self.assertTrue(hasattr(self.fconf.fbaar, 'baa'))


class ExposeTestCase(BaseTestCase):

    def test_expose_opt(self):
        self.assertFalse(hasattr(self.conf, 'foo'))
        self.assertFalse(hasattr(self.fconf, 'foo'))

        self.conf.register_opt(cfg.StrOpt('foo'))
        self.conf.set_override('foo', 'bar')

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, 'bar')
        self.assertFalse(hasattr(self.fconf, 'foo'))

        self.fconf.expose_opt('foo')
        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertTrue(hasattr(self.fconf, 'foo'))
        self.assertEqual(self.fconf.foo, 'bar')

    def test_expose_opt_with_group(self):
        self.assertFalse(hasattr(self.conf, 'foo'))
        self.assertFalse(hasattr(self.fconf, 'foo'))

        self.conf.register_opt(cfg.StrOpt('foo'), group='group')
        self.conf.set_override('foo', 'bar', group='group')

        self.assertTrue(hasattr(self.conf.group, 'foo'))
        self.assertEqual(self.conf.group.foo, 'bar')
        self.assertFalse(hasattr(self.fconf, 'group'))

        self.fconf.expose_opt('foo', group='group')
        self.assertTrue(hasattr(self.conf.group, 'foo'))
        self.assertTrue(hasattr(self.fconf.group, 'foo'))
        self.assertEqual(self.fconf.group.foo, 'bar')

    def test_expose_group(self):
        self.conf.register_opts([cfg.StrOpt('foo'),
                                 cfg.StrOpt('bar')], group='group')
        self.conf.register_opts([cfg.StrOpt('foo'),
                                 cfg.StrOpt('bar')], group='another')
        self.conf.set_override('foo', 'a', group='group')
        self.conf.set_override('bar', 'b', group='group')

        self.fconf.expose_group('group')

        self.assertEqual('a', self.fconf.group.foo)
        self.assertEqual('b', self.fconf.group.bar)
        self.assertFalse(hasattr(self.fconf, 'another'))
        self.assertTrue(hasattr(self.conf, 'another'))
