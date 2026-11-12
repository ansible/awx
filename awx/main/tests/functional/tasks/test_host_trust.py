"""host_trust.assess turns the inventory check into what adoption does with the job.

What counts as a change is pinned in test_inventory_change_check.py; these tests cover the verdict.
"""

import dataclasses
from unittest import mock

import pytest

from django.utils.timezone import now

from awx.main.models import Inventory, InventoryUpdate, Job, ProjectUpdate
from awx.main.tasks import host_trust


@pytest.fixture
def inv(organization):
    inv = Inventory.objects.create(organization=organization, name='trust-inv')
    for name in ('h1', 'h2'):
        inv.hosts.create(name=name)
    return inv


@pytest.fixture
def job(inv):
    return Job.objects.create(inventory=inv, status='running', started=now(), job_env={'host_count': 2})


@pytest.mark.django_db
def test_an_unchanged_inventory_proceeds_with_the_map(job, inv):
    verdict = host_trust.assess(job)
    assert verdict == host_trust.Verdict(None, {h.name: h.id for h in inv.hosts.all()}, host_trust.PROCEED)


@pytest.mark.django_db
def test_a_changed_inventory_fails_the_job_when_done(job, inv):
    inv.hosts.create(name='h3')
    assert host_trust.assess(job) == host_trust.Verdict('hosts were added or removed', {}, host_trust.FAIL_WHEN_DONE)


@pytest.mark.django_db
def test_a_canceled_job_proceeds_but_keeps_the_reason(job, inv):
    inv.hosts.create(name='h3')
    job.cancel_flag = True
    assert host_trust.assess(job) == host_trust.Verdict('hosts were added or removed', {}, host_trust.PROCEED)


@pytest.mark.django_db
@pytest.mark.parametrize('instance', [InventoryUpdate(), ProjectUpdate()])
def test_job_types_without_host_ids_proceed_unchecked(instance):
    assert host_trust.assess(instance) == host_trust.Verdict(None, {}, host_trust.PROCEED)


@pytest.mark.django_db
def test_without_the_map_read_the_inventory_is_not_read(job):
    with mock.patch.object(Inventory, 'get_script_data') as read:
        assert host_trust.assess(job, read_map=False) == host_trust.Verdict(None, {}, host_trust.PROCEED)
    read.assert_not_called()


@pytest.mark.django_db
def test_a_change_while_the_map_is_read_empties_the_map(job):
    real = Inventory.get_script_data

    def read_then_delete_a_host(self, *args, **kwargs):
        data = real(self, *args, **kwargs)
        self.hosts.filter(name='h1').delete()
        return data

    with mock.patch.object(Inventory, 'get_script_data', read_then_delete_a_host):
        assert host_trust.assess(job) == host_trust.Verdict('hosts were added or removed', {}, host_trust.FAIL_WHEN_DONE)


@pytest.mark.django_db
def test_a_map_that_cannot_be_read_fails_the_job_when_done(job):
    with mock.patch.object(Inventory, 'get_script_data', side_effect=RuntimeError('db went away')):
        assert host_trust.assess(job) == host_trust.Verdict('the host map could not be read', {}, host_trust.FAIL_WHEN_DONE)


def test_the_verdict_is_frozen():
    with pytest.raises(dataclasses.FrozenInstanceError):
        host_trust.Verdict(None, {}, host_trust.PROCEED).action = host_trust.FAIL_WHEN_DONE
