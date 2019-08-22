from distutils.util import strtobool

from .custom import CustomAction
from .format import add_output_formatting_arguments


class ResourceOptionsParser(object):

    def __init__(self, page, resource, parser):
        """Used to submit an OPTIONS request to the appropriate endpoint
        and apply the appropriate argparse arguments

        :param page: a awxkit.api.pages.page.TentativePage instance
        :param resource: a string containing the resource (e.g., jobs)
        :param parser: an argparse.ArgumentParser object to append new args to
        """
        self.page = page
        self.resource = resource
        self.parser = parser
        self.options = getattr(
            self.page.options().json, 'actions', {'GET': {}}
        )
        if self.resource != 'settings':
            # /api/v2/settings is a special resource that doesn't have
            # traditional list/detail endpoints
            self.build_list_actions()
            self.build_detail_actions()

        self.handle_custom_actions()

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
        for method in ('get', 'modify', 'delete'):
            parser = self.parser.add_parser(method, help='')
            self.parser.choices[method].add_argument('id', type=int, help='')
            if method == 'get':
                add_output_formatting_arguments(parser, {})

    def build_query_arguments(self, method, http_method):
        for k, param in self.options.get(http_method, {}).items():
            required = (
                method == 'create' and
                param.get('required', False) is True
            )
            help_text = param.get('help_text', '')
            if required:
                help_text = '[REQUIRED] {}'.format(help_text)

            if method == 'list':
                help_text = 'only list {} with the specified {}'.format(
                    self.resource,
                    k
                )

            if method == 'list' and param.get('filterable') is False:
                continue

            kwargs = {
                'help': help_text,
                'type': {
                    'string': str,
                    'field': int,
                    'integer': int,
                    'boolean': strtobool,
                }.get(param['type'], str),
            }
            meta_map = {
                'string': 'TEXT',
                'integer': 'INTEGER',
                'boolean': 'BOOLEAN',
            }
            if param.get('choices', []):
                kwargs['choices'] = [c[0] for c in param['choices']]
                # if there are choices, try to guess at the type (we can't
                # just assume it's a list of str, but the API doesn't actually
                # explicitly tell us in OPTIONS all the time)
                if isinstance(kwargs['choices'][0], int):
                    kwargs['type'] = int
                kwargs['choices'] = [str(choice) for choice in kwargs['choices']]
            elif param['type'] in meta_map:
                if required:
                    kwargs['metavar'] = ' '.join([k, meta_map[param['type']]])
                else:
                    kwargs['metavar'] = meta_map[param['type']]

            self.parser.choices[method].add_argument(
                k if required else '--{}'.format(k),
                **kwargs
            )

    def handle_custom_actions(self):
        for _, action in CustomAction.registry.items():
            if action.resource != self.resource:
                continue
            if action.action not in self.parser.choices:
                self.parser.add_parser(action.action, help='')
            action(self.page).add_arguments(self.parser)
