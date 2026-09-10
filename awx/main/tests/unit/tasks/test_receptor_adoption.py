"""Unit tests for receptor job adoption (same-controller restart reattach).

Covers:
  - reattach_to_work_unit: all branch paths
  - AWXReceptorJob._process_phase / _handle_work_error: all branch paths
  - receptor_config_exists
  - _get_or_create_private_data_dir
  - should_update_config FileNotFoundError path
"""

import json
import socket
from collections import namedtuple
from unittest.mock import MagicMock, Mock, patch

import pytest

from awx.main.models import Job
from awx.main.tasks.callback import RunnerCallback
from awx.main.tasks.jobs import _finalize_job_run
from awx.main.tasks.receptor import (
    AWXReceptorJob,
    _AdoptionTask,
    _compute_adoption_dedup,
    _configure_runner_callback,
    _finalize_adopted_job,
    _get_adoption_exit_code,
    _get_or_create_private_data_dir,
    adopt_remote_work,
    receptor_config_exists,
    reattach_to_work_unit,
    should_update_config,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_Result = namedtuple('result', ['status', 'rc'])


def _make_receptor_job(unit_id='unit-1', extra_update_fields=None, event_ct=0):
    """Return a minimal AWXReceptorJob built without touching Django models."""
    rj = AWXReceptorJob.__new__(AWXReceptorJob)
    task = Mock()
    task.instance.is_container_group_task = False
    task.instance.execution_node = 'remote-node'
    task.instance.controller_node = 'controller-node'
    task.instance.log_format = 'job 1'
    task.instance.pk = 1
    task.instance.id = 1
    task.instance.work_unit_id = unit_id
    task.runner_callback.extra_update_fields = extra_update_fields if extra_update_fields is not None else {}
    task.runner_callback.event_ct = event_ct
    rj.task = task
    rj.unit_id = unit_id
    rj.runner_params = {'private_data_dir': '/tmp/test'}
    return rj


def _make_receptor_ctl(state='Succeeded', exit_code=None, detail='', stdout_size=0):
    """Return a mock ReceptorControl with configurable work-status response."""
    ctl = Mock()
    status = {'StateName': state, 'Detail': detail, 'StdoutSize': stdout_size}
    if exit_code is not None:
        status['ExitCode'] = exit_code
    ctl.simple_command.return_value = status
    sock_mock = Mock(spec=socket.socket)
    file_mock = MagicMock()
    file_mock.readlines.return_value = [b'some output']
    ctl.get_work_results.return_value = (sock_mock, file_mock)
    return ctl


# ---------------------------------------------------------------------------
# receptor_config_exists
# ---------------------------------------------------------------------------


def test_receptor_config_exists_true():
    with patch('awx.main.tasks.receptor.os.path.exists', return_value=True):
        assert receptor_config_exists() is True


def test_receptor_config_exists_false():
    with patch('awx.main.tasks.receptor.os.path.exists', return_value=False):
        assert receptor_config_exists() is False


# ---------------------------------------------------------------------------
# _get_or_create_private_data_dir
# ---------------------------------------------------------------------------


def test_get_or_create_private_data_dir(tmp_path):
    job = Mock()
    job.pk = 42
    with patch('awx.main.tasks.receptor.settings') as s:
        s.AWX_ISOLATION_BASE_PATH = str(tmp_path)
        result = _get_or_create_private_data_dir(job)
    import os

    assert os.path.isdir(result)
    assert 'adoption_' in result
    os.rmdir(result)


# ---------------------------------------------------------------------------
# should_update_config — FileNotFoundError path (new in this PR)
# ---------------------------------------------------------------------------


def test_should_update_config_file_not_found():
    with patch('awx.main.tasks.receptor.read_receptor_config', side_effect=FileNotFoundError):
        assert should_update_config([]) is True


# ---------------------------------------------------------------------------
# AWXReceptorJob._process_phase — success path
# ---------------------------------------------------------------------------


@patch('awx.main.tasks.receptor.connections')
@patch('awx.main.tasks.receptor.signal_callback', return_value=False)
def test_process_phase_success(mock_signal, mock_connections):
    rj = _make_receptor_job()
    expected_res = _Result(status='successful', rc=0)
    rj.processor = Mock(return_value=expected_res)
    ctl = _make_receptor_ctl()

    res = rj._process_phase(ctl)

    assert res.status == 'successful'
    mock_connections.close_all.assert_called_once()


# ---------------------------------------------------------------------------
# AWXReceptorJob._process_phase — SignalExit path
# ---------------------------------------------------------------------------


@patch('awx.main.tasks.receptor.connections')
@patch('awx.main.tasks.receptor.signal_callback', return_value=True)
def test_process_phase_signal_exit(mock_signal, mock_connections):
    rj = _make_receptor_job()
    rj.processor = Mock()
    ctl = _make_receptor_ctl()

    res = rj._process_phase(ctl)

    assert res.status == 'canceled'
    ctl.simple_command.assert_any_call('work cancel unit-1')


# ---------------------------------------------------------------------------
# _handle_work_error — result_traceback already recorded → return res early
# ---------------------------------------------------------------------------


def test_handle_work_error_result_traceback_present():
    rj = _make_receptor_job(extra_update_fields={'result_traceback': 'boom'})
    ctl = _make_receptor_ctl()
    err_res = _Result(status='error', rc=1)

    result = rj._handle_work_error(ctl, err_res)

    assert result is err_res
    ctl.simple_command.assert_not_called()


# ---------------------------------------------------------------------------
# _handle_work_error — status command raises exception
# ---------------------------------------------------------------------------


def test_handle_work_error_status_command_raises():
    rj = _make_receptor_job()
    ctl = Mock()
    ctl.simple_command.side_effect = Exception('network error')
    err_res = _Result(status='error', rc=1)

    # should not raise; falls through and returns res
    result = rj._handle_work_error(ctl, err_res)
    assert result is err_res


# ---------------------------------------------------------------------------
# _handle_work_error — 'exceeded quota' in detail
# ---------------------------------------------------------------------------


def test_handle_work_error_exceeded_quota():
    rj = _make_receptor_job()
    ctl = _make_receptor_ctl(detail='exceeded quota for namespace')
    err_res = _Result(status='error', rc=1)

    result = rj._handle_work_error(ctl, err_res)

    assert result is None
    rj.task.update_model.assert_called_once_with(1, status='pending')


# ---------------------------------------------------------------------------
# _handle_work_error — Failed state with no events → reads receptor stdout
# ---------------------------------------------------------------------------


def test_handle_work_error_reads_receptor_output_on_failed():
    rj = _make_receptor_job(event_ct=0)
    ctl = _make_receptor_ctl(state='Failed', stdout_size=2000)
    err_res = _Result(status='error', rc=1)

    rj._handle_work_error(ctl, err_res)

    rj.task.runner_callback.delay_update.assert_called_once()
    call_kwargs = rj.task.runner_callback.delay_update.call_args[1]
    assert 'Worker output' in call_kwargs.get('result_traceback', '')


# ---------------------------------------------------------------------------
# _handle_work_error — detail present, no receptor output → delay_update with detail
# ---------------------------------------------------------------------------


def test_handle_work_error_detail_only():
    rj = _make_receptor_job(event_ct=1)  # event_ct > 0, so no stdout fetch
    ctl = _make_receptor_ctl(state='Succeeded', detail='some error detail')
    err_res = _Result(status='error', rc=1)

    rj._handle_work_error(ctl, err_res)

    rj.task.runner_callback.delay_update.assert_called_once()
    call_kwargs = rj.task.runner_callback.delay_update.call_args[1]
    assert 'Receptor detail' in call_kwargs.get('result_traceback', '')


# ---------------------------------------------------------------------------
# _handle_work_error — no detail, no output → logs warning, returns res
# ---------------------------------------------------------------------------


def test_handle_work_error_no_detail_no_output():
    rj = _make_receptor_job(event_ct=1)
    ctl = _make_receptor_ctl(state='Succeeded', detail='')
    err_res = _Result(status='error', rc=1)

    result = rj._handle_work_error(ctl, err_res)

    assert result is err_res
    rj.task.runner_callback.delay_update.assert_not_called()


# ---------------------------------------------------------------------------
# _handle_work_error — get_work_results raises → RuntimeError propagated
# ---------------------------------------------------------------------------


def test_handle_work_error_get_results_raises():
    rj = _make_receptor_job(event_ct=0)
    ctl = _make_receptor_ctl(state='Failed', stdout_size=500)
    ctl.get_work_results.side_effect = Exception('socket error')
    err_res = _Result(status='error', rc=1)

    with pytest.raises(RuntimeError):
        rj._handle_work_error(ctl, err_res)


# ---------------------------------------------------------------------------
# reattach_to_work_unit — callback.job_created is set from job.created
# ---------------------------------------------------------------------------


@patch('awx.main.tasks.jobs._finalize_job_run')
@patch('awx.main.tasks.receptor._compute_adoption_dedup', return_value=(0, set()))
@patch('awx.main.tasks.receptor.AWXReceptorJob._process_phase')
@patch('awx.main.tasks.receptor.AWXReceptorJob._receptor_release_work')
@patch('awx.main.tasks.receptor._get_or_create_private_data_dir', return_value='/tmp/adopt')
@patch('awx.main.tasks.receptor.shutil.rmtree')
def test_reattach_sets_job_created_on_callback(mock_rmtree, mock_pdd, mock_release, mock_process, mock_dedup, mock_finalize):
    """callback.job_created must be set so events are stored with the correct timestamp."""
    job = Mock()
    job.id = 1
    job.work_unit_id = 'unit-1'
    job.created = '2026-01-01T00:00:00Z'
    job.spawned_by_workflow = False
    job.status = 'successful'
    ctl = Mock()
    ctl.simple_command.return_value = {'StateName': 'Succeeded', 'ExitCode': 0, 'Detail': ''}

    from awx.main.tasks.callback import RunnerCallback as RealCallback

    created_callbacks = []
    original_cb_init = RealCallback.__init__

    def capturing_cb_init(self, model=None):
        original_cb_init(self, model)
        created_callbacks.append(self)

    with patch.object(RealCallback, '__init__', capturing_cb_init):
        reattach_to_work_unit(job, ctl)

    assert len(created_callbacks) == 1
    assert created_callbacks[0].job_created == str(job.created)


# ---------------------------------------------------------------------------
# reattach_to_work_unit — _receptor_release_work called after success and failure
# ---------------------------------------------------------------------------


@patch('awx.main.tasks.jobs._finalize_job_run')
@patch('awx.main.tasks.receptor._compute_adoption_dedup', return_value=(0, set()))
@patch('awx.main.tasks.receptor.AWXReceptorJob._process_phase')
@patch('awx.main.tasks.receptor.AWXReceptorJob._receptor_release_work')
@patch('awx.main.tasks.receptor._get_or_create_private_data_dir', return_value='/tmp/adopt')
@patch('awx.main.tasks.receptor.shutil.rmtree')
def test_reattach_releases_work_unit_on_success(mock_rmtree, mock_pdd, mock_release, mock_process, mock_dedup, mock_finalize):
    """_receptor_release_work must be called after _finalize_adopted_job."""
    job = Mock()
    job.id = 1
    job.work_unit_id = 'unit-1'
    job.spawned_by_workflow = False
    job.status = 'successful'
    job.started = None
    ctl = Mock()
    ctl.simple_command.return_value = {'StateName': ''}
    mock_process.return_value = Mock(status='successful', rc=0)

    reattach_to_work_unit(job, ctl)

    mock_release.assert_called_once()


@patch('awx.main.tasks.jobs._finalize_job_run')
@patch('awx.main.tasks.receptor._compute_adoption_dedup', return_value=(0, set()))
@patch('awx.main.tasks.receptor.AWXReceptorJob._process_phase', side_effect=RuntimeError('network failure'))
@patch('awx.main.tasks.receptor.AWXReceptorJob._receptor_release_work')
@patch('awx.main.tasks.receptor._get_or_create_private_data_dir', return_value='/tmp/adopt')
@patch('awx.main.tasks.receptor.shutil.rmtree')
def test_reattach_releases_work_unit_on_failure(mock_rmtree, mock_pdd, mock_release, mock_process, mock_dedup, mock_finalize):
    """_receptor_release_work must run even when _process_phase raises."""
    job = Mock()
    job.id = 1
    job.work_unit_id = 'unit-1'
    job.spawned_by_workflow = False
    job.started = None
    job.status = 'running'
    ctl = Mock()
    ctl.simple_command.side_effect = [
        {'StateName': ''},  # initial state check (unknown → _process_phase)
        {'StateName': 'Succeeded', 'ExitCode': 0, 'Detail': ''},  # fallback re-check
    ]

    result = reattach_to_work_unit(job, ctl)

    assert result is True  # finalized via exit_code path
    mock_release.assert_called_once()
    mock_finalize.assert_called_once()  # _finalize_job_run was invoked


# ---------------------------------------------------------------------------
# reattach_to_work_unit — spawned_by_workflow=True → parent_workflow_job_id set
# ---------------------------------------------------------------------------


@patch('awx.main.tasks.jobs._finalize_job_run')
@patch('awx.main.tasks.receptor._compute_adoption_dedup', return_value=(0, set()))
@patch('awx.main.tasks.receptor.AWXReceptorJob._process_phase')
@patch('awx.main.tasks.receptor.AWXReceptorJob._receptor_release_work')
@patch('awx.main.tasks.receptor._get_or_create_private_data_dir', return_value='/tmp/adopt')
@patch('awx.main.tasks.receptor.shutil.rmtree')
def test_reattach_sets_parent_workflow_job_id_when_workflow_child(mock_rmtree, mock_pdd, mock_release, mock_process, mock_dedup, mock_finalize):
    """callback.parent_workflow_job_id must be set for workflow-child jobs so events are
    correctly associated with their parent workflow in the event stream."""
    job = Mock()
    job.id = 1
    job.work_unit_id = 'unit-1'
    job.created = '2026-01-01T00:00:00Z'
    job.spawned_by_workflow = True
    job.get_workflow_job.return_value.id = 999
    job.status = 'successful'
    ctl = Mock()
    ctl.simple_command.return_value = {'StateName': 'Succeeded', 'ExitCode': 0, 'Detail': ''}

    from awx.main.tasks.callback import RunnerCallback as RealCallback

    created_callbacks = []
    original_cb_init = RealCallback.__init__

    def capturing_cb_init(self, model=None):
        original_cb_init(self, model)
        created_callbacks.append(self)

    with patch.object(RealCallback, '__init__', capturing_cb_init):
        reattach_to_work_unit(job, ctl)

    assert len(created_callbacks) == 1
    assert created_callbacks[0].parent_workflow_job_id == 999


@patch('awx.main.tasks.jobs._finalize_job_run')
@patch('awx.main.tasks.receptor._compute_adoption_dedup', return_value=(0, set()))
@patch('awx.main.tasks.receptor.AWXReceptorJob._process_phase')
@patch('awx.main.tasks.receptor.AWXReceptorJob._receptor_release_work')
@patch('awx.main.tasks.receptor._get_or_create_private_data_dir', return_value='/tmp/adopt')
@patch('awx.main.tasks.receptor.shutil.rmtree')
def test_reattach_workflow_job_lookup_exception_swallowed(mock_rmtree, mock_pdd, mock_release, mock_process, mock_dedup, mock_finalize):
    """If get_workflow_job() raises, adoption must still complete (bare except: pass)."""
    job = Mock()
    job.id = 1
    job.work_unit_id = 'unit-1'
    job.created = '2026-01-01T00:00:00Z'
    job.spawned_by_workflow = True
    job.get_workflow_job.side_effect = Exception('workflow lookup failed')
    job.status = 'successful'
    ctl = Mock()
    ctl.simple_command.return_value = {'StateName': 'Succeeded', 'ExitCode': 0, 'Detail': ''}

    result = reattach_to_work_unit(job, ctl)

    assert result is True  # exception swallowed, adoption completes


# ---------------------------------------------------------------------------
# _get_adoption_exit_code — all three branches
# ---------------------------------------------------------------------------


def test_get_adoption_exit_code_from_key():
    assert _get_adoption_exit_code({'ExitCode': 42, 'Detail': 'ignored'}, 'Succeeded') == 42


def test_get_adoption_exit_code_from_detail_string():
    assert _get_adoption_exit_code({'Detail': 'exit status 1'}, 'Failed') == 1


def test_get_adoption_exit_code_fallback_succeeded():
    assert _get_adoption_exit_code({'Detail': 'no int here!'}, 'Succeeded') == 0


def test_get_adoption_exit_code_fallback_failed():
    assert _get_adoption_exit_code({}, 'Failed') == 1


# ---------------------------------------------------------------------------
# _AdoptionTask — method coverage
# ---------------------------------------------------------------------------


def test_adoption_task_build_ee_params_returns_empty_dict():
    task = _AdoptionTask(Mock(), Mock())
    assert task.build_execution_environment_params(None, None) == {}


def test_adoption_task_update_model_is_noop():
    task = _AdoptionTask(Mock(), Mock())
    task.update_model(1, status='successful', result_traceback='boom')  # must not raise


# ---------------------------------------------------------------------------
# _configure_runner_callback — shared initialization for normal + adoption paths
# ---------------------------------------------------------------------------


def test_configure_runner_callback_sets_common_fields():
    from awx.main.tasks.callback import RunnerCallback

    cb = RunnerCallback(model=None)
    instance = Mock()
    instance.created = '2026-01-01T00:00:00Z'
    instance.spawned_by_workflow = False

    _configure_runner_callback(cb, instance, safe_env={'KEY': 'val'}, dedup_threshold=5, persisted_counters={6, 7})

    assert cb.instance is instance
    assert cb.job_created == str(instance.created)
    assert cb.safe_env == {'KEY': 'val'}
    assert cb.dedup_threshold == 5
    assert cb.persisted_counters == {6, 7}


def test_configure_runner_callback_safe_env_defaults_to_empty_dict():
    from awx.main.tasks.callback import RunnerCallback

    cb = RunnerCallback(model=None)
    instance = Mock()
    instance.created = '2026-01-01'
    instance.spawned_by_workflow = False

    _configure_runner_callback(cb, instance)

    assert cb.safe_env == {}
    assert cb.dedup_threshold is None
    assert cb.persisted_counters is None


def test_configure_runner_callback_sets_parent_workflow_job_id():
    from awx.main.tasks.callback import RunnerCallback

    cb = RunnerCallback(model=None)
    instance = Mock()
    instance.created = '2026-01-01'
    instance.spawned_by_workflow = True
    instance.get_workflow_job.return_value.id = 42

    _configure_runner_callback(cb, instance)

    assert cb.parent_workflow_job_id == 42


def test_configure_runner_callback_swallows_workflow_lookup_error():
    from awx.main.tasks.callback import RunnerCallback

    cb = RunnerCallback(model=None)
    instance = Mock()
    instance.created = '2026-01-01'
    instance.spawned_by_workflow = True
    instance.get_workflow_job.side_effect = Exception('lookup failed')

    _configure_runner_callback(cb, instance)  # must not raise
    assert cb.parent_workflow_job_id is None


# ---------------------------------------------------------------------------
# _build_adoption_callback — spawned_by_workflow False path
# ---------------------------------------------------------------------------


@patch('awx.main.tasks.jobs._finalize_job_run')
@patch('awx.main.tasks.receptor._compute_adoption_dedup', return_value=(0, set()))
@patch('awx.main.tasks.receptor.AWXReceptorJob._process_phase')
@patch('awx.main.tasks.receptor.AWXReceptorJob._receptor_release_work')
@patch('awx.main.tasks.receptor._get_or_create_private_data_dir', return_value='/tmp/adopt')
@patch('awx.main.tasks.receptor.shutil.rmtree')
def test_reattach_non_workflow_job_no_parent_id(mock_rmtree, mock_pdd, mock_release, mock_process, mock_dedup, mock_finalize):
    """callback.parent_workflow_job_id is NOT set for non-workflow jobs."""
    job = Mock()
    job.id = 1
    job.work_unit_id = 'unit-1'
    job.created = '2026-01-01T00:00:00Z'
    job.spawned_by_workflow = False
    job.status = 'successful'
    ctl = Mock()
    ctl.simple_command.return_value = {'StateName': 'Succeeded', 'ExitCode': 0, 'Detail': ''}

    from awx.main.tasks.callback import RunnerCallback as RealCallback

    created_callbacks = []
    original_cb_init = RealCallback.__init__

    def capturing_cb_init(self, model=None):
        original_cb_init(self, model)
        created_callbacks.append(self)

    with patch.object(RealCallback, '__init__', capturing_cb_init):
        reattach_to_work_unit(job, ctl)

    assert created_callbacks[0].parent_workflow_job_id is None


# ---------------------------------------------------------------------------
# reattach_to_work_unit — streams immediately even for still-running units
# ---------------------------------------------------------------------------


@patch('awx.main.tasks.jobs._finalize_job_run')
@patch('awx.main.tasks.receptor._compute_adoption_dedup', return_value=(0, set()))
@patch('awx.main.tasks.receptor.AWXReceptorJob._process_phase')
@patch('awx.main.tasks.receptor.AWXReceptorJob._receptor_release_work')
@patch('awx.main.tasks.receptor._get_or_create_private_data_dir', return_value='/tmp/adopt')
@patch('awx.main.tasks.receptor.shutil.rmtree')
def test_reattach_running_defers_without_streaming_variant(mock_rmtree, mock_pdd, mock_release, mock_process, mock_dedup, mock_finalize):
    """Running state returns False — stdout forwarding is not available for adopted units.

    PR#1564 work adopt starts a status-monitoring goroutine but does not proxy the EE's
    stdout bytes to the adopting node.  Calling _process_phase → get_work_results would
    block forever on the empty local stdout file.  Return False so the heartbeat retries.
    """
    job = Mock()
    job.id = 1
    job.work_unit_id = 'unit-running'
    job.created = '2026-01-01T00:00:00Z'
    job.spawned_by_workflow = False
    job.status = 'running'
    job.started = None
    ctl = Mock()
    ctl.simple_command.return_value = {'StateName': 'Running'}

    result = reattach_to_work_unit(job, ctl)

    mock_process.assert_not_called()
    assert result is False


@patch('awx.main.tasks.jobs._finalize_job_run')
@patch('awx.main.tasks.receptor._compute_adoption_dedup', return_value=(0, set()))
@patch('awx.main.tasks.receptor.AWXReceptorJob._process_phase')
@patch('awx.main.tasks.receptor.AWXReceptorJob._receptor_release_work')
@patch('awx.main.tasks.receptor._get_or_create_private_data_dir', return_value='/tmp/adopt')
@patch('awx.main.tasks.receptor.shutil.rmtree')
def test_reattach_process_phase_failure_falls_back_to_work_status(mock_rmtree, mock_pdd, mock_release, mock_process, mock_dedup, mock_finalize):
    """When _process_phase raises, exit code falls back to work status re-check.

    If the re-check also fails, the exception is swallowed and the job is finalized
    with exit_code=1 (failed). This path only triggers when _process_phase itself
    raises (process_phase_failed=True), not when the job streams normally.
    """
    job = Mock()
    job.id = 1
    job.work_unit_id = 'unit-recheck-err'
    job.created = '2026-01-01T00:00:00Z'
    job.spawned_by_workflow = False
    job.status = 'running'
    job.started = None
    ctl = Mock()
    # Initial check: Running (falls through to _process_phase); re-check after raise also raises
    ctl.simple_command.side_effect = [
        {'StateName': ''},  # initial state check (unknown → _process_phase)
        RuntimeError('socket closed'),
    ]
    mock_process.side_effect = RuntimeError('process phase failed')

    result = reattach_to_work_unit(job, ctl)  # must not raise

    # Returns True (function completed without re-raising)
    assert result is True


# ---------------------------------------------------------------------------
# reattach_to_work_unit — state guards (Pending / terminal / Running)
# ---------------------------------------------------------------------------


def test_reattach_pending_defers_without_streaming():
    """Pending state returns False immediately — avoids the infinite get_work_results block.

    When work adopt creates a cross-controller adoption unit it starts in Pending while
    the receptor mesh connects.  get_work_results would block forever because the adopted
    unit's stdout pipe is not yet (and may never be) forwarded.  We return False so
    adopt_job_async exits cleanly and _process_running_jobs re-queues it next heartbeat.
    """
    job = Mock()
    job.id = 42
    job.work_unit_id = 'unit-pending'
    ctl = Mock()
    ctl.simple_command.return_value = {'StateName': 'Pending'}

    with patch('awx.main.tasks.receptor.AWXReceptorJob._process_phase') as mock_process:
        result = reattach_to_work_unit(job, ctl)

    assert result is False
    mock_process.assert_not_called()


@patch('awx.main.tasks.jobs._finalize_job_run')
@patch('awx.main.tasks.receptor._finalize_adopted_job')
@patch('awx.main.tasks.receptor._compute_adoption_dedup', return_value=(0, set()))
@patch('awx.main.tasks.receptor.AWXReceptorJob._receptor_release_work')
@patch('awx.main.tasks.receptor._get_or_create_private_data_dir', return_value='/tmp/adopt')
@patch('awx.main.tasks.receptor.shutil.rmtree')
def test_reattach_succeeded_goes_through_process_phase(mock_rmtree, mock_pdd, mock_release, mock_dedup, mock_finalize_job, mock_finalize_run):
    """Succeeded units now go through _process_phase so output is not missed.

    The terminal fast-path was removed — all non-Pending/Running units stream
    through _process_phase so the dedup can skip already-committed events while
    still capturing any output that arrived after the DB snapshot.
    """
    job = Mock()
    job.id = 42
    job.work_unit_id = 'unit-done'
    job.spawned_by_workflow = False
    job.started = None
    ctl = Mock()
    ctl.simple_command.return_value = {'StateName': 'Succeeded', 'ExitCode': 0, 'Detail': ''}

    with patch('awx.main.tasks.receptor.AWXReceptorJob._process_phase', return_value=Mock(status='successful', rc=0)) as mock_process:
        reattach_to_work_unit(job, ctl)

    mock_process.assert_called_once()
    mock_finalize_job.assert_called_once()
    _, _, exit_code, process_phase_failed = mock_finalize_job.call_args[0]
    assert exit_code == 0
    assert process_phase_failed is False


@patch('awx.main.tasks.jobs._finalize_job_run')
@patch('awx.main.tasks.receptor._finalize_adopted_job')
@patch('awx.main.tasks.receptor._compute_adoption_dedup', return_value=(0, set()))
@patch('awx.main.tasks.receptor.AWXReceptorJob._receptor_release_work')
@patch('awx.main.tasks.receptor._get_or_create_private_data_dir', return_value='/tmp/adopt')
@patch('awx.main.tasks.receptor.shutil.rmtree')
def test_reattach_failed_goes_through_process_phase(mock_rmtree, mock_pdd, mock_release, mock_dedup, mock_finalize_job, mock_finalize_run):
    """Failed units go through _process_phase; exit_code=1 from res.status."""
    job = Mock()
    job.id = 42
    job.work_unit_id = 'unit-failed'
    job.spawned_by_workflow = False
    job.started = None
    ctl = Mock()
    ctl.simple_command.return_value = {'StateName': 'Failed', 'ExitCode': 1, 'Detail': 'exit status 1'}

    with patch('awx.main.tasks.receptor.AWXReceptorJob._process_phase', return_value=Mock(status='failed', rc=1)) as mock_process:
        reattach_to_work_unit(job, ctl)

    mock_process.assert_called_once()
    mock_finalize_job.assert_called_once()
    _, _, exit_code, _ = mock_finalize_job.call_args[0]
    assert exit_code == 1


@patch('awx.main.tasks.jobs._finalize_job_run')
@patch('awx.main.tasks.receptor._finalize_adopted_job')
@patch('awx.main.tasks.receptor._compute_adoption_dedup', return_value=(0, set()))
@patch('awx.main.tasks.receptor.AWXReceptorJob._receptor_release_work')
@patch('awx.main.tasks.receptor._get_or_create_private_data_dir', return_value='/tmp/adopt')
@patch('awx.main.tasks.receptor.shutil.rmtree')
def test_reattach_canceled_goes_through_process_phase(mock_rmtree, mock_pdd, mock_release, mock_dedup, mock_finalize_job, mock_finalize_run):
    """Canceled units go through _process_phase; exit_code=1 (non-successful)."""
    job = Mock()
    job.id = 42
    job.work_unit_id = 'unit-canceled'
    job.spawned_by_workflow = False
    job.started = None
    ctl = Mock()
    ctl.simple_command.return_value = {'StateName': 'Canceled', 'Detail': ''}

    with patch('awx.main.tasks.receptor.AWXReceptorJob._process_phase', return_value=Mock(status='error', rc=1)) as mock_process:
        reattach_to_work_unit(job, ctl)

    mock_process.assert_called_once()
    mock_finalize_job.assert_called_once()
    _, _, exit_code, _ = mock_finalize_job.call_args[0]
    assert exit_code == 1


@patch('awx.main.tasks.jobs._finalize_job_run')
@patch('awx.main.tasks.receptor._compute_adoption_dedup', return_value=(0, set()))
@patch('awx.main.tasks.receptor.AWXReceptorJob._receptor_release_work')
@patch('awx.main.tasks.receptor._get_or_create_private_data_dir', return_value='/tmp/adopt')
@patch('awx.main.tasks.receptor.shutil.rmtree')
def test_reattach_running_defers_without_streaming(mock_rmtree, mock_pdd, mock_release, mock_dedup, mock_finalize):
    """Running state returns False — get_work_results blocks on the adopted unit's 0-byte
    local stdout file.  Defer so adopt_job_async exits and _process_running_jobs retries
    next heartbeat; when the EE finishes the unit becomes terminal and is finalized there.
    """
    job = Mock()
    job.id = 42
    job.work_unit_id = 'unit-running'
    job.spawned_by_workflow = False
    job.started = None
    job.status = 'running'
    ctl = Mock()
    ctl.simple_command.return_value = {'StateName': 'Running'}

    with patch('awx.main.tasks.receptor.AWXReceptorJob._process_phase') as mock_process:
        result = reattach_to_work_unit(job, ctl)

    assert result is False
    mock_process.assert_not_called()


# ---------------------------------------------------------------------------
# _finalize_adopted_job — all branches
# ---------------------------------------------------------------------------


@patch('awx.main.tasks.jobs._finalize_job_run')
def test_finalize_adopted_job_skips_when_already_finalized(mock_finalize):
    """If job.status != 'running' after _process_phase, _finalize_job_run is not called."""
    job = Mock()
    job.status = 'successful'
    callback = Mock()

    _finalize_adopted_job(job, callback, exit_code=0, process_phase_failed=False)

    mock_finalize.assert_not_called()


@patch('awx.main.tasks.jobs._finalize_job_run')
def test_finalize_adopted_job_successful(mock_finalize):
    """exit_code=0 → _finalize_job_run called with status='successful' and finished in extra_fields."""
    job = Mock()
    job.status = 'running'
    job.started = None
    callback = Mock()

    _finalize_adopted_job(job, callback, exit_code=0, process_phase_failed=False)

    mock_finalize.assert_called_once()
    _, _, _, status, extra_fields = (
        mock_finalize.call_args[0][0],
        mock_finalize.call_args[0][1],
        mock_finalize.call_args[0][2],
        mock_finalize.call_args[0][3],
        mock_finalize.call_args[1].get('extra_fields') or mock_finalize.call_args[0][4],
    )
    assert status == 'successful'
    assert 'finished' in extra_fields


@patch('awx.main.tasks.jobs._finalize_job_run')
def test_finalize_adopted_job_failed(mock_finalize):
    """exit_code=1 → _finalize_job_run called with status='failed'."""
    job = Mock()
    job.status = 'running'
    job.started = None
    callback = Mock()

    _finalize_adopted_job(job, callback, exit_code=1, process_phase_failed=False)

    _, _, _, status = mock_finalize.call_args[0][:4]
    assert status == 'failed'


@patch('awx.main.tasks.jobs._finalize_job_run')
def test_finalize_adopted_job_includes_elapsed_when_started(mock_finalize):
    """elapsed is passed in extra_fields when job.started is set."""
    from datetime import datetime, timezone

    job = Mock()
    job.status = 'running'
    job.started = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    callback = Mock()

    _finalize_adopted_job(job, callback, exit_code=0, process_phase_failed=False)

    extra_fields = mock_finalize.call_args[1].get('extra_fields') or mock_finalize.call_args[0][4]
    assert 'elapsed' in extra_fields


@patch('awx.main.tasks.jobs._finalize_job_run')
def test_finalize_adopted_job_process_phase_failed_label(mock_finalize):
    """process_phase_failed=True still calls _finalize_job_run — just changes the log label."""
    job = Mock()
    job.status = 'running'
    job.started = None
    callback = Mock()

    _finalize_adopted_job(job, callback, exit_code=1, process_phase_failed=True)

    mock_finalize.assert_called_once()


# ---------------------------------------------------------------------------
# event_handler dedup_threshold — O(1) integer check
# ---------------------------------------------------------------------------


def test_event_handler_dedup_threshold_skips_below_threshold():
    """Events with counter <= dedup_threshold are skipped without hitting persisted_counters."""
    from awx.main.tasks.callback import RunnerCallback

    cb = RunnerCallback(model=None)
    cb.dedup_threshold = 10
    cb.persisted_counters = None  # not needed — threshold handles it

    dispatched = []
    cb.dispatcher = Mock()
    cb.dispatcher.dispatch.side_effect = dispatched.append

    cb.event_handler({'event': 'runner_on_ok', 'counter': 5})
    cb.event_handler({'event': 'runner_on_ok', 'counter': 10})
    assert len(dispatched) == 0


def test_event_handler_dedup_threshold_lets_through_above_threshold():
    """Events above threshold and not in collision zone are let through."""
    from collections import deque
    from awx.main.tasks.callback import RunnerCallback

    cb = RunnerCallback(model=None)
    cb.dedup_threshold = 5
    cb.persisted_counters = set()

    dispatched = []
    cb.dispatcher = Mock()
    cb.dispatcher.dispatch.side_effect = dispatched.append

    # minimal setup to get past the event_handler guards
    cb.instance = Mock()
    cb.instance.event_class.WRAPUP_EVENT = 'playbook_on_stats'
    cb.event_data_key = 'job_id'
    cb.job_created = None
    cb.parent_workflow_job_id = None
    cb.host_map = {}
    cb.recent_event_timings = deque(maxlen=100)

    cb.event_handler({'event': 'runner_on_ok', 'counter': 6, 'job_id': 1})
    assert len(dispatched) == 1


def test_event_handler_collision_zone_skips():
    """Events above threshold but in collision_zone are skipped."""
    from awx.main.tasks.callback import RunnerCallback

    cb = RunnerCallback(model=None)
    cb.dedup_threshold = 5
    cb.persisted_counters = {7, 8, 9}

    dispatched = []
    cb.dispatcher = Mock()
    cb.dispatcher.dispatch.side_effect = dispatched.append

    cb.event_handler({'event': 'runner_on_ok', 'counter': 7})
    cb.event_handler({'event': 'runner_on_ok', 'counter': 9})
    assert len(dispatched) == 0


# ---------------------------------------------------------------------------
# adopt_remote_work — new receptorctl API and JSON fallback
# ---------------------------------------------------------------------------


@patch('awx.main.tasks.receptor.get_tls_client', return_value=None)
@patch('awx.main.tasks.receptor.work_signing_enabled', return_value=False)
def test_adopt_remote_work_uses_adopt_work_when_available(mock_sign, mock_tls):
    """If adopt_work() is present on receptor_ctl, call it directly."""
    ctl = Mock()
    ctl.adopt_work.return_value = {'unitid': 'u1'}

    result = adopt_remote_work(ctl, node='ee-node', unit_id='u1', config_data={})

    ctl.adopt_work.assert_called_once_with('ee-node', 'u1', tlsclient=None, signwork=False)
    assert result == {'unitid': 'u1'}


@patch('awx.main.tasks.receptor.get_tls_client', return_value=None)
@patch('awx.main.tasks.receptor.work_signing_enabled', return_value=False)
def test_adopt_remote_work_json_fallback_without_tls(mock_sign, mock_tls):
    """Falls back to raw JSON when adopt_work() is absent and no TLS."""
    ctl = Mock(spec=['connect', 'writestr', 'read_and_parse_json'])  # no adopt_work
    ctl.read_and_parse_json.return_value = {'unitid': 'u2'}

    adopt_remote_work(ctl, node='ee-node', unit_id='u2', config_data={})

    ctl.connect.assert_called_once()
    payload = json.loads(ctl.writestr.call_args[0][0].rstrip())
    assert payload == {'command': 'work', 'subcommand': 'adopt', 'node': 'ee-node', 'unitid': 'u2'}
    assert 'tlsclient' not in payload
    assert 'signwork' not in payload


@patch('awx.main.tasks.receptor.get_tls_client', return_value='my-tls')
@patch('awx.main.tasks.receptor.work_signing_enabled', return_value=True)
def test_adopt_remote_work_json_fallback_with_tls_and_sign(mock_sign, mock_tls):
    """JSON fallback includes tlsclient and signwork when configured."""
    ctl = Mock(spec=['connect', 'writestr', 'read_and_parse_json'])  # no adopt_work
    ctl.read_and_parse_json.return_value = {}

    adopt_remote_work(ctl, node='ee-node', unit_id='u3', config_data={})

    payload = json.loads(ctl.writestr.call_args[0][0].rstrip())
    assert payload['tlsclient'] == 'my-tls'
    assert payload['signwork'] is True


# ---------------------------------------------------------------------------
# reattach_to_work_unit — receptor status check exception returns False
# ---------------------------------------------------------------------------


def test_reattach_returns_false_when_status_command_raises():
    """If simple_command('work status ...') raises, return False without crashing."""
    job = Mock()
    job.id = 1
    job.work_unit_id = 'dead-unit'
    job.created = '2026-01-01T00:00:00Z'
    job.spawned_by_workflow = False

    ctl = Mock()
    ctl.simple_command.side_effect = Exception('socket closed')

    result = reattach_to_work_unit(job, ctl)

    assert result is False


# ---------------------------------------------------------------------------
# _compute_adoption_dedup — collision zone cap warning
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_compute_adoption_dedup_logs_warning_when_collision_zone_exceeds_cap(caplog):
    """When collision_zone_list exceeds the dedup cap, a warning is logged and results are capped."""
    job = Mock(spec=Job)
    # Build a queryset-like mock: annotate/filter/values_list chain returns a large list
    large_list = list(range(10000))

    qs = Mock()
    qs.annotate.return_value = qs
    qs.filter.return_value = qs
    qs.order_by.return_value = qs
    qs.first.return_value = None  # no gap → safe_threshold=0
    qs.values_list.return_value = large_list

    job.get_event_queryset.return_value = qs

    with caplog.at_level('WARNING', logger='awx.main.tasks.receptor'):
        safe_threshold, collision_zone = _compute_adoption_dedup(job)

    assert 'collision_zone' in caplog.text
    assert safe_threshold == 0


# ---------------------------------------------------------------------------
# _finalize_job_run — extra_fields merges into update fields
# ---------------------------------------------------------------------------


@patch('awx.main.tasks.jobs.update_model')
def test_finalize_job_run_extra_fields_merged(mock_update):
    """extra_fields dict is merged into the update kwargs alongside runner fields."""
    instance = Mock()
    instance.host_status_counts = None
    mock_update.return_value = instance

    cb = Mock()
    cb.get_delayed_update_fields.return_value = {'emitted_events': 3}
    cb.wrapup_event_dispatched = True

    _finalize_job_run(Mock, pk=1, runner_callback=cb, status='successful', extra_fields={'finished': 'NOW', 'elapsed': 1.5})

    _, kwargs = mock_update.call_args
    assert kwargs['finished'] == 'NOW'
    assert kwargs['elapsed'] == 1.5
    assert kwargs['emitted_events'] == 3


# ---------------------------------------------------------------------------
# _configure_runner_callback — host_map exception swallowed
# ---------------------------------------------------------------------------


def test_configure_runner_callback_swallows_host_map_error():
    """If fetching inventory hosts raises, the exception is swallowed and host_map stays {}."""
    cb = RunnerCallback(model=None)
    instance = Mock()
    instance.created = '2026-01-01'
    instance.spawned_by_workflow = False
    instance.inventory_id = 1
    instance.inventory.hosts.only.side_effect = Exception('DB error')

    _configure_runner_callback(cb, instance)  # must not raise

    assert cb.host_map == {}
