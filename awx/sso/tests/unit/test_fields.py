
import pytest
from unittest import mock

from rest_framework.exceptions import ValidationError

from awx.sso.fields import (
    SAMLOrgAttrField,
    SAMLTeamAttrField,
    LDAPGroupTypeParamsField,
    LDAPServerURIField
)


class TestSAMLOrgAttrField():

    @pytest.mark.parametrize("data, expected", [
        ({}, {}),
        ({'remove': True, 'saml_attr': 'foobar'}, {'remove': True, 'saml_attr': 'foobar'}),
        ({'remove': True, 'saml_attr': 1234}, {'remove': True, 'saml_attr': '1234'}),
        ({'remove': True, 'saml_attr': 3.14}, {'remove': True, 'saml_attr': '3.14'}),
        ({'saml_attr': 'foobar'}, {'saml_attr': 'foobar'}),
        ({'remove': True}, {'remove': True}),
        ({'remove': True, 'saml_admin_attr': 'foobar'}, {'remove': True, 'saml_admin_attr': 'foobar'}),
        ({'saml_admin_attr': 'foobar'}, {'saml_admin_attr': 'foobar'}),
        ({'remove_admins': True, 'saml_admin_attr': 'foobar'}, {'remove_admins': True, 'saml_admin_attr': 'foobar'}),
        ({'remove': True, 'saml_attr': 'foo', 'remove_admins': True, 'saml_admin_attr': 'bar'},
            {'remove': True, 'saml_attr': 'foo', 'remove_admins': True, 'saml_admin_attr': 'bar'}),
    ])
    def test_internal_value_valid(self, data, expected):
        field = SAMLOrgAttrField()
        res = field.to_internal_value(data)
        assert res == expected

    @pytest.mark.parametrize("data, expected", [
        ({'remove': 'blah', 'saml_attr': 'foobar'},
            {'remove': ['Must be a valid boolean.']}),
        ({'remove': True, 'saml_attr': False},
            {'saml_attr': ['Not a valid string.']}),
        ({'remove': True, 'saml_attr': False, 'foo': 'bar', 'gig': 'ity'},
            {'saml_attr': ['Not a valid string.'],
             'foo': ['Invalid field.'],
             'gig': ['Invalid field.']}),
        ({'remove_admins': True, 'saml_admin_attr': False},
            {'saml_admin_attr': ['Not a valid string.']}),
        ({'remove_admins': 'blah', 'saml_admin_attr': 'foobar'},
            {'remove_admins': ['Must be a valid boolean.']}),
    ])
    def test_internal_value_invalid(self, data, expected):
        field = SAMLOrgAttrField()
        with pytest.raises(ValidationError) as e:
            field.to_internal_value(data)
        assert e.value.detail == expected


class TestSAMLTeamAttrField():

    @pytest.mark.parametrize("data", [
        {},
        {'remove': True, 'saml_attr': 'foobar', 'team_org_map': []},
        {'remove': True, 'saml_attr': 'foobar', 'team_org_map': [
            {'team': 'Engineering', 'organization': 'Ansible'}
        ]},
        {'remove': True, 'saml_attr': 'foobar', 'team_org_map': [
            {'team': 'Engineering', 'organization': 'Ansible'},
            {'team': 'Engineering', 'organization': 'Ansible2'},
            {'team': 'Engineering2', 'organization': 'Ansible'},
        ]},
        {'remove': True, 'saml_attr': 'foobar', 'team_org_map': [
            {'team': 'Engineering', 'organization': 'Ansible'},
            {'team': 'Engineering', 'organization': 'Ansible2'},
            {'team': 'Engineering2', 'organization': 'Ansible'},
        ]},
    ])
    def test_internal_value_valid(self, data):
        field = SAMLTeamAttrField()
        res = field.to_internal_value(data)
        assert res == data

    @pytest.mark.parametrize("data, expected", [
        ({'remove': True, 'saml_attr': 'foobar', 'team_org_map': [
            {'team': 'foobar', 'not_a_valid_key': 'blah', 'organization': 'Ansible'},
        ]}, {'team_org_map': {0: {'not_a_valid_key': ['Invalid field.']}}}),
        ({'remove': False, 'saml_attr': 'foobar', 'team_org_map': [
            {'organization': 'Ansible'},
        ]}, {'team_org_map': {0: {'team': ['This field is required.']}}}),
        ({'remove': False, 'saml_attr': 'foobar', 'team_org_map': [
            {},
        ]}, {'team_org_map': {
            0: {'organization': ['This field is required.'],
                'team': ['This field is required.']}}}),
    ])
    def test_internal_value_invalid(self, data, expected):
        field = SAMLTeamAttrField()
        with pytest.raises(ValidationError) as e:
            field.to_internal_value(data)
        assert e.value.detail == expected


class TestLDAPGroupTypeParamsField():

    @pytest.mark.parametrize("group_type, data, expected", [
        ('LDAPGroupType', {'name_attr': 'user', 'bob': ['a', 'b'], 'scooter': 'hello'},
         ['Invalid key(s): "bob", "scooter".']),
        ('MemberDNGroupType', {'name_attr': 'user', 'member_attr': 'west', 'bob': ['a', 'b'], 'scooter': 'hello'},
         ['Invalid key(s): "bob", "scooter".']),
        ('PosixUIDGroupType', {'name_attr': 'user', 'member_attr': 'west', 'ldap_group_user_attr': 'legacyThing',
         'bob': ['a', 'b'], 'scooter': 'hello'},
         ['Invalid key(s): "bob", "member_attr", "scooter".']),
    ])
    def test_internal_value_invalid(self, group_type, data, expected):
        field = LDAPGroupTypeParamsField()
        field.get_depends_on = mock.MagicMock(return_value=group_type)

        with pytest.raises(ValidationError) as e:
            field.to_internal_value(data)
        assert e.value.detail == expected


class TestLDAPServerURIField():

    valid_URIs = [
        r'ldap://servername.so3:444',
        r'ldaps://servername3.s300:344'
    ]

    invalid_URIs = [
        r'lpads://servername.-so3:444'
    ]

    def test_run_validators(self):
        field = LDAPServerURIField()
        for valid_uri in TestLDAPServerURIField.valid_URIs:
            assert field.run_validators(valid_uri) == valid_uri
        for invalid_uri in TestLDAPServerURIField.invalid_URIs:
            with pytest.raises(ValidationError):
                field.run_validators(invalid_uri)
