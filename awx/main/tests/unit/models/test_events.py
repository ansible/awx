from datetime import datetime
from django.utils.timezone import utc
import pytest

from awx.main.models import (JobEvent, ProjectUpdateEvent, AdHocCommandEvent,
                             InventoryUpdateEvent, SystemJobEvent)


@pytest.mark.parametrize('job_identifier, cls', [
    ['job_id', JobEvent],
    ['project_update_id', ProjectUpdateEvent],
    ['ad_hoc_command_id', AdHocCommandEvent],
    ['inventory_update_id', InventoryUpdateEvent],
    ['system_job_id', SystemJobEvent],
])
@pytest.mark.parametrize('created', [
    datetime(2018, 1, 1).isoformat(), datetime(2018, 1, 1)
])
def test_event_parse_created(job_identifier, cls, created):
    event = cls.create_from_data(**{
        job_identifier: 123,
        'created': created
    })
    assert event.created == datetime(2018, 1, 1).replace(tzinfo=utc)


@pytest.mark.parametrize('job_identifier, cls', [
    ['job_id', JobEvent],
    ['project_update_id', ProjectUpdateEvent],
    ['ad_hoc_command_id', AdHocCommandEvent],
    ['inventory_update_id', InventoryUpdateEvent],
    ['system_job_id', SystemJobEvent],
])
def test_playbook_event_strip_invalid_keys(job_identifier, cls):
    event = cls.create_from_data(**{
        job_identifier: 123,
        'extra_key': 'extra_value'
    })
    assert getattr(event, job_identifier) == 123
    assert not hasattr(event, 'extra_key')


@pytest.mark.parametrize('field', [
    'play', 'role', 'task', 'playbook'
])
def test_really_long_event_fields(field):
    event = JobEvent.create_from_data(**{
        'job_id': 123,
        'event_data': {field: 'X' * 4096}
    })
    assert event.event_data[field] == 'X' * 1023 + '…'
