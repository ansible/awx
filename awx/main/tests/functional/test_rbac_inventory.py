import pytest

from awx.main.models import (
    Host,
    Schedule,
)
from awx.main.access import (
    InventoryAccess,
    InventorySourceAccess,
    HostAccess,
    InventoryUpdateAccess,
    ScheduleAccess,
)


@pytest.mark.django_db
@pytest.mark.parametrize("role", ["admin_role", "inventory_admin_role"])
def test_access_admin(role, organization, inventory, user):
    a = user('admin', False)
    inventory.organization = organization

    role = getattr(organization, role)
    role.members.add(a)

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


@pytest.mark.parametrize("role_field,allowed", [(None, False), ('admin_role', True), ('update_role', False), ('adhoc_role', False), ('use_role', False)])
@pytest.mark.django_db
def test_inventory_source_delete(inventory_source, alice, role_field, allowed):
    if role_field:
        getattr(inventory_source.inventory, role_field).members.add(alice)
    assert allowed == InventorySourceAccess(alice).can_delete(inventory_source), '{} test failed'.format(role_field)


# See companion test in tests/functional/api/test_inventory.py::test_inventory_update_access_called
@pytest.mark.parametrize("role_field,allowed", [(None, False), ('admin_role', True), ('update_role', True), ('adhoc_role', False), ('use_role', False)])
@pytest.mark.django_db
def test_inventory_source_update(inventory_source, alice, role_field, allowed):
    if role_field:
        getattr(inventory_source.inventory, role_field).members.add(alice)
    assert allowed == InventorySourceAccess(alice).can_start(inventory_source), '{} test failed'.format(role_field)


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


@pytest.mark.django_db
def test_inventory_source_credential_check(rando, inventory_source, credential):
    inventory_source.inventory.admin_role.members.add(rando)
    access = InventorySourceAccess(rando)
    assert not access.can_attach(inventory_source, credential, 'credentials', {'id': credential.pk})


@pytest.mark.django_db
def test_inventory_source_org_admin_schedule_access(org_admin, inventory_source):
    schedule = Schedule.objects.create(unified_job_template=inventory_source, rrule='DTSTART:20151117T050000Z RRULE:FREQ=DAILY;INTERVAL=1;COUNT=1')
    access = ScheduleAccess(org_admin)
    assert access.get_queryset()
    assert access.can_read(schedule)
    assert access.can_change(schedule, {'rrule': 'DTSTART:20151117T050000Z RRULE:FREQ=DAILY;INTERVAL=1;COUNT=2'})


@pytest.fixture
def smart_inventory(organization):
    return organization.inventories.create(name="smart-inv", kind="smart")


@pytest.mark.django_db
class TestSmartInventory:
    def test_host_filter_edit(self, smart_inventory, rando, org_admin):
        assert InventoryAccess(org_admin).can_admin(smart_inventory, {'host_filter': 'search=foo'})
        smart_inventory.admin_role.members.add(rando)
        assert not InventoryAccess(rando).can_admin(smart_inventory, {'host_filter': 'search=foo'})
