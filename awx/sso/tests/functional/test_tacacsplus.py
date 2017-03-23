import pytest
import mock


@pytest.mark.django_db
def test_fetch_user_if_exist(tacacsplus_backend, existing_tacacsplus_user):
    new_user = tacacsplus_backend._get_or_set_user("foo", "password")
    assert new_user == existing_tacacsplus_user


@pytest.mark.django_db
def test_create_user_if_not_exist(tacacsplus_backend, existing_tacacsplus_user):
    with mock.patch('awx.sso.backends.logger') as mocked_logger:
        new_user = tacacsplus_backend._get_or_set_user("bar", "password")
        mocked_logger.debug.assert_called_once_with(
            'Created TACACS+ user bar'
        )
        assert new_user != existing_tacacsplus_user


@pytest.mark.django_db
def test_created_user_has_no_usable_password(tacacsplus_backend):
    new_user = tacacsplus_backend._get_or_set_user("bar", "password")
    assert not new_user.has_usable_password()
