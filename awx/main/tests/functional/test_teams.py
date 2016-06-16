import pytest


@pytest.mark.django_db()
def test_admin_not_member(team):
    """Test to ensure we don't add admin_role as a parent to team.member_role, as
    this creates a cycle with organization administration, which we've decided
    to remove support for

    (2016-06-16) I think this might have been resolved. I'm asserting
    this to be true in the mean time.
    """

    assert team.admin_role.is_ancestor_of(team.member_role) is True
