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

import argparse
import os

from keystoneclient.auth import base
from keystoneclient import utils


@utils.positional()
def register_argparse_arguments(parser, argv, default=None):
    """Register CLI options needed to create a plugin.

    The function inspects the provided arguments so that it can also register
    the options required for that specific plugin if available.

    :param argparse.ArgumentParser: the parser to attach argparse options to.
    :param list argv: the arguments provided to the appliation.
    :param str/class default: a default plugin name or a plugin object to use
                              if one isn't specified by the CLI. default: None.

    :returns: The plugin class that will be loaded or None if not provided.
    :rtype: :py:class:`keystoneclient.auth.BaseAuthPlugin`

    :raises keystoneclient.exceptions.NoMatchingPlugin: if a plugin cannot be
                                                        created.
    """
    in_parser = argparse.ArgumentParser(add_help=False)
    env_plugin = os.environ.get('OS_AUTH_PLUGIN', default)
    for p in (in_parser, parser):
        p.add_argument('--os-auth-plugin',
                       metavar='<name>',
                       default=env_plugin,
                       help='The auth plugin to load')

    options, _args = in_parser.parse_known_args(argv)

    if not options.os_auth_plugin:
        return None

    if isinstance(options.os_auth_plugin, type):
        msg = 'Default Authentication options'
        plugin = options.os_auth_plugin
    else:
        msg = 'Options specific to the %s plugin.' % options.os_auth_plugin
        plugin = base.get_plugin_class(options.os_auth_plugin)

    group = parser.add_argument_group('Authentication Options', msg)
    plugin.register_argparse_arguments(group)
    return plugin


def load_from_argparse_arguments(namespace, **kwargs):
    """Retrieve the created plugin from the completed argparse results.

    Loads and creates the auth plugin from the information parsed from the
    command line by argparse.

    :param Namespace namespace: The result from CLI parsing.

    :returns: An auth plugin, or None if a name is not provided.
    :rtype: :py:class:`keystoneclient.auth.BaseAuthPlugin`

    :raises keystoneclient.exceptions.NoMatchingPlugin: if a plugin cannot be
                                                        created.
    """
    if not namespace.os_auth_plugin:
        return None

    if isinstance(namespace.os_auth_plugin, type):
        plugin = namespace.os_auth_plugin
    else:
        plugin = base.get_plugin_class(namespace.os_auth_plugin)

    return plugin.load_from_argparse_arguments(namespace, **kwargs)
