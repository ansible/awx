import argparse
import functools
import json
import os
import re
import sys
import yaml

from distutils.util import strtobool

from .custom import CustomAction
from .format import add_output_formatting_arguments
from .resource import DEPRECATED_RESOURCES_REVERSE


UNIQUENESS_RULES = {
    'me': ('id', 'username'),
    'users': ('id', 'username'),
    'instances': ('id', 'hostname'),
}


def pk_or_name_list(v2, model_name, value, page=None):
    return [
        pk_or_name(v2, model_name, v.strip(), page=page)
        for v in value.split(',')
    ]


def pk_or_name(v2, model_name, value, page=None):
    if isinstance(value, int):
        return value

    if re.match(r'^[\d]+$', value):
        return int(value)

    identity = 'name'

    if not page:
        if not hasattr(v2, model_name):
            if model_name in DEPRECATED_RESOURCES_REVERSE:
                model_name = DEPRECATED_RESOURCES_REVERSE[model_name]

        if hasattr(v2, model_name):
            page = getattr(v2, model_name)

    if model_name in UNIQUENESS_RULES:
        identity = UNIQUENESS_RULES[model_name][-1]

    # certain related fields follow a pattern of <foo>_<model> e.g.,
    # insights_credential, target_credential etc...
    if not page and '_' in model_name:
        return pk_or_name(v2, model_name.split('_')[-1], value, page)

    if page:
        results = page.get(**{identity: value})
        if results.count == 1:
            return int(results.results[0].id)
        if results.count > 1:
            raise argparse.ArgumentTypeError(
                'Multiple {0} exist with that {1}. '
                'To look up an ID, run:\n'
                'awx {0} list --{1} "{2}" -f human'.format(
                    model_name, identity, value
                )
            )
        raise argparse.ArgumentTypeError(
            'Could not find any {0} with that {1}.'.format(
                model_name, identity
            )
        )

    return value


class ResourceOptionsParser(object):

    deprecated = False

    def __init__(self, v2, page, resource, parser):
        """Used to submit an OPTIONS request to the appropriate endpoint
        and apply the appropriate argparse arguments

        :param v2: a awxkit.api.pages.page.TentativePage instance
        :param page: a awxkit.api.pages.page.TentativePage instance
        :param resource: a string containing the resource (e.g., jobs)
        :param parser: an argparse.ArgumentParser object to append new args to
        """
        self.v2 = v2
        self.page = page
        self.resource = resource
        self.parser = parser
        self.options = getattr(
            self.page.options().json, 'actions', {'GET': {}}
        )
        self.get_allowed_options()
        if self.resource != 'settings':
            # /api/v2/settings is a special resource that doesn't have
            # traditional list/detail endpoints
            self.build_list_actions()
            self.build_detail_actions()

        self.handle_custom_actions()

    def get_allowed_options(self):
        options = self.page.connection.options(
            self.page.endpoint + '1/'
        )
        warning = options.headers.get('Warning', '')
        if '299' in warning and 'deprecated' in warning:
            self.deprecated = True
        self.allowed_options = options.headers.get('Allow', '').split(', ')

    def build_list_actions(self):
        action_map = {
            'GET': 'list',
            'POST': 'create',
        }
        for method, action in self.options.items():
            method = action_map[method]
            parser = self.parser.add_parser(method, help='')
            if method == 'list':
                parser.add_argument(
                    '--all', dest='all_pages', action='store_true',
                    help=(
                        'fetch all pages of content from the API when '
                        'returning results (instead of just the first page)'
                    )
                )
                add_output_formatting_arguments(parser, {})

    def build_detail_actions(self):
        allowed = ['get']
        if 'PUT' in self.allowed_options:
            allowed.append('modify')
        if 'DELETE' in self.allowed_options:
            allowed.append('delete')
        for method in allowed:
            parser = self.parser.add_parser(method, help='')
            self.parser.choices[method].add_argument(
                'id',
                type=functools.partial(pk_or_name, self.v2, self.resource),
                help='the ID (or unique name) of the resource'
            )
            if method == 'get':
                add_output_formatting_arguments(parser, {})

    def build_query_arguments(self, method, http_method):
        required_group = None
        for k, param in self.options.get(http_method, {}).items():
            required = (
                method == 'create' and
                param.get('required', False) is True
            )
            help_text = param.get('help_text', '')

            if method == 'list':
                if k == 'id':
                    # don't allow `awx <resource> list` to filter on `--id`
                    # it's weird, and that's what awx <resource> get is for
                    continue
                help_text = 'only list {} with the specified {}'.format(
                    self.resource,
                    k
                )

            if method == 'list' and param.get('filterable') is False:
                continue

            def json_or_yaml(v):
                if v.startswith('@'):
                    v = open(os.path.expanduser(v[1:])).read()
                try:
                    parsed = json.loads(v)
                except Exception:
                    try:
                        parsed = yaml.safe_load(v)
                    except Exception:
                        raise argparse.ArgumentTypeError("{} is not valid JSON or YAML".format(v))

                if not isinstance(parsed, dict):
                    raise argparse.ArgumentTypeError("{} is not valid JSON or YAML".format(v))

                for k, v in parsed.items():
                    # add support for file reading at top-level JSON keys
                    # (to make things like SSH key data easier to work with)
                    if isinstance(v, str) and v.startswith('@'):
                        path = os.path.expanduser(v[1:])
                        parsed[k] = open(path).read()

                return parsed

            def jsonstr(v):
                return json.dumps(json_or_yaml(v))

            kwargs = {
                'help': help_text,
                'required': required,
                'type': {
                    'string': str,
                    'field': int,
                    'integer': int,
                    'boolean': strtobool,
                    'id': functools.partial(pk_or_name, self.v2, k),
                    'json': json_or_yaml,
                    'list_of_ids': functools.partial(pk_or_name_list, self.v2, k),
                }.get(param['type'], str),
            }
            meta_map = {
                'string': 'TEXT',
                'integer': 'INTEGER',
                'boolean': 'BOOLEAN',
                'id': 'ID',  # foreign key
                'list_of_ids': '[ID, ID, ...]',
                'json': 'JSON/YAML',
            }
            if param.get('choices', []):
                kwargs['choices'] = [c[0] for c in param['choices']]
                # if there are choices, try to guess at the type (we can't
                # just assume it's a list of str, but the API doesn't actually
                # explicitly tell us in OPTIONS all the time)
                sphinx = 'sphinx-build' in ' '.join(sys.argv)
                if isinstance(kwargs['choices'][0], int) and not sphinx:
                    kwargs['type'] = int
                else:
                    kwargs['choices'] = [str(choice) for choice in kwargs['choices']]
            elif param['type'] in meta_map:
                kwargs['metavar'] = meta_map[param['type']]

                if param['type'] == 'id' and not kwargs.get('help'):
                    kwargs['help'] = 'the ID of the associated  {}'.format(k)

                if param['type'] == 'list_of_ids':
                    kwargs['help'] = 'a list of comma-delimited {} to associate (IDs or unique names)'.format(k)

                if param['type'] == 'json' and method != 'list':
                    help_parts = []
                    if kwargs.get('help'):
                        help_parts.append(kwargs['help'])
                    else:
                        help_parts.append('a JSON or YAML string.')
                    help_parts.append('You can optionally specify a file path e.g., @path/to/file.yml')
                    kwargs['help'] = ' '.join(help_parts)

            # SPECIAL CUSTOM LOGIC GOES HERE :'(
            # There are certain requirements that aren't captured well by our
            # HTTP OPTIONS due to $reasons
            # This is where custom handling for those goes.
            if self.resource == 'users' and method == 'create' and k == 'password':
                kwargs['required'] = required = True
            if self.resource == 'ad_hoc_commands' and method == 'create' and k in ('inventory', 'credential'):
                kwargs['required'] = required = True
            if self.resource == 'job_templates' and method == 'create' and k in ('project', 'playbook'):
                kwargs['required'] = required = True

            # unlike *other* actual JSON fields in the API, inventory and JT
            # variables *actually* want json.dumps() strings (ugh)
            # see: https://github.com/ansible/awx/issues/2371
            if (
                (self.resource in ('job_templates', 'workflow_job_templates') and k == 'extra_vars') or
                (self.resource in ('inventory', 'groups', 'hosts') and k == 'variables')
            ):
                kwargs['type'] = jsonstr

            if required:
                if required_group is None:
                    required_group = self.parser.choices[method].add_argument_group('required arguments')
                    # put the required group first (before the optional args group)
                    self.parser.choices[method]._action_groups.reverse()
                required_group.add_argument(
                    '--{}'.format(k),
                    **kwargs
                )
            else:
                self.parser.choices[method].add_argument(
                    '--{}'.format(k),
                    **kwargs
                )

    def handle_custom_actions(self):
        for _, action in CustomAction.registry.items():
            if action.resource != self.resource:
                continue
            if action.action not in self.parser.choices:
                self.parser.add_parser(action.action, help='')
            action(self.page).add_arguments(self.parser, self)
