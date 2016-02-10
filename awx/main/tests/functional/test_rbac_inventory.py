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

    migrations = rbac.migrate_inventory(apps, None)

    assert len(migrations[inventory.name]['users']) == 1
    assert len(migrations[inventory.name]['teams']) == 0
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

    migrations = rbac.migrate_inventory(apps, None)

    assert len(migrations[inventory.name]['users']) == 1
    assert len(migrations[inventory.name]['teams']) == 0
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

    migrations = rbac.migrate_inventory(apps, None)

    assert len(migrations[inventory.name]['users']) == 1
    assert len(migrations[inventory.name]['teams']) == 0
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

    migrations = rbac.migrate_inventory(apps, None)

    assert len(migrations[inventory.name]['users']) == 1
    assert len(migrations[inventory.name]['teams']) == 0
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
    migrations = rbac.migrate_inventory(apps, None)

    assert len(team_migrations) == 1
    assert team.member_role.members.count() == 1
    assert len(migrations[inventory.name]['users']) == 0
    assert len(migrations[inventory.name]['teams']) == 1
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
    migrations = rbac.migrate_inventory(apps, None)

    assert len(team_migrations) == 1
    assert team.member_role.members.count() == 1
    assert len(migrations[inventory.name]['users']) == 0
    assert len(migrations[inventory.name]['teams']) == 1
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
    migrations = rbac.migrate_inventory(apps, None)

    assert len(team_migrations) == 1
    assert team.member_role.members.count() == 1
    assert len(migrations[inventory.name]['users']) == 0
    assert len(migrations[inventory.name]['teams']) == 1
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
    migrations = rbac.migrate_inventory(apps, None)

    assert len(team_migrations) == 1
    assert team.member_role.members.count() == 1
    assert len(migrations[inventory.name]['users']) == 0
    assert len(migrations[inventory.name]['teams']) == 1
    assert inventory.admin_role.members.filter(id=u.id).exists() is False
    assert inventory.auditor_role.members.filter(id=u.id).exists() is False
    assert inventory.executor_role.members.filter(id=u.id).exists() is False
    assert inventory.updater_role.members.filter(id=u.id).exists() is False
    assert team.member_role.is_ancestor_of(inventory.updater_role) is False
    assert team.member_role.is_ancestor_of(inventory.executor_role)

@pytest.mark.django_db
def test_group_parent_admin(group, permissions, user):
    u = user('admin', False)
    parent1 = group('parent-1')
    parent2 = group('parent-2')
    childA = group('child-1')

    parent1.admin_role.members.add(u)
    assert parent1.accessible_by(u, permissions['admin'])
    assert not parent2.accessible_by(u, permissions['admin'])
    assert not childA.accessible_by(u, permissions['admin'])

    childA.parents.add(parent1)
    assert childA.accessible_by(u, permissions['admin'])

    childA.parents.remove(parent1)
    assert not childA.accessible_by(u, permissions['admin'])

    parent2.children.add(childA)
    assert not childA.accessible_by(u, permissions['admin'])

    parent2.admin_role.members.add(u)
    assert childA.accessible_by(u, permissions['admin'])
