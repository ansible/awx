from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from awx.main.models import OAuth2AccessToken


@pytest.mark.django_db
def test_create_token(run_module, admin_user):

    module_args = {
        'description': 'barfoo',
        'state': 'present',
        'scope': 'read',
        'tower_host': None,
        'tower_username': None,
        'tower_password': None,
        'validate_certs': None,
        'tower_oauthtoken': None,
        'tower_config_file': None,
    }

    result = run_module('tower_token', module_args, admin_user)
    assert result.get('changed'), result

    tokens = OAuth2AccessToken.objects.filter(description='barfoo')
    assert len(tokens) == 1, 'Tokens with description of barfoo != 0: {0}'.format(len(tokens))
    assert tokens[0].scope == 'read', 'Token was not given read access'
