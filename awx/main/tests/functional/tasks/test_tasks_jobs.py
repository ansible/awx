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


@pytest.mark.django_db
def test_finalize_job_run_with_real_job_instance(jt_linked, mocker):
    """Test that _finalize_job_run executes the real finalization path with actual Job instance."""
    from awx.main.tasks.jobs import _finalize_job_run
    from awx.main.tasks.callback import RunnerCallback

    job = jt_linked.create_unified_job()
    job.status = 'running'
    job.save()

    # Create a real callback
    callback = RunnerCallback(model=Job)
    callback.event_ct = 5
    callback.host_status_counts = {'ok': 1, 'failed': 0}  # Non-None triggers events_processed_hook

    # Mock the hooks that would be called
    mocker.patch('awx.main.tasks.jobs.events_processed_hook')
    mocker.patch('awx.main.tasks.jobs.ScheduleTaskManager')
    mocker.patch('awx.main.tasks.jobs.ScheduleWorkflowManager')

    # Call the real finalization function
    result = _finalize_job_run(Job, job.id, callback, 'successful')

    # Verify the job was updated with successful status
    job.refresh_from_db()
    assert job.status == 'successful'
    assert result.id == job.id


@pytest.mark.django_db
def test_finalize_job_run_with_blocked_jobs(jt_linked, mocker):
    """Test that _finalize_job_run calls ScheduleTaskManager for jobs with blocked dependencies."""
    from awx.main.tasks.jobs import _finalize_job_run
    from awx.main.tasks.callback import RunnerCallback

    job = jt_linked.create_unified_job()
    job.status = 'running'
    job.save()

    # Create another job that depends on this one
    blocked_job = jt_linked.create_unified_job()
    blocked_job.status = 'blocked'
    blocked_job.save()
    job.unifiedjob_blocked_jobs.add(blocked_job)

    callback = RunnerCallback(model=Job)
    callback.event_ct = 0

    # Mock the hooks
    mock_schedule_task = mocker.patch('awx.main.tasks.jobs.ScheduleTaskManager')
    mocker.patch('awx.main.tasks.jobs.events_processed_hook')
    mocker.patch('awx.main.tasks.jobs.ScheduleWorkflowManager')

    # Call finalization
    _finalize_job_run(Job, job.id, callback, 'successful')

    # Verify ScheduleTaskManager was called
    mock_schedule_task.return_value.schedule.assert_called_once()


@pytest.mark.django_db
def test_finalize_job_run_calls_websocket_emit(jt_linked, mocker):
    """Test that websocket status is emitted after finalization."""
    from awx.main.tasks.jobs import _finalize_job_run
    from awx.main.tasks.callback import RunnerCallback

    job = jt_linked.create_unified_job()
    job.status = 'running'
    job.save()

    callback = RunnerCallback(model=Job)
    callback.event_ct = 0

    # Mock websocket_emit_status
    mocker.patch('awx.main.tasks.jobs.events_processed_hook')
    mocker.patch('awx.main.tasks.jobs.ScheduleTaskManager')
    mocker.patch('awx.main.tasks.jobs.ScheduleWorkflowManager')
    mock_websocket = mocker.patch.object(type(job), 'websocket_emit_status')

    # Call finalization with failed status
    _finalize_job_run(Job, job.id, callback, 'failed')

    # Verify websocket was called with correct status
    mock_websocket.assert_called_with('failed')
