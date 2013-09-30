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

"""
Command-line interface to the OpenStack Nova API.
"""

from __future__ import print_function
import argparse
import getpass
import glob
import imp
import itertools
import logging
import os
import pkgutil
import sys

import pkg_resources
import six

HAS_KEYRING = False
all_errors = ValueError
try:
    import keyring
    HAS_KEYRING = True
    try:
        if isinstance(keyring.get_keyring(), keyring.backend.GnomeKeyring):
            import gnomekeyring
            all_errors = (ValueError,
                          gnomekeyring.IOError,
                          gnomekeyring.NoKeyringDaemonError)
    except Exception:
        pass
except ImportError:
    pass

import novaclient
import novaclient.auth_plugin
from novaclient import client
from novaclient import exceptions as exc
import novaclient.extension
from novaclient.openstack.common import strutils
from novaclient import utils
from novaclient.v1_1 import shell as shell_v1_1
from novaclient.v3 import shell as shell_v3

DEFAULT_OS_COMPUTE_API_VERSION = "1.1"
DEFAULT_NOVA_ENDPOINT_TYPE = 'publicURL'
DEFAULT_NOVA_SERVICE_TYPE = 'compute'

logger = logging.getLogger(__name__)


def positive_non_zero_float(text):
    if text is None:
        return None
    try:
        value = float(text)
    except ValueError:
        msg = "%s must be a float" % text
        raise argparse.ArgumentTypeError(msg)
    if value <= 0:
        msg = "%s must be greater than 0" % text
        raise argparse.ArgumentTypeError(msg)
    return value


class SecretsHelper(object):
    def __init__(self, args, client):
        self.args = args
        self.client = client
        self.key = None

    def _validate_string(self, text):
        if text is None or len(text) == 0:
            return False
        return True

    def _make_key(self):
        if self.key is not None:
            return self.key
        keys = [
            self.client.auth_url,
            self.client.projectid,
            self.client.user,
            self.client.region_name,
            self.client.endpoint_type,
            self.client.service_type,
            self.client.service_name,
            self.client.volume_service_name,
        ]
        for (index, key) in enumerate(keys):
            if key is None:
                keys[index] = '?'
            else:
                keys[index] = str(keys[index])
        self.key = "/".join(keys)
        return self.key

    def _prompt_password(self, verify=True):
        pw = None
        if hasattr(sys.stdin, 'isatty') and sys.stdin.isatty():
            # Check for Ctl-D
            try:
                while True:
                    pw1 = getpass.getpass('OS Password: ')
                    if verify:
                        pw2 = getpass.getpass('Please verify: ')
                    else:
                        pw2 = pw1
                    if pw1 == pw2 and self._validate_string(pw1):
                        pw = pw1
                        break
            except EOFError:
                pass
        return pw

    def save(self, auth_token, management_url, tenant_id):
        if not HAS_KEYRING or not self.args.os_cache:
            return
        if (auth_token == self.auth_token and
            management_url == self.management_url):
            # Nothing changed....
            return
        if not all([management_url, auth_token, tenant_id]):
            raise ValueError("Unable to save empty management url/auth token")
        value = "|".join([str(auth_token),
                          str(management_url),
                          str(tenant_id)])
        keyring.set_password("novaclient_auth", self._make_key(), value)

    @property
    def password(self):
        if self._validate_string(self.args.os_password):
            return self.args.os_password
        verify_pass = utils.bool_from_str(utils.env("OS_VERIFY_PASSWORD"))
        return self._prompt_password(verify_pass)

    @property
    def management_url(self):
        if not HAS_KEYRING or not self.args.os_cache:
            return None
        management_url = None
        try:
            block = keyring.get_password('novaclient_auth', self._make_key())
            if block:
                _token, management_url, _tenant_id = block.split('|', 2)
        except all_errors:
            pass
        return management_url

    @property
    def auth_token(self):
        # Now is where it gets complicated since we
        # want to look into the keyring module, if it
        # exists and see if anything was provided in that
        # file that we can use.
        if not HAS_KEYRING or not self.args.os_cache:
            return None
        token = None
        try:
            block = keyring.get_password('novaclient_auth', self._make_key())
            if block:
                token, _management_url, _tenant_id = block.split('|', 2)
        except all_errors:
            pass
        return token

    @property
    def tenant_id(self):
        if not HAS_KEYRING or not self.args.os_cache:
            return None
        tenant_id = None
        try:
            block = keyring.get_password('novaclient_auth', self._make_key())
            if block:
                _token, _management_url, tenant_id = block.split('|', 2)
        except all_errors:
            pass
        return tenant_id


class NovaClientArgumentParser(argparse.ArgumentParser):

    def __init__(self, *args, **kwargs):
        super(NovaClientArgumentParser, self).__init__(*args, **kwargs)

    def error(self, message):
        """error(message: string)

        Prints a usage message incorporating the message to stderr and
        exits.
        """
        self.print_usage(sys.stderr)
        #FIXME(lzyeval): if changes occur in argparse.ArgParser._check_value
        choose_from = ' (choose from'
        progparts = self.prog.partition(' ')
        self.exit(2, "error: %(errmsg)s\nTry '%(mainp)s help %(subp)s'"
                     " for more information.\n" %
                     {'errmsg': message.split(choose_from)[0],
                      'mainp': progparts[0],
                      'subp': progparts[2]})


class OpenStackComputeShell(object):

    def get_base_parser(self):
        parser = NovaClientArgumentParser(
            prog='nova',
            description=__doc__.strip(),
            epilog='See "nova help COMMAND" '
                   'for help on a specific command.',
            add_help=False,
            formatter_class=OpenStackHelpFormatter,
        )

        # Global arguments
        parser.add_argument('-h', '--help',
            action='store_true',
            help=argparse.SUPPRESS,
        )

        parser.add_argument('--version',
                            action='version',
                            version=novaclient.__version__)

        parser.add_argument('--debug',
            default=False,
            action='store_true',
            help="Print debugging output")

        parser.add_argument('--no-cache',
            default=not utils.bool_from_str(
                    utils.env('OS_NO_CACHE', default='true')),
            action='store_false',
            dest='os_cache',
            help=argparse.SUPPRESS)
        parser.add_argument('--no_cache',
            action='store_false',
            dest='os_cache',
            help=argparse.SUPPRESS)

        parser.add_argument('--os-cache',
            default=utils.env('OS_CACHE', default=False),
            action='store_true',
            help="Use the auth token cache.")

        parser.add_argument('--timings',
            default=False,
            action='store_true',
            help="Print call timing info")

        parser.add_argument('--timeout',
            default=600,
            metavar='<seconds>',
            type=positive_non_zero_float,
            help="Set HTTP call timeout (in seconds)")

        parser.add_argument('--os-username',
            metavar='<auth-user-name>',
            default=utils.env('OS_USERNAME', 'NOVA_USERNAME'),
            help='Defaults to env[OS_USERNAME].')
        parser.add_argument('--os_username',
            help=argparse.SUPPRESS)

        parser.add_argument('--os-password',
            metavar='<auth-password>',
            default=utils.env('OS_PASSWORD', 'NOVA_PASSWORD'),
            help='Defaults to env[OS_PASSWORD].')
        parser.add_argument('--os_password',
            help=argparse.SUPPRESS)

        parser.add_argument('--os-tenant-name',
            metavar='<auth-tenant-name>',
            default=utils.env('OS_TENANT_NAME', 'NOVA_PROJECT_ID'),
            help='Defaults to env[OS_TENANT_NAME].')
        parser.add_argument('--os_tenant_name',
            help=argparse.SUPPRESS)

        parser.add_argument('--os-tenant-id',
            metavar='<auth-tenant-id>',
            default=utils.env('OS_TENANT_ID'),
            help='Defaults to env[OS_TENANT_ID].')

        parser.add_argument('--os-auth-url',
            metavar='<auth-url>',
            default=utils.env('OS_AUTH_URL', 'NOVA_URL'),
            help='Defaults to env[OS_AUTH_URL].')
        parser.add_argument('--os_auth_url',
            help=argparse.SUPPRESS)

        parser.add_argument('--os-region-name',
            metavar='<region-name>',
            default=utils.env('OS_REGION_NAME', 'NOVA_REGION_NAME'),
            help='Defaults to env[OS_REGION_NAME].')
        parser.add_argument('--os_region_name',
            help=argparse.SUPPRESS)

        parser.add_argument('--os-auth-system',
            metavar='<auth-system>',
            default=utils.env('OS_AUTH_SYSTEM'),
            help='Defaults to env[OS_AUTH_SYSTEM].')
        parser.add_argument('--os_auth_system',
            help=argparse.SUPPRESS)

        parser.add_argument('--service-type',
            metavar='<service-type>',
            help='Defaults to compute for most actions')
        parser.add_argument('--service_type',
            help=argparse.SUPPRESS)

        parser.add_argument('--service-name',
            metavar='<service-name>',
            default=utils.env('NOVA_SERVICE_NAME'),
            help='Defaults to env[NOVA_SERVICE_NAME]')
        parser.add_argument('--service_name',
            help=argparse.SUPPRESS)

        parser.add_argument('--volume-service-name',
            metavar='<volume-service-name>',
            default=utils.env('NOVA_VOLUME_SERVICE_NAME'),
            help='Defaults to env[NOVA_VOLUME_SERVICE_NAME]')
        parser.add_argument('--volume_service_name',
            help=argparse.SUPPRESS)

        parser.add_argument('--endpoint-type',
            metavar='<endpoint-type>',
            default=utils.env('NOVA_ENDPOINT_TYPE',
                        default=DEFAULT_NOVA_ENDPOINT_TYPE),
            help='Defaults to env[NOVA_ENDPOINT_TYPE] or '
                    + DEFAULT_NOVA_ENDPOINT_TYPE + '.')
        # NOTE(dtroyer): We can't add --endpoint_type here due to argparse
        #                thinking usage-list --end is ambiguous; but it
        #                works fine with only --endpoint-type present
        #                Go figure.  I'm leaving this here for doc purposes.
        #parser.add_argument('--endpoint_type',
        #    help=argparse.SUPPRESS)

        parser.add_argument('--os-compute-api-version',
            metavar='<compute-api-ver>',
            default=utils.env('OS_COMPUTE_API_VERSION',
                default=DEFAULT_OS_COMPUTE_API_VERSION),
            help='Accepts 1.1 or 3, '
                 'defaults to env[OS_COMPUTE_API_VERSION].')
        parser.add_argument('--os_compute_api_version',
            help=argparse.SUPPRESS)

        parser.add_argument('--os-cacert',
            metavar='<ca-certificate>',
            default=utils.env('OS_CACERT', default=None),
            help='Specify a CA bundle file to use in '
                 'verifying a TLS (https) server certificate. '
                 'Defaults to env[OS_CACERT]')

        parser.add_argument('--insecure',
            default=utils.env('NOVACLIENT_INSECURE', default=False),
            action='store_true',
            help="Explicitly allow novaclient to perform \"insecure\" "
                 "SSL (https) requests. The server's certificate will "
                 "not be verified against any certificate authorities. "
                 "This option should be used with caution.")

        parser.add_argument('--bypass-url',
            metavar='<bypass-url>',
            dest='bypass_url',
            help="Use this API endpoint instead of the Service Catalog")
        parser.add_argument('--bypass_url',
            help=argparse.SUPPRESS)

        # The auth-system-plugins might require some extra options
        novaclient.auth_plugin.load_auth_system_opts(parser)

        return parser

    def get_subcommand_parser(self, version):
        parser = self.get_base_parser()

        self.subcommands = {}
        subparsers = parser.add_subparsers(metavar='<subcommand>')

        try:
            actions_module = {
                '1.1': shell_v1_1,
                '2': shell_v1_1,
                '3': shell_v3,
            }[version]
        except KeyError:
            actions_module = shell_v1_1

        self._find_actions(subparsers, actions_module)
        self._find_actions(subparsers, self)

        for extension in self.extensions:
            self._find_actions(subparsers, extension.module)

        self._add_bash_completion_subparser(subparsers)

        return parser

    def _discover_extensions(self, version):
        extensions = []
        for name, module in itertools.chain(
                self._discover_via_python_path(),
                self._discover_via_contrib_path(version),
                self._discover_via_entry_points()):

            extension = novaclient.extension.Extension(name, module)
            extensions.append(extension)

        return extensions

    def _discover_via_python_path(self):
        for (module_loader, name, _ispkg) in pkgutil.iter_modules():
            if name.endswith('_python_novaclient_ext'):
                if not hasattr(module_loader, 'load_module'):
                    # Python 2.6 compat: actually get an ImpImporter obj
                    module_loader = module_loader.find_module(name)

                module = module_loader.load_module(name)
                if hasattr(module, 'extension_name'):
                    name = module.extension_name

                yield name, module

    def _discover_via_contrib_path(self, version):
        module_path = os.path.dirname(os.path.abspath(__file__))
        version_str = "v%s" % version.replace('.', '_')
        ext_path = os.path.join(module_path, version_str, 'contrib')
        ext_glob = os.path.join(ext_path, "*.py")

        for ext_path in glob.iglob(ext_glob):
            name = os.path.basename(ext_path)[:-3]

            if name == "__init__":
                continue

            module = imp.load_source(name, ext_path)
            yield name, module

    def _discover_via_entry_points(self):
        for ep in pkg_resources.iter_entry_points('novaclient.extension'):
            name = ep.name
            module = ep.load()

            yield name, module

    def _add_bash_completion_subparser(self, subparsers):
        subparser = subparsers.add_parser('bash_completion',
            add_help=False,
            formatter_class=OpenStackHelpFormatter
        )
        self.subcommands['bash_completion'] = subparser
        subparser.set_defaults(func=self.do_bash_completion)

    def _find_actions(self, subparsers, actions_module):
        for attr in (a for a in dir(actions_module) if a.startswith('do_')):
            # I prefer to be hypen-separated instead of underscores.
            command = attr[3:].replace('_', '-')
            callback = getattr(actions_module, attr)
            desc = callback.__doc__ or ''
            action_help = desc.strip()
            arguments = getattr(callback, 'arguments', [])

            subparser = subparsers.add_parser(command,
                help=action_help,
                description=desc,
                add_help=False,
                formatter_class=OpenStackHelpFormatter
            )
            subparser.add_argument('-h', '--help',
                action='help',
                help=argparse.SUPPRESS,
            )
            self.subcommands[command] = subparser
            for (args, kwargs) in arguments:
                subparser.add_argument(*args, **kwargs)
            subparser.set_defaults(func=callback)

    def setup_debugging(self, debug):
        if not debug:
            return

        streamformat = "%(levelname)s (%(module)s:%(lineno)d) %(message)s"
        # Set up the root logger to debug so that the submodules can
        # print debug messages
        logging.basicConfig(level=logging.DEBUG,
                            format=streamformat)

    def main(self, argv):

        # Parse args once to find version and debug settings
        parser = self.get_base_parser()
        (options, args) = parser.parse_known_args(argv)
        self.setup_debugging(options.debug)

        # Discover available auth plugins
        novaclient.auth_plugin.discover_auth_systems()

        # build available subcommands based on version
        self.extensions = self._discover_extensions(
                options.os_compute_api_version)
        self._run_extension_hooks('__pre_parse_args__')

        # NOTE(dtroyer): Hackery to handle --endpoint_type due to argparse
        #                thinking usage-list --end is ambiguous; but it
        #                works fine with only --endpoint-type present
        #                Go figure.
        if '--endpoint_type' in argv:
            spot = argv.index('--endpoint_type')
            argv[spot] = '--endpoint-type'

        subcommand_parser = self.get_subcommand_parser(
                options.os_compute_api_version)
        self.parser = subcommand_parser

        if options.help or not argv:
            subcommand_parser.print_help()
            return 0

        args = subcommand_parser.parse_args(argv)
        self._run_extension_hooks('__post_parse_args__', args)

        # Short-circuit and deal with help right away.
        if args.func == self.do_help:
            self.do_help(args)
            return 0
        elif args.func == self.do_bash_completion:
            self.do_bash_completion(args)
            return 0

        (os_username, os_tenant_name, os_tenant_id, os_auth_url,
                os_region_name, os_auth_system, endpoint_type, insecure,
                service_type, service_name, volume_service_name,
                bypass_url, os_cache, cacert, timeout) = (
                        args.os_username,
                        args.os_tenant_name, args.os_tenant_id,
                        args.os_auth_url,
                        args.os_region_name, args.os_auth_system,
                        args.endpoint_type, args.insecure, args.service_type,
                        args.service_name, args.volume_service_name,
                        args.bypass_url, args.os_cache,
                        args.os_cacert, args.timeout)

        if os_auth_system and os_auth_system != "keystone":
            auth_plugin = novaclient.auth_plugin.load_plugin(os_auth_system)
        else:
            auth_plugin = None

        # Fetched and set later as needed
        os_password = None

        if not endpoint_type:
            endpoint_type = DEFAULT_NOVA_ENDPOINT_TYPE

        if not service_type:
            service_type = DEFAULT_NOVA_SERVICE_TYPE
            service_type = utils.get_service_type(args.func) or service_type

        #FIXME(usrleon): Here should be restrict for project id same as
        # for os_username or os_password but for compatibility it is not.
        if not utils.isunauthenticated(args.func):
            if auth_plugin:
                auth_plugin.parse_opts(args)

            if not auth_plugin or not auth_plugin.opts:
                if not os_username:
                    raise exc.CommandError("You must provide a username "
                            "via either --os-username or env[OS_USERNAME]")

            if not os_tenant_name and not os_tenant_id:
                raise exc.CommandError("You must provide a tenant name "
                        "or tenant id via --os-tenant-name, "
                        "--os-tenant-id, env[OS_TENANT_NAME] "
                        "or env[OS_TENANT_ID]")

            if not os_auth_url:
                if os_auth_system and os_auth_system != 'keystone':
                    os_auth_url = auth_plugin.get_auth_url()

            if not os_auth_url:
                    raise exc.CommandError("You must provide an auth url "
                            "via either --os-auth-url or env[OS_AUTH_URL] "
                            "or specify an auth_system which defines a "
                            "default url with --os-auth-system "
                            "or env[OS_AUTH_SYSTEM]")

        if (options.os_compute_api_version and
                options.os_compute_api_version != '1.0'):
            if not os_tenant_name and not os_tenant_id:
                raise exc.CommandError("You must provide a tenant name "
                        "or tenant id via --os-tenant-name, "
                        "--os-tenant-id, env[OS_TENANT_NAME] "
                        "or env[OS_TENANT_ID]")

            if not os_auth_url:
                raise exc.CommandError("You must provide an auth url "
                        "via either --os-auth-url or env[OS_AUTH_URL]")

        self.cs = client.Client(options.os_compute_api_version, os_username,
                os_password, os_tenant_name, tenant_id=os_tenant_id,
                auth_url=os_auth_url, insecure=insecure,
                region_name=os_region_name, endpoint_type=endpoint_type,
                extensions=self.extensions, service_type=service_type,
                service_name=service_name, auth_system=os_auth_system,
                auth_plugin=auth_plugin,
                volume_service_name=volume_service_name,
                timings=args.timings, bypass_url=bypass_url,
                os_cache=os_cache, http_log_debug=options.debug,
                cacert=cacert, timeout=timeout)

        # Now check for the password/token of which pieces of the
        # identifying keyring key can come from the underlying client
        if not utils.isunauthenticated(args.func):
            helper = SecretsHelper(args, self.cs.client)
            if (auth_plugin and auth_plugin.opts and
                    "os_password" not in auth_plugin.opts):
                use_pw = False
            else:
                use_pw = True

            tenant_id, auth_token, management_url = (helper.tenant_id,
                                                     helper.auth_token,
                                                     helper.management_url)
            if tenant_id and auth_token and management_url:
                self.cs.client.tenant_id = tenant_id
                self.cs.client.auth_token = auth_token
                self.cs.client.management_url = management_url
                # Try to auth with the given info, if it fails
                # go into password mode...
                try:
                    self.cs.authenticate()
                    use_pw = False
                except (exc.Unauthorized, exc.AuthorizationFailure):
                    # Likely it expired or just didn't work...
                    self.cs.client.auth_token = None
                    self.cs.client.management_url = None
            if use_pw:
                # Auth using token must have failed or not happened
                # at all, so now switch to password mode and save
                # the token when its gotten... using our keyring
                # saver
                os_password = helper.password
                if not os_password:
                    raise exc.CommandError(
                        'Expecting a password provided via either '
                        '--os-password, env[OS_PASSWORD], or '
                        'prompted response')
                self.cs.client.password = os_password
                self.cs.client.keyring_saver = helper

        try:
            if not utils.isunauthenticated(args.func):
                self.cs.authenticate()
        except exc.Unauthorized:
            raise exc.CommandError("Invalid OpenStack Nova credentials.")
        except exc.AuthorizationFailure:
            raise exc.CommandError("Unable to authorize user")

        args.func(self.cs, args)

        if args.timings:
            self._dump_timings(self.cs.get_timings())

    def _dump_timings(self, timings):
        class Tyme(object):
            def __init__(self, url, seconds):
                self.url = url
                self.seconds = seconds
        results = [Tyme(url, end - start) for url, start, end in timings]
        total = 0.0
        for tyme in results:
            total += tyme.seconds
        results.append(Tyme("Total", total))
        utils.print_list(results, ["url", "seconds"], sortby_index=None)

    def _run_extension_hooks(self, hook_type, *args, **kwargs):
        """Run hooks for all registered extensions."""
        for extension in self.extensions:
            extension.run_hooks(hook_type, *args, **kwargs)

    def do_bash_completion(self, _args):
        """
        Prints all of the commands and options to stdout so that the
        nova.bash_completion script doesn't have to hard code them.
        """
        commands = set()
        options = set()
        for sc_str, sc in self.subcommands.items():
            commands.add(sc_str)
            for option in sc._optionals._option_string_actions.keys():
                options.add(option)

        commands.remove('bash-completion')
        commands.remove('bash_completion')
        print(' '.join(commands | options))

    @utils.arg('command', metavar='<subcommand>', nargs='?',
                    help='Display help for <subcommand>')
    def do_help(self, args):
        """
        Display help about this program or one of its subcommands.
        """
        if args.command:
            if args.command in self.subcommands:
                self.subcommands[args.command].print_help()
            else:
                raise exc.CommandError("'%s' is not a valid subcommand" %
                                       args.command)
        else:
            self.parser.print_help()


# I'm picky about my shell help.
class OpenStackHelpFormatter(argparse.HelpFormatter):
    def start_section(self, heading):
        # Title-case the headings
        heading = '%s%s' % (heading[0].upper(), heading[1:])
        super(OpenStackHelpFormatter, self).start_section(heading)


def main():
    try:
        OpenStackComputeShell().main(map(strutils.safe_decode, sys.argv[1:]))

    except Exception as e:
        logger.debug(e, exc_info=1)
        print("ERROR: %s" % strutils.safe_encode(six.text_type(e)),
              file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
