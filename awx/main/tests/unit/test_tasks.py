import pytest

from awx.main.models import (
    UnifiedJob,
    Notification,
)

from awx.main.tasks import (
    run_label_cleanup,
    send_notifications,
)

def test_run_label_cleanup(mocker):
    qs = mocker.Mock(**{'count.return_value': 3, 'delete.return_value': None})
    mock_label = mocker.patch('awx.main.models.label.Label.get_orphaned_labels',return_value=qs)

    ret = run_label_cleanup()

    mock_label.assert_called_with()
    qs.delete.assert_called_with()
    assert 3 == ret

def test_send_notifications_not_list():
    with pytest.raises(TypeError):
        send_notifications(None)

def test_send_notifications_job_id(mocker):
    with mocker.patch('awx.main.models.UnifiedJob.objects.get'):
        send_notifications([], job_id=1)
        assert UnifiedJob.objects.get.called
        assert UnifiedJob.objects.get.called_with(id=1)

def test_send_notifications_list(mocker):
    mock_job = mocker.MagicMock(spec=UnifiedJob)
    with mocker.patch('awx.main.models.UnifiedJob.objects.get', return_value=mock_job):
        mock_notification = mocker.MagicMock(spec=Notification, subject="test")
        with mocker.patch('awx.main.models.Notification.objects.get', return_value=mock_notification):
            send_notifications([1,2], job_id=1)
            assert Notification.objects.get.call_count == 2
            assert mock_notification.status == "successful"
            assert mock_notification.save.called

            assert mock_job.notifications.add.called
            assert mock_job.notifications.add.called_with(mock_notification)

