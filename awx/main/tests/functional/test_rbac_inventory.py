import pytest

from awx.main.migrations import _rbac as rbac
from awx.main.models import (
    Permission,
    Host,
    CustomInventoryScript,
)
from awx.main.access import (
    InventoryAccess,
    HostAccess,
    InventoryUpdateAccess,
    CustomInventoryScriptAccess
)
from django.apps import apps

@pytest.mark.django_db
def test_custom_inv_script_access(organization, user):
    u = user('user', False)
    ou = user('oadm', False)

    custom_inv = CustomInventoryScript.objects.create(name='test', script='test', description='test')
    custom_inv.organization = organization
    custom_inv.save()
    assert u not in custom_inv.read_role

    organization.member_role.members.add(u)
    assert u in custom_inv.read_role

    organization.admin_role.members.add(ou)
    assert ou in custom_inv.admin_role

@pytest.mark.django_db
def test_modify_inv_script_foreign_org_admin(org_admin, organization, organization_factory, project):
    custom_inv = CustomInventoryScript.objects.create(name='test', script='test', description='test')
    custom_inv.organization = organization
    custom_inv.save()

    other_org = organization_factory('not-my-org').organization
    access = CustomInventoryScriptAccess(org_admin)
    assert not access.can_change(custom_inv, {'organization': other_org.pk, 'name': 'new-project'})

@pytest.mark.django_db
def test_inventory_admin_user(inventory, permissions, user):
    u = user('admin', False)
    perm = Permission(user=u, inventory=inventory, permission_type='admin')
    perm.save()

    assert u not in inventory.admin_role

    rbac.migrate_inventory(apps, None)

    assert u in inventory.admin_role
    assert inventory.use_role.members.filter(id=u.id).exists() is False
    assert inventory.update_role.members.filter(id=u.id).exists() is False

@pytest.mark.django_db
def test_inventory_auditor_user(inventory, permissions, user):
    u = user('auditor', False)
    perm = Permission(user=u, inventory=inventory, permission_type='read')
    perm.save()

    assert u not in inventory.admin_role
    assert u not in inventory.read_role

    rbac.migrate_inventory(apps, None)

    assert u not in inventory.admin_role
    assert u in inventory.read_role
    assert inventory.use_role.members.filter(id=u.id).exists() is False
    assert inventory.update_role.members.filter(id=u.id).exists() is False

@pytest.mark.django_db
def test_inventory_updater_user(inventory, permissions, user):
    u = user('updater', False)
    perm = Permission(user=u, inventory=inventory, permission_type='write')
    perm.save()

    assert u not in inventory.admin_role
    assert u not in inventory.read_role

    rbac.migrate_inventory(apps, None)

    assert u not in inventory.admin_role
    assert inventory.use_role.members.filter(id=u.id).exists() is False
    assert inventory.update_role.members.filter(id=u.id).exists()

@pytest.mark.django_db
def test_inventory_executor_user(inventory, permissions, user):
    u = user('executor', False)
    perm = Permission(user=u, inventory=inventory, permission_type='read', run_ad_hoc_commands=True)
    perm.save()

    assert u not in inventory.admin_role
    assert u not in inventory.read_role

    rbac.migrate_inventory(apps, None)

    assert u not in inventory.admin_role
    assert u in inventory.read_role
    assert inventory.use_role.members.filter(id=u.id).exists()
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
    assert inventory.read_role.members.filter(id=u.id).exists() is False
    assert inventory.use_role.members.filter(id=u.id).exists() is False
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
    assert u not in inventory.read_role

    rbac.migrate_team(apps,None)
    rbac.migrate_inventory(apps, None)

    assert team.member_role.members.count() == 1
    assert inventory.admin_role.members.filter(id=u.id).exists() is False
    assert inventory.read_role.members.filter(id=u.id).exists() is False
    assert inventory.use_role.members.filter(id=u.id).exists() is False
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
    assert u not in inventory.read_role

    rbac.migrate_team(apps,None)
    rbac.migrate_inventory(apps, None)

    assert team.member_role.members.count() == 1
    assert inventory.admin_role.members.filter(id=u.id).exists() is False
    assert inventory.read_role.members.filter(id=u.id).exists() is False
    assert inventory.use_role.members.filter(id=u.id).exists() is False
    assert inventory.update_role.members.filter(id=u.id).exists() is False
    assert team.member_role.is_ancestor_of(inventory.update_role)
    assert team.member_role.is_ancestor_of(inventory.use_role) is False


@pytest.mark.django_db
def test_inventory_executor(inventory, permissions, user, team):
    u = user('executor', False)
    perm = Permission(team=team, inventory=inventory, permission_type='read', run_ad_hoc_commands=True)
    perm.save()
    team.deprecated_users.add(u)

    assert u not in inventory.admin_role
    assert u not in inventory.read_role

    rbac.migrate_team(apps, None)
    rbac.migrate_inventory(apps, None)

    assert team.member_role.members.count() == 1
    assert inventory.admin_role.members.filter(id=u.id).exists() is False
    assert inventory.read_role.members.filter(id=u.id).exists() is False
    assert inventory.use_role.members.filter(id=u.id).exists() is False
    assert inventory.update_role.members.filter(id=u.id).exists() is False
    assert team.member_role.is_ancestor_of(inventory.update_role) is False
    assert team.member_role.is_ancestor_of(inventory.use_role)


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
def test_inventory_update_org_admin(inventory_update, org_admin):
    access = InventoryUpdateAccess(org_admin)
    assert access.can_delete(inventory_update)


@pytest.mark.django_db
def test_host_access(organization, inventory, group, user, group_factory):
    other_inventory = organization.inventories.create(name='other-inventory')
    inventory_admin = user('inventory_admin', False)

    inventory_admin_access = HostAccess(inventory_admin)

    host = Host.objects.create(inventory=inventory, name='host1')
    host.groups.add(group)

    assert inventory_admin_access.can_read(host) is False

    inventory.admin_role.members.add(inventory_admin)

    assert inventory_admin_access.can_read(host)

    group.hosts.remove(host)

    assert inventory_admin_access.can_read(host)

    host.inventory = other_inventory
    host.save()

    assert inventory_admin_access.can_read(host) is False



