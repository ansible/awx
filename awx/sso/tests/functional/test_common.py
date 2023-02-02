import pytest
from collections import Counter
from django.core.exceptions import FieldError
from django.utils.timezone import now

from awx.main.models import Credential, CredentialType, Organization, Team, User
from awx.sso.common import get_orgs_by_ids, reconcile_users_org_team_mappings, create_org_and_teams, get_or_create_org_with_default_galaxy_cred


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
