import pytest
from awx.main.models import Inventory, Host


@pytest.mark.django_db
def test_dashboard_host_count_ignores_constructed_inventories(get, admin_user, organization):
    # 1. Create a standard inventory and host
    base_inv = Inventory.objects.create(name='Base', organization=organization)
    Host.objects.create(name='web-server-01', inventory=base_inv)

    # 2. Create a Constructed Inventory and a duplicate host record
    cons_inv = Inventory.objects.create(name='Constructed', organization=organization, kind='constructed')
    Host.objects.create(name='web-server-01', inventory=cons_inv)

    # 3. Call the dashboard API using the built-in test fixtures
    response = get(url='/api/v2/dashboard/', user=admin_user)

    # 4. Assert that the dashboard completely ignored the constructed inventory duplicate
    assert response.data['hosts']['total'] == 1
