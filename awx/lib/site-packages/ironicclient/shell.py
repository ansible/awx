# -*- coding: utf-8 -*-
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
Command-line interface to the OpenStack Bare Metal Provisioning API.
"""

from __future__ import print_function

import argparse
import getpass
import logging
import sys

import httplib2
from keystoneclient.auth.identity import v2 as v2_auth
from keystoneclient.auth.identity import v3 as v3_auth
from keystoneclient import discover
from keystoneclient.openstack.common.apiclient import exceptions as ks_exc
from keystoneclient import session as kssession
import six.moves.urllib.parse as urlparse


import ironicclient
from ironicclient import client as iroclient
from ironicclient.common.i18n import _
from ironicclient.common import utils
from ironicclient import exc
from ironicclient.openstack.common import cliutils


LATEST_API_VERSION = ('1', 'latest')


class IronicShell(object):

    def _append_global_identity_args(self, parser):
        # FIXME(dhu): these are global identity (Keystone) arguments which
        # should be consistent and shared by all service clients. Therefore,
        # they should be provided by python-keystoneclient. We will need to
        # refactor this code once this functionality is avaible in
        # python-keystoneclient.

        # Register arguments needed for a Session
        kssession.Session.register_cli_options(parser)

        parser.add_argument('--os-user-domain-id',
                            default=cliutils.env('OS_USER_DOMAIN_ID'),
                            help='Defaults to env[OS_USER_DOMAIN_ID].')

        parser.add_argument('--os-user-domain-name',
                            default=cliutils.env('OS_USER_DOMAIN_NAME'),
                            help='Defaults to env[OS_USER_DOMAIN_NAME].')

        parser.add_argument('--os-project-id',
                            default=cliutils.env('OS_PROJECT_ID'),
                            help='Another way to specify tenant ID. '
                                 'This option is mutually exclusive with '
                                 ' --os-tenant-id. '
                                 'Defaults to env[OS_PROJECT_ID].')

        parser.add_argument('--os-project-name',
                            default=cliutils.env('OS_PROJECT_NAME'),
                            help='Another way to specify tenant name. '
                                 'This option is mutually exclusive with '
                                 ' --os-tenant-name. '
                                 'Defaults to env[OS_PROJECT_NAME].')

        parser.add_argument('--os-project-domain-id',
                            default=cliutils.env('OS_PROJECT_DOMAIN_ID'),
                            help='Defaults to env[OS_PROJECT_DOMAIN_ID].')

        parser.add_argument('--os-project-domain-name',
                            default=cliutils.env('OS_PROJECT_DOMAIN_NAME'),
                            help='Defaults to env[OS_PROJECT_DOMAIN_NAME].')

    def get_base_parser(self):
        parser = argparse.ArgumentParser(
            prog='ironic',
            description=__doc__.strip(),
            epilog='See "ironic help COMMAND" '
                   'for help on a specific command.',
            add_help=False,
            formatter_class=HelpFormatter,
        )

        # Global arguments
        parser.add_argument('-h', '--help',
                            action='store_true',
                            help=argparse.SUPPRESS,
                            )

        parser.add_argument('--version',
                            action='version',
                            version=ironicclient.__version__)

        parser.add_argument('--debug',
                            default=bool(cliutils.env('IRONICCLIENT_DEBUG')),
                            action='store_true',
                            help='Defaults to env[IRONICCLIENT_DEBUG]')

        parser.add_argument('-v', '--verbose',
                            default=False, action="store_true",
                            help="Print more verbose output")

        # for backward compatibility only
        parser.add_argument('--cert-file',
                            dest='os_cert',
                            help='DEPRECATED! Use --os-cert.')

        # for backward compatibility only
        parser.add_argument('--key-file',
                            dest='os_key',
                            help='DEPRECATED! Use --os-key.')

        # for backward compatibility only
        parser.add_argument('--ca-file',
                            dest='os_cacert',
                            help='DEPRECATED! Use --os-cacert.')

        parser.add_argument('--os-username',
                            default=cliutils.env('OS_USERNAME'),
                            help='Defaults to env[OS_USERNAME]')

        parser.add_argument('--os_username',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-password',
                            default=cliutils.env('OS_PASSWORD'),
                            help='Defaults to env[OS_PASSWORD]')

        parser.add_argument('--os_password',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-tenant-id',
                            default=cliutils.env('OS_TENANT_ID'),
                            help='Defaults to env[OS_TENANT_ID]')

        parser.add_argument('--os_tenant_id',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-tenant-name',
                            default=cliutils.env('OS_TENANT_NAME'),
                            help='Defaults to env[OS_TENANT_NAME]')

        parser.add_argument('--os_tenant_name',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-auth-url',
                            default=cliutils.env('OS_AUTH_URL'),
                            help='Defaults to env[OS_AUTH_URL]')

        parser.add_argument('--os_auth_url',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-region-name',
                            default=cliutils.env('OS_REGION_NAME'),
                            help='Defaults to env[OS_REGION_NAME]')

        parser.add_argument('--os_region_name',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-auth-token',
                            default=cliutils.env('OS_AUTH_TOKEN'),
                            help='Defaults to env[OS_AUTH_TOKEN]')

        parser.add_argument('--os_auth_token',
                            help=argparse.SUPPRESS)

        parser.add_argument('--ironic-url',
                            default=cliutils.env('IRONIC_URL'),
                            help='Defaults to env[IRONIC_URL]')

        parser.add_argument('--ironic_url',
                            help=argparse.SUPPRESS)

        parser.add_argument('--ironic-api-version',
                            default=cliutils.env(
                                'IRONIC_API_VERSION', default='1'),
                            help='Accepts 1.x (where "x" is microversion) '
                                 'or "latest", Defaults to '
                                 'env[IRONIC_API_VERSION] or 1')

        parser.add_argument('--ironic_api_version',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-service-type',
                            default=cliutils.env('OS_SERVICE_TYPE'),
                            help='Defaults to env[OS_SERVICE_TYPE] or '
                                 '"baremetal"')

        parser.add_argument('--os_service_type',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-endpoint',
                            default=cliutils.env('OS_SERVICE_ENDPOINT'),
                            help='Specify an endpoint to use instead of '
                                 'retrieving one from the service catalog '
                                 '(via authentication). '
                                 'Defaults to env[OS_SERVICE_ENDPOINT].')

        parser.add_argument('--os_endpoint',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-endpoint-type',
                            default=cliutils.env('OS_ENDPOINT_TYPE'),
                            help='Defaults to env[OS_ENDPOINT_TYPE] or '
                                 '"publicURL"')

        parser.add_argument('--os_endpoint_type',
                            help=argparse.SUPPRESS)

        # FIXME(gyee): this method should come from python-keystoneclient.
        # Will refactor this code once it is available.
        # https://bugs.launchpad.net/python-keystoneclient/+bug/1332337

        self._append_global_identity_args(parser)

        return parser

    def get_subcommand_parser(self, version):
        parser = self.get_base_parser()

        self.subcommands = {}
        subparsers = parser.add_subparsers(metavar='<subcommand>')
        submodule = utils.import_versioned_module(version, 'shell')
        submodule.enhance_parser(parser, subparsers, self.subcommands)
        utils.define_commands_from_module(subparsers, self, self.subcommands)
        return parser

    def _setup_debugging(self, debug):
        if debug:
            logging.basicConfig(
                format="%(levelname)s (%(module)s:%(lineno)d) %(message)s",
                level=logging.DEBUG)

            httplib2.debuglevel = 1
        else:
            logging.basicConfig(
                format="%(levelname)s %(message)s",
                level=logging.CRITICAL)

    def do_bash_completion(self):
        """Prints all of the commands and options for bash-completion."""
        commands = set()
        options = set()
        for sc_str, sc in self.subcommands.items():
            commands.add(sc_str)
            for option in sc._optionals._option_string_actions.keys():
                options.add(option)

        commands.remove('bash-completion')
        print(' '.join(commands | options))

    def _discover_auth_versions(self, session, auth_url):
        # discover the API versions the server is supporting base on the
        # given URL
        v2_auth_url = None
        v3_auth_url = None
        try:
            ks_discover = discover.Discover(session=session, auth_url=auth_url)
            v2_auth_url = ks_discover.url_for('2.0')
            v3_auth_url = ks_discover.url_for('3.0')
        except ks_exc.ClientException:
            # Identity service may not support discover API version.
            # Let's try to figure out the API version from the original URL.
            url_parts = urlparse.urlparse(auth_url)
            (scheme, netloc, path, params, query, fragment) = url_parts
            path = path.lower()
            if path.startswith('/v3'):
                v3_auth_url = auth_url
            elif path.startswith('/v2'):
                v2_auth_url = auth_url
            else:
                # not enough information to determine the auth version
                msg = _('Unable to determine the Keystone version '
                        'to authenticate with using the given '
                        'auth_url. Identity service may not support API '
                        'version discovery. Please provide a versioned '
                        'auth_url instead. %s') % auth_url
                raise exc.CommandError(msg)

        return (v2_auth_url, v3_auth_url)

    def _get_keystone_v3_auth(self, v3_auth_url, **kwargs):
        auth_token = kwargs.pop('auth_token', None)
        if auth_token:
            return v3_auth.Token(v3_auth_url, auth_token)
        else:
            return v3_auth.Password(v3_auth_url, **kwargs)

    def _get_keystone_v2_auth(self, v2_auth_url, **kwargs):
        auth_token = kwargs.pop('auth_token', None)
        if auth_token:
            return v2_auth.Token(v2_auth_url, auth_token,
                                 tenant_id=kwargs.pop('project_id', None),
                                 tenant_name=kwargs.pop('project_name', None))
        else:
            return v2_auth.Password(
                v2_auth_url,
                username=kwargs.pop('username', None),
                password=kwargs.pop('password', None),
                tenant_id=kwargs.pop('project_id', None),
                tenant_name=kwargs.pop('project_name', None))

    def _get_keystone_auth(self, session, auth_url, **kwargs):
        # FIXME(dhu): this code should come from keystoneclient

        # discover the supported keystone versions using the given url
        (v2_auth_url, v3_auth_url) = self._discover_auth_versions(
            session=session,
            auth_url=auth_url)

        # Determine which authentication plugin to use. First inspect the
        # auth_url to see the supported version. If both v3 and v2 are
        # supported, then use the highest version if possible.
        auth = None
        if v3_auth_url and v2_auth_url:
            user_domain_name = kwargs.get('user_domain_name', None)
            user_domain_id = kwargs.get('user_domain_id', None)
            project_domain_name = kwargs.get('project_domain_name', None)
            project_domain_id = kwargs.get('project_domain_id', None)

            # support both v2 and v3 auth. Use v3 if domain information is
            # provided.
            if (user_domain_name or user_domain_id or project_domain_name or
                    project_domain_id):
                auth = self._get_keystone_v3_auth(v3_auth_url, **kwargs)
            else:
                auth = self._get_keystone_v2_auth(v2_auth_url, **kwargs)
        elif v3_auth_url:
            # support only v3
            auth = self._get_keystone_v3_auth(v3_auth_url, **kwargs)
        elif v2_auth_url:
            # support only v2
            auth = self._get_keystone_v2_auth(v2_auth_url, **kwargs)
        else:
            msg = _('Unable to determine the Keystone version '
                    'to authenticate with using the given '
                    'auth_url.')
            raise exc.CommandError(msg)

        return auth

    def _check_version(self, api_version):
        if api_version == 'latest':
            return LATEST_API_VERSION
        else:
            try:
                versions = tuple(int(i) for i in api_version.split('.'))
            except ValueError:
                versions = ()
            if len(versions) == 1:
                # Default value of ironic_api_version is '1'.
                # If user not specify the value of api version, not passing
                # headers at all.
                os_ironic_api_version = None
            elif len(versions) == 2:
                os_ironic_api_version = api_version
                # In the case of '1.0'
                if versions[1] == 0:
                    os_ironic_api_version = None
            else:
                msg = _("The requested API version %(ver)s is an unexpected "
                        "format. Acceptable formats are 'X', 'X.Y', or the "
                        "literal string '%(latest)s'."
                        ) % {'ver': api_version, 'latest': 'latest'}
                raise exc.CommandError(msg)

            api_major_version = versions[0]
            return (api_major_version, os_ironic_api_version)

    def main(self, argv):
        # Parse args once to find version
        parser = self.get_base_parser()
        (options, args) = parser.parse_known_args(argv)
        self._setup_debugging(options.debug)

        # build available subcommands based on version
        (api_major_version, os_ironic_api_version) = (
            self._check_version(options.ironic_api_version))

        subcommand_parser = self.get_subcommand_parser(api_major_version)
        self.parser = subcommand_parser

        # Handle top-level --help/-h before attempting to parse
        # a command off the command line
        if options.help or not argv:
            self.do_help(options)
            return 0

        # Parse args again and call whatever callback was selected
        args = subcommand_parser.parse_args(argv)

        # Short-circuit and deal with these commands right away.
        if args.func == self.do_help:
            self.do_help(args)
            return 0
        elif args.func == self.do_bash_completion:
            self.do_bash_completion()
            return 0

        if not (args.os_auth_token and (args.ironic_url or args.os_endpoint)):
            if not args.os_username:
                raise exc.CommandError(_("You must provide a username via "
                                         "either --os-username or via "
                                         "env[OS_USERNAME]"))

            if not args.os_password:
                # No password, If we've got a tty, try prompting for it
                if hasattr(sys.stdin, 'isatty') and sys.stdin.isatty():
                    # Check for Ctl-D
                    try:
                        args.os_password = getpass.getpass(
                            'OpenStack Password: ')
                    except EOFError:
                        pass
            # No password because we didn't have a tty or the
            # user Ctl-D when prompted.
            if not args.os_password:
                raise exc.CommandError(_("You must provide a password via "
                                         "either --os-password, "
                                         "env[OS_PASSWORD], "
                                         "or prompted response"))

            if not (args.os_tenant_id or args.os_tenant_name or
                    args.os_project_id or args.os_project_name):
                raise exc.CommandError(
                    _("You must provide a project name or"
                      " project id via --os-project-name, --os-project-id,"
                      " env[OS_PROJECT_ID] or env[OS_PROJECT_NAME].  You may"
                      " use os-project and os-tenant interchangeably."))

            if not args.os_auth_url:
                raise exc.CommandError(_("You must provide an auth url via "
                                         "either --os-auth-url or via "
                                         "env[OS_AUTH_URL]"))

        endpoint = args.ironic_url or args.os_endpoint
        service_type = args.os_service_type or 'baremetal'
        project_id = args.os_project_id or args.os_tenant_id
        project_name = args.os_project_name or args.os_tenant_name

        if (args.os_auth_token and (args.ironic_url or args.os_endpoint)):
            kwargs = {
                'token': args.os_auth_token,
                'insecure': args.insecure,
                'timeout': args.timeout,
                'ca_file': args.os_cacert,
                'cert_file': args.os_cert,
                'key_file': args.os_key,
                'auth_ref': None,
            }
        elif (args.os_username and
              args.os_password and
              args.os_auth_url and
              (project_id or project_name)):

            keystone_session = kssession.Session.load_from_cli_options(args)

            kwargs = {
                'username': args.os_username,
                'user_domain_id': args.os_user_domain_id,
                'user_domain_name': args.os_user_domain_name,
                'password': args.os_password,
                'auth_token': args.os_auth_token,
                'project_id': project_id,
                'project_name': project_name,
                'project_domain_id': args.os_project_domain_id,
                'project_domain_name': args.os_project_domain_name,
            }
            keystone_auth = self._get_keystone_auth(keystone_session,
                                                    args.os_auth_url,
                                                    **kwargs)
            if not endpoint:
                svc_type = args.os_service_type
                region_name = args.os_region_name
                endpoint = keystone_auth.get_endpoint(keystone_session,
                                                      service_type=svc_type,
                                                      region_name=region_name)

            endpoint_type = args.os_endpoint_type or 'publicURL'
            kwargs = {
                'auth_url': args.os_auth_url,
                'session': keystone_session,
                'auth': keystone_auth,
                'service_type': service_type,
                'endpoint_type': endpoint_type,
                'region_name': args.os_region_name,
                'username': args.os_username,
                'password': args.os_password,
            }
        kwargs['os_ironic_api_version'] = os_ironic_api_version
        client = iroclient.Client(api_major_version, endpoint, **kwargs)

        try:
            args.func(client, args)
        except exc.Unauthorized:
            raise exc.CommandError(_("Invalid OpenStack Identity credentials"))

    @cliutils.arg('command', metavar='<subcommand>', nargs='?',
                  help='Display help for <subcommand>')
    def do_help(self, args):
        """Display help about this program or one of its subcommands."""
        if getattr(args, 'command', None):
            if args.command in self.subcommands:
                self.subcommands[args.command].print_help()
            else:
                raise exc.CommandError(_("'%s' is not a valid subcommand") %
                                       args.command)
        else:
            self.parser.print_help()


class HelpFormatter(argparse.HelpFormatter):
    def start_section(self, heading):
        # Title-case the headings
        heading = '%s%s' % (heading[0].upper(), heading[1:])
        super(HelpFormatter, self).start_section(heading)


def main():
    try:
        IronicShell().main(sys.argv[1:])
    except KeyboardInterrupt:
        print("... terminating ironic client", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
