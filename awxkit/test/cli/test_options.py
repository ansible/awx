import argparse
import unittest
from io import StringIO

from awxkit.api.pages import Page
from awxkit.cli.options import ResourceOptionsParser


class ResourceOptionsParser(ResourceOptionsParser):
    def get_allowed_options(self):
        self.allowed_options = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']


class OptionsPage(Page):
    def options(self):
        return self

    def endswith(self, v):
        return self.endpoint.endswith(v)

    def __getitem__(self, k):
        return {
            'GET': {},
            'POST': {},
            'PUT': {},
        }


class TestOptions(unittest.TestCase):
    def setUp(self):
        _parser = argparse.ArgumentParser()
        self.parser = _parser.add_subparsers(help='action')

    def test_list(self):
        page = OptionsPage.from_json(
            {
                'actions': {
                    'GET': {},
                    'POST': {},
                }
            }
        )
        ResourceOptionsParser(None, page, 'users', self.parser)
        assert 'list' in self.parser.choices

    def test_list_filtering(self):
        page = OptionsPage.from_json(
            {
                'actions': {
                    'GET': {},
                    'POST': {'first_name': {'type': 'string'}},
                }
            }
        )
        options = ResourceOptionsParser(None, page, 'users', self.parser)
        options.build_query_arguments('list', 'POST')
        assert 'list' in self.parser.choices

        out = StringIO()
        self.parser.choices['list'].print_help(out)
        assert '--first_name TEXT' in out.getvalue()

    def test_list_not_filterable(self):
        page = OptionsPage.from_json(
            {
                'actions': {
                    'GET': {},
                    'POST': {'middle_name': {'type': 'string', 'filterable': False}},
                }
            }
        )
        options = ResourceOptionsParser(None, page, 'users', self.parser)
        options.build_query_arguments('list', 'POST')
        assert 'list' in self.parser.choices

        out = StringIO()
        self.parser.choices['list'].print_help(out)
        assert '--middle_name' not in out.getvalue()

    def test_creation_optional_argument(self):
        page = OptionsPage.from_json(
            {
                'actions': {
                    'POST': {
                        'first_name': {
                            'type': 'string',
                            'help_text': 'Please specify your first name',
                        }
                    },
                }
            }
        )
        options = ResourceOptionsParser(None, page, 'users', self.parser)
        options.build_query_arguments('create', 'POST')
        assert 'create' in self.parser.choices

        out = StringIO()
        self.parser.choices['create'].print_help(out)
        assert '--first_name TEXT  Please specify your first name' in out.getvalue()

    def test_creation_required_argument(self):
        page = OptionsPage.from_json(
            {
                'actions': {
                    'POST': {'username': {'type': 'string', 'help_text': 'Please specify a username', 'required': True}},
                }
            }
        )
        options = ResourceOptionsParser(None, page, 'users', self.parser)
        options.build_query_arguments('create', 'POST')
        assert 'create' in self.parser.choices

        out = StringIO()
        self.parser.choices['create'].print_help(out)
        assert '--username TEXT  Please specify a username'

    def test_integer_argument(self):
        page = OptionsPage.from_json(
            {
                'actions': {
                    'POST': {'max_hosts': {'type': 'integer'}},
                }
            }
        )
        options = ResourceOptionsParser(None, page, 'organizations', self.parser)
        options.build_query_arguments('create', 'POST')
        assert 'create' in self.parser.choices

        out = StringIO()
        self.parser.choices['create'].print_help(out)
        assert '--max_hosts INTEGER' in out.getvalue()

    def test_boolean_argument(self):
        page = OptionsPage.from_json(
            {
                'actions': {
                    'POST': {'diff_mode': {'type': 'boolean'}},
                }
            }
        )
        options = ResourceOptionsParser(None, page, 'users', self.parser)
        options.build_query_arguments('create', 'POST')
        assert 'create' in self.parser.choices

        out = StringIO()
        self.parser.choices['create'].print_help(out)
        assert '--diff_mode BOOLEAN' in out.getvalue()

    def test_choices(self):
        page = OptionsPage.from_json(
            {
                'actions': {
                    'POST': {
                        'verbosity': {
                            'type': 'integer',
                            'choices': [
                                (0, '0 (Normal)'),
                                (1, '1 (Verbose)'),
                                (2, '2 (More Verbose)'),
                                (3, '3 (Debug)'),
                                (4, '4 (Connection Debug)'),
                                (5, '5 (WinRM Debug)'),
                            ],
                        }
                    },
                }
            }
        )
        options = ResourceOptionsParser(None, page, 'users', self.parser)
        options.build_query_arguments('create', 'POST')
        assert 'create' in self.parser.choices

        out = StringIO()
        self.parser.choices['create'].print_help(out)
        assert '--verbosity {0,1,2,3,4,5}' in out.getvalue()

    def test_actions_with_primary_key(self):
        for method in ('get', 'modify', 'delete'):
            page = OptionsPage.from_json({'actions': {'GET': {}, 'POST': {}}})
            ResourceOptionsParser(None, page, 'jobs', self.parser)
            assert method in self.parser.choices

            out = StringIO()
            self.parser.choices[method].print_help(out)
            assert 'positional arguments:\n  id' in out.getvalue()


class TestSettingsOptions(unittest.TestCase):
    def setUp(self):
        _parser = argparse.ArgumentParser()
        self.parser = _parser.add_subparsers(help='action')

    def test_list(self):
        page = OptionsPage.from_json(
            {
                'actions': {
                    'GET': {},
                    'POST': {},
                    'PUT': {},
                }
            }
        )
        page.endpoint = '/settings/all/'
        ResourceOptionsParser(None, page, 'settings', self.parser)
        assert 'list' in self.parser.choices
        assert 'modify' in self.parser.choices

        out = StringIO()
        self.parser.choices['modify'].print_help(out)
        assert 'modify [-h] key value' in out.getvalue()
