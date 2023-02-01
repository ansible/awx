import pytest
import re

from django.test.utils import override_settings
from awx.main.models import User, Organization, Team
from awx.sso.saml_pipeline import (
    _update_m2m_from_expression,
    _update_user_orgs,
    _update_user_teams,
    _update_user_orgs_by_saml_attr,
    _update_user_teams_by_saml_attr,
    _check_flag,
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
class TestSAMLPopulateUser:
    # The main populate_user does not need to be tested since its just a conglomeration of other functions that we test
    # This test is here in case someone alters the code in the future in a way that does require testing
    def test_populate_user(self):
        assert True


@pytest.mark.django_db
class TestSAMLSimpleMaps:
    # This tests __update_user_orgs and __update_user_teams
    @pytest.fixture
    def backend(self):
        class Backend:
            s = {
                'ORGANIZATION_MAP': {
                    'Default': {
                        'remove': True,
                        'admins': 'foobar',
                        'remove_admins': True,
                        'users': 'foo',
                        'remove_users': True,
                        'organization_alias': '',
                    }
                },
                'TEAM_MAP': {'Blue': {'organization': 'Default', 'remove': True, 'users': ''}, 'Red': {'organization': 'Default', 'remove': True, 'users': ''}},
            }

            def setting(self, key):
                return self.s[key]

        return Backend()

    def test__update_user_orgs(self, backend, users):
        u1, u2, u3 = users

        # Test user membership logic with regular expressions
        backend.setting('ORGANIZATION_MAP')['Default']['admins'] = re.compile('.*')
        backend.setting('ORGANIZATION_MAP')['Default']['users'] = re.compile('.*')

        desired_org_state = {}
        orgs_to_create = []
        _update_user_orgs(backend, desired_org_state, orgs_to_create, u1)
        _update_user_orgs(backend, desired_org_state, orgs_to_create, u2)
        _update_user_orgs(backend, desired_org_state, orgs_to_create, u3)

        assert desired_org_state == {'Default': {'member_role': True, 'admin_role': True, 'auditor_role': False}}
        assert orgs_to_create == ['Default']

        # Test remove feature enabled
        backend.setting('ORGANIZATION_MAP')['Default']['admins'] = ''
        backend.setting('ORGANIZATION_MAP')['Default']['users'] = ''
        backend.setting('ORGANIZATION_MAP')['Default']['remove_admins'] = True
        backend.setting('ORGANIZATION_MAP')['Default']['remove_users'] = True
        desired_org_state = {}
        orgs_to_create = []
        _update_user_orgs(backend, desired_org_state, orgs_to_create, u1)
        assert desired_org_state == {'Default': {'member_role': False, 'admin_role': False, 'auditor_role': False}}
        assert orgs_to_create == ['Default']

        # Test remove feature disabled
        backend.setting('ORGANIZATION_MAP')['Default']['remove_admins'] = False
        backend.setting('ORGANIZATION_MAP')['Default']['remove_users'] = False
        desired_org_state = {}
        orgs_to_create = []
        _update_user_orgs(backend, desired_org_state, orgs_to_create, u2)

        assert desired_org_state == {'Default': {'member_role': None, 'admin_role': None, 'auditor_role': False}}
        assert orgs_to_create == ['Default']

        # Test organization alias feature
        backend.setting('ORGANIZATION_MAP')['Default']['organization_alias'] = 'Default_Alias'
        orgs_to_create = []
        _update_user_orgs(backend, {}, orgs_to_create, u1)
        assert orgs_to_create == ['Default_Alias']

    def test__update_user_teams(self, backend, users):
        u1, u2, u3 = users

        # Test user membership logic with regular expressions
        backend.setting('TEAM_MAP')['Blue']['users'] = re.compile('.*')
        backend.setting('TEAM_MAP')['Red']['users'] = re.compile('.*')

        desired_team_state = {}
        teams_to_create = {}
        _update_user_teams(backend, desired_team_state, teams_to_create, u1)
        assert teams_to_create == {'Red': 'Default', 'Blue': 'Default'}
        assert desired_team_state == {'Default': {'Blue': {'member_role': True}, 'Red': {'member_role': True}}}

        # Test remove feature enabled
        backend.setting('TEAM_MAP')['Blue']['remove'] = True
        backend.setting('TEAM_MAP')['Red']['remove'] = True
        backend.setting('TEAM_MAP')['Blue']['users'] = ''
        backend.setting('TEAM_MAP')['Red']['users'] = ''

        desired_team_state = {}
        teams_to_create = {}
        _update_user_teams(backend, desired_team_state, teams_to_create, u1)
        assert teams_to_create == {'Red': 'Default', 'Blue': 'Default'}
        assert desired_team_state == {'Default': {'Blue': {'member_role': False}, 'Red': {'member_role': False}}}

        # Test remove feature disabled
        backend.setting('TEAM_MAP')['Blue']['remove'] = False
        backend.setting('TEAM_MAP')['Red']['remove'] = False

        desired_team_state = {}
        teams_to_create = {}
        _update_user_teams(backend, desired_team_state, teams_to_create, u2)
        assert teams_to_create == {'Red': 'Default', 'Blue': 'Default'}
        # If we don't care about team memberships we just don't add them to the hash so this would be an empty hash
        assert desired_team_state == {}


@pytest.mark.django_db
class TestSAMLM2M:
    @pytest.mark.parametrize(
        "expression, remove, expected_return",
        [
            # No expression with no remove
            (None, False, None),
            ("", False, None),
            # No expression with remove
            (None, True, False),
            # True expression with and without remove
            (True, False, True),
            (True, True, True),
            # Single string matching the user name
            ("user1", False, True),
            # Single string matching the user email
            ("user1@foo.com", False, True),
            # Single string not matching username or email, no remove
            ("user27", False, None),
            # Single string not matching username or email, with remove
            ("user27", True, False),
            # Same tests with arrays instead of strings
            (["user1"], False, True),
            (["user1@foo.com"], False, True),
            (["user27"], False, None),
            (["user27"], True, False),
            # Arrays with nothing matching
            (["user27", "user28"], False, None),
            (["user27", "user28"], True, False),
            # Arrays with all matches
            (["user1", "user1@foo.com"], False, True),
            # Arrays with some match, some not
            (["user1", "user28", "user27"], False, True),
            #
            # Note: For RE's, usually settings takes care of the compilation for us, so we have to do it manually for testing.
            #       we also need to remove any / or flags for the compile to happen
            #
            # Matching username regex non-array
            (re.compile("^user.*"), False, True),
            (re.compile("^user.*"), True, True),
            # Matching email regex non-array
            (re.compile(".*@foo.com$"), False, True),
            (re.compile(".*@foo.com$"), True, True),
            # Non-array not matching username or email
            (re.compile("^$"), False, None),
            (re.compile("^$"), True, False),
            # All re tests just in array form
            ([re.compile("^user.*")], False, True),
            ([re.compile("^user.*")], True, True),
            ([re.compile(".*@foo.com$")], False, True),
            ([re.compile(".*@foo.com$")], True, True),
            ([re.compile("^$")], False, None),
            ([re.compile("^$")], True, False),
            # An re with username matching but not email
            ([re.compile("^user.*"), re.compile(".*@bar.com$")], False, True),
            # An re with email matching but not username
            ([re.compile("^user27$"), re.compile(".*@foo.com$")], False, True),
            # An re array with no matching
            ([re.compile("^user27$"), re.compile(".*@bar.com$")], False, None),
            ([re.compile("^user27$"), re.compile(".*@bar.com$")], True, False),
            #
            # A mix of re and strings
            #
            # String matches, re does not
            (["user1", re.compile(".*@bar.com$")], False, True),
            # String does not match, re does
            (["user27", re.compile(".*@foo.com$")], False, True),
            # Nothing matches
            (["user27", re.compile(".*@bar.com$")], False, None),
            (["user27", re.compile(".*@bar.com$")], True, False),
        ],
    )
    def test__update_m2m_from_expression(self, expression, remove, expected_return):
        user = User.objects.create(username='user1', last_name='foo', first_name='bar', email='user1@foo.com')
        return_val = _update_m2m_from_expression(user, expression, remove)
        assert return_val == expected_return


@pytest.mark.django_db
class TestSAMLAttrMaps:
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
        "setting, expected_state, expected_orgs_to_create, kwargs_member_of_mods",
        [
            (
                # Default test, make sure that our roles get applied and removed as specified (with an alias)
                {
                    'saml_attr': 'memberOf',
                    'saml_admin_attr': 'admins',
                    'saml_auditor_attr': 'auditors',
                    'remove': True,
                    'remove_admins': True,
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
                None,
            ),
            (
                # Similar test, we are just going to override the values "coming from the IdP" to limit the teams
                {
                    'saml_attr': 'memberOf',
                    'saml_admin_attr': 'admins',
                    'saml_auditor_attr': 'auditors',
                    'remove': True,
                    'remove_admins': True,
                },
                {
                    'Default3': {'admin_role': True, 'member_role': True},
                    'Default4': {'auditor_role': True},
                    'Rando1': {'admin_role': False, 'auditor_role': False, 'member_role': False},
                },
                [
                    'Default3',
                    'Default4',
                ],
                ['Default3'],
            ),
            (
                # Test to make sure the remove logic is working
                {
                    'saml_attr': 'memberOf',
                    'saml_admin_attr': 'admins',
                    'saml_auditor_attr': 'auditors',
                    'remove': False,
                    'remove_admins': False,
                    'remove_auditors': False,
                },
                {
                    'Default2': {'member_role': True},
                    'Default3': {'admin_role': True},
                    'Default4': {'auditor_role': True},
                    'o1_alias': {'member_role': True},
                },
                [
                    'o1_alias',
                    'Default2',
                    'Default3',
                    'Default4',
                ],
                ['Default1', 'Default2'],
            ),
        ],
    )
    def test__update_user_orgs_by_saml_attr(self, backend, setting, expected_state, expected_orgs_to_create, kwargs_member_of_mods):
        kwargs = {
            'username': u'cmeyers@redhat.com',
            'uid': 'idp:cmeyers@redhat.com',
            'request': {u'SAMLResponse': [], u'RelayState': [u'idp']},
            'is_new': False,
            'response': {
                'session_index': '_0728f0e0-b766-0135-75fa-02842b07c044',
                'idp_name': u'idp',
                'attributes': {
                    'memberOf': ['Default1', 'Default2'],
                    'admins': ['Default3'],
                    'auditors': ['Default4'],
                    'groups': ['Blue', 'Red'],
                    'User.email': ['cmeyers@redhat.com'],
                    'User.LastName': ['Meyers'],
                    'name_id': 'cmeyers@redhat.com',
                    'User.FirstName': ['Chris'],
                    'PersonImmutableID': [],
                },
            },
            'social': None,
            'strategy': None,
            'new_association': False,
        }
        if kwargs_member_of_mods:
            kwargs['response']['attributes']['memberOf'] = kwargs_member_of_mods

        # Create a random organization in the database for testing
        Organization.objects.create(name='Rando1')

        with override_settings(SOCIAL_AUTH_SAML_ORGANIZATION_ATTR=setting):
            desired_org_state = {}
            orgs_to_create = []
            _update_user_orgs_by_saml_attr(backend, desired_org_state, orgs_to_create, **kwargs)
            assert desired_org_state == expected_state
            assert orgs_to_create == expected_orgs_to_create

    @pytest.mark.parametrize(
        "setting, expected_team_state, expected_teams_to_create, kwargs_group_override",
        [
            (
                {
                    'saml_attr': 'groups',
                    'remove': False,
                    'team_org_map': [
                        {'team': 'Blue', 'organization': 'Default1'},
                        {'team': 'Blue', 'organization': 'Default2'},
                        {'team': 'Blue', 'organization': 'Default3'},
                        {'team': 'Red', 'organization': 'Default1'},
                        {'team': 'Green', 'organization': 'Default1'},
                        {'team': 'Green', 'organization': 'Default3'},
                        {'team': 'Yellow', 'team_alias': 'Yellow_Alias', 'organization': 'Default4', 'organization_alias': 'Default4_Alias'},
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
                },
                {
                    'Blue': 'Default3',
                    'Red': 'Default1',
                },
                None,
            ),
            (
                {
                    'saml_attr': 'groups',
                    'remove': False,
                    'team_org_map': [
                        {'team': 'Blue', 'organization': 'Default1'},
                        {'team': 'Blue', 'organization': 'Default2'},
                        {'team': 'Blue', 'organization': 'Default3'},
                        {'team': 'Red', 'organization': 'Default1'},
                        {'team': 'Green', 'organization': 'Default1'},
                        {'team': 'Green', 'organization': 'Default3'},
                        {'team': 'Yellow', 'team_alias': 'Yellow_Alias', 'organization': 'Default4', 'organization_alias': 'Default4_Alias'},
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
                ['Blue', 'Red', 'Green'],
            ),
            (
                {
                    'saml_attr': 'groups',
                    'remove': True,
                    'team_org_map': [
                        {'team': 'Blue', 'organization': 'Default1'},
                        {'team': 'Blue', 'organization': 'Default2'},
                        {'team': 'Blue', 'organization': 'Default3'},
                        {'team': 'Red', 'organization': 'Default1'},
                        {'team': 'Green', 'organization': 'Default1'},
                        {'team': 'Green', 'organization': 'Default3'},
                        {'team': 'Yellow', 'team_alias': 'Yellow_Alias', 'organization': 'Default4', 'organization_alias': 'Default4_Alias'},
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
                ['Green'],
            ),
        ],
    )
    def test__update_user_teams_by_saml_attr(self, setting, expected_team_state, expected_teams_to_create, kwargs_group_override):
        kwargs = {
            'username': u'cmeyers@redhat.com',
            'uid': 'idp:cmeyers@redhat.com',
            'request': {u'SAMLResponse': [], u'RelayState': [u'idp']},
            'is_new': False,
            'response': {
                'session_index': '_0728f0e0-b766-0135-75fa-02842b07c044',
                'idp_name': u'idp',
                'attributes': {
                    'memberOf': ['Default1', 'Default2'],
                    'admins': ['Default3'],
                    'auditors': ['Default4'],
                    'groups': ['Blue', 'Red'],
                    'User.email': ['cmeyers@redhat.com'],
                    'User.LastName': ['Meyers'],
                    'name_id': 'cmeyers@redhat.com',
                    'User.FirstName': ['Chris'],
                    'PersonImmutableID': [],
                },
            },
            'social': None,
            'strategy': None,
            'new_association': False,
        }
        if kwargs_group_override:
            kwargs['response']['attributes']['groups'] = kwargs_group_override

        o = Organization.objects.create(name='Rando1')
        Team.objects.create(name='Rando1', organization_id=o.id)

        with override_settings(SOCIAL_AUTH_SAML_TEAM_ATTR=setting):
            desired_team_state = {}
            teams_to_create = {}
            _update_user_teams_by_saml_attr(desired_team_state, teams_to_create, **kwargs)
            assert desired_team_state == expected_team_state
            assert teams_to_create == expected_teams_to_create


@pytest.mark.django_db
class TestSAMLUserFlags:
    @pytest.mark.parametrize(
        "user_flags_settings, expected, is_superuser",
        [
            # In this case we will pass no user flags so new_flag should be false and changed will def be false
            (
                {},
                (False, False),
                False,
            ),
            # NOTE: The first handful of tests test role/value as string instead of lists.
            #       This was from the initial implementation of these fields but the code should be able to handle this
            #       There are a couple tests at the end of this which will validate arrays in these values.
            #
            # In this case we will give the user a group to make them an admin
            (
                {'is_superuser_role': 'test-role-1'},
                (True, True),
                False,
            ),
            # In this case we will give the user a flag that will make then an admin
            (
                {'is_superuser_attr': 'is_superuser'},
                (True, True),
                False,
            ),
            # In this case we will give the user a flag but the wrong value
            (
                {'is_superuser_attr': 'is_superuser', 'is_superuser_value': 'junk'},
                (False, False),
                False,
            ),
            # In this case we will give the user a flag and the right value
            (
                {'is_superuser_attr': 'is_superuser', 'is_superuser_value': 'true'},
                (True, True),
                False,
            ),
            # In this case we will give the user a proper role and an is_superuser_attr role that they don't have, this should make them an admin
            (
                {'is_superuser_role': 'test-role-1', 'is_superuser_attr': 'gibberish', 'is_superuser_value': 'true'},
                (True, True),
                False,
            ),
            # In this case we will give the user a proper role and an is_superuser_attr role that they have, this should make them an admin
            (
                {'is_superuser_role': 'test-role-1', 'is_superuser_attr': 'test-role-1'},
                (True, True),
                False,
            ),
            # In this case we will give the user a proper role and an is_superuser_attr role that they have but a bad value, this should make them an admin
            (
                {'is_superuser_role': 'test-role-1', 'is_superuser_attr': 'is_superuser', 'is_superuser_value': 'junk'},
                (False, False),
                False,
            ),
            # In this case we will give the user everything
            (
                {'is_superuser_role': 'test-role-1', 'is_superuser_attr': 'is_superuser', 'is_superuser_value': 'true'},
                (True, True),
                False,
            ),
            # In this test case we will validate that a single attribute (instead of a list) still works
            (
                {'is_superuser_attr': 'name_id', 'is_superuser_value': 'test_id'},
                (True, True),
                False,
            ),
            # This will be a negative test for a single attribute
            (
                {'is_superuser_attr': 'name_id', 'is_superuser_value': 'junk'},
                (False, False),
                False,
            ),
            # The user is already a superuser so we should remove them
            (
                {'is_superuser_attr': 'name_id', 'is_superuser_value': 'junk', 'remove_superusers': True},
                (False, True),
                True,
            ),
            # The user is already a superuser but we don't have a remove field
            (
                {'is_superuser_attr': 'name_id', 'is_superuser_value': 'junk', 'remove_superusers': False},
                (True, False),
                True,
            ),
            # Positive test for multiple values for is_superuser_value
            (
                {'is_superuser_attr': 'is_superuser', 'is_superuser_value': ['junk', 'junk2', 'else', 'junk']},
                (True, True),
                False,
            ),
            # Negative test for multiple values for is_superuser_value
            (
                {'is_superuser_attr': 'is_superuser', 'is_superuser_value': ['junk', 'junk2', 'junk']},
                (False, True),
                True,
            ),
            # Positive test for multiple values of is_superuser_role
            (
                {'is_superuser_role': ['junk', 'junk2', 'something', 'junk']},
                (True, True),
                False,
            ),
            # Negative test for multiple values of is_superuser_role
            (
                {'is_superuser_role': ['junk', 'junk2', 'junk']},
                (False, True),
                True,
            ),
        ],
    )
    def test__check_flag(self, user_flags_settings, expected, is_superuser):
        user = User()
        user.username = 'John'
        user.is_superuser = is_superuser

        attributes = {
            'email': ['noone@nowhere.com'],
            'last_name': ['Westcott'],
            'is_superuser': ['something', 'else', 'true'],
            'username': ['test_id'],
            'first_name': ['John'],
            'Role': ['test-role-1', 'something', 'different'],
            'name_id': 'test_id',
        }

        assert expected == _check_flag(user, 'superuser', attributes, user_flags_settings)
