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
        'controller_host': None,
        'controller_username': None,
        'controller_password': None,
        'validate_certs': None,
        'controller_oauthtoken': None,
        'controller_config_file': None,
    }

    result = run_module('organization', module_args, admin_user)
    assert result.get('changed'), result

    org = Organization.objects.get(name='foo')
    assert result == {"name": "foo", "changed": True, "id": org.id, "invocation": {"module_args": module_args}}

    assert org.description == 'barfoo'
