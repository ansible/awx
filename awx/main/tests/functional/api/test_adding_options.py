import pytest

from django.core.urlresolvers import reverse

@pytest.mark.django_db
def test_inventory_group_host_can_add(inventory, alice, options):
    inventory.admin_role.members.add(alice)

    response = options(reverse('api:inventory_hosts_list', args=[inventory.pk]), alice)
    assert 'POST' in response.data['actions']
    response = options(reverse('api:inventory_groups_list', args=[inventory.pk]), alice)
    assert 'POST' in response.data['actions']


@pytest.mark.django_db
def test_inventory_group_host_can_not_add(inventory, bob, options):
    inventory.read_role.members.add(bob)

    response = options(reverse('api:inventory_hosts_list', args=[inventory.pk]), bob)
    assert 'POST' not in response.data['actions']
    response = options(reverse('api:inventory_groups_list', args=[inventory.pk]), bob)
    assert 'POST' not in response.data['actions']
