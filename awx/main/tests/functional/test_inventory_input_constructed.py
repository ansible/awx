import pytest
from awx.main.models import Inventory
from awx.api.versioning import reverse


@pytest.mark.django_db
def test_constructed_inventory_post(post, organization, admin_user):
    inventory1 = Inventory.objects.create(name='dummy1', kind='constructed', organization=organization)
    inventory2 = Inventory.objects.create(name='dummy2', kind='constructed', organization=organization)
    resp = post(
        url=reverse('api:inventory_input_inventories', kwargs={'pk': inventory1.id}),
        data={'id': inventory2.id},
        user=admin_user,
        expect=405,
    )
    print(resp)
    assert resp.status_code == 405
