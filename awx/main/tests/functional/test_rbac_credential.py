import pytest

@pytest.mark.django_db
def test_credential_migration_user(credential, user, permissions):
    u = user('user', False)
    credential.user = u
    migrated = credential.migrate_to_rbac()
    assert len(migrated) == 1
    assert credential.accessible_by(u, permissions['admin'])

@pytest.mark.django_db
def test_credential_usage_role(credential, user, permissions):
    u = user('user', False)
    credential.usage_role.members.add(u)
    assert credential.accessible_by(u, permissions['usage'])

@pytest.mark.django_db
def test_credential_migration_team_member(credential, team, user, permissions):
    u = user('user', False)
    team.admin_role.members.add(u)
    credential.team = team

    # No permissions pre-migration
    assert credential.accessible_by(u, permissions['admin']) == False

    migrated = credential.migrate_to_rbac()
    # Admin permissions post migration
    assert len(migrated) == 1
    assert credential.accessible_by(u, permissions['admin'])

@pytest.mark.django_db
def test_credential_migration_team_admin(credential, team, user, permissions):
    u = user('user', False)
    team.member_role.members.add(u)
    credential.team = team

    # No permissions pre-migration
    assert credential.accessible_by(u, permissions['usage']) == False

    # Usage permissions post migration
    migrated = credential.migrate_to_rbac()
    assert len(migrated) == 1
    assert credential.accessible_by(u, permissions['usage'])

