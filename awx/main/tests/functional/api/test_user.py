from unittest import mock
import json

import pytest

from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory
from django.test.utils import override_settings

from awx.main.models import User
from awx.main.middleware import ForcePasswordChangeMiddleware
from awx.api.versioning import reverse

#
# user creation
#

EXAMPLE_USER_DATA = {"username": "affable", "first_name": "a", "last_name": "a", "email": "a@a.com", "is_superuser": False, "password": "r$TyKiOCb#ED"}


@pytest.mark.django_db
def test_user_create(post, admin):
    response = post(reverse('api:user_list'), EXAMPLE_USER_DATA, admin, middleware=SessionMiddleware(mock.Mock()))
    assert response.status_code == 201
    assert not response.data['is_superuser']
    assert not response.data['is_system_auditor']


# Disable local password checks to ensure that any ValidationError originates from the Django validators.
@override_settings(
    LOCAL_PASSWORD_MIN_LENGTH=1,
    LOCAL_PASSWORD_MIN_DIGITS=0,
    LOCAL_PASSWORD_MIN_UPPER=0,
    LOCAL_PASSWORD_MIN_SPECIAL=0,
)
@pytest.mark.django_db
def test_user_create_with_django_password_validation_basic(post, admin):
    """Test if the Django password validators are applied correctly."""
    with override_settings(
        AUTH_PASSWORD_VALIDATORS=[
            {
                'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
            },
            {
                'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
                'OPTIONS': {
                    'min_length': 3,
                },
            },
            {
                'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
            },
            {
                'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
            },
        ],
    ):
        # This user should fail the UserAttrSimilarity, MinLength and CommonPassword validators.
        user_attrs = (
            {
                "password": "Password",  # NOSONAR
                "username": "Password",
                "is_superuser": False,
            },
        )
        print(f"Create user with invalid password {user_attrs=}")
        response = post(reverse('api:user_list'), user_attrs, admin, middleware=SessionMiddleware(mock.Mock()))
        assert response.status_code == 400
        # This user should pass all Django validators.
        user_attrs = {
            "password": "r$TyKiOCb#ED",  # NOSONAR
            "username": "TestUser",
            "is_superuser": False,
        }
        print(f"Create user with valid password {user_attrs=}")
        response = post(reverse('api:user_list'), user_attrs, admin, middleware=SessionMiddleware(mock.Mock()))
        assert response.status_code == 201


@pytest.mark.parametrize(
    "user_attrs,validators,expected_status_code",
    [
        # Test password similarity with username.
        (
            {"password": "TestUser1", "username": "TestUser1", "is_superuser": False},  # NOSONAR
            [
                {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
            ],
            400,
        ),
        (
            {"password": "abc", "username": "TestUser1", "is_superuser": False},  # NOSONAR
            [
                {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
            ],
            201,
        ),
        # Test password min length criterion.
        (
            {"password": "TooShort", "username": "TestUser1", "is_superuser": False},  # NOSONAR
            [
                {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 9}},
            ],
            400,
        ),
        (
            {"password": "LongEnough", "username": "TestUser1", "is_superuser": False},  # NOSONAR
            [
                {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 9}},
            ],
            201,
        ),
        # Test password is too common criterion.
        (
            {"password": "Password", "username": "TestUser1", "is_superuser": False},  # NOSONAR
            [
                {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
            ],
            400,
        ),
        (
            {"password": "aEArV$5Vkdw", "username": "TestUser1", "is_superuser": False},  # NOSONAR
            [
                {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
            ],
            201,
        ),
        # Test if password is only numeric.
        (
            {"password": "1234567890", "username": "TestUser1", "is_superuser": False},  # NOSONAR
            [
                {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
            ],
            400,
        ),
        (
            {"password": "abc4567890", "username": "TestUser1", "is_superuser": False},  # NOSONAR
            [
                {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
            ],
            201,
        ),
    ],
)
# Disable local password checks to ensure that any ValidationError originates from the Django validators.
@override_settings(
    LOCAL_PASSWORD_MIN_LENGTH=1,
    LOCAL_PASSWORD_MIN_DIGITS=0,
    LOCAL_PASSWORD_MIN_UPPER=0,
    LOCAL_PASSWORD_MIN_SPECIAL=0,
)
@pytest.mark.django_db
def test_user_create_with_django_password_validation_ext(post, delete, admin, user_attrs, validators, expected_status_code):
    """Test the functionality of the single Django password validators."""
    #
    default_parameters = {
        # Default values for input parameters which are None.
        "user_attrs": {
            "password": "r$TyKiOCb#ED",  # NOSONAR
            "username": "DefaultUser",
            "is_superuser": False,
        },
        "validators": [
            {
                'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
            },
            {
                'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
                'OPTIONS': {
                    'min_length': 8,
                },
            },
            {
                'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
            },
            {
                'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
            },
        ],
    }
    user_attrs = user_attrs if user_attrs is not None else default_parameters["user_attrs"]
    validators = validators if validators is not None else default_parameters["validators"]
    with override_settings(AUTH_PASSWORD_VALIDATORS=validators):
        response = post(reverse('api:user_list'), user_attrs, admin, middleware=SessionMiddleware(mock.Mock()))
        assert response.status_code == expected_status_code
        # Delete user if it was created succesfully.
        if response.status_code == 201:
            response = delete(reverse('api:user_detail', kwargs={'pk': response.data['id']}), admin, middleware=SessionMiddleware(mock.Mock()))
            assert response.status_code == 204
        else:
            # Catch the unexpected behavior that sometimes the user is written
            # into the database before the validation fails. This actually can
            # happen if UserSerializer.validate instantiates User(**attrs)!
            username = user_attrs['username']
            assert not User.objects.filter(username=username)


@pytest.mark.django_db
def test_fail_double_create_user(post, admin):
    response = post(reverse('api:user_list'), EXAMPLE_USER_DATA, admin, middleware=SessionMiddleware(mock.Mock()))
    assert response.status_code == 201

    response = post(reverse('api:user_list'), EXAMPLE_USER_DATA, admin, middleware=SessionMiddleware(mock.Mock()))
    assert response.status_code == 400


@pytest.mark.django_db
def test_creating_user_retains_session(post, admin):
    '''
    Creating a new user should not refresh a new session id for the current user.
    '''
    with mock.patch('awx.api.serializers.update_session_auth_hash') as update_session_auth_hash:
        response = post(reverse('api:user_list'), EXAMPLE_USER_DATA, admin)
        assert response.status_code == 201
        assert not update_session_auth_hash.called


@pytest.mark.django_db
def test_updating_own_password_refreshes_session(patch, admin):
    '''
    Updating your own password should refresh the session id.
    '''
    with mock.patch('awx.api.serializers.update_session_auth_hash') as update_session_auth_hash:
        # Attention: If the Django password validator `CommonPasswordValidator`
        # is active, this test case will fail because this validator raises on
        # password 'newpassword'. Consider changing the hard-coded password to
        # something uncommon.
        patch(reverse('api:user_detail', kwargs={'pk': admin.pk}), {'password': 'newpassword'}, admin, middleware=SessionMiddleware(mock.Mock()))
        assert update_session_auth_hash.called


@pytest.mark.django_db
def test_create_delete_create_user(post, delete, admin):
    response = post(reverse('api:user_list'), EXAMPLE_USER_DATA, admin, middleware=SessionMiddleware(mock.Mock()))
    assert response.status_code == 201

    response = delete(reverse('api:user_detail', kwargs={'pk': response.data['id']}), admin, middleware=SessionMiddleware(mock.Mock()))
    assert response.status_code == 204

    response = post(reverse('api:user_list'), EXAMPLE_USER_DATA, admin, middleware=SessionMiddleware(mock.Mock()))
    print(response.data)
    assert response.status_code == 201


@pytest.mark.django_db
def test_user_cannot_update_last_login(patch, admin):
    assert admin.last_login is None
    patch(reverse('api:user_detail', kwargs={'pk': admin.pk}), {'last_login': '2020-03-13T16:39:47.303016Z'}, admin, middleware=SessionMiddleware(mock.Mock()))
    assert User.objects.get(pk=admin.pk).last_login is None


@pytest.mark.django_db
def test_user_verify_attribute_created(admin, get):
    assert admin.created == admin.date_joined
    resp = get(reverse('api:user_detail', kwargs={'pk': admin.pk}), admin)
    assert resp.data['created'] == admin.date_joined

    past = "2020-01-01T00:00:00Z"
    for op, count in (('gt', 1), ('lt', 0)):
        resp = get(reverse('api:user_list') + f'?created__{op}={past}', admin)
        assert resp.data['count'] == count


@pytest.mark.django_db
def test_org_not_shown_in_admin_user_sublists(admin_user, get, organization, setup_managed_roles):
    for view_name in ('user_admin_of_organizations_list', 'user_organizations_list'):
        url = reverse(f'api:{view_name}', kwargs={'pk': admin_user.pk})
        r = get(url, user=admin_user, expect=200)
        assert organization.pk not in [org['id'] for org in r.data['results']]


@pytest.mark.django_db
def test_admin_user_not_shown_in_org_users(admin_user, get, organization):
    for view_name in ('organization_users_list', 'organization_admins_list'):
        url = reverse(f'api:{view_name}', kwargs={'pk': organization.pk})
        r = get(url, user=admin_user, expect=200)
        assert admin_user.pk not in [u['id'] for u in r.data['results']]


@pytest.mark.django_db
def test_create_user_with_password_reset_required(post, get, admin):
    """Admins can create users that must reset password on next login."""
    data = dict(EXAMPLE_USER_DATA, password_reset_required=True)
    response = post(reverse('api:user_list'), data, admin, middleware=SessionMiddleware(mock.Mock()))
    assert response.status_code == 201
    assert response.data['password_reset_required'] is True
    user = User.objects.get(pk=response.data['id'])
    assert user.password_reset_required is True

    # Flag is persisted and visible on detail/me-style reads.
    detail = get(reverse('api:user_detail', kwargs={'pk': user.pk}), admin)
    assert detail.status_code == 200
    assert detail.data['password_reset_required'] is True


@pytest.mark.django_db
def test_update_password_reset_required_flag(post, patch, admin):
    response = post(reverse('api:user_list'), EXAMPLE_USER_DATA, admin, middleware=SessionMiddleware(mock.Mock()))
    assert response.status_code == 201
    user_id = response.data['id']
    assert response.data['password_reset_required'] is False

    response = patch(
        reverse('api:user_detail', kwargs={'pk': user_id}),
        {'password_reset_required': True},
        admin,
        middleware=SessionMiddleware(mock.Mock()),
    )
    assert response.status_code == 200
    assert response.data['password_reset_required'] is True
    assert User.objects.get(pk=user_id).password_reset_required is True


@pytest.mark.django_db
def test_password_change_clears_password_reset_required(post, patch, admin):
    """Changing password on an existing user clears the force-reset flag."""
    data = dict(EXAMPLE_USER_DATA, password_reset_required=True)
    response = post(reverse('api:user_list'), data, admin, middleware=SessionMiddleware(mock.Mock()))
    assert response.status_code == 201
    user_id = response.data['id']
    assert User.objects.get(pk=user_id).password_reset_required is True

    response = patch(
        reverse('api:user_detail', kwargs={'pk': user_id}),
        {'password': 'nEwP@ssw0rd!xyz'},
        admin,
        middleware=SessionMiddleware(mock.Mock()),
    )
    assert response.status_code == 200
    user = User.objects.get(pk=user_id)
    assert user.password_reset_required is False
    assert user.check_password('nEwP@ssw0rd!xyz')


@pytest.mark.django_db
def test_create_with_temp_password_keeps_reset_flag(post, admin):
    """Create may set a temporary password and still require reset."""
    data = dict(EXAMPLE_USER_DATA, password_reset_required=True, password='T3mpP@ssw0rd!')
    response = post(reverse('api:user_list'), data, admin, middleware=SessionMiddleware(mock.Mock()))
    assert response.status_code == 201
    user = User.objects.get(pk=response.data['id'])
    assert user.password_reset_required is True
    assert user.check_password('T3mpP@ssw0rd!')


@pytest.mark.django_db
def test_force_password_change_middleware_blocks_other_api(alice):
    alice.password_reset_required = True
    alice.save(update_fields=['password_reset_required'])

    request = RequestFactory().get('/api/v2/organizations/')
    request.user = alice
    response = ForcePasswordChangeMiddleware(lambda r: None).process_request(request)
    assert response is not None
    assert response.status_code == 403
    body = json.loads(response.content.decode('utf-8'))
    assert body['password_reset_required'] is True


@pytest.mark.django_db
def test_force_password_change_middleware_allows_own_user_and_me(alice):
    alice.password_reset_required = True
    alice.save(update_fields=['password_reset_required'])
    mw = ForcePasswordChangeMiddleware(lambda r: None)

    for path in (
        reverse('api:user_me_list'),
        reverse('api:user_detail', kwargs={'pk': alice.pk}),
        '/api/login/',
        '/api/logout/',
        '/static/foo.js',
    ):
        request = RequestFactory().get(path)
        request.user = alice
        assert mw.process_request(request) is None, path

    # Password update on own user is allowed.
    request = RequestFactory().patch(reverse('api:user_detail', kwargs={'pk': alice.pk}))
    request.user = alice
    assert mw.process_request(request) is None


@pytest.mark.django_db
def test_force_password_change_middleware_noop_without_flag(alice):
    assert alice.password_reset_required is False
    request = RequestFactory().get('/api/v2/organizations/')
    request.user = alice
    assert ForcePasswordChangeMiddleware(lambda r: None).process_request(request) is None
