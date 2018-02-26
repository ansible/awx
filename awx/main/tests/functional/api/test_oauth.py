import pytest

from awx.api.versioning import reverse
from awx.main.models.oauth import (OAuth2Application as Application, 
                                   OAuth2AccessToken as AccessToken, 
                                   OAuth2RefreshToken as RefreshToken
                                   )


@pytest.mark.django_db
def test_oauth_application_create(admin, post):
    response = post(
        reverse('api:o_auth2_application_list'), {
            'name': 'test app',
            'user': admin.pk,
            'client_type': 'confidential',
            'authorization_grant_type': 'password',
        }, admin, expect=201
    )
    assert 'modified' in response.data
    assert 'updated' not in response.data
    assert 'user' in response.data['related']
    created_app = Application.objects.get(client_id=response.data['client_id'])
    assert created_app.name == 'test app'
    assert created_app.user == admin
    assert created_app.skip_authorization is False
    assert created_app.redirect_uris == ''
    assert created_app.client_type == 'confidential'
    assert created_app.authorization_grant_type == 'password'


@pytest.mark.django_db
def test_oauth_application_update(oauth_application, patch, admin, alice):
    patch(
        reverse('api:o_auth2_application_detail', kwargs={'pk': oauth_application.pk}), {
            'name': 'Test app with immutable grant type and user',
            'redirect_uris': 'http://localhost/api/',
            'authorization_grant_type': 'implicit',
            'skip_authorization': True,
            'user': alice.pk,
        }, admin, expect=200
    )
    updated_app = Application.objects.get(client_id=oauth_application.client_id)
    assert updated_app.name == 'Test app with immutable grant type and user'
    assert updated_app.redirect_uris == 'http://localhost/api/'
    assert updated_app.skip_authorization is True
    assert updated_app.authorization_grant_type == 'password'
    assert updated_app.user == admin


@pytest.mark.skip(reason="Needs Update - CA")
@pytest.mark.django_db
def test_oauth_token_create(oauth_application, get, post, admin):
    response = post(
        reverse('api:o_auth2_application_token_list', kwargs={'pk': oauth_application.pk}),
        {'scope': 'read'}, admin, expect=201
    )
    assert 'modified' in response.data
    assert 'updated' not in response.data
    token = AccessToken.objects.get(token=response.data['token'])
    refresh_token = RefreshToken.objects.get(token=response.data['refresh_token'])
    assert token.application == oauth_application
    assert refresh_token.application == oauth_application
    assert token.user == admin
    assert refresh_token.user == admin
    assert refresh_token.access_token == token
    assert token.scope == 'read'
    response = get(
        reverse('api:o_auth2_application_token_list', kwargs={'pk': oauth_application.pk}),
        admin, expect=200
    )
    assert response.data['count'] == 1
    response = get(
        reverse('api:o_auth2_application_detail', kwargs={'pk': oauth_application.pk}),
        admin, expect=200
    )
    assert response.data['summary_fields']['tokens']['count'] == 1
    assert response.data['summary_fields']['tokens']['results'][0] == {
        'id': token.pk, 'token': token.token
    }


@pytest.mark.django_db
def test_oauth_token_update(oauth_application, post, patch, admin):
    response = post(
        reverse('api:o_auth2_application_token_list', kwargs={'pk': oauth_application.pk}),
        {'scope': 'read'}, admin, expect=201
    )
    token = AccessToken.objects.get(token=response.data['token'])
    patch(
        reverse('api:o_auth2_token_detail', kwargs={'pk': token.pk}),
        {'scope': 'write'}, admin, expect=200
    )
    token = AccessToken.objects.get(token=token.token)
    assert token.scope == 'write'


@pytest.mark.django_db
def test_oauth_token_delete(oauth_application, post, delete, get, admin):
    response = post(
        reverse('api:o_auth2_application_token_list', kwargs={'pk': oauth_application.pk}),
        {'scope': 'read'}, admin, expect=201
    )
    token = AccessToken.objects.get(token=response.data['token'])
    delete(
        reverse('api:o_auth2_token_detail', kwargs={'pk': token.pk}),
        admin, expect=204
    )
    assert AccessToken.objects.count() == 0
    assert RefreshToken.objects.count() == 0
    response = get(
        reverse('api:o_auth2_application_token_list', kwargs={'pk': oauth_application.pk}),
        admin, expect=200
    )
    assert response.data['count'] == 0
    response = get(
        reverse('api:o_auth2_application_detail', kwargs={'pk': oauth_application.pk}),
        admin, expect=200
    )
    assert response.data['summary_fields']['tokens']['count'] == 0


@pytest.mark.django_db
def test_oauth_application_delete(oauth_application, post, delete, admin):
    post(
        reverse('api:o_auth2_application_token_list', kwargs={'pk': oauth_application.pk}),
        {'scope': 'read'}, admin, expect=201
    )
    delete(
        reverse('api:o_auth2_application_detail', kwargs={'pk': oauth_application.pk}),
        admin, expect=204
    )
    assert Application.objects.filter(client_id=oauth_application.client_id).count() == 0
    assert RefreshToken.objects.filter(application=oauth_application).count() == 0
    assert AccessToken.objects.filter(application=oauth_application).count() == 0
