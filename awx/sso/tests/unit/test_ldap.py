import ldap

from awx.sso.backends import LDAPSettings
from awx.sso.validators import validate_ldap_filter


def test_ldap_default_settings(mocker):
    from_db = mocker.Mock(**{'order_by.return_value': []})
    with mocker.patch('awx.conf.models.Setting.objects.filter', return_value=from_db):
        settings = LDAPSettings()
        assert settings.ORGANIZATION_MAP == {}
        assert settings.TEAM_MAP == {}


def test_ldap_default_network_timeout(mocker):
    from_db = mocker.Mock(**{'order_by.return_value': []})
    with mocker.patch('awx.conf.models.Setting.objects.filter', return_value=from_db):
        settings = LDAPSettings()
        assert settings.CONNECTION_OPTIONS == {
            ldap.OPT_REFERRALS: 0,
            ldap.OPT_NETWORK_TIMEOUT: 30
        }


def test_ldap_filter_validator():
    validate_ldap_filter('(test-uid=%(user)s)', with_user=True)
