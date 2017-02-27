from django.test.utils import override_settings
import ldap
import pytest

from awx.sso.backends import LDAPSettings


@override_settings(AUTH_LDAP_CONNECTION_OPTIONS = {ldap.OPT_NETWORK_TIMEOUT: 60})
@pytest.mark.django_db
def test_ldap_with_custom_timeout():
    settings = LDAPSettings()
    assert settings.CONNECTION_OPTIONS == {
        ldap.OPT_NETWORK_TIMEOUT: 60
    }


@override_settings(AUTH_LDAP_CONNECTION_OPTIONS = {ldap.OPT_REFERRALS: 0})
@pytest.mark.django_db
def test_ldap_with_missing_timeout():
    settings = LDAPSettings()
    assert settings.CONNECTION_OPTIONS == {
        ldap.OPT_REFERRALS: 0,
        ldap.OPT_NETWORK_TIMEOUT: 30
    }
