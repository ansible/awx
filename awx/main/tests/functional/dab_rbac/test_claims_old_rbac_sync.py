"""
Tests that save_user_claims (which uses bulk_create, skipping signals)
correctly syncs old Role.members when run through AwxJWTAuthentication.
"""

import pytest

from ansible_base.jwt_consumer.awx.auth import AwxJWTAuthentication
from ansible_base.rbac.claims import save_user_claims
from ansible_base.rbac.models import RoleDefinition


@pytest.mark.django_db
class TestClaimsOldRbacSync:

    def _build_claims(self, orgs, teams):
        """Build a claims dict from org/team model instances."""
        objects = {"organization": [], "team": []}
        object_roles = {}

        org_indexes = []
        for i, org in enumerate(orgs):
            objects["organization"].append(
                {
                    "ansible_id": str(org.resource.ansible_id),
                    "name": org.name,
                }
            )
            org_indexes.append(i)

        team_indexes = []
        for i, team in enumerate(teams):
            org_idx = next(j for j, o in enumerate(orgs) if o.pk == team.organization_id)
            objects["team"].append(
                {
                    "ansible_id": str(team.resource.ansible_id),
                    "name": team.name,
                    "org": org_idx,
                }
            )
            team_indexes.append(i)

        if org_indexes:
            object_roles["Organization Admin"] = {"content_type": "organization", "objects": org_indexes}
        if team_indexes:
            object_roles["Team Member"] = {"content_type": "team", "objects": team_indexes}

        return {"objects": objects, "object_roles": object_roles, "global_roles": []}

    def test_bulk_claims_skips_old_rbac_signals(self, bob, organization, team, setup_managed_roles):
        """Verify that save_user_claims (bulk path) does NOT populate old Role.members via signals."""
        claims = self._build_claims([organization], [team])

        save_user_claims(bob, **claims)

        # DAB assignment exists
        from ansible_base.rbac.models import RoleUserAssignment

        assert RoleUserAssignment.objects.filter(user=bob, role_definition__name="Organization Admin").exists()
        assert RoleUserAssignment.objects.filter(user=bob, role_definition__name="Team Member").exists()

        # Old Role.members NOT populated (bulk_create skips post_save signals)
        assert bob not in organization.admin_role.members.all()
        assert bob not in team.member_role.members.all()

    def test_awx_sync_populates_old_rbac(self, bob, organization, team, setup_managed_roles):
        """Verify that _sync_old_rbac populates old Role.members after bulk claims."""
        claims = self._build_claims([organization], [team])

        save_user_claims(bob, **claims)

        # Manually call the AWX sync (normally called via process_permissions)
        auth = AwxJWTAuthentication()
        auth._sync_old_rbac(bob, claims["objects"], claims["object_roles"])

        assert bob in organization.admin_role.members.all()
        assert bob in team.member_role.members.all()

    def test_awx_sync_removes_stale_old_rbac(self, bob, organization, team, setup_managed_roles):
        """Verify that _sync_old_rbac removes old Role.members when claims shrink."""
        # First: give bob both org admin and team member
        claims_full = self._build_claims([organization], [team])
        save_user_claims(bob, **claims_full)

        auth = AwxJWTAuthentication()
        auth._sync_old_rbac(bob, claims_full["objects"], claims_full["object_roles"])

        assert bob in organization.admin_role.members.all()
        assert bob in team.member_role.members.all()

        # Second: claims shrink to just org admin (no team member)
        claims_reduced = self._build_claims([organization], [])
        save_user_claims(bob, **claims_reduced)
        auth._sync_old_rbac(bob, claims_reduced["objects"], claims_reduced["object_roles"])

        assert bob in organization.admin_role.members.all()
        assert bob not in team.member_role.members.all()

    def test_awx_sync_multiple_orgs_and_teams(self, bob, setup_managed_roles):
        """Test sync at small scale with multiple orgs and teams."""
        from awx.main.models import Organization, Team

        orgs = [Organization.objects.create(name=f"sync-org-{i}") for i in range(3)]
        teams = []
        for org in orgs:
            teams.append(Team.objects.create(name=f"sync-team-{org.name}", organization=org))

        claims = self._build_claims(orgs, teams)
        save_user_claims(bob, **claims)

        auth = AwxJWTAuthentication()
        auth._sync_old_rbac(bob, claims["objects"], claims["object_roles"])

        for org in orgs:
            org.refresh_from_db()
            assert bob in org.admin_role.members.all(), f"bob not in {org.name}.admin_role"

        for team in teams:
            team.refresh_from_db()
            assert bob in team.member_role.members.all(), f"bob not in {team.name}.member_role"
