import pytest
from unittest import mock

from rest_framework.exceptions import ValidationError

from awx.sso.fields import LDAPGroupTypeParamsField, LDAPServerURIField


class TestLDAPGroupTypeParamsField:
    @pytest.mark.parametrize(
        "group_type, data, expected",
        [
            ('LDAPGroupType', {'name_attr': 'user', 'bob': ['a', 'b'], 'scooter': 'hello'}, ['Invalid key(s): "bob", "scooter".']),
            ('MemberDNGroupType', {'name_attr': 'user', 'member_attr': 'west', 'bob': ['a', 'b'], 'scooter': 'hello'}, ['Invalid key(s): "bob", "scooter".']),
            (
                'PosixUIDGroupType',
                {'name_attr': 'user', 'member_attr': 'west', 'ldap_group_user_attr': 'legacyThing', 'bob': ['a', 'b'], 'scooter': 'hello'},
                ['Invalid key(s): "bob", "member_attr", "scooter".'],
            ),
        ],
    )
    def test_internal_value_invalid(self, group_type, data, expected):
        field = LDAPGroupTypeParamsField()
        field.get_depends_on = mock.MagicMock(return_value=group_type)

        with pytest.raises(ValidationError) as e:
            field.to_internal_value(data)
        assert e.value.detail == expected


class TestLDAPServerURIField:
    @pytest.mark.parametrize(
        "ldap_uri, exception, expected",
        [
            (r'ldap://servername.com:444', None, r'ldap://servername.com:444'),
            (r'ldap://servername.so3:444', None, r'ldap://servername.so3:444'),
            (r'ldaps://servername3.s300:344', None, r'ldaps://servername3.s300:344'),
            (r'ldap://servername.-so3:444', ValidationError, None),
        ],
    )
    def test_run_validators_valid(self, ldap_uri, exception, expected):
        field = LDAPServerURIField()
        if exception is None:
            assert field.run_validators(ldap_uri) == expected
        else:
            with pytest.raises(exception):
                field.run_validators(ldap_uri)
