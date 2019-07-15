# Python
import pytest
from unittest import mock

# Tower
from awx.sso.backends import _get_or_set_enterprise_user


@pytest.mark.django_db
def test_fetch_user_if_exist(existing_tacacsplus_user):
    with mock.patch('awx.sso.backends.logger') as mocked_logger:
        new_user = _get_or_set_enterprise_user("foo", "password", "tacacs+")
        mocked_logger.debug.assert_not_called()
        mocked_logger.warn.assert_not_called()
        assert new_user == existing_tacacsplus_user


@pytest.mark.django_db
def test_create_user_if_not_exist(existing_tacacsplus_user):
    with mock.patch('awx.sso.backends.logger') as mocked_logger:
        new_user = _get_or_set_enterprise_user("bar", "password", "tacacs+")
        mocked_logger.debug.assert_called_once_with(
            u'Created enterprise user bar via TACACS+ backend.'
        )
        assert new_user != existing_tacacsplus_user


@pytest.mark.django_db
def test_created_user_has_no_usable_password():
    new_user = _get_or_set_enterprise_user("bar", "password", "tacacs+")
    assert not new_user.has_usable_password()


@pytest.mark.django_db
def test_non_enterprise_user_does_not_get_pass(existing_normal_user):
    with mock.patch('awx.sso.backends.logger') as mocked_logger:
        new_user = _get_or_set_enterprise_user("alice", "password", "tacacs+")
        mocked_logger.warn.assert_called_once_with(
            u'Enterprise user alice already defined in Tower.'
        )
        assert new_user is None
