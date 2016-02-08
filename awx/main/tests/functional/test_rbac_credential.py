import pytest

from awx.main.migrations import _rbac as rbac
from django.apps import apps

@pytest.mark.django_db
def test_credential_migration_user(credential, user, permissions):
    u = user('user', False)
    credential.user = u
    credential.save()

    migrated = rbac.migrate_credential(apps, None)

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
    credential.save()

    # No permissions pre-migration
    assert not credential.accessible_by(u, permissions['admin'])

    migrated = rbac.migrate_credential(apps, None)

    # Admin permissions post migration
    assert len(migrated) == 1
    assert credential.accessible_by(u, permissions['admin'])

@pytest.mark.django_db
def test_credential_migration_team_admin(credential, team, user, permissions):
    u = user('user', False)
    team.member_role.members.add(u)
    credential.team = team
    credential.save()

    # No permissions pre-migration
    assert not credential.accessible_by(u, permissions['usage'])

    # Usage permissions post migration
    migrated = rbac.migrate_credential(apps, None)
    assert len(migrated) == 1
    assert credential.accessible_by(u, permissions['usage'])

