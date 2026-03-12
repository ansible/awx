import pytest

from django.contrib.contenttypes.models import ContentType
from django.test import override_settings
from django.apps import apps

from ansible_base.rbac.models import RoleDefinition, RoleUserAssignment, RoleTeamAssignment
from ansible_base.rbac.migrations._utils import give_permissions

from awx.main.models import User, Team
from awx.main.migrations._dab_rbac import consolidate_indirect_user_roles


@pytest.mark.django_db
@override_settings(ANSIBLE_BASE_ALLOW_TEAM_PARENTS=True)
def test_consolidate_indirect_user_roles_with_nested_teams(setup_managed_roles, organization):
    """
    Test the consolidate_indirect_user_roles function with a nested team hierarchy.
    Setup:
    - Users: A, B, C, D
    - Teams: E, F, G
    - Direct assignments: A→(E,F,G), B→E, C→F, D→G
    - Team hierarchy: F→E (F is member of E), G→F (G is member of F)
    Expected result after consolidation:
    - Team E should have users: A, B, C, D (A directly, B directly, C through F, D through G→F)
    - Team F should have users: A, C, D (A directly, C directly, D through G)
    - Team G should have users: A, D (A directly, D directly)
    """
    user_a = User.objects.create_user(username='user_a')
    user_b = User.objects.create_user(username='user_b')
    user_c = User.objects.create_user(username='user_c')
    user_d = User.objects.create_user(username='user_d')

    team_e = Team.objects.create(name='Team E', organization=organization)
    team_f = Team.objects.create(name='Team F', organization=organization)
    team_g = Team.objects.create(name='Team G', organization=organization)

    # Get role definition and content type for give_permissions
    team_member_role = RoleDefinition.objects.get(name='Team Member')
    team_content_type = ContentType.objects.get_for_model(Team)

    # Assign users to teams
    give_permissions(apps=apps, rd=team_member_role, users=[user_a], object_id=team_e.id, content_type_id=team_content_type.id)
    give_permissions(apps=apps, rd=team_member_role, users=[user_a], object_id=team_f.id, content_type_id=team_content_type.id)
    give_permissions(apps=apps, rd=team_member_role, users=[user_a], object_id=team_g.id, content_type_id=team_content_type.id)
    give_permissions(apps=apps, rd=team_member_role, users=[user_b], object_id=team_e.id, content_type_id=team_content_type.id)
    give_permissions(apps=apps, rd=team_member_role, users=[user_c], object_id=team_f.id, content_type_id=team_content_type.id)
    give_permissions(apps=apps, rd=team_member_role, users=[user_d], object_id=team_g.id, content_type_id=team_content_type.id)

    # Mirror user assignments in the old RBAC system because signals don't run in tests
    team_e.member_role.members.add(user_a.id, user_b.id)
    team_f.member_role.members.add(user_a.id, user_c.id)
    team_g.member_role.members.add(user_a.id, user_d.id)

    # Setup team-to-team relationships
    give_permissions(apps=apps, rd=team_member_role, teams=[team_f], object_id=team_e.id, content_type_id=team_content_type.id)
    give_permissions(apps=apps, rd=team_member_role, teams=[team_g], object_id=team_f.id, content_type_id=team_content_type.id)

    # Verify initial direct assignments
    team_e_users_before = set(RoleUserAssignment.objects.filter(role_definition=team_member_role, object_id=team_e.id).values_list('user_id', flat=True))
    assert team_e_users_before == {user_a.id, user_b.id}
    team_f_users_before = set(RoleUserAssignment.objects.filter(role_definition=team_member_role, object_id=team_f.id).values_list('user_id', flat=True))
    assert team_f_users_before == {user_a.id, user_c.id}
    team_g_users_before = set(RoleUserAssignment.objects.filter(role_definition=team_member_role, object_id=team_g.id).values_list('user_id', flat=True))
    assert team_g_users_before == {user_a.id, user_d.id}

    # Verify team-to-team relationships exist
    assert RoleTeamAssignment.objects.filter(role_definition=team_member_role, team=team_f, object_id=team_e.id).exists()
    assert RoleTeamAssignment.objects.filter(role_definition=team_member_role, team=team_g, object_id=team_f.id).exists()

    # Run the consolidation function
    consolidate_indirect_user_roles(apps, None)

    # Verify consolidation
    team_e_users_after = set(RoleUserAssignment.objects.filter(role_definition=team_member_role, object_id=team_e.id).values_list('user_id', flat=True))
    assert team_e_users_after == {user_a.id, user_b.id, user_c.id, user_d.id}, f"Team E should have users A, B, C, D but has {team_e_users_after}"
    team_f_users_after = set(RoleUserAssignment.objects.filter(role_definition=team_member_role, object_id=team_f.id).values_list('user_id', flat=True))
    assert team_f_users_after == {user_a.id, user_c.id, user_d.id}, f"Team F should have users A, C, D but has {team_f_users_after}"
    team_g_users_after = set(RoleUserAssignment.objects.filter(role_definition=team_member_role, object_id=team_g.id).values_list('user_id', flat=True))
    assert team_g_users_after == {user_a.id, user_d.id}, f"Team G should have users A, D but has {team_g_users_after}"

    # Verify team member changes are mirrored to the old RBAC system
    assert team_e_users_after == set(team_e.member_role.members.all().values_list('id', flat=True))
    assert team_f_users_after == set(team_f.member_role.members.all().values_list('id', flat=True))
    assert team_g_users_after == set(team_g.member_role.members.all().values_list('id', flat=True))

    # Verify team-to-team relationships are removed after consolidation
    assert not RoleTeamAssignment.objects.filter(
        role_definition=team_member_role, team=team_f, object_id=team_e.id
    ).exists(), "Team-to-team relationship F→E should be removed"
    assert not RoleTeamAssignment.objects.filter(
        role_definition=team_member_role, team=team_g, object_id=team_f.id
    ).exists(), "Team-to-team relationship G→F should be removed"


@pytest.mark.django_db
@override_settings(ANSIBLE_BASE_ALLOW_TEAM_PARENTS=True)
def test_consolidate_indirect_user_roles_no_team_relationships(setup_managed_roles, organization):
    """
    Test that the function handles the case where there are no team-to-team relationships.
    It should return early without making any changes.
    """
    # Create a user and team with direct assignment
    user = User.objects.create_user(username='test_user')
    team = Team.objects.create(name='Test Team', organization=organization)

    team_member_role = RoleDefinition.objects.get(name='Team Member')
    team_content_type = ContentType.objects.get_for_model(Team)
    give_permissions(apps=apps, rd=team_member_role, users=[user], object_id=team.id, content_type_id=team_content_type.id)

    # Compare count of assignments before and after consolidation
    assignments_before = RoleUserAssignment.objects.filter(role_definition=team_member_role).count()
    consolidate_indirect_user_roles(apps, None)
    assignments_after = RoleUserAssignment.objects.filter(role_definition=team_member_role).count()

    assert assignments_before == assignments_after, "Number of assignments should not change when there are no team-to-team relationships"


@pytest.mark.django_db
@override_settings(ANSIBLE_BASE_ALLOW_TEAM_PARENTS=True)
def test_consolidate_indirect_user_roles_circular_reference(setup_managed_roles, organization):
    """
    Test that the function handles circular team references without infinite recursion.
    """
    team_a = Team.objects.create(name='Team A', organization=organization)
    team_b = Team.objects.create(name='Team B', organization=organization)

    # Create a user assigned to team A
    user = User.objects.create_user(username='test_user')

    team_member_role = RoleDefinition.objects.get(name='Team Member')
    team_content_type = ContentType.objects.get_for_model(Team)
    give_permissions(apps=apps, rd=team_member_role, users=[user], object_id=team_a.id, content_type_id=team_content_type.id)

    # Create circular team relationships: A → B → A
    give_permissions(apps=apps, rd=team_member_role, teams=[team_b], object_id=team_a.id, content_type_id=team_content_type.id)
    give_permissions(apps=apps, rd=team_member_role, teams=[team_a], object_id=team_b.id, content_type_id=team_content_type.id)

    # Run the consolidation function - should not raise an exception
    consolidate_indirect_user_roles(apps, None)

    # Both teams should have the user assigned
    team_a_users = set(RoleUserAssignment.objects.filter(role_definition=team_member_role, object_id=team_a.id).values_list('user_id', flat=True))
    team_b_users = set(RoleUserAssignment.objects.filter(role_definition=team_member_role, object_id=team_b.id).values_list('user_id', flat=True))

    assert user.id in team_a_users, "User should be assigned to team A"
    assert user.id in team_b_users, "User should be assigned to team B"
