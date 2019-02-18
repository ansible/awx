import pytest

from awx.main.models import CredentialInputSource
from awx.api.versioning import reverse


@pytest.mark.django_db
def test_associate_credential_input_source(get, post, admin, vault_credential, external_credential):
    sublist_url = reverse(
        'api:credential_input_source_sublist',
        kwargs={'version': 'v2', 'pk': vault_credential.pk}
    )

    # attach
    params = {
        'source_credential': external_credential.pk,
        'input_field_name': 'vault_password',
        'associate': True
    }
    response = post(sublist_url, params, admin)
    assert response.status_code == 201

    detail = get(response.data['url'], admin)
    assert detail.status_code == 200

    response = get(sublist_url, admin)
    assert response.status_code == 200
    assert response.data['count'] == 1
    assert get(reverse(
        'api:credential_input_source_list',
        kwargs={'version': 'v2'}
    ), admin).data['count'] == 1
    assert CredentialInputSource.objects.count() == 1

    # detach
    params = {
        'id': detail.data['id'],
        'disassociate': True
    }
    response = post(sublist_url, params, admin)
    assert response.status_code == 204

    response = get(sublist_url, admin)
    assert response.status_code == 200
    assert response.data['count'] == 0
    assert get(reverse(
        'api:credential_input_source_list',
        kwargs={'version': 'v2'}
    ), admin).data['count'] == 0
    assert CredentialInputSource.objects.count() == 0


@pytest.mark.django_db
def test_cannot_create_from_list(get, post, admin, vault_credential, external_credential):
    params = {
        'source_credential': external_credential.pk,
        'target_credential': vault_credential.pk,
        'input_field_name': 'vault_password',
    }
    assert post(reverse(
        'api:credential_input_source_list',
        kwargs={'version': 'v2'}
    ), params, admin).status_code == 405


@pytest.mark.django_db
def test_create_credential_input_source_with_external_target_returns_400(post, admin, external_credential, other_external_credential):
    sublist_url = reverse(
        'api:credential_input_source_sublist',
        kwargs={'version': 'v2', 'pk': other_external_credential.pk}
    )
    params = {
        'source_credential': external_credential.pk,
        'input_field_name': 'token',
        'associate': True,
    }
    response = post(sublist_url, params, admin)
    assert response.status_code == 400
    assert response.data['target_credential'] == ['Target must be a non-external credential']


@pytest.mark.django_db
def test_create_credential_input_source_with_non_external_source_returns_400(post, admin, credential, vault_credential):
    sublist_url = reverse(
        'api:credential_input_source_sublist',
        kwargs={'version': 'v2', 'pk': vault_credential.pk}
    )
    params = {
        'source_credential': credential.pk,
        'input_field_name': 'vault_password'
    }
    response = post(sublist_url, params, admin)
    assert response.status_code == 400
    assert response.data['source_credential'] == ['Source must be an external credential']


@pytest.mark.django_db
def test_create_credential_input_source_with_undefined_input_returns_400(post, admin, vault_credential, external_credential):
    sublist_url = reverse(
        'api:credential_input_source_sublist',
        kwargs={'version': 'v2', 'pk': vault_credential.pk}
    )
    params = {
        'source_credential': external_credential.pk,
        'input_field_name': 'not_defined_for_credential_type'
    }
    response = post(sublist_url, params, admin)
    assert response.status_code == 400
    assert response.data['input_field_name'] == ['Input field must be defined on target credential.']


@pytest.mark.django_db
def test_create_credential_input_source_with_already_used_input_returns_400(post, admin, vault_credential, external_credential, other_external_credential):
    sublist_url = reverse(
        'api:credential_input_source_sublist',
        kwargs={'version': 'v2', 'pk': vault_credential.pk}
    )
    all_params = [{
        'source_credential': external_credential.pk,
        'input_field_name': 'vault_password'
    }, {
        'source_credential': other_external_credential.pk,
        'input_field_name': 'vault_password'
    }]
    all_responses = [post(sublist_url, params, admin) for params in all_params]
    assert all_responses.pop().status_code == 400
