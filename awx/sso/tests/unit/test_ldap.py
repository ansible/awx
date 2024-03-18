import pytest
import ldap

from awx.sso.backends import LDAPSettings as OldLDAPSettings
from awx.sso.validators import validate_ldap_filter as old_validate_ldap_filter
from ansible_base.authentication.authenticator_plugins.ldap import LDAPSettings, validate_ldap_filter

from django.core.cache import cache


def test_old_ldap_default_settings(mocker):
    from_db = mocker.Mock(**{'order_by.return_value': []})
    with mocker.patch('awx.conf.models.Setting.objects.filter', return_value=from_db):
        settings = OldLDAPSettings()
        assert settings.ORGANIZATION_MAP == {}
        assert settings.TEAM_MAP == {}


def test_old_ldap_default_network_timeout(mocker):
    cache.clear()  # clearing cache avoids picking up stray default for OPT_REFERRALS
    from_db = mocker.Mock(**{'order_by.return_value': []})
    with mocker.patch('awx.conf.models.Setting.objects.filter', return_value=from_db):
        settings = OldLDAPSettings()
        assert settings.CONNECTION_OPTIONS[ldap.OPT_NETWORK_TIMEOUT] == 30


def test_old_ldap_filter_validator():
    old_validate_ldap_filter('(test-uid=%(user)s)', with_user=True)


@pytest.mark.django_db
def test_ldap_default_settings(ldap_configuration):
    settings = LDAPSettings(defaults=ldap_configuration)
    assert settings.DENY_GROUP == None
    assert settings.USER_QUERY_FIELD == None


@pytest.mark.django_db
def test_ldap_default_network_timeout(ldap_configuration):
    cache.clear()  # clearing cache avoids picking up stray default for OPT_REFERRALS
    settings = LDAPSettings(defaults=ldap_configuration)
    assert settings.CONNECTION_OPTIONS[ldap.OPT_NETWORK_TIMEOUT] == 30


def test_ldap_filter_validator():
    validate_ldap_filter('(test-uid=%(user)s)', with_user=True)
