from __future__ import absolute_import, division, print_function

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
    }

    result = run_module('tower_organization', module_args, admin_user)
    assert result.get('changed'), result

    org = Organization.objects.get(name='foo')
    assert result == {"name": "foo", "changed": True, "id": org.id, "invocation": {"module_args": module_args}}

    assert org.description == 'barfoo'
