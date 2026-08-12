"""
Tests that save_user_claims (which uses bulk_create, skipping signals)
correctly syncs old Role.members when run through AwxJWTAuthentication.
"""

from unittest import mock

import pytest

from ansible_base.jwt_consumer.awx.auth import AwxJWTAuthentication
from ansible_base.jwt_consumer.common.auth import JWTAuthentication
from ansible_base.rbac.claims import save_user_claims
from awx.main.models import Organization, Team


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

    def _call_process_permissions(self, auth, user, claims):
        """Call process_permissions with claims pre-loaded, mocking the JWT layer."""
        save_user_claims(user, **claims)
        auth.common_auth.user = user
        auth.common_auth._saved_claims = (claims["objects"], claims["object_roles"], claims["global_roles"])
        with mock.patch.object(JWTAuthentication, 'process_permissions'):
            auth.process_permissions()

    def test_process_permissions_populates_old_rbac(self, bob, organization, team, setup_managed_roles):
        """Verify that process_permissions populates old Role.members after bulk claims."""
        claims = self._build_claims([organization], [team])

        auth = AwxJWTAuthentication()
        self._call_process_permissions(auth, bob, claims)

        assert bob in organization.admin_role.members.all()
        assert bob in team.member_role.members.all()

    def test_process_permissions_removes_stale_old_rbac(self, bob, organization, team, setup_managed_roles):
        """Verify that process_permissions removes old Role.members when claims shrink."""
        auth = AwxJWTAuthentication()

        # First: give bob both org admin and team member
        claims_full = self._build_claims([organization], [team])
        self._call_process_permissions(auth, bob, claims_full)

        assert bob in organization.admin_role.members.all()
        assert bob in team.member_role.members.all()

        # Second: claims shrink to just org admin (no team member)
        claims_reduced = self._build_claims([organization], [])
        self._call_process_permissions(auth, bob, claims_reduced)

        assert bob in organization.admin_role.members.all()
        assert bob not in team.member_role.members.all()

    def test_process_permissions_multiple_orgs_and_teams(self, bob, setup_managed_roles):
        """Test sync at small scale with multiple orgs and teams."""
        orgs = [Organization.objects.create(name=f"sync-org-{i}") for i in range(3)]
        teams = []
        for org in orgs:
            teams.append(Team.objects.create(name=f"sync-team-{org.name}", organization=org))

        claims = self._build_claims(orgs, teams)

        auth = AwxJWTAuthentication()
        self._call_process_permissions(auth, bob, claims)

        for org in orgs:
            org.refresh_from_db()
            assert bob in org.admin_role.members.all(), f"bob not in {org.name}.admin_role"

        for team in teams:
            team.refresh_from_db()
            assert bob in team.member_role.members.all(), f"bob not in {team.name}.member_role"
