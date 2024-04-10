import pytest

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse as django_reverse

from awx.api.versioning import reverse
from awx.main.models import JobTemplate, Inventory, Organization

from ansible_base.rbac.models import RoleDefinition


@pytest.mark.django_db
def test_managed_roles_created(managed_roles):
    "Managed RoleDefinitions are created in post_migration signal, we expect to see them here"
    for cls in (JobTemplate, Inventory):
        ct = ContentType.objects.get_for_model(cls)
        rds = list(RoleDefinition.objects.filter(content_type=ct))
        assert len(rds) > 1
        assert f'{cls.__name__} Admin' in [rd.name for rd in rds]
        for rd in rds:
            assert rd.managed is True


@pytest.mark.django_db
def test_custom_read_role(admin_user, post, managed_roles):
    rd_url = django_reverse('roledefinition-list')
    resp = post(
        url=rd_url, data={"name": "read role made for test", "content_type": "awx.inventory", "permissions": ['view_inventory']}, user=admin_user, expect=201
    )
    rd_id = resp.data['id']
    rd = RoleDefinition.objects.get(id=rd_id)
    assert rd.content_type == ContentType.objects.get_for_model(Inventory)


@pytest.mark.django_db
def test_custom_system_roles_prohibited(admin_user, post):
    rd_url = django_reverse('roledefinition-list')
    resp = post(url=rd_url, data={"name": "read role made for test", "content_type": None, "permissions": ['view_inventory']}, user=admin_user, expect=400)
    assert 'System-wide roles are not enabled' in str(resp.data)


@pytest.mark.django_db
def test_assign_managed_role(admin_user, alice, rando, inventory, post, managed_roles):
    rd = RoleDefinition.objects.get(name='Inventory Admin')
    rd.give_permission(alice, inventory)
    # Now that alice has full permissions to the inventory, she will give rando permission
    url = django_reverse('roleuserassignment-list')
    post(url=url, data={"user": rando.id, "role_definition": rd.id, "object_id": inventory.id}, user=alice, expect=201)
    assert rando.has_obj_perm(inventory, 'change') is True


@pytest.mark.django_db
def test_assign_custom_delete_role(admin_user, rando, inventory, delete, patch):
    rd, _ = RoleDefinition.objects.get_or_create(
        name='inventory-delete', permissions=['delete_inventory', 'view_inventory'], content_type=ContentType.objects.get_for_model(Inventory)
    )
    rd.give_permission(rando, inventory)
    inv_id = inventory.pk
    inv_url = reverse('api:inventory_detail', kwargs={'pk': inv_id})
    patch(url=inv_url, data={"description": "new"}, user=rando, expect=403)
    delete(url=inv_url, user=rando, expect=202)
    assert Inventory.objects.get(id=inv_id).pending_deletion


@pytest.mark.django_db
def test_assign_custom_add_role(admin_user, rando, organization, post, managed_roles):
    rd, _ = RoleDefinition.objects.get_or_create(
        name='inventory-add', permissions=['add_inventory', 'view_organization'], content_type=ContentType.objects.get_for_model(Organization)
    )
    rd.give_permission(rando, organization)
    url = reverse('api:inventory_list')
    r = post(url=url, data={'name': 'abc', 'organization': organization.id}, user=rando, expect=201)
    inv_id = r.data['id']
    inventory = Inventory.objects.get(id=inv_id)
    assert rando.has_obj_perm(inventory, 'change')
