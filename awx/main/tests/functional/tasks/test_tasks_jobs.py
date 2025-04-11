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
def test_cancel_flag_on_start(jt_linked):
    job = jt_linked.create_unified_job()
    job.status = 'waiting'
    job.cancel_flag = True
    job.save()

    task = RunJob()
    with pytest.raises(RuntimeError) as exc:
        task.run(job.id)
    assert 'because its status "canceled" is not expected' in str(exc)

    job = Job.objects.get(id=job.id)
    assert job.status == 'canceled'
