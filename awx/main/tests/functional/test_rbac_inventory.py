import pytest

from awx.main.migrations import _rbac as rbac
from awx.main.models import Permission, Host
from awx.main.access import InventoryAccess
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
    team.deprecated_users.add(u)

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
    team.deprecated_users.add(u)

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
    team.deprecated_users.add(u)

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
    team.deprecated_users.add(u)

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

@pytest.mark.django_db
def test_access_admin(organization, inventory, user):
    a = user('admin', False)
    inventory.organization = organization
    organization.admin_role.members.add(a)

    access = InventoryAccess(a)
    assert access.can_read(inventory)
    assert access.can_add(None)
    assert access.can_add({'organization': organization.id})
    assert access.can_change(inventory, None)
    assert access.can_change(inventory, {'organization': organization.id})
    assert access.can_admin(inventory, None)
    assert access.can_admin(inventory, {'organization': organization.id})
    assert access.can_delete(inventory)
    assert access.can_run_ad_hoc_commands(inventory)

@pytest.mark.django_db
def test_access_auditor(organization, inventory, user):
    u = user('admin', False)
    inventory.organization = organization
    organization.auditor_role.members.add(u)

    access = InventoryAccess(u)
    assert access.can_read(inventory)
    assert not access.can_add(None)
    assert not access.can_add({'organization': organization.id})
    assert not access.can_change(inventory, None)
    assert not access.can_change(inventory, {'organization': organization.id})
    assert not access.can_admin(inventory, None)
    assert not access.can_admin(inventory, {'organization': organization.id})
    assert not access.can_delete(inventory)
    assert not access.can_run_ad_hoc_commands(inventory)



@pytest.mark.django_db
def test_host_access(organization, inventory, user, group):
    other_inventory = organization.inventories.create(name='other-inventory')
    inventory_admin = user('inventory_admin', False)
    my_group = group('my-group')
    not_my_group = group('not-my-group')
    group_admin = user('group_admin', False)


    h1 = Host.objects.create(inventory=inventory, name='host1')
    h2 = Host.objects.create(inventory=inventory, name='host2')
    h1.groups.add(my_group)
    h2.groups.add(not_my_group)

    assert h1.accessible_by(inventory_admin, {'read': True}) is False
    assert h1.accessible_by(group_admin, {'read': True}) is False

    inventory.admin_role.members.add(inventory_admin)
    my_group.admin_role.members.add(group_admin)

    assert h1.accessible_by(inventory_admin, {'read': True})
    assert h2.accessible_by(inventory_admin, {'read': True})
    assert h1.accessible_by(group_admin, {'read': True})
    assert h2.accessible_by(group_admin, {'read': True}) is False

    my_group.hosts.remove(h1)

    assert h1.accessible_by(inventory_admin, {'read': True})
    assert h1.accessible_by(group_admin, {'read': True}) is False

    h1.inventory = other_inventory
    h1.save()

    assert h1.accessible_by(inventory_admin, {'read': True}) is False
    assert h1.accessible_by(group_admin, {'read': True}) is False



