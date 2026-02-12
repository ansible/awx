import io
import json

import yaml

from awxkit.api.pages import Page
from awxkit.api.pages.users import Users
from awxkit.cli import CLI
from awxkit.cli.format import format_response
from awxkit.cli.resource import Import


def test_json_empty_list():
    page = Page.from_json({'results': []})
    formatted = format_response(page)
    assert json.loads(formatted) == {'results': []}


def test_yaml_empty_list():
    page = Page.from_json({'results': []})
    formatted = format_response(page, fmt='yaml')
    assert yaml.safe_load(formatted) == {'results': []}


def test_json_list():
    users = {
        'results': [
            {'username': 'betty'},
            {'username': 'tom'},
            {'username': 'anne'},
        ]
    }
    page = Users.from_json(users)
    formatted = format_response(page)
    assert json.loads(formatted) == users


def test_yaml_list():
    users = {
        'results': [
            {'username': 'betty'},
            {'username': 'tom'},
            {'username': 'anne'},
        ]
    }
    page = Users.from_json(users)
    formatted = format_response(page, fmt='yaml')
    assert yaml.safe_load(formatted) == users


def test_yaml_import():
    class MockedV2:
        def import_assets(self, data):
            self._parsed_data = data

    def _dummy_authenticate():
        pass

    yaml_fd = io.StringIO(
        """
        workflow_job_templates:
          - name: Workflow1
        """
    )
    yaml_fd.name = 'file.yaml'
    cli = CLI(stdin=yaml_fd)
    cli.parse_args(['--conf.format', 'yaml'])
    cli.v2 = MockedV2()
    cli.authenticate = _dummy_authenticate

    Import().handle(cli, None)
    assert cli.v2._parsed_data['workflow_job_templates'][0]['name']
