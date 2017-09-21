# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved.

import mock
import pytest

from django.utils.timezone import now as tz_now
from django.db import DatabaseError

from awx.main.scheduler import TaskManager
from awx.main.models import (
    Job,
    Instance,
    InstanceGroup,
)
from django.core.cache import cache


class TestCleanupInconsistentCeleryTasks():
    @mock.patch.object(cache, 'get', return_value=None)
    @mock.patch.object(TaskManager, 'get_active_tasks', return_value=([], {}))
    @mock.patch.object(TaskManager, 'get_running_tasks', return_value=({'host1': [Job(id=2), Job(id=3),]}, []))
    @mock.patch.object(InstanceGroup.objects, 'prefetch_related', return_value=[])
    @mock.patch.object(Instance.objects, 'filter', return_value=mock.MagicMock(first=lambda: None))
    @mock.patch('awx.main.scheduler.task_manager.logger')
    def test_instance_does_not_exist(self, logger_mock, *args):
        logger_mock.error = mock.MagicMock(side_effect=RuntimeError("mocked"))
        tm = TaskManager()
        with pytest.raises(RuntimeError) as excinfo:
            tm.cleanup_inconsistent_celery_tasks()

        assert "mocked" in str(excinfo.value)
        logger_mock.error.assert_called_once_with("Execution node Instance host1 not found in database. "
                                                  "The node is currently executing jobs ['job 2 (new)', "
                                                  "'job 3 (new)']")

    @mock.patch.object(cache, 'get', return_value=None)
    @mock.patch.object(TaskManager, 'get_active_tasks', return_value=([], {'host1': []}))
    @mock.patch.object(InstanceGroup.objects, 'prefetch_related', return_value=[])
    @mock.patch.object(TaskManager, 'get_running_tasks')
    @mock.patch('awx.main.scheduler.task_manager.logger')
    def test_save_failed(self, logger_mock, get_running_tasks, *args):
        logger_mock.error = mock.MagicMock()
        job = Job(id=2, modified=tz_now(), status='running', celery_task_id='blah', execution_node='host1')
        job.websocket_emit_status = mock.MagicMock()
        get_running_tasks.return_value = ({'host1': [job]}, [])
        tm = TaskManager()

        with mock.patch.object(job, 'save', side_effect=DatabaseError):
            tm.cleanup_inconsistent_celery_tasks()
            job.save.assert_called_once()
            logger_mock.error.assert_called_once_with("Task job 2 (failed) DB error in marking failed. Job possibly deleted.")

    @mock.patch.object(InstanceGroup.objects, 'prefetch_related', return_value=[])
    @mock.patch('awx.main.scheduler.task_manager.inspect')
    def test_multiple_active_instances_sanity_check(self, inspect_mock, *args):
        class MockInspector:
            pass

        mock_inspector = MockInspector()
        mock_inspector.active = lambda: {
            'celery@host1': [],
            'celery@host2': []
        }
        inspect_mock.return_value = mock_inspector
        tm = TaskManager()
        active_task_queues, queues = tm.get_active_tasks()
        assert 'host1' in queues
        assert 'host2' in queues
