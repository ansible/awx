# Copyright 2012 OpenStack Foundation
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
Command-line interface to the OpenStack Images API.
"""

from __future__ import print_function

import argparse
import copy
import getpass
import json
import logging
import os
from os.path import expanduser
import sys
import traceback

from oslo_utils import encodeutils
from oslo_utils import importutils
import six.moves.urllib.parse as urlparse

import glanceclient
from glanceclient import _i18n
from glanceclient.common import utils
from glanceclient import exc

from keystoneclient.auth.identity import v2 as v2_auth
from keystoneclient.auth.identity import v3 as v3_auth
from keystoneclient import discover
from keystoneclient.openstack.common.apiclient import exceptions as ks_exc
from keystoneclient import session

osprofiler_profiler = importutils.try_import("osprofiler.profiler")
_ = _i18n._


class OpenStackImagesShell(object):

    def _append_global_identity_args(self, parser):
        # FIXME(bobt): these are global identity (Keystone) arguments which
        # should be consistent and shared by all service clients. Therefore,
        # they should be provided by python-keystoneclient. We will need to
        # refactor this code once this functionality is avaible in
        # python-keystoneclient. See
        #
        # https://bugs.launchpad.net/python-keystoneclient/+bug/1332337
        #
        parser.add_argument('-k', '--insecure',
                            default=False,
                            action='store_true',
                            help='Explicitly allow glanceclient to perform '
                            '\"insecure SSL\" (https) requests. The server\'s '
                            'certificate will not be verified against any '
                            'certificate authorities. This option should '
                            'be used with caution.')

        parser.add_argument('--os-cert',
                            help='Path of certificate file to use in SSL '
                            'connection. This file can optionally be '
                            'prepended with the private key.')

        parser.add_argument('--cert-file',
                            dest='os_cert',
                            help='DEPRECATED! Use --os-cert.')

        parser.add_argument('--os-key',
                            help='Path of client key to use in SSL '
                            'connection. This option is not necessary '
                            'if your key is prepended to your cert file.')

        parser.add_argument('--key-file',
                            dest='os_key',
                            help='DEPRECATED! Use --os-key.')

        parser.add_argument('--os-cacert',
                            metavar='<ca-certificate-file>',
                            dest='os_cacert',
                            default=utils.env('OS_CACERT'),
                            help='Path of CA TLS certificate(s) used to '
                            'verify the remote server\'s certificate. '
                            'Without this option glance looks for the '
                            'default system CA certificates.')

        parser.add_argument('--ca-file',
                            dest='os_cacert',
                            help='DEPRECATED! Use --os-cacert.')

        parser.add_argument('--os-username',
                            default=utils.env('OS_USERNAME'),
                            help='Defaults to env[OS_USERNAME].')

        parser.add_argument('--os_username',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-user-id',
                            default=utils.env('OS_USER_ID'),
                            help='Defaults to env[OS_USER_ID].')

        parser.add_argument('--os-user-domain-id',
                            default=utils.env('OS_USER_DOMAIN_ID'),
                            help='Defaults to env[OS_USER_DOMAIN_ID].')

        parser.add_argument('--os-user-domain-name',
                            default=utils.env('OS_USER_DOMAIN_NAME'),
                            help='Defaults to env[OS_USER_DOMAIN_NAME].')

        parser.add_argument('--os-project-id',
                            default=utils.env('OS_PROJECT_ID'),
                            help='Another way to specify tenant ID. '
                                 'This option is mutually exclusive with '
                                 ' --os-tenant-id. '
                                 'Defaults to env[OS_PROJECT_ID].')

        parser.add_argument('--os-project-name',
                            default=utils.env('OS_PROJECT_NAME'),
                            help='Another way to specify tenant name. '
                                 'This option is mutually exclusive with '
                                 ' --os-tenant-name. '
                                 'Defaults to env[OS_PROJECT_NAME].')

        parser.add_argument('--os-project-domain-id',
                            default=utils.env('OS_PROJECT_DOMAIN_ID'),
                            help='Defaults to env[OS_PROJECT_DOMAIN_ID].')

        parser.add_argument('--os-project-domain-name',
                            default=utils.env('OS_PROJECT_DOMAIN_NAME'),
                            help='Defaults to env[OS_PROJECT_DOMAIN_NAME].')

        parser.add_argument('--os-password',
                            default=utils.env('OS_PASSWORD'),
                            help='Defaults to env[OS_PASSWORD].')

        parser.add_argument('--os_password',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-tenant-id',
                            default=utils.env('OS_TENANT_ID'),
                            help='Defaults to env[OS_TENANT_ID].')

        parser.add_argument('--os_tenant_id',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-tenant-name',
                            default=utils.env('OS_TENANT_NAME'),
                            help='Defaults to env[OS_TENANT_NAME].')

        parser.add_argument('--os_tenant_name',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-auth-url',
                            default=utils.env('OS_AUTH_URL'),
                            help='Defaults to env[OS_AUTH_URL].')

        parser.add_argument('--os_auth_url',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-region-name',
                            default=utils.env('OS_REGION_NAME'),
                            help='Defaults to env[OS_REGION_NAME].')

        parser.add_argument('--os_region_name',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-auth-token',
                            default=utils.env('OS_AUTH_TOKEN'),
                            help='Defaults to env[OS_AUTH_TOKEN].')

        parser.add_argument('--os_auth_token',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-service-type',
                            default=utils.env('OS_SERVICE_TYPE'),
                            help='Defaults to env[OS_SERVICE_TYPE].')

        parser.add_argument('--os_service_type',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-endpoint-type',
                            default=utils.env('OS_ENDPOINT_TYPE'),
                            help='Defaults to env[OS_ENDPOINT_TYPE].')

        parser.add_argument('--os_endpoint_type',
                            help=argparse.SUPPRESS)

    def get_base_parser(self):
        parser = argparse.ArgumentParser(
            prog='glance',
            description=__doc__.strip(),
            epilog='See "glance help COMMAND" '
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
                            version=glanceclient.__version__)

        parser.add_argument('-d', '--debug',
                            default=bool(utils.env('GLANCECLIENT_DEBUG')),
                            action='store_true',
                            help='Defaults to env[GLANCECLIENT_DEBUG].')

        parser.add_argument('-v', '--verbose',
                            default=False, action="store_true",
                            help="Print more verbose output")

        parser.add_argument('--get-schema',
                            default=False, action="store_true",
                            dest='get_schema',
                            help='Ignores cached copy and forces retrieval '
                                 'of schema that generates portions of the '
                                 'help text. Ignored with API version 1.')

        parser.add_argument('--timeout',
                            default=600,
                            help='Number of seconds to wait for a response')

        parser.add_argument('--no-ssl-compression',
                            dest='ssl_compression',
                            default=True, action='store_false',
                            help='Disable SSL compression when using https.')

        parser.add_argument('-f', '--force',
                            dest='force',
                            default=False, action='store_true',
                            help='Prevent select actions from requesting '
                            'user confirmation.')

        parser.add_argument('--os-image-url',
                            default=utils.env('OS_IMAGE_URL'),
                            help=('Defaults to env[OS_IMAGE_URL]. '
                                  'If the provided image url contains '
                                  'a version number and '
                                  '`--os-image-api-version` is omitted '
                                  'the version of the URL will be picked as '
                                  'the image api version to use.'))

        parser.add_argument('--os_image_url',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-image-api-version',
                            default=utils.env('OS_IMAGE_API_VERSION',
                                              default=None),
                            help='Defaults to env[OS_IMAGE_API_VERSION] or 1.')

        parser.add_argument('--os_image_api_version',
                            help=argparse.SUPPRESS)

        if osprofiler_profiler:
            parser.add_argument('--profile',
                                metavar='HMAC_KEY',
                                help='HMAC key to use for encrypting context '
                                'data for performance profiling of operation. '
                                'This key should be the value of HMAC key '
                                'configured in osprofiler middleware in '
                                'glance, it is specified in paste '
                                'configuration file at '
                                '/etc/glance/api-paste.ini and '
                                '/etc/glance/registry-paste.ini. Without key '
                                'the profiling will not be triggered even '
                                'if osprofiler is enabled on server side.')

        # FIXME(bobt): this method should come from python-keystoneclient
        self._append_global_identity_args(parser)

        return parser

    def get_subcommand_parser(self, version):
        parser = self.get_base_parser()

        self.subcommands = {}
        subparsers = parser.add_subparsers(metavar='<subcommand>')
        try:
            submodule = utils.import_versioned_module(version, 'shell')
        except ImportError:
            print('"%s" is not a supported API version. Example '
                  'values are "1" or "2".' % version)
            utils.exit()

        self._find_actions(subparsers, submodule)
        self._find_actions(subparsers, self)

        self._add_bash_completion_subparser(subparsers)

        return parser

    def _find_actions(self, subparsers, actions_module):
        for attr in (a for a in dir(actions_module) if a.startswith('do_')):
            # I prefer to be hypen-separated instead of underscores.
            command = attr[3:].replace('_', '-')
            callback = getattr(actions_module, attr)
            desc = callback.__doc__ or ''
            help = desc.strip().split('\n')[0]
            arguments = getattr(callback, 'arguments', [])

            subparser = subparsers.add_parser(command,
                                              help=help,
                                              description=desc,
                                              add_help=False,
                                              formatter_class=HelpFormatter
                                              )
            subparser.add_argument('-h', '--help',
                                   action='help',
                                   help=argparse.SUPPRESS,
                                   )
            self.subcommands[command] = subparser
            for (args, kwargs) in arguments:
                subparser.add_argument(*args, **kwargs)
            subparser.set_defaults(func=callback)

    def _add_bash_completion_subparser(self, subparsers):
        subparser = subparsers.add_parser('bash_completion',
                                          add_help=False,
                                          formatter_class=HelpFormatter)
        self.subcommands['bash_completion'] = subparser
        subparser.set_defaults(func=self.do_bash_completion)

    def _get_image_url(self, args):
        """Translate the available url-related options into a single string.

        Return the endpoint that should be used to talk to Glance if a
        clear decision can be made. Otherwise, return None.
        """
        if args.os_image_url:
            return args.os_image_url
        else:
            return None

    def _discover_auth_versions(self, session, auth_url):
        # discover the API versions the server is supporting base on the
        # given URL
        v2_auth_url = None
        v3_auth_url = None
        try:
            ks_discover = discover.Discover(session=session, auth_url=auth_url)
            v2_auth_url = ks_discover.url_for('2.0')
            v3_auth_url = ks_discover.url_for('3.0')
        except ks_exc.ClientException as e:
            # Identity service may not support discover API version.
            # Lets trying to figure out the API version from the original URL.
            url_parts = urlparse.urlparse(auth_url)
            (scheme, netloc, path, params, query, fragment) = url_parts
            path = path.lower()
            if path.startswith('/v3'):
                v3_auth_url = auth_url
            elif path.startswith('/v2'):
                v2_auth_url = auth_url
            else:
                # not enough information to determine the auth version
                msg = ('Unable to determine the Keystone version '
                       'to authenticate with using the given '
                       'auth_url. Identity service may not support API '
                       'version discovery. Please provide a versioned '
                       'auth_url instead. error=%s') % (e)
                raise exc.CommandError(msg)

        return (v2_auth_url, v3_auth_url)

    def _get_keystone_session(self, **kwargs):
        ks_session = session.Session.construct(kwargs)

        # discover the supported keystone versions using the given auth url
        auth_url = kwargs.pop('auth_url', None)
        (v2_auth_url, v3_auth_url) = self._discover_auth_versions(
            session=ks_session,
            auth_url=auth_url)

        # Determine which authentication plugin to use. First inspect the
        # auth_url to see the supported version. If both v3 and v2 are
        # supported, then use the highest version if possible.
        user_id = kwargs.pop('user_id', None)
        username = kwargs.pop('username', None)
        password = kwargs.pop('password', None)
        user_domain_name = kwargs.pop('user_domain_name', None)
        user_domain_id = kwargs.pop('user_domain_id', None)
        # project and tenant can be used interchangeably
        project_id = (kwargs.pop('project_id', None) or
                      kwargs.pop('tenant_id', None))
        project_name = (kwargs.pop('project_name', None) or
                        kwargs.pop('tenant_name', None))
        project_domain_id = kwargs.pop('project_domain_id', None)
        project_domain_name = kwargs.pop('project_domain_name', None)
        auth = None

        use_domain = (user_domain_id or
                      user_domain_name or
                      project_domain_id or
                      project_domain_name)
        use_v3 = v3_auth_url and (use_domain or (not v2_auth_url))
        use_v2 = v2_auth_url and not use_domain

        if use_v3:
            auth = v3_auth.Password(
                v3_auth_url,
                user_id=user_id,
                username=username,
                password=password,
                user_domain_id=user_domain_id,
                user_domain_name=user_domain_name,
                project_id=project_id,
                project_name=project_name,
                project_domain_id=project_domain_id,
                project_domain_name=project_domain_name)
        elif use_v2:
            auth = v2_auth.Password(
                v2_auth_url,
                username,
                password,
                tenant_id=project_id,
                tenant_name=project_name)
        else:
            # if we get here it means domain information is provided
            # (caller meant to use Keystone V3) but the auth url is
            # actually Keystone V2. Obviously we can't authenticate a V3
            # user using V2.
            exc.CommandError("Credential and auth_url mismatch. The given "
                             "auth_url is using Keystone V2 endpoint, which "
                             "may not able to handle Keystone V3 credentials. "
                             "Please provide a correct Keystone V3 auth_url.")

        ks_session.auth = auth
        return ks_session

    def _get_endpoint_and_token(self, args, force_auth=False):
        image_url = self._get_image_url(args)
        auth_token = args.os_auth_token

        auth_reqd = force_auth or (utils.is_authentication_required(args.func)
                                   and not (auth_token and image_url))

        if not auth_reqd:
            endpoint = image_url
            token = args.os_auth_token
        else:

            if not args.os_username:
                raise exc.CommandError(
                    _("You must provide a username via"
                      " either --os-username or "
                      "env[OS_USERNAME]"))

            if not args.os_password:
                # No password, If we've got a tty, try prompting for it
                if hasattr(sys.stdin, 'isatty') and sys.stdin.isatty():
                    # Check for Ctl-D
                    try:
                        args.os_password = getpass.getpass('OS Password: ')
                    except EOFError:
                        pass
                # No password because we didn't have a tty or the
                # user Ctl-D when prompted.
                if not args.os_password:
                    raise exc.CommandError(
                        _("You must provide a password via "
                          "either --os-password, "
                          "env[OS_PASSWORD], "
                          "or prompted response"))

            # Validate password flow auth
            project_info = (
                args.os_tenant_name or args.os_tenant_id or (
                    args.os_project_name and (
                        args.os_project_domain_name or
                        args.os_project_domain_id
                    )
                ) or args.os_project_id
            )

            if not project_info:
                # tenant is deprecated in Keystone v3. Use the latest
                # terminology instead.
                raise exc.CommandError(
                    _("You must provide a project_id or project_name ("
                      "with project_domain_name or project_domain_id) "
                      "via "
                      "  --os-project-id (env[OS_PROJECT_ID])"
                      "  --os-project-name (env[OS_PROJECT_NAME]),"
                      "  --os-project-domain-id "
                      "(env[OS_PROJECT_DOMAIN_ID])"
                      "  --os-project-domain-name "
                      "(env[OS_PROJECT_DOMAIN_NAME])"))

            if not args.os_auth_url:
                raise exc.CommandError(
                    _("You must provide an auth url via"
                      " either --os-auth-url or "
                      "via env[OS_AUTH_URL]"))

            kwargs = {
                'auth_url': args.os_auth_url,
                'username': args.os_username,
                'user_id': args.os_user_id,
                'user_domain_id': args.os_user_domain_id,
                'user_domain_name': args.os_user_domain_name,
                'password': args.os_password,
                'tenant_name': args.os_tenant_name,
                'tenant_id': args.os_tenant_id,
                'project_name': args.os_project_name,
                'project_id': args.os_project_id,
                'project_domain_name': args.os_project_domain_name,
                'project_domain_id': args.os_project_domain_id,
                'insecure': args.insecure,
                'cacert': args.os_cacert,
                'cert': args.os_cert,
                'key': args.os_key
            }
            ks_session = self._get_keystone_session(**kwargs)
            token = args.os_auth_token or ks_session.get_token()

            endpoint_type = args.os_endpoint_type or 'public'
            service_type = args.os_service_type or 'image'
            endpoint = args.os_image_url or ks_session.get_endpoint(
                service_type=service_type,
                interface=endpoint_type,
                region_name=args.os_region_name)

        return endpoint, token

    def _get_versioned_client(self, api_version, args, force_auth=False):
        endpoint, token = self._get_endpoint_and_token(args,
                                                       force_auth=force_auth)

        kwargs = {
            'token': token,
            'insecure': args.insecure,
            'timeout': args.timeout,
            'cacert': args.os_cacert,
            'cert': args.os_cert,
            'key': args.os_key,
            'ssl_compression': args.ssl_compression
        }
        client = glanceclient.Client(api_version, endpoint, **kwargs)
        return client

    def _cache_schemas(self, options, home_dir='~/.glanceclient'):
        homedir = expanduser(home_dir)
        if not os.path.exists(homedir):
            os.makedirs(homedir)

        resources = ['image', 'metadefs/namespace', 'metadefs/resource_type']
        schema_file_paths = [homedir + os.sep + x + '_schema.json'
                             for x in ['image', 'namespace', 'resource_type']]

        client = None
        for resource, schema_file_path in zip(resources, schema_file_paths):
            if (not os.path.exists(schema_file_path)) or options.get_schema:
                try:
                    if not client:
                        client = self._get_versioned_client('2', options,
                                                            force_auth=True)
                    schema = client.schemas.get(resource)

                    with open(schema_file_path, 'w') as f:
                        f.write(json.dumps(schema.raw()))
                except Exception:
                    # NOTE(esheffield) do nothing here, we'll get a message
                    # later if the schema is missing
                    pass

    def main(self, argv):
        # Parse args once to find version

        # NOTE(flepied) Under Python3, parsed arguments are removed
        # from the list so make a copy for the first parsing
        base_argv = copy.deepcopy(argv)
        parser = self.get_base_parser()
        (options, args) = parser.parse_known_args(base_argv)

        try:
            # NOTE(flaper87): Try to get the version from the
            # image-url first. If no version was specified, fallback
            # to the api-image-version arg. If both of these fail then
            # fallback to the minimum supported one and let keystone
            # do the magic.
            endpoint = self._get_image_url(options)
            endpoint, url_version = utils.strip_version(endpoint)
        except ValueError:
            # NOTE(flaper87): ValueError is raised if no endpoint is povided
            url_version = None

        # build available subcommands based on version
        try:
            api_version = int(options.os_image_api_version or url_version or 1)
        except ValueError:
            print("Invalid API version parameter")
            utils.exit()

        if api_version == 2:
            self._cache_schemas(options)

        subcommand_parser = self.get_subcommand_parser(api_version)
        self.parser = subcommand_parser

        # Handle top-level --help/-h before attempting to parse
        # a command off the command line
        if options.help or not argv:
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

        LOG = logging.getLogger('glanceclient')
        LOG.addHandler(logging.StreamHandler())
        LOG.setLevel(logging.DEBUG if args.debug else logging.INFO)

        profile = osprofiler_profiler and options.profile
        if profile:
            osprofiler_profiler.init(options.profile)

        client = self._get_versioned_client(api_version, args,
                                            force_auth=False)

        try:
            args.func(client, args)
        except exc.Unauthorized:
            raise exc.CommandError("Invalid OpenStack Identity credentials.")
        except Exception:
            # NOTE(kragniz) Print any exceptions raised to stderr if the
            # --debug flag is set
            if args.debug:
                traceback.print_exc()
            raise
        finally:
            if profile:
                trace_id = osprofiler_profiler.get().get_base_id()
                print("Profiling trace ID: %s" % trace_id)
                print("To display trace use next command:\n"
                      "osprofiler trace show --html %s " % trace_id)

    @utils.arg('command', metavar='<subcommand>', nargs='?',
               help='Display help for <subcommand>.')
    def do_help(self, args):
        """
        Display help about this program or one of its subcommands.
        """
        if getattr(args, 'command', None):
            if args.command in self.subcommands:
                self.subcommands[args.command].print_help()
            else:
                raise exc.CommandError("'%s' is not a valid subcommand" %
                                       args.command)
        else:
            self.parser.print_help()

    def do_bash_completion(self, _args):
        """Prints arguments for bash_completion.

        Prints all of the commands and options to stdout so that the
        glance.bash_completion script doesn't have to hard code them.
        """
        commands = set()
        options = set()
        for sc_str, sc in self.subcommands.items():
            commands.add(sc_str)
            for option in sc._optionals._option_string_actions.keys():
                options.add(option)

        commands.remove('bash_completion')
        commands.remove('bash-completion')
        print(' '.join(commands | options))


class HelpFormatter(argparse.HelpFormatter):
    def start_section(self, heading):
        # Title-case the headings
        heading = '%s%s' % (heading[0].upper(), heading[1:])
        super(HelpFormatter, self).start_section(heading)


def main():
    try:
        OpenStackImagesShell().main(map(encodeutils.safe_decode, sys.argv[1:]))
    except KeyboardInterrupt:
        utils.exit('... terminating glance client', exit_code=130)
    except Exception as e:
        utils.exit(utils.exception_to_str(e))
