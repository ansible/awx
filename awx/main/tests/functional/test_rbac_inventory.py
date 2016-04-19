import pytest

from awx.main.migrations import _rbac as rbac
from awx.main.models import (
    Permission,
    Host,
    CustomInventoryScript,
)
from awx.main.access import InventoryAccess, HostAccess
from django.apps import apps

@pytest.mark.django_db
def test_custom_inv_script_access(organization, user):
    u = user('user', False)

    custom_inv = CustomInventoryScript.objects.create(name='test', script='test', description='test')
    custom_inv.organization = organization
    custom_inv.save()
    assert u not in custom_inv.read_role

    organization.member_role.members.add(u)
    assert u in custom_inv.read_role

@pytest.mark.django_db
def test_inventory_admin_user(inventory, permissions, user):
    u = user('admin', False)
    perm = Permission(user=u, inventory=inventory, permission_type='admin')
    perm.save()

    assert u not in inventory.admin_role

    rbac.migrate_inventory(apps, None)

    assert u in inventory.admin_role
    assert inventory.execute_role.members.filter(id=u.id).exists() is False
    assert inventory.update_role.members.filter(id=u.id).exists() is False

@pytest.mark.django_db
def test_inventory_auditor_user(inventory, permissions, user):
    u = user('auditor', False)
    perm = Permission(user=u, inventory=inventory, permission_type='read')
    perm.save()

    assert u not in inventory.admin_role
    assert u not in inventory.auditor_role

    rbac.migrate_inventory(apps, None)

    assert u not in inventory.admin_role
    assert u in inventory.auditor_role
    assert inventory.execute_role.members.filter(id=u.id).exists() is False
    assert inventory.update_role.members.filter(id=u.id).exists() is False

@pytest.mark.django_db
def test_inventory_updater_user(inventory, permissions, user):
    u = user('updater', False)
    perm = Permission(user=u, inventory=inventory, permission_type='write')
    perm.save()

    assert u not in inventory.admin_role
    assert u not in inventory.auditor_role

    rbac.migrate_inventory(apps, None)

    assert u not in inventory.admin_role
    assert inventory.execute_role.members.filter(id=u.id).exists() is False
    assert inventory.update_role.members.filter(id=u.id).exists()

@pytest.mark.django_db
def test_inventory_executor_user(inventory, permissions, user):
    u = user('executor', False)
    perm = Permission(user=u, inventory=inventory, permission_type='read', run_ad_hoc_commands=True)
    perm.save()

    assert u not in inventory.admin_role
    assert u not in inventory.auditor_role

    rbac.migrate_inventory(apps, None)

    assert u not in inventory.admin_role
    assert u in inventory.read_role
    assert inventory.execute_role.members.filter(id=u.id).exists()
    assert inventory.update_role.members.filter(id=u.id).exists() is False



@pytest.mark.django_db
def test_inventory_admin_team(inventory, permissions, user, team):
    u = user('admin', False)
    perm = Permission(team=team, inventory=inventory, permission_type='admin')
    perm.save()
    team.deprecated_users.add(u)

    assert u not in inventory.admin_role

    rbac.migrate_team(apps, None)
    rbac.migrate_inventory(apps, None)

    assert team.member_role.members.count() == 1
    assert inventory.admin_role.members.filter(id=u.id).exists() is False
    assert inventory.auditor_role.members.filter(id=u.id).exists() is False
    assert inventory.execute_role.members.filter(id=u.id).exists() is False
    assert inventory.update_role.members.filter(id=u.id).exists() is False
    assert u in inventory.read_role
    assert u in inventory.admin_role


@pytest.mark.django_db
def test_inventory_auditor(inventory, permissions, user, team):
    u = user('auditor', False)
    perm = Permission(team=team, inventory=inventory, permission_type='read')
    perm.save()
    team.deprecated_users.add(u)

    assert u not in inventory.admin_role
    assert u not in inventory.auditor_role

    rbac.migrate_team(apps,None)
    rbac.migrate_inventory(apps, None)

    assert team.member_role.members.count() == 1
    assert inventory.admin_role.members.filter(id=u.id).exists() is False
    assert inventory.auditor_role.members.filter(id=u.id).exists() is False
    assert inventory.execute_role.members.filter(id=u.id).exists() is False
    assert inventory.update_role.members.filter(id=u.id).exists() is False
    assert u in inventory.read_role
    assert u not in inventory.admin_role

@pytest.mark.django_db
def test_inventory_updater(inventory, permissions, user, team):
    u = user('updater', False)
    perm = Permission(team=team, inventory=inventory, permission_type='write')
    perm.save()
    team.deprecated_users.add(u)

    assert u not in inventory.admin_role
    assert u not in inventory.auditor_role

    rbac.migrate_team(apps,None)
    rbac.migrate_inventory(apps, None)

    assert team.member_role.members.count() == 1
    assert inventory.admin_role.members.filter(id=u.id).exists() is False
    assert inventory.auditor_role.members.filter(id=u.id).exists() is False
    assert inventory.execute_role.members.filter(id=u.id).exists() is False
    assert inventory.update_role.members.filter(id=u.id).exists() is False
    assert team.member_role.is_ancestor_of(inventory.update_role)
    assert team.member_role.is_ancestor_of(inventory.execute_role) is False


@pytest.mark.django_db
def test_inventory_executor(inventory, permissions, user, team):
    u = user('executor', False)
    perm = Permission(team=team, inventory=inventory, permission_type='read', run_ad_hoc_commands=True)
    perm.save()
    team.deprecated_users.add(u)

    assert u not in inventory.admin_role
    assert u not in inventory.auditor_role

    rbac.migrate_team(apps, None)
    rbac.migrate_inventory(apps, None)

    assert team.member_role.members.count() == 1
    assert inventory.admin_role.members.filter(id=u.id).exists() is False
    assert inventory.auditor_role.members.filter(id=u.id).exists() is False
    assert inventory.execute_role.members.filter(id=u.id).exists() is False
    assert inventory.update_role.members.filter(id=u.id).exists() is False
    assert team.member_role.is_ancestor_of(inventory.update_role) is False
    assert team.member_role.is_ancestor_of(inventory.execute_role)

@pytest.mark.django_db
def test_group_parent_admin(group, permissions, user):
    u = user('admin', False)
    parent1 = group('parent-1')
    parent2 = group('parent-2')
    childA = group('child-1')

    parent1.admin_role.members.add(u)
    assert u in parent1.admin_role
    assert u not in parent2.admin_role
    assert u not in childA.admin_role

    childA.parents.add(parent1)
    assert u in childA.admin_role

    childA.parents.remove(parent1)
    assert u not in childA.admin_role

    parent2.children.add(childA)
    assert u not in childA.admin_role

    parent2.admin_role.members.add(u)
    assert u in childA.admin_role

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

    inventory_admin_access = HostAccess(inventory_admin)
    group_admin_access = HostAccess(group_admin)

    h1 = Host.objects.create(inventory=inventory, name='host1')
    h2 = Host.objects.create(inventory=inventory, name='host2')
    h1.groups.add(my_group)
    h2.groups.add(not_my_group)

    assert inventory_admin_access.can_read(h1) is False
    assert group_admin_access.can_read(h1) is False

    inventory.admin_role.members.add(inventory_admin)
    my_group.admin_role.members.add(group_admin)

    assert inventory_admin_access.can_read(h1)
    assert inventory_admin_access.can_read(h2)
    assert group_admin_access.can_read(h1)
    assert group_admin_access.can_read(h2) is False

    my_group.hosts.remove(h1)

    assert inventory_admin_access.can_read(h1)
    assert group_admin_access.can_read(h1) is False

    h1.inventory = other_inventory
    h1.save()

    assert inventory_admin_access.can_read(h1) is False
    assert group_admin_access.can_read(h1) is False



