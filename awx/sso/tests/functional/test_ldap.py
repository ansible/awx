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


@pytest.mark.parametrize(
    'setting',
    [
        'USER_DN_TEMPLATE',
        'REQUIRE_GROUP',
        'DENY_GROUP',
    ],
)
@pytest.mark.django_db
def test_empty_ldap_dn(ldap_settings, setting):
    setattr(ldap_settings, setting, '')
    assert getattr(ldap_settings, setting) is ''

    setattr(ldap_settings, setting, None)
    assert getattr(ldap_settings, setting) is None


@pytest.mark.skip(reason='still a TODO in DAB')
@pytest.mark.django_db
@pytest.mark.parametrize(
    'value',
    [
        None,
        '',
        'INVALID',
        1,
        [1],
        ['INVALID'],
    ],
)
def test_ldap_user_flags_by_group_invalid_dn(value, ldap_settings):
    # should fail when implemented but currently isn't validated
    pass


@pytest.mark.django_db
def test_ldap_user_flags_by_group_string(ldap_settings):
    expected = "cn=ldapadmin,dc=example,dc=org"
    setattr(ldap_settings, 'USER_FLAGS_BY_GROUP', {'is_superuser': expected})
    assert getattr(ldap_settings, 'USER_FLAGS_BY_GROUP') == {'is_superuser': expected}


@pytest.mark.django_db
def test_ldap_user_flags_by_group_list(ldap_settings):
    expected = ['CN=Admins,OU=Groups,DC=example,DC=com', 'CN=Superadmins,OU=Groups,DC=example,DC=com']
    setattr(ldap_settings, 'USER_FLAGS_BY_GROUP', {'is_superuser': expected})
    assert getattr(ldap_settings, 'USER_FLAGS_BY_GROUP') == {'is_superuser': expected}
