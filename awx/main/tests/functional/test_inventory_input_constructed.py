import pytest
from awx.main.models import Inventory
from awx.api.versioning import reverse


@pytest.fixture
def constructed_inventory(organization):
    """
    creates a new constructed inventory source
    """
    return Inventory.objects.create(name='dummy2', kind='constructed', organization=organization)


@pytest.mark.django_db
def test_constructed_inventory_post(post, organization, admin_user):
    inventory1 = Inventory.objects.create(name='dummy1', kind='constructed', organization=organization)
    inventory2 = Inventory.objects.create(name='dummy2', kind='constructed', organization=organization)
    resp = post(
        url=reverse('api:inventory_input_inventories', kwargs={'pk': inventory1.pk}),
        data={'id': inventory2.pk},
        user=admin_user,
        expect=405,
    )
    assert resp.status_code == 405


@pytest.mark.django_db
def test_add_constructed_inventory_source(post, admin_user, constructed_inventory):
    resp = post(
        url=reverse('api:inventory_inventory_sources_list', kwargs={'pk': constructed_inventory.pk}),
        data={'name': 'dummy1', 'source': 'constructed'},
        user=admin_user,
        expect=400,
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_add_constructed_inventory_host(post, admin_user, constructed_inventory):
    resp = post(
        url=reverse('api:inventory_hosts_list', kwargs={'pk': constructed_inventory.pk}),
        data={'name': 'dummy1'},
        user=admin_user,
        expect=400,
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_add_constructed_inventory_group(post, admin_user, constructed_inventory):
    resp = post(
        reverse('api:inventory_groups_list', kwargs={'pk': constructed_inventory.pk}),
        data={'name': 'group-test'},
        user=admin_user,
        expect=400,
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_edit_constructed_inventory_source(patch, admin_user, inventory):
    inventory.inventory_sources.create(name="dummysrc", source="constructed")
    inv_id = inventory.inventory_sources.get(name='dummysrc').id
    resp = patch(
        reverse('api:inventory_source_detail', kwargs={'pk': inv_id}),
        data={'description': inventory.name},
        user=admin_user,
        expect=400,
    )
    assert resp.status_code == 400
