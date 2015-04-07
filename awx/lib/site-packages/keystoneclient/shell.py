# Copyright 2010 Jacob Kaplan-Moss
# Copyright 2011 OpenStack Foundation
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

"""Command-line interface to the OpenStack Identity API."""

from __future__ import print_function

import argparse
import getpass
import logging
import os
import sys
import warnings

from oslo_utils import encodeutils
import six

import keystoneclient
from keystoneclient import access
from keystoneclient.contrib.bootstrap import shell as shell_bootstrap
from keystoneclient import exceptions as exc
from keystoneclient.generic import shell as shell_generic
from keystoneclient import session
from keystoneclient import utils
from keystoneclient.v2_0 import shell as shell_v2_0


def env(*vars, **kwargs):
    """Search for the first defined of possibly many env vars

    Returns the first environment variable defined in vars, or
    returns the default defined in kwargs.

    """
    for v in vars:
        value = os.environ.get(v)
        if value:
            return value
    return kwargs.get('default', '')


class OpenStackIdentityShell(object):

    def __init__(self, parser_class=argparse.ArgumentParser):

        # Since Python 2.7, DeprecationWarning is ignored by default, enable
        # it so that the deprecation message is displayed.
        warnings.simplefilter('once', category=DeprecationWarning)
        warnings.warn(
            'The keystone CLI is deprecated in favor of '
            'python-openstackclient. For a Python library, continue using '
            'python-keystoneclient.', DeprecationWarning)
        # And back to normal!
        warnings.resetwarnings()
        self.parser_class = parser_class

    def get_base_parser(self):
        parser = self.parser_class(
            prog='keystone',
            description=__doc__.strip(),
            epilog='See "keystone help COMMAND" '
                   'for help on a specific command.',
            add_help=False,
            formatter_class=OpenStackHelpFormatter,
        )

        # Global arguments
        parser.add_argument('-h',
                            '--help',
                            action='store_true',
                            help=argparse.SUPPRESS)

        parser.add_argument('--version',
                            action='version',
                            version=keystoneclient.__version__,
                            help="Shows the client version and exits.")

        parser.add_argument('--debug',
                            default=False,
                            action='store_true',
                            help="Prints debugging output onto the console, "
                                 "this includes the curl request and response "
                                 "calls. Helpful for debugging and "
                                 "understanding the API calls.")

        parser.add_argument('--os-username',
                            metavar='<auth-user-name>',
                            default=env('OS_USERNAME'),
                            help='Name used for authentication with the '
                                 'OpenStack Identity service. '
                                 'Defaults to env[OS_USERNAME].')
        parser.add_argument('--os_username',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-password',
                            metavar='<auth-password>',
                            default=env('OS_PASSWORD'),
                            help='Password used for authentication with the '
                                 'OpenStack Identity service. '
                                 'Defaults to env[OS_PASSWORD].')
        parser.add_argument('--os_password',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-tenant-name',
                            metavar='<auth-tenant-name>',
                            default=env('OS_TENANT_NAME'),
                            help='Tenant to request authorization on. '
                                 'Defaults to env[OS_TENANT_NAME].')
        parser.add_argument('--os_tenant_name',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-tenant-id',
                            metavar='<tenant-id>',
                            default=env('OS_TENANT_ID'),
                            help='Tenant to request authorization on. '
                                 'Defaults to env[OS_TENANT_ID].')
        parser.add_argument('--os_tenant_id',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-auth-url',
                            metavar='<auth-url>',
                            default=env('OS_AUTH_URL'),
                            help='Specify the Identity endpoint to use for '
                                 'authentication. '
                                 'Defaults to env[OS_AUTH_URL].')
        parser.add_argument('--os_auth_url',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-region-name',
                            metavar='<region-name>',
                            default=env('OS_REGION_NAME'),
                            help='Specify the region to use. '
                                 'Defaults to env[OS_REGION_NAME].')
        parser.add_argument('--os_region_name',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-identity-api-version',
                            metavar='<identity-api-version>',
                            default=env('OS_IDENTITY_API_VERSION',
                                        'KEYSTONE_VERSION'),
                            help='Specify Identity API version to use. '
                                 'Defaults to env[OS_IDENTITY_API_VERSION]'
                                 ' or 2.0.')
        parser.add_argument('--os_identity_api_version',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-token',
                            metavar='<service-token>',
                            default=env('OS_SERVICE_TOKEN'),
                            help='Specify an existing token to use instead of '
                                 'retrieving one via authentication (e.g. '
                                 'with username & password). '
                                 'Defaults to env[OS_SERVICE_TOKEN].')

        parser.add_argument('--os-endpoint',
                            metavar='<service-endpoint>',
                            default=env('OS_SERVICE_ENDPOINT'),
                            help='Specify an endpoint to use instead of '
                                 'retrieving one from the service catalog '
                                 '(via authentication). '
                                 'Defaults to env[OS_SERVICE_ENDPOINT].')

        parser.add_argument('--os-cache',
                            default=env('OS_CACHE', default=False),
                            action='store_true',
                            help='Use the auth token cache. '
                                 'Defaults to env[OS_CACHE].')
        parser.add_argument('--os_cache',
                            help=argparse.SUPPRESS)

        parser.add_argument('--force-new-token',
                            default=False,
                            action="store_true",
                            dest='force_new_token',
                            help="If the keyring is available and in use, "
                                 "token will always be stored and fetched "
                                 "from the keyring until the token has "
                                 "expired. Use this option to request a "
                                 "new token and replace the existing one "
                                 "in the keyring.")

        parser.add_argument('--stale-duration',
                            metavar='<seconds>',
                            default=access.STALE_TOKEN_DURATION,
                            dest='stale_duration',
                            help="Stale duration (in seconds) used to "
                                 "determine whether a token has expired "
                                 "when retrieving it from keyring. This "
                                 "is useful in mitigating process or "
                                 "network delays. Default is %s seconds." %
                                 access.STALE_TOKEN_DURATION)

        session.Session.register_cli_options(parser)

        parser.add_argument('--os_cacert', help=argparse.SUPPRESS)
        parser.add_argument('--os_key', help=argparse.SUPPRESS)
        parser.add_argument('--os_cert', help=argparse.SUPPRESS)

        return parser

    def get_subcommand_parser(self, version):
        parser = self.get_base_parser()

        self.subcommands = {}
        subparsers = parser.add_subparsers(metavar='<subcommand>')

        try:
            actions_module = {
                '2.0': shell_v2_0,
            }[version]
        except KeyError:
            actions_module = shell_v2_0

        self._find_actions(subparsers, actions_module)
        self._find_actions(subparsers, shell_generic)
        self._find_actions(subparsers, shell_bootstrap)
        self._find_actions(subparsers, self)
        self._add_bash_completion_subparser(subparsers)

        return parser

    def _add_bash_completion_subparser(self, subparsers):
        subparser = subparsers.add_parser(
            'bash_completion',
            add_help=False,
            formatter_class=OpenStackHelpFormatter
        )
        self.subcommands['bash_completion'] = subparser
        subparser.set_defaults(func=self.do_bash_completion)

    def _find_actions(self, subparsers, actions_module):
        for attr in (a for a in dir(actions_module) if a.startswith('do_')):
            # I prefer to be hyphen-separated instead of underscores.
            command = attr[3:].replace('_', '-')
            callback = getattr(actions_module, attr)
            desc = callback.__doc__ or ''
            help = desc.strip().split('\n')[0]
            arguments = getattr(callback, 'arguments', [])

            subparser = subparsers.add_parser(
                command,
                help=help,
                description=desc,
                add_help=False,
                formatter_class=OpenStackHelpFormatter)
            subparser.add_argument('-h', '--help', action='help',
                                   help=argparse.SUPPRESS)
            self.subcommands[command] = subparser
            group = subparser.add_argument_group(title='Arguments')
            for (args, kwargs) in arguments:
                group.add_argument(*args, **kwargs)
            subparser.set_defaults(func=callback)

    def auth_check(self, args):
        if args.os_token or args.os_endpoint:
            if not args.os_token:
                raise exc.CommandError(
                    'Expecting a token provided via either --os-token or '
                    'env[OS_SERVICE_TOKEN]')

            if not args.os_endpoint:
                raise exc.CommandError(
                    'Expecting an endpoint provided via either '
                    '--os-endpoint or env[OS_SERVICE_ENDPOINT]')

            # user supplied a token and endpoint and at least one other cred
            if args.os_username or args.os_password or args.os_auth_url:
                msg = ('WARNING: Bypassing authentication using a token & '
                       'endpoint (authentication credentials are being '
                       'ignored).')
                print(msg)

        else:
            if not args.os_auth_url:
                raise exc.CommandError(
                    'Expecting an auth URL via either --os-auth-url or '
                    'env[OS_AUTH_URL]')

            if args.os_username or args.os_password:
                if not args.os_username:
                    raise exc.CommandError(
                        'Expecting a username provided via either '
                        '--os-username or env[OS_USERNAME]')

                if not args.os_password:
                    # No password, If we've got a tty, try prompting for it
                    if hasattr(sys.stdin, 'isatty') and sys.stdin.isatty():
                        # Check for Ctl-D
                        try:
                            args.os_password = getpass.getpass('OS Password: ')
                        except EOFError:
                            pass
                    # No password because we didn't have a tty or the
                    # user Ctl-D when prompted?
                    if not args.os_password:
                        raise exc.CommandError(
                            'Expecting a password provided via either '
                            '--os-password, env[OS_PASSWORD], or '
                            'prompted response')

            else:
                raise exc.CommandError('Expecting authentication method via'
                                       '\n  either a service token, '
                                       '--os-token or env[OS_SERVICE_TOKEN], '
                                       '\n  credentials, '
                                       '--os-username or env[OS_USERNAME]')

    def main(self, argv):
        # Parse args once to find version
        parser = self.get_base_parser()
        (options, args) = parser.parse_known_args(argv)

        # build available subcommands based on version
        api_version = options.os_identity_api_version
        subcommand_parser = self.get_subcommand_parser(api_version)
        self.parser = subcommand_parser

        # Handle top-level --help/-h before attempting to parse
        # a command off the command line
        if not argv or options.help:
            self.do_help(options)
            return 0

        # Parse args again and call whatever callback was selected
        args = subcommand_parser.parse_args(argv)

        # Short-circuit and deal with help command right away.
        if args.func == self.do_help:
            self.do_help(args)
            return 0
        elif args.func == self.do_bash_completion:
            self.do_bash_completion(args)
            return 0

        if args.debug:
            logging_level = logging.DEBUG
            iso_logger = logging.getLogger('iso8601')
            iso_logger.setLevel('WARN')
        else:
            logging_level = logging.WARNING

        logging.basicConfig(level=logging_level)

        # TODO(heckj): supporting backwards compatibility with environment
        # variables. To be removed after DEVSTACK is updated, ideally in
        # the Grizzly release cycle.
        args.os_token = args.os_token or env('SERVICE_TOKEN')
        args.os_endpoint = args.os_endpoint or env('SERVICE_ENDPOINT')

        if utils.isunauthenticated(args.func):
            self.cs = shell_generic.CLIENT_CLASS(endpoint=args.os_auth_url,
                                                 cacert=args.os_cacert,
                                                 key=args.os_key,
                                                 cert=args.os_cert,
                                                 insecure=args.insecure,
                                                 timeout=args.timeout)
        else:
            self.auth_check(args)
            token = None
            if args.os_token and args.os_endpoint:
                token = args.os_token
            api_version = options.os_identity_api_version
            self.cs = self.get_api_class(api_version)(
                username=args.os_username,
                tenant_name=args.os_tenant_name,
                tenant_id=args.os_tenant_id,
                token=token,
                endpoint=args.os_endpoint,
                password=args.os_password,
                auth_url=args.os_auth_url,
                region_name=args.os_region_name,
                cacert=args.os_cacert,
                key=args.os_key,
                cert=args.os_cert,
                insecure=args.insecure,
                debug=args.debug,
                use_keyring=args.os_cache,
                force_new_token=args.force_new_token,
                stale_duration=args.stale_duration,
                timeout=args.timeout)

        try:
            args.func(self.cs, args)
        except exc.Unauthorized:
            raise exc.CommandError("Invalid OpenStack Identity credentials.")
        except exc.AuthorizationFailure:
            raise exc.CommandError("Unable to authorize user")

    def get_api_class(self, version):
        try:
            return {
                "2.0": shell_v2_0.CLIENT_CLASS,
            }[version]
        except KeyError:
            if version:
                msg = ('WARNING: unsupported identity-api-version %s, '
                       'falling back to 2.0' % version)
                print(msg)
            return shell_v2_0.CLIENT_CLASS

    def do_bash_completion(self, args):
        """Prints all of the commands and options to stdout.

        The keystone.bash_completion script doesn't have to hard code them.
        """
        commands = set()
        options = set()
        for sc_str, sc in self.subcommands.items():
            commands.add(sc_str)
            for option in list(sc._optionals._option_string_actions):
                options.add(option)

        commands.remove('bash-completion')
        commands.remove('bash_completion')
        print(' '.join(commands | options))

    @utils.arg('command', metavar='<subcommand>', nargs='?',
               help='Display help for <subcommand>.')
    def do_help(self, args):
        """Display help about this program or one of its subcommands."""
        if getattr(args, 'command', None):
            if args.command in self.subcommands:
                self.subcommands[args.command].print_help()
            else:
                raise exc.CommandError("'%s' is not a valid subcommand" %
                                       args.command)
        else:
            self.parser.print_help()


# I'm picky about my shell help.
class OpenStackHelpFormatter(argparse.HelpFormatter):
    INDENT_BEFORE_ARGUMENTS = 6
    MAX_WIDTH_ARGUMENTS = 32

    def add_arguments(self, actions):
        for action in filter(lambda x: not x.option_strings, actions):
            if not action.choices:
                continue
            for choice in action.choices:
                length = len(choice) + self.INDENT_BEFORE_ARGUMENTS
                if(length > self._max_help_position and
                   length <= self.MAX_WIDTH_ARGUMENTS):
                    self._max_help_position = length
        super(OpenStackHelpFormatter, self).add_arguments(actions)

    def start_section(self, heading):
        # Title-case the headings
        heading = '%s%s' % (heading[0].upper(), heading[1:])
        super(OpenStackHelpFormatter, self).start_section(heading)


def main():
    try:
        OpenStackIdentityShell().main(sys.argv[1:])
    except KeyboardInterrupt:
        print("... terminating keystone client", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(encodeutils.safe_encode(six.text_type(e)), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
