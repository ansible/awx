import pytest
from collections import Counter
from django.core.exceptions import FieldError
from django.utils.timezone import now
from django.test.utils import override_settings

from awx.main.models import Credential, CredentialType, Organization, Team, User
from awx.sso.common import (
    get_orgs_by_ids,
    reconcile_users_org_team_mappings,
    create_org_and_teams,
    get_or_create_org_with_default_galaxy_cred,
    is_remote_auth_enabled,
    get_external_account,
)


class MicroMockObject(object):
    def all(self):
        return True


@pytest.mark.django_db
class TestCommonFunctions:
    @pytest.fixture
    def orgs(self):
        o1 = Organization.objects.create(name='Default1')
        o2 = Organization.objects.create(name='Default2')
        o3 = Organization.objects.create(name='Default3')
        return (o1, o2, o3)

    @pytest.fixture
    def galaxy_credential(self):
        galaxy_type = CredentialType.objects.create(kind='galaxy')
        cred = Credential(
            created=now(), modified=now(), name='Ansible Galaxy', managed=True, credential_type=galaxy_type, inputs={'url': 'https://galaxy.ansible.com/'}
        )
        cred.save()

    def test_get_orgs_by_ids(self, orgs):
        orgs_and_ids = get_orgs_by_ids()
        o1, o2, o3 = orgs
        assert Counter(orgs_and_ids.keys()) == Counter([o1.name, o2.name, o3.name])
        assert Counter(orgs_and_ids.values()) == Counter([o1.id, o2.id, o3.id])

    def test_reconcile_users_org_team_mappings(self):
        # Create objects for us to play with
        user = User.objects.create(username='user1@foo.com', last_name='foo', first_name='bar', email='user1@foo.com', is_active=True)
        org1 = Organization.objects.create(name='Default1')
        org2 = Organization.objects.create(name='Default2')
        team1 = Team.objects.create(name='Team1', organization=org1)
        team2 = Team.objects.create(name='Team1', organization=org2)

        # Try adding nothing
        reconcile_users_org_team_mappings(user, {}, {}, 'Nada')
        assert list(user.roles.all()) == []

        # Add a user to an org that does not exist (should have no affect)
        reconcile_users_org_team_mappings(
            user,
            {
                'junk': {'member_role': True},
            },
            {},
            'Nada',
        )
        assert list(user.roles.all()) == []

        # Remove a user to an org that does not exist (should have no affect)
        reconcile_users_org_team_mappings(
            user,
            {
                'junk': {'member_role': False},
            },
            {},
            'Nada',
        )
        assert list(user.roles.all()) == []

        # Add the user to the orgs
        reconcile_users_org_team_mappings(user, {org1.name: {'member_role': True}, org2.name: {'member_role': True}}, {}, 'Nada')
        assert len(user.roles.all()) == 2
        assert user in org1.member_role
        assert user in org2.member_role

        # Remove the user from the orgs
        reconcile_users_org_team_mappings(user, {org1.name: {'member_role': False}, org2.name: {'member_role': False}}, {}, 'Nada')
        assert list(user.roles.all()) == []
        assert user not in org1.member_role
        assert user not in org2.member_role

        # Remove the user from the orgs (again, should have no affect)
        reconcile_users_org_team_mappings(user, {org1.name: {'member_role': False}, org2.name: {'member_role': False}}, {}, 'Nada')
        assert list(user.roles.all()) == []
        assert user not in org1.member_role
        assert user not in org2.member_role

        # Add a user back to the member role
        reconcile_users_org_team_mappings(
            user,
            {
                org1.name: {
                    'member_role': True,
                },
            },
            {},
            'Nada',
        )
        users_roles = set(user.roles.values_list('pk', flat=True))
        assert len(users_roles) == 1
        assert user in org1.member_role

        # Add the user to additional roles
        reconcile_users_org_team_mappings(
            user,
            {
                org1.name: {'admin_role': True, 'auditor_role': True},
            },
            {},
            'Nada',
        )
        assert len(user.roles.all()) == 3
        assert user in org1.member_role
        assert user in org1.admin_role
        assert user in org1.auditor_role

        # Add a user to a non-existent role (results in FieldError exception)
        with pytest.raises(FieldError):
            reconcile_users_org_team_mappings(
                user,
                {
                    org1.name: {
                        'dne_role': True,
                    },
                },
                {},
                'Nada',
            )

        # Try adding a user to a role that should not exist on an org (technically this works at this time)
        reconcile_users_org_team_mappings(
            user,
            {
                org1.name: {
                    'read_role_id': True,
                },
            },
            {},
            'Nada',
        )
        assert len(user.roles.all()) == 4
        assert user in org1.member_role
        assert user in org1.admin_role
        assert user in org1.auditor_role

        # Remove all of the org perms to test team perms
        reconcile_users_org_team_mappings(
            user,
            {
                org1.name: {
                    'read_role_id': False,
                    'member_role': False,
                    'admin_role': False,
                    'auditor_role': False,
                },
            },
            {},
            'Nada',
        )
        assert list(user.roles.all()) == []

        # Add the user as a member to one of the teams
        reconcile_users_org_team_mappings(user, {}, {org1.name: {team1.name: {'member_role': True}}}, 'Nada')
        assert len(user.roles.all()) == 1
        assert user in team1.member_role
        # Validate that the user did not become a member of a team with the same name in a different org
        assert user not in team2.member_role

        # Remove the user from the team
        reconcile_users_org_team_mappings(user, {}, {org1.name: {team1.name: {'member_role': False}}}, 'Nada')
        assert list(user.roles.all()) == []
        assert user not in team1.member_role

        # Remove the user from the team again
        reconcile_users_org_team_mappings(user, {}, {org1.name: {team1.name: {'member_role': False}}}, 'Nada')
        assert list(user.roles.all()) == []

        # Add the user to a team that does not exist (should have no affect)
        reconcile_users_org_team_mappings(user, {}, {org1.name: {'junk': {'member_role': True}}}, 'Nada')
        assert list(user.roles.all()) == []

        # Remove the user from a team that does not exist (should have no affect)
        reconcile_users_org_team_mappings(user, {}, {org1.name: {'junk': {'member_role': False}}}, 'Nada')
        assert list(user.roles.all()) == []

        # Test a None setting
        reconcile_users_org_team_mappings(user, {}, {org1.name: {'junk': {'member_role': None}}}, 'Nada')
        assert list(user.roles.all()) == []

        # Add the user multiple teams in different orgs
        reconcile_users_org_team_mappings(user, {}, {org1.name: {team1.name: {'member_role': True}}, org2.name: {team2.name: {'member_role': True}}}, 'Nada')
        assert len(user.roles.all()) == 2
        assert user in team1.member_role
        assert user in team2.member_role

        # Remove the user from just one of the teams
        reconcile_users_org_team_mappings(user, {}, {org2.name: {team2.name: {'member_role': False}}}, 'Nada')
        assert len(user.roles.all()) == 1
        assert user in team1.member_role
        assert user not in team2.member_role

    @pytest.mark.parametrize(
        "org_list, team_map, can_create, org_count, team_count",
        [
            # In this case we will only pass in organizations
            (
                ["org1", "org2"],
                {},
                True,
                2,
                0,
            ),
            # In this case we will only pass in teams but the orgs will be created from the teams
            (
                [],
                {"team1": "org1", "team2": "org2"},
                True,
                2,
                2,
            ),
            # In this case we will reuse an org
            (
                ["org1"],
                {"team1": "org1", "team2": "org1"},
                True,
                1,
                2,
            ),
            # In this case we have a combination of orgs, orgs reused and an org created by a team
            (
                ["org1", "org2", "org3"],
                {"team1": "org1", "team2": "org4"},
                True,
                4,
                2,
            ),
            # In this case we will test a case that the UI should prevent and have a team with no Org
            #   This should create org1/2 but only team1
            (
                ["org1"],
                {"team1": "org2", "team2": None},
                True,
                2,
                1,
            ),
            # Block any creation with the can_create flag
            (
                ["org1"],
                {"team1": "org2", "team2": None},
                False,
                0,
                0,
            ),
        ],
    )
    def test_create_org_and_teams(self, galaxy_credential, org_list, team_map, can_create, org_count, team_count):
        create_org_and_teams(org_list, team_map, 'py.test', can_create=can_create)
        assert Organization.objects.count() == org_count
        assert Team.objects.count() == team_count

    def test_get_or_create_org_with_default_galaxy_cred_add_galaxy_cred(self, galaxy_credential):
        # If this method creates the org it should get the default galaxy credential
        num_orgs = 4
        for number in range(1, (num_orgs + 1)):
            get_or_create_org_with_default_galaxy_cred(name=f"Default {number}")

        assert Organization.objects.count() == 4

        for o in Organization.objects.all():
            assert o.galaxy_credentials.count() == 1
            assert o.galaxy_credentials.first().name == 'Ansible Galaxy'

    def test_get_or_create_org_with_default_galaxy_cred_no_galaxy_cred(self, galaxy_credential):
        # If the org is pre-created, we should not add the galaxy_credential
        num_orgs = 4
        for number in range(1, (num_orgs + 1)):
            Organization.objects.create(name=f"Default {number}")
            get_or_create_org_with_default_galaxy_cred(name=f"Default {number}")

        assert Organization.objects.count() == 4

        for o in Organization.objects.all():
            assert o.galaxy_credentials.count() == 0

    @pytest.mark.parametrize(
        "enable_ldap, enable_social, enable_enterprise, expected_results",
        [
            (False, False, False, None),
            (True, False, False, 'ldap'),
            (True, True, False, 'social'),
            (True, True, True, 'enterprise'),
            (False, True, True, 'enterprise'),
            (False, False, True, 'enterprise'),
            (False, True, False, 'social'),
        ],
    )
    def test_get_external_account(self, enable_ldap, enable_social, enable_enterprise, expected_results):
        try:
            user = User.objects.get(username="external_tester")
        except User.DoesNotExist:
            user = User(username="external_tester")
            user.set_unusable_password()
            user.save()

        if enable_ldap:
            user.profile.ldap_dn = 'test.dn'
        if enable_social:
            from social_django.models import UserSocialAuth

            social_auth, _ = UserSocialAuth.objects.get_or_create(
                uid='667ec049-cdf3-45d0-a4dc-0465f7505954',
                provider='oidc',
                extra_data={},
                user_id=user.id,
            )
            user.social_auth.set([social_auth])
        if enable_enterprise:
            from awx.sso.models import UserEnterpriseAuth

            enterprise_auth = UserEnterpriseAuth(user=user, provider='tacacs+')
            enterprise_auth.save()

        assert get_external_account(user) == expected_results

    @pytest.mark.parametrize(
        "setting, expected",
        [
            # Set none of the social auth settings
            ('JUNK_SETTING', False),
            # Set the hard coded settings
            ('AUTH_LDAP_SERVER_URI', True),
            ('SOCIAL_AUTH_SAML_ENABLED_IDPS', True),
            ('RADIUS_SERVER', True),
            ('TACACSPLUS_HOST', True),
            # Set some SOCIAL_SOCIAL_AUTH_OIDC_KEYAUTH_*_KEY settings
            ('SOCIAL_AUTH_AZUREAD_OAUTH2_KEY', True),
            ('SOCIAL_AUTH_GITHUB_ENTERPRISE_KEY', True),
            ('SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_KEY', True),
            ('SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_KEY', True),
            ('SOCIAL_AUTH_GITHUB_KEY', True),
            ('SOCIAL_AUTH_GITHUB_ORG_KEY', True),
            ('SOCIAL_AUTH_GITHUB_TEAM_KEY', True),
            ('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', True),
            ('SOCIAL_AUTH_OIDC_KEY', True),
            # Try a hypothetical future one
            ('SOCIAL_AUTH_GIBBERISH_KEY', True),
            # Do a SAML one
            ('SOCIAL_AUTH_SAML_SP_PRIVATE_KEY', False),
        ],
    )
    def test_is_remote_auth_enabled(self, setting, expected):
        with override_settings(**{setting: True}):
            assert is_remote_auth_enabled() == expected

    @pytest.mark.parametrize(
        "key_one, key_one_value, key_two, key_two_value, expected",
        [
            ('JUNK_SETTING', True, 'JUNK2_SETTING', True, False),
            ('AUTH_LDAP_SERVER_URI', True, 'SOCIAL_AUTH_AZUREAD_OAUTH2_KEY', True, True),
            ('JUNK_SETTING', True, 'SOCIAL_AUTH_AZUREAD_OAUTH2_KEY', True, True),
            ('AUTH_LDAP_SERVER_URI', False, 'SOCIAL_AUTH_AZUREAD_OAUTH2_KEY', False, False),
        ],
    )
    def test_is_remote_auth_enabled_multiple_keys(self, key_one, key_one_value, key_two, key_two_value, expected):
        with override_settings(**{key_one: key_one_value}):
            with override_settings(**{key_two: key_two_value}):
                assert is_remote_auth_enabled() == expected
