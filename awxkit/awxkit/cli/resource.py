import json
import os
import sys

from awxkit import api, config
from awxkit.utils import to_str
from awxkit.api.pages import Page, TentativePage
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

EXPORTABLE_RESOURCES = [
    'users',
    'organizations',
    'teams',
    # 'credential_types',
    # 'credentials',
    # 'notification_templates',
    # 'projects',
    # 'inventory',
    # 'job_templates',
    # 'workflow_job_templates',
]

NATURAL_KEYS = {
    'user': ('username',),
    'organization': ('name',),
    'team': ('organization', 'name'),
    'credential_type': ('name', 'kind'),
    'credential': ('organization', 'name', 'credential_type'),
    'notification_template': ('organization', 'name'),
    'project': ('organization', 'name'),
    'inventory': ('organization', 'name'),
    'job_template': ('name',),
    'workflow_job_template': ('organization', 'name'),

    # related resources
    'role': ('name',),  # FIXME: we also need the content_object, itself as a natural key representation
}


class CustomCommand(metaclass=CustomRegistryMeta):
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
        auth.add_argument('--description', help='description of the generated OAuth2.0 token', metavar='TEXT')
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
        if getattr(parsed, 'description', None):
            kwargs['description'] = parsed.description
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
                print('export TOWER_OAUTH_TOKEN={}'.format(token))
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


class Import(CustomCommand):
    name = 'import'
    help_text = 'import resources into Tower'

    def create_resource(self, client, resource, asset):
        api_resource = getattr(client.v2, resource)
        if resource == 'users' and 'password' not in asset:
            asset['password'] = 'password'
        api_resource.post(asset)

    def handle(self, client, parser):
        if client.help:
            parser.print_help()
            raise SystemExit()

        data = json.load(sys.stdin)
        client.authenticate()

        for resource, assets in data.items():
            for asset in assets:
                self.create_resource(client, resource, asset)

        return {}


class Export(CustomCommand):
    name = 'export'
    help_text = 'export resources from Tower'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._natural_keys = {}

    def extend_parser(self, parser):
        resources = parser.add_argument_group('resources')

        for resource in EXPORTABLE_RESOURCES:
            # This parsing pattern will result in 3 different possible outcomes:
            # 1) the resource flag is not used at all, which will result in the attr being None
            # 2) the resource flag is used with no argument, which will result in the attr being ''
            # 3) the resource flag is used with an argument, and the attr will be that argument's value
            resources.add_argument('--{}'.format(resource), nargs='?', const='')

    def get_resource_options(self, endpoint):
        return endpoint.options().json['actions']['POST']

    def register_natural_key(self, asset):
        if asset['url'] in self._natural_keys:
            return

        natural_key = {'type': asset['type']}
        lookup = NATURAL_KEYS.get(asset['type'])
        if callable(lookup):
            natural_key.update(lookup(asset))
        else:
            natural_key.update((key, asset.get(key)) for key in lookup or ())

        self._natural_keys[asset['url']] = natural_key

    def get_natural_key(self, url=None, asset=None):
        if url is None:
            url = asset['url']
        if url not in self._natural_keys:
            if asset is None:
                # get the asset by following the url
                raise Exception("Oops!")

            self.register_natural_key(asset)

        return self._natural_keys[url]

    def get_assets(self, resource, value):
        endpoint = getattr(self.v2, resource)
        if value:
            from .options import pk_or_name

            pk = pk_or_name(self.v2, resource, value)
            results = endpoint.get(id=pk).json['results']
        else:
            results = endpoint.get(all_pages=True).json['results']

        for asset in results:
            self.register_natural_key(asset)

        options = self.get_resource_options(endpoint)
        return [self.enhance_asset(endpoint, asset, options) for asset in results]

    def enhance_asset(self, endpoint, asset, options):
        fields = {
            key: asset[key] for key in options
            if key in asset and options[key]['type'] != 'id'
        }

        fk_fields = {
            key: self.get_natural_key(url=asset['related'][key]) for key in options
            if key in asset and options[key]['type'] == 'id'
        }

        related = {}
        for k, v in asset['related'].items():
            if k != 'roles':
                continue
            related_endpoint = TentativePage(v, endpoint.connection)
            data = related_endpoint.get(all_pages=True).json
            if 'results' in data:
                related[k] = [self.get_natural_key(asset=x) for x in data['results']]

        related_fields = {'related': related} if related else {}
        return dict(**fields, **fk_fields, **related_fields)

    def handle(self, client, parser):
        self.extend_parser(parser)

        if client.help:
            parser.print_help()
            raise SystemExit()

        client.authenticate()
        parsed = parser.parse_known_args()[0]

        # If no resource flags are explicitly used, export everything.
        all_resources = all(getattr(parsed, resource, None) is None for resource in EXPORTABLE_RESOURCES)

        self.v2 = client.v2

        data = {}
        for resource in EXPORTABLE_RESOURCES:
            value = getattr(parsed, resource, None)
            if all_resources or value is not None:
                data[resource] = self.get_assets(resource, value)

        return data


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

    resource = client.parser.parse_known_args()[0].resource
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
            try:
                connection = client.root.connection
            except AttributeError:
                connection = None
            formatted = format_response(
                Page.from_json(response, connection=connection),
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
