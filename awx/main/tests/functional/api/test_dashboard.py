import pytest

from awx.api.versioning import reverse
from awx.main.models import Host, Inventory


@pytest.mark.django_db
def test_dashboard_hosts_total_excludes_constructed(get, admin_user, organization):
    """
    Constructed inventory hosts are not counted in the dashboard
    """
    source_inv = Inventory.objects.create(name='source-inv', organization=organization)
    source_host = source_inv.hosts.create(name='host1')

    constructed = Inventory.objects.create(name='constructed-inv', kind='constructed', organization=organization)
    Host.objects.create(name='host1', inventory=constructed, instance_id=str(source_host.pk))

    response = get(reverse('api:dashboard_view'), user=admin_user, expect=200)
    assert response.data['hosts']['total'] == 1


@pytest.mark.django_db
def test_host_list_still_returns_constructed(get, admin_user, organization):
    """
    Constructed inventory hosts are still visible through the API
    """
    source_inv = Inventory.objects.create(name='source-inv', organization=organization)
    source_host = source_inv.hosts.create(name='host1')

    constructed = Inventory.objects.create(name='constructed-inv', kind='constructed', organization=organization)
    Host.objects.create(name='host1', inventory=constructed, instance_id=str(source_host.pk))

    response = get(reverse('api:host_list'), user=admin_user, expect=200)
    assert response.data['count'] == 2
