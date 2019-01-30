import pytest

from awx.api.versioning import reverse


@pytest.mark.django_db
def test_create_credential_input_source(get, post, admin, vault_credential, external_credential):
    list_url = reverse(
        'api:credential_input_source_list',
        kwargs={'version': 'v2'}
    )
    sublist_url = reverse(
        'api:credential_input_source_sublist',
        kwargs={'version': 'v2', 'pk': vault_credential.pk}
    )
    params = {
        'source_credential': external_credential.pk,
        'target_credential': vault_credential.pk,
        'input_field_name': 'vault_password'
    }
    response = post(list_url, params, admin)
    assert response.status_code == 201

    response = get(response.data['url'], admin)
    assert response.status_code == 200

    response = get(list_url, admin)
    assert response.status_code == 200
    assert response.data['count'] == 1

    response = get(sublist_url, admin)
    assert response.status_code == 200
    assert response.data['count'] == 1


@pytest.mark.django_db
def test_create_credential_input_source_using_sublist_returns_405(post, admin, vault_credential, external_credential):
    sublist_url = reverse(
        'api:credential_input_source_sublist',
        kwargs={'version': 'v2', 'pk': vault_credential.pk}
    )
    params = {
        'source_credential': external_credential.pk,
        'target_credential': vault_credential.pk,
        'input_field_name': 'vault_password'
    }
    response = post(sublist_url, params, admin)
    assert response.status_code == 405


@pytest.mark.django_db
def test_create_credential_input_source_with_external_target_returns_400(post, admin, external_credential, other_external_credential):
    list_url = reverse(
        'api:credential_input_source_list',
        kwargs={'version': 'v2'}
    )
    params = {
        'source_credential': external_credential.pk,
        'target_credential': other_external_credential.pk,
        'input_field_name': 'token'
    }
    response = post(list_url, params, admin)
    assert response.status_code == 400
    assert response.data['target_credential'] == ['Target must be a non-external credential']


@pytest.mark.django_db
def test_create_credential_input_source_with_non_external_source_returns_400(post, admin, credential, vault_credential):
    list_url = reverse(
        'api:credential_input_source_list',
        kwargs={'version': 'v2'}
    )
    params = {
        'source_credential': credential.pk,
        'target_credential': vault_credential.pk,
        'input_field_name': 'vault_password'
    }
    response = post(list_url, params, admin)
    assert response.status_code == 400
    assert response.data['source_credential'] == ['Source must be an external credential']


@pytest.mark.django_db
def test_create_credential_input_source_with_undefined_input_returns_400(post, admin, vault_credential, external_credential):
    list_url = reverse(
        'api:credential_input_source_list',
        kwargs={'version': 'v2'}
    )
    params = {
        'source_credential': external_credential.pk,
        'target_credential': vault_credential.pk,
        'input_field_name': 'not_defined_for_credential_type'
    }
    response = post(list_url, params, admin)
    assert response.status_code == 400
    assert response.data['input_field_name'] == ['Input field must be defined on target credential.']


@pytest.mark.django_db
def test_create_credential_input_source_with_already_used_input_returns_400(post, admin, vault_credential, external_credential, other_external_credential):
    list_url = reverse(
        'api:credential_input_source_list',
        kwargs={'version': 'v2'}
    )
    all_params = [{
        'source_credential': external_credential.pk,
        'target_credential': vault_credential.pk,
        'input_field_name': 'vault_password'
    }, {
        'source_credential': other_external_credential.pk,
        'target_credential': vault_credential.pk,
        'input_field_name': 'vault_password'
    }]
    all_responses = [post(list_url, params, admin) for params in all_params]
    assert all_responses.pop().status_code == 400
