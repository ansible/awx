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
    resp = get(reverse('api:inventory_script_view', kwargs={'version': 'v2', 'pk': inventory.pk}), admin_user)
    jdata = json.loads(resp.content)
    
    assert inventory.hosts.count() == 0
    assert jdata == {}
    
    
@pytest.mark.django_db
def test_empty_smart_inventory(post, get, admin_user, organization, group_factory):
    smart_inventory = Inventory(name='smart',
                                kind='smart',
                                organization=organization,
                                host_filter='enabled=True')
    smart_inventory.save()
    resp = get(reverse('api:inventory_script_view', kwargs={'version': 'v2', 'pk': smart_inventory.pk}), admin_user)
    smartjdata = json.loads(resp.content)

    assert smart_inventory.hosts.count() == 0
    assert smartjdata == {}
    
    
@pytest.mark.django_db
def test_ungrouped_hosts(post, get, admin_user, organization, group_factory):
    inventory = Inventory(name='basic_inventory', 
                          kind='', 
                          organization=organization)
    inventory.save()
    Host.objects.create(name='first_host', inventory=inventory)
    Host.objects.create(name='second_host', inventory=inventory)
    resp = get(reverse('api:inventory_script_view', kwargs={'version': 'v2', 'pk': inventory.pk}), admin_user)
    jdata = json.loads(resp.content)
    assert inventory.hosts.count() == 2
    assert len(jdata['all']['hosts']) == 2


@pytest.mark.django_db
def test_grouped_hosts_smart_inventory(post, get, admin_user, organization, group_factory):
    inventory = Inventory(name='basic_inventory', 
                          kind='', 
                          organization=organization)
    inventory.save()
    groupA = group_factory('test_groupA')
    host1 = Host.objects.create(name='first_host', inventory=inventory)
    host2 = Host.objects.create(name='second_host', inventory=inventory)
    Host.objects.create(name='third_host', inventory=inventory)
    groupA.hosts.add(host1)
    groupA.hosts.add(host2)       
    smart_inventory = Inventory(name='smart_inventory',
                                kind='smart',
                                organization=organization,
                                host_filter='enabled=True')
    smart_inventory.save()
    resp = get(reverse('api:inventory_script_view', kwargs={'version': 'v2', 'pk': inventory.pk}), admin_user)
    jdata = json.loads(resp.content)
    resp = get(reverse('api:inventory_script_view', kwargs={'version': 'v2', 'pk': smart_inventory.pk}), admin_user)
    smartjdata = json.loads(resp.content)

    assert getattr(smart_inventory, 'kind') == 'smart'
    assert inventory.hosts.count() == 3
    assert len(jdata['all']['hosts']) == 1
    assert smart_inventory.hosts.count() == 3
    assert len(smartjdata['all']['hosts']) == 3
