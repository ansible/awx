import pytest

from awx.main.migrations import _rbac as rbac
from awx.main.models import Permission
from django.apps import apps

@pytest.mark.django_db
def test_inventory_admin_user(inventory, permissions, user):
    u = user('admin', False)
    perm = Permission(user=u, inventory=inventory, permission_type='admin')
    perm.save()

    assert inventory.accessible_by(u, permissions['admin']) is False

    migrations = inventory.migrate_to_rbac()

    assert len(migrations['migrated_users']) == 1
    assert len(migrations['migrated_teams']) == 0
    assert inventory.accessible_by(u, permissions['admin'])
    assert inventory.executor_role.members.filter(id=u.id).exists() is False
    assert inventory.updater_role.members.filter(id=u.id).exists() is False

@pytest.mark.django_db
def test_inventory_auditor_user(inventory, permissions, user):
    u = user('auditor', False)
    perm = Permission(user=u, inventory=inventory, permission_type='read')
    perm.save()

    assert inventory.accessible_by(u, permissions['admin']) is False
    assert inventory.accessible_by(u, permissions['auditor']) is False

    migrations = inventory.migrate_to_rbac()

    assert len(migrations['migrated_users']) == 1
    assert len(migrations['migrated_teams']) == 0
    assert inventory.accessible_by(u, permissions['admin']) is False
    assert inventory.accessible_by(u, permissions['auditor']) is True
    assert inventory.executor_role.members.filter(id=u.id).exists() is False
    assert inventory.updater_role.members.filter(id=u.id).exists() is False

@pytest.mark.django_db
def test_inventory_updater_user(inventory, permissions, user):
    u = user('updater', False)
    perm = Permission(user=u, inventory=inventory, permission_type='write')
    perm.save()

    assert inventory.accessible_by(u, permissions['admin']) is False
    assert inventory.accessible_by(u, permissions['auditor']) is False

    migrations = inventory.migrate_to_rbac()

    assert len(migrations['migrated_users']) == 1
    assert len(migrations['migrated_teams']) == 0
    assert inventory.accessible_by(u, permissions['admin']) is False
    assert inventory.executor_role.members.filter(id=u.id).exists() is False
    assert inventory.updater_role.members.filter(id=u.id).exists()

@pytest.mark.django_db
def test_inventory_executor_user(inventory, permissions, user):
    u = user('executor', False)
    perm = Permission(user=u, inventory=inventory, permission_type='read', run_ad_hoc_commands=True)
    perm.save()

    assert inventory.accessible_by(u, permissions['admin']) is False
    assert inventory.accessible_by(u, permissions['auditor']) is False

    migrations = inventory.migrate_to_rbac()

    assert len(migrations['migrated_users']) == 1
    assert len(migrations['migrated_teams']) == 0
    assert inventory.accessible_by(u, permissions['admin']) is False
    assert inventory.accessible_by(u, permissions['auditor']) is True
    assert inventory.executor_role.members.filter(id=u.id).exists()
    assert inventory.updater_role.members.filter(id=u.id).exists() is False



@pytest.mark.django_db
def test_inventory_admin_team(inventory, permissions, user, team):
    u = user('admin', False)
    perm = Permission(team=team, inventory=inventory, permission_type='admin')
    perm.save()
    team.users.add(u)

    assert inventory.accessible_by(u, permissions['admin']) is False

    team_migrations = rbac.migrate_team(apps, None)
    migrations = inventory.migrate_to_rbac()

    assert len(team_migrations) == 1
    assert team.member_role.members.count() == 1
    assert len(migrations['migrated_users']) == 0
    assert len(migrations['migrated_teams']) == 1
    assert inventory.admin_role.members.filter(id=u.id).exists() is False
    assert inventory.auditor_role.members.filter(id=u.id).exists() is False
    assert inventory.executor_role.members.filter(id=u.id).exists() is False
    assert inventory.updater_role.members.filter(id=u.id).exists() is False
    assert inventory.accessible_by(u, permissions['auditor'])
    assert inventory.accessible_by(u, permissions['admin'])


@pytest.mark.django_db
def test_inventory_auditor(inventory, permissions, user, team):
    u = user('auditor', False)
    perm = Permission(team=team, inventory=inventory, permission_type='read')
    perm.save()
    team.users.add(u)

    assert inventory.accessible_by(u, permissions['admin']) is False
    assert inventory.accessible_by(u, permissions['auditor']) is False

    team_migrations = rbac.migrate_team(apps,None)
    migrations = inventory.migrate_to_rbac()

    assert len(team_migrations) == 1
    assert team.member_role.members.count() == 1
    assert len(migrations['migrated_users']) == 0
    assert len(migrations['migrated_teams']) == 1
    assert inventory.admin_role.members.filter(id=u.id).exists() is False
    assert inventory.auditor_role.members.filter(id=u.id).exists() is False
    assert inventory.executor_role.members.filter(id=u.id).exists() is False
    assert inventory.updater_role.members.filter(id=u.id).exists() is False
    assert inventory.accessible_by(u, permissions['auditor'])
    assert inventory.accessible_by(u, permissions['admin']) is False

@pytest.mark.django_db
def test_inventory_updater(inventory, permissions, user, team):
    u = user('updater', False)
    perm = Permission(team=team, inventory=inventory, permission_type='write')
    perm.save()
    team.users.add(u)

    assert inventory.accessible_by(u, permissions['admin']) is False
    assert inventory.accessible_by(u, permissions['auditor']) is False

    team_migrations = rbac.migrate_team(apps,None)
    migrations = inventory.migrate_to_rbac()

    assert len(team_migrations) == 1
    assert team.member_role.members.count() == 1
    assert len(migrations['migrated_users']) == 0
    assert len(migrations['migrated_teams']) == 1
    assert inventory.admin_role.members.filter(id=u.id).exists() is False
    assert inventory.auditor_role.members.filter(id=u.id).exists() is False
    assert inventory.executor_role.members.filter(id=u.id).exists() is False
    assert inventory.updater_role.members.filter(id=u.id).exists() is False
    assert team.member_role.is_ancestor_of(inventory.updater_role)
    assert team.member_role.is_ancestor_of(inventory.executor_role) is False


@pytest.mark.django_db
def test_inventory_executor(inventory, permissions, user, team):
    u = user('executor', False)
    perm = Permission(team=team, inventory=inventory, permission_type='read', run_ad_hoc_commands=True)
    perm.save()
    team.users.add(u)

    assert inventory.accessible_by(u, permissions['admin']) is False
    assert inventory.accessible_by(u, permissions['auditor']) is False

    team_migrations = rbac.migrate_team(apps, None)
    migrations = inventory.migrate_to_rbac()

    assert len(team_migrations) == 1
    assert team.member_role.members.count() == 1
    assert len(migrations['migrated_users']) == 0
    assert len(migrations['migrated_teams']) == 1
    assert inventory.admin_role.members.filter(id=u.id).exists() is False
    assert inventory.auditor_role.members.filter(id=u.id).exists() is False
    assert inventory.executor_role.members.filter(id=u.id).exists() is False
    assert inventory.updater_role.members.filter(id=u.id).exists() is False
    assert team.member_role.is_ancestor_of(inventory.updater_role) is False
    assert team.member_role.is_ancestor_of(inventory.executor_role)

