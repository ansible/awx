import os

from six import PY3, with_metaclass

from awxkit import api, config
from awxkit.utils import to_str
from awxkit.api.pages import Page
from awxkit.cli.format import FORMATTERS, format_response, add_authentication_arguments
from awxkit.cli.utils import CustomRegistryMeta, cprint


CONTROL_RESOURCES = ['ping', 'config', 'me', 'metrics']

DEPRECATED_RESOURCES = {
    'ad_hoc_commands': 'ad_hoc',
    'applications': 'application',
    'credentials': 'credential',
    'credential_types': 'credential_type',
    'groups': 'group',
    'hosts': 'host',
    'instances': 'instance',
    'instance_groups': 'instance_group',
    'inventory': 'inventories',
    'inventory_scripts': 'inventory_script',
    'inventory_sources': 'inventory_source',
    'inventory_updates': 'inventory_update',
    'jobs': 'job',
    'job_templates': 'job_template',
    'labels': 'label',
    'workflow_job_template_nodes': 'node',
    'notification_templates': 'notification_template',
    'organizations': 'organization',
    'projects': 'project',
    'project_updates': 'project_update',
    'roles': 'role',
    'schedules': 'schedule',
    'settings': 'setting',
    'teams': 'team',
    'workflow_job_templates': 'workflow',
    'workflow_jobs': 'workflow_job',
    'users': 'user'
}
DEPRECATED_RESOURCES_REVERSE = dict(
    (v, k) for k, v in DEPRECATED_RESOURCES.items()
)


class CustomCommand(with_metaclass(CustomRegistryMeta)):
    """Base class for implementing custom commands.

    Custom commands represent static code which should run - they are
    responsible for returning and formatting their own output (which may or may
    not be JSON/YAML).
    """

    help_text = ''

    @property
    def name(self):
        raise NotImplementedError()

    def handle(self, client, parser):
        """To be implemented by subclasses.
        Should return a dictionary that is JSON serializable
        """
        raise NotImplementedError()


class Login(CustomCommand):
    name = 'login'
    help_text = 'authenticate and retrieve an OAuth2 token'

    def print_help(self, parser):
        add_authentication_arguments(parser, os.environ)
        parser.print_help()

    def handle(self, client, parser):
        auth = parser.add_argument_group('OAuth2.0 Options')
        auth.add_argument('--conf.client_id', metavar='TEXT')
        auth.add_argument('--conf.client_secret', metavar='TEXT')
        auth.add_argument(
            '--conf.scope', choices=['read', 'write'], default='write'
        )
        if client.help:
            self.print_help(parser)
            raise SystemExit()
        parsed = parser.parse_known_args()[0]
        kwargs = {
            'client_id': getattr(parsed, 'conf.client_id', None),
            'client_secret': getattr(parsed, 'conf.client_secret', None),
            'scope': getattr(parsed, 'conf.scope', None),
        }
        try:
            token = api.Api().get_oauth2_token(**kwargs)
        except Exception as e:
            self.print_help(parser)
            cprint(
                'Error retrieving an OAuth2.0 token ({}).'.format(e.__class__),
                'red'
            )
        else:
            fmt = client.get_config('format')
            if fmt == 'human':
                print('export TOWER_TOKEN={}'.format(token))
            else:
                print(to_str(FORMATTERS[fmt]({'token': token}, '.')).strip())


class Config(CustomCommand):
    name = 'config'
    help_text = 'print current configuration values'

    def handle(self, client, parser):
        if client.help:
            parser.print_help()
            raise SystemExit()
        return {
            'base_url': config.base_url,
            'token': client.get_config('token'),
            'use_sessions': config.use_sessions,
            'credentials': config.credentials,
        }


def parse_resource(client, skip_deprecated=False):
    subparsers = client.parser.add_subparsers(
        dest='resource',
        metavar='resource',
    )

    # check if the user is running a custom command
    for command in CustomCommand.__subclasses__():
        client.subparsers[command.name] = subparsers.add_parser(
            command.name, help=command.help_text
        )

    if hasattr(client, 'v2'):
        for k in client.v2.json.keys():
            if k in ('dashboard',):
                # the Dashboard API is deprecated and not supported
                continue

            # argparse aliases are *only* supported in Python3 (not 2.7)
            kwargs = {}
            if not skip_deprecated:
                if k in DEPRECATED_RESOURCES:
                    kwargs['aliases'] = [DEPRECATED_RESOURCES[k]]

            client.subparsers[k] = subparsers.add_parser(
                k, help='', **kwargs
            )

    try:
        resource = client.parser.parse_known_args()[0].resource
    except SystemExit:
        if PY3:
            raise
        else:
            # Unfortunately, argparse behavior between py2 and py3
            # changed in a notable way when required subparsers
            # have invalid (or missing) arguments specified
            # see: https://github.com/python/cpython/commit/f97c59aaba2d93e48cbc6d25f7ff9f9c87f8d0b2
            # In py2, this raises a SystemExit; which we want to _ignore_
            resource = None
    if resource in DEPRECATED_RESOURCES.values():
        client.argv[
            client.argv.index(resource)
        ] = DEPRECATED_RESOURCES_REVERSE[resource]
        resource = DEPRECATED_RESOURCES_REVERSE[resource]

    if resource in CustomCommand.registry:
        parser = client.subparsers[resource]
        command = CustomCommand.registry[resource]()
        response = command.handle(client, parser)
        if response:
            _filter = client.get_config('filter')
            if (
                resource == 'config' and
                client.get_config('format') == 'human'
            ):
                response = {
                    'count': len(response),
                    'results': [
                        {'key': k, 'value': v}
                        for k, v in response.items()
                    ]
                }
                _filter = 'key, value'
            formatted = format_response(
                Page.from_json(response),
                fmt=client.get_config('format'),
                filter=_filter
            )
            print(formatted)
        raise SystemExit()
    else:
        return resource


def is_control_resource(resource):
    # special root level resources that don't don't represent database
    # entities that follow the list/detail semantic
    return resource in CONTROL_RESOURCES
