import json

import yaml

from awxkit.api.pages import Page
from awxkit.api.pages.users import Users, User
from awxkit.cli.format import format_response


def test_json_empty_list():
    page = Page.from_json({
        'results': []
    })
    formatted = format_response(page)
    assert json.loads(formatted) == {'results': []}

def test_yaml_empty_list():
    page = Page.from_json({
        'results': []
    })
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
