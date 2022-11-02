import pytest

from awx.main.dispatch.worker.callback import job_stats_wrapup
from awx.main.models.jobs import Job


@pytest.mark.django_db
def test_wrapup_does_not_send_notifications(mocker):
    job = Job.objects.create(status='running')
    assert job.host_status_counts is None
    mock = mocker.patch('awx.main.models.notifications.JobNotificationMixin.send_notification_templates')
    job_stats_wrapup(job.id)
    job.refresh_from_db()
    assert job.host_status_counts == {}
    mock.assert_not_called()


@pytest.mark.django_db
def test_wrapup_does_send_notifications(mocker):
    job = Job.objects.create(status='successful')
    assert job.host_status_counts is None
    mock = mocker.patch('awx.main.models.notifications.JobNotificationMixin.send_notification_templates')
    job_stats_wrapup(job.id)
    job.refresh_from_db()
    assert job.host_status_counts == {}
    mock.assert_called_once_with('succeeded')
