from datetime import date
from unittest import mock

import pytest

from django.contrib.sessions.middleware import SessionMiddleware
from django.test.utils import override_settings
from django.contrib.auth.models import AnonymousUser

from ansible_base.lib.utils.response import get_relative_url
from ansible_base.lib.testing.fixtures import settings_override_mutable  # NOQA: F401 imported to be a pytest fixture

from awx.main.models import User
from awx.api.versioning import reverse


#
# user creation
#

EXAMPLE_USER_DATA = {"username": "affable", "first_name": "a", "last_name": "a", "email": "a@a.com", "is_superuser": False, "password": "r$TyKiOCb#ED"}


@pytest.mark.django_db
def test_validate_local_user(post, admin_user, settings, settings_override_mutable):  # NOQA: F811 this is how you use a pytest fixture
    "Copy of the test by same name in django-ansible-base for integration and compatibility testing"
    url = get_relative_url('validate-local-account')
    admin_user.set_password('password')
    admin_user.save()
    data = {
        "username": admin_user.username,
        "password": "password",
    }
    with override_settings(RESOURCE_SERVER={"URL": "https://foo.invalid", "SECRET_KEY": "foobar"}):
        response = post(url=url, data=data, user=AnonymousUser(), expect=200)

    assert 'ansible_id' in response.data
    assert response.data['auth_code'] is not None, response.data

    # No resource server, return coherent response but can not provide auth code
    response = post(url=url, data=data, user=AnonymousUser(), expect=200)
    assert 'ansible_id' in response.data
    assert response.data['auth_code'] is None

    # wrong password
    data['password'] = 'foobar'
    response = post(url=url, data=data, user=AnonymousUser(), expect=401)
    # response.data may be none here, this is just testing that we get no server error


@pytest.mark.django_db
def test_user_create(post, admin):
    response = post(reverse('api:user_list'), EXAMPLE_USER_DATA, admin, middleware=SessionMiddleware(mock.Mock()))
    assert response.status_code == 201
    assert not response.data['is_superuser']
    assert not response.data['is_system_auditor']


@pytest.mark.django_db
# Disable local password checks to ensure that any ValidationError originates from the Django validators.
@override_settings(
    LOCAL_PASSWORD_MIN_LENGTH=1,
    LOCAL_PASSWORD_MIN_DIGITS=0,
    LOCAL_PASSWORD_MIN_UPPER=0,
    LOCAL_PASSWORD_MIN_SPECIAL=0,
)
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


@pytest.mark.django_db
# Disable local password checks to ensure that any ValidationError originates from the Django validators.
@override_settings(
    LOCAL_PASSWORD_MIN_LENGTH=1,
    LOCAL_PASSWORD_MIN_DIGITS=0,
    LOCAL_PASSWORD_MIN_UPPER=0,
    LOCAL_PASSWORD_MIN_SPECIAL=0,
)
def test_user_create_with_django_password_validation_ext(post, delete, admin):
    """Test the functionality of the single Django password validators."""
    #
    default_fixtures = {
        # Keys in `fixtures` override `default_fixtures` if they exist and their
        # value is not 'None'.
        "user_attrs": {
            "password": "r$TyKiOCb#ED",  # NOSONAR
            "username": "DefaultUser",
            "is_superuser": False,
        },
        "password_validators": [
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
    # The list of fixture dicts which constitute the test cases.
    fixtures_list = [
        # Test password similarity with username.
        {
            "user_attrs": {
                "password": "TestUser1",  # NOSONAR
                "username": "TestUser1",
                "is_superuser": False,
            },
            "password_validators": [
                {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
            ],
            "expected_status_code": 400,
        },
        {
            "user_attrs": {
                "password": "abc",  # NOSONAR
                "username": "TestUser1",
                "is_superuser": False,
            },
            "password_validators": [
                {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
            ],
            "expected_status_code": 201,
        },
        # Test password min length criterion.
        {
            "user_attrs": {
                "password": "TooShort",  # NOSONAR
                "username": "TestUser1",
                "is_superuser": False,
            },
            "password_validators": [
                {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 9}},
            ],
            "expected_status_code": 400,
        },
        {
            "user_attrs": {
                "password": "LongEnough",  # NOSONAR
                "username": "TestUser1",
                "is_superuser": False,
            },
            "password_validators": [
                {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 9}},
            ],
            "expected_status_code": 201,
        },
        # Test password is too common criterion.
        {
            "user_attrs": {
                "password": "Password",  # NOSONAR
                "username": "TestUser1",
                "is_superuser": False,
            },
            "password_validators": [
                {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
            ],
            "expected_status_code": 400,
        },
        {
            "user_attrs": {
                "password": "Password",  # NOSONAR
                "username": "TestUser1",
                "is_superuser": False,
            },
            "password_validators": [],
            "expected_status_code": 201,
        },
        # Test if password is only numeric.
        {
            "user_attrs": {
                "password": "1234567890",  # NOSONAR
                "username": "TestUser1",
                "is_superuser": False,
            },
            "password_validators": [
                {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
            ],
            "expected_status_code": 400,
        },
        {
            "user_attrs": {
                "password": "1234567890",  # NOSONAR
                "username": "TestUser1",
                "is_superuser": False,
            },
            "password_validators": [],
            "expected_status_code": 201,
        },
    ]
    for i, fixtures in enumerate(fixtures_list):
        user_attrs = fixtures.setdefault("user_attrs", default_fixtures["user_attrs"])
        password_validators = fixtures.setdefault("password_validators", default_fixtures["password_validators"])
        expected_status_code = fixtures["expected_status_code"]
        print(f"Testing fixtures {i}: {expected_status_code=} {user_attrs=}")
        with override_settings(AUTH_PASSWORD_VALIDATORS=password_validators):
            response = post(reverse('api:user_list'), user_attrs, admin, middleware=SessionMiddleware(mock.Mock()))
            assert response.status_code == expected_status_code, (i, fixtures)
            # Delete user if it was created succesfully.
            if response.status_code == 201:
                response = delete(reverse('api:user_detail', kwargs={'pk': response.data['id']}), admin, middleware=SessionMiddleware(mock.Mock()))
                assert response.status_code == 204
            else:
                # Catch the unexpected behavour that sometimes the user is
                # written into the database before the validation fails. This
                # actually can happen if UserSerializer.validate instantiates
                # User(**attrs)!
                username = fixtures['user_attrs']['username']
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

    past = date(2020, 1, 1).isoformat()
    for op, count in (('gt', 1), ('lt', 0)):
        resp = get(reverse('api:user_list') + f'?created__{op}={past}', admin)
        assert resp.data['count'] == count
