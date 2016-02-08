import pytest

from awx.main.migrations import _rbac as rbac
from django.apps import apps

@pytest.mark.django_db
def test_team_migration_user(team, user, permissions):
    u = user('user', False)
    team.users.add(u)
    team.save()

    assert not team.accessible_by(u, permissions['auditor'])

    migrated = rbac.migrate_team(apps, None)

    assert len(migrated) == 1
    assert team.accessible_by(u, permissions['auditor'])
