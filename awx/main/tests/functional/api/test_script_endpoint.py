import pytest
import json
from awx.api.versioning import reverse

from awx.main.models import Inventory, Host


@pytest.mark.django_db
def test_empty_inventory(post, get, admin_user, organization, group_factory):
    inventory = Inventory(name='basic_inventory',
                          kind='',
                          organization=organization)
    inventory.save()
    resp = get(reverse('api:inventory_script_view', kwargs={'pk': inventory.pk}), admin_user)
    jdata = json.loads(resp.content)
    jdata.pop('all')

    assert inventory.hosts.count() == 0
    assert jdata == {}


@pytest.mark.django_db
def test_ungrouped_hosts(post, get, admin_user, organization, group_factory):
    inventory = Inventory(name='basic_inventory',
                          kind='',
                          organization=organization)
    inventory.save()
    Host.objects.create(name='first_host', inventory=inventory)
    Host.objects.create(name='second_host', inventory=inventory)
    resp = get(reverse('api:inventory_script_view', kwargs={'pk': inventory.pk}), admin_user)
    jdata = json.loads(resp.content)
    assert inventory.hosts.count() == 2
    assert len(jdata['all']['hosts']) == 2
