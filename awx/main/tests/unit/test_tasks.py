import pytest
from contextlib import contextmanager

from awx.main.models import (
    UnifiedJob,
    Notification,
)

from awx.main.tasks import (
    send_notifications,
    run_administrative_checks,
)
from awx.main.task_engine import TaskEnhancer

@contextmanager
def apply_patches(_patches):
    [p.start() for p in _patches]
    yield
    [p.stop() for p in _patches]

def test_send_notifications_not_list():
    with pytest.raises(TypeError):
        send_notifications(None)

def test_send_notifications_job_id(mocker):
    with mocker.patch('awx.main.models.UnifiedJob.objects.get'):
        send_notifications([], job_id=1)
        assert UnifiedJob.objects.get.called
        assert UnifiedJob.objects.get.called_with(id=1)

def test_send_notifications_list(mocker):
    patches = list()

    mock_job = mocker.MagicMock(spec=UnifiedJob)
    patches.append(mocker.patch('awx.main.models.UnifiedJob.objects.get', return_value=mock_job))

    mock_notification = mocker.MagicMock(spec=Notification, subject="test")
    patches.append(mocker.patch('awx.main.models.Notification.objects.get', return_value=mock_notification))

    with apply_patches(patches):
        send_notifications([1,2], job_id=1)
        assert Notification.objects.get.call_count == 2
        assert mock_notification.status == "successful"
        assert mock_notification.save.called

        assert mock_job.notifications.add.called
        assert mock_job.notifications.add.called_with(mock_notification)

@pytest.mark.parametrize("current_instances,call_count", [(91, 2), (89,1)])
def test_run_admin_checks_usage(mocker, current_instances, call_count):
    patches = list()
    patches.append(mocker.patch('awx.main.tasks.User'))

    mock_te = mocker.Mock(spec=TaskEnhancer)
    mock_te.validate_enhancements.return_value = {'instance_count': 100, 'current_instances': current_instances, 'date_warning': True}
    patches.append(mocker.patch('awx.main.tasks.TaskEnhancer', return_value=mock_te))

    mock_sm = mocker.Mock()
    patches.append(mocker.patch('awx.main.tasks.send_mail', wraps=mock_sm))

    with apply_patches(patches):
        run_administrative_checks()
        assert mock_sm.called
        if call_count == 2:
            assert '90%' in mock_sm.call_args_list[0][0][0]
        else:
            assert 'expire' in mock_sm.call_args_list[0][0][0]
