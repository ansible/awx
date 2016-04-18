import pytest


@pytest.mark.django_db()
def test_admin_not_member(team):
    "Test to ensure we don't add admin_role as a parent to team.member_role, as "
    "this creates a cycle with organization administration, which we've decided "
    "to remove support for"

    assert team.admin_role.is_ancestor_of(team.member_role) is False
