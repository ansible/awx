import pytest

from django.contrib.auth.models import User

from awx.sso.backends import TACACSPlusBackend
from awx.sso.models import UserEnterpriseAuth


@pytest.fixture
def tacacsplus_backend():
    return TACACSPlusBackend()


@pytest.fixture
def existing_normal_user():
    try:
        user = User.objects.get(username="alice")
    except User.DoesNotExist:
        user = User(username="alice", password="password")
        user.save()
    return user


@pytest.fixture
def existing_tacacsplus_user():
    try:
        user = User.objects.get(username="foo")
    except User.DoesNotExist:
        user = User(username="foo")
        user.set_unusable_password()
        user.save()
        enterprise_auth = UserEnterpriseAuth(user=user, provider='tacacs+')
        enterprise_auth.save()
    return user


@pytest.fixture
def ldap_configuration():
    return {
        "SERVER_URI": ["ldap://ldap06.example.com:389"],
        "BIND_DN": "cn=ldapadmin,dc=example,dc=org",
        "BIND_PASSWORD": "securepassword",
        "START_TLS": False,
        "CONNECTION_OPTIONS": {"OPT_REFERRALS": 0, "OPT_NETWORK_TIMEOUT": 30},
        "USER_SEARCH": ["ou=users,dc=example,dc=org", "SCOPE_SUBTREE", "(cn=%(user)s)"],
        "USER_DN_TEMPLATE": "cn=%(user)s,ou=users,dc=example,dc=org",
        "USER_ATTR_MAP": {"email": "mail", "last_name": "sn", "first_name": "givenName"},
        "GROUP_SEARCH": ["ou=groups,dc=example,dc=org", "SCOPE_SUBTREE", "(objectClass=groupOfNames)"],
        "GROUP_TYPE": "MemberDNGroupType",
        "GROUP_TYPE_PARAMS": {"name_attr": "cn", "member_attr": "member"},
    }


@pytest.fixture
def ldap_authenticator(ldap_configuration):
    from ansible_base.authentication.models import Authenticator

    authenticator = Authenticator.objects.create(
        name="Test LDAP Authenticator",
        enabled=True,
        create_objects=True,
        users_unique=False,
        remove_users=True,
        type="ansible_base.authentication.authenticator_plugins.ldap",
        configuration=ldap_configuration,
    )
    yield authenticator
    authenticator.delete()


@pytest.fixture
def ldap_settings():
    from ansible_base.authentication.authenticator_plugins.ldap import LDAPSettings

    data = {
        "SERVER_URI": ["ldap://ldap06.example.com:389"],
        "BIND_DN": "cn=ldapadmin,dc=example,dc=org",
        "BIND_PASSWORD": "securepassword",
        "START_TLS": False,
        "CONNECTION_OPTIONS": {"OPT_REFERRALS": 0, "OPT_NETWORK_TIMEOUT": 30},
        "USER_SEARCH": ["ou=users,dc=example,dc=org", "SCOPE_SUBTREE", "(cn=%(user)s)"],
        "USER_DN_TEMPLATE": "cn=%(user)s,ou=users,dc=example,dc=org",
        "USER_ATTR_MAP": {"email": "mail", "last_name": "sn", "first_name": "givenName"},
        "GROUP_SEARCH": ["ou=groups,dc=example,dc=org", "SCOPE_SUBTREE", "(objectClass=groupOfNames)"],
        "GROUP_TYPE": "MemberDNGroupType",
        "GROUP_TYPE_PARAMS": {"name_attr": "cn", "member_attr": "member"},
    }
    settings = LDAPSettings(defaults=data)
    return settings
