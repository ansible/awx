from collections import namedtuple

import pytest

from awx.main.tasks.jobs import RunJob, RunSystemJob
from awx.main.models import Job, SystemJob

_Result = namedtuple('result', ['status', 'rc'])


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


def _detached_receptor_job(mocker, unit_id='unit-detach'):
    """Stand in for an AWXReceptorJob whose stream was interrupted by a shutdown signal."""
    receptor_job = mocker.MagicMock()
    receptor_job.detached = True
    receptor_job.unit_id = unit_id
    receptor_job.run.return_value = _Result(status='canceled', rc=1)
    return receptor_job


@pytest.mark.django_db
def test_run_leaves_detached_job_running_and_adoptable(jt_linked, execution_environment, mocker):
    """A detached stream must leave the job exactly as the next adopter needs to find it.

    Marking it failed, running post-run hooks or releasing the work unit would each on their
    own make the still-running EE unrecoverable: the orphan scan only looks at jobs that are
    still 'running' and still carry a work_unit_id.
    """
    job = jt_linked.create_unified_job()
    job.status = 'running'
    job.work_unit_id = 'unit-detach'
    job.execution_environment = execution_environment
    job.save()

    receptor_job = _detached_receptor_job(mocker)
    mocker.patch('awx.main.tasks.jobs.AWXReceptorJob', return_value=receptor_job)
    mocker.patch.object(RunJob, 'pre_run_hook')
    mocker.patch.object(RunJob, 'build_project_dir')
    mock_finalize = mocker.patch('awx.main.tasks.jobs._finalize_job_run')
    mock_post_run = mocker.patch.object(RunJob, 'post_run_hook')

    RunJob().run(job.id)

    receptor_job.run.assert_called_once()
    job.refresh_from_db()
    assert job.status == 'running'
    assert job.work_unit_id == 'unit-detach'
    mock_finalize.assert_not_called()
    mock_post_run.assert_not_called()
    receptor_job._receptor_release_work.assert_not_called()


@pytest.mark.django_db
def test_run_leaves_detached_job_running_when_shutdown_raises(jt_linked, execution_environment, mocker):
    """Detaching must survive an exception thrown after the decision to detach was made.

    Everything the shutdown path touches afterwards — the receptor control socket, the
    results socket — is dying at the same moment, so it can fail. Reaching the generic
    handler would mark the job 'error' and strand the live EE, which is the one outcome
    detaching exists to avoid. The decision, not a clean return, is what counts.
    """
    job = jt_linked.create_unified_job()
    job.status = 'running'
    job.work_unit_id = 'unit-detach'
    job.execution_environment = execution_environment
    job.save()

    receptor_job = _detached_receptor_job(mocker)
    receptor_job.run.side_effect = ConnectionRefusedError(111, 'Connection refused')
    mocker.patch('awx.main.tasks.jobs.AWXReceptorJob', return_value=receptor_job)
    mocker.patch.object(RunJob, 'pre_run_hook')
    mocker.patch.object(RunJob, 'build_project_dir')
    mock_finalize = mocker.patch('awx.main.tasks.jobs._finalize_job_run')
    mock_post_run = mocker.patch.object(RunJob, 'post_run_hook')

    RunJob().run(job.id)

    job.refresh_from_db()
    assert job.status == 'running'
    assert job.work_unit_id == 'unit-detach'
    mock_finalize.assert_not_called()
    mock_post_run.assert_not_called()
    receptor_job._receptor_release_work.assert_not_called()


@pytest.mark.django_db
def test_run_finalizes_normally_when_not_detached(jt_linked, execution_environment, mocker):
    """The guard must not swallow the shutdown path it replaces: an undetached stream still
    finalizes and releases, exactly as it did before."""
    job = jt_linked.create_unified_job()
    job.status = 'running'
    job.work_unit_id = 'unit-cancel'
    job.execution_environment = execution_environment
    job.save()

    receptor_job = _detached_receptor_job(mocker, unit_id='unit-cancel')
    receptor_job.detached = False
    mocker.patch('awx.main.tasks.jobs.AWXReceptorJob', return_value=receptor_job)
    mocker.patch.object(RunJob, 'pre_run_hook')
    mocker.patch.object(RunJob, 'build_project_dir')
    mock_finalize = mocker.patch('awx.main.tasks.jobs._finalize_job_run')
    mocker.patch.object(RunJob, 'post_run_hook')

    task = RunJob()

    # AwxTaskError.TaskError is a plain Exception carrying attributes, so the message is the
    # only thing that distinguishes the failed-job raise from an unrelated error.
    with pytest.raises(Exception, match=r'encountered an error \(rc=1\)'):
        task.run(job.id)

    mock_finalize.assert_called_once()
    assert mock_finalize.call_args[0][3] == 'failed'
    receptor_job._receptor_release_work.assert_called_once()


def _run_with_receptor_dying(jt_linked, execution_environment, mocker, unit_id=None, signal_on_failure=True, on_failure=None):
    """Run a job whose receptor call fails; the shutdown signal lands during that call.

    The pre-EE signal check has already passed by then, which is the window a pod kill hits:
    the receptor container dies with the pod, and the signal flag is set around the same time.
    """
    job = jt_linked.create_unified_job()
    job.status = 'running'
    job.controller_node = 'controller-a'
    job.execution_node = 'ee-1'
    job.execution_environment = execution_environment
    job.save()

    shutdown = {'signalled': False}

    def receptor_fails(*args, **kwargs):
        shutdown['signalled'] = signal_on_failure
        if on_failure:
            on_failure(job)
        raise ConnectionRefusedError(111, 'Connection refused')

    receptor_job = _detached_receptor_job(mocker, unit_id=unit_id)
    receptor_job.detached = False
    receptor_job.run.side_effect = receptor_fails
    mocker.patch('awx.main.tasks.jobs.AWXReceptorJob', return_value=receptor_job)
    mocker.patch('awx.main.tasks.jobs.signal_callback', side_effect=lambda: shutdown['signalled'])
    mocker.patch.object(RunJob, 'pre_run_hook')
    mocker.patch.object(RunJob, 'build_project_dir')
    mock_finalize = mocker.patch('awx.main.tasks.jobs._finalize_job_run')
    mock_post_run = mocker.patch.object(RunJob, 'post_run_hook')

    try:
        RunJob().run(job.id)
    except Exception:
        pass  # a finalized error re-raises TaskError; the assertions look at what was recorded

    job.refresh_from_db()
    return job, mock_finalize, mock_post_run


@pytest.mark.django_db
def test_run_resets_job_to_pending_when_receptor_dies_at_shutdown(jt_linked, execution_environment, mocker):
    """A shutdown that takes receptor down before any work unit exists must not fail the job.

    The pod stops every container at once, so the receptor container can die after the
    pre-EE signal check and before submit_work. Nothing reached an EE and no work_unit_id
    was saved, so the orphan scan can never pick the job up: pending is the only recovery.
    """
    job, mock_finalize, mock_post_run = _run_with_receptor_dying(jt_linked, execution_environment, mocker)

    assert job.status == 'pending'
    assert job.controller_node == ''
    assert job.execution_node == ''
    mock_finalize.assert_not_called()
    mock_post_run.assert_not_called()


@pytest.mark.django_db
def test_run_still_errors_when_receptor_fails_without_shutdown(jt_linked, execution_environment, mocker):
    """Only a shutdown makes a receptor failure retryable; a plain one is still an error."""
    job, mock_finalize, _ = _run_with_receptor_dying(jt_linked, execution_environment, mocker, signal_on_failure=False)

    mock_finalize.assert_called_once()
    assert mock_finalize.call_args[0][3] == 'error'


@pytest.mark.django_db
def test_run_still_errors_when_work_unit_exists_at_shutdown(jt_linked, execution_environment, mocker):
    """Once a work unit was created the EE may be running the job, so re-dispatching could run it twice."""
    job, mock_finalize, _ = _run_with_receptor_dying(jt_linked, execution_environment, mocker, unit_id='unit-created')

    mock_finalize.assert_called_once()
    assert mock_finalize.call_args[0][3] == 'error'


@pytest.mark.django_db
def test_run_does_not_reset_to_pending_when_user_cancelled_during_shutdown(jt_linked, execution_environment, mocker):
    """SIGUSR1 is also the dispatcher's cancel signal; cancel_flag is what tells the two apart.

    The flag is set after this task loaded the job, so only a fresh read sees it.
    """

    def user_cancels(job):
        type(job).objects.filter(pk=job.pk).update(cancel_flag=True)

    job, mock_finalize, _ = _run_with_receptor_dying(jt_linked, execution_environment, mocker, on_failure=user_cancels)

    assert job.status != 'pending'
    mock_finalize.assert_called_once()


@pytest.mark.django_db
def test_run_does_not_reset_to_pending_when_receptor_dies_during_submit(jt_linked, execution_environment, mocker):
    """receptor starts the unit before it replies, so a submit that got no reply may have a playbook running."""

    def submit_started(job):
        type(job).objects.filter(pk=job.pk).update(job_env={'receptor_submit_started': True})

    job, mock_finalize, _ = _run_with_receptor_dying(jt_linked, execution_environment, mocker, on_failure=submit_started)

    assert job.status != 'pending'
    mock_finalize.assert_called_once()


@pytest.mark.django_db
def test_run_errors_local_system_job_that_loses_redis_at_shutdown(mocker):
    """A system job runs ansible-runner inside the controller pod, so it may have done work by the
    time redis (a pod container) goes away; only receptor jobs that never reached an EE are safe to re-dispatch."""
    job = SystemJob.objects.create(job_type='cleanup_jobs', status='running', controller_node='controller-a')
    mocker.patch('awx.main.tasks.jobs.signal_callback', return_value=True)
    mocker.patch('awx.main.tasks.jobs.ansible_runner.interface.run', side_effect=ConnectionError('Error 2 connecting to /var/run/redis/redis.sock.'))
    mock_finalize = mocker.patch('awx.main.tasks.jobs._finalize_job_run')
    mocker.patch.object(RunSystemJob, 'post_run_hook')

    try:
        RunSystemJob().run(job.id)
    except Exception:
        pass  # a finalized error re-raises TaskError

    job.refresh_from_db()
    assert job.status != 'pending'
    mock_finalize.assert_called_once()
    assert mock_finalize.call_args[0][3] == 'error'


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
