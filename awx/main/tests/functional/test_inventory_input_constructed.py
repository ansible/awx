import pytest
from awx.main.models import Inventory
from awx.api.versioning import reverse


@pytest.fixture
def constructed_inventory(organization):
    """
    creates a new constructed inventory source
    """

    def factory(name, org=organization):
        try:
            inv = Inventory.objects.get(name=name, organization=org, kind='constructed')
        except Inventory.DoesNotExist:
            inv = Inventory.objects.create(name=name, organization=org, kind='constructed')
        return inv

    return factory


@pytest.mark.django_db
def test_constructed_inventory_post(post, admin_user, constructed_inventory):
    inv1 = constructed_inventory(name='dummy1')
    inv2 = constructed_inventory(name='dummy2')
    resp = post(
        url=reverse('api:inventory_input_inventories', kwargs={'pk': inv1.pk}),
        data={'id': inv2.pk},
        user=admin_user,
        expect=400,
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_add_constructed_inventory_source(post, admin_user, constructed_inventory):
    inv1 = constructed_inventory(name='dummy1')
    resp = post(
        url=reverse('api:inventory_inventory_sources_list', kwargs={'pk': inv1.pk}),
        data={'name': 'dummy1', 'source': 'constructed'},
        user=admin_user,
        expect=400,
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_add_constructed_inventory_host(post, admin_user, constructed_inventory):
    inv1 = constructed_inventory(name='dummy1')
    resp = post(
        url=reverse('api:inventory_hosts_list', kwargs={'pk': inv1.pk}),
        data={'name': 'dummy1'},
        user=admin_user,
        expect=400,
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_add_constructed_inventory_group(post, admin_user, constructed_inventory):
    inv1 = constructed_inventory(name='dummy1')
    resp = post(
        reverse('api:inventory_groups_list', kwargs={'pk': inv1.pk}),
        data={'name': 'group-test'},
        user=admin_user,
        expect=400,
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_edit_constructed_inventory_source(patch, admin_user, inventory_source_factory):
    inv_src = inventory_source_factory(name='dummy1', source='constructed')
    resp = patch(
        reverse('api:inventory_source_detail', kwargs={'pk': inv_src.id}),
        data={'description': inv_src.name},
        user=admin_user,
        expect=400,
    )
    assert resp.status_code == 400
