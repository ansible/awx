
import pytest

from rest_framework.exceptions import ValidationError

from awx.sso.fields import (
    SAMLOrgAttrField,
    SAMLTeamAttrField,
)


class TestSAMLOrgAttrField():

    @pytest.mark.parametrize("data, expected", [
        ({}, {}),
        ({'remove': True, 'saml_attr': 'foobar'}, {'remove': True, 'saml_attr': 'foobar'}),
        ({'remove': True, 'saml_attr': 1234}, {'remove': True, 'saml_attr': '1234'}),
        ({'remove': True, 'saml_attr': 3.14}, {'remove': True, 'saml_attr': '3.14'}),
        ({'saml_attr': 'foobar'}, {'saml_attr': 'foobar'}),
        ({'remove': True}, {'remove': True}),
    ])
    def test_internal_value_valid(self, data, expected):
        field = SAMLOrgAttrField()
        res = field.to_internal_value(data)
        assert res == expected

    @pytest.mark.parametrize("data, expected", [
        ({'remove': 'blah', 'saml_attr': 'foobar'},
            ValidationError('"blah" is not a valid boolean.')),
        ({'remove': True, 'saml_attr': False},
            ValidationError('Not a valid string.')),
        ({'remove': True, 'saml_attr': False, 'foo': 'bar', 'gig': 'ity'},
            ValidationError('Invalid key(s): "gig", "foo".')),
    ])
    def test_internal_value_invalid(self, data, expected):
        field = SAMLOrgAttrField()
        with pytest.raises(type(expected)) as e:
            field.to_internal_value(data)
        assert str(e.value) == str(expected)


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
        ]}, ValidationError('Invalid key(s): "not_a_valid_key".')),
        ({'remove': False, 'saml_attr': 'foobar', 'team_org_map': [
            {'organization': 'Ansible'},
        ]}, ValidationError('Missing key(s): "team".')),
        ({'remove': False, 'saml_attr': 'foobar', 'team_org_map': [
            {},
        ]}, ValidationError('Missing key(s): "organization", "team".')),
    ])
    def test_internal_value_invalid(self, data, expected):
        field = SAMLTeamAttrField()
        with pytest.raises(type(expected)) as e:
            field.to_internal_value(data)
        assert str(e.value) == str(expected)

