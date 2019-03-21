from unittest import mock
import pytest

from awx.main.models import (Job, JobEvent, ProjectUpdate, ProjectUpdateEvent,
                             AdHocCommand, AdHocCommandEvent, InventoryUpdate,
                             InventorySource, InventoryUpdateEvent, SystemJob,
                             SystemJobEvent)


@pytest.mark.django_db
@mock.patch('awx.main.consumers.emit_channel_notification')
def test_parent_changed(emit):
    j = Job()
    j.save()
    JobEvent.create_from_data(job_id=j.pk, uuid='abc123', event='playbook_on_task_start')
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
    )
    assert JobEvent.objects.count() == 2
    for e in JobEvent.objects.all():
        assert e.changed is True


@pytest.mark.django_db
@pytest.mark.parametrize('event', JobEvent.FAILED_EVENTS)
@mock.patch('awx.main.consumers.emit_channel_notification')
def test_parent_failed(emit, event):
    j = Job()
    j.save()
    JobEvent.create_from_data(job_id=j.pk, uuid='abc123', event='playbook_on_task_start')
    assert JobEvent.objects.count() == 1
    for e in JobEvent.objects.all():
        assert e.failed is False

    JobEvent.create_from_data(
        job_id=j.pk,
        parent_uuid='abc123',
        event=event
    )
    assert JobEvent.objects.count() == 2
    for e in JobEvent.objects.all():
        assert e.failed is True


@pytest.mark.django_db
@mock.patch('awx.main.consumers.emit_channel_notification')
def test_job_event_websocket_notifications(emit):
    j = Job(id=123)
    j.save()
    JobEvent.create_from_data(job_id=j.pk)
    assert len(emit.call_args_list) == 1
    topic, payload = emit.call_args_list[0][0]
    assert topic == 'job_events-123'
    assert payload['job'] == 123


@pytest.mark.django_db
@mock.patch('awx.main.consumers.emit_channel_notification')
def test_ad_hoc_event_websocket_notifications(emit):
    ahc = AdHocCommand(id=123)
    ahc.save()
    AdHocCommandEvent.create_from_data(ad_hoc_command_id=ahc.pk)
    assert len(emit.call_args_list) == 1
    topic, payload = emit.call_args_list[0][0]
    assert topic == 'ad_hoc_command_events-123'
    assert payload['ad_hoc_command'] == 123


@pytest.mark.django_db
@mock.patch('awx.main.consumers.emit_channel_notification')
def test_project_update_event_websocket_notifications(emit, project):
    pu = ProjectUpdate(id=123, project=project)
    pu.save()
    ProjectUpdateEvent.create_from_data(project_update_id=pu.pk)
    assert len(emit.call_args_list) == 1
    topic, payload = emit.call_args_list[0][0]
    assert topic == 'project_update_events-123'
    assert payload['project_update'] == 123


@pytest.mark.django_db
@mock.patch('awx.main.consumers.emit_channel_notification')
def test_inventory_update_event_websocket_notifications(emit, inventory):
    source = InventorySource()
    source.save()
    iu = InventoryUpdate(id=123, inventory_source=source)
    iu.save()
    InventoryUpdateEvent.create_from_data(inventory_update_id=iu.pk)
    assert len(emit.call_args_list) == 1
    topic, payload = emit.call_args_list[0][0]
    assert topic == 'inventory_update_events-123'
    assert payload['inventory_update'] == 123


@pytest.mark.django_db
@mock.patch('awx.main.consumers.emit_channel_notification')
def test_system_job_event_websocket_notifications(emit, inventory):
    j = SystemJob(id=123)
    j.save()
    SystemJobEvent.create_from_data(system_job_id=j.pk)
    assert len(emit.call_args_list) == 1
    topic, payload = emit.call_args_list[0][0]
    assert topic == 'system_job_events-123'
    assert payload['system_job'] == 123
