import pytest

from rest_framework.exceptions import ValidationError

from awx.sso.fields import SAMLOrgAttrField, SAMLTeamAttrField, SAMLUserFlagsAttrField


class TestSAMLOrgAttrField:
    @pytest.mark.parametrize(
        "data, expected",
        [
            ({}, {}),
            ({'remove': True, 'saml_attr': 'foobar'}, {'remove': True, 'saml_attr': 'foobar'}),
            ({'remove': True, 'saml_attr': 1234}, {'remove': True, 'saml_attr': '1234'}),
            ({'remove': True, 'saml_attr': 3.14}, {'remove': True, 'saml_attr': '3.14'}),
            ({'saml_attr': 'foobar'}, {'saml_attr': 'foobar'}),
            ({'remove': True}, {'remove': True}),
            ({'remove': True, 'saml_admin_attr': 'foobar'}, {'remove': True, 'saml_admin_attr': 'foobar'}),
            ({'saml_admin_attr': 'foobar'}, {'saml_admin_attr': 'foobar'}),
            ({'remove_admins': True, 'saml_admin_attr': 'foobar'}, {'remove_admins': True, 'saml_admin_attr': 'foobar'}),
            (
                {'remove': True, 'saml_attr': 'foo', 'remove_admins': True, 'saml_admin_attr': 'bar'},
                {'remove': True, 'saml_attr': 'foo', 'remove_admins': True, 'saml_admin_attr': 'bar'},
            ),
        ],
    )
    def test_internal_value_valid(self, data, expected):
        field = SAMLOrgAttrField()
        res = field.to_internal_value(data)
        assert res == expected

    @pytest.mark.parametrize(
        "data, expected",
        [
            ({'remove': 'blah', 'saml_attr': 'foobar'}, {'remove': ['Must be a valid boolean.']}),
            ({'remove': True, 'saml_attr': False}, {'saml_attr': ['Not a valid string.']}),
            (
                {'remove': True, 'saml_attr': False, 'foo': 'bar', 'gig': 'ity'},
                {'saml_attr': ['Not a valid string.'], 'foo': ['Invalid field.'], 'gig': ['Invalid field.']},
            ),
            ({'remove_admins': True, 'saml_admin_attr': False}, {'saml_admin_attr': ['Not a valid string.']}),
            ({'remove_admins': 'blah', 'saml_admin_attr': 'foobar'}, {'remove_admins': ['Must be a valid boolean.']}),
        ],
    )
    def test_internal_value_invalid(self, data, expected):
        field = SAMLOrgAttrField()
        with pytest.raises(ValidationError) as e:
            field.to_internal_value(data)
        assert e.value.detail == expected


class TestSAMLTeamAttrField:
    @pytest.mark.parametrize(
        "data",
        [
            {},
            {'remove': True, 'saml_attr': 'foobar', 'team_org_map': []},
            {'remove': True, 'saml_attr': 'foobar', 'team_org_map': [{'team': 'Engineering', 'organization': 'Ansible'}]},
            {
                'remove': True,
                'saml_attr': 'foobar',
                'team_org_map': [
                    {'team': 'Engineering', 'organization': 'Ansible'},
                    {'team': 'Engineering', 'organization': 'Ansible2'},
                    {'team': 'Engineering2', 'organization': 'Ansible'},
                ],
            },
            {
                'remove': True,
                'saml_attr': 'foobar',
                'team_org_map': [
                    {'team': 'Engineering', 'organization': 'Ansible'},
                    {'team': 'Engineering', 'organization': 'Ansible2'},
                    {'team': 'Engineering2', 'organization': 'Ansible'},
                ],
            },
            {
                'remove': True,
                'saml_attr': 'foobar',
                'team_org_map': [
                    {'team': 'Engineering', 'team_alias': 'Engineering Team', 'organization': 'Ansible'},
                    {'team': 'Engineering', 'organization': 'Ansible2'},
                    {'team': 'Engineering2', 'organization': 'Ansible'},
                ],
            },
        ],
    )
    def test_internal_value_valid(self, data):
        field = SAMLTeamAttrField()
        res = field.to_internal_value(data)
        assert res == data

    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {'remove': True, 'saml_attr': 'foobar', 'team_org_map': [{'team': 'foobar', 'not_a_valid_key': 'blah', 'organization': 'Ansible'}]},
                {'team_org_map': {0: {'not_a_valid_key': ['Invalid field.']}}},
            ),
            (
                {'remove': False, 'saml_attr': 'foobar', 'team_org_map': [{'organization': 'Ansible'}]},
                {'team_org_map': {0: {'team': ['This field is required.']}}},
            ),
            (
                {'remove': False, 'saml_attr': 'foobar', 'team_org_map': [{}]},
                {'team_org_map': {0: {'organization': ['This field is required.'], 'team': ['This field is required.']}}},
            ),
        ],
    )
    def test_internal_value_invalid(self, data, expected):
        field = SAMLTeamAttrField()
        with pytest.raises(ValidationError) as e:
            field.to_internal_value(data)
        assert e.value.detail == expected


class TestSAMLUserFlagsAttrField:
    @pytest.mark.parametrize(
        "data",
        [
            {},
            {'is_superuser_attr': 'something'},
            {'is_superuser_value': ['value']},
            {'is_superuser_role': ['my_peeps']},
            {'remove_superusers': False},
            {'is_system_auditor_attr': 'something_else'},
            {'is_system_auditor_value': ['value2']},
            {'is_system_auditor_role': ['other_peeps']},
            {'remove_system_auditors': False},
        ],
    )
    def test_internal_value_valid(self, data):
        field = SAMLUserFlagsAttrField()
        res = field.to_internal_value(data)
        assert res == data

    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {
                    'junk': 'something',
                    'is_superuser_value': 'value',
                    'is_superuser_role': 'my_peeps',
                    'is_system_auditor_attr': 'else',
                    'is_system_auditor_value': 'value2',
                    'is_system_auditor_role': 'other_peeps',
                },
                {
                    'junk': ['Invalid field.'],
                    'is_superuser_role': ['Expected a list of items but got type "str".'],
                    'is_superuser_value': ['Expected a list of items but got type "str".'],
                    'is_system_auditor_role': ['Expected a list of items but got type "str".'],
                    'is_system_auditor_value': ['Expected a list of items but got type "str".'],
                },
            ),
            (
                {
                    'junk': 'something',
                },
                {
                    'junk': ['Invalid field.'],
                },
            ),
            (
                {
                    'junk': 'something',
                    'junk2': 'else',
                },
                {
                    'junk': ['Invalid field.'],
                    'junk2': ['Invalid field.'],
                },
            ),
            # make sure we can't pass a string to the boolean fields
            (
                {
                    'remove_superusers': 'test',
                    'remove_system_auditors': 'test',
                },
                {
                    "remove_superusers": ["Must be a valid boolean."],
                    "remove_system_auditors": ["Must be a valid boolean."],
                },
            ),
        ],
    )
    def test_internal_value_invalid(self, data, expected):
        field = SAMLUserFlagsAttrField()
        with pytest.raises(ValidationError) as e:
            field.to_internal_value(data)
        print(e.value.detail)
        assert e.value.detail == expected
