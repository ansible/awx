import json

import pytest

from awx.main.models.credential import CredentialType, Credential
from awx.api.versioning import reverse


@pytest.mark.django_db
def test_list_as_unauthorized_xfail(get):
    response = get(reverse('api:credential_type_list'))
    assert response.status_code == 401


@pytest.mark.django_db
def test_list_as_normal_user(get, alice):
    response = get(reverse('api:credential_type_list'), alice)
    assert response.status_code == 200
    assert response.data['count'] == 0


@pytest.mark.django_db
def test_list_as_admin(get, admin):
    response = get(reverse('api:credential_type_list'), admin)
    assert response.status_code == 200
    assert response.data['count'] == 0


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
    assert response.status_code == 400
    assert delete(url, admin).status_code == 403


@pytest.mark.django_db
def test_update_credential_type_in_use_xfail(patch, delete, admin):
    ssh = CredentialType.defaults['ssh']()
    ssh.managed_by_tower = False
    ssh.save()
    Credential(credential_type=ssh, name='My SSH Key').save()

    url = reverse('api:credential_type_detail', kwargs={'pk': ssh.pk})
    response = patch(url, {'name': 'Some Other Name'}, admin)
    assert response.status_code == 200

    url = reverse('api:credential_type_detail', kwargs={'pk': ssh.pk})
    response = patch(url, {'inputs': {}}, admin)
    assert response.status_code == 400

    assert delete(url, admin).status_code == 403


@pytest.mark.django_db
def test_update_credential_type_success(get, patch, delete, admin):
    ssh = CredentialType.defaults['ssh']()
    ssh.managed_by_tower = False
    ssh.save()

    url = reverse('api:credential_type_detail', kwargs={'pk': ssh.pk})
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
def test_create_with_invalid_inputs_xfail(post, admin):
    response = post(reverse('api:credential_type_list'), {
        'kind': 'cloud',
        'name': 'MyCloud',
        'inputs': {'feeelds': {},},
        'injectors': {}
    }, admin)
    assert response.status_code == 400
    assert "'feeelds' was unexpected" in json.dumps(response.data)


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
                'ANSIBLE_MY_CLOUD_TOKEN': '{{api_token}}'
            }
        }
    }, admin)
    assert response.status_code == 201

    response = get(reverse('api:credential_type_list'), admin)
    assert response.data['count'] == 1
    injectors = response.data['results'][0]['injectors']
    assert len(injectors) == 1
    assert injectors['env'] == {
        'ANSIBLE_MY_CLOUD_TOKEN': '{{api_token}}'
    }


@pytest.mark.django_db
def test_create_with_invalid_injectors_xfail(post, admin):
    response = post(reverse('api:credential_type_list'), {
        'kind': 'cloud',
        'name': 'MyCloud',
        'inputs': {},
        'injectors': {'nonsense': 123}
    }, admin)
    assert response.status_code == 400


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
            'env': {'ANSIBLE_MY_CLOUD_TOKEN': '{{api_tolkien}}'}
        }
    }, admin)
    assert response.status_code == 400
    assert "'api_tolkien' is undefined" in json.dumps(response.data)
