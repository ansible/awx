import pytest

@pytest.mark.django_db
def test_team_migration_user(team, user, permissions):
    u = user('user', False)
    team.users.add(u)

    assert not team.accessible_by(u, permissions['auditor'])

    migrated = team.migrate_to_rbac()
    assert len(migrated) == 1
    assert team.accessible_by(u, permissions['auditor'])

