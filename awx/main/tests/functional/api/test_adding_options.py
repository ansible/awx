import pytest

from django.core.urlresolvers import reverse

@pytest.fixture
def test_inventory_group_add(inventory, alice, bob, options):
    inventory.admin_role.add(alice)
    response = options(reverse('api:inventory_detail', args=[inventory.pk]), alice)
    print ' resp: ' + str(response.data)
    assert 'POST' in response.data

    inventory.read_role.add(bob)
    
    
