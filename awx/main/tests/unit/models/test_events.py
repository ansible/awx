from datetime import datetime
from django.utils.timezone import utc
from unittest import mock
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
    with mock.patch.object(cls, 'objects') as manager:
        cls.create_from_data(**{
            job_identifier: 123,
            'created': created
        })
        expected_created = datetime(2018, 1, 1).replace(tzinfo=utc)
        manager.create.assert_called_with(**{
            job_identifier: 123,
            'created': expected_created
        })


@pytest.mark.parametrize('job_identifier, cls', [
    ['job_id', JobEvent],
    ['project_update_id', ProjectUpdateEvent],
    ['ad_hoc_command_id', AdHocCommandEvent],
    ['inventory_update_id', InventoryUpdateEvent],
    ['system_job_id', SystemJobEvent],
])
def test_playbook_event_strip_invalid_keys(job_identifier, cls):
    with mock.patch.object(cls, 'objects') as manager:
        cls.create_from_data(**{
            job_identifier: 123,
            'extra_key': 'extra_value'
        })
        manager.create.assert_called_with(**{job_identifier: 123})


@pytest.mark.parametrize('field', [
    'play', 'role', 'task', 'playbook'
])
def test_really_long_event_fields(field):
    with mock.patch.object(JobEvent, 'objects') as manager:
        JobEvent.create_from_data(**{
            'job_id': 123,
            'event_data': {field: 'X' * 4096}
        })
        manager.create.assert_called_with(**{
            'job_id': 123,
            'event_data': {field: 'X' * 1023 + '…'}
        })
