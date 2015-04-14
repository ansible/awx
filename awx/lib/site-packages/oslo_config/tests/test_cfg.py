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

import argparse
import errno
import functools
import os
import shutil
import sys
import tempfile

import fixtures
import mock
from oslotest import base
import six
from six import moves
import testscenarios

from oslo_config import cfg
from oslo_config import types

load_tests = testscenarios.load_tests_apply_scenarios


class ExceptionsTestCase(base.BaseTestCase):

    def test_error(self):
        msg = str(cfg.Error('foobar'))
        self.assertEqual(msg, 'foobar')

    def test_args_already_parsed_error(self):
        msg = str(cfg.ArgsAlreadyParsedError('foobar'))
        self.assertEqual(msg, 'arguments already parsed: foobar')

    def test_no_such_opt_error(self):
        msg = str(cfg.NoSuchOptError('foo'))
        self.assertEqual(msg, 'no such option: foo')

    def test_no_such_opt_error_with_group(self):
        msg = str(cfg.NoSuchOptError('foo', cfg.OptGroup('bar')))
        self.assertEqual(msg, 'no such option in group bar: foo')

    def test_no_such_group_error(self):
        msg = str(cfg.NoSuchGroupError('bar'))
        self.assertEqual(msg, 'no such group: bar')

    def test_duplicate_opt_error(self):
        msg = str(cfg.DuplicateOptError('foo'))
        self.assertEqual(msg, 'duplicate option: foo')

    def test_required_opt_error(self):
        msg = str(cfg.RequiredOptError('foo'))
        self.assertEqual(msg, 'value required for option: foo')

    def test_required_opt_error_with_group(self):
        msg = str(cfg.RequiredOptError('foo', cfg.OptGroup('bar')))
        self.assertEqual(msg, 'value required for option: bar.foo')

    def test_template_substitution_error(self):
        msg = str(cfg.TemplateSubstitutionError('foobar'))
        self.assertEqual(msg, 'template substitution error: foobar')

    def test_config_files_not_found_error(self):
        msg = str(cfg.ConfigFilesNotFoundError(['foo', 'bar']))
        self.assertEqual(msg, 'Failed to find some config files: foo,bar')

    def test_config_files_permission_denied_error(self):
        msg = str(cfg.ConfigFilesPermissionDeniedError(['foo', 'bar']))
        self.assertEqual(msg, 'Failed to open some config files: foo,bar')

    def test_config_dir_not_found_error(self):
        msg = str(cfg.ConfigDirNotFoundError('foobar'))
        self.assertEqual(msg, 'Failed to read config file directory: foobar')

    def test_config_file_parse_error(self):
        msg = str(cfg.ConfigFileParseError('foo', 'foobar'))
        self.assertEqual(msg, 'Failed to parse foo: foobar')


class BaseTestCase(base.BaseTestCase):

    class TestConfigOpts(cfg.ConfigOpts):
        def __call__(self, args=None, default_config_files=[]):
            return cfg.ConfigOpts.__call__(
                self,
                args=args,
                prog='test',
                version='1.0',
                usage='%(prog)s FOO BAR',
                default_config_files=default_config_files,
                validate_default_values=True)

    def setUp(self):
        super(BaseTestCase, self).setUp()
        self.useFixture(fixtures.NestedTempfile())
        self.conf = self.TestConfigOpts()

        self.tempdirs = []

    def create_tempfiles(self, files, ext='.conf'):
        tempfiles = []
        for (basename, contents) in files:
            if not os.path.isabs(basename):
                (fd, path) = tempfile.mkstemp(prefix=basename, suffix=ext)
            else:
                path = basename + ext
                fd = os.open(path, os.O_CREAT | os.O_WRONLY)
            tempfiles.append(path)
            try:
                os.write(fd, contents.encode('utf-8'))
            finally:
                os.close(fd)
        return tempfiles


class UsageTestCase(BaseTestCase):

    def test_print_usage(self):
        f = moves.StringIO()
        self.conf([])
        self.conf.print_usage(file=f)
        self.assertTrue('usage: test FOO BAR' in f.getvalue())
        self.assertTrue('optional:' not in f.getvalue())


class HelpTestCase(BaseTestCase):

    def test_print_help(self):
        f = moves.StringIO()
        self.conf([])
        self.conf.print_help(file=f)
        self.assertTrue('usage: test FOO BAR' in f.getvalue())
        self.assertTrue('optional' in f.getvalue())
        self.assertTrue('-h, --help' in f.getvalue())

    def test_print_sorted_help(self):
        f = moves.StringIO()
        self.conf.register_cli_opt(cfg.StrOpt('zba'))
        self.conf.register_cli_opt(cfg.StrOpt('abc'))
        self.conf.register_cli_opt(cfg.StrOpt('ghi'))
        self.conf.register_cli_opt(cfg.StrOpt('deb'))
        self.conf([])
        self.conf.print_help(file=f)
        zba = f.getvalue().find('--zba')
        abc = f.getvalue().find('--abc')
        ghi = f.getvalue().find('--ghi')
        deb = f.getvalue().find('--deb')
        list = [abc, deb, ghi, zba]
        self.assertEqual(sorted(list), list)


class FindConfigFilesTestCase(BaseTestCase):

    def test_find_config_files(self):
        config_files = [os.path.expanduser('~/.blaa/blaa.conf'),
                        '/etc/foo.conf']

        self.useFixture(fixtures.MonkeyPatch('sys.argv', ['foo']))
        self.useFixture(fixtures.MonkeyPatch('os.path.exists',
                        lambda p: p in config_files))

        self.assertEqual(cfg.find_config_files(project='blaa'), config_files)

    def test_find_config_files_with_extension(self):
        config_files = ['/etc/foo.json']

        self.useFixture(fixtures.MonkeyPatch('sys.argv', ['foo']))
        self.useFixture(fixtures.MonkeyPatch('os.path.exists',
                        lambda p: p in config_files))

        self.assertEqual(cfg.find_config_files(project='blaa'), [])
        self.assertEqual(cfg.find_config_files(project='blaa',
                                               extension='.json'),
                         config_files)


class DefaultConfigFilesTestCase(BaseTestCase):

    def test_use_default(self):
        self.conf.register_opt(cfg.StrOpt('foo'))
        paths = self.create_tempfiles([('foo-', '[DEFAULT]\n''foo = bar\n')])

        self.conf.register_cli_opt(cfg.StrOpt('config-file-foo'))
        self.conf(args=['--config-file-foo', 'foo.conf'],
                  default_config_files=[paths[0]])

        self.assertEqual(self.conf.config_file, [paths[0]])
        self.assertEqual(self.conf.foo, 'bar')

    def test_do_not_use_default_multi_arg(self):
        self.conf.register_opt(cfg.StrOpt('foo'))
        paths = self.create_tempfiles([('foo-', '[DEFAULT]\n''foo = bar\n')])

        self.conf(args=['--config-file', paths[0]],
                  default_config_files=['bar.conf'])

        self.assertEqual(self.conf.config_file, [paths[0]])
        self.assertEqual(self.conf.foo, 'bar')

    def test_do_not_use_default_single_arg(self):
        self.conf.register_opt(cfg.StrOpt('foo'))
        paths = self.create_tempfiles([('foo-', '[DEFAULT]\n''foo = bar\n')])

        self.conf(args=['--config-file=' + paths[0]],
                  default_config_files=['bar.conf'])

        self.assertEqual(self.conf.config_file, [paths[0]])
        self.assertEqual(self.conf.foo, 'bar')

    def test_no_default_config_file(self):
        self.conf(args=[])
        self.assertEqual(self.conf.config_file, [])

    def test_find_default_config_file(self):
        paths = self.create_tempfiles([('def', '[DEFAULT]')])

        self.useFixture(fixtures.MonkeyPatch(
                        'oslo_config.cfg.find_config_files',
                        lambda project, prog: paths))

        self.conf(args=[], default_config_files=None)
        self.assertEqual(self.conf.config_file, paths)

    def test_default_config_file(self):
        paths = self.create_tempfiles([('def', '[DEFAULT]')])

        self.conf(args=[], default_config_files=paths)

        self.assertEqual(self.conf.config_file, paths)

    def test_default_config_file_with_value(self):
        self.conf.register_cli_opt(cfg.StrOpt('foo'))

        paths = self.create_tempfiles([('def', '[DEFAULT]\n''foo = bar\n')])

        self.conf(args=[], default_config_files=paths)

        self.assertEqual(self.conf.config_file, paths)
        self.assertEqual(self.conf.foo, 'bar')

    def test_default_config_file_priority(self):
        self.conf.register_cli_opt(cfg.StrOpt('foo'))

        paths = self.create_tempfiles([('def', '[DEFAULT]\n''foo = bar\n')])

        self.conf(args=['--foo=blaa'], default_config_files=paths)

        self.assertEqual(self.conf.config_file, paths)
        self.assertEqual(self.conf.foo, 'blaa')


class CliOptsTestCase(BaseTestCase):
    """Test CLI Options.

    Each test scenario takes a name for the scenarios, as well as a dict:
    opt_class - class of the type of option that should be tested
    default - a default value for the option
    cli_args - a list containing a representation of an input command line
    value - the result value that is expected to be found
    deps - a tuple of deprecated name/group
    """

    IPv4Opt = functools.partial(cfg.IPOpt, version=4)
    IPv6Opt = functools.partial(cfg.IPOpt, version=6)

    multi_int = functools.partial(cfg.MultiOpt, item_type=types.Integer())
    multi_float = functools.partial(cfg.MultiOpt, item_type=types.Float())
    multi_string = functools.partial(cfg.MultiOpt, item_type=types.String())

    scenarios = [
        ('str_default',
         dict(opt_class=cfg.StrOpt, default=None, cli_args=[], value=None,
              deps=(None, None))),
        ('str_arg',
         dict(opt_class=cfg.StrOpt, default=None, cli_args=['--foo', 'bar'],
              value='bar', deps=(None, None))),
        ('str_arg_deprecated_name',
         dict(opt_class=cfg.StrOpt, default=None,
              cli_args=['--oldfoo', 'bar'], value='bar',
              deps=('oldfoo', None))),
        ('str_arg_deprecated_group',
         dict(opt_class=cfg.StrOpt, default=None,
              cli_args=['--old-foo', 'bar'], value='bar',
              deps=(None, 'old'))),
        ('str_arg_deprecated_group_default',
         dict(opt_class=cfg.StrOpt, default=None, cli_args=['--foo', 'bar'],
              value='bar', deps=(None, 'DEFAULT'))),
        ('str_arg_deprecated_group_and_name',
         dict(opt_class=cfg.StrOpt, default=None,
              cli_args=['--old-oof', 'bar'], value='bar',
              deps=('oof', 'old'))),
        ('bool_default',
         dict(opt_class=cfg.BoolOpt, default=False,
              cli_args=[], value=False, deps=(None, None))),
        ('bool_arg',
         dict(opt_class=cfg.BoolOpt, default=None,
              cli_args=['--foo'], value=True, deps=(None, None))),
        ('bool_arg_deprecated_name',
         dict(opt_class=cfg.BoolOpt, default=None,
              cli_args=['--oldfoo'], value=True,
              deps=('oldfoo', None))),
        ('bool_arg_deprecated_group',
         dict(opt_class=cfg.BoolOpt, default=None,
              cli_args=['--old-foo'], value=True,
              deps=(None, 'old'))),
        ('bool_arg_deprecated_group_default',
         dict(opt_class=cfg.BoolOpt, default=None,
              cli_args=['--foo'], value=True,
              deps=(None, 'DEFAULT'))),
        ('bool_arg_deprecated_group_and_name',
         dict(opt_class=cfg.BoolOpt, default=None,
              cli_args=['--old-oof'], value=True,
              deps=('oof', 'old'))),
        ('bool_arg_inverse',
         dict(opt_class=cfg.BoolOpt, default=None,
              cli_args=['--foo', '--nofoo'], value=False, deps=(None, None))),
        ('bool_arg_inverse_deprecated_name',
         dict(opt_class=cfg.BoolOpt, default=None,
              cli_args=['--oldfoo', '--nooldfoo'], value=False,
              deps=('oldfoo', None))),
        ('bool_arg_inverse_deprecated_group',
         dict(opt_class=cfg.BoolOpt, default=None,
              cli_args=['--old-foo', '--old-nofoo'], value=False,
              deps=(None, 'old'))),
        ('bool_arg_inverse_deprecated_group_default',
         dict(opt_class=cfg.BoolOpt, default=None,
              cli_args=['--foo', '--nofoo'], value=False,
              deps=(None, 'DEFAULT'))),
        ('bool_arg_inverse_deprecated_group_and_name',
         dict(opt_class=cfg.BoolOpt, default=None,
              cli_args=['--old-oof', '--old-nooof'], value=False,
              deps=('oof', 'old'))),
        ('int_default',
         dict(opt_class=cfg.IntOpt, default=10,
              cli_args=[], value=10, deps=(None, None))),
        ('int_arg',
         dict(opt_class=cfg.IntOpt, default=None,
              cli_args=['--foo=20'], value=20, deps=(None, None))),
        ('int_arg_deprecated_name',
         dict(opt_class=cfg.IntOpt, default=None,
              cli_args=['--oldfoo=20'], value=20, deps=('oldfoo', None))),
        ('int_arg_deprecated_group',
         dict(opt_class=cfg.IntOpt, default=None,
              cli_args=['--old-foo=20'], value=20, deps=(None, 'old'))),
        ('int_arg_deprecated_group_default',
         dict(opt_class=cfg.IntOpt, default=None,
              cli_args=['--foo=20'], value=20, deps=(None, 'DEFAULT'))),
        ('int_arg_deprecated_group_and_name',
         dict(opt_class=cfg.IntOpt, default=None,
              cli_args=['--old-oof=20'], value=20, deps=('oof', 'old'))),
        ('float_default',
         dict(opt_class=cfg.FloatOpt, default=1.0,
              cli_args=[], value=1.0, deps=(None, None))),
        ('float_arg',
         dict(opt_class=cfg.FloatOpt, default=None,
              cli_args=['--foo', '2.0'], value=2.0, deps=(None, None))),
        ('float_arg_deprecated_name',
         dict(opt_class=cfg.FloatOpt, default=None,
              cli_args=['--oldfoo', '2.0'], value=2.0, deps=('oldfoo', None))),
        ('float_arg_deprecated_group',
         dict(opt_class=cfg.FloatOpt, default=None,
              cli_args=['--old-foo', '2.0'], value=2.0, deps=(None, 'old'))),
        ('float_arg_deprecated_group_default',
         dict(opt_class=cfg.FloatOpt, default=None,
              cli_args=['--foo', '2.0'], value=2.0, deps=(None, 'DEFAULT'))),
        ('float_arg_deprecated_group_and_name',
         dict(opt_class=cfg.FloatOpt, default=None,
              cli_args=['--old-oof', '2.0'], value=2.0, deps=('oof', 'old'))),
        ('float_default_as_integer',
         dict(opt_class=cfg.FloatOpt, default=2,
              cli_args=['--old-oof', '2.0'], value=2.0, deps=('oof', 'old'))),
        ('ipv4addr_arg',
         dict(opt_class=IPv4Opt, default=None,
              cli_args=['--foo', '192.168.0.1'], value='192.168.0.1',
              deps=(None, None))),
        ('ipaddr_arg_implicitv4',
         dict(opt_class=cfg.IPOpt, default=None,
              cli_args=['--foo', '192.168.0.1'], value='192.168.0.1',
              deps=(None, None))),
        ('ipaddr_arg_implicitv6',
         dict(opt_class=cfg.IPOpt, default=None,
              cli_args=['--foo', 'abcd:ef::1'], value='abcd:ef::1',
              deps=(None, None))),
        ('ipv6addr_arg',
         dict(opt_class=IPv6Opt, default=None,
              cli_args=['--foo', 'abcd:ef::1'], value='abcd:ef::1',
              deps=(None, None))),
        ('list_default',
         dict(opt_class=cfg.ListOpt, default=['bar'],
              cli_args=[], value=['bar'], deps=(None, None))),
        ('list_arg',
         dict(opt_class=cfg.ListOpt, default=None,
              cli_args=['--foo', 'blaa,bar'], value=['blaa', 'bar'],
              deps=(None, None))),
        ('list_arg_with_spaces',
         dict(opt_class=cfg.ListOpt, default=None,
              cli_args=['--foo', 'blaa ,bar'], value=['blaa', 'bar'],
              deps=(None, None))),
        ('list_arg_deprecated_name',
         dict(opt_class=cfg.ListOpt, default=None,
              cli_args=['--oldfoo', 'blaa,bar'], value=['blaa', 'bar'],
              deps=('oldfoo', None))),
        ('list_arg_deprecated_group',
         dict(opt_class=cfg.ListOpt, default=None,
              cli_args=['--old-foo', 'blaa,bar'], value=['blaa', 'bar'],
              deps=(None, 'old'))),
        ('list_arg_deprecated_group_default',
         dict(opt_class=cfg.ListOpt, default=None,
              cli_args=['--foo', 'blaa,bar'], value=['blaa', 'bar'],
              deps=(None, 'DEFAULT'))),
        ('list_arg_deprecated_group_and_name',
         dict(opt_class=cfg.ListOpt, default=None,
              cli_args=['--old-oof', 'blaa,bar'], value=['blaa', 'bar'],
              deps=('oof', 'old'))),
        ('dict_default',
         dict(opt_class=cfg.DictOpt, default={'foo': 'bar'},
              cli_args=[], value={'foo': 'bar'}, deps=(None, None))),
        ('dict_arg',
         dict(opt_class=cfg.DictOpt, default=None,
              cli_args=['--foo', 'key1:blaa,key2:bar'],
              value={'key1': 'blaa', 'key2': 'bar'}, deps=(None, None))),
        ('dict_arg_multiple_keys_last_wins',
         dict(opt_class=cfg.DictOpt, default=None,
              cli_args=['--foo', 'key1:blaa', '--foo', 'key2:bar'],
              value={'key2': 'bar'}, deps=(None, None))),
        ('dict_arg_with_spaces',
         dict(opt_class=cfg.DictOpt, default=None,
              cli_args=['--foo', 'key1:blaa   ,key2:bar'],
              value={'key1': 'blaa', 'key2': 'bar'}, deps=(None, None))),
        ('dict_arg_deprecated_name',
         dict(opt_class=cfg.DictOpt, default=None,
              cli_args=['--oldfoo', 'key1:blaa', '--oldfoo', 'key2:bar'],
              value={'key2': 'bar'}, deps=('oldfoo', None))),
        ('dict_arg_deprecated_group',
         dict(opt_class=cfg.DictOpt, default=None,
              cli_args=['--old-foo', 'key1:blaa,key2:bar'],
              value={'key1': 'blaa', 'key2': 'bar'}, deps=(None, 'old'))),
        ('dict_arg_deprecated_group2',
         dict(opt_class=cfg.DictOpt, default=None,
              cli_args=['--old-foo', 'key1:blaa', '--old-foo', 'key2:bar'],
              value={'key2': 'bar'}, deps=(None, 'old'))),
        ('dict_arg_deprecated_group_default',
         dict(opt_class=cfg.DictOpt, default=None,
              cli_args=['--foo', 'key1:blaa', '--foo', 'key2:bar'],
              value={'key2': 'bar'}, deps=(None, 'DEFAULT'))),
        ('dict_arg_deprecated_group_and_name',
         dict(opt_class=cfg.DictOpt, default=None,
              cli_args=['--old-oof', 'key1:blaa,key2:bar'],
              value={'key1': 'blaa', 'key2': 'bar'}, deps=('oof', 'old'))),
        ('dict_arg_deprecated_group_and_name2',
         dict(opt_class=cfg.DictOpt, default=None,
              cli_args=['--old-oof', 'key1:blaa', '--old-oof', 'key2:bar'],
              value={'key2': 'bar'}, deps=('oof', 'old'))),
        ('multistr_default',
         dict(opt_class=cfg.MultiStrOpt, default=['bar'], cli_args=[],
              value=['bar'], deps=(None, None))),
        ('multistr_arg',
         dict(opt_class=cfg.MultiStrOpt, default=None,
              cli_args=['--foo', 'blaa', '--foo', 'bar'],
              value=['blaa', 'bar'], deps=(None, None))),
        ('multistr_arg_deprecated_name',
         dict(opt_class=cfg.MultiStrOpt, default=None,
              cli_args=['--oldfoo', 'blaa', '--oldfoo', 'bar'],
              value=['blaa', 'bar'], deps=('oldfoo', None))),
        ('multistr_arg_deprecated_group',
         dict(opt_class=cfg.MultiStrOpt, default=None,
              cli_args=['--old-foo', 'blaa', '--old-foo', 'bar'],
              value=['blaa', 'bar'], deps=(None, 'old'))),
        ('multistr_arg_deprecated_group_default',
         dict(opt_class=cfg.MultiStrOpt, default=None,
              cli_args=['--foo', 'blaa', '--foo', 'bar'],
              value=['blaa', 'bar'], deps=(None, 'DEFAULT'))),
        ('multistr_arg_deprecated_group_and_name',
         dict(opt_class=cfg.MultiStrOpt, default=None,
              cli_args=['--old-oof', 'blaa', '--old-oof', 'bar'],
              value=['blaa', 'bar'], deps=('oof', 'old'))),
        ('multiopt_arg_int',
         dict(opt_class=multi_int, default=None,
              cli_args=['--foo', '1', '--foo', '2'],
              value=[1, 2], deps=(None, None))),
        ('multiopt_float_int',
         dict(opt_class=multi_float, default=None,
              cli_args=['--foo', '1.2', '--foo', '2.3'],
              value=[1.2, 2.3], deps=(None, None))),
        ('multiopt_string',
         dict(opt_class=multi_string, default=None,
              cli_args=['--foo', 'bar', '--foo', 'baz'],
              value=["bar", "baz"], deps=(None, None))),
    ]

    def test_cli(self):

        self.conf.register_cli_opt(
            self.opt_class('foo', default=self.default,
                           deprecated_name=self.deps[0],
                           deprecated_group=self.deps[1]))

        self.conf(self.cli_args)

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, self.value)


class CliSpecialOptsTestCase(BaseTestCase):

    def test_help(self):
        self.useFixture(fixtures.MonkeyPatch('sys.stdout', moves.StringIO()))
        self.assertRaises(SystemExit, self.conf, ['--help'])
        self.assertTrue('FOO BAR' in sys.stdout.getvalue())
        self.assertTrue('--version' in sys.stdout.getvalue())
        self.assertTrue('--help' in sys.stdout.getvalue())
        self.assertTrue('--config-file' in sys.stdout.getvalue())

    def test_version(self):
        # In Python 3.4+, argparse prints the version on stdout; before 3.4, it
        # printed it on stderr.
        if sys.version_info >= (3, 4):
            stream_name = 'stdout'
        else:
            stream_name = 'stderr'
        self.useFixture(fixtures.MonkeyPatch("sys.%s" % stream_name,
                                             moves.StringIO()))
        self.assertRaises(SystemExit, self.conf, ['--version'])
        self.assertTrue('1.0' in getattr(sys, stream_name).getvalue())

    def test_config_file(self):
        paths = self.create_tempfiles([('1', '[DEFAULT]'),
                                       ('2', '[DEFAULT]')])

        self.conf(['--config-file', paths[0], '--config-file', paths[1]])

        self.assertEqual(self.conf.config_file, paths)


class PositionalTestCase(BaseTestCase):

    def _do_pos_test(self, opt_class, default, cli_args, value):
        self.conf.register_cli_opt(opt_class('foo',
                                             default=default,
                                             positional=True))

        self.conf(cli_args)

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, value)

    def test_positional_str_none_default(self):
        self._do_pos_test(cfg.StrOpt, None, [], None)

    def test_positional_str_default(self):
        self._do_pos_test(cfg.StrOpt, 'bar', [], 'bar')

    def test_positional_str_arg(self):
        self._do_pos_test(cfg.StrOpt, None, ['bar'], 'bar')

    def test_positional_int_none_default(self):
        self._do_pos_test(cfg.IntOpt, None, [], None)

    def test_positional_int_default(self):
        self._do_pos_test(cfg.IntOpt, 10, [], 10)

    def test_positional_int_arg(self):
        self._do_pos_test(cfg.IntOpt, None, ['20'], 20)

    def test_positional_float_none_default(self):
        self._do_pos_test(cfg.FloatOpt, None, [], None)

    def test_positional_float_default(self):
        self._do_pos_test(cfg.FloatOpt, 1.0, [], 1.0)

    def test_positional_float_arg(self):
        self._do_pos_test(cfg.FloatOpt, None, ['2.0'], 2.0)

    def test_positional_list_none_default(self):
        self._do_pos_test(cfg.ListOpt, None, [], None)

    def test_positional_list_empty_default(self):
        self._do_pos_test(cfg.ListOpt, [], [], [])

    def test_positional_list_default(self):
        self._do_pos_test(cfg.ListOpt, ['bar'], [], ['bar'])

    def test_positional_list_arg(self):
        self._do_pos_test(cfg.ListOpt, None,
                          ['blaa,bar'], ['blaa', 'bar'])

    def test_positional_dict_none_default(self):
        self._do_pos_test(cfg.DictOpt, None, [], None)

    def test_positional_dict_empty_default(self):
        self._do_pos_test(cfg.DictOpt, {}, [], {})

    def test_positional_dict_default(self):
        self._do_pos_test(cfg.DictOpt, {'key1': 'bar'}, [], {'key1': 'bar'})

    def test_positional_dict_arg(self):
        self._do_pos_test(cfg.DictOpt, None,
                          ['key1:blaa,key2:bar'],
                          {'key1': 'blaa', 'key2': 'bar'})

    def test_positional_multistr_none_default(self):
        self._do_pos_test(cfg.MultiStrOpt, None, [], None)

    def test_positional_multistr_empty_default(self):
        self._do_pos_test(cfg.MultiStrOpt, [], [], [])

    def test_positional_multistr_default(self):
        self._do_pos_test(cfg.MultiStrOpt, ['bar'], [], ['bar'])

    def test_positional_multistr_arg(self):
        self._do_pos_test(cfg.MultiStrOpt, None,
                          ['blaa', 'bar'], ['blaa', 'bar'])

    def test_positional_bool(self):
        self.assertRaises(ValueError, cfg.BoolOpt, 'foo', positional=True)

    def test_required_positional_opt(self):
        self.conf.register_cli_opt(
            cfg.StrOpt('foo', required=True, positional=True))

        self.conf(['bar'])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, 'bar')

    def test_missing_required_cli_opt(self):
        self.conf.register_cli_opt(
            cfg.StrOpt('foo', required=True, positional=True))
        self.assertRaises(cfg.RequiredOptError, self.conf, [])

    def test_positional_opts_order(self):
        self.conf.register_cli_opts((
            cfg.StrOpt('command', positional=True),
            cfg.StrOpt('arg1', positional=True),
            cfg.StrOpt('arg2', positional=True))
        )

        self.conf(['command', 'arg1', 'arg2'])

        self.assertEqual('command', self.conf.command)
        self.assertEqual('arg1', self.conf.arg1)
        self.assertEqual('arg2', self.conf.arg2)

    def test_positional_opt_order(self):
        self.conf.register_cli_opt(
            cfg.StrOpt('command', positional=True))
        self.conf.register_cli_opt(
            cfg.StrOpt('arg1', positional=True))
        self.conf.register_cli_opt(
            cfg.StrOpt('arg2', positional=True))

        self.conf(['command', 'arg1', 'arg2'])

        self.assertEqual('command', self.conf.command)
        self.assertEqual('arg1', self.conf.arg1)
        self.assertEqual('arg2', self.conf.arg2)

    def test_positional_opt_unregister(self):
        command = cfg.StrOpt('command', positional=True)
        arg1 = cfg.StrOpt('arg1', positional=True)
        arg2 = cfg.StrOpt('arg2', positional=True)
        self.conf.register_cli_opt(command)
        self.conf.register_cli_opt(arg1)
        self.conf.register_cli_opt(arg2)

        self.conf(['command', 'arg1', 'arg2'])

        self.assertEqual('command', self.conf.command)
        self.assertEqual('arg1', self.conf.arg1)
        self.assertEqual('arg2', self.conf.arg2)

        self.conf.reset()

        self.conf.unregister_opt(arg1)
        self.conf.unregister_opt(arg2)

        arg0 = cfg.StrOpt('arg0', positional=True)
        self.conf.register_cli_opt(arg0)
        self.conf.register_cli_opt(arg1)

        self.conf(['command', 'arg0', 'arg1'])

        self.assertEqual('command', self.conf.command)
        self.assertEqual('arg0', self.conf.arg0)
        self.assertEqual('arg1', self.conf.arg1)


class ConfigFileOptsTestCase(BaseTestCase):

    def _do_deprecated_test(self, opt_class, value, result, key,
                            section='DEFAULT',
                            dname=None, dgroup=None):
        self.conf.register_opt(opt_class('newfoo',
                                         deprecated_name=dname,
                                         deprecated_group=dgroup))

        paths = self.create_tempfiles([('test',
                                        '[' + section + ']\n' +
                                        key + ' = ' + value + '\n')])

        self.conf(['--config-file', paths[0]])
        self.assertTrue(hasattr(self.conf, 'newfoo'))
        self.assertEqual(self.conf.newfoo, result)

    def _do_dname_test_use(self, opt_class, value, result):
        self._do_deprecated_test(opt_class, value, result, 'oldfoo',
                                 dname='oldfoo')

    def _do_dgroup_test_use(self, opt_class, value, result):
        self._do_deprecated_test(opt_class, value, result, 'newfoo',
                                 section='old', dgroup='old')

    def _do_default_dgroup_test_use(self, opt_class, value, result):
        self._do_deprecated_test(opt_class, value, result, 'newfoo',
                                 section='DEFAULT', dgroup='DEFAULT')

    def _do_dgroup_and_dname_test_use(self, opt_class, value, result):
        self._do_deprecated_test(opt_class, value, result, 'oof',
                                 section='old', dgroup='old', dname='oof')

    def _do_dname_test_ignore(self, opt_class, value, result):
        self._do_deprecated_test(opt_class, value, result, 'newfoo',
                                 dname='oldfoo')

    def _do_dgroup_test_ignore(self, opt_class, value, result):
        self._do_deprecated_test(opt_class, value, result, 'newfoo',
                                 section='DEFAULT', dgroup='old')

    def _do_dgroup_and_dname_test_ignore(self, opt_class, value, result):
        self._do_deprecated_test(opt_class, value, result, 'oof',
                                 section='old', dgroup='old', dname='oof')

    def test_conf_file_str_default(self):
        self.conf.register_opt(cfg.StrOpt('foo', default='bar'))

        paths = self.create_tempfiles([('test', '[DEFAULT]\n')])

        self.conf(['--config-file', paths[0]])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, 'bar')

    def test_conf_file_str_value(self):
        self.conf.register_opt(cfg.StrOpt('foo'))

        paths = self.create_tempfiles([('test', '[DEFAULT]\n''foo = bar\n')])

        self.conf(['--config-file', paths[0]])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, 'bar')

    def test_conf_file_str_value_override(self):
        self.conf.register_cli_opt(cfg.StrOpt('foo'))

        paths = self.create_tempfiles([('1',
                                        '[DEFAULT]\n'
                                        'foo = baar\n'),
                                       ('2',
                                        '[DEFAULT]\n'
                                        'foo = baaar\n')])

        self.conf(['--foo', 'bar',
                   '--config-file', paths[0],
                   '--config-file', paths[1]])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, 'baaar')

    def test_conf_file_str_value_override_use_deprecated(self):
        """last option should always win, even if last uses deprecated."""
        self.conf.register_cli_opt(
            cfg.StrOpt('newfoo', deprecated_name='oldfoo'))

        paths = self.create_tempfiles([('0',
                                        '[DEFAULT]\n'
                                        'newfoo = middle\n'),
                                       ('1',
                                        '[DEFAULT]\n'
                                        'oldfoo = last\n')])

        self.conf(['--newfoo', 'first',
                   '--config-file', paths[0],
                   '--config-file', paths[1]])

        self.assertTrue(hasattr(self.conf, 'newfoo'))
        self.assertFalse(hasattr(self.conf, 'oldfoo'))
        self.assertEqual(self.conf.newfoo, 'last')

    def test_conf_file_str_use_dname(self):
        self._do_dname_test_use(cfg.StrOpt, 'value1', 'value1')

    def test_conf_file_str_use_dgroup(self):
        self._do_dgroup_test_use(cfg.StrOpt, 'value1', 'value1')

    def test_conf_file_str_use_default_dgroup(self):
        self._do_default_dgroup_test_use(cfg.StrOpt, 'value1', 'value1')

    def test_conf_file_str_use_dgroup_and_dname(self):
        self._do_dgroup_and_dname_test_use(cfg.StrOpt, 'value1', 'value1')

    def test_conf_file_str_ignore_dname(self):
        self._do_dname_test_ignore(cfg.StrOpt, 'value2', 'value2')

    def test_conf_file_str_ignore_dgroup(self):
        self._do_dgroup_test_ignore(cfg.StrOpt, 'value2', 'value2')

    def test_conf_file_str_ignore_dgroup_and_dname(self):
        self._do_dgroup_and_dname_test_ignore(cfg.StrOpt, 'value2', 'value2')

    def test_conf_file_bool_default(self):
        self.conf.register_opt(cfg.BoolOpt('foo', default=False))

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n')])

        self.conf(['--config-file', paths[0]])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, False)

    def test_conf_file_bool_value(self):
        self.conf.register_opt(cfg.BoolOpt('foo'))

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n'
                                        'foo = true\n')])

        self.conf(['--config-file', paths[0]])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, True)

    def test_conf_file_bool_cli_value_override(self):
        self.conf.register_cli_opt(cfg.BoolOpt('foo'))

        paths = self.create_tempfiles([('1',
                                        '[DEFAULT]\n'
                                        'foo = 0\n')])

        self.conf(['--foo',
                   '--config-file', paths[0]])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, False)

    def test_conf_file_bool_cli_inverse_override(self):
        self.conf.register_cli_opt(cfg.BoolOpt('foo'))

        paths = self.create_tempfiles([('1',
                                        '[DEFAULT]\n'
                                        'foo = true\n')])

        self.conf(['--nofoo',
                   '--config-file', paths[0]])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, True)

    def test_conf_file_bool_cli_order_override(self):
        self.conf.register_cli_opt(cfg.BoolOpt('foo'))

        paths = self.create_tempfiles([('1',
                                        '[DEFAULT]\n'
                                        'foo = false\n')])

        self.conf(['--config-file', paths[0],
                   '--foo'])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, True)

    def test_conf_file_bool_file_value_override(self):
        self.conf.register_cli_opt(cfg.BoolOpt('foo'))

        paths = self.create_tempfiles([('1',
                                        '[DEFAULT]\n'
                                        'foo = 0\n'),
                                       ('2',
                                        '[DEFAULT]\n'
                                        'foo = yes\n')])

        self.conf(['--config-file', paths[0],
                   '--config-file', paths[1]])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, True)

    def test_conf_file_bool_use_dname(self):
        self._do_dname_test_use(cfg.BoolOpt, 'yes', True)

    def test_conf_file_bool_use_dgroup(self):
        self._do_dgroup_test_use(cfg.BoolOpt, 'yes', True)

    def test_conf_file_bool_use_default_dgroup(self):
        self._do_default_dgroup_test_use(cfg.BoolOpt, 'yes', True)

    def test_conf_file_bool_use_dgroup_and_dname(self):
        self._do_dgroup_and_dname_test_use(cfg.BoolOpt, 'yes', True)

    def test_conf_file_bool_ignore_dname(self):
        self._do_dname_test_ignore(cfg.BoolOpt, 'no', False)

    def test_conf_file_bool_ignore_dgroup(self):
        self._do_dgroup_test_ignore(cfg.BoolOpt, 'no', False)

    def test_conf_file_bool_ignore_group_and_dname(self):
        self._do_dgroup_and_dname_test_ignore(cfg.BoolOpt, 'no', False)

    def test_conf_file_int_default(self):
        self.conf.register_opt(cfg.IntOpt('foo', default=666))

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n')])

        self.conf(['--config-file', paths[0]])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, 666)

    @mock.patch.object(cfg, 'LOG')
    def test_conf_file_int_wrong_default(self, mock_log):
        cfg.IntOpt('foo', default='666')
        mock_log.debug.assert_call_count(1)

    def test_conf_file_int_value(self):
        self.conf.register_opt(cfg.IntOpt('foo'))

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n'
                                        'foo = 666\n')])

        self.conf(['--config-file', paths[0]])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, 666)

    def test_conf_file_int_value_override(self):
        self.conf.register_cli_opt(cfg.IntOpt('foo'))

        paths = self.create_tempfiles([('1',
                                        '[DEFAULT]\n'
                                        'foo = 66\n'),
                                       ('2',
                                        '[DEFAULT]\n'
                                        'foo = 666\n')])

        self.conf(['--foo', '6',
                   '--config-file', paths[0],
                   '--config-file', paths[1]])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, 666)

    def test_conf_file_int_use_dname(self):
        self._do_dname_test_use(cfg.IntOpt, '66', 66)

    def test_conf_file_int_use_dgroup(self):
        self._do_dgroup_test_use(cfg.IntOpt, '66', 66)

    def test_conf_file_int_use_default_dgroup(self):
        self._do_default_dgroup_test_use(cfg.IntOpt, '66', 66)

    def test_conf_file_int_use_dgroup_and_dname(self):
        self._do_dgroup_and_dname_test_use(cfg.IntOpt, '66', 66)

    def test_conf_file_int_ignore_dname(self):
        self._do_dname_test_ignore(cfg.IntOpt, '64', 64)

    def test_conf_file_int_ignore_dgroup(self):
        self._do_dgroup_test_ignore(cfg.IntOpt, '64', 64)

    def test_conf_file_int_ignore_dgroup_and_dname(self):
        self._do_dgroup_and_dname_test_ignore(cfg.IntOpt, '64', 64)

    def test_conf_file_float_default(self):
        self.conf.register_opt(cfg.FloatOpt('foo', default=6.66))

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n')])

        self.conf(['--config-file', paths[0]])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, 6.66)

    @mock.patch.object(cfg, 'LOG')
    def test_conf_file_float_default_wrong_type(self, mock_log):
        cfg.FloatOpt('foo', default='foobar6.66')
        mock_log.debug.assert_call_count(1)

    def test_conf_file_float_value(self):
        self.conf.register_opt(cfg.FloatOpt('foo'))

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n'
                                        'foo = 6.66\n')])

        self.conf(['--config-file', paths[0]])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, 6.66)

    def test_conf_file_float_value_override(self):
        self.conf.register_cli_opt(cfg.FloatOpt('foo'))

        paths = self.create_tempfiles([('1',
                                        '[DEFAULT]\n'
                                        'foo = 6.6\n'),
                                       ('2',
                                        '[DEFAULT]\n'
                                        'foo = 6.66\n')])

        self.conf(['--foo', '6',
                   '--config-file', paths[0],
                   '--config-file', paths[1]])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, 6.66)

    def test_conf_file_float_use_dname(self):
        self._do_dname_test_use(cfg.FloatOpt, '66.54', 66.54)

    def test_conf_file_float_use_dgroup(self):
        self._do_dgroup_test_use(cfg.FloatOpt, '66.54', 66.54)

    def test_conf_file_float_use_default_dgroup(self):
        self._do_default_dgroup_test_use(cfg.FloatOpt, '66.54', 66.54)

    def test_conf_file_float_use_dgroup_and_dname(self):
        self._do_dgroup_and_dname_test_use(cfg.FloatOpt, '66.54', 66.54)

    def test_conf_file_float_ignore_dname(self):
        self._do_dname_test_ignore(cfg.FloatOpt, '64.54', 64.54)

    def test_conf_file_float_ignore_dgroup(self):
        self._do_dgroup_test_ignore(cfg.FloatOpt, '64.54', 64.54)

    def test_conf_file_float_ignore_dgroup_and_dname(self):
        self._do_dgroup_and_dname_test_ignore(cfg.FloatOpt, '64.54', 64.54)

    def test_conf_file_list_default(self):
        self.conf.register_opt(cfg.ListOpt('foo', default=['bar']))

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n')])

        self.conf(['--config-file', paths[0]])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, ['bar'])

    @mock.patch.object(cfg, 'LOG')
    def test_conf_file_list_default_wrong_type(self, mock_log):
        cfg.ListOpt('foo', default=25)
        mock_log.debug.assert_called_once_with(
            'Expected default value of type(s) %(extypes)s but '
            'got %(default)r of type %(deftypes)s',
            {'extypes': 'list',
             'default': 25,
             'deftypes': 'int'})

    def test_conf_file_list_value(self):
        self.conf.register_opt(cfg.ListOpt('foo'))

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n'
                                        'foo = bar\n')])

        self.conf(['--config-file', paths[0]])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, ['bar'])

    def test_conf_file_list_value_override(self):
        self.conf.register_cli_opt(cfg.ListOpt('foo'))

        paths = self.create_tempfiles([('1',
                                        '[DEFAULT]\n'
                                        'foo = bar,bar\n'),
                                       ('2',
                                        '[DEFAULT]\n'
                                        'foo = b,a,r\n')])

        self.conf(['--foo', 'bar',
                   '--config-file', paths[0],
                   '--config-file', paths[1]])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, ['b', 'a', 'r'])

    def test_conf_file_list_use_dname(self):
        self._do_dname_test_use(cfg.ListOpt, 'a,b,c', ['a', 'b', 'c'])

    def test_conf_file_list_use_dgroup(self):
        self._do_dgroup_test_use(cfg.ListOpt, 'a,b,c', ['a', 'b', 'c'])

    def test_conf_file_list_use_default_dgroup(self):
        self._do_default_dgroup_test_use(cfg.ListOpt, 'a,b,c', ['a', 'b', 'c'])

    def test_conf_file_list_use_dgroup_and_dname(self):
        self._do_dgroup_and_dname_test_use(cfg.ListOpt, 'a,b,c',
                                           ['a', 'b', 'c'])

    def test_conf_file_list_ignore_dname(self):
        self._do_dname_test_ignore(cfg.ListOpt, 'd,e,f', ['d', 'e', 'f'])

    def test_conf_file_list_ignore_dgroup(self):
        self._do_dgroup_test_ignore(cfg.ListOpt, 'd,e,f', ['d', 'e', 'f'])

    def test_conf_file_list_ignore_dgroup_and_dname(self):
        self._do_dgroup_and_dname_test_ignore(
            cfg.ListOpt, 'd,e,f', ['d', 'e', 'f'])

    def test_conf_file_list_spaces_use_dname(self):
        self._do_dname_test_use(cfg.ListOpt, 'a, b, c', ['a', 'b', 'c'])

    def test_conf_file_list_spaces_use_dgroup(self):
        self._do_dgroup_test_use(cfg.ListOpt, 'a, b, c', ['a', 'b', 'c'])

    def test_conf_file_list_spaces_use_default_dgroup(self):
        self._do_default_dgroup_test_use(
            cfg.ListOpt, 'a, b, c', ['a', 'b', 'c'])

    def test_conf_file_list_spaces_use_dgroup_and_dname(self):
        self._do_dgroup_and_dname_test_use(
            cfg.ListOpt, 'a, b, c', ['a', 'b', 'c'])

    def test_conf_file_list_spaces_ignore_dname(self):
        self._do_dname_test_ignore(cfg.ListOpt, 'd, e, f', ['d', 'e', 'f'])

    def test_conf_file_list_spaces_ignore_dgroup(self):
        self._do_dgroup_test_ignore(cfg.ListOpt, 'd, e, f', ['d', 'e', 'f'])

    def test_conf_file_list_spaces_ignore_dgroup_and_dname(self):
        self._do_dgroup_and_dname_test_ignore(cfg.ListOpt, 'd, e, f',
                                              ['d', 'e', 'f'])

    def test_conf_file_dict_default(self):
        self.conf.register_opt(cfg.DictOpt('foo', default={'key': 'bar'}))

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n')])

        self.conf(['--config-file', paths[0]])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, {'key': 'bar'})

    def test_conf_file_dict_value(self):
        self.conf.register_opt(cfg.DictOpt('foo'))

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n'
                                        'foo = key:bar\n')])

        self.conf(['--config-file', paths[0]])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, {'key': 'bar'})

    def test_conf_file_dict_colon_in_value(self):
        self.conf.register_opt(cfg.DictOpt('foo'))

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n'
                                        'foo = key:bar:baz\n')])

        self.conf(['--config-file', paths[0]])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, {'key': 'bar:baz'})

    def test_conf_file_dict_value_no_colon(self):
        self.conf.register_opt(cfg.DictOpt('foo'))

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n'
                                        'foo = key:bar,baz\n')])

        self.conf(['--config-file', paths[0]])

        self.assertRaises(cfg.ConfigFileValueError, self.conf._get, 'foo')
        self.assertRaises(AttributeError, getattr, self.conf, 'foo')

    def test_conf_file_dict_value_duplicate_key(self):
        self.conf.register_opt(cfg.DictOpt('foo'))

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n'
                                        'foo = key:bar,key:baz\n')])

        self.conf(['--config-file', paths[0]])

        self.assertRaises(cfg.ConfigFileValueError, self.conf._get, 'foo')
        self.assertRaises(AttributeError, getattr, self.conf, 'foo')

    def test_conf_file_dict_values_override_deprecated(self):
        self.conf.register_cli_opt(cfg.DictOpt('foo',
                                   deprecated_name='oldfoo'))

        paths = self.create_tempfiles([('1',
                                        '[DEFAULT]\n'
                                        'foo = key1:bar1\n'),
                                       ('2',
                                        '[DEFAULT]\n'
                                        'oldfoo = key2:bar2\n'
                                        'oldfoo = key3:bar3\n')])

        self.conf(['--foo', 'key0:bar0',
                   '--config-file', paths[0],
                   '--config-file', paths[1]])

        self.assertTrue(hasattr(self.conf, 'foo'))

        self.assertEqual(self.conf.foo, {'key3': 'bar3'})

    def test_conf_file_dict_deprecated(self):
        self.conf.register_opt(cfg.DictOpt('newfoo', deprecated_name='oldfoo'))

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n'
                                        'oldfoo= key1:bar1\n'
                                        'oldfoo = key2:bar2\n')])

        self.conf(['--config-file', paths[0]])
        self.assertTrue(hasattr(self.conf, 'newfoo'))
        self.assertEqual(self.conf.newfoo, {'key2': 'bar2'})

    def test_conf_file_dict_value_override(self):
        self.conf.register_cli_opt(cfg.DictOpt('foo'))

        paths = self.create_tempfiles([('1',
                                        '[DEFAULT]\n'
                                        'foo = key:bar,key2:bar\n'),
                                       ('2',
                                        '[DEFAULT]\n'
                                        'foo = k1:v1,k2:v2\n')])

        self.conf(['--foo', 'x:y,x2:y2',
                   '--config-file', paths[0],
                   '--config-file', paths[1]])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, {'k1': 'v1', 'k2': 'v2'})

    def test_conf_file_dict_use_dname(self):
        self._do_dname_test_use(cfg.DictOpt,
                                'k1:a,k2:b,k3:c',
                                {'k1': 'a', 'k2': 'b', 'k3': 'c'})

    def test_conf_file_dict_use_dgroup(self):
        self._do_dgroup_test_use(cfg.DictOpt,
                                 'k1:a,k2:b,k3:c',
                                 {'k1': 'a', 'k2': 'b', 'k3': 'c'})

    def test_conf_file_dict_use_default_dgroup(self):
        self._do_default_dgroup_test_use(cfg.DictOpt,
                                         'k1:a,k2:b,k3:c',
                                         {'k1': 'a', 'k2': 'b', 'k3': 'c'})

    def test_conf_file_dict_use_dgroup_and_dname(self):
        self._do_dgroup_and_dname_test_use(cfg.DictOpt,
                                           'k1:a,k2:b,k3:c',
                                           {'k1': 'a', 'k2': 'b', 'k3': 'c'})

    def test_conf_file_dict_ignore_dname(self):
        self._do_dname_test_ignore(cfg.DictOpt,
                                   'k1:d,k2:e,k3:f',
                                   {'k1': 'd', 'k2': 'e', 'k3': 'f'})

    def test_conf_file_dict_ignore_dgroup(self):
        self._do_dgroup_test_ignore(cfg.DictOpt,
                                    'k1:d,k2:e,k3:f',
                                    {'k1': 'd', 'k2': 'e', 'k3': 'f'})

    def test_conf_file_dict_ignore_dgroup_and_dname(self):
        self._do_dgroup_and_dname_test_ignore(cfg.DictOpt,
                                              'k1:d,k2:e,k3:f',
                                              {'k1': 'd',
                                               'k2': 'e',
                                               'k3': 'f'})

    def test_conf_file_dict_spaces_use_dname(self):
        self._do_dname_test_use(cfg.DictOpt,
                                'k1:a,k2:b,k3:c',
                                {'k1': 'a', 'k2': 'b', 'k3': 'c'})

    def test_conf_file_dict_spaces_use_dgroup(self):
        self._do_dgroup_test_use(cfg.DictOpt,
                                 'k1:a,k2:b,k3:c',
                                 {'k1': 'a', 'k2': 'b', 'k3': 'c'})

    def test_conf_file_dict_spaces_use_default_dgroup(self):
        self._do_default_dgroup_test_use(cfg.DictOpt,
                                         'k1:a,k2:b,k3:c',
                                         {'k1': 'a', 'k2': 'b', 'k3': 'c'})

    def test_conf_file_dict_spaces_use_dgroup_and_dname(self):
        self._do_dgroup_and_dname_test_use(cfg.DictOpt,
                                           'k1:a,k2:b,k3:c',
                                           {'k1': 'a', 'k2': 'b', 'k3': 'c'})

    def test_conf_file_dict_spaces_ignore_dname(self):
        self._do_dname_test_ignore(cfg.DictOpt,
                                   'k1:d,k2:e,k3:f',
                                   {'k1': 'd', 'k2': 'e', 'k3': 'f'})

    def test_conf_file_dict_spaces_ignore_dgroup(self):
        self._do_dgroup_test_ignore(cfg.DictOpt,
                                    'k1:d,k2:e,k3:f',
                                    {'k1': 'd', 'k2': 'e', 'k3': 'f'})

    def test_conf_file_dict_spaces_ignore_dgroup_and_dname(self):
        self._do_dgroup_and_dname_test_ignore(cfg.DictOpt,
                                              'k1:d,k2:e,k3:f',
                                              {'k1': 'd',
                                               'k2': 'e',
                                               'k3': 'f'})

    def test_conf_file_multistr_default(self):
        self.conf.register_opt(cfg.MultiStrOpt('foo', default=['bar']))

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n')])

        self.conf(['--config-file', paths[0]])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, ['bar'])

    def test_conf_file_multistr_value(self):
        self.conf.register_opt(cfg.MultiStrOpt('foo'))

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n'
                                        'foo = bar\n')])

        self.conf(['--config-file', paths[0]])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, ['bar'])

    def test_conf_file_multistr_values_append_deprecated(self):
        self.conf.register_cli_opt(cfg.MultiStrOpt('foo',
                                   deprecated_name='oldfoo'))

        paths = self.create_tempfiles([('1',
                                        '[DEFAULT]\n'
                                        'foo = bar1\n'),
                                       ('2',
                                        '[DEFAULT]\n'
                                        'oldfoo = bar2\n'
                                        'oldfoo = bar3\n')])

        self.conf(['--foo', 'bar0',
                   '--config-file', paths[0],
                   '--config-file', paths[1]])

        self.assertTrue(hasattr(self.conf, 'foo'))

        self.assertEqual(self.conf.foo, ['bar0', 'bar1', 'bar2', 'bar3'])

    def test_conf_file_multistr_values_append(self):
        self.conf.register_cli_opt(cfg.MultiStrOpt('foo'))

        paths = self.create_tempfiles([('1',
                                        '[DEFAULT]\n'
                                        'foo = bar1\n'),
                                       ('2',
                                        '[DEFAULT]\n'
                                        'foo = bar2\n'
                                        'foo = bar3\n')])

        self.conf(['--foo', 'bar0',
                   '--config-file', paths[0],
                   '--config-file', paths[1]])

        self.assertTrue(hasattr(self.conf, 'foo'))

        self.assertEqual(self.conf.foo, ['bar0', 'bar1', 'bar2', 'bar3'])

    def test_conf_file_multistr_deprecated(self):
        self.conf.register_opt(
            cfg.MultiStrOpt('newfoo', deprecated_name='oldfoo'))

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n'
                                        'oldfoo= bar1\n'
                                        'oldfoo = bar2\n')])

        self.conf(['--config-file', paths[0]])
        self.assertTrue(hasattr(self.conf, 'newfoo'))
        self.assertEqual(self.conf.newfoo, ['bar1', 'bar2'])

    def test_conf_file_multiple_opts(self):
        self.conf.register_opts([cfg.StrOpt('foo'), cfg.StrOpt('bar')])

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n'
                                        'foo = bar\n'
                                        'bar = foo\n')])

        self.conf(['--config-file', paths[0]])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, 'bar')
        self.assertTrue(hasattr(self.conf, 'bar'))
        self.assertEqual(self.conf.bar, 'foo')

    def test_conf_file_raw_value(self):
        self.conf.register_opt(cfg.StrOpt('foo'))

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n'
                                        'foo = bar-%08x\n')])

        self.conf(['--config-file', paths[0]])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, 'bar-%08x')


class ConfigFileReloadTestCase(BaseTestCase):

    def test_conf_files_reload(self):
        self.conf.register_cli_opt(cfg.StrOpt('foo'))

        paths = self.create_tempfiles([('1',
                                        '[DEFAULT]\n'
                                        'foo = baar\n'),
                                       ('2',
                                        '[DEFAULT]\n'
                                        'foo = baaar\n')])

        self.conf(['--config-file', paths[0]])
        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, 'baar')

        shutil.copy(paths[1], paths[0])

        self.conf.reload_config_files()
        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, 'baaar')

    def test_conf_files_reload_default(self):
        self.conf.register_cli_opt(cfg.StrOpt('foo1'))
        self.conf.register_cli_opt(cfg.StrOpt('foo2'))

        paths = self.create_tempfiles([('1',
                                        '[DEFAULT]\n'
                                        'foo1 = default1\n'),
                                       ('2',
                                        '[DEFAULT]\n'
                                        'foo2 = default2\n')])

        paths_change = self.create_tempfiles([('1',
                                               '[DEFAULT]\n'
                                               'foo1 = change_default1\n'),
                                              ('2',
                                               '[DEFAULT]\n'
                                               'foo2 = change_default2\n')])

        self.conf(args=[], default_config_files=paths)
        self.assertTrue(hasattr(self.conf, 'foo1'))
        self.assertEqual(self.conf.foo1, 'default1')
        self.assertTrue(hasattr(self.conf, 'foo2'))
        self.assertEqual(self.conf.foo2, 'default2')

        shutil.copy(paths_change[0], paths[0])
        shutil.copy(paths_change[1], paths[1])

        self.conf.reload_config_files()
        self.assertTrue(hasattr(self.conf, 'foo1'))
        self.assertEqual(self.conf.foo1, 'change_default1')
        self.assertTrue(hasattr(self.conf, 'foo2'))
        self.assertEqual(self.conf.foo2, 'change_default2')

    def test_conf_files_reload_file_not_found(self):
        self.conf.register_cli_opt(cfg.StrOpt('foo', required=True))
        paths = self.create_tempfiles([('1',
                                        '[DEFAULT]\n'
                                        'foo = baar\n')])

        self.conf(['--config-file', paths[0]])
        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, 'baar')

        os.remove(paths[0])

        self.conf.reload_config_files()
        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, 'baar')

    def test_conf_files_reload_error(self):
        self.conf.register_cli_opt(cfg.StrOpt('foo', required=True))
        self.conf.register_cli_opt(cfg.StrOpt('foo1', required=True))
        paths = self.create_tempfiles([('1',
                                        '[DEFAULT]\n'
                                        'foo = test1\n'
                                        'foo1 = test11\n'),
                                       ('2',
                                        '[DEFAULT]\n'
                                        'foo2 = test2\n'
                                        'foo3 = test22\n')])

        self.conf(['--config-file', paths[0]])
        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, 'test1')
        self.assertTrue(hasattr(self.conf, 'foo1'))
        self.assertEqual(self.conf.foo1, 'test11')

        shutil.copy(paths[1], paths[0])

        self.conf.reload_config_files()
        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, 'test1')
        self.assertTrue(hasattr(self.conf, 'foo1'))
        self.assertEqual(self.conf.foo1, 'test11')


class OptGroupsTestCase(BaseTestCase):

    def test_arg_group(self):
        blaa_group = cfg.OptGroup('blaa', 'blaa options')
        self.conf.register_group(blaa_group)
        self.conf.register_cli_opt(cfg.StrOpt('foo'), group=blaa_group)

        self.conf(['--blaa-foo', 'bar'])

        self.assertTrue(hasattr(self.conf, 'blaa'))
        self.assertTrue(hasattr(self.conf.blaa, 'foo'))
        self.assertEqual(self.conf.blaa.foo, 'bar')

    def test_autocreate_group_by_name(self):
        self.conf.register_cli_opt(cfg.StrOpt('foo'), group='blaa')

        self.conf(['--blaa-foo', 'bar'])

        self.assertTrue(hasattr(self.conf, 'blaa'))
        self.assertTrue(hasattr(self.conf.blaa, 'foo'))
        self.assertEqual(self.conf.blaa.foo, 'bar')

    def test_autocreate_group_by_group(self):
        group = cfg.OptGroup(name='blaa', title='Blaa options')
        self.conf.register_cli_opt(cfg.StrOpt('foo'), group=group)

        self.conf(['--blaa-foo', 'bar'])

        self.assertTrue(hasattr(self.conf, 'blaa'))
        self.assertTrue(hasattr(self.conf.blaa, 'foo'))
        self.assertEqual(self.conf.blaa.foo, 'bar')

    def test_autocreate_title(self):
        blaa_group = cfg.OptGroup('blaa')
        self.assertEqual(blaa_group.title, 'blaa options')

    def test_arg_group_by_name(self):
        self.conf.register_group(cfg.OptGroup('blaa'))
        self.conf.register_cli_opt(cfg.StrOpt('foo'), group='blaa')

        self.conf(['--blaa-foo', 'bar'])

        self.assertTrue(hasattr(self.conf, 'blaa'))
        self.assertTrue(hasattr(self.conf.blaa, 'foo'))
        self.assertEqual(self.conf.blaa.foo, 'bar')

    def test_arg_group_with_default(self):
        self.conf.register_group(cfg.OptGroup('blaa'))
        self.conf.register_cli_opt(
            cfg.StrOpt('foo', default='bar'), group='blaa')

        self.conf([])

        self.assertTrue(hasattr(self.conf, 'blaa'))
        self.assertTrue(hasattr(self.conf.blaa, 'foo'))
        self.assertEqual(self.conf.blaa.foo, 'bar')

    def test_arg_group_with_conf_and_group_opts(self):
        self.conf.register_cli_opt(cfg.StrOpt('conf'), group='blaa')
        self.conf.register_cli_opt(cfg.StrOpt('group'), group='blaa')

        self.conf(['--blaa-conf', 'foo', '--blaa-group', 'bar'])

        self.assertTrue(hasattr(self.conf, 'blaa'))
        self.assertTrue(hasattr(self.conf.blaa, 'conf'))
        self.assertEqual(self.conf.blaa.conf, 'foo')
        self.assertTrue(hasattr(self.conf.blaa, 'group'))
        self.assertEqual(self.conf.blaa.group, 'bar')

    def test_arg_group_in_config_file(self):
        self.conf.register_group(cfg.OptGroup('blaa'))
        self.conf.register_opt(cfg.StrOpt('foo'), group='blaa')

        paths = self.create_tempfiles([('test',
                                        '[blaa]\n'
                                        'foo = bar\n')])

        self.conf(['--config-file', paths[0]])

        self.assertTrue(hasattr(self.conf, 'blaa'))
        self.assertTrue(hasattr(self.conf.blaa, 'foo'))
        self.assertEqual(self.conf.blaa.foo, 'bar')

    def test_arg_group_in_config_file_with_deprecated_name(self):
        self.conf.register_group(cfg.OptGroup('blaa'))
        self.conf.register_opt(cfg.StrOpt('foo', deprecated_name='oldfoo'),
                               group='blaa')

        paths = self.create_tempfiles([('test',
                                        '[blaa]\n'
                                        'oldfoo = bar\n')])

        self.conf(['--config-file', paths[0]])

        self.assertTrue(hasattr(self.conf, 'blaa'))
        self.assertTrue(hasattr(self.conf.blaa, 'foo'))
        self.assertEqual(self.conf.blaa.foo, 'bar')

    def test_arg_group_in_config_file_with_deprecated_group(self):
        self.conf.register_group(cfg.OptGroup('blaa'))
        self.conf.register_opt(cfg.StrOpt('foo', deprecated_group='DEFAULT'),
                               group='blaa')

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n'
                                        'foo = bar\n')])

        self.conf(['--config-file', paths[0]])

        self.assertTrue(hasattr(self.conf, 'blaa'))
        self.assertTrue(hasattr(self.conf.blaa, 'foo'))
        self.assertEqual(self.conf.blaa.foo, 'bar')

    def test_arg_group_in_config_file_with_deprecated_group_and_name(self):
        self.conf.register_group(cfg.OptGroup('blaa'))
        self.conf.register_opt(
            cfg.StrOpt('foo', deprecated_group='DEFAULT',
                       deprecated_name='oldfoo'), group='blaa')

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n'
                                        'oldfoo = bar\n')])

        self.conf(['--config-file', paths[0]])

        self.assertTrue(hasattr(self.conf, 'blaa'))
        self.assertTrue(hasattr(self.conf.blaa, 'foo'))
        self.assertEqual(self.conf.blaa.foo, 'bar')

    def test_arg_group_in_config_file_override_deprecated_name(self):
        self.conf.register_group(cfg.OptGroup('blaa'))
        self.conf.register_opt(cfg.StrOpt('foo', deprecated_name='oldfoo'),
                               group='blaa')

        paths = self.create_tempfiles([('test',
                                        '[blaa]\n'
                                        'foo = bar\n'
                                        'oldfoo = blabla\n')])

        self.conf(['--config-file', paths[0]])

        self.assertTrue(hasattr(self.conf, 'blaa'))
        self.assertTrue(hasattr(self.conf.blaa, 'foo'))
        self.assertEqual(self.conf.blaa.foo, 'bar')

    def test_arg_group_in_config_file_override_deprecated_group(self):
        self.conf.register_group(cfg.OptGroup('blaa'))
        self.conf.register_opt(cfg.StrOpt('foo', deprecated_group='DEFAULT'),
                               group='blaa')

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n'
                                        'foo = blabla\n'
                                        '[blaa]\n'
                                        'foo = bar\n')])

        self.conf(['--config-file', paths[0]])

        self.assertTrue(hasattr(self.conf, 'blaa'))
        self.assertTrue(hasattr(self.conf.blaa, 'foo'))
        self.assertEqual(self.conf.blaa.foo, 'bar')

    def test_arg_group_in_config_file_override_deprecated_group_and_name(self):
        self.conf.register_group(cfg.OptGroup('blaa'))
        self.conf.register_opt(
            cfg.StrOpt('foo', deprecated_group='DEFAULT',
                       deprecated_name='oldfoo'), group='blaa')

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n'
                                        'oldfoo = blabla\n'
                                        '[blaa]\n'
                                        'foo = bar\n')])

        self.conf(['--config-file', paths[0]])

        self.assertTrue(hasattr(self.conf, 'blaa'))
        self.assertTrue(hasattr(self.conf.blaa, 'foo'))
        self.assertEqual(self.conf.blaa.foo, 'bar')

    def test_arg_group_in_config_file_with_capital_name(self):
        self.conf.register_group(cfg.OptGroup('blaa'))
        self.conf.register_opt(cfg.StrOpt('foo'), group='blaa')

        paths = self.create_tempfiles([('test',
                                        '[BLAA]\n'
                                        'foo = bar\n')])

        self.conf(['--config-file', paths[0]])

        self.assertFalse(hasattr(self.conf, 'BLAA'))
        self.assertTrue(hasattr(self.conf, 'blaa'))
        self.assertTrue(hasattr(self.conf.blaa, 'foo'))
        self.assertEqual(self.conf.blaa.foo, 'bar')

    def test_arg_group_in_config_file_with_capital_name_on_legacy_code(self):
        self.conf.register_group(cfg.OptGroup('BLAA'))
        self.conf.register_opt(cfg.StrOpt('foo'), group='BLAA')

        paths = self.create_tempfiles([('test',
                                        '[BLAA]\n'
                                        'foo = bar\n')])

        self.conf(['--config-file', paths[0]])

        self.assertFalse(hasattr(self.conf, 'blaa'))
        self.assertTrue(hasattr(self.conf, 'BLAA'))
        self.assertTrue(hasattr(self.conf.BLAA, 'foo'))
        self.assertEqual(self.conf.BLAA.foo, 'bar')


class MappingInterfaceTestCase(BaseTestCase):

    def test_mapping_interface(self):
        self.conf.register_cli_opt(cfg.StrOpt('foo'))

        self.conf(['--foo', 'bar'])

        self.assertTrue('foo' in self.conf)
        self.assertTrue('config_file' in self.conf)
        self.assertEqual(len(self.conf), 3)
        self.assertEqual(self.conf['foo'], 'bar')
        self.assertEqual(self.conf.get('foo'), 'bar')
        self.assertTrue('bar' in list(self.conf.values()))

    def test_mapping_interface_with_group(self):
        self.conf.register_group(cfg.OptGroup('blaa'))
        self.conf.register_cli_opt(cfg.StrOpt('foo'), group='blaa')

        self.conf(['--blaa-foo', 'bar'])

        self.assertTrue('blaa' in self.conf)
        self.assertTrue('foo' in list(self.conf['blaa']))
        self.assertEqual(len(self.conf['blaa']), 1)
        self.assertEqual(self.conf['blaa']['foo'], 'bar')
        self.assertEqual(self.conf['blaa'].get('foo'), 'bar')
        self.assertTrue('bar' in self.conf['blaa'].values())
        self.assertEqual(self.conf.blaa, self.conf['blaa'])


class OptNameSeparatorTestCast(BaseTestCase):

    scenarios = [
        ('hyphen',
         dict(opt_name='foo-bar',
              opt_dest='foo_bar',
              broken_opt_dest='foo-bar',
              cf_name='foo_bar',
              broken_cf_name='foo-bar',
              cli_name='foo-bar',
              broken_cli_name='foo_bar',
              broken=True)),  # FIXME(markmc): see #1279973
        ('underscore',
         dict(opt_name='foo_bar',
              opt_dest='foo_bar',
              broken_opt_dest='foo-bar',
              cf_name='foo_bar',
              broken_cf_name='foo-bar',
              cli_name='foo_bar',
              broken_cli_name='foo_bar',
              broken=False)),
    ]

    def test_attribute_and_key_name(self):
        self.conf.register_opt(cfg.StrOpt(self.opt_name))

        self.assertTrue(hasattr(self.conf, self.opt_dest))
        self.assertFalse(hasattr(self.conf, self.broken_opt_dest))
        self.assertIn(self.opt_dest, self.conf)
        self.assertNotIn(self.broken_opt_dest, self.conf)

    def test_cli_opt_name(self):
        self.conf.register_cli_opt(cfg.BoolOpt(self.opt_name))

        self.conf(['--' + self.cli_name])

        self.assertTrue(getattr(self.conf, self.opt_dest))

    def test_config_file_opt_name(self):
        self.conf.register_opt(cfg.BoolOpt(self.opt_name))

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n' +
                                        self.cf_name + ' = True\n' +
                                        self.broken_cf_name + ' = False\n')])

        self.conf(['--config-file', paths[0]])

        self.assertTrue(getattr(self.conf, self.opt_dest))

    def test_deprecated_name(self):
        self.conf.register_opt(cfg.StrOpt('foobar',
                                          deprecated_name=self.opt_name))

        self.assertTrue(hasattr(self.conf, 'foobar'))
        self.assertFalse(hasattr(self.conf, self.opt_dest))
        self.assertFalse(hasattr(self.conf, self.broken_opt_dest))
        self.assertIn('foobar', self.conf)
        self.assertNotIn(self.opt_dest, self.conf)
        self.assertNotIn(self.broken_opt_dest, self.conf)

    def test_deprecated_name_cli(self):
        self.conf.register_cli_opt(cfg.BoolOpt('foobar',
                                               deprecated_name=self.opt_name))

        # FIXME(markmc): this should be self.cli_name, see #1279973
        if self.broken:
            self.conf(['--' + self.broken_cli_name])
        else:
            self.conf(['--' + self.cli_name])

        self.assertTrue(self.conf.foobar)

    def test_deprecated_name_config_file(self):
        self.conf.register_opt(cfg.BoolOpt('foobar',
                                           deprecated_name=self.opt_name))

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n' +
                                        self.cf_name + ' = True\n')])

        self.conf(['--config-file', paths[0]])

        self.assertTrue(self.conf.foobar)

    def test_deprecated_opts(self):
        oldopts = [cfg.DeprecatedOpt(self.opt_name)]
        self.conf.register_opt(cfg.StrOpt('foobar',
                                          deprecated_opts=oldopts))

        self.assertTrue(hasattr(self.conf, 'foobar'))
        self.assertFalse(hasattr(self.conf, self.opt_dest))
        self.assertFalse(hasattr(self.conf, self.broken_opt_dest))
        self.assertIn('foobar', self.conf)
        self.assertNotIn(self.opt_dest, self.conf)
        self.assertNotIn(self.broken_opt_dest, self.conf)

    def test_deprecated_opts_cli(self):
        oldopts = [cfg.DeprecatedOpt(self.opt_name)]
        self.conf.register_cli_opt(cfg.BoolOpt('foobar',
                                               deprecated_opts=oldopts))

        self.conf(['--' + self.cli_name])

        self.assertTrue(self.conf.foobar)

    def test_deprecated_opts_config_file(self):
        oldopts = [cfg.DeprecatedOpt(self.opt_name)]
        self.conf.register_opt(cfg.BoolOpt('foobar',
                                           deprecated_opts=oldopts))

        # FIXME(markmc): this should be self.cf_name, see #1279973
        if self.broken:
            paths = self.create_tempfiles([('test',
                                            '[DEFAULT]\n' +
                                            self.broken_cf_name +
                                            ' = True\n')])
        else:
            paths = self.create_tempfiles([('test',
                                            '[DEFAULT]\n' +
                                            self.cf_name + ' = True\n')])

        self.conf(['--config-file', paths[0]])

        self.assertTrue(self.conf.foobar)


class ReRegisterOptTestCase(BaseTestCase):

    def test_conf_file_re_register_opt(self):
        opt = cfg.StrOpt('foo')
        self.assertTrue(self.conf.register_opt(opt))
        self.assertFalse(self.conf.register_opt(opt))

    def test_conf_file_re_register_opt_in_group(self):
        group = cfg.OptGroup('blaa')
        self.conf.register_group(group)
        self.conf.register_group(group)  # not an error
        opt = cfg.StrOpt('foo')
        self.assertTrue(self.conf.register_opt(opt, group=group))
        self.assertFalse(self.conf.register_opt(opt, group='blaa'))


class TemplateSubstitutionTestCase(BaseTestCase):

    def _prep_test_str_sub(self, foo_default=None, bar_default=None):
        self.conf.register_cli_opt(cfg.StrOpt('foo', default=foo_default))
        self.conf.register_cli_opt(cfg.StrOpt('bar', default=bar_default))

    def _assert_str_sub(self):
        self.assertTrue(hasattr(self.conf, 'bar'))
        self.assertEqual(self.conf.bar, 'blaa')

    def test_str_sub_default_from_default(self):
        self._prep_test_str_sub(foo_default='blaa', bar_default='$foo')

        self.conf([])

        self._assert_str_sub()

    def test_str_sub_default_from_default_recurse(self):
        self.conf.register_cli_opt(cfg.StrOpt('blaa', default='blaa'))
        self._prep_test_str_sub(foo_default='$blaa', bar_default='$foo')

        self.conf([])

        self._assert_str_sub()

    def test_str_sub_default_from_arg(self):
        self._prep_test_str_sub(bar_default='$foo')

        self.conf(['--foo', 'blaa'])

        self._assert_str_sub()

    def test_str_sub_default_from_config_file(self):
        self._prep_test_str_sub(bar_default='$foo')

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n'
                                        'foo = blaa\n')])

        self.conf(['--config-file', paths[0]])

        self._assert_str_sub()

    def test_str_sub_arg_from_default(self):
        self._prep_test_str_sub(foo_default='blaa')

        self.conf(['--bar', '$foo'])

        self._assert_str_sub()

    def test_str_sub_arg_from_arg(self):
        self._prep_test_str_sub()

        self.conf(['--foo', 'blaa', '--bar', '$foo'])

        self._assert_str_sub()

    def test_str_sub_arg_from_config_file(self):
        self._prep_test_str_sub()

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n'
                                        'foo = blaa\n')])

        self.conf(['--config-file', paths[0], '--bar=$foo'])

        self._assert_str_sub()

    def test_str_sub_config_file_from_default(self):
        self._prep_test_str_sub(foo_default='blaa')

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n'
                                        'bar = $foo\n')])

        self.conf(['--config-file', paths[0]])

        self._assert_str_sub()

    def test_str_sub_config_file_from_arg(self):
        self._prep_test_str_sub()

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n'
                                        'bar = $foo\n')])

        self.conf(['--config-file', paths[0], '--foo=blaa'])

        self._assert_str_sub()

    def test_str_sub_config_file_from_config_file(self):
        self._prep_test_str_sub()

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n'
                                        'bar = $foo\n'
                                        'foo = blaa\n')])

        self.conf(['--config-file', paths[0]])

        self._assert_str_sub()

    def test_str_sub_with_dollar_escape_char(self):
        self._prep_test_str_sub()

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n'
                                        'bar=foo-somethin$$k2\n')])

        self.conf(['--config-file', paths[0]])

        self.assertTrue(hasattr(self.conf, 'bar'))
        self.assertEqual(self.conf.bar, 'foo-somethin$k2')

    def test_str_sub_with_backslash_escape_char(self):
        self._prep_test_str_sub()

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n'
                                        'bar=foo-somethin\$k2\n')])

        self.conf(['--config-file', paths[0]])

        self.assertTrue(hasattr(self.conf, 'bar'))
        self.assertEqual(self.conf.bar, 'foo-somethin$k2')

    def test_str_sub_group_from_default(self):
        self.conf.register_cli_opt(cfg.StrOpt('foo', default='blaa'))
        self.conf.register_group(cfg.OptGroup('ba'))
        self.conf.register_cli_opt(cfg.StrOpt('r', default='$foo'), group='ba')

        self.conf([])

        self.assertTrue(hasattr(self.conf, 'ba'))
        self.assertTrue(hasattr(self.conf.ba, 'r'))
        self.assertEqual(self.conf.ba.r, 'blaa')

    def test_str_sub_set_default(self):
        self._prep_test_str_sub()
        self.conf.set_default('bar', '$foo')
        self.conf.set_default('foo', 'blaa')

        self.conf([])

        self._assert_str_sub()

    def test_str_sub_set_override(self):
        self._prep_test_str_sub()
        self.conf.set_override('bar', '$foo')
        self.conf.set_override('foo', 'blaa')

        self.conf([])

        self._assert_str_sub()

    def _prep_test_str_int_sub(self, foo_default=None, bar_default=None):
        self.conf.register_cli_opt(cfg.StrOpt('foo', default=foo_default))
        self.conf.register_cli_opt(cfg.IntOpt('bar', default=bar_default))

    def _assert_int_sub(self):
        self.assertTrue(hasattr(self.conf, 'bar'))
        self.assertEqual(self.conf.bar, 123)

    def test_sub_default_from_default(self):
        self._prep_test_str_int_sub(foo_default='123', bar_default='$foo')

        self.conf([])

        self._assert_int_sub()

    def test_sub_default_from_default_recurse(self):
        self.conf.register_cli_opt(cfg.StrOpt('blaa', default='123'))
        self._prep_test_str_int_sub(foo_default='$blaa', bar_default='$foo')

        self.conf([])

        self._assert_int_sub()

    def test_sub_default_from_arg(self):
        self._prep_test_str_int_sub(bar_default='$foo')

        self.conf(['--foo', '123'])

        self._assert_int_sub()

    def test_sub_default_from_config_file(self):
        self._prep_test_str_int_sub(bar_default='$foo')

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n'
                                        'foo = 123\n')])

        self.conf(['--config-file', paths[0]])

        self._assert_int_sub()

    def test_sub_arg_from_default(self):
        self._prep_test_str_int_sub(foo_default='123')

        self.conf(['--bar', '$foo'])

        self._assert_int_sub()

    def test_sub_arg_from_arg(self):
        self._prep_test_str_int_sub()

        self.conf(['--foo', '123', '--bar', '$foo'])

        self._assert_int_sub()

    def test_sub_arg_from_config_file(self):
        self._prep_test_str_int_sub()

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n'
                                        'foo = 123\n')])

        self.conf(['--config-file', paths[0], '--bar=$foo'])

        self._assert_int_sub()

    def test_sub_config_file_from_default(self):
        self._prep_test_str_int_sub(foo_default='123')

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n'
                                        'bar = $foo\n')])

        self.conf(['--config-file', paths[0]])

        self._assert_int_sub()

    def test_sub_config_file_from_arg(self):
        self._prep_test_str_int_sub()

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n'
                                        'bar = $foo\n')])

        self.conf(['--config-file', paths[0], '--foo=123'])

        self._assert_int_sub()

    def test_sub_config_file_from_config_file(self):
        self._prep_test_str_int_sub()

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n'
                                        'bar = $foo\n'
                                        'foo = 123\n')])

        self.conf(['--config-file', paths[0]])

        self._assert_int_sub()

    def test_sub_group_from_default(self):
        self.conf.register_cli_opt(cfg.StrOpt('foo', default='123'))
        self.conf.register_group(cfg.OptGroup('ba'))
        self.conf.register_cli_opt(cfg.IntOpt('r', default='$foo'), group='ba')

        self.conf([])

        self.assertTrue(hasattr(self.conf, 'ba'))
        self.assertTrue(hasattr(self.conf.ba, 'r'))
        self.assertEqual(self.conf.foo, '123')
        self.assertEqual(self.conf.ba.r, 123)

    def test_sub_group_from_default_deprecated(self):
        self.conf.register_group(cfg.OptGroup('ba'))
        self.conf.register_cli_opt(cfg.StrOpt(
            'foo', default='123', deprecated_group='DEFAULT'), group='ba')
        self.conf.register_cli_opt(cfg.IntOpt('r', default='$foo'), group='ba')

        self.conf([])

        self.assertTrue(hasattr(self.conf, 'ba'))
        self.assertTrue(hasattr(self.conf.ba, 'foo'))
        self.assertEqual(self.conf.ba.foo, '123')
        self.assertTrue(hasattr(self.conf.ba, 'r'))
        self.assertEqual(self.conf.ba.r, 123)

    def test_sub_group_from_args_deprecated(self):
        self.conf.register_group(cfg.OptGroup('ba'))
        self.conf.register_cli_opt(cfg.StrOpt(
            'foo', default='123', deprecated_group='DEFAULT'), group='ba')
        self.conf.register_cli_opt(cfg.IntOpt('r', default='$foo'), group='ba')

        self.conf(['--ba-foo=4242'])

        self.assertTrue(hasattr(self.conf, 'ba'))
        self.assertTrue(hasattr(self.conf.ba, 'foo'))
        self.assertTrue(hasattr(self.conf.ba, 'r'))
        self.assertEqual(self.conf.ba.foo, '4242')
        self.assertEqual(self.conf.ba.r, 4242)

    def test_sub_group_from_configfile_deprecated(self):
        self.conf.register_group(cfg.OptGroup('ba'))
        self.conf.register_cli_opt(cfg.StrOpt(
            'foo', default='123', deprecated_group='DEFAULT'), group='ba')
        self.conf.register_cli_opt(cfg.IntOpt('r', default='$foo'), group='ba')

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n'
                                        'foo=4242\n')])

        self.conf(['--config-file', paths[0]])

        self.assertTrue(hasattr(self.conf, 'ba'))
        self.assertTrue(hasattr(self.conf.ba, 'foo'))
        self.assertTrue(hasattr(self.conf.ba, 'r'))
        self.assertEqual(self.conf.ba.foo, '4242')
        self.assertEqual(self.conf.ba.r, 4242)


class ConfigDirTestCase(BaseTestCase):

    def test_config_dir(self):
        snafu_group = cfg.OptGroup('snafu')
        self.conf.register_group(snafu_group)
        self.conf.register_cli_opt(cfg.StrOpt('foo'))
        self.conf.register_cli_opt(cfg.StrOpt('bell'), group=snafu_group)

        dir = tempfile.mkdtemp()
        self.tempdirs.append(dir)

        paths = self.create_tempfiles([(os.path.join(dir, '00-test'),
                                        '[DEFAULT]\n'
                                        'foo = bar-00\n'
                                        '[snafu]\n'
                                        'bell = whistle-00\n'),
                                       (os.path.join(dir, '02-test'),
                                        '[snafu]\n'
                                        'bell = whistle-02\n'
                                        '[DEFAULT]\n'
                                        'foo = bar-02\n'),
                                       (os.path.join(dir, '01-test'),
                                        '[DEFAULT]\n'
                                        'foo = bar-01\n')])

        self.conf(['--foo', 'bar',
                   '--config-dir', os.path.dirname(paths[0])])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, 'bar-02')
        self.assertTrue(hasattr(self.conf, 'snafu'))
        self.assertTrue(hasattr(self.conf.snafu, 'bell'))
        self.assertEqual(self.conf.snafu.bell, 'whistle-02')

    def test_config_dir_file_precedence(self):
        snafu_group = cfg.OptGroup('snafu')
        self.conf.register_group(snafu_group)
        self.conf.register_cli_opt(cfg.StrOpt('foo'))
        self.conf.register_cli_opt(cfg.StrOpt('bell'), group=snafu_group)

        dir = tempfile.mkdtemp()
        self.tempdirs.append(dir)

        paths = self.create_tempfiles([(os.path.join(dir, '00-test'),
                                        '[DEFAULT]\n'
                                        'foo = bar-00\n'),
                                       ('01-test',
                                        '[snafu]\n'
                                        'bell = whistle-01\n'
                                        '[DEFAULT]\n'
                                        'foo = bar-01\n'),
                                       ('03-test',
                                        '[snafu]\n'
                                        'bell = whistle-03\n'
                                        '[DEFAULT]\n'
                                        'foo = bar-03\n'),
                                       (os.path.join(dir, '02-test'),
                                        '[DEFAULT]\n'
                                        'foo = bar-02\n')])

        self.conf(['--foo', 'bar',
                   '--config-file', paths[1],
                   '--config-dir', os.path.dirname(paths[0]),
                   '--config-file', paths[2], ])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, 'bar-03')
        self.assertTrue(hasattr(self.conf, 'snafu'))
        self.assertTrue(hasattr(self.conf.snafu, 'bell'))
        self.assertEqual(self.conf.snafu.bell, 'whistle-03')

    def test_config_dir_default_file_precedence(self):
        snafu_group = cfg.OptGroup('snafu')
        self.conf.register_group(snafu_group)
        self.conf.register_cli_opt(cfg.StrOpt('foo'))
        self.conf.register_cli_opt(cfg.StrOpt('bell'), group=snafu_group)

        dir = tempfile.mkdtemp()
        self.tempdirs.append(dir)

        paths = self.create_tempfiles([(os.path.join(dir, '00-test'),
                                        '[DEFAULT]\n'
                                        'foo = bar-00\n'
                                        '[snafu]\n'
                                        'bell = whistle-11\n'),
                                       ('01-test',
                                        '[snafu]\n'
                                        'bell = whistle-01\n'
                                        '[DEFAULT]\n'
                                        'foo = bar-01\n'),
                                       ('03-test',
                                        '[snafu]\n'
                                        'bell = whistle-03\n'
                                        '[DEFAULT]\n'
                                        'foo = bar-03\n'),
                                       (os.path.join(dir, '02-test'),
                                        '[DEFAULT]\n'
                                        'foo = bar-02\n')])

        self.conf(['--foo', 'bar', '--config-dir', os.path.dirname(paths[0])],
                  default_config_files=[paths[1], paths[2]])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, 'bar-02')
        self.assertTrue(hasattr(self.conf, 'snafu'))
        self.assertTrue(hasattr(self.conf.snafu, 'bell'))
        self.assertEqual(self.conf.snafu.bell, 'whistle-11')

    def test_config_dir_doesnt_exist(self):
        tmpdir = '/tmp/foo'

        self.assertRaises(cfg.ConfigDirNotFoundError,
                          self.conf,
                          ['--config-dir', tmpdir]
                          )


class ReparseTestCase(BaseTestCase):

    def test_reparse(self):
        self.conf.register_group(cfg.OptGroup('blaa'))
        self.conf.register_cli_opt(
            cfg.StrOpt('foo', default='r'), group='blaa')

        paths = self.create_tempfiles([('test',
                                        '[blaa]\n'
                                        'foo = b\n')])

        self.conf(['--config-file', paths[0]])

        self.assertTrue(hasattr(self.conf, 'blaa'))
        self.assertTrue(hasattr(self.conf.blaa, 'foo'))
        self.assertEqual(self.conf.blaa.foo, 'b')

        self.conf(['--blaa-foo', 'a'])

        self.assertTrue(hasattr(self.conf, 'blaa'))
        self.assertTrue(hasattr(self.conf.blaa, 'foo'))
        self.assertEqual(self.conf.blaa.foo, 'a')

        self.conf([])

        self.assertTrue(hasattr(self.conf, 'blaa'))
        self.assertTrue(hasattr(self.conf.blaa, 'foo'))
        self.assertEqual(self.conf.blaa.foo, 'r')


class OverridesTestCase(BaseTestCase):

    def test_default_none(self):
        self.conf.register_opt(cfg.StrOpt('foo', default='foo'))
        self.conf([])
        self.assertEqual(self.conf.foo, 'foo')
        self.conf.set_default('foo', None)
        self.assertIsNone(self.conf.foo)
        self.conf.clear_default('foo')
        self.assertEqual(self.conf.foo, 'foo')

    def test_override_none(self):
        self.conf.register_opt(cfg.StrOpt('foo', default='foo'))
        self.conf([])
        self.assertEqual(self.conf.foo, 'foo')
        self.conf.set_override('foo', None)
        self.assertIsNone(self.conf.foo)
        self.conf.clear_override('foo')
        self.assertEqual(self.conf.foo, 'foo')

    def test_no_default_override(self):
        self.conf.register_opt(cfg.StrOpt('foo'))
        self.conf([])
        self.assertIsNone(self.conf.foo)
        self.conf.set_default('foo', 'bar')
        self.assertEqual(self.conf.foo, 'bar')
        self.conf.clear_default('foo')
        self.assertIsNone(self.conf.foo)

    def test_default_override(self):
        self.conf.register_opt(cfg.StrOpt('foo', default='foo'))
        self.conf([])
        self.assertEqual(self.conf.foo, 'foo')
        self.conf.set_default('foo', 'bar')
        self.assertEqual(self.conf.foo, 'bar')
        self.conf.clear_default('foo')
        self.assertEqual(self.conf.foo, 'foo')

    def test_override(self):
        self.conf.register_opt(cfg.StrOpt('foo'))
        self.conf.set_override('foo', 'bar')
        self.conf([])
        self.assertEqual(self.conf.foo, 'bar')
        self.conf.clear_override('foo')
        self.assertIsNone(self.conf.foo)

    def test_group_no_default_override(self):
        self.conf.register_group(cfg.OptGroup('blaa'))
        self.conf.register_opt(cfg.StrOpt('foo'), group='blaa')
        self.conf([])
        self.assertIsNone(self.conf.blaa.foo)
        self.conf.set_default('foo', 'bar', group='blaa')
        self.assertEqual(self.conf.blaa.foo, 'bar')
        self.conf.clear_default('foo', group='blaa')
        self.assertIsNone(self.conf.blaa.foo)

    def test_group_default_override(self):
        self.conf.register_group(cfg.OptGroup('blaa'))
        self.conf.register_opt(cfg.StrOpt('foo', default='foo'), group='blaa')
        self.conf([])
        self.assertEqual(self.conf.blaa.foo, 'foo')
        self.conf.set_default('foo', 'bar', group='blaa')
        self.assertEqual(self.conf.blaa.foo, 'bar')
        self.conf.clear_default('foo', group='blaa')
        self.assertEqual(self.conf.blaa.foo, 'foo')

    def test_group_override(self):
        self.conf.register_group(cfg.OptGroup('blaa'))
        self.conf.register_opt(cfg.StrOpt('foo'), group='blaa')
        self.assertIsNone(self.conf.blaa.foo)
        self.conf.set_override('foo', 'bar', group='blaa')
        self.conf([])
        self.assertEqual(self.conf.blaa.foo, 'bar')
        self.conf.clear_override('foo', group='blaa')
        self.assertIsNone(self.conf.blaa.foo)

    def test_cli_bool_default(self):
        self.conf.register_cli_opt(cfg.BoolOpt('foo'))
        self.conf.set_default('foo', True)
        self.assertTrue(self.conf.foo)
        self.conf([])
        self.assertTrue(self.conf.foo)
        self.conf.set_default('foo', False)
        self.assertFalse(self.conf.foo)
        self.conf.clear_default('foo')
        self.assertIsNone(self.conf.foo)

    def test_cli_bool_override(self):
        self.conf.register_cli_opt(cfg.BoolOpt('foo'))
        self.conf.set_override('foo', True)
        self.assertTrue(self.conf.foo)
        self.conf([])
        self.assertTrue(self.conf.foo)
        self.conf.set_override('foo', False)
        self.assertFalse(self.conf.foo)
        self.conf.clear_override('foo')
        self.assertIsNone(self.conf.foo)


class ResetAndClearTestCase(BaseTestCase):

    def test_clear(self):
        self.conf.register_cli_opt(cfg.StrOpt('foo'))
        self.conf.register_cli_opt(cfg.StrOpt('bar'), group='blaa')

        self.assertIsNone(self.conf.foo)
        self.assertIsNone(self.conf.blaa.bar)

        self.conf(['--foo', 'foo', '--blaa-bar', 'bar'])

        self.assertEqual(self.conf.foo, 'foo')
        self.assertEqual(self.conf.blaa.bar, 'bar')

        self.conf.clear()

        self.assertIsNone(self.conf.foo)
        self.assertIsNone(self.conf.blaa.bar)

    def test_reset_and_clear_with_defaults_and_overrides(self):
        self.conf.register_cli_opt(cfg.StrOpt('foo'))
        self.conf.register_cli_opt(cfg.StrOpt('bar'), group='blaa')

        self.conf.set_default('foo', 'foo')
        self.conf.set_override('bar', 'bar', group='blaa')

        self.conf(['--foo', 'foofoo'])

        self.assertEqual(self.conf.foo, 'foofoo')
        self.assertEqual(self.conf.blaa.bar, 'bar')

        self.conf.clear()

        self.assertEqual(self.conf.foo, 'foo')
        self.assertEqual(self.conf.blaa.bar, 'bar')

        self.conf.reset()

        self.assertIsNone(self.conf.foo)
        self.assertIsNone(self.conf.blaa.bar)


class UnregisterOptTestCase(BaseTestCase):

    def test_unregister_opt(self):
        opts = [cfg.StrOpt('foo'), cfg.StrOpt('bar')]

        self.conf.register_opts(opts)

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertTrue(hasattr(self.conf, 'bar'))

        self.conf.unregister_opt(opts[0])

        self.assertFalse(hasattr(self.conf, 'foo'))
        self.assertTrue(hasattr(self.conf, 'bar'))

        self.conf([])

        self.assertRaises(cfg.ArgsAlreadyParsedError,
                          self.conf.unregister_opt, opts[1])

        self.conf.clear()

        self.assertTrue(hasattr(self.conf, 'bar'))

        self.conf.unregister_opts(opts)

    def test_unregister_opt_from_group(self):
        opt = cfg.StrOpt('foo')

        self.conf.register_opt(opt, group='blaa')

        self.assertTrue(hasattr(self.conf, 'blaa'))
        self.assertTrue(hasattr(self.conf.blaa, 'foo'))

        self.conf.unregister_opt(opt, group='blaa')

        self.assertFalse(hasattr(self.conf.blaa, 'foo'))


class ImportOptTestCase(BaseTestCase):

    def test_import_opt(self):
        self.assertFalse(hasattr(cfg.CONF, 'blaa'))
        cfg.CONF.import_opt('blaa', 'tests.testmods.blaa_opt')
        self.assertTrue(hasattr(cfg.CONF, 'blaa'))

    def test_import_opt_in_group(self):
        self.assertFalse(hasattr(cfg.CONF, 'bar'))
        cfg.CONF.import_opt('foo', 'tests.testmods.bar_foo_opt', group='bar')
        self.assertTrue(hasattr(cfg.CONF, 'bar'))
        self.assertTrue(hasattr(cfg.CONF.bar, 'foo'))

    def test_import_opt_import_errror(self):
        self.assertRaises(ImportError, cfg.CONF.import_opt,
                          'blaa', 'tests.testmods.blaablaa_opt')

    def test_import_opt_no_such_opt(self):
        self.assertRaises(cfg.NoSuchOptError, cfg.CONF.import_opt,
                          'blaablaa', 'tests.testmods.blaa_opt')

    def test_import_opt_no_such_group(self):
        self.assertRaises(cfg.NoSuchGroupError, cfg.CONF.import_opt,
                          'blaa', 'tests.testmods.blaa_opt', group='blaa')


class ImportGroupTestCase(BaseTestCase):

    def test_import_group(self):
        self.assertFalse(hasattr(cfg.CONF, 'qux'))
        cfg.CONF.import_group('qux', 'tests.testmods.baz_qux_opt')
        self.assertTrue(hasattr(cfg.CONF, 'qux'))
        self.assertTrue(hasattr(cfg.CONF.qux, 'baz'))

    def test_import_group_import_error(self):
        self.assertRaises(ImportError, cfg.CONF.import_group,
                          'qux', 'tests.testmods.bazzz_quxxx_opt')

    def test_import_group_no_such_group(self):
        self.assertRaises(cfg.NoSuchGroupError, cfg.CONF.import_group,
                          'quxxx', 'tests.testmods.baz_qux_opt')


class RequiredOptsTestCase(BaseTestCase):

    def setUp(self):
        BaseTestCase.setUp(self)
        self.conf.register_opt(cfg.StrOpt('boo', required=False))

    def test_required_opt(self):
        self.conf.register_opt(cfg.StrOpt('foo', required=True))

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n'
                                        'foo = bar')])

        self.conf(['--config-file', paths[0]])
        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, 'bar')

    def test_required_cli_opt(self):
        self.conf.register_cli_opt(cfg.StrOpt('foo', required=True))

        self.conf(['--foo', 'bar'])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, 'bar')

    def test_required_cli_opt_with_dash(self):
        self.conf.register_cli_opt(cfg.StrOpt('foo-bar', required=True))

        self.conf(['--foo-bar', 'baz'])

        self.assertTrue(hasattr(self.conf, 'foo_bar'))
        self.assertEqual(self.conf.foo_bar, 'baz')

    def test_missing_required_opt(self):
        self.conf.register_opt(cfg.StrOpt('foo', required=True))
        self.assertRaises(cfg.RequiredOptError, self.conf, [])

    def test_missing_required_cli_opt(self):
        self.conf.register_cli_opt(cfg.StrOpt('foo', required=True))
        self.assertRaises(cfg.RequiredOptError, self.conf, [])

    def test_required_group_opt(self):
        self.conf.register_group(cfg.OptGroup('blaa'))
        self.conf.register_opt(cfg.StrOpt('foo', required=True), group='blaa')

        paths = self.create_tempfiles([('test',
                                        '[blaa]\n'
                                        'foo = bar')])

        self.conf(['--config-file', paths[0]])
        self.assertTrue(hasattr(self.conf, 'blaa'))
        self.assertTrue(hasattr(self.conf.blaa, 'foo'))
        self.assertEqual(self.conf.blaa.foo, 'bar')

    def test_required_cli_group_opt(self):
        self.conf.register_group(cfg.OptGroup('blaa'))
        self.conf.register_cli_opt(
            cfg.StrOpt('foo', required=True), group='blaa')

        self.conf(['--blaa-foo', 'bar'])

        self.assertTrue(hasattr(self.conf, 'blaa'))
        self.assertTrue(hasattr(self.conf.blaa, 'foo'))
        self.assertEqual(self.conf.blaa.foo, 'bar')

    def test_missing_required_group_opt(self):
        self.conf.register_group(cfg.OptGroup('blaa'))
        self.conf.register_opt(cfg.StrOpt('foo', required=True), group='blaa')
        self.assertRaises(cfg.RequiredOptError, self.conf, [])

    def test_missing_required_cli_group_opt(self):
        self.conf.register_group(cfg.OptGroup('blaa'))
        self.conf.register_cli_opt(
            cfg.StrOpt('foo', required=True), group='blaa')
        self.assertRaises(cfg.RequiredOptError, self.conf, [])

    def test_required_opt_with_default(self):
        self.conf.register_cli_opt(cfg.StrOpt('foo', required=True))
        self.conf.set_default('foo', 'bar')

        self.conf([])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, 'bar')

    def test_required_opt_with_override(self):
        self.conf.register_cli_opt(cfg.StrOpt('foo', required=True))
        self.conf.set_override('foo', 'bar')

        self.conf([])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, 'bar')


class SadPathTestCase(BaseTestCase):

    def test_unknown_attr(self):
        self.conf([])
        self.assertFalse(hasattr(self.conf, 'foo'))
        self.assertRaises(AttributeError, getattr, self.conf, 'foo')
        self.assertRaises(cfg.NoSuchOptError, self.conf._get, 'foo')
        self.assertRaises(cfg.NoSuchOptError, self.conf.__getattr__, 'foo')

    def test_unknown_attr_is_attr_error(self):
        self.conf([])
        self.assertFalse(hasattr(self.conf, 'foo'))
        self.assertRaises(AttributeError, getattr, self.conf, 'foo')

    def test_unknown_group_attr(self):
        self.conf.register_group(cfg.OptGroup('blaa'))

        self.conf([])

        self.assertTrue(hasattr(self.conf, 'blaa'))
        self.assertFalse(hasattr(self.conf.blaa, 'foo'))
        self.assertRaises(cfg.NoSuchOptError, getattr, self.conf.blaa, 'foo')

    def test_ok_duplicate(self):
        opt = cfg.StrOpt('foo')
        self.conf.register_cli_opt(opt)
        opt2 = cfg.StrOpt('foo')
        self.conf.register_cli_opt(opt2)

        self.conf([])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertIsNone(self.conf.foo)

    def test_error_duplicate(self):
        self.conf.register_cli_opt(cfg.StrOpt('foo', help='bar'))
        self.assertRaises(cfg.DuplicateOptError,
                          self.conf.register_cli_opt, cfg.StrOpt('foo'))

    def test_error_duplicate_with_different_dest(self):
        self.conf.register_cli_opt(cfg.StrOpt('foo', dest='f'))
        self.conf.register_cli_opt(cfg.StrOpt('foo'))
        self.assertRaises(cfg.DuplicateOptError, self.conf, [])

    def test_error_duplicate_short(self):
        self.conf.register_cli_opt(cfg.StrOpt('foo', short='f'))
        self.conf.register_cli_opt(cfg.StrOpt('bar', short='f'))
        self.assertRaises(cfg.DuplicateOptError, self.conf, [])

    def test_already_parsed(self):
        self.conf([])

        self.assertRaises(cfg.ArgsAlreadyParsedError,
                          self.conf.register_cli_opt, cfg.StrOpt('foo'))

    def test_bad_cli_arg(self):
        self.conf.register_opt(cfg.BoolOpt('foo'))

        self.useFixture(fixtures.MonkeyPatch('sys.stderr', moves.StringIO()))

        self.assertRaises(SystemExit, self.conf, ['--foo'])

        self.assertTrue('error' in sys.stderr.getvalue())
        self.assertTrue('--foo' in sys.stderr.getvalue())

    def _do_test_bad_cli_value(self, opt_class):
        self.conf.register_cli_opt(opt_class('foo'))

        self.useFixture(fixtures.MonkeyPatch('sys.stderr', moves.StringIO()))

        self.assertRaises(SystemExit, self.conf, ['--foo', 'bar'])

        self.assertTrue('foo' in sys.stderr.getvalue())
        self.assertTrue('bar' in sys.stderr.getvalue())

    def test_bad_int_arg(self):
        self._do_test_bad_cli_value(cfg.IntOpt)

    def test_bad_float_arg(self):
        self._do_test_bad_cli_value(cfg.FloatOpt)

    def test_conf_file_not_found(self):
        (fd, path) = tempfile.mkstemp()

        os.remove(path)

        self.assertRaises(cfg.ConfigFilesNotFoundError,
                          self.conf, ['--config-file', path])

    def test_conf_file_permission_denied(self):
        (fd, path) = tempfile.mkstemp()

        os.chmod(path, 0x000)

        self.assertRaises(cfg.ConfigFilesPermissionDeniedError,
                          self.conf, ['--config-file', path])
        os.remove(path)

    def test_conf_file_broken(self):
        paths = self.create_tempfiles([('test', 'foo')])

        self.assertRaises(cfg.ConfigFileParseError,
                          self.conf, ['--config-file', paths[0]])

    def _do_test_conf_file_bad_value(self, opt_class):
        self.conf.register_opt(opt_class('foo'))

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n'
                                        'foo = bar\n')])

        self.conf(['--config-file', paths[0]])

        self.assertRaises(AttributeError, getattr, self.conf, 'foo')
        self.assertRaises(cfg.ConfigFileValueError, self.conf._get, 'foo')

    def test_conf_file_bad_bool(self):
        self._do_test_conf_file_bad_value(cfg.BoolOpt)

    def test_conf_file_bad_int(self):
        self._do_test_conf_file_bad_value(cfg.IntOpt)

    def test_conf_file_bad_float(self):
        self._do_test_conf_file_bad_value(cfg.FloatOpt)

    def test_str_sub_from_group(self):
        self.conf.register_group(cfg.OptGroup('f'))
        self.conf.register_cli_opt(cfg.StrOpt('oo', default='blaa'), group='f')
        self.conf.register_cli_opt(cfg.StrOpt('bar', default='$f.oo'))

        self.conf([])

        self.assertFalse(hasattr(self.conf, 'bar'))
        self.assertRaises(
            AttributeError, getattr, self.conf, 'bar')
        self.assertRaises(
            cfg.TemplateSubstitutionError, self.conf._get, 'bar')

    def test_set_default_unknown_attr(self):
        self.conf([])
        self.assertRaises(
            cfg.NoSuchOptError, self.conf.set_default, 'foo', 'bar')

    def test_set_default_unknown_group(self):
        self.conf([])
        self.assertRaises(cfg.NoSuchGroupError,
                          self.conf.set_default, 'foo', 'bar', group='blaa')

    def test_set_override_unknown_attr(self):
        self.conf([])
        self.assertRaises(
            cfg.NoSuchOptError, self.conf.set_override, 'foo', 'bar')

    def test_set_override_unknown_group(self):
        self.conf([])
        self.assertRaises(cfg.NoSuchGroupError,
                          self.conf.set_override, 'foo', 'bar', group='blaa')


class FindFileTestCase(BaseTestCase):

    def test_find_policy_file(self):
        policy_file = '/etc/policy.json'

        self.useFixture(fixtures.MonkeyPatch(
                        'os.path.exists',
                        lambda p: p == policy_file))

        self.conf([])

        self.assertIsNone(self.conf.find_file('foo.json'))
        self.assertEqual(self.conf.find_file('policy.json'), policy_file)

    def test_find_policy_file_with_config_file(self):
        dir = tempfile.mkdtemp()
        self.tempdirs.append(dir)

        paths = self.create_tempfiles([(os.path.join(dir, 'test.conf'),
                                        '[DEFAULT]'),
                                       (os.path.join(dir, 'policy.json'),
                                        '{}')],
                                      ext='')

        self.conf(['--config-file', paths[0]])

        self.assertEqual(self.conf.find_file('policy.json'), paths[1])

    def test_find_policy_file_with_config_dir(self):
        dir = tempfile.mkdtemp()
        self.tempdirs.append(dir)

        path = self.create_tempfiles([(os.path.join(dir, 'policy.json'),
                                       '{}')],
                                     ext='')[0]

        self.conf(['--config-dir', dir])

        self.assertEqual(self.conf.find_file('policy.json'), path)


class OptDumpingTestCase(BaseTestCase):

    class FakeLogger:

        def __init__(self, test_case, expected_lvl):
            self.test_case = test_case
            self.expected_lvl = expected_lvl
            self.logged = []

        def log(self, lvl, fmt, *args):
            self.test_case.assertEqual(lvl, self.expected_lvl)
            self.logged.append(fmt % args)

    def setUp(self):
        super(OptDumpingTestCase, self).setUp()
        self._args = ['--foo', 'this', '--blaa-bar', 'that',
                      '--blaa-key', 'admin', '--passwd', 'hush']

    def _do_test_log_opt_values(self, args):
        self.conf.register_cli_opt(cfg.StrOpt('foo'))
        self.conf.register_cli_opt(cfg.StrOpt('passwd', secret=True))
        self.conf.register_group(cfg.OptGroup('blaa'))
        self.conf.register_cli_opt(cfg.StrOpt('bar'), 'blaa')
        self.conf.register_cli_opt(cfg.StrOpt('key', secret=True), 'blaa')

        self.conf(args)

        logger = self.FakeLogger(self, 666)

        self.conf.log_opt_values(logger, 666)

        self.assertEqual(logger.logged, [
                         "*" * 80,
                         "Configuration options gathered from:",
                         "command line args: ['--foo', 'this', '--blaa-bar', "
                         "'that', '--blaa-key', 'admin', '--passwd', 'hush']",
                         "config files: []",
                         "=" * 80,
                         "config_dir                     = None",
                         "config_file                    = []",
                         "foo                            = this",
                         "passwd                         = ****",
                         "blaa.bar                       = that",
                         "blaa.key                       = ****",
                         "*" * 80,
                         ])

    def test_log_opt_values(self):
        self._do_test_log_opt_values(self._args)

    def test_log_opt_values_from_sys_argv(self):
        self.useFixture(fixtures.MonkeyPatch('sys.argv', ['foo'] + self._args))
        self._do_test_log_opt_values(None)


class ConfigParserTestCase(BaseTestCase):

    def test_parse_file(self):
        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n'
                                        'foo = bar\n'
                                        '[BLAA]\n'
                                        'bar = foo\n')])

        sections = {}
        parser = cfg.ConfigParser(paths[0], sections)
        parser.parse()

        self.assertTrue('DEFAULT' in sections)
        self.assertTrue('BLAA' in sections)
        self.assertEqual(sections['DEFAULT']['foo'], ['bar'])
        self.assertEqual(sections['BLAA']['bar'], ['foo'])

    def test_parse_file_with_normalized(self):
        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n'
                                        'foo = bar\n'
                                        '[BLAA]\n'
                                        'bar = foo\n')])

        sections = {}
        normalized = {}
        parser = cfg.ConfigParser(paths[0], sections)
        parser._add_normalized(normalized)
        parser.parse()

        self.assertTrue('DEFAULT' in sections)
        self.assertTrue('DEFAULT' in normalized)
        self.assertTrue('BLAA' in sections)
        self.assertTrue('blaa' in normalized)
        self.assertEqual(sections['DEFAULT']['foo'], ['bar'])
        self.assertEqual(normalized['DEFAULT']['foo'], ['bar'])
        self.assertEqual(sections['BLAA']['bar'], ['foo'])
        self.assertEqual(normalized['blaa']['bar'], ['foo'])

    def test_no_section(self):
        with tempfile.NamedTemporaryFile() as tmpfile:
            tmpfile.write(six.b('foo = bar'))
            tmpfile.flush()

            parser = cfg.ConfigParser(tmpfile.name, {})
            self.assertRaises(cfg.ParseError, parser.parse)

    def test__parse_file_ioerror(self):
        # Test that IOErrors (other than 'No such file or directory')
        # are propagated.
        filename = 'fake'
        namespace = mock.Mock()
        with mock.patch('oslo_config.cfg.ConfigParser.parse') as parse:
            parse.side_effect = IOError(errno.EMFILE, filename,
                                        'Too many open files')
            self.assertRaises(IOError, cfg.ConfigParser._parse_file, filename,
                              namespace)


class MultiConfigParserTestCase(BaseTestCase):

    def test_parse_single_file(self):
        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n'
                                        'foo = bar\n'
                                        '[BLAA]\n'
                                        'bar = foo\n')])

        parser = cfg.MultiConfigParser()
        read_ok = parser.read(paths)

        self.assertEqual(read_ok, paths)

        self.assertTrue('DEFAULT' in parser.parsed[0])
        self.assertEqual(parser.parsed[0]['DEFAULT']['foo'], ['bar'])
        self.assertEqual(parser.get([('DEFAULT', 'foo')]), ['bar'])
        self.assertEqual(parser.get([('DEFAULT', 'foo')], multi=True),
                         ['bar'])
        self.assertEqual(parser.get([('DEFAULT', 'foo')], multi=True),
                         ['bar'])
        self.assertEqual(parser._get([('DEFAULT', 'foo')],
                                     multi=True, normalized=True),
                         ['bar'])

        self.assertTrue('BLAA' in parser.parsed[0])
        self.assertEqual(parser.parsed[0]['BLAA']['bar'], ['foo'])
        self.assertEqual(parser.get([('BLAA', 'bar')]), ['foo'])
        self.assertEqual(parser.get([('BLAA', 'bar')], multi=True),
                         ['foo'])
        self.assertEqual(parser._get([('blaa', 'bar')],
                                     multi=True, normalized=True),
                         ['foo'])

    def test_parse_multiple_files(self):
        paths = self.create_tempfiles([('test1',
                                        '[DEFAULT]\n'
                                        'foo = bar\n'
                                        '[BLAA]\n'
                                        'bar = foo'),
                                       ('test2',
                                        '[DEFAULT]\n'
                                        'foo = barbar\n'
                                        '[BLAA]\n'
                                        'bar = foofoo\n'
                                        '[bLAa]\n'
                                        'bar = foofoofoo\n')])

        parser = cfg.MultiConfigParser()
        read_ok = parser.read(paths)

        self.assertEqual(read_ok, paths)

        self.assertTrue('DEFAULT' in parser.parsed[0])
        self.assertEqual(parser.parsed[0]['DEFAULT']['foo'], ['barbar'])
        self.assertTrue('DEFAULT' in parser.parsed[1])
        self.assertEqual(parser.parsed[1]['DEFAULT']['foo'], ['bar'])
        self.assertEqual(parser.get([('DEFAULT', 'foo')]), ['barbar'])
        self.assertEqual(parser.get([('DEFAULT', 'foo')], multi=True),
                         ['bar', 'barbar'])

        self.assertTrue('BLAA' in parser.parsed[0])
        self.assertTrue('bLAa' in parser.parsed[0])
        self.assertEqual(parser.parsed[0]['BLAA']['bar'], ['foofoo'])
        self.assertEqual(parser.parsed[0]['bLAa']['bar'], ['foofoofoo'])
        self.assertTrue('BLAA' in parser.parsed[1])
        self.assertEqual(parser.parsed[1]['BLAA']['bar'], ['foo'])
        self.assertEqual(parser.get([('BLAA', 'bar')]), ['foofoo'])
        self.assertEqual(parser.get([('bLAa', 'bar')]), ['foofoofoo'])
        self.assertEqual(parser.get([('BLAA', 'bar')], multi=True),
                         ['foo', 'foofoo'])
        self.assertEqual(parser._get([('BLAA', 'bar')],
                                     multi=True, normalized=True),
                         ['foo', 'foofoo', 'foofoofoo'])


class TildeExpansionTestCase(BaseTestCase):

    def test_config_file_tilde(self):
        homedir = os.path.expanduser('~')
        tmpfile = tempfile.mktemp(dir=homedir, prefix='cfg-', suffix='.conf')
        tmpbase = os.path.basename(tmpfile)

        try:
            self.conf(['--config-file', os.path.join('~', tmpbase)])
        except cfg.ConfigFilesNotFoundError as cfnfe:
            self.assertTrue(homedir in str(cfnfe))

        self.useFixture(fixtures.MonkeyPatch(
            'os.path.exists',
            lambda p: p == tmpfile))

        self.assertEqual(self.conf.find_file(tmpbase), tmpfile)

    def test_config_dir_tilde(self):
        homedir = os.path.expanduser('~')
        try:
            tmpdir = tempfile.mkdtemp(dir=homedir,
                                      prefix='cfg-',
                                      suffix='.d')
            tmpfile = os.path.join(tmpdir, 'foo.conf')

            self.useFixture(fixtures.MonkeyPatch(
                            'glob.glob',
                            lambda p: [tmpfile]))

            e = self.assertRaises(cfg.ConfigFilesNotFoundError,
                                  self.conf,
                                  ['--config-dir',
                                   os.path.join('~',
                                                os.path.basename(tmpdir))]
                                  )
            self.assertIn(tmpdir, str(e))
        finally:
            try:
                shutil.rmtree(tmpdir)
            except OSError as exc:
                if exc.errno != 2:
                    raise


class SubCommandTestCase(BaseTestCase):

    def test_sub_command(self):
        def add_parsers(subparsers):
            sub = subparsers.add_parser('a')
            sub.add_argument('bar', type=int)

        self.conf.register_cli_opt(
            cfg.SubCommandOpt('cmd', handler=add_parsers))
        self.assertTrue(hasattr(self.conf, 'cmd'))
        self.conf(['a', '10'])
        self.assertTrue(hasattr(self.conf.cmd, 'name'))
        self.assertTrue(hasattr(self.conf.cmd, 'bar'))
        self.assertEqual(self.conf.cmd.name, 'a')
        self.assertEqual(self.conf.cmd.bar, 10)

    def test_sub_command_with_parent(self):
        def add_parsers(subparsers):
            parent = argparse.ArgumentParser(add_help=False)
            parent.add_argument('bar', type=int)
            subparsers.add_parser('a', parents=[parent])

        self.conf.register_cli_opt(
            cfg.SubCommandOpt('cmd', handler=add_parsers))
        self.assertTrue(hasattr(self.conf, 'cmd'))
        self.conf(['a', '10'])
        self.assertTrue(hasattr(self.conf.cmd, 'name'))
        self.assertTrue(hasattr(self.conf.cmd, 'bar'))
        self.assertEqual(self.conf.cmd.name, 'a')
        self.assertEqual(self.conf.cmd.bar, 10)

    def test_sub_command_with_dest(self):
        def add_parsers(subparsers):
            subparsers.add_parser('a')

        self.conf.register_cli_opt(
            cfg.SubCommandOpt('cmd', dest='command', handler=add_parsers))
        self.assertTrue(hasattr(self.conf, 'command'))
        self.conf(['a'])
        self.assertEqual(self.conf.command.name, 'a')

    def test_sub_command_with_group(self):
        def add_parsers(subparsers):
            sub = subparsers.add_parser('a')
            sub.add_argument('--bar', choices='XYZ')

        self.conf.register_cli_opt(
            cfg.SubCommandOpt('cmd', handler=add_parsers), group='blaa')
        self.assertTrue(hasattr(self.conf, 'blaa'))
        self.assertTrue(hasattr(self.conf.blaa, 'cmd'))
        self.conf(['a', '--bar', 'Z'])
        self.assertTrue(hasattr(self.conf.blaa.cmd, 'name'))
        self.assertTrue(hasattr(self.conf.blaa.cmd, 'bar'))
        self.assertEqual(self.conf.blaa.cmd.name, 'a')
        self.assertEqual(self.conf.blaa.cmd.bar, 'Z')

    def test_sub_command_not_cli(self):
        self.conf.register_opt(cfg.SubCommandOpt('cmd'))
        self.conf([])

    def test_sub_command_resparse(self):
        def add_parsers(subparsers):
            subparsers.add_parser('a')

        self.conf.register_cli_opt(
            cfg.SubCommandOpt('cmd', handler=add_parsers))

        foo_opt = cfg.StrOpt('foo')
        self.conf.register_cli_opt(foo_opt)

        self.conf(['--foo=bar', 'a'])

        self.assertTrue(hasattr(self.conf.cmd, 'name'))
        self.assertEqual(self.conf.cmd.name, 'a')
        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, 'bar')

        self.conf.clear()
        self.conf.unregister_opt(foo_opt)
        self.conf(['a'])

        self.assertTrue(hasattr(self.conf.cmd, 'name'))
        self.assertEqual(self.conf.cmd.name, 'a')
        self.assertFalse(hasattr(self.conf, 'foo'))

    def test_sub_command_no_handler(self):
        self.conf.register_cli_opt(cfg.SubCommandOpt('cmd'))
        self.useFixture(fixtures.MonkeyPatch('sys.stderr', moves.StringIO()))
        self.assertRaises(SystemExit, self.conf, [])
        self.assertTrue('error' in sys.stderr.getvalue())

    def test_sub_command_with_help(self):
        def add_parsers(subparsers):
            subparsers.add_parser('a')

        self.conf.register_cli_opt(cfg.SubCommandOpt('cmd',
                                                     title='foo foo',
                                                     description='bar bar',
                                                     help='blaa blaa',
                                                     handler=add_parsers))
        self.useFixture(fixtures.MonkeyPatch('sys.stdout', moves.StringIO()))
        self.assertRaises(SystemExit, self.conf, ['--help'])
        self.assertTrue('foo foo' in sys.stdout.getvalue())
        self.assertTrue('bar bar' in sys.stdout.getvalue())
        self.assertTrue('blaa blaa' in sys.stdout.getvalue())

    def test_sub_command_errors(self):
        def add_parsers(subparsers):
            sub = subparsers.add_parser('a')
            sub.add_argument('--bar')

        self.conf.register_cli_opt(cfg.BoolOpt('bar'))
        self.conf.register_cli_opt(
            cfg.SubCommandOpt('cmd', handler=add_parsers))
        self.conf(['a'])
        self.assertRaises(cfg.DuplicateOptError, getattr, self.conf.cmd, 'bar')
        self.assertRaises(cfg.NoSuchOptError, getattr, self.conf.cmd, 'foo')

    def test_sub_command_multiple(self):
        self.conf.register_cli_opt(cfg.SubCommandOpt('cmd1'))
        self.conf.register_cli_opt(cfg.SubCommandOpt('cmd2'))
        self.useFixture(fixtures.MonkeyPatch('sys.stderr', moves.StringIO()))
        self.assertRaises(SystemExit, self.conf, [])
        self.assertTrue('multiple' in sys.stderr.getvalue())


class SetDefaultsTestCase(BaseTestCase):

    def test_default_to_none(self):
        opts = [cfg.StrOpt('foo', default='foo')]
        self.conf.register_opts(opts)
        cfg.set_defaults(opts, foo=None)
        self.conf([])
        self.assertIsNone(self.conf.foo)

    def test_default_from_none(self):
        opts = [cfg.StrOpt('foo')]
        self.conf.register_opts(opts)
        cfg.set_defaults(opts, foo='bar')
        self.conf([])
        self.assertEqual(self.conf.foo, 'bar')

    def test_change_default(self):
        opts = [cfg.StrOpt('foo', default='foo')]
        self.conf.register_opts(opts)
        cfg.set_defaults(opts, foo='bar')
        self.conf([])
        self.assertEqual(self.conf.foo, 'bar')

    def test_change_default_many(self):
        opts = [cfg.StrOpt('foo', default='foo'),
                cfg.StrOpt('foo2', default='foo2')]
        self.conf.register_opts(opts)
        cfg.set_defaults(opts, foo='bar', foo2='bar2')
        self.conf([])
        self.assertEqual(self.conf.foo, 'bar')
        self.assertEqual(self.conf.foo2, 'bar2')

    def test_group_default_to_none(self):
        opts = [cfg.StrOpt('foo', default='foo')]
        self.conf.register_opts(opts, group='blaa')
        cfg.set_defaults(opts, foo=None)
        self.conf([])
        self.assertIsNone(self.conf.blaa.foo)

    def test_group_default_from_none(self):
        opts = [cfg.StrOpt('foo')]
        self.conf.register_opts(opts, group='blaa')
        cfg.set_defaults(opts, foo='bar')
        self.conf([])
        self.assertEqual(self.conf.blaa.foo, 'bar')

    def test_group_change_default(self):
        opts = [cfg.StrOpt('foo', default='foo')]
        self.conf.register_opts(opts, group='blaa')
        cfg.set_defaults(opts, foo='bar')
        self.conf([])
        self.assertEqual(self.conf.blaa.foo, 'bar')


class DeprecatedOptionsTestCase(BaseTestCase):

    def test_deprecated_opts_equal(self):
        d1 = cfg.DeprecatedOpt('oldfoo', group='oldgroup')
        d2 = cfg.DeprecatedOpt('oldfoo', group='oldgroup')
        self.assertEqual(d1, d2)

    def test_deprecated_opts_not_equal(self):
        d1 = cfg.DeprecatedOpt('oldfoo', group='oldgroup')
        d2 = cfg.DeprecatedOpt('oldfoo2', group='oldgroup')
        self.assertNotEqual(d1, d2)


class MultipleDeprecatedOptionsTestCase(BaseTestCase):

    def test_conf_file_override_use_deprecated_name_and_group(self):
        self.conf.register_group(cfg.OptGroup('blaa'))
        self.conf.register_opt(cfg.StrOpt('foo',
                                          deprecated_name='oldfoo',
                                          deprecated_group='oldgroup'),
                               group='blaa')

        paths = self.create_tempfiles([('test',
                                        '[oldgroup]\n'
                                        'oldfoo = bar\n')])

        self.conf(['--config-file', paths[0]])
        self.assertEqual(self.conf.blaa.foo, 'bar')

    def test_conf_file_override_use_deprecated_opts(self):
        self.conf.register_group(cfg.OptGroup('blaa'))
        oldopts = [cfg.DeprecatedOpt('oldfoo', group='oldgroup')]
        self.conf.register_opt(cfg.StrOpt('foo', deprecated_opts=oldopts),
                               group='blaa')

        paths = self.create_tempfiles([('test',
                                        '[oldgroup]\n'
                                        'oldfoo = bar\n')])

        self.conf(['--config-file', paths[0]])
        self.assertEqual(self.conf.blaa.foo, 'bar')

    def test_conf_file_override_use_deprecated_multi_opts(self):
        self.conf.register_group(cfg.OptGroup('blaa'))
        oldopts = [cfg.DeprecatedOpt('oldfoo', group='oldgroup'),
                   cfg.DeprecatedOpt('oldfoo2', group='oldgroup2')]
        self.conf.register_opt(cfg.StrOpt('foo', deprecated_opts=oldopts),
                               group='blaa')

        paths = self.create_tempfiles([('test',
                                        '[oldgroup2]\n'
                                        'oldfoo2 = bar\n')])

        self.conf(['--config-file', paths[0]])
        self.assertEqual(self.conf.blaa.foo, 'bar')


class MultipleDeprecatedCliOptionsTestCase(BaseTestCase):

    def test_conf_file_override_use_deprecated_name_and_group(self):
        self.conf.register_group(cfg.OptGroup('blaa'))
        self.conf.register_cli_opt(cfg.StrOpt('foo',
                                              deprecated_name='oldfoo',
                                              deprecated_group='oldgroup'),
                                   group='blaa')

        paths = self.create_tempfiles([('test',
                                        '[oldgroup]\n'
                                        'oldfoo = bar\n')])

        self.conf(['--config-file', paths[0]])
        self.assertEqual(self.conf.blaa.foo, 'bar')

    def test_conf_file_override_use_deprecated_opts(self):
        self.conf.register_group(cfg.OptGroup('blaa'))
        oldopts = [cfg.DeprecatedOpt('oldfoo', group='oldgroup')]
        self.conf.register_cli_opt(cfg.StrOpt('foo', deprecated_opts=oldopts),
                                   group='blaa')

        paths = self.create_tempfiles([('test',
                                        '[oldgroup]\n'
                                        'oldfoo = bar\n')])

        self.conf(['--config-file', paths[0]])
        self.assertEqual(self.conf.blaa.foo, 'bar')

    def test_conf_file_override_use_deprecated_multi_opts(self):
        self.conf.register_group(cfg.OptGroup('blaa'))
        oldopts = [cfg.DeprecatedOpt('oldfoo', group='oldgroup'),
                   cfg.DeprecatedOpt('oldfoo2', group='oldgroup2')]
        self.conf.register_cli_opt(cfg.StrOpt('foo', deprecated_opts=oldopts),
                                   group='blaa')

        paths = self.create_tempfiles([('test',
                                        '[oldgroup2]\n'
                                        'oldfoo2 = bar\n')])

        self.conf(['--config-file', paths[0]])
        self.assertEqual(self.conf.blaa.foo, 'bar')

    def test_conf_file_common_deprecated_group(self):
        self.conf.register_group(cfg.OptGroup('foo'))
        self.conf.register_group(cfg.OptGroup('bar'))
        oldopts = [cfg.DeprecatedOpt('foo', group='DEFAULT')]
        self.conf.register_opt(cfg.StrOpt('common_opt',
                                          deprecated_opts=oldopts),
                               group='bar')
        self.conf.register_opt(cfg.StrOpt('common_opt',
                                          deprecated_opts=oldopts),
                               group='foo')

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n'
                                        'foo = bla\n')])

        self.conf(['--config-file', paths[0]])
        self.assertEqual(self.conf.foo.common_opt, 'bla')
        self.assertEqual(self.conf.bar.common_opt, 'bla')

        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n'
                                        'foo = bla\n'
                                        '[bar]\n'
                                        'common_opt = blabla\n')])

        self.conf(['--config-file', paths[0]])
        self.assertEqual(self.conf.foo.common_opt, 'bla')
        self.assertEqual(self.conf.bar.common_opt, 'blabla')

        paths = self.create_tempfiles([('test',
                                        '[foo]\n'
                                        'common_opt = bla\n'
                                        '[bar]\n'
                                        'common_opt = blabla\n')])

        self.conf(['--config-file', paths[0]])
        self.assertEqual(self.conf.foo.common_opt, 'bla')
        self.assertEqual(self.conf.bar.common_opt, 'blabla')


class ChoicesTestCase(BaseTestCase):

    def test_choice_default(self):
        self.conf.register_cli_opt(cfg.StrOpt('protocol',
                                   default='http',
                                   choices=['http', 'https', 'ftp']))
        self.conf([])
        self.assertEqual(self.conf.protocol, 'http')

    def test_choice_good(self):
        self.conf.register_cli_opt(cfg.StrOpt('foo',
                                   choices=['bar1', 'bar2']))
        self.conf(['--foo', 'bar1'])
        self.assertEqual(self.conf.foo, 'bar1')

    def test_choice_bad(self):
        self.conf.register_cli_opt(cfg.StrOpt('foo',
                                   choices=['bar1', 'bar2']))
        self.assertRaises(SystemExit, self.conf, ['--foo', 'bar3'])

    def test_conf_file_choice_value(self):
        self.conf.register_opt(cfg.StrOpt('foo',
                               choices=['bar1', 'bar2']))

        paths = self.create_tempfiles([('test', '[DEFAULT]\n''foo = bar1\n')])

        self.conf(['--config-file', paths[0]])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, 'bar1')

    def test_conf_file_choice_empty_value(self):
        self.conf.register_opt(cfg.StrOpt('foo',
                               choices=['', 'bar1', 'bar2']))

        paths = self.create_tempfiles([('test', '[DEFAULT]\n''foo = \n')])

        self.conf(['--config-file', paths[0]])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, '')

    def test_conf_file_choice_none_value(self):
        self.conf.register_opt(cfg.StrOpt('foo',
                               default=None,
                               choices=[None, 'bar1', 'bar2']))

        paths = self.create_tempfiles([('test', '[DEFAULT]\n''\n')])

        self.conf(['--config-file', paths[0]])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, None)

    def test_conf_file_bad_choice_value(self):
        self.conf.register_opt(cfg.StrOpt('foo',
                               choices=['bar1', 'bar2']))

        paths = self.create_tempfiles([('test', '[DEFAULT]\n''foo = bar3\n')])

        self.conf(['--config-file', paths[0]])

        self.assertRaises(cfg.ConfigFileValueError, self.conf._get, 'foo')
        self.assertRaises(AttributeError, getattr, self.conf, 'foo')

    def test_conf_file_choice_value_override(self):
        self.conf.register_cli_opt(cfg.StrOpt('foo',
                                   choices=['baar', 'baaar']))

        paths = self.create_tempfiles([('1',
                                        '[DEFAULT]\n'
                                        'foo = baar\n'),
                                       ('2',
                                        '[DEFAULT]\n'
                                        'foo = baaar\n')])

        self.conf(['--foo', 'baar',
                   '--config-file', paths[0],
                   '--config-file', paths[1]])

        self.assertTrue(hasattr(self.conf, 'foo'))
        self.assertEqual(self.conf.foo, 'baaar')

    def test_conf_file_choice_bad_default(self):
        self.conf.register_cli_opt(cfg.StrOpt('foo',
                                              choices=['baar', 'baaar'],
                                              default='foobaz'))
        self.conf([])
        self.assertRaises(AttributeError,
                          getattr,
                          self.conf,
                          'foobaz')


class PrintHelpTestCase(base.BaseTestCase):

    def test_print_help_without_init(self):
        conf = cfg.ConfigOpts()
        conf.register_opts([])
        self.assertRaises(cfg.NotInitializedError,
                          conf.print_help)

    def test_print_help_with_clear(self):
        conf = cfg.ConfigOpts()
        conf.register_opts([])
        conf([])
        conf.clear()
        self.assertRaises(cfg.NotInitializedError,
                          conf.print_help)


class OptTestCase(base.BaseTestCase):

    def test_opt_eq(self):
        d1 = cfg.ListOpt('oldfoo')
        d2 = cfg.ListOpt('oldfoo')
        self.assertEqual(d1, d2)

    def test_opt_not_eq(self):
        d1 = cfg.ListOpt('oldfoo')
        d2 = cfg.ListOpt('oldbar')
        self.assertNotEqual(d1, d2)

    def test_illegal_name(self):
        self.assertRaises(ValueError, cfg.BoolOpt, '_foo')


class SectionsTestCase(base.BaseTestCase):
    def test_list_all_sections(self):
        paths = self.create_tempfiles([('test.ini',
                                        '[DEFAULT]\n'
                                        'foo = bar\n'
                                        '[BLAA]\n'
                                        'bar = foo\n')])
        config = cfg.ConfigOpts()
        config(args=[], default_config_files=[paths[0]])
        sections = set(config.list_all_sections())
        self.assertEqual(sections, set(['DEFAULT', 'BLAA']))


class DeprecationWarningTestBase(BaseTestCase):
    def setUp(self):
        super(DeprecationWarningTestBase, self).setUp()
        self.log_fixture = self.useFixture(fixtures.FakeLogger())
        self._parser_class = cfg.MultiConfigParser


class DeprecationWarningTestScenarios(DeprecationWarningTestBase):
    scenarios = [('default-deprecated', dict(deprecated=True,
                                             group='DEFAULT')),
                 ('default-not-deprecated', dict(deprecated=False,
                                                 group='DEFAULT')),
                 ('other-deprecated', dict(deprecated=True,
                                           group='other')),
                 ('other-not-deprecated', dict(deprecated=False,
                                               group='other')),
                 ]

    def test_deprecated_logging(self):
        self.conf.register_opt(cfg.StrOpt('foo', deprecated_name='bar'))
        self.conf.register_group(cfg.OptGroup('other'))
        self.conf.register_opt(cfg.StrOpt('foo', deprecated_name='bar'),
                               group='other')
        if self.deprecated:
            content = 'bar=baz'
        else:
            content = 'foo=baz'
        paths = self.create_tempfiles([('test',
                                        '[' + self.group + ']\n' +
                                        content + '\n')])

        self.conf(['--config-file', paths[0]])
        # Reference these twice to verify they only get logged once
        if self.group == 'DEFAULT':
            self.assertEqual('baz', self.conf.foo)
            self.assertEqual('baz', self.conf.foo)
        else:
            self.assertEqual('baz', self.conf.other.foo)
            self.assertEqual('baz', self.conf.other.foo)
        if self.deprecated:
            expected = (self._parser_class._deprecated_opt_message %
                        ('bar', self.group, 'foo', self.group) + '\n')
        else:
            expected = ''
        self.assertEqual(expected, self.log_fixture.output)


class DeprecationWarningTests(DeprecationWarningTestBase):
    def test_DeprecatedOpt(self):
        default_deprecated = [cfg.DeprecatedOpt('bar')]
        other_deprecated = [cfg.DeprecatedOpt('baz', group='other')]
        self.conf.register_group(cfg.OptGroup('other'))
        self.conf.register_opt(cfg.StrOpt('foo',
                                          deprecated_opts=default_deprecated))
        self.conf.register_opt(cfg.StrOpt('foo',
                                          deprecated_opts=other_deprecated),
                               group='other')
        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n' +
                                        'bar=baz\n' +
                                        '[other]\n' +
                                        'baz=baz\n')])
        self.conf(['--config-file', paths[0]])
        self.assertEqual('baz', self.conf.foo)
        self.assertEqual('baz', self.conf.other.foo)
        self.assertIn('Option "bar" from group "DEFAULT"',
                      self.log_fixture.output)
        self.assertIn('Option "baz" from group "other"',
                      self.log_fixture.output)

    def test_check_deprecated_default_none(self):
        parser = self._parser_class()
        deprecated_list = [(None, 'bar')]
        parser._check_deprecated(('DEFAULT', 'bar'), (None, 'foo'),
                                 deprecated_list)
        self.assert_message_logged('bar', 'DEFAULT', 'foo', 'DEFAULT')
        # Make sure check_deprecated didn't modify the list passed in
        self.assertEqual([(None, 'bar')], deprecated_list)

    def test_check_deprecated_none_default(self):
        parser = self._parser_class()
        deprecated_list = [('DEFAULT', 'bar')]
        parser._check_deprecated((None, 'bar'), ('DEFAULT', 'foo'),
                                 deprecated_list)
        self.assert_message_logged('bar', 'DEFAULT', 'foo', 'DEFAULT')
        # Make sure check_deprecated didn't modify the list passed in
        self.assertEqual([('DEFAULT', 'bar')], deprecated_list)

    def assert_message_logged(self, deprecated_name, deprecated_group,
                              current_name, current_group):
        expected = (self._parser_class._deprecated_opt_message %
                    (deprecated_name, deprecated_group,
                     current_name, current_group)
                    )
        self.assertEqual(expected + '\n', self.log_fixture.output)

    def test_deprecated_for_removal(self):
        self.conf.register_opt(cfg.StrOpt('foo',
                                          deprecated_for_removal=True))
        self.conf.register_opt(cfg.StrOpt('bar',
                                          deprecated_for_removal=True))
        paths = self.create_tempfiles([('test',
                                        '[DEFAULT]\n' +
                                        'foo=bar\n')])
        self.conf(['--config-file', paths[0]])
        # Multiple references should be logged only once.
        self.assertEqual('bar', self.conf.foo)
        self.assertEqual('bar', self.conf.foo)
        # Options not set in the config should not be logged.
        self.assertEqual(None, self.conf.bar)
        expected = ('Option "foo" from group "DEFAULT" is deprecated for '
                    'removal.  Its value may be silently ignored in the '
                    'future.\n')
        self.assertEqual(expected, self.log_fixture.output)

    def test_deprecated_for_removal_with_group(self):
        self.conf.register_group(cfg.OptGroup('other'))
        self.conf.register_opt(cfg.StrOpt('foo',
                                          deprecated_for_removal=True),
                               group='other')
        self.conf.register_opt(cfg.StrOpt('bar',
                                          deprecated_for_removal=True),
                               group='other')
        paths = self.create_tempfiles([('test',
                                        '[other]\n' +
                                        'foo=bar\n')])
        self.conf(['--config-file', paths[0]])
        # Multiple references should be logged only once.
        self.assertEqual('bar', self.conf.other.foo)
        self.assertEqual('bar', self.conf.other.foo)
        # Options not set in the config should not be logged.
        self.assertEqual(None, self.conf.other.bar)
        expected = ('Option "foo" from group "other" is deprecated for '
                    'removal.  Its value may be silently ignored in the '
                    'future.\n')
        self.assertEqual(expected, self.log_fixture.output)
