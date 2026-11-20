"""host_map.read_host_map: the host ids an adopted job's replayed events get."""

from unittest import mock

import pytest

from django.utils.timezone import now

from awx.main.models import Inventory, InventoryUpdate, Job, ProjectUpdate
from awx.main.tasks import host_map


@pytest.fixture
def inv(organization):
    inv = Inventory.objects.create(organization=organization, name='map-inv')
    for name in ('h1', 'h2'):
        inv.hosts.create(name=name)
    return inv


@pytest.fixture
def job(inv):
    return Job.objects.create(inventory=inv, status='running', started=now())


@pytest.mark.django_db
def test_the_map_holds_the_inventorys_hosts(job, inv):
    assert host_map.read_host_map(job) == {h.name: h.id for h in inv.hosts.all()}


@pytest.mark.django_db
def test_a_host_renamed_or_removed_since_the_job_started_gets_no_id(job, inv):
    inv.hosts.filter(name='h1').update(name='h1-renamed')
    inv.hosts.filter(name='h2').delete()

    assert 'h1' not in host_map.read_host_map(job)
    assert 'h2' not in host_map.read_host_map(job)


@pytest.mark.django_db
def test_hosts_whose_ids_were_swapped_since_the_job_started_get_each_others(job, inv):
    h1, h2 = inv.hosts.get(name='h1'), inv.hosts.get(name='h2')
    for host, name in ((h1, 'tmp'), (h2, 'h1'), (h1, 'h2')):  # names are unique, so swap through a third
        host.name = name
        host.save()

    assert host_map.read_host_map(job) == {'h1': h2.id, 'h2': h1.id}


@pytest.mark.django_db
@pytest.mark.parametrize('instance', [InventoryUpdate(), ProjectUpdate()])
def test_job_types_without_host_ids_get_no_map(instance):
    assert host_map.read_host_map(instance) == {}


@pytest.mark.django_db
def test_a_job_without_an_inventory_gets_no_map():
    assert host_map.read_host_map(Job.objects.create(status='running', started=now())) == {}


@pytest.mark.django_db
def test_a_map_that_cannot_be_read_is_empty_and_does_not_raise(job):
    with mock.patch.object(Inventory, 'get_script_data', side_effect=RuntimeError('db went away')):
        assert host_map.read_host_map(job) == {}
