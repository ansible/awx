from unittest import mock
import pytest

from awx.main.models import Job, JobEvent


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
