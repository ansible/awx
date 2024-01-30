import ldap
import pytest

from ansible_base.authentication.authenticator_plugins.ldap import LDAPSettings


@pytest.mark.django_db
def test_ldap_with_custom_timeout(ldap_configuration):
    ldap_configuration["CONNECTION_OPTIONS"] = {"OPT_NETWORK_TIMEOUT": 60}
    settings = LDAPSettings(defaults=ldap_configuration)
    assert settings.CONNECTION_OPTIONS == {ldap.OPT_NETWORK_TIMEOUT: 60}


@pytest.mark.django_db
def test_ldap_with_missing_timeout(ldap_configuration):
    ldap_configuration["CONNECTION_OPTIONS"] = {"OPT_REFERRALS": 0}
    settings = LDAPSettings(defaults=ldap_configuration)
    assert settings.CONNECTION_OPTIONS == {ldap.OPT_REFERRALS: 0, ldap.OPT_NETWORK_TIMEOUT: 30}
