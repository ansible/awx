"""Host.modified must not move when another job finishes in the same inventory.

Adoption fails a job when `inventory.hosts.filter(modified__gt=job.started)` finds a host.
That is only safe if the writes a finishing job makes (facts, host summaries) leave
Host.modified alone. The last test shows the check does see a real edit.
"""

import json
import os
import time

import pytest

from django.utils.timezone import now

from awx.api.versioning import reverse
from awx.main.models import Host, Inventory, Job, JobEvent
from awx.main.tasks.facts import finish_fact_cache, start_fact_cache


@pytest.fixture
def inv(organization):
    inv = Inventory.objects.create(organization=organization, name='modified-inv')
    for name in ('h1', 'h2'):
        host = inv.hosts.create(name=name)
        host.ansible_facts = {'old': name}
        host.ansible_facts_modified = now()
        host.save(update_fields=['ansible_facts', 'ansible_facts_modified'])
    return inv


def _modified(inv):
    return dict(inv.hosts.values_list('name', 'modified'))


@pytest.mark.django_db
def test_job_finishing_in_the_inventory_leaves_host_modified_alone(inv, tmp_path):
    before = _modified(inv)
    orphan = Job.objects.create(name='orphan', inventory=inv, status='running', started=now())
    other = Job.objects.create(name='other', inventory=inv, status='running')

    # The other job's fact cache: h1 gets new facts, h2's file is removed.
    artifacts = str(tmp_path)
    start_fact_cache(inv.hosts.all(), artifacts_dir=artifacts, timeout=0, inventory_id=inv.id)
    h1_file = os.path.join(artifacts, 'fact_cache', 'h1')
    with open(h1_file, 'w') as f:
        json.dump({'new': True}, f)
    future = time.time() + 60
    os.utime(h1_file, (future, future))
    os.remove(os.path.join(artifacts, 'fact_cache', 'h2'))
    finish_fact_cache(inv.hosts, artifacts_dir=artifacts, job_id=other.id, inventory_id=inv.id, job_created=other.created)
    assert Host.objects.get(inventory=inv, name='h1').ansible_facts == {'new': True}

    # The other job's playbook_on_stats: writes the host summaries and host metrics.
    event = JobEvent(job=other, event='playbook_on_stats', counter=1, job_created=other.created, event_data={'ok': {'h1': 1, 'h2': 1}})
    event.host_map = {h.name: h.id for h in inv.hosts.all()}
    event._update_host_summary_from_stats({'h1', 'h2'})
    assert other.job_host_summaries.count() == 2

    assert _modified(inv) == before
    assert not inv.hosts.filter(modified__gt=orphan.started).exists()


@pytest.mark.django_db
def test_save_with_update_fields_does_not_move_modified(inv):
    """BaseModel.save does not add 'modified' to update_fields, and the inventory importer saves
    hosts that way (rename, enabled, variables). A sync's edits are therefore only visible
    through the InventoryUpdate it creates, not through Host.modified."""
    before = _modified(inv)
    host = inv.hosts.get(name='h1')
    host.enabled = False
    host.save(update_fields=['enabled'])
    assert _modified(inv) == before


@pytest.mark.django_db
def test_an_edit_after_the_job_started_is_seen(inv):
    job = Job.objects.create(name='orphan', inventory=inv, status='running', started=now())
    host = inv.hosts.get(name='h1')
    host.description = 'edited'
    host.save()
    assert inv.hosts.filter(modified__gt=job.started).exists()


@pytest.mark.django_db
def test_an_api_edit_after_the_job_started_is_seen(inv, patch, admin_user):
    """The API saves the whole row, so a user's rename or enabled toggle moves modified."""
    job = Job.objects.create(name='orphan', inventory=inv, status='running', started=now())
    host = inv.hosts.get(name='h1')
    patch(reverse('api:host_detail', kwargs={'pk': host.id}), {'name': 'h1-renamed', 'enabled': False}, admin_user, expect=200)
    assert inv.hosts.filter(modified__gt=job.started).exists()
