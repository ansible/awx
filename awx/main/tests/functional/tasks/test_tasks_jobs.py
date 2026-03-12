import pytest

from awx.main.tasks.jobs import RunJob
from awx.main.models import Job


@pytest.mark.django_db
def test_does_not_run_reaped_job(mocker, mock_me):
    job = Job.objects.create(status='failed', job_explanation='This job has been reaped.')
    mock_run = mocker.patch('awx.main.tasks.jobs.ansible_runner.interface.run')
    try:
        RunJob().run(job.id)
    except Exception:
        pass
    job.refresh_from_db()
    assert job.status == 'failed'
    mock_run.assert_not_called()


@pytest.mark.django_db
def test_cancel_flag_on_start(jt_linked, caplog):
    job = jt_linked.create_unified_job()
    job.status = 'waiting'
    job.cancel_flag = True
    job.save()

    task = RunJob()
    task.run(job.id)

    job = Job.objects.get(id=job.id)
    assert job.status == 'canceled'


@pytest.mark.django_db
def test_runjob_run_can_accept_waiting_status(jt_linked, mocker):
    """Test that RunJob.run() can accept a job in 'waiting' status and transition it to 'running'
    before the pre_run_hook is called"""
    job = jt_linked.create_unified_job()
    job.status = 'waiting'
    job.save()

    status_at_pre_run = None

    def capture_status(instance, private_data_dir):
        nonlocal status_at_pre_run
        instance.refresh_from_db()
        status_at_pre_run = instance.status

    mock_pre_run = mocker.patch.object(RunJob, 'pre_run_hook', side_effect=capture_status)

    task = RunJob()
    try:
        task.run(job.id)
    except Exception:
        pass

    mock_pre_run.assert_called_once()
    assert status_at_pre_run == 'running'
