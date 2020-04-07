import base64
import json
import time

import pytest

from django.db import connection
from django.test.utils import override_settings
from django.utils.encoding import smart_str, smart_bytes

from awx.main.utils.encryption import decrypt_value, get_encryption_key
from awx.api.versioning import reverse, drf_reverse
from awx.main.models.oauth import (OAuth2Application as Application, 
                                   OAuth2AccessToken as AccessToken)
from awx.main.tests.functional import immediate_on_commit
from awx.sso.models import UserEnterpriseAuth
from oauth2_provider.models import RefreshToken


@pytest.mark.django_db
def test_personal_access_token_creation(oauth_application, post, alice):
    url = drf_reverse('api:oauth_authorization_root_view') + 'token/'
    resp = post(
        url,
        data='grant_type=password&username=alice&password=alice&scope=read',
        content_type='application/x-www-form-urlencoded',
        HTTP_AUTHORIZATION='Basic ' + smart_str(base64.b64encode(smart_bytes(':'.join([
            oauth_application.client_id, oauth_application.client_secret
        ]))))
    )
    resp_json = smart_str(resp._container[0])
    assert 'access_token' in resp_json
    assert 'scope' in resp_json
    assert 'refresh_token' in resp_json


@pytest.mark.django_db
@pytest.mark.parametrize('allow_oauth, status', [(True, 201), (False, 403)])
def test_token_creation_disabled_for_external_accounts(oauth_application, post, alice, allow_oauth, status):
    UserEnterpriseAuth(user=alice, provider='radius').save()
    url = drf_reverse('api:oauth_authorization_root_view') + 'token/'

    with override_settings(RADIUS_SERVER='example.org', ALLOW_OAUTH2_FOR_EXTERNAL_USERS=allow_oauth):
        resp = post(
            url,
            data='grant_type=password&username=alice&password=alice&scope=read',
            content_type='application/x-www-form-urlencoded',
            HTTP_AUTHORIZATION='Basic ' + smart_str(base64.b64encode(smart_bytes(':'.join([
                oauth_application.client_id, oauth_application.client_secret
            ])))),
            status=status
        )
        if allow_oauth:
            assert AccessToken.objects.count() == 1
        else:
            assert 'OAuth2 Tokens cannot be created by users associated with an external authentication provider' in smart_str(resp.content)  # noqa
            assert AccessToken.objects.count() == 0


@pytest.mark.django_db
def test_existing_token_enabled_for_external_accounts(oauth_application, get, post, admin):
    UserEnterpriseAuth(user=admin, provider='radius').save()
    url = drf_reverse('api:oauth_authorization_root_view') + 'token/'
    with override_settings(RADIUS_SERVER='example.org', ALLOW_OAUTH2_FOR_EXTERNAL_USERS=True):
        resp = post(
            url,
            data='grant_type=password&username=admin&password=admin&scope=read',
            content_type='application/x-www-form-urlencoded',
            HTTP_AUTHORIZATION='Basic ' + smart_str(base64.b64encode(smart_bytes(':'.join([
                oauth_application.client_id, oauth_application.client_secret
            ])))),
            status=201
        )
        token = json.loads(resp.content)['access_token']
        assert AccessToken.objects.count() == 1

        with immediate_on_commit():
            resp = get(
                drf_reverse('api:user_me_list', kwargs={'version': 'v2'}),
                HTTP_AUTHORIZATION='Bearer ' + token,
                status=200
            )
            assert json.loads(resp.content)['results'][0]['username'] == 'admin'

    with override_settings(RADIUS_SERVER='example.org', ALLOW_OAUTH2_FOR_EXTERNAL_USER=False):
        with immediate_on_commit():
            resp = get(
                drf_reverse('api:user_me_list', kwargs={'version': 'v2'}),
                HTTP_AUTHORIZATION='Bearer ' + token,
                status=200
            )
            assert json.loads(resp.content)['results'][0]['username'] == 'admin'


@pytest.mark.django_db
def test_pat_creation_no_default_scope(oauth_application, post, admin):
    # tests that the default scope is overriden
    url = reverse('api:o_auth2_token_list')
    response = post(url, {'description': 'test token',
                          'scope': 'read',
                          'application': oauth_application.pk,
                          }, admin)
    assert response.data['scope'] == 'read'
    
    
@pytest.mark.django_db
def test_pat_creation_no_scope(oauth_application, post, admin):
    url = reverse('api:o_auth2_token_list')
    response = post(url, {'description': 'test token',
                          'application': oauth_application.pk,
                          }, admin)
    assert response.data['scope'] == 'write'


@pytest.mark.django_db
def test_oauth2_application_create(admin, organization, post):
    response = post(
        reverse('api:o_auth2_application_list'), {
            'name': 'test app',
            'organization': organization.pk,
            'client_type': 'confidential',
            'authorization_grant_type': 'password',
        }, admin, expect=201
    )
    assert 'modified' in response.data
    assert 'updated' not in response.data
    created_app = Application.objects.get(client_id=response.data['client_id'])
    assert created_app.name == 'test app'
    assert created_app.skip_authorization is False
    assert created_app.redirect_uris == ''
    assert created_app.client_type == 'confidential'
    assert created_app.authorization_grant_type == 'password'
    assert created_app.organization == organization
    
    
@pytest.mark.django_db
def test_oauth2_validator(admin, oauth_application, post):
    post(
        reverse('api:o_auth2_application_list'), {
            'name': 'Write App Token', 
            'application': oauth_application.pk,
            'scope': 'Write',
        }, admin, expect=400
    )
    

@pytest.mark.django_db
def test_oauth_application_update(oauth_application, organization, patch, admin, alice):
    patch(
        reverse('api:o_auth2_application_detail', kwargs={'pk': oauth_application.pk}), {
            'name': 'Test app with immutable grant type and user',
            'organization': organization.pk,
            'redirect_uris': 'http://localhost/api/',
            'authorization_grant_type': 'password',
            'skip_authorization': True,
        }, admin, expect=200
    )
    updated_app = Application.objects.get(client_id=oauth_application.client_id)
    assert updated_app.name == 'Test app with immutable grant type and user'
    assert updated_app.redirect_uris == 'http://localhost/api/'
    assert updated_app.skip_authorization is True
    assert updated_app.authorization_grant_type == 'password'
    assert updated_app.organization == organization


@pytest.mark.django_db
def test_oauth_application_encryption(admin, organization, post):
    response = post(
        reverse('api:o_auth2_application_list'), {
            'name': 'test app',
            'organization': organization.pk,
            'client_type': 'confidential',
            'authorization_grant_type': 'password',
        }, admin, expect=201
    )
    pk = response.data.get('id')
    secret = response.data.get('client_secret')
    with connection.cursor() as cursor:
        encrypted = cursor.execute(
            'SELECT client_secret FROM main_oauth2application WHERE id={}'.format(pk)
        ).fetchone()[0]
        assert encrypted.startswith('$encrypted$')
        assert decrypt_value(get_encryption_key('value', pk=None), encrypted) == secret


@pytest.mark.django_db
def test_oauth_token_create(oauth_application, get, post, admin):
    response = post(
        reverse('api:o_auth2_application_token_list', kwargs={'pk': oauth_application.pk}),
        {'scope': 'read'}, admin, expect=201
    )
    assert 'modified' in response.data and response.data['modified'] is not None
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
        'id': token.pk, 'scope': token.scope, 'token': '************'
    }

    response = post(
        reverse('api:o_auth2_token_list'),
        {'scope': 'read', 'application': oauth_application.pk}, admin, expect=201
    )
    assert response.data['refresh_token']
    response = post(
        reverse('api:user_authorized_token_list', kwargs={'pk': admin.pk}),
        {'scope': 'read', 'application': oauth_application.pk}, admin, expect=201
    )
    assert response.data['refresh_token']
    response = post(
        reverse('api:application_o_auth2_token_list', kwargs={'pk': oauth_application.pk}),
        {'scope': 'read'}, admin, expect=201
    )
    assert response.data['refresh_token']


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
    assert RefreshToken.objects.count() == 1
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


@pytest.mark.django_db
def test_oauth_list_user_tokens(oauth_application, post, get, admin, alice):
    for user in (admin, alice):
        url = reverse('api:o_auth2_token_list', kwargs={'pk': user.pk})
        post(url, {'scope': 'read'}, user, expect=201)
        response = get(url, admin, expect=200)
        assert response.data['count'] == 1
    

@pytest.mark.django_db
def test_refresh_accesstoken(oauth_application, post, get, delete, admin):
    response = post(
        reverse('api:o_auth2_application_token_list', kwargs={'pk': oauth_application.pk}),
        {'scope': 'read'}, admin, expect=201
    )    
    assert AccessToken.objects.count() == 1
    assert RefreshToken.objects.count() == 1
    token = AccessToken.objects.get(token=response.data['token'])
    refresh_token = RefreshToken.objects.get(token=response.data['refresh_token'])
    
    refresh_url = drf_reverse('api:oauth_authorization_root_view') + 'token/'    
    response = post(
        refresh_url,
        data='grant_type=refresh_token&refresh_token=' + refresh_token.token,
        content_type='application/x-www-form-urlencoded',
        HTTP_AUTHORIZATION='Basic ' + smart_str(base64.b64encode(smart_bytes(':'.join([
            oauth_application.client_id, oauth_application.client_secret
        ]))))
    )
    assert RefreshToken.objects.filter(token=refresh_token).exists()
    original_refresh_token = RefreshToken.objects.get(token=refresh_token)
    assert token not in AccessToken.objects.all()
    assert AccessToken.objects.count() == 1
    # the same RefreshToken remains but is marked revoked
    assert RefreshToken.objects.count() == 2
    new_token = json.loads(response._container[0])['access_token']
    new_refresh_token = json.loads(response._container[0])['refresh_token']
    assert AccessToken.objects.filter(token=new_token).count() == 1
    # checks that RefreshTokens are rotated (new RefreshToken issued)
    assert RefreshToken.objects.filter(token=new_refresh_token).count() == 1
    assert original_refresh_token.revoked # is not None


@pytest.mark.django_db
def test_refresh_token_expiration_is_respected(oauth_application, post, get, delete, admin):
    response = post(
        reverse('api:o_auth2_application_token_list', kwargs={'pk': oauth_application.pk}),
        {'scope': 'read'}, admin, expect=201
    )
    assert AccessToken.objects.count() == 1
    assert RefreshToken.objects.count() == 1
    refresh_token = RefreshToken.objects.get(token=response.data['refresh_token'])
    refresh_url = drf_reverse('api:oauth_authorization_root_view') + 'token/'
    short_lived = {
        'ACCESS_TOKEN_EXPIRE_SECONDS': 1,
        'AUTHORIZATION_CODE_EXPIRE_SECONDS': 1,
        'REFRESH_TOKEN_EXPIRE_SECONDS': 1
    }
    time.sleep(1)
    with override_settings(OAUTH2_PROVIDER=short_lived):
        response = post(
            refresh_url,
            data='grant_type=refresh_token&refresh_token=' + refresh_token.token,
            content_type='application/x-www-form-urlencoded',
            HTTP_AUTHORIZATION='Basic ' + smart_str(base64.b64encode(smart_bytes(':'.join([
                oauth_application.client_id, oauth_application.client_secret
            ]))))
        )
    assert response.status_code == 403
    assert b'The refresh token has expired.' in response.content
    assert RefreshToken.objects.filter(token=refresh_token).exists()
    assert AccessToken.objects.count() == 1
    assert RefreshToken.objects.count() == 1



@pytest.mark.django_db
def test_revoke_access_then_refreshtoken(oauth_application, post, get, delete, admin):
    response = post(
        reverse('api:o_auth2_application_token_list', kwargs={'pk': oauth_application.pk}),
        {'scope': 'read'}, admin, expect=201
    )    
    token = AccessToken.objects.get(token=response.data['token'])
    refresh_token = RefreshToken.objects.get(token=response.data['refresh_token'])
    assert AccessToken.objects.count() == 1
    assert RefreshToken.objects.count() == 1
    
    token.revoke()
    assert AccessToken.objects.count() == 0
    assert RefreshToken.objects.count() == 1
    assert not refresh_token.revoked
    
    refresh_token.revoke()
    assert AccessToken.objects.count() == 0
    assert RefreshToken.objects.count() == 1
    
    
@pytest.mark.django_db
def test_revoke_refreshtoken(oauth_application, post, get, delete, admin):
    response = post(
        reverse('api:o_auth2_application_token_list', kwargs={'pk': oauth_application.pk}),
        {'scope': 'read'}, admin, expect=201
    )    
    refresh_token = RefreshToken.objects.get(token=response.data['refresh_token'])
    assert AccessToken.objects.count() == 1
    assert RefreshToken.objects.count() == 1
    
    refresh_token.revoke()
    assert AccessToken.objects.count() == 0
    # the same RefreshToken is recycled
    new_refresh_token = RefreshToken.objects.all().first()
    assert refresh_token == new_refresh_token
    assert new_refresh_token.revoked
