import json

import pytest

from awx.main.models.credential import CredentialType, Credential
from awx.api.versioning import reverse


@pytest.mark.django_db
def test_list_as_unauthorized_xfail(get):
    response = get(reverse('api:credential_type_list'))
    assert response.status_code == 401


@pytest.mark.django_db
@pytest.mark.parametrize('method, valid', [
    ('GET', sorted(dict(CredentialType.KIND_CHOICES).keys())),
    ('POST', ['cloud', 'net']),
])
def test_options_valid_kinds(method, valid, options, admin):
    response = options(reverse('api:credential_type_list'), admin)
    choices = sorted(dict(response.data['actions'][method]['kind']['choices']).keys())
    assert valid == choices


@pytest.mark.django_db
def test_options_valid_put_kinds(options, admin):
    ssh = CredentialType.defaults['ssh']()
    ssh.save()
    response = options(reverse('api:credential_type_detail', kwargs={'pk': ssh.pk}), admin)
    choices = sorted(dict(response.data['actions']['PUT']['kind']['choices']).keys())
    assert ['cloud', 'net'] == choices


@pytest.mark.django_db
def test_list_as_normal_user(get, alice):
    ssh = CredentialType.defaults['ssh']()
    ssh.save()
    response = get(reverse('api:credential_type_list'), alice)
    assert response.status_code == 200
    assert response.data['count'] == 1


@pytest.mark.django_db
def test_list_as_admin(get, admin):
    ssh = CredentialType.defaults['ssh']()
    ssh.save()
    response = get(reverse('api:credential_type_list'), admin)
    assert response.status_code == 200
    assert response.data['count'] == 1


@pytest.mark.django_db
def test_create_as_unauthorized_xfail(get, post):
    response = post(reverse('api:credential_type_list'), {
        'name': 'Custom Credential Type',
    })
    assert response.status_code == 401


@pytest.mark.django_db
def test_update_as_unauthorized_xfail(patch, delete):
    ssh = CredentialType.defaults['ssh']()
    ssh.save()
    url = reverse('api:credential_type_detail', kwargs={'pk': ssh.pk})
    response = patch(url, {'name': 'Some Other Name'})
    assert response.status_code == 401
    assert delete(url).status_code == 401


@pytest.mark.django_db
def test_update_managed_by_tower_xfail(patch, delete, admin):
    ssh = CredentialType.defaults['ssh']()
    ssh.save()
    url = reverse('api:credential_type_detail', kwargs={'pk': ssh.pk})
    response = patch(url, {'name': 'Some Other Name'}, admin)
    assert response.status_code == 403
    assert delete(url, admin).status_code == 403


@pytest.mark.django_db
def test_update_credential_type_in_use_xfail(patch, delete, admin):
    _type = CredentialType(kind='cloud', inputs={'fields': []})
    _type.save()
    Credential(credential_type=_type, name='My Custom Cred').save()

    url = reverse('api:credential_type_detail', kwargs={'pk': _type.pk})
    patch(url, {'name': 'Some Other Name'}, admin, expect=200)

    url = reverse('api:credential_type_detail', kwargs={'pk': _type.pk})
    response = patch(url, {'inputs': {}}, admin, expect=403)
    assert response.data['detail'] == 'Modifications to inputs are not allowed for credential types that are in use'

    response = delete(url, admin, expect=403)
    assert response.data['detail'] == 'Credential types that are in use cannot be deleted'


@pytest.mark.django_db
def test_update_credential_type_unvalidated_inputs(post, patch, admin):
    simple_inputs = {'fields': [
        {'id': 'api_token', 'label': 'fooo'}
    ]}
    response = post(
        url=reverse('api:credential_type_list'),
        data={'name': 'foo', 'kind': 'cloud', 'inputs': simple_inputs},
        user=admin,
        expect=201
    )
    # validation adds the type field to the input
    _type = CredentialType.objects.get(pk=response.data['id'])
    Credential(credential_type=_type, name='My Custom Cred').save()

    # should not raise an error because we should only compare
    # post-validation values to other post-validation values
    url = reverse('api:credential_type_detail', kwargs={'pk': _type.id})
    patch(url, {'inputs': simple_inputs}, admin, expect=200)


@pytest.mark.django_db
def test_update_credential_type_success(get, patch, delete, admin):
    _type = CredentialType(kind='cloud')
    _type.save()

    url = reverse('api:credential_type_detail', kwargs={'pk': _type.pk})
    response = patch(url, {'name': 'Some Other Name'}, admin)
    assert response.status_code == 200

    assert get(url, admin).data.get('name') == 'Some Other Name'
    assert delete(url, admin).status_code == 204


@pytest.mark.django_db
def test_delete_as_unauthorized_xfail(delete):
    ssh = CredentialType.defaults['ssh']()
    ssh.save()
    response = delete(
        reverse('api:credential_type_detail', kwargs={'pk': ssh.pk}),
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_create_as_normal_user_xfail(get, post, alice):
    response = post(reverse('api:credential_type_list'), {
        'name': 'Custom Credential Type',
    }, alice)
    assert response.status_code == 403
    assert get(reverse('api:credential_type_list'), alice).data['count'] == 0


@pytest.mark.django_db
def test_create_as_admin(get, post, admin):
    response = post(reverse('api:credential_type_list'), {
        'kind': 'cloud',
        'name': 'Custom Credential Type',
        'inputs': {},
        'injectors': {}
    }, admin)
    assert response.status_code == 201

    response = get(reverse('api:credential_type_list'), admin)
    assert response.data['count'] == 1
    assert response.data['results'][0]['name'] == 'Custom Credential Type'
    assert response.data['results'][0]['inputs'] == {}
    assert response.data['results'][0]['injectors'] == {}
    assert response.data['results'][0]['managed_by_tower'] is False


@pytest.mark.django_db
def test_create_managed_by_tower_readonly(get, post, admin):
    response = post(reverse('api:credential_type_list'), {
        'kind': 'cloud',
        'name': 'Custom Credential Type',
        'inputs': {},
        'injectors': {},
        'managed_by_tower': True
    }, admin)
    assert response.status_code == 201

    response = get(reverse('api:credential_type_list'), admin)
    assert response.data['count'] == 1
    assert response.data['results'][0]['managed_by_tower'] is False


@pytest.mark.django_db
def test_create_dependencies_not_supported(get, post, admin):
    response = post(reverse('api:credential_type_list'), {
        'kind': 'cloud',
        'name': 'Custom Credential Type',
        'inputs': {'dependencies': {'foo': ['bar']}},
        'injectors': {},
    }, admin)
    assert response.status_code == 400
    assert response.data['inputs'] == ["'dependencies' is not supported for custom credentials."]

    response = get(reverse('api:credential_type_list'), admin)
    assert response.data['count'] == 0


@pytest.mark.django_db
@pytest.mark.parametrize('kind', ['cloud', 'net'])
def test_create_valid_kind(kind, get, post, admin):
    response = post(reverse('api:credential_type_list'), {
        'kind': kind,
        'name': 'My Custom Type',
        'inputs': {
            'fields': [{
                'id': 'api_token',
                'label': 'API Token',
                'type': 'string',
                'secret': True
            }]
        },
        'injectors': {}
    }, admin)
    assert response.status_code == 201

    response = get(reverse('api:credential_type_list'), admin)
    assert response.data['count'] == 1


@pytest.mark.django_db
@pytest.mark.parametrize('kind', ['ssh', 'vault', 'scm', 'insights', 'kubernetes', 'galaxy'])
def test_create_invalid_kind(kind, get, post, admin):
    response = post(reverse('api:credential_type_list'), {
        'kind': kind,
        'name': 'My Custom Type',
        'inputs': {
            'fields': [{
                'id': 'api_token',
                'label': 'API Token',
                'type': 'string',
                'secret': True
            }]
        },
        'injectors': {}
    }, admin)
    assert response.status_code == 400

    response = get(reverse('api:credential_type_list'), admin)
    assert response.data['count'] == 0


@pytest.mark.django_db
def test_create_with_valid_inputs(get, post, admin):
    response = post(reverse('api:credential_type_list'), {
        'kind': 'cloud',
        'name': 'MyCloud',
        'inputs': {
            'fields': [{
                'id': 'api_token',
                'label': 'API Token',
                'type': 'string',
                'secret': True
            }]
        },
        'injectors': {}
    }, admin)
    assert response.status_code == 201

    response = get(reverse('api:credential_type_list'), admin)
    assert response.data['count'] == 1
    fields = response.data['results'][0]['inputs']['fields']
    assert len(fields) == 1
    assert fields[0]['id'] == 'api_token'
    assert fields[0]['label'] == 'API Token'
    assert fields[0]['secret'] is True
    assert fields[0]['type'] == 'string'


@pytest.mark.django_db
def test_create_with_required_inputs(get, post, admin):
    response = post(reverse('api:credential_type_list'), {
        'kind': 'cloud',
        'name': 'MyCloud',
        'inputs': {
            'fields': [{
                'id': 'api_token',
                'label': 'API Token',
                'type': 'string',
                'secret': True
            }],
            'required': ['api_token'],
        },
        'injectors': {}
    }, admin)
    assert response.status_code == 201

    response = get(reverse('api:credential_type_list'), admin)
    assert response.data['count'] == 1
    required = response.data['results'][0]['inputs']['required']
    assert required == ['api_token']


@pytest.mark.django_db
@pytest.mark.parametrize('default, status_code', [
    ['some default string', 201],
    [None, 400],
    [True, 400],
    [False, 400],
])
@pytest.mark.parametrize('secret', [True, False])
def test_create_with_default_string(get, post, admin, default, status_code, secret):
    response = post(reverse('api:credential_type_list'), {
        'kind': 'cloud',
        'name': 'MyCloud',
        'inputs': {
            'fields': [{
                'id': 'api_token',
                'label': 'API Token',
                'type': 'string',
                'secret': secret,
                'default': default,
            }],
            'required': ['api_token'],
        },
        'injectors': {}
    }, admin)
    assert response.status_code == status_code
    if status_code == 201:
        cred = Credential(
            credential_type=CredentialType.objects.get(pk=response.data['id']),
            name='My Custom Cred'
        )
        assert cred.get_input('api_token') == default
    elif status_code == 400:
        assert "{} is not a string".format(default) in json.dumps(response.data)


@pytest.mark.django_db
@pytest.mark.parametrize('default, status_code', [
    ['some default string', 400],
    [None, 400],
    [True, 201],
    [False, 201],
])
def test_create_with_default_bool(get, post, admin, default, status_code):
    response = post(reverse('api:credential_type_list'), {
        'kind': 'cloud',
        'name': 'MyCloud',
        'inputs': {
            'fields': [{
                'id': 'api_token',
                'label': 'API Token',
                'type': 'boolean',
                'default': default,
            }],
            'required': ['api_token'],
        },
        'injectors': {}
    }, admin)
    assert response.status_code == status_code
    if status_code == 201:
        cred = Credential(
            credential_type=CredentialType.objects.get(pk=response.data['id']),
            name='My Custom Cred'
        )
        assert cred.get_input('api_token') == default
    elif status_code == 400:
        assert "{} is not a boolean".format(default) in json.dumps(response.data)


@pytest.mark.django_db
@pytest.mark.parametrize('inputs', [
    True,
    100,
    [1, 2, 3, 4],
    'malformed',
    {'feelds': {}},
    {'fields': [123, 234, 345]},
    {'fields': [{'id':'one', 'label':'One'}, 234]},
    {'feelds': {}, 'fields': [{'id':'one', 'label':'One'}, 234]}
])
def test_create_with_invalid_inputs_xfail(post, admin, inputs):
    response = post(reverse('api:credential_type_list'), {
        'kind': 'cloud',
        'name': 'MyCloud',
        'inputs': inputs,
        'injectors': {}
    }, admin)
    assert response.status_code == 400


@pytest.mark.django_db
@pytest.mark.parametrize('injectors', [
    True,
    100,
    [1, 2, 3, 4],
    'malformed',
    {'mal': 'formed'},
    {'env': {'ENV_VAR': 123}, 'mal': 'formed'},
    {'env': True},
    {'env': [1, 2, 3]},
    {'file': True},
    {'file': [1, 2, 3]},
    {'extra_vars': True},
    {'extra_vars': [1, 2, 3]},
])
def test_create_with_invalid_injectors_xfail(post, admin, injectors):
    response = post(reverse('api:credential_type_list'), {
        'kind': 'cloud',
        'name': 'MyCloud',
        'inputs': {},
        'injectors': injectors,
    }, admin)
    assert response.status_code == 400


@pytest.mark.django_db
def test_ask_at_runtime_xfail(get, post, admin):
    # ask_at_runtime is only supported by the built-in SSH and Vault types
    response = post(reverse('api:credential_type_list'), {
        'kind': 'cloud',
        'name': 'MyCloud',
        'inputs': {
            'fields': [{
                'id': 'api_token',
                'label': 'API Token',
                'type': 'string',
                'secret': True,
                'ask_at_runtime': True
            }]
        },
        'injectors': {
            'env': {
                'ANSIBLE_MY_CLOUD_TOKEN': '{{api_token}}'
            }
        }
    }, admin)
    assert response.status_code == 400

    response = get(reverse('api:credential_type_list'), admin)
    assert response.data['count'] == 0


@pytest.mark.django_db
def test_create_with_valid_injectors(get, post, admin):
    response = post(reverse('api:credential_type_list'), {
        'kind': 'cloud',
        'name': 'MyCloud',
        'inputs': {
            'fields': [{
                'id': 'api_token',
                'label': 'API Token',
                'type': 'string',
                'secret': True
            }]
        },
        'injectors': {
            'env': {
                'AWX_MY_CLOUD_TOKEN': '{{api_token}}'
            }
        }
    }, admin, expect=201)

    response = get(reverse('api:credential_type_list'), admin)
    assert response.data['count'] == 1
    injectors = response.data['results'][0]['injectors']
    assert len(injectors) == 1
    assert injectors['env'] == {
        'AWX_MY_CLOUD_TOKEN': '{{api_token}}'
    }


@pytest.mark.django_db
def test_create_with_undefined_template_variable_xfail(post, admin):
    response = post(reverse('api:credential_type_list'), {
        'kind': 'cloud',
        'name': 'MyCloud',
        'inputs': {
            'fields': [{
                'id': 'api_token',
                'label': 'API Token',
                'type': 'string',
                'secret': True
            }]
        },
        'injectors': {
            'env': {'AWX_MY_CLOUD_TOKEN': '{{api_tolkien}}'}
        }
    }, admin)
    assert response.status_code == 400
    assert "'api_tolkien' is undefined" in json.dumps(response.data)


@pytest.mark.django_db
def test_credential_type_rbac_external_test(post, alice, admin, credentialtype_external):
    # only admins may use the credential type test endpoint
    url = reverse('api:credential_type_external_test', kwargs={'pk': credentialtype_external.pk})
    data = {'inputs': {}, 'metadata': {}}
    assert post(url, data, admin).status_code == 202
    assert post(url, data, alice).status_code == 403
