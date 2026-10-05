import json

import pytest

from awx.api.versioning import reverse
from awx.main.models import Organization, Host, Group, Inventory


@pytest.fixture
def smart_inv_org():
    return Organization.objects.create(name="smart-org")


@pytest.fixture
def smart_inv_source(smart_inv_org):
    inv = Inventory.objects.create(name="smart-source-inv", organization=smart_inv_org)
    Host.objects.create(name="hostA", inventory=inv)
    Host.objects.create(name="hostB", inventory=inv)
    Host.objects.create(name="hostDup", inventory=inv)
    groupA = Group.objects.create(name="groupA", inventory=inv)
    groupB = Group.objects.create(name="groupB", inventory=inv)
    groupA.hosts.add(*inv.hosts.filter(name__in=["hostA", "hostDup"]))
    groupB.hosts.add(*inv.hosts.filter(name__in=["hostB", "hostDup"]))
    return inv


@pytest.mark.django_db
def test_create_smart_inventory(post, admin_user, smart_inv_org):
    resp = post(
        reverse('api:inventory_list'),
        {
            'name': 'my-smart-inv',
            'kind': 'smart',
            'organization': smart_inv_org.pk,
            'host_filter': 'name=hostA',
        },
        admin_user,
        expect=201,
    )
    assert resp.data['kind'] == 'smart'
    assert resp.data['host_filter'] == 'name=hostA'


@pytest.mark.django_db
def test_create_smart_inventory_requires_host_filter(post, admin_user, smart_inv_org):
    resp = post(
        reverse('api:inventory_list'),
        {
            'name': 'no-filter-smart',
            'kind': 'smart',
            'organization': smart_inv_org.pk,
        },
        admin_user,
        expect=400,
    )
    assert 'host_filter' in json.dumps(resp.data)


@pytest.mark.django_db
def test_unable_to_create_host_in_smart_inventory(post, admin_user, smart_inv_org):
    smart_inv = Inventory.objects.create(
        name="no-host-create",
        kind="smart",
        host_filter="name=hostA",
        organization=smart_inv_org,
    )
    url = reverse('api:inventory_hosts_list', kwargs={'pk': smart_inv.pk})
    resp = post(url, {'name': 'new-host'}, admin_user, expect=400)
    assert 'Cannot create' in json.dumps(resp.data)


@pytest.mark.django_db
def test_unable_to_create_group_in_smart_inventory(post, admin_user, smart_inv_org):
    smart_inv = Inventory.objects.create(
        name="no-group-create",
        kind="smart",
        host_filter="name=hostA",
        organization=smart_inv_org,
    )
    url = reverse('api:inventory_groups_list', kwargs={'pk': smart_inv.pk})
    resp = post(url, {'name': 'new-group'}, admin_user, expect=400)
    assert 'Cannot create' in json.dumps(resp.data)


@pytest.mark.django_db
def test_unable_to_create_inventory_source_in_smart_inventory(post, admin_user, smart_inv_org):
    smart_inv = Inventory.objects.create(
        name="no-src-create",
        kind="smart",
        host_filter="name=hostA",
        organization=smart_inv_org,
    )
    url = reverse('api:inventory_inventory_sources_list', kwargs={'pk': smart_inv.pk})
    resp = post(url, {'name': 'new-src', 'source': 'ec2'}, admin_user, expect=400)
    assert 'Cannot create' in json.dumps(resp.data)


@pytest.mark.django_db
def test_convert_smart_to_regular_inventory(admin_user, smart_inv_org):
    smart_inv = Inventory.objects.create(
        name="convert-to-regular",
        kind="smart",
        host_filter="name=anything",
        organization=smart_inv_org,
    )
    assert smart_inv.kind == 'smart'
    smart_inv.host_filter = ''
    smart_inv.kind = ''
    smart_inv.save()
    smart_inv.refresh_from_db()
    assert smart_inv.kind == ''
    assert not smart_inv.host_filter


@pytest.mark.django_db
def test_smart_inventory_deletion_does_not_cascade(admin_user, smart_inv_source, smart_inv_org):
    host = smart_inv_source.hosts.first()
    smart_inv = Inventory.objects.create(
        name="delete-no-cascade",
        kind="smart",
        host_filter="name=%s" % host.name,
        organization=smart_inv_org,
    )
    smart_inv.delete()
    assert Host.objects.filter(pk=host.pk).exists()


@pytest.mark.django_db
def test_urlencode_host_filter(post, admin_user, smart_inv_org):
    post(
        reverse('api:inventory_list'),
        data={
            'name': 'url-encoded-smart',
            'kind': 'smart',
            'organization': smart_inv_org.pk,
            'host_filter': 'ansible_facts__ansible_distribution_version=%227.4%22',
        },
        user=admin_user,
        expect=201,
    )
    si = Inventory.objects.get(name='url-encoded-smart')
    assert si.host_filter == 'ansible_facts__ansible_distribution_version="7.4"'


@pytest.mark.django_db
def test_host_filter_unicode(post, admin_user, smart_inv_org):
    post(
        reverse('api:inventory_list'),
        data={
            'name': 'unicode-smart',
            'kind': 'smart',
            'organization': smart_inv_org.pk,
            'host_filter': 'ansible_facts__ansible_distribution=レッドハット',
        },
        user=admin_user,
        expect=201,
    )
    si = Inventory.objects.get(name='unicode-smart')
    assert si.host_filter == 'ansible_facts__ansible_distribution=レッドハット'


@pytest.mark.django_db
@pytest.mark.parametrize("lookup", ['icontains', 'has_keys'])
def test_host_filter_invalid_ansible_facts_lookup(post, admin_user, smart_inv_org, lookup):
    resp = post(
        reverse('api:inventory_list'),
        data={
            'name': 'invalid-lookup-smart',
            'kind': 'smart',
            'organization': smart_inv_org.pk,
            'host_filter': 'ansible_facts__ansible_distribution__{}=cent'.format(lookup),
        },
        user=admin_user,
        expect=400,
    )
    assert 'ansible_facts does not support searching with __{}'.format(lookup) in json.dumps(resp.data)


@pytest.mark.django_db
def test_host_filter_ansible_facts_exact(post, admin_user, smart_inv_org):
    post(
        reverse('api:inventory_list'),
        data={
            'name': 'exact-smart',
            'kind': 'smart',
            'organization': smart_inv_org.pk,
            'host_filter': 'ansible_facts__ansible_distribution__exact="CentOS"',
        },
        user=admin_user,
        expect=201,
    )
