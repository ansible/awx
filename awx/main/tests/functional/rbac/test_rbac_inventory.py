import urllib.parse

import pytest

from awx.api.versioning import reverse
from awx.main.models import (
    Group,
    Host,
    Inventory,
    Organization,
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

    def test_host_filter_edit_unprivileged(self, smart_inventory, user):
        unprivileged = user('unprivileged', False)
        assert not InventoryAccess(unprivileged).can_change(smart_inventory, None)
        assert not InventoryAccess(unprivileged).can_admin(smart_inventory, {'host_filter': 'search=bar'})

    def test_host_filter_edit_inventory_admin_role(self, smart_inventory, user):
        inv_admin = user('inv_admin', False)
        smart_inventory.admin_role.members.add(inv_admin)
        assert InventoryAccess(inv_admin).can_change(smart_inventory, None)
        assert not InventoryAccess(inv_admin).can_admin(smart_inventory, {'host_filter': 'search=bar'})

    def test_host_filter_edit_org_admin_via_api(self, smart_inventory, patch, user):
        oa = user('smart_oa', False)
        smart_inventory.organization.admin_role.members.add(oa)
        url = reverse('api:inventory_detail', kwargs={'pk': smart_inventory.pk})
        resp = patch(url, {'host_filter': 'search=bar'}, oa, expect=200)
        assert resp.data['host_filter'] == 'search=bar'

    @pytest.mark.parametrize("role_field", ['admin_role', 'use_role', 'adhoc_role', 'read_role'])
    def test_inventory_role_cannot_edit_host_filter(self, smart_inventory, patch, user, role_field):
        u = user('role_test_user', False)
        getattr(smart_inventory, role_field).members.add(u)
        url = reverse('api:inventory_detail', kwargs={'pk': smart_inventory.pk})
        patch(url, {'host_filter': 'search=bar'}, u, expect=403)


@pytest.mark.django_db
class TestHostFilterRBAC:
    @pytest.fixture
    def two_org_inventories(self):
        orgA = Organization.objects.create(name="rbac-orgA")
        orgB = Organization.objects.create(name="rbac-orgB")
        invA = Inventory.objects.create(name="rbac-invA", organization=orgA)
        invB = Inventory.objects.create(name="rbac-invB", organization=orgB)
        hostA = Host.objects.create(name="shared_name", inventory=invA)
        hostB = Host.objects.create(name="shared_name", inventory=invB)
        groupA = Group.objects.create(name="shared_group", inventory=invA)
        groupB = Group.objects.create(name="shared_group", inventory=invB)
        groupA.hosts.add(hostA)
        groupB.hosts.add(hostB)
        return {
            'orgA': orgA,
            'orgB': orgB,
            'invA': invA,
            'invB': invB,
            'hostA': hostA,
            'hostB': hostB,
        }

    @pytest.mark.parametrize("host_filter", ["name=shared_name", "groups__name=shared_group"])
    def test_host_filter_scoped_to_inventory_read_role(self, two_org_inventories, get, user, host_filter):
        data = two_org_inventories
        userA = user('rbac_userA', False)
        userB = user('rbac_userB', False)
        data['invA'].read_role.members.add(userA)
        data['invB'].read_role.members.add(userB)

        url = reverse('api:host_list')
        params = "?host_filter=%s" % urllib.parse.quote(host_filter, safe='')

        respA = get(url + params, userA)
        idsA = [h['id'] for h in respA.data['results']]
        assert data['hostA'].id in idsA
        assert data['hostB'].id not in idsA

        respB = get(url + params, userB)
        idsB = [h['id'] for h in respB.data['results']]
        assert data['hostB'].id in idsB
        assert data['hostA'].id not in idsB

    @pytest.mark.parametrize("host_filter", ["name=shared_name", "groups__name=shared_group"])
    def test_host_filter_scoped_to_org_admin(self, two_org_inventories, get, user, host_filter):
        data = two_org_inventories
        adminA = user('rbac_adminA', False)
        adminB = user('rbac_adminB', False)
        data['orgA'].admin_role.members.add(adminA)
        data['orgB'].admin_role.members.add(adminB)

        url = reverse('api:host_list')
        params = "?host_filter=%s" % urllib.parse.quote(host_filter, safe='')

        respA = get(url + params, adminA)
        idsA = [h['id'] for h in respA.data['results']]
        assert data['hostA'].id in idsA
        assert data['hostB'].id not in idsA

        respB = get(url + params, adminB)
        idsB = [h['id'] for h in respB.data['results']]
        assert data['hostB'].id in idsB
        assert data['hostA'].id not in idsB
