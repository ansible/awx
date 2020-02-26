from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from awx.main.models import Organization


@pytest.mark.django_db
def test_create_organization(run_module, admin_user):

    module_args = {
        'name': 'foo',
        'description': 'barfoo',
        'state': 'present',
        'max_hosts': '0',
        'tower_host': None,
        'tower_username': None,
        'tower_password': None,
        'validate_certs': None,
        'tower_oauthtoken': None,
        'tower_config_file': None,
        'custom_virtualenv': None
    }

    result = run_module('tower_organization', module_args, admin_user)
    assert result.get('changed'), result

    org = Organization.objects.get(name='foo')
    assert result == {
        "name": "foo",
        "changed": True,
        "id": org.id,
        "invocation": {
            "module_args": module_args
        }
    }

    assert org.description == 'barfoo'


@pytest.mark.django_db
def test_create_organization_with_venv(run_module, admin_user, mocker):
    path = '/var/lib/awx/venv/custom-venv/foobar13489435/'
    with mocker.patch('awx.main.models.mixins.get_custom_venv_choices', return_value=[path]):
        result = run_module('tower_organization', {
            'name': 'foo',
            'custom_virtualenv': path,
            'state': 'present'
        }, admin_user)
    assert result.pop('changed'), result

    org = Organization.objects.get(name='foo')
    result.pop('invocation')
    assert result == {
        "name": "foo",
        "id": org.id
    }

    assert org.custom_virtualenv == path
