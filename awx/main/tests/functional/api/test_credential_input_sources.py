import pytest

from awx.main.models import CredentialInputSource
from awx.api.versioning import reverse


@pytest.mark.django_db
def test_associate_credential_input_source(get, post, delete, admin, vault_credential, external_credential):
    list_url = reverse('api:credential_input_source_list')

    # attach
    params = {
        'target_credential': vault_credential.pk,
        'source_credential': external_credential.pk,
        'input_field_name': 'vault_password',
        'metadata': {'key': 'some_example_key'}
    }
    response = post(list_url, params, admin)
    assert response.status_code == 201

    detail = get(response.data['url'], admin)
    assert detail.status_code == 200

    response = get(list_url, admin)
    assert response.status_code == 200
    assert response.data['count'] == 1
    assert CredentialInputSource.objects.count() == 1
    input_source = CredentialInputSource.objects.first()
    assert input_source.metadata == {'key': 'some_example_key'}

    # detach
    response = delete(
        reverse(
            'api:credential_input_source_detail',
            kwargs={'pk': detail.data['id']}
        ),
        admin
    )
    assert response.status_code == 204

    response = get(list_url, admin)
    assert response.status_code == 200
    assert response.data['count'] == 0
    assert CredentialInputSource.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize('metadata', [
    {},  # key is required
    {'key': None},  # must be a string
    {'key': 123},  # must be a string
    {'extraneous': 'foo'},  # invalid parameter
])
def test_associate_credential_input_source_with_invalid_metadata(get, post, admin, vault_credential, external_credential, metadata):
    list_url = reverse('api:credential_input_source_list')

    params = {
        'target_credential': vault_credential.pk,
        'source_credential': external_credential.pk,
        'input_field_name': 'vault_password',
        'metadata': metadata,
    }
    response = post(list_url, params, admin)
    assert response.status_code == 400
    assert b'metadata' in response.content


@pytest.mark.django_db
def test_create_from_list(get, post, admin, vault_credential, external_credential):
    params = {
        'source_credential': external_credential.pk,
        'target_credential': vault_credential.pk,
        'input_field_name': 'vault_password',
        'metadata': {'key': 'some_example_key'},
    }
    assert post(reverse(
        'api:credential_input_source_list',
    ), params, admin).status_code == 201
    assert CredentialInputSource.objects.count() == 1


@pytest.mark.django_db
def test_create_credential_input_source_with_external_target_returns_400(post, admin, external_credential, other_external_credential):
    list_url = reverse(
        'api:credential_input_source_list',
    )
    params = {
        'target_credential': other_external_credential.pk,
        'source_credential': external_credential.pk,
        'input_field_name': 'token',
        'metadata': {'key': 'some_key'},
    }
    response = post(list_url, params, admin)
    assert response.status_code == 400
    assert response.data['target_credential'] == ['Target must be a non-external credential']


@pytest.mark.django_db
def test_input_source_rbac_associate(get, post, delete, alice, vault_credential, external_credential):
    list_url = reverse(
        'api:credential_input_source_list',
    )
    params = {
        'target_credential': vault_credential.pk,
        'source_credential': external_credential.pk,
        'input_field_name': 'vault_password',
        'metadata': {'key': 'some_key'},
    }

    # alice can't admin the target *or* source cred
    response = post(list_url, params, alice)
    assert response.status_code == 403

    # alice can't use the source cred
    vault_credential.admin_role.members.add(alice)
    response = post(list_url, params, alice)
    assert response.status_code == 403

    # alice is allowed to associate now
    external_credential.use_role.members.add(alice)
    response = post(list_url, params, alice)
    assert response.status_code == 201

    # now let's try disassociation
    detail = get(response.data['url'], alice)
    assert detail.status_code == 200
    vault_credential.admin_role.members.remove(alice)
    external_credential.use_role.members.remove(alice)

    # now that permissions are removed, alice can't *read* the input source
    assert get(response.data['url'], alice).status_code == 403

    # alice can't admin the target (so she can't remove the input source)
    delete_url = reverse(
        'api:credential_input_source_detail',
        kwargs={'pk': detail.data['id']}
    )
    response = delete(delete_url, alice)
    assert response.status_code == 403

    # alice is allowed to disassociate now
    vault_credential.admin_role.members.add(alice)
    response = delete(delete_url, alice)
    assert response.status_code == 204


@pytest.mark.django_db
def test_input_source_detail_rbac(get, post, patch, delete, admin, alice,
                                  vault_credential, external_credential,
                                  other_external_credential):
    sublist_url = reverse(
        'api:credential_input_source_sublist',
        kwargs={'pk': vault_credential.pk}
    )
    params = {
        'source_credential': external_credential.pk,
        'input_field_name': 'vault_password',
        'metadata': {'key': 'some_key'},
    }

    response = post(sublist_url, params, admin)
    assert response.status_code == 201

    url = response.data['url']

    # alice can't read the input source directly because she can't read the target cred
    detail = get(url, alice)
    assert detail.status_code == 403

    # alice can read the input source directly
    vault_credential.read_role.members.add(alice)
    detail = get(url, alice)
    assert detail.status_code == 200

    # she can also see it on the credential sublist
    response = get(sublist_url, admin)
    assert response.status_code == 200
    assert response.data['count'] == 1

    # alice can't change or delete the input source because she can't change
    # the target cred and she can't use the source cred
    assert patch(url, {'input_field_name': 'vault_id'}, alice).status_code == 403
    assert delete(url, alice).status_code == 403

    # alice still can't change the input source because she she can't use the
    # source cred
    vault_credential.admin_role.members.add(alice)
    assert patch(url, {'input_field_name': 'vault_id'}, alice).status_code == 403

    # alice can now admin the target cred and use the source cred, so she can
    # change the input field name
    external_credential.use_role.members.add(alice)
    assert patch(url, {'input_field_name': 'vault_id'}, alice).status_code == 200
    assert CredentialInputSource.objects.first().input_field_name == 'vault_id'

    # she _cannot_, however, apply a source credential she doesn't have access to
    assert patch(url, {'source_credential': other_external_credential.pk}, alice).status_code == 403

    assert delete(url, alice).status_code == 204
    assert CredentialInputSource.objects.count() == 0


@pytest.mark.django_db
def test_input_source_create_rbac(get, post, patch, delete, alice,
                                  vault_credential, external_credential,
                                  other_external_credential):
    list_url = reverse('api:credential_input_source_list')
    params = {
        'target_credential': vault_credential.pk,
        'source_credential': external_credential.pk,
        'input_field_name': 'vault_password',
        'metadata': {'key': 'some_key'},
    }

    # alice can't create the inv source because she has access to neither credential
    response = post(list_url, params, alice)
    assert response.status_code == 403

    # alice still can't because she can't use the source credential
    vault_credential.admin_role.members.add(alice)
    response = post(list_url, params, alice)
    assert response.status_code == 403

    # alice can create an input source if she has permissions on both credentials
    external_credential.use_role.members.add(alice)
    response = post(list_url, params, alice)
    assert response.status_code == 201
    assert CredentialInputSource.objects.count() == 1


@pytest.mark.django_db
def test_input_source_rbac_swap_target_credential(get, post, put, patch, admin, alice,
                                                  machine_credential, vault_credential,
                                                  external_credential):
    # If you change the target credential for an input source,
    # you have to have admin role on the *original* credential (so you can
    # remove the relationship) *and* on the *new* credential (so you can apply the
    # new relationship)
    list_url = reverse('api:credential_input_source_list')
    params = {
        'target_credential': vault_credential.pk,
        'source_credential': external_credential.pk,
        'input_field_name': 'vault_password',
        'metadata': {'key': 'some_key'},
    }

    response = post(list_url, params, admin)
    assert response.status_code == 201
    url = response.data['url']

    # alice starts with use permission on the source credential
    # alice starts with no permissions on the target credential
    external_credential.admin_role.members.add(alice)

    # alice can't change target cred because she can't admin either one
    assert patch(url, {
        'target_credential': machine_credential.pk,
        'input_field_name': 'password'
    }, alice).status_code == 403

    # alice still can't change target cred because she can't admin *the new one*
    vault_credential.admin_role.members.add(alice)
    assert patch(url, {
        'target_credential': machine_credential.pk,
        'input_field_name': 'password'
    }, alice).status_code == 403

    machine_credential.admin_role.members.add(alice)
    assert patch(url, {
        'target_credential': machine_credential.pk,
        'input_field_name': 'password'
    }, alice).status_code == 200


@pytest.mark.django_db
def test_input_source_rbac_change_metadata(get, post, put, patch, admin, alice,
                                           machine_credential, external_credential):
    # To change an input source, a user must have admin permissions on the
    # target credential and use permissions on the source credential.
    list_url = reverse('api:credential_input_source_list')
    params = {
        'target_credential': machine_credential.pk,
        'source_credential': external_credential.pk,
        'input_field_name': 'password',
        'metadata': {'key': 'some_key'},
    }

    response = post(list_url, params, admin)
    assert response.status_code == 201
    url = response.data['url']

    # alice can't change input source metadata because she isn't an admin of the
    # target credential and doesn't have use permission on the source credential
    assert patch(url, {
        'metadata': {'key': 'some_other_key'}
    }, alice).status_code == 403

    # alice still can't change input source metadata because she doesn't have
    # use permission on the source credential.
    machine_credential.admin_role.members.add(alice)
    assert patch(url, {
        'metadata': {'key': 'some_other_key'}
    }, alice).status_code == 403

    external_credential.use_role.members.add(alice)
    assert patch(url, {
        'metadata': {'key': 'some_other_key'}
    }, alice).status_code == 200


@pytest.mark.django_db
def test_create_credential_input_source_with_non_external_source_returns_400(post, admin, credential, vault_credential):
    list_url = reverse('api:credential_input_source_list')
    params = {
        'target_credential': vault_credential.pk,
        'source_credential': credential.pk,
        'input_field_name': 'vault_password'
    }
    response = post(list_url, params, admin)
    assert response.status_code == 400
    assert response.data['source_credential'] == ['Source must be an external credential']


@pytest.mark.django_db
def test_create_credential_input_source_with_undefined_input_returns_400(post, admin, vault_credential, external_credential):
    list_url = reverse('api:credential_input_source_list')
    params = {
        'target_credential': vault_credential.pk,
        'source_credential': external_credential.pk,
        'input_field_name': 'not_defined_for_credential_type',
        'metadata': {'key': 'some_key'}
    }
    response = post(list_url, params, admin)
    assert response.status_code == 400
    assert response.data['input_field_name'] == ['Input field must be defined on target credential (options are vault_id, vault_password).']


@pytest.mark.django_db
def test_create_credential_input_source_with_already_used_input_returns_400(post, admin, vault_credential, external_credential, other_external_credential):
    list_url = reverse('api:credential_input_source_list')
    all_params = [{
        'target_credential': vault_credential.pk,
        'source_credential': external_credential.pk,
        'input_field_name': 'vault_password'
    }, {
        'target_credential': vault_credential.pk,
        'source_credential': other_external_credential.pk,
        'input_field_name': 'vault_password'
    }]
    all_responses = [post(list_url, params, admin) for params in all_params]
    assert all_responses.pop().status_code == 400
