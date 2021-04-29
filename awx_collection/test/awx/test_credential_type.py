from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from awx.main.models import CredentialType


@pytest.mark.django_db
def test_create_custom_credential_type(run_module, admin_user, silence_deprecation):
    # Example from docs
    result = run_module(
        'credential_type',
        dict(
            name='Nexus',
            description='Credentials type for Nexus',
            kind='cloud',
            inputs={"fields": [{"id": "server", "type": "string", "default": "", "label": ""}], "required": []},
            injectors={'extra_vars': {'nexus_credential': 'test'}},
            state='present',
        ),
        admin_user,
    )
    assert not result.get('failed', False), result.get('msg', result)
    assert result.get('changed'), result

    ct = CredentialType.objects.get(name='Nexus')

    assert result['name'] == 'Nexus'
    assert result['id'] == ct.pk

    assert ct.inputs == {"fields": [{"id": "server", "type": "string", "default": "", "label": ""}], "required": []}
    assert ct.injectors == {'extra_vars': {'nexus_credential': 'test'}}


@pytest.mark.django_db
def test_changed_false_with_api_changes(run_module, admin_user):
    result = run_module(
        'credential_type',
        dict(
            name='foo',
            kind='cloud',
            inputs={"fields": [{"id": "env_value", "label": "foo", "default": "foo"}]},
            injectors={'env': {'TEST_ENV_VAR': '{{ env_value }}'}},
        ),
        admin_user,
    )
    assert not result.get('failed', False), result.get('msg', result)
    assert result.get('changed'), result

    result = run_module(
        'credential_type',
        dict(
            name='foo',
            inputs={"fields": [{"id": "env_value", "label": "foo", "default": "foo"}]},
            injectors={'env': {'TEST_ENV_VAR': '{{ env_value }}'}},
        ),
        admin_user,
    )
    assert not result.get('failed', False), result.get('msg', result)
    assert not result.get('changed'), result
