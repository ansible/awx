import argparse
import unittest
from io import StringIO

from awxkit.api.pages import Page
from awxkit.cli.options import ResourceOptionsParser


class ResourceOptionsParser(ResourceOptionsParser):
    # Bypass the live detail-endpoint OPTIONS call and the CustomAction
    # registry (which would otherwise wire up the real JobTemplateLaunch
    # action and make a live HTTP call), matching the override pattern
    # used in test_options.py.

    def get_allowed_options(self):
        self.allowed_options = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']

    def handle_custom_actions(self):
        pass


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


class TestJobTemplateLaunchFieldAssignment(unittest.TestCase):

    def setUp(self):
        top_parser = argparse.ArgumentParser()
        self.parser = top_parser.add_subparsers(help='action')
        page = OptionsPage.from_json({'actions': {'GET': {}, 'POST': {}}})
        self.options = ResourceOptionsParser(None, page, 'job_templates', self.parser)
        self.parser.add_parser('launch', help='', add_help=True)

    def _launch_args(self, *args):
        return self.parser.choices['launch'].parse_args(list(args))

    def test_assigning_credentials_to_a_job_template_at_launch(self):
        self.options.options['LAUNCH'] = {'credentials': {'type': 'list_of_ids'}}
        self.options.build_query_arguments('launch', 'LAUNCH')
        args = self._launch_args('--credentials', '1,2,3')
        assert args.credentials == [1, 2, 3]

    def test_assigning_instance_groups_to_a_job_template_at_launch(self):
        self.options.options['LAUNCH'] = {'instance_groups': {'type': 'list_of_ids'}}
        self.options.build_query_arguments('launch', 'LAUNCH')
        args = self._launch_args('--instance_groups', '4,5')
        assert args.instance_groups == [4, 5]

    def test_instance_groups_and_credentials_build_identical_argument_shapes(self):
        self.options.options['LAUNCH'] = {
            'credentials': {'type': 'list_of_ids'},
            'instance_groups': {'type': 'list_of_ids'},
        }
        self.options.build_query_arguments('launch', 'LAUNCH')
        out = StringIO()
        self.parser.choices['launch'].print_help(out)
        help_text = out.getvalue()
        assert '--credentials [ID, ID, ...]' in help_text
        assert '--instance_groups [ID, ID, ...]' in help_text
