import ldap
import pytest

from ansible_base.authentication.authenticator_plugins.ldap import LDAPSettings, validate_ldap_filter

from django.core.cache import cache


def test_ldap_default_settings(ldap_configuration):
    settings = LDAPSettings(defaults=ldap_configuration)
    assert settings.DENY_GROUP == None
    assert settings.USER_QUERY_FIELD == None


def test_ldap_authenticatormap(ldap_authenticator_map):
    assert ldap_authenticator_map.map_type == "team"
    assert ldap_authenticator_map.team == None
    assert ldap_authenticator_map.organization == None


def test_ldap_default_network_timeout(ldap_configuration):
    cache.clear()  # clearing cache avoids picking up stray default for OPT_REFERRALS
    settings = LDAPSettings(defaults=ldap_configuration)
    assert settings.CONNECTION_OPTIONS[ldap.OPT_NETWORK_TIMEOUT] == 30


def test_ldap_filter_validator():
    validate_ldap_filter('(test-uid=%(user)s)', with_user=True)
