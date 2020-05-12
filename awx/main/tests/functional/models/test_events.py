from unittest import mock
import pytest

from django.utils.timezone import now

from awx.main.models import Job, JobEvent, Inventory, Host


@pytest.mark.django_db
@mock.patch('awx.main.models.events.emit_event_detail')
def test_parent_changed(emit):
    j = Job()
    j.save()
    JobEvent.create_from_data(job_id=j.pk, uuid='abc123', event='playbook_on_task_start').save()
    assert JobEvent.objects.count() == 1
    for e in JobEvent.objects.all():
        assert e.changed is False

    JobEvent.create_from_data(
        job_id=j.pk,
        parent_uuid='abc123',
        event='runner_on_ok',
        event_data={
            'res': {'changed': ['localhost']}
        }
    ).save()
    # the `playbook_on_stats` event is where we update the parent changed linkage
    JobEvent.create_from_data(
        job_id=j.pk,
        parent_uuid='abc123',
        event='playbook_on_stats'
    ).save()
    events = JobEvent.objects.filter(event__in=['playbook_on_task_start', 'runner_on_ok'])
    assert events.count() == 2
    for e in events.all():
        assert e.changed is True


@pytest.mark.django_db
@pytest.mark.parametrize('event', JobEvent.FAILED_EVENTS)
@mock.patch('awx.main.models.events.emit_event_detail')
def test_parent_failed(emit, event):
    j = Job()
    j.save()
    JobEvent.create_from_data(job_id=j.pk, uuid='abc123', event='playbook_on_task_start').save()
    assert JobEvent.objects.count() == 1
    for e in JobEvent.objects.all():
        assert e.failed is False

    JobEvent.create_from_data(
        job_id=j.pk,
        parent_uuid='abc123',
        event=event
    ).save()

    # the `playbook_on_stats` event is where we update the parent failed linkage
    JobEvent.create_from_data(
        job_id=j.pk,
        parent_uuid='abc123',
        event='playbook_on_stats'
    ).save()
    events = JobEvent.objects.filter(event__in=['playbook_on_task_start', event])
    assert events.count() == 2
    for e in events.all():
        assert e.failed is True


@pytest.mark.django_db
def test_host_summary_generation():
    hostnames = [f'Host {i}' for i in range(500)]
    inv = Inventory()
    inv.save()
    Host.objects.bulk_create([
        Host(created=now(), modified=now(), name=h, inventory_id=inv.id)
        for h in hostnames
    ])
    j = Job(inventory=inv)
    j.save()
    host_map = dict((host.name, host.id) for host in inv.hosts.all())
    JobEvent.create_from_data(
        job_id=j.pk,
        parent_uuid='abc123',
        event='playbook_on_stats',
        event_data={
            'ok': dict((hostname, len(hostname)) for hostname in hostnames),
            'changed': {},
            'dark': {},
            'failures': {},
            'ignored': {},
            'processed': {},
            'rescued': {},
            'skipped': {},
        },
        host_map=host_map
    ).save()

    assert j.job_host_summaries.count() == len(hostnames)
    assert sorted([s.host_name for s in j.job_host_summaries.all()]) == sorted(hostnames)

    for s in j.job_host_summaries.all():
        assert host_map[s.host_name] == s.host_id
        assert s.ok == len(s.host_name)
        assert s.changed == 0
        assert s.dark == 0
        assert s.failures == 0
        assert s.ignored == 0
        assert s.processed == 0
        assert s.rescued == 0
        assert s.skipped == 0


@pytest.mark.django_db
def test_host_summary_generation_with_deleted_hosts():
    hostnames = [f'Host {i}' for i in range(10)]
    inv = Inventory()
    inv.save()
    Host.objects.bulk_create([
        Host(created=now(), modified=now(), name=h, inventory_id=inv.id)
        for h in hostnames
    ])
    j = Job(inventory=inv)
    j.save()
    host_map = dict((host.name, host.id) for host in inv.hosts.all())

    # delete half of the hosts during the playbook run
    for h in inv.hosts.all()[:5]:
        h.delete()

    JobEvent.create_from_data(
        job_id=j.pk,
        parent_uuid='abc123',
        event='playbook_on_stats',
        event_data={
            'ok': dict((hostname, len(hostname)) for hostname in hostnames),
            'changed': {},
            'dark': {},
            'failures': {},
            'ignored': {},
            'processed': {},
            'rescued': {},
            'skipped': {},
        },
        host_map=host_map
    ).save()


    ids = sorted([s.host_id or -1 for s in j.job_host_summaries.order_by('id').all()])
    names = sorted([s.host_name for s in j.job_host_summaries.all()])
    assert ids == [-1, -1, -1, -1, -1, 6, 7, 8, 9, 10]
    assert names == ['Host 0', 'Host 1', 'Host 2', 'Host 3', 'Host 4', 'Host 5',
                     'Host 6', 'Host 7', 'Host 8', 'Host 9']
