# Copyright 2012 SINA Corporation
# Copyright 2014 Cisco Systems, Inc.
# All Rights Reserved.
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

r"""
A sample configuration file generator.

oslo-config-generator is a utility for generating sample config files. For
example, to generate a sample config file for oslo.messaging you would run::

  $> oslo-config-generator --namespace oslo.messaging > oslo.messaging.conf

This generated sample lists all of the available options, along with their help
string, type, deprecated aliases and defaults.

The --namespace option specifies an entry point name registered under the
'oslo.config.opts' entry point namespace. For example, in oslo.messaging's
setup.cfg we have::

  [entry_points]
  oslo.config.opts =
      oslo.messaging = oslo.messaging.opts:list_opts

The callable referenced by the entry point should take no arguments and return
a list of (group_name, [opt_1, opt_2]) tuples. For example::

  opts = [
      cfg.StrOpt('foo'),
      cfg.StrOpt('bar'),
  ]

  cfg.CONF.register_opts(opts, group='blaa')

  def list_opts():
      return [('blaa', opts)]

You might choose to return a copy of the options so that the return value can't
be modified for nefarious purposes::

  def list_opts():
      return [('blaa', copy.deepcopy(opts))]

A single codebase might have multiple programs, each of which use a subset of
the total set of options registered by the codebase. In that case, you can
register multiple entry points::

  [entry_points]
  oslo.config.opts =
      nova.common = nova.config:list_common_opts
      nova.api = nova.config:list_api_opts
      nova.compute = nova.config:list_compute_opts

and generate a config file specific to each program::

  $> oslo-config-generator --namespace oslo.messaging \
                           --namespace nova.common \
                           --namespace nova.api > nova-api.conf
  $> oslo-config-generator --namespace oslo.messaging \
                           --namespace nova.common \
                           --namespace nova.compute > nova-compute.conf

To make this more convenient, you can use config files to describe your config
files::

  $> cat > config-generator/api.conf <<EOF
  [DEFAULT]
  output_file = etc/nova/nova-api.conf
  namespace = oslo.messaging
  namespace = nova.common
  namespace = nova.api
  EOF
  $> cat > config-generator/compute.conf <<EOF
  [DEFAULT]
  output_file = etc/nova/nova-compute.conf
  namespace = oslo.messaging
  namespace = nova.common
  namespace = nova.compute
  EOF
  $> oslo-config-generator --config-file config-generator/api.conf
  $> oslo-config-generator --config-file config-generator/compute.conf

The default runtime values of configuration options are not always the most
suitable values to include in sample config files - for example, rather than
including the IP address or hostname of the machine where the config file
was generated, you might want to include something like '10.0.0.1'. To
facilitate this, options can be supplied with a 'sample_default' attribute::

  cfg.StrOpt('base_dir'
             default=os.getcwd(),
             sample_default='/usr/lib/myapp')
"""

import logging
import operator
import sys
import textwrap

import pkg_resources
import six

from oslo_config import cfg
import stevedore.named  # noqa

LOG = logging.getLogger(__name__)

_generator_opts = [
    cfg.StrOpt('output-file',
               help='Path of the file to write to. Defaults to stdout.'),
    cfg.IntOpt('wrap-width',
               default=70,
               help='The maximum length of help lines.'),
    cfg.MultiStrOpt('namespace',
                    help='Option namespace under "oslo.config.opts" in which '
                         'to query for options.'),
]


def register_cli_opts(conf):
    """Register the formatter's CLI options with a ConfigOpts instance.

    Note, this must be done before the ConfigOpts instance is called to parse
    the configuration.

    :param conf: a ConfigOpts instance
    :raises: DuplicateOptError, ArgsAlreadyParsedError
    """
    conf.register_cli_opts(_generator_opts)


class _OptFormatter(object):

    """Format configuration option descriptions to a file."""

    _TYPE_DESCRIPTIONS = {
        cfg.StrOpt: 'string value',
        cfg.BoolOpt: 'boolean value',
        cfg.IntOpt: 'integer value',
        cfg.FloatOpt: 'floating point value',
        cfg.ListOpt: 'list value',
        cfg.DictOpt: 'dict value',
        cfg.MultiStrOpt: 'multi valued',
    }

    def __init__(self, output_file=None, wrap_width=70):
        """Construct an OptFormatter object.

        :param output_file: a writeable file object
        :param wrap_width: The maximum length of help lines, 0 to not wrap
        """
        self.output_file = output_file or sys.stdout
        self.wrap_width = wrap_width

    def _format_help(self, help_text):
        """Format the help for a group or option to the output file.

        :param help_text: The text of the help string
        """
        if self.wrap_width is not None and self.wrap_width > 0:
            lines = [textwrap.fill(help_text,
                                   self.wrap_width,
                                   initial_indent='# ',
                                   subsequent_indent='# ') + '\n']
        else:
            lines = ['# ' + help_text + '\n']
        return lines

    def _get_choice_text(self, choice):
        if choice is None:
            return '<None>'
        elif choice == '':
            return "''"
        return six.text_type(choice)

    def format(self, opt):
        """Format a description of an option to the output file.

        :param opt: a cfg.Opt instance
        """
        if not opt.help:
            LOG.warning('"%s" is missing a help string', opt.dest)

        opt_type = self._TYPE_DESCRIPTIONS.get(type(opt), 'unknown type')

        if opt.help:
            help_text = u'%s (%s)' % (opt.help,
                                      opt_type)
        else:
            help_text = u'(%s)' % opt_type
        lines = self._format_help(help_text)

        if getattr(opt.type, 'choices', None):
            choices_text = ', '.join([self._get_choice_text(choice)
                                      for choice in opt.type.choices])
            lines.append('# Allowed values: %s\n' % choices_text)

        for d in opt.deprecated_opts:
            lines.append('# Deprecated group/name - [%s]/%s\n' %
                         (d.group or 'DEFAULT', d.name or opt.dest))

        if isinstance(opt, cfg.MultiStrOpt):
            if opt.sample_default is not None:
                defaults = opt.sample_default
            elif not opt.default:
                defaults = ['']
            else:
                defaults = opt.default
        else:
            if opt.sample_default is not None:
                default_str = str(opt.sample_default)
            elif opt.default is None:
                default_str = '<None>'
            elif isinstance(opt, cfg.StrOpt):
                default_str = opt.default
            elif isinstance(opt, cfg.BoolOpt):
                default_str = str(opt.default).lower()
            elif (isinstance(opt, cfg.IntOpt) or
                  isinstance(opt, cfg.FloatOpt)):
                default_str = str(opt.default)
            elif isinstance(opt, cfg.ListOpt):
                default_str = ','.join(opt.default)
            elif isinstance(opt, cfg.DictOpt):
                sorted_items = sorted(opt.default.items(),
                                      key=operator.itemgetter(0))
                default_str = ','.join(['%s:%s' % i for i in sorted_items])
            else:
                LOG.warning('Unknown option type: %s', repr(opt))
                default_str = str(opt.default)
            defaults = [default_str]

        for default_str in defaults:
            if default_str.strip() != default_str:
                default_str = '"%s"' % default_str
            if default_str:
                default_str = ' ' + default_str
            lines.append('#%s =%s\n' % (opt.dest, default_str))

        self.writelines(lines)

    def write(self, s):
        """Write an arbitrary string to the output file.

        :param s: an arbitrary string
        """
        self.output_file.write(s)

    def writelines(self, l):
        """Write an arbitrary sequence of strings to the output file.

        :param l: a list of arbitrary strings
        """
        self.output_file.writelines(l)


def _list_opts(namespaces):
    """List the options available via the given namespaces.

    :param namespaces: a list of namespaces registered under 'oslo.config.opts'
    :returns: a list of (namespace, [(group, [opt_1, opt_2])]) tuples
    """
    mgr = stevedore.named.NamedExtensionManager(
        'oslo.config.opts',
        names=namespaces,
        on_load_failure_callback=on_load_failure_callback,
        invoke_on_load=True)
    return [(ep.name, ep.obj) for ep in mgr]


def on_load_failure_callback(*args, **kwargs):
    raise


def generate(conf):
    """Generate a sample config file.

    List all of the options available via the namespaces specified in the given
    configuration and write a description of them to the specified output file.

    :param conf: a ConfigOpts instance containing the generator's configuration
    """
    conf.register_opts(_generator_opts)

    output_file = (open(conf.output_file, 'w')
                   if conf.output_file else sys.stdout)

    formatter = _OptFormatter(output_file=output_file,
                              wrap_width=conf.wrap_width)

    groups = {'DEFAULT': []}
    for namespace, listing in _list_opts(conf.namespace):
        for group, opts in listing:
            if not opts:
                continue
            namespaces = groups.setdefault(group or 'DEFAULT', [])
            namespaces.append((namespace, opts))

    def _output_opts(f, group, namespaces):
        f.write('[%s]\n' % group)
        for (namespace, opts) in sorted(namespaces,
                                        key=operator.itemgetter(0)):
            f.write('\n#\n# From %s\n#\n' % namespace)
            for opt in opts:
                f.write('\n')
                f.format(opt)

    _output_opts(formatter, 'DEFAULT', groups.pop('DEFAULT'))
    for group, namespaces in sorted(groups.items(),
                                    key=operator.itemgetter(0)):
        formatter.write('\n\n')
        _output_opts(formatter, group, namespaces)


def main(args=None):
    """The main function of oslo-config-generator."""
    version = pkg_resources.get_distribution('oslo.config').version
    logging.basicConfig(level=logging.WARN)
    conf = cfg.ConfigOpts()
    register_cli_opts(conf)
    conf(args, version=version)
    generate(conf)


if __name__ == '__main__':
    main()
