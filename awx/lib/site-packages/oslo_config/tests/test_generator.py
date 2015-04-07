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

import sys

import fixtures
import mock
from oslotest import base
from six import moves
import testscenarios

from oslo_config import cfg
from oslo_config import fixture as config_fixture
from oslo_config import generator

load_tests = testscenarios.load_tests_apply_scenarios


class GeneratorTestCase(base.BaseTestCase):

    opts = {
        'foo': cfg.StrOpt('foo', help='foo option'),
        'bar': cfg.StrOpt('bar', help='bar option'),
        'foo-bar': cfg.StrOpt('foo-bar', help='foobar'),
        'no_help': cfg.StrOpt('no_help'),
        'long_help': cfg.StrOpt('long_help',
                                help='Lorem ipsum dolor sit amet, consectetur '
                                     'adipisicing elit, sed do eiusmod tempor '
                                     'incididunt ut labore et dolore magna '
                                     'aliqua. Ut enim ad minim veniam, quis '
                                     'nostrud exercitation ullamco laboris '
                                     'nisi ut aliquip ex ea commodo '
                                     'consequat. Duis aute irure dolor in '
                                     'reprehenderit in voluptate velit esse '
                                     'cillum dolore eu fugiat nulla '
                                     'pariatur. Excepteur sint occaecat '
                                     'cupidatat non proident, sunt in culpa '
                                     'qui officia deserunt mollit anim id est '
                                     'laborum.'),
        'choices_opt': cfg.StrOpt('choices_opt',
                                  default='a',
                                  choices=(None, '', 'a', 'b', 'c'),
                                  help='a string with choices'),
        'deprecated_opt': cfg.StrOpt('bar',
                                     deprecated_name='foobar',
                                     help='deprecated'),
        'deprecated_group': cfg.StrOpt('bar',
                                       deprecated_group='group1',
                                       deprecated_name='foobar',
                                       help='deprecated'),
        # Unknown Opt default must be a string
        'unknown_type': cfg.Opt('unknown_opt',
                                default='123',
                                help='unknown'),
        'str_opt': cfg.StrOpt('str_opt',
                              default='foo bar',
                              help='a string'),
        'str_opt_sample_default': cfg.StrOpt('str_opt',
                                             default='fooishbar',
                                             help='a string'),
        'str_opt_with_space': cfg.StrOpt('str_opt',
                                         default='  foo bar  ',
                                         help='a string with spaces'),
        'bool_opt': cfg.BoolOpt('bool_opt',
                                default=False,
                                help='a boolean'),
        'int_opt': cfg.IntOpt('int_opt',
                              default=10,
                              help='an integer'),
        'float_opt': cfg.FloatOpt('float_opt',
                                  default=0.1,
                                  help='a float'),
        'list_opt': cfg.ListOpt('list_opt',
                                default=['1', '2', '3'],
                                help='a list'),
        'dict_opt': cfg.DictOpt('dict_opt',
                                default={'1': 'yes', '2': 'no'},
                                help='a dict'),
        'multi_opt': cfg.MultiStrOpt('multi_opt',
                                     default=['1', '2', '3'],
                                     help='multiple strings'),
        'multi_opt_none': cfg.MultiStrOpt('multi_opt_none',
                                          help='multiple strings'),
        'multi_opt_empty': cfg.MultiStrOpt('multi_opt_empty',
                                           default=[],
                                           help='multiple strings'),
        'multi_opt_sample_default': cfg.MultiStrOpt('multi_opt',
                                                    default=['1', '2', '3'],
                                                    sample_default=['5', '6'],
                                                    help='multiple strings'),
    }

    content_scenarios = [
        ('empty',
         dict(opts=[], expected='''[DEFAULT]
''')),
        ('single_namespace',
         dict(opts=[('test', [(None, [opts['foo']])])],
              expected='''[DEFAULT]

#
# From test
#

# foo option (string value)
#foo = <None>
''')),
        ('multiple_namespaces',
         dict(opts=[('test', [(None, [opts['foo']])]),
                    ('other', [(None, [opts['bar']])])],
              expected='''[DEFAULT]

#
# From other
#

# bar option (string value)
#bar = <None>

#
# From test
#

# foo option (string value)
#foo = <None>
''')),
        ('group',
         dict(opts=[('test', [('group1', [opts['foo']])])],
              expected='''[DEFAULT]


[group1]

#
# From test
#

# foo option (string value)
#foo = <None>
''')),
        ('empty_group',
         dict(opts=[('test', [('group1', [])])],
              expected='''[DEFAULT]
''')),
        ('multiple_groups',
         dict(opts=[('test', [('group1', [opts['foo']]),
                              ('group2', [opts['bar']])])],
              expected='''[DEFAULT]


[group1]

#
# From test
#

# foo option (string value)
#foo = <None>


[group2]

#
# From test
#

# bar option (string value)
#bar = <None>
''')),
        ('group_in_multiple_namespaces',
         dict(opts=[('test', [('group1', [opts['foo']])]),
                    ('other', [('group1', [opts['bar']])])],
              expected='''[DEFAULT]


[group1]

#
# From other
#

# bar option (string value)
#bar = <None>

#
# From test
#

# foo option (string value)
#foo = <None>
''')),
        ('hyphenated_name',
         dict(opts=[('test', [(None, [opts['foo-bar']])])],
              expected='''[DEFAULT]

#
# From test
#

# foobar (string value)
#foo_bar = <None>
''')),
        ('no_help',
         dict(opts=[('test', [(None, [opts['no_help']])])],
              log_warning=('"%s" is missing a help string', 'no_help'),
              expected='''[DEFAULT]

#
# From test
#

# (string value)
#no_help = <None>
''')),
        ('long_help',
         dict(opts=[('test', [(None, [opts['long_help']])])],
              expected='''[DEFAULT]

#
# From test
#

# Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do
# eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim
# ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut
# aliquip ex ea commodo consequat. Duis aute irure dolor in
# reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla
# pariatur. Excepteur sint occaecat cupidatat non proident, sunt in
# culpa qui officia deserunt mollit anim id est laborum. (string
# value)
#long_help = <None>
''')),
        ('long_help_wrap_at_40',
         dict(opts=[('test', [(None, [opts['long_help']])])],
              wrap_width=40,
              expected='''[DEFAULT]

#
# From test
#

# Lorem ipsum dolor sit amet,
# consectetur adipisicing elit, sed do
# eiusmod tempor incididunt ut labore et
# dolore magna aliqua. Ut enim ad minim
# veniam, quis nostrud exercitation
# ullamco laboris nisi ut aliquip ex ea
# commodo consequat. Duis aute irure
# dolor in reprehenderit in voluptate
# velit esse cillum dolore eu fugiat
# nulla pariatur. Excepteur sint
# occaecat cupidatat non proident, sunt
# in culpa qui officia deserunt mollit
# anim id est laborum. (string value)
#long_help = <None>
''')),
        ('long_help_no_wrapping',
         dict(opts=[('test', [(None, [opts['long_help']])])],
              wrap_width=0,
              expected='''[DEFAULT]

#
# From test
#

'''   # noqa
'# Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod '
'tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, '
'quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo '
'consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse '
'cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat '
'non proident, sunt in culpa qui officia deserunt mollit anim id est laborum. '
'(string value)'
'''
#long_help = <None>
''')),
        ('choices_opt',
         dict(opts=[('test', [(None, [opts['choices_opt']])])],
              expected='''[DEFAULT]

#
# From test
#

# a string with choices (string value)
# Allowed values: <None>, '', a, b, c
#choices_opt = a
''')),
        ('deprecated',
         dict(opts=[('test', [('foo', [opts['deprecated_opt']])])],
              expected='''[DEFAULT]


[foo]

#
# From test
#

# deprecated (string value)
# Deprecated group/name - [DEFAULT]/foobar
#bar = <None>
''')),
        ('deprecated_group',
         dict(opts=[('test', [('foo', [opts['deprecated_group']])])],
              expected='''[DEFAULT]


[foo]

#
# From test
#

# deprecated (string value)
# Deprecated group/name - [group1]/foobar
#bar = <None>
''')),
        ('unknown_type',
         dict(opts=[('test', [(None, [opts['unknown_type']])])],
              log_warning=('Unknown option type: %s',
                           repr(opts['unknown_type'])),
              expected='''[DEFAULT]

#
# From test
#

# unknown (unknown type)
#unknown_opt = 123
''')),
        ('str_opt',
         dict(opts=[('test', [(None, [opts['str_opt']])])],
              expected='''[DEFAULT]

#
# From test
#

# a string (string value)
#str_opt = foo bar
''')),
        ('str_opt_with_space',
         dict(opts=[('test', [(None, [opts['str_opt_with_space']])])],
              expected='''[DEFAULT]

#
# From test
#

# a string with spaces (string value)
#str_opt = "  foo bar  "
''')),
        ('bool_opt',
         dict(opts=[('test', [(None, [opts['bool_opt']])])],
              expected='''[DEFAULT]

#
# From test
#

# a boolean (boolean value)
#bool_opt = false
''')),
        ('int_opt',
         dict(opts=[('test', [(None, [opts['int_opt']])])],
              expected='''[DEFAULT]

#
# From test
#

# an integer (integer value)
#int_opt = 10
''')),
        ('float_opt',
         dict(opts=[('test', [(None, [opts['float_opt']])])],
              expected='''[DEFAULT]

#
# From test
#

# a float (floating point value)
#float_opt = 0.1
''')),
        ('list_opt',
         dict(opts=[('test', [(None, [opts['list_opt']])])],
              expected='''[DEFAULT]

#
# From test
#

# a list (list value)
#list_opt = 1,2,3
''')),
        ('dict_opt',
         dict(opts=[('test', [(None, [opts['dict_opt']])])],
              expected='''[DEFAULT]

#
# From test
#

# a dict (dict value)
#dict_opt = 1:yes,2:no
''')),
        ('multi_opt',
         dict(opts=[('test', [(None, [opts['multi_opt']])])],
              expected='''[DEFAULT]

#
# From test
#

# multiple strings (multi valued)
#multi_opt = 1
#multi_opt = 2
#multi_opt = 3
''')),
        ('multi_opt_none',
         dict(opts=[('test', [(None, [opts['multi_opt_none']])])],
              expected='''[DEFAULT]

#
# From test
#

# multiple strings (multi valued)
#multi_opt_none =
''')),
        ('multi_opt_empty',
         dict(opts=[('test', [(None, [opts['multi_opt_empty']])])],
              expected='''[DEFAULT]

#
# From test
#

# multiple strings (multi valued)
#multi_opt_empty =
''')),
        ('str_opt_sample_default',
         dict(opts=[('test', [(None, [opts['str_opt_sample_default']])])],
              expected='''[DEFAULT]

#
# From test
#

# a string (string value)
#str_opt = fooishbar
''')),
        ('multi_opt_sample_default',
         dict(opts=[('test', [(None, [opts['multi_opt_sample_default']])])],
              expected='''[DEFAULT]

#
# From test
#

# multiple strings (multi valued)
#multi_opt = 5
#multi_opt = 6
''')),
    ]

    output_file_scenarios = [
        ('stdout',
         dict(stdout=True, output_file=None)),
        ('output_file',
         dict(output_file='sample.conf', stdout=False)),
    ]

    @classmethod
    def generate_scenarios(cls):
        cls.scenarios = testscenarios.multiply_scenarios(
            cls.content_scenarios,
            cls.output_file_scenarios)

    def setUp(self):
        super(GeneratorTestCase, self).setUp()

        self.conf = cfg.ConfigOpts()
        self.config_fixture = config_fixture.Config(self.conf)
        self.config = self.config_fixture.config
        self.useFixture(self.config_fixture)

        self.tempdir = self.useFixture(fixtures.TempDir())

    def _capture_stream(self, stream_name):
        self.useFixture(fixtures.MonkeyPatch("sys.%s" % stream_name,
                                             moves.StringIO()))
        return getattr(sys, stream_name)

    def _capture_stdout(self):
        return self._capture_stream('stdout')

    @mock.patch('stevedore.named.NamedExtensionManager')
    @mock.patch.object(generator, 'LOG')
    def test_generate(self, mock_log, named_mgr):
        generator.register_cli_opts(self.conf)

        namespaces = [i[0] for i in self.opts]
        self.config(namespace=namespaces)

        wrap_width = getattr(self, 'wrap_width', None)
        if wrap_width is not None:
            self.config(wrap_width=wrap_width)

        if self.stdout:
            stdout = self._capture_stdout()
        else:
            output_file = self.tempdir.join(self.output_file)
            self.config(output_file=output_file)

        mock_eps = []
        for name, opts in self.opts:
            mock_ep = mock.Mock()
            mock_ep.configure_mock(name=name, obj=opts)
            mock_eps.append(mock_ep)
        named_mgr.return_value = mock_eps

        generator.generate(self.conf)

        if self.stdout:
            self.assertEqual(self.expected, stdout.getvalue())
        else:
            content = open(output_file).read()
            self.assertEqual(self.expected, content)

        named_mgr.assert_called_once_with(
            'oslo.config.opts',
            names=namespaces,
            on_load_failure_callback=generator.on_load_failure_callback,
            invoke_on_load=True)

        log_warning = getattr(self, 'log_warning', None)
        if log_warning is not None:
            mock_log.warning.assert_called_once_with(*log_warning)
        else:
            self.assertFalse(mock_log.warning.called)


class GeneratorRaiseErrorTestCase(base.BaseTestCase):

    def test_generator_raises_error(self):
        """Verifies that errors from extension manager are not suppressed."""
        class FakeException(Exception):
            pass

        class FakeEP(object):

            def __init__(self):
                self.name = 'callback_is_expected'
                self.require = self.resolve
                self.load = self.resolve

            def resolve(self, *args, **kwargs):
                raise FakeException()

        fake_ep = FakeEP()
        self.conf = cfg.ConfigOpts()
        self.conf.register_opts(generator._generator_opts)
        self.conf.set_default('namespace', fake_ep.name)
        fake_eps = mock.Mock(return_value=[fake_ep])
        with mock.patch('pkg_resources.iter_entry_points', fake_eps):
            self.assertRaises(FakeException, generator.generate, self.conf)


GeneratorTestCase.generate_scenarios()
