import pytest

from awx.main.models import Credential, CredentialType, Organization


@pytest.mark.django_db
def test_create_machine_credential(run_module, admin_user):
    Organization.objects.create(name='test-org')
    # create the ssh credential type
    CredentialType.defaults['ssh']().save()
    # Example from docs
    result = run_module('tower_credential', dict(
        name='Team Name',
        description='Team Description',
        organization='test-org',
        kind='ssh',
        state='present'
    ), admin_user)

    cred = Credential.objects.get(name='Team Name')
    result.pop('invocation')
    assert result == {
        "credential": "Team Name",
        "state": "present",
        "id": cred.pk,
        "changed": True
    }


@pytest.mark.django_db
def test_create_custom_credential_type(run_module, admin_user):
    # Example from docs
    result = run_module('tower_credential_type', dict(
        name='Nexus',
        description='Credentials type for Nexus',
        kind='cloud',
        inputs={"fields": [{"id": "server", "type": "string", "default": "", "label": ""}], "required": []},
        injectors={'extra_vars': {'nexus_credential': 'test'}},
        state='present',
        validate_certs='false'
    ), admin_user)

    ct = CredentialType.objects.get(name='Nexus')
    result.pop('invocation')
    assert result == {
        "credential_type": "Nexus",
        "state": "present",
        "id": ct.pk,
        "changed": True
    }

    assert ct.inputs == {"fields": [{"id": "server", "type": "string", "default": "", "label": ""}], "required": []}
    assert ct.injectors == {'extra_vars': {'nexus_credential': 'test'}}


@pytest.mark.django_db
def test_kind_ct_exclusivity(run_module, admin_user):
    result = run_module('tower_credential', dict(
        name='A credential',
        organization='test-org',
        kind='ssh',
        credential_type='foobar',  # cannot specify if kind is also specified
        state='present'
    ), admin_user)

    result.pop('invocation')
    assert result == {
        'failed': True,
        'msg': 'parameters are mutually exclusive: kind|credential_type'
    }


@pytest.mark.django_db
def test_input_exclusivity(run_module, admin_user):
    result = run_module('tower_credential', dict(
        name='A credential',
        organization='test-org',
        kind='ssh',
        inputs={'token': '7rEZK38DJl58A7RxA6EC7lLvUHbBQ1'},
        security_token='7rEZK38DJl58A7RxA6EC7lLvUHbBQ1',
        state='present'
    ), admin_user)

    result.pop('invocation')
    assert result == {
        'failed': True,
        'msg': 'parameters are mutually exclusive: inputs|security_token'
    }


@pytest.mark.django_db
def test_missing_credential_type(run_module, admin_user):
    Organization.objects.create(name='test-org')
    result = run_module('tower_credential', dict(
        name='A credential',
        organization='test-org',
        credential_type='foobar',
        state='present'
    ), admin_user)

    result.pop('invocation')
    assert result == {
        "changed": False,
        "failed": True,
        'msg': 'Failed to update credential, credential_type not found: The requested object could not be found.'
    }


@pytest.mark.django_db
def test_make_use_of_custom_credential_type(run_module, admin_user):
    Organization.objects.create(name='test-org')
    # Make a credential type which will be used by the credential
    ct = CredentialType.objects.create(
        name='Ansible Galaxy Token',
        inputs={
            "fields": [
                {
                    "id": "token",
                    "type": "string",
                    "secret": True,
                    "label": "Ansible Galaxy Secret Token Value"
                }
            ],
            "required": ["token"]
        },
        injectors={
            "extra_vars": {
                "galaxy_token": "{{token}}",
            }
        }
    )
    result = run_module('tower_credential', dict(
        name='Galaxy Token for Steve',
        organization='test-org',
        credential_type='Ansible Galaxy Token',
        inputs={'token': '7rEZK38DJl58A7RxA6EC7lLvUHbBQ1'},
        state='present'
    ), admin_user)

    cred = Credential.objects.get(name='Galaxy Token for Steve')
    assert cred.credential_type_id == ct.id
    assert list(cred.inputs.keys()) == ['token']
    assert cred.inputs['token'].startswith('$encrypted$')
    assert len(cred.inputs['token']) >= len('$encrypted$') + len('7rEZK38DJl58A7RxA6EC7lLvUHbBQ1')
    result.pop('invocation')
    assert result == {
        "credential": "Galaxy Token for Steve",
        "state": "present",
        "id": cred.pk,
        "changed": True
    }
