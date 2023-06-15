import pytest
import re

from django.test.utils import override_settings
from awx.main.models import User, Organization, Team
from awx.sso.social_oidc_pipeline import (
    _update_user_orgs_by_scope,
    _update_user_teams_by_scope,
    _set_flag,
)

# from unittest import mock
# from django.utils.timezone import now
# , Credential, CredentialType


@pytest.fixture
def users():
    u1 = User.objects.create(username='user1@foo.com', last_name='foo', first_name='bar', email='user1@foo.com')
    u2 = User.objects.create(username='user2@foo.com', last_name='foo', first_name='bar', email='user2@foo.com')
    u3 = User.objects.create(username='user3@foo.com', last_name='foo', first_name='bar', email='user3@foo.com')
    return (u1, u2, u3)


@pytest.mark.django_db
class TestAzureADPopulateUser:
    # The main populate_user does not need to be tested since its just a conglomeration of other functions that we test
    # This test is here in case someone alters the code in the future in a way that does require testing
    def test_populate_user(self):
        assert True


@pytest.mark.django_db
class TestAzureADScopeMaps:
    @pytest.fixture
    def backend(self):
        class Backend:
            s = {
                'ORGANIZATION_MAP': {
                    'Default1': {
                        'remove': True,
                        'admins': 'foobar',
                        'remove_admins': True,
                        'users': 'foo',
                        'remove_users': True,
                        'organization_alias': 'o1_alias',
                    }
                }
            }

            def setting(self, key):
                return self.s[key]

        return Backend()

    @pytest.mark.parametrize(
        "setting, expected_state, expected_orgs_to_create",
        [
            (
                # Default test, make sure that our roles get applied and removed as specified (with an alias)
                {
                    "org_map": [
                        {
                            "organization": "Default1",
                        },
                        {
                            "organization": "Default2",
                        },
                        {
                            "organization": "Default3",
                        },
                        {
                            "organization": "Default4",
                        },
                    ]
                },
                {
                    'Default2': {'member_role': True},
                    'Default3': {'admin_role': True},
                    'Default4': {'auditor_role': True},
                    'o1_alias': {'member_role': True},
                    'Rando1': {'admin_role': False, 'auditor_role': False, 'member_role': False},
                },
                [
                    'o1_alias',
                    'Default2',
                    'Default3',
                    'Default4',
                ],
            ),
            (
                # Similar test, we are just going to override the values "coming from the IdP" to limit the teams
                {
                    'social_auth_member_scope': 'roles',
                    'social_auth_admin_scope': 'groups',
                    'social_auth_auditor_scope': 'groups',
                    "org_map": [
                        {
                            "organization": "Default1",
                        },
                        {
                            "organization": "Default2",
                        },
                        {
                            "organization": "Default3",
                        },
                        {
                            "organization": "Default4",
                        },
                    ],
                },
                {
                    'Default2': {'member_role': True},
                    'Default3': {'admin_role': True},
                    'Default4': {'auditor_role': True},
                    'o1_alias': {'member_role': True},
                    'Rando1': {'admin_role': False, 'auditor_role': False, 'member_role': False},
                },
                [
                    'o1_alias',
                    'Default2',
                    'Default3',
                    'Default4',
                ],
            ),
            (
                # Test to make sure the remove logic is working
                {
                    'remove_members': False,
                    'remove_admins': False,
                    'remove_auditors': False,
                    "org_map": [
                        {
                            "organization": "Default2",
                        },
                        {
                            "organization": "Default3",
                        },
                        {
                            "organization": "Default4",
                        },
                        {
                            "organization": "o1_alias",
                        },
                    ],
                },
                {
                    'Default2': {'member_role': True},
                    'Default3': {'admin_role': True},
                    'Default4': {'auditor_role': True},
                    'o1_alias': {'member_role': True},
                },
                [
                    'Default2',
                    'Default3',
                    'Default4',
                    'o1_alias',
                ],
            ),
        ],
    )
    def test__update_user_orgs_by_azuread_oauth_scope(self, backend, setting, expected_state, expected_orgs_to_create):
        kwargs = {
            'name': 'Chris',
            'family_name': 'Meyers',
            'given_name': 'Chris Meyers',
            'upn': 'cmeyers@redhat.com',
            'response': {
                'roles': [
                    "ORG_DEFAULT1_MEMBER",
                    "ORG_DEFAULT2_MEMBER",
                    "ORG_DEFAULT3_ADMIN",
                    "ORG_DEFAULT4_AUDITOR",
                    "ORG_O1_ALIAS_MEMBER",
                ],
                'groups': ["ORG_DEFAULT3_ADMIN", "ORG_DEFAULT4_AUDITOR"],
            },
        }

        # Create a random organization in the database for testing
        Organization.objects.create(name='Rando1')

        with override_settings(SOCIAL_AUTH_OIDC_ORGANIZATION_REMOTE_MAP=setting):
            desired_org_state = {}
            orgs_to_create = []
            _update_user_orgs_by_scope(backend, desired_org_state, orgs_to_create, **kwargs)
            assert desired_org_state == expected_state
            assert orgs_to_create == expected_orgs_to_create

    @pytest.mark.parametrize(
        "setting, expected_team_state, expected_teams_to_create",
        [
            (
                {
                    'remove_members': False,
                    'team_org_map': [
                        {'team': 'Blue', 'organization': 'Default1'},
                        {'team': 'Blue', 'organization': 'Default2'},
                        {'team': 'Blue', 'organization': 'Default3'},
                        {'team': 'Red', 'organization': 'Default1'},
                        {'team': 'Green', 'organization': 'Default1'},
                        {'team': 'Green', 'organization': 'Default3'},
                        {'team': 'Yellow', 'organization': 'Default4'},
                    ],
                },
                {
                    'Default1': {
                        'Blue': {'member_role': True},
                        'Green': {'member_role': True},
                        'Red': {'member_role': True},
                    },
                    'Default2': {
                        'Blue': {'member_role': True},
                    },
                    'Default3': {
                        'Blue': {'member_role': True},
                        'Green': {'member_role': True},
                    },
                    'Default4': {
                        'Yellow': {'member_role': False},
                    },
                },
                {
                    'Blue': 'Default3',
                    'Red': 'Default1',
                    'Green': 'Default3',
                },
            ),
            (
                {
                    'social_auth_member_scope': 'groups',
                    'team_org_map': [
                        {'team': 'Blue', 'organization': 'Default1'},
                        {'team': 'Blue', 'organization': 'Default2'},
                        {'team': 'Blue', 'organization': 'Default3'},
                        {'team': 'Red', 'organization': 'Default1'},
                        {'team': 'Green', 'organization': 'Default1'},
                        {'team': 'Green', 'organization': 'Default3'},
                        {'team': 'Yellow', 'organization': 'Default4'},
                    ],
                },
                {
                    'Default1': {
                        'Blue': {'member_role': True},
                        'Green': {'member_role': False},
                        'Red': {'member_role': True},
                    },
                    'Default2': {
                        'Blue': {'member_role': True},
                    },
                    'Default3': {
                        'Blue': {'member_role': True},
                        'Green': {'member_role': False},
                    },
                    'Default4': {
                        'Yellow': {'member_role': False},
                    },
                    'Rando1': {
                        'Rando1': {'member_role': False},
                    },
                },
                {
                    'Blue': 'Default3',
                    'Red': 'Default1',
                },
            ),
            (
                {
                    'team_org_map': [
                        {'team': 'Blue', 'organization': 'Default1', 'social_auth_member_value': 'ALTERED_BLUE_DEFAULT1'},
                        {'team': 'Blue', 'organization': 'Default2', 'social_auth_member_value': 'ALTERED_BLUE_DEFAULT2'},
                        {'team': 'Blue', 'organization': 'Default3', 'social_auth_member_value': 'ALTERED_BLUE_DEFAULT3'},
                        {'team': 'Red', 'organization': 'Default1', 'social_auth_member_value': 'ALTERED_RED_DEFAULT1'},
                        {'team': 'Green', 'organization': 'Default1', 'social_auth_member_value': 'ALTERED_GREEN_DEFAULT1'},
                        {'team': 'Green', 'organization': 'Default3', 'social_auth_member_value': 'ALTERED_GREEN_DEFAULT3'},
                        {'team': 'Yellow', 'organization': 'Default4', 'social_auth_member_value': 'ALTERED_YELLOW_DEFAULT4'},
                    ],
                },
                {
                    'Default1': {
                        'Blue': {'member_role': False},
                        'Green': {'member_role': True},
                        'Red': {'member_role': False},
                    },
                    'Default2': {
                        'Blue': {'member_role': False},
                    },
                    'Default3': {
                        'Blue': {'member_role': False},
                        'Green': {'member_role': True},
                    },
                    'Default4': {
                        'Yellow': {'member_role': False},
                    },
                    'Rando1': {
                        'Rando1': {'member_role': False},
                    },
                },
                {
                    'Green': 'Default3',
                },
            ),
        ],
    )
    def test__update_user_teams_by_azuread_oauth_scope(self, setting, expected_team_state, expected_teams_to_create):
        kwargs = {
            'name': 'Chris',
            'family_name': 'Meyers',
            'given_name': 'Chris Meyers',
            'upn': 'cmeyers@redhat.com',
            'response': {
                'roles': [
                    "TEAM_BLUE_DEFAULT1_MEMBER",
                    "TEAM_GREEN_DEFAULT1_MEMBER",
                    "TEAM_RED_DEFAULT1_MEMBER",
                    "TEAM_BLUE_DEFAULT2_MEMBER",
                    "TEAM_BLUE_DEFAULT3_MEMBER",
                    "TEAM_GREEN_DEFAULT3_MEMBER",
                    "ALTERED_GREEN_DEFAULT1",
                    "ALTERED_GREEN_DEFAULT3",
                ],
                'groups': ["TEAM_BLUE_DEFAULT1_MEMBER", "TEAM_RED_DEFAULT1_MEMBER", "TEAM_BLUE_DEFAULT2_MEMBER", "TEAM_BLUE_DEFAULT3_MEMBER"],
            },
        }

        o = Organization.objects.create(name='Rando1')
        Team.objects.create(name='Rando1', organization_id=o.id)

        with override_settings(SOCIAL_AUTH_OIDC_TEAM_REMOTE_MAP=setting):
            desired_team_state = {}
            teams_to_create = {}
            _update_user_teams_by_scope(desired_team_state, teams_to_create, **kwargs)
            assert desired_team_state == expected_team_state
            assert teams_to_create == expected_teams_to_create


@pytest.mark.django_db
class TestAzureADUserFlags:
    @pytest.mark.parametrize(
        "response, user_flags_settings, expected",
        [
            # No value set for the roles
            (
                {
                    'roles': [
                        "SUPERADMIN",
                        "AUDITOR",
                    ],
                },
                {},
                {'superuser': (False, False), 'system_auditor': (False, False)},
            ),
            (
                {
                    'roles': [
                        "SUPERADMIN",
                        "SYSTEM_AUDITOR",
                    ],
                },
                {
                    "is_superuser_value": "SUPERADMIN",
                    "is_system_auditor_value": "SYSTEM_AUDITOR",
                },
                {'superuser': (False, True), 'system_auditor': (False, True)},
            ),
            (
                {
                    'roles': [
                        "SUPERADMIN",
                        "SYSTEM_AUDITOR",
                    ],
                },
                {
                    "is_superuser_value": "SUPERADMIN",
                    "is_system_auditor_value": "SYSTEM_AUDITOR",
                },
                {'superuser': (True, True), 'system_auditor': (True, True)},
            ),
            (
                {
                    'roles': [
                        "SUPERADMIN",
                        "SYSTEM_AUDITOR",
                    ],
                },
                {"remove_superusers": False, "remove_system_auditors": False},
                {'superuser': (True, True), 'system_auditor': (True, True)},
            ),
        ],
    )
    def test__set_flag(self, response, user_flags_settings, expected):
        user = User()
        user.username = 'John'

        with override_settings(SOCIAL_AUTH_OIDC_USER_FLAGS_REMOTE_MAP=user_flags_settings):
            for flag, result in expected.items():
                setattr(user, f"is_{flag}", result[0])
                _set_flag(user, response, flag)
                assert result[1] == getattr(user, f"is_{flag}")
