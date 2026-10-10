"""Unit tests for receptor job adoption (same-controller restart reattach).

Covers:
  - reattach_to_work_unit: all branch paths
  - AWXReceptorJob._process_phase / _handle_work_error: all branch paths
  - receptor_config_exists
  - _get_or_create_private_data_dir
  - should_update_config FileNotFoundError path
"""

import concurrent.futures
import json
import signal
import socket
import threading
import time
from collections import namedtuple
from datetime import timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest
from django.test import override_settings
from django.utils.timezone import now

from awx.main.tasks.callback import RunnerCallback
from awx.main.tasks.jobs import _finalize_job_run
from awx.main.tasks.receptor import (
    AWXReceptorJob,
    _AdoptionTask,
    _CountingReader,
    _adopted_finished_at,
    _adoption_stall_budget_exhausted,
    _finalize_adopted_job,
    _get_adoption_exit_code,
    _get_or_create_private_data_dir,
    adopt_remote_work,
    receptor_config_exists,
    reattach_to_work_unit,
    should_update_config,
)
from awx.main.tasks.signals import signal_state

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_Result = namedtuple('result', ['status', 'rc'])


def _make_receptor_job(unit_id='unit-1', extra_update_fields=None, event_ct=0, cancel_flag=False, refresh_error=None):
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
    task.instance.cancel_flag = cancel_flag
    if refresh_error is not None:
        task.instance.refresh_from_db.side_effect = refresh_error
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


def _stub_last_event(job, last=None):
    """Give a Mock job an event queryset that answers the back-dating aggregate.

    `_finalize_adopted_job` reads the last job event to recover when the playbook really
    ended, so a bare Mock is no longer enough — `aggregate()` has to hand back a real dict.
    `last=None` models a job with no events at all, which is the fall-back-to-now() path.
    """
    job.get_event_queryset.return_value.aggregate.return_value = {'last': last}
    return job


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
#
# A signal means one of two unrelated things, and the work unit's fate differs: a cancel
# is about the job, a shutdown is about this controller. This is not adoption-specific —
# every receptor job makes the same distinction.
# ---------------------------------------------------------------------------


@patch('awx.main.tasks.receptor.connections')
@patch('awx.main.tasks.receptor.signal_callback', return_value=True)
def test_process_phase_shutdown_signal_detaches(mock_signal, mock_connections):
    """A shutdown leaves the work unit running instead of canceling it.

    The EE is on another node and still working; this controller going away says nothing
    about the job. _process_running_jobs re-queues adoption for any running job we own, so
    an abandoned unit gets picked back up — a canceled one is gone for good.
    """
    rj = _make_receptor_job(cancel_flag=False)
    rj.processor = Mock()
    ctl = _make_receptor_ctl()

    res = rj._process_phase(ctl)

    assert res.status == 'canceled'
    assert rj.detached is True
    assert not any('work cancel' in str(call) for call in ctl.simple_command.call_args_list)


@patch('awx.main.tasks.receptor.connections')
@patch('awx.main.tasks.receptor.signal_callback', return_value=True)
def test_process_phase_sigusr1_without_cancel_flag_detaches(mock_signal, mock_connections):
    """SIGUSR1 alone does not mean the user canceled the job.

    This is the exact production shutdown: dispatcherd signals every running worker with
    SIGUSR1 while 'canceling for shutdown', so SIGUSR1 arrives with no SIGTERM and no
    cancel_flag. Reading it as a cancel kills a healthy EE on every pod restart, which is
    the whole failure adoption exists to prevent.
    """
    rj = _make_receptor_job(cancel_flag=False)
    rj.processor = Mock()
    ctl = _make_receptor_ctl()

    with patch.dict(signal_state.signal_flags, {signal.SIGUSR1: True}):
        res = rj._process_phase(ctl)

    assert res.status == 'canceled'
    assert rj.detached is True
    assert not any('work cancel' in str(call) for call in ctl.simple_command.call_args_list)


@patch('awx.main.tasks.receptor.connections')
@patch('awx.main.tasks.receptor.signal_callback', return_value=True)
def test_process_phase_cancel_flag_cancels_unit(mock_signal, mock_connections):
    """A real cancel is identified by the job row, which cancel() commits before it signals."""
    rj = _make_receptor_job(cancel_flag=True)
    rj.processor = Mock()
    ctl = _make_receptor_ctl()

    with patch.dict(signal_state.signal_flags, {signal.SIGUSR1: True}):
        res = rj._process_phase(ctl)

    assert res.status == 'canceled'
    assert rj.detached is False
    ctl.simple_command.assert_any_call('work cancel unit-1')


@patch('awx.main.tasks.receptor.connections')
@patch('awx.main.tasks.receptor.signal_callback', return_value=True)
def test_process_phase_cancel_survives_dead_control_socket(mock_signal, mock_connections):
    """A failed 'work cancel' must not escape as an unhandled exception.

    The receptor control socket lives in a sibling container that dies alongside this one,
    so on shutdown the cancel attempt routinely hits ConnectionRefusedError. If that
    propagates it lands in BaseTask.run()'s generic handler, which records the job 'error'
    and destroys the running + work_unit_id pair the orphan scan matches on.
    """
    rj = _make_receptor_job(cancel_flag=True)
    rj.processor = Mock()
    ctl = _make_receptor_ctl()
    ctl.simple_command.side_effect = ConnectionRefusedError(111, 'Connection refused')

    with patch.dict(signal_state.signal_flags, {signal.SIGUSR1: True}):
        res = rj._process_phase(ctl)

    assert res.status == 'canceled'
    assert rj.detached is False


@patch('awx.main.tasks.receptor.connections')
@patch('awx.main.tasks.receptor.signal_callback', return_value=True)
def test_process_phase_detaches_when_cancel_flag_unreadable(mock_signal, mock_connections):
    """If the cancel_flag cannot be read, detach — killing a healthy job is the worse error."""
    rj = _make_receptor_job(cancel_flag=True, refresh_error=RuntimeError('db gone'))
    rj.processor = Mock()
    ctl = _make_receptor_ctl()

    res = rj._process_phase(ctl)

    assert res.status == 'canceled'
    assert rj.detached is True
    assert not any('work cancel' in str(call) for call in ctl.simple_command.call_args_list)


# ---------------------------------------------------------------------------
# reattach_to_work_unit — detach and cancel outcomes
# ---------------------------------------------------------------------------


@patch('awx.main.tasks.jobs._finalize_job_run')
@patch('awx.main.tasks.receptor._finalize_adopted_job')
@patch('awx.main.tasks.receptor._compute_adoption_dedup', return_value=(0, set(), 0))
@patch('awx.main.tasks.receptor.AWXReceptorJob._receptor_release_work')
@patch('awx.main.tasks.receptor._get_or_create_private_data_dir', return_value='/tmp/adopt')
@patch('awx.main.tasks.receptor.shutil.rmtree')
def test_reattach_detach_leaves_job_running_and_unit_alive(mock_rmtree, mock_pdd, mock_release, mock_dedup, mock_finalize_job, mock_finalize_run):
    """A detached stream finalizes nothing and releases nothing — the job stays adoptable."""
    job = Mock()
    job.id = 5
    job.work_unit_id = 'unit-detach'
    job.spawned_by_workflow = False
    job.started = None
    job.execution_node = None
    job.job_env = {}
    ctl = Mock()
    ctl.simple_command.return_value = {'StateName': 'Running'}

    def _detach(self, receptor_ctl):
        self.detached = True
        return _Result(status='canceled', rc=1)

    with patch.object(AWXReceptorJob, '_process_phase', autospec=True, side_effect=_detach):
        result = reattach_to_work_unit(job, ctl)

    assert result is False
    mock_finalize_job.assert_not_called()
    mock_release.assert_not_called()
    mock_rmtree.assert_called_once_with('/tmp/adopt', ignore_errors=True)


@patch('awx.main.tasks.jobs._finalize_job_run')
@patch('awx.main.tasks.receptor._finalize_adopted_job')
@patch('awx.main.tasks.receptor._compute_adoption_dedup', return_value=(0, set(), 0))
@patch('awx.main.tasks.receptor.AWXReceptorJob._receptor_release_work')
@patch('awx.main.tasks.receptor._get_or_create_private_data_dir', return_value='/tmp/adopt')
@patch('awx.main.tasks.receptor.shutil.rmtree')
def test_reattach_user_cancel_finalizes_as_canceled(mock_rmtree, mock_pdd, mock_release, mock_dedup, mock_finalize_job, mock_finalize_run):
    """A canceled stream that was not a detach finalizes the job as canceled, not failed."""
    job = Mock()
    job.id = 6
    job.work_unit_id = 'unit-cancel'
    job.spawned_by_workflow = False
    job.started = None
    job.execution_node = None
    job.job_env = {}
    ctl = Mock()
    ctl.simple_command.return_value = {'StateName': 'Running'}

    with patch('awx.main.tasks.receptor.AWXReceptorJob._process_phase', return_value=_Result(status='canceled', rc=1)):
        result = reattach_to_work_unit(job, ctl)

    assert result is True
    mock_finalize_job.assert_called_once()
    assert mock_finalize_job.call_args[1]['final_status'] == 'canceled'


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


def test_handle_work_error_detaches_when_unit_status_unreachable():
    """An unreachable receptor is not evidence that the job failed.

    The second half of the production shutdown: the results stream dies with the pod and
    ansible-runner reports 'error', but the control socket needed to check the unit is
    gone too. Recording the error would clear the running + work_unit_id pair the orphan
    scan matches on, failing a job whose EE is still working on another node.
    """
    rj = _make_receptor_job(cancel_flag=False)
    ctl = Mock()
    ctl.simple_command.side_effect = ConnectionResetError(104, 'Connection reset by peer')
    err_res = _Result(status='error', rc=1)

    result = rj._handle_work_error(ctl, err_res)

    assert result is err_res
    assert rj.detached is True
    rj.task.runner_callback.delay_update.assert_not_called()


def test_handle_work_error_does_not_detach_a_canceled_job():
    """A canceled job is meant to stop, so an unreadable status must not keep it alive."""
    rj = _make_receptor_job(cancel_flag=True)
    ctl = Mock()
    ctl.simple_command.side_effect = ConnectionResetError(104, 'Connection reset by peer')
    err_res = _Result(status='error', rc=1)

    result = rj._handle_work_error(ctl, err_res)

    assert result is err_res
    assert rj.detached is False


def test_handle_work_error_still_reports_a_reachable_units_failure():
    """The guard must only fire when the status is unknown — a real failure still reports."""
    rj = _make_receptor_job(cancel_flag=False)
    ctl = _make_receptor_ctl(state='Failed', detail='container image not found')
    err_res = _Result(status='error', rc=1)

    result = rj._handle_work_error(ctl, err_res)

    assert result is err_res
    assert rj.detached is False
    rj.task.runner_callback.delay_update.assert_called_once()


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
@patch('awx.main.tasks.receptor._compute_adoption_dedup', return_value=(0, set(), 0))
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
    job.execution_node = None
    job.job_env = {}
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
@patch('awx.main.tasks.receptor._compute_adoption_dedup', return_value=(0, set(), 0))
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
    job.execution_node = None
    job.job_env = {}
    ctl = Mock()
    ctl.simple_command.return_value = {'StateName': ''}
    mock_process.return_value = Mock(status='successful', rc=0)

    reattach_to_work_unit(job, ctl)

    mock_release.assert_called_once()


@patch('awx.main.tasks.jobs._finalize_job_run')
@patch('awx.main.tasks.receptor._compute_adoption_dedup', return_value=(0, set(), 0))
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
    job.execution_node = None
    job.job_env = {}
    _stub_last_event(job)
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
@patch('awx.main.tasks.receptor._compute_adoption_dedup', return_value=(0, set(), 0))
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
    job.execution_node = None
    job.job_env = {}
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
@patch('awx.main.tasks.receptor._compute_adoption_dedup', return_value=(0, set(), 0))
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
    job.execution_node = None
    job.job_env = {}
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

    cb.configure_for_job(instance, safe_env={'KEY': 'val'}, dedup_threshold=5, persisted_counters={6, 7})

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

    cb.configure_for_job(instance)

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

    cb.configure_for_job(instance)

    assert cb.parent_workflow_job_id == 42


def test_configure_runner_callback_swallows_workflow_lookup_error():
    from awx.main.tasks.callback import RunnerCallback

    cb = RunnerCallback(model=None)
    instance = Mock()
    instance.created = '2026-01-01'
    instance.spawned_by_workflow = True
    instance.get_workflow_job.side_effect = Exception('lookup failed')

    cb.configure_for_job(instance)  # must not raise
    assert cb.parent_workflow_job_id is None


# ---------------------------------------------------------------------------
# _build_adoption_callback — spawned_by_workflow False path
# ---------------------------------------------------------------------------


@patch('awx.main.tasks.jobs._finalize_job_run')
@patch('awx.main.tasks.receptor._compute_adoption_dedup', return_value=(0, set(), 0))
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
    job.execution_node = None
    job.job_env = {}
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
@patch('awx.main.tasks.receptor._finalize_adopted_job')
@patch('awx.main.tasks.receptor._compute_adoption_dedup', return_value=(0, set(), 0))
@patch('awx.main.tasks.receptor.AWXReceptorJob._process_phase', return_value=_Result(status='successful', rc=0))
@patch('awx.main.tasks.receptor.AWXReceptorJob._receptor_release_work')
@patch('awx.main.tasks.receptor._get_or_create_private_data_dir', return_value='/tmp/adopt')
@patch('awx.main.tasks.receptor.shutil.rmtree')
def test_reattach_running_streams_live(mock_rmtree, mock_pdd, mock_release, mock_process, mock_dedup, mock_finalize_job, mock_finalize_run):
    """A Running unit is streamed live, not held until the EE finishes.

    _process_phase reads the unit with get_work_results, which is exactly what a normal
    run does from the moment work is submitted — the unit is Pending or Running there too.
    Deferring a Running unit would hold every event back until the job ended.
    """
    job = Mock()
    job.id = 1
    job.work_unit_id = 'unit-running'
    job.created = '2026-01-01T00:00:00Z'
    job.spawned_by_workflow = False
    job.status = 'running'
    job.started = None
    job.execution_node = None
    job.job_env = {}
    ctl = Mock()
    ctl.simple_command.return_value = {'StateName': 'Running'}

    result = reattach_to_work_unit(job, ctl)

    mock_process.assert_called_once()
    mock_finalize_job.assert_called_once()
    assert result is True


@patch('awx.main.tasks.jobs._finalize_job_run')
@patch('awx.main.tasks.receptor._compute_adoption_dedup', return_value=(0, set(), 0))
@patch('awx.main.tasks.receptor.AWXReceptorJob._process_phase')
@patch('awx.main.tasks.receptor.AWXReceptorJob._receptor_release_work')
@patch('awx.main.tasks.receptor._get_or_create_private_data_dir', return_value='/tmp/adopt')
@patch('awx.main.tasks.receptor.shutil.rmtree')
def test_reattach_process_phase_failure_falls_back_to_work_status(mock_rmtree, mock_pdd, mock_release, mock_process, mock_dedup, mock_finalize):
    """When _process_phase raises and status is unknown, adoption is deferred.

    Finding #2 fix: require terminal state before finalizing. If we can't determine
    state (empty StateName or status query fails), defer adoption for retry instead
    of incorrectly marking healthy running units as failed.
    """
    job = Mock()
    job.id = 1
    job.work_unit_id = 'unit-recheck-err'
    job.created = '2026-01-01T00:00:00Z'
    job.spawned_by_workflow = False
    job.status = 'running'
    job.started = None
    job.execution_node = None
    job.job_env = {}
    ctl = Mock()
    # Initial check: Running (falls through to _process_phase); re-check after raise fails
    ctl.simple_command.side_effect = [
        {'StateName': ''},  # initial state check (unknown → _process_phase)
        RuntimeError('socket closed'),  # re-check also fails
    ]
    mock_process.side_effect = RuntimeError('process phase failed')

    result = reattach_to_work_unit(job, ctl)  # must not raise

    # Returns False (adoption deferred, state unknown)
    assert result is False


# ---------------------------------------------------------------------------
# reattach_to_work_unit — state guards (Pending / terminal / Running)
# ---------------------------------------------------------------------------


@patch('awx.main.tasks.jobs._finalize_job_run')
@patch('awx.main.tasks.receptor._finalize_adopted_job')
@patch('awx.main.tasks.receptor._compute_adoption_dedup', return_value=(0, set(), 0))
@patch('awx.main.tasks.receptor.AWXReceptorJob._receptor_release_work')
@patch('awx.main.tasks.receptor._get_or_create_private_data_dir', return_value='/tmp/adopt')
@patch('awx.main.tasks.receptor.shutil.rmtree')
def test_reattach_pending_streams_live(mock_rmtree, mock_pdd, mock_release, mock_dedup, mock_finalize_job, mock_finalize_run):
    """Pending is streamed too — get_work_results waits for the unit to produce output.

    A cross-controller adoption unit starts in Pending while the mesh connection comes up.
    That is the same state a freshly submitted unit is in when _run_internal calls
    _process_phase, so there is nothing to wait for here that the streamer cannot handle.
    """
    job = Mock()
    job.id = 42
    job.work_unit_id = 'unit-pending'
    job.spawned_by_workflow = False
    job.started = None
    job.execution_node = None
    job.job_env = {}
    ctl = Mock()
    ctl.simple_command.return_value = {'StateName': 'Pending'}

    with patch('awx.main.tasks.receptor.AWXReceptorJob._process_phase', return_value=_Result(status='successful', rc=0)) as mock_process:
        result = reattach_to_work_unit(job, ctl)

    assert result is True
    mock_process.assert_called_once()


@patch('awx.main.tasks.jobs._finalize_job_run')
@patch('awx.main.tasks.receptor._finalize_adopted_job')
@patch('awx.main.tasks.receptor._compute_adoption_dedup', return_value=(0, set(), 0))
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
    job.execution_node = None
    job.job_env = {}
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
@patch('awx.main.tasks.receptor._compute_adoption_dedup', return_value=(0, set(), 0))
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
    job.execution_node = None
    job.job_env = {}
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
@patch('awx.main.tasks.receptor._compute_adoption_dedup', return_value=(0, set(), 0))
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
    job.execution_node = None
    job.job_env = {}
    ctl = Mock()
    ctl.simple_command.return_value = {'StateName': 'Canceled', 'Detail': ''}

    with patch('awx.main.tasks.receptor.AWXReceptorJob._process_phase', return_value=Mock(status='error', rc=1)) as mock_process:
        reattach_to_work_unit(job, ctl)

    mock_process.assert_called_once()
    mock_finalize_job.assert_called_once()
    _, _, exit_code, _ = mock_finalize_job.call_args[0]
    assert exit_code == 1


# ---------------------------------------------------------------------------
# reattach_to_work_unit — cross-controller adoption (execution_node set)
# ---------------------------------------------------------------------------


@patch('awx.main.tasks.jobs._finalize_job_run')
@patch('awx.main.tasks.receptor._compute_adoption_dedup', return_value=(0, set(), 0))
@patch('awx.main.tasks.receptor.AWXReceptorJob._process_phase')
@patch('awx.main.tasks.receptor.AWXReceptorJob._receptor_release_work')
@patch('awx.main.tasks.receptor._get_or_create_private_data_dir', return_value='/tmp/adopt')
@patch('awx.main.tasks.receptor.adopt_remote_work')
@patch('awx.main.tasks.receptor.shutil.rmtree')
def test_reattach_cross_controller_adoption_calls_adopt_remote_work(
    mock_rmtree, mock_adopt_remote, mock_pdd, mock_release, mock_process, mock_dedup, mock_finalize
):
    """When the local receptor does not know the unit, reattach_to_work_unit adopts from the execution node."""
    job = Mock()
    job.id = 1
    job.work_unit_id = 'unit-1'
    job.spawned_by_workflow = False
    job.status = 'successful'
    job.execution_node = 'remote-ee'  # Cross-controller adoption
    job.job_env = {}
    ctl = Mock()
    ctl.simple_command.side_effect = RuntimeError('unknown work unit unit-1')
    mock_adopt_remote.return_value = {'StateName': 'Succeeded', 'ExitCode': 0, 'Detail': ''}
    mock_process.return_value = Mock(status='successful', rc=0)

    reattach_to_work_unit(job, ctl)

    mock_adopt_remote.assert_called_once_with(ctl, 'remote-ee', 'unit-1')


@patch('awx.main.tasks.jobs._finalize_job_run')
@patch('awx.main.tasks.receptor._compute_adoption_dedup', return_value=(0, set(), 0))
@patch('awx.main.tasks.receptor.AWXReceptorJob._receptor_release_work')
@patch('awx.main.tasks.receptor._get_or_create_private_data_dir', return_value='/tmp/adopt')
@patch('awx.main.tasks.receptor.adopt_remote_work')
@patch('awx.main.tasks.receptor.shutil.rmtree')
def test_reattach_cross_controller_defers_when_adopt_remote_work_raises(mock_rmtree, mock_adopt_remote, mock_pdd, mock_release, mock_dedup, mock_finalize):
    """When neither the local receptor nor the execution node can be queried, reattach defers."""
    job = Mock()
    job.id = 1
    job.work_unit_id = 'unit-1'
    job.execution_node = 'remote-ee'
    ctl = Mock()
    ctl.simple_command.side_effect = RuntimeError('unknown work unit unit-1')
    mock_adopt_remote.side_effect = RuntimeError('EE unreachable')

    result = reattach_to_work_unit(job, ctl)

    assert result is False  # Adoption deferred


# ---------------------------------------------------------------------------
# get_adoption_unit_status — local receptor first, remote adopt as fallback
# ---------------------------------------------------------------------------


@patch('awx.main.tasks.receptor.adopt_remote_work')
def test_adoption_unit_status_prefers_local_receptor(mock_adopt_remote):
    """A same-controller restart with a remote EE reads real state from the local receptor."""
    from awx.main.tasks.receptor import get_adoption_unit_status

    job = Mock(id=1, work_unit_id='unit-1', execution_node='remote-ee')
    ctl = Mock()
    ctl.simple_command.return_value = {'StateName': 'Running'}

    status = get_adoption_unit_status(ctl, job)

    assert status['StateName'] == 'Running'
    ctl.simple_command.assert_called_once_with('work status unit-1')
    mock_adopt_remote.assert_not_called()


@patch('awx.main.tasks.receptor.adopt_remote_work')
def test_adoption_unit_status_falls_back_to_remote_adopt(mock_adopt_remote):
    """Unknown to the local receptor → adopt the unit from the execution node."""
    from awx.main.tasks.receptor import get_adoption_unit_status

    job = Mock(id=1, work_unit_id='unit-1', execution_node='remote-ee')
    ctl = Mock()
    ctl.simple_command.side_effect = RuntimeError('unknown work unit unit-1')
    mock_adopt_remote.return_value = {'unitid': 'unit-1', 'result': 'Adopted'}

    status = get_adoption_unit_status(ctl, job)

    assert status['result'] == 'Adopted'
    mock_adopt_remote.assert_called_once_with(ctl, 'remote-ee', 'unit-1')


@patch('awx.main.tasks.receptor.adopt_remote_work')
def test_adoption_unit_status_reraises_without_remote_node(mock_adopt_remote):
    """No execution node to fall back to → the local failure propagates, marking the unit unreachable."""
    from awx.main.tasks.receptor import get_adoption_unit_status

    job = Mock(id=1, work_unit_id='unit-1', execution_node=None)
    ctl = Mock()
    ctl.simple_command.side_effect = RuntimeError('unknown work unit unit-1')

    with pytest.raises(RuntimeError):
        get_adoption_unit_status(ctl, job)

    mock_adopt_remote.assert_not_called()


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


@override_settings(CLUSTER_HOST_ID='surviving-controller')
@patch('awx.main.tasks.jobs._finalize_job_run')
def test_finalize_adopted_job_successful(mock_finalize):
    """exit_code=0 → _finalize_job_run called with status='successful' and finished in extra_fields."""
    job = Mock()
    job.status = 'running'
    job.started = None
    job.execution_node = None
    _stub_last_event(job)
    callback = Mock(wrapup_event_created=None)

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


@override_settings(CLUSTER_HOST_ID='surviving-controller')
@patch('awx.main.tasks.jobs._finalize_job_run')
def test_finalize_adopted_job_failed(mock_finalize):
    """exit_code=1 → _finalize_job_run called with status='failed'."""
    job = Mock()
    job.status = 'running'
    job.started = None
    job.execution_node = None
    _stub_last_event(job)
    callback = Mock(wrapup_event_created=None)

    _finalize_adopted_job(job, callback, exit_code=1, process_phase_failed=False)

    _, _, _, status = mock_finalize.call_args[0][:4]
    assert status == 'failed'


@override_settings(CLUSTER_HOST_ID='surviving-controller')
@patch('awx.main.tasks.jobs._finalize_job_run')
def test_finalize_adopted_job_includes_elapsed_when_started(mock_finalize):
    """elapsed is passed in extra_fields when job.started is set."""
    from datetime import datetime, timezone

    job = Mock()
    job.status = 'running'
    job.started = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    job.execution_node = None
    # The playbook ended 30 s in; the adoption that notices it happens much later.
    _stub_last_event(job, job.started + timedelta(seconds=30))
    callback = Mock()

    _finalize_adopted_job(job, callback, exit_code=0, process_phase_failed=False)

    extra_fields = mock_finalize.call_args[1].get('extra_fields') or mock_finalize.call_args[0][4]
    assert extra_fields['elapsed'] == 30.0
    assert extra_fields['finished'] == job.started + timedelta(seconds=30)


@patch('awx.main.tasks.jobs._finalize_job_run')
def test_finalize_adopted_job_process_phase_failed_label(mock_finalize):
    """process_phase_failed=True still calls _finalize_job_run — just changes the log label."""
    job = Mock()
    job.status = 'running'
    job.started = None
    _stub_last_event(job)
    callback = Mock(wrapup_event_created=None)

    _finalize_adopted_job(job, callback, exit_code=1, process_phase_failed=True)

    mock_finalize.assert_called_once()


@override_settings(CLUSTER_HOST_ID='surviving-ctrl-9')
@patch('awx.main.tasks.jobs._finalize_job_run')
def test_finalize_adopted_job_records_metadata_when_process_phase_failed(mock_finalize):
    """Adoption metadata is recorded even when the process phase raised.

    Both branches of this function are adoptions, and knowing which controller took the job
    over matters most when the adoption itself blew up.
    """
    job = Mock()
    job.id = 7
    job.work_unit_id = 'unit-boom'
    job.execution_node = 'remote-ee-9'
    job.status = 'running'
    job.started = None
    _stub_last_event(job)
    callback = Mock(wrapup_event_created=None)

    _finalize_adopted_job(job, callback, exit_code=1, process_phase_failed=True)

    mock_finalize.assert_called_once()
    callback.delay_update.assert_called_once()
    explanation = callback.delay_update.call_args[1]['job_explanation']
    assert 'surviving-ctrl-9' in explanation
    assert 'unit-boom' in explanation


@override_settings(CLUSTER_HOST_ID='surviving-ctrl-1')
@patch('awx.main.tasks.jobs._finalize_job_run')
def test_finalize_adopted_job_stores_adoption_metadata(mock_finalize):
    """job_explanation is set with surviving controller, unit ID, and execution node."""
    job = Mock()
    job.id = 42
    job.work_unit_id = 'unit-xyz'
    job.execution_node = 'remote-ee-1'
    job.status = 'running'
    job.started = None
    _stub_last_event(job)
    callback = Mock(wrapup_event_created=None)

    _finalize_adopted_job(job, callback, exit_code=0, process_phase_failed=False)

    mock_finalize.assert_called_once()
    # Goes through delay_update, not extra_fields — _finalize_job_run lets extra_fields
    # overwrite delayed fields, which would drop any explanation the runner recorded.
    callback.delay_update.assert_called_once()
    explanation = callback.delay_update.call_args[1]['job_explanation']
    assert 'surviving-ctrl-1' in explanation
    assert 'unit-xyz' in explanation
    assert 'remote-ee-1' in explanation
    extra_fields = mock_finalize.call_args[1].get('extra_fields') or mock_finalize.call_args[0][4]
    assert 'job_explanation' not in extra_fields


@override_settings(CLUSTER_HOST_ID='surviving-ctrl-1')
@patch('awx.main.tasks.jobs._finalize_job_run')
def test_finalize_adopted_job_preserves_runner_job_explanation(mock_finalize):
    """Adoption metadata appends to an explanation the runner already recorded, it does not replace it."""
    from awx.main.tasks.callback import RunnerCallback

    job = Mock()
    job.id = 42
    job.work_unit_id = 'unit-xyz'
    job.execution_node = 'remote-ee-1'
    job.status = 'running'
    job.started = None
    _stub_last_event(job)

    callback = RunnerCallback(model=None)
    # status_handler records the real failure cause during _process_phase
    callback.status_handler({'status': 'error', 'job_explanation': 'Job terminated due to error'}, None)

    _finalize_adopted_job(job, callback, exit_code=1, process_phase_failed=False)

    explanation = callback.get_delayed_update_fields()['job_explanation']
    assert 'Job terminated due to error' in explanation
    assert 'surviving-ctrl-1' in explanation


# ---------------------------------------------------------------------------
# _adopted_finished_at — recovering the real end time of an adopted job
# ---------------------------------------------------------------------------


def test_adopted_finished_at_uses_the_wrapup_event_the_callback_saw():
    """The playbook's own wrapup event, not the moment we got around to noticing it."""
    started = now() - timedelta(seconds=300)
    ended = started + timedelta(seconds=27)
    job = _stub_last_event(Mock(started=started), None)

    finished_at, lag = _adopted_finished_at(job, Mock(wrapup_event_created=ended))

    assert finished_at == ended
    # ~273 s sat between the playbook ending and this controller committing the status.
    assert 270 < lag < 280


def test_adopted_finished_at_parses_a_string_wrapup_timestamp():
    """Runner hands the timestamp over as an ISO string, not a datetime."""
    started = now() - timedelta(seconds=300)
    ended = (started + timedelta(seconds=27)).replace(microsecond=0)
    job = _stub_last_event(Mock(started=started), None)

    finished_at, _ = _adopted_finished_at(job, Mock(wrapup_event_created=ended.isoformat()))

    assert finished_at == ended


def test_adopted_finished_at_assumes_utc_for_a_naive_wrapup_timestamp():
    """A payload without an offset must not blow up on a naive/aware comparison."""
    started = now() - timedelta(seconds=300)
    ended = (started + timedelta(seconds=27)).replace(microsecond=0)
    job = _stub_last_event(Mock(started=started), None)

    finished_at, _ = _adopted_finished_at(job, Mock(wrapup_event_created=ended.replace(tzinfo=None).isoformat()))

    assert finished_at == ended


def test_adopted_finished_at_beats_the_database_which_lags_ingestion():
    """The callback wins over the queryset — that is the whole point of plumbing it through.

    Event dispatch is asynchronous, so at finalization time the database holds only a prefix
    of the adopted job's events. Trusting it back-dates `finished` into the middle of the run.
    """
    started = now() - timedelta(seconds=300)
    really_ended = started + timedelta(seconds=240)
    job = _stub_last_event(Mock(started=started), started + timedelta(seconds=46))  # all that landed so far

    finished_at, _ = _adopted_finished_at(job, Mock(wrapup_event_created=really_ended))

    assert finished_at == really_ended


def test_adopted_finished_at_discards_an_unparseable_wrapup_timestamp():
    """A malformed runner payload degrades the measurement; it must not abort finalization."""
    started = now() - timedelta(seconds=300)
    last = started + timedelta(seconds=27)
    job = _stub_last_event(Mock(started=started), last)

    finished_at, _ = _adopted_finished_at(job, Mock(wrapup_event_created='not a timestamp'))

    assert finished_at == last


def test_adopted_finished_at_falls_back_to_the_database_without_a_callback_event():
    """On a re-adoption this process never sees a wrapup event, but the old ones are persisted."""
    started = now() - timedelta(seconds=300)
    last = started + timedelta(seconds=27)
    job = _stub_last_event(Mock(started=started), last)

    finished_at, _ = _adopted_finished_at(job, Mock(wrapup_event_created=None))

    assert finished_at == last


def test_adopted_finished_at_falls_back_to_now_without_events():
    """No events means no second clock to read — and for a wedged pod the gap is real work time."""
    before = now()
    job = _stub_last_event(Mock(started=before - timedelta(seconds=10)), None)

    finished_at, lag = _adopted_finished_at(job)

    assert before <= finished_at <= now()
    assert lag == 0.0


def test_adopted_finished_at_never_precedes_started():
    """Clock skew on a mesh execution node must not produce a negative elapsed."""
    started = now() - timedelta(seconds=60)
    job = _stub_last_event(Mock(started=started), started - timedelta(seconds=90))

    finished_at, _ = _adopted_finished_at(job)

    assert finished_at == started


def test_adopted_finished_at_never_lands_in_the_future():
    """An execution node running ahead of us must not stamp a finished time we have not reached."""
    started = now() - timedelta(seconds=60)
    job = _stub_last_event(Mock(started=started), now() + timedelta(seconds=600))

    finished_at, lag = _adopted_finished_at(job)

    assert finished_at <= now()
    assert lag >= 0.0


def test_adopted_finished_at_tolerates_a_job_that_never_started():
    """`started` is nullable on the model; the clamp has to survive it."""
    last = now() - timedelta(seconds=45)
    job = _stub_last_event(Mock(started=None), last)

    finished_at, lag = _adopted_finished_at(job)

    assert finished_at == last
    assert 40 < lag < 50


# ---------------------------------------------------------------------------
# status_handler 'starting' — job_env must never be persisted unmasked
# ---------------------------------------------------------------------------


def test_status_handler_masks_env_when_safe_env_is_empty():
    """A replayed 'starting' status must not write raw credentials into job_env.

    Adoption seeds safe_env from job.job_env, which is empty when the original controller
    died after submitting the work unit but before the EE's 'starting' status was persisted.
    The replayed status then carries the EE's real environment, so masking cannot depend on
    safe_env being populated.
    """
    from awx.main.tasks.callback import RunnerCallback

    callback = RunnerCallback(model=None)
    callback.safe_env = {}  # adoption seeded this from an empty job.job_env
    callback.instance = Mock(pk=7)
    callback.update_model = Mock(return_value=callback.instance)

    runner_config = Mock(env={'MY_VAULT_PASSWORD': 'hunter2', 'PATH': '/usr/bin'}, command=['ansible-playbook'], cwd='/tmp')
    callback.status_handler({'status': 'starting'}, runner_config)

    persisted_env = callback.update_model.call_args.kwargs['job_env']
    assert persisted_env['MY_VAULT_PASSWORD'] != 'hunter2'
    assert persisted_env['PATH'] == '/usr/bin'


def test_status_handler_safe_env_still_overrides_pattern_masking():
    """Caller-supplied safe_env wins over regex masking — it covers credential-plugin values."""
    from awx.main.tasks.callback import RunnerCallback

    callback = RunnerCallback(model=None)
    # MY_TOKEN would be regex-masked anyway; CUSTOM_VALUE only safe_env knows about.
    callback.safe_env = {'CUSTOM_VALUE': '$encrypted$'}
    callback.instance = Mock(pk=8)
    callback.update_model = Mock(return_value=callback.instance)

    runner_config = Mock(env={'CUSTOM_VALUE': 'secret-from-plugin', 'MY_TOKEN': 'abc'}, command=[], cwd='/tmp')
    callback.status_handler({'status': 'starting'}, runner_config)

    persisted_env = callback.update_model.call_args.kwargs['job_env']
    assert persisted_env['CUSTOM_VALUE'] == '$encrypted$'
    assert persisted_env['MY_TOKEN'] != 'abc'


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
    assert payload['signwork'] == 'true'


@patch('awx.main.tasks.receptor.get_tls_client', return_value=None)
@patch('awx.main.tasks.receptor.work_signing_enabled', return_value=True)
def test_adopt_remote_work_json_fallback_signwork_is_a_string_not_a_bool(mock_sign, mock_tls):
    """signwork must be the *string* "true", never a JSON boolean.

    receptor's boolFromMap() asserts value.(string) and accepts only "true"/"false".
    A JSON bool fails that assertion, and the adopt handler discards the error and
    defaults to signWork=false. The adopted unit then sends `work results` unsigned,
    the remote rejects it, and remote_work.go loops forever on "did not stream
    results" — the stream delivers 0 bytes. receptorctl's own submit_work() sends
    the string, which is why only adoptions were affected.
    """
    ctl = Mock(spec=['connect', 'writestr', 'read_and_parse_json'])  # no adopt_work
    ctl.read_and_parse_json.return_value = {}

    adopt_remote_work(ctl, node='ee-node', unit_id='u4', config_data={})

    raw = ctl.writestr.call_args[0][0]
    assert '"signwork": true' not in raw
    assert isinstance(json.loads(raw.rstrip())['signwork'], str)


# ---------------------------------------------------------------------------
# reattach_to_work_unit — pre-cached unit_status parameter
# ---------------------------------------------------------------------------


@patch('awx.main.tasks.receptor.shutil.rmtree')
@patch('awx.main.tasks.receptor._get_or_create_private_data_dir', return_value='/tmp/adopt')
@patch('awx.main.tasks.receptor.AWXReceptorJob._receptor_release_work')
@patch('awx.main.tasks.receptor._compute_adoption_dedup', return_value=(0, set(), 0))
@patch('awx.main.tasks.receptor._finalize_adopted_job')
def test_reattach_uses_precached_unit_status(mock_finalize, mock_dedup, mock_release, mock_pdd, mock_rmtree):
    """Verify reattach_to_work_unit uses provided unit_status instead of refetching."""
    job = Mock()
    job.id = 1
    job.work_unit_id = 'unit-cached'
    job.spawned_by_workflow = False
    job.started = None
    job.execution_node = None
    job.job_env = {}
    ctl = Mock()
    ctl.simple_command.return_value = {'StateName': 'Failed'}  # Should NOT be called for status fetch

    # Pre-cached status from adopt_job_async
    precached_status = {'StateName': 'Succeeded', 'ExitCode': 0}

    with patch('awx.main.tasks.receptor.AWXReceptorJob._process_phase', return_value=Mock(status='successful')):
        reattach_to_work_unit(job, ctl, unit_status=precached_status)

    # Verify simple_command was NOT called (status was provided)
    ctl.simple_command.assert_not_called()


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
# _finalize_job_run — extra_fields merges into update fields
# ---------------------------------------------------------------------------


@patch('awx.main.tasks.jobs.ScheduleWorkflowManager')
@patch('awx.main.tasks.jobs.ScheduleTaskManager')
@patch('awx.main.tasks.jobs.update_model')
def test_finalize_job_run_extra_fields_merged(mock_update, mock_task_mgr, mock_workflow_mgr):
    """extra_fields dict is merged into the update kwargs alongside runner fields."""
    instance = Mock()
    instance.host_status_counts = None
    instance.unifiedjob_blocked_jobs.exists.return_value = False
    instance.spawned_by_workflow = False
    instance.inventory_id = None
    mock_update.return_value = instance

    cb = Mock()
    cb.get_delayed_update_fields.return_value = {'emitted_events': 3}
    cb.wrapup_event_dispatched = True

    _finalize_job_run(Mock, pk=1, runner_callback=cb, status='successful', extra_fields={'finished': 'NOW', 'elapsed': 1.5})

    _, kwargs = mock_update.call_args
    assert kwargs['finished'] == 'NOW'
    assert kwargs['elapsed'] == 1.5
    assert kwargs['emitted_events'] == 3


@patch('awx.main.tasks.jobs.update_model')
def test_finalize_job_run_instance_deleted(mock_update):
    """When update_model returns None (instance deleted), returns None early."""
    cb = Mock()
    cb.get_delayed_update_fields.return_value = {}
    mock_update.return_value = None

    result = _finalize_job_run(Mock, pk=1, runner_callback=cb, status='successful')

    assert result is None


@patch('awx.main.tasks.jobs.update_inventory_computed_fields')
@patch('awx.main.tasks.jobs.ScheduleWorkflowManager')
@patch('awx.main.tasks.jobs.ScheduleTaskManager')
@patch('awx.main.tasks.jobs.events_processed_hook')
@patch('awx.main.tasks.jobs.update_model')
def test_finalize_job_run_with_blocked_jobs(mock_update, mock_hook, mock_task_mgr, mock_wf_mgr, mock_inv_update):
    """ScheduleTaskManager is called when unifiedjob_blocked_jobs.exists()."""
    instance = Mock()
    instance.host_status_counts = None
    instance.unifiedjob_blocked_jobs.exists.return_value = True
    instance.spawned_by_workflow = False
    instance.inventory_id = None
    mock_update.return_value = instance

    cb = Mock()
    cb.get_delayed_update_fields.return_value = {}
    cb.wrapup_event_dispatched = True

    _finalize_job_run(Mock, pk=1, runner_callback=cb, status='successful')

    mock_task_mgr.return_value.schedule.assert_called_once()
    mock_wf_mgr.return_value.schedule.assert_not_called()


@patch('awx.main.tasks.jobs.update_inventory_computed_fields')
@patch('awx.main.tasks.jobs.ScheduleWorkflowManager')
@patch('awx.main.tasks.jobs.ScheduleTaskManager')
@patch('awx.main.tasks.jobs.events_processed_hook')
@patch('awx.main.tasks.jobs.update_model')
def test_finalize_job_run_with_workflow(mock_update, mock_hook, mock_task_mgr, mock_wf_mgr, mock_inv_update):
    """ScheduleWorkflowManager is called when spawned_by_workflow is True."""
    instance = Mock()
    instance.host_status_counts = None
    instance.unifiedjob_blocked_jobs.exists.return_value = False
    instance.spawned_by_workflow = True
    instance.inventory_id = None
    mock_update.return_value = instance

    cb = Mock()
    cb.get_delayed_update_fields.return_value = {}
    cb.wrapup_event_dispatched = True

    _finalize_job_run(Mock, pk=1, runner_callback=cb, status='successful')

    mock_wf_mgr.return_value.schedule.assert_called_once()
    mock_task_mgr.return_value.schedule.assert_not_called()


@patch('awx.main.tasks.jobs.update_inventory_computed_fields')
@patch('awx.main.tasks.jobs.ScheduleWorkflowManager')
@patch('awx.main.tasks.jobs.ScheduleTaskManager')
@patch('awx.main.tasks.jobs.events_processed_hook')
@patch('awx.main.tasks.jobs.update_model')
def test_finalize_job_run_with_inventory(mock_update, mock_hook, mock_task_mgr, mock_wf_mgr, mock_inv_update):
    """update_inventory_computed_fields.delay is called when inventory_id is set."""
    instance = Mock()
    instance.host_status_counts = None
    instance.unifiedjob_blocked_jobs.exists.return_value = False
    instance.spawned_by_workflow = False
    instance.inventory_id = 42
    mock_update.return_value = instance

    cb = Mock()
    cb.get_delayed_update_fields.return_value = {}
    cb.wrapup_event_dispatched = True

    _finalize_job_run(Mock, pk=1, runner_callback=cb, status='successful')

    mock_inv_update.delay.assert_called_once_with(42)


@patch('awx.main.tasks.jobs.update_inventory_computed_fields')
@patch('awx.main.tasks.jobs.ScheduleWorkflowManager')
@patch('awx.main.tasks.jobs.ScheduleTaskManager')
@patch('awx.main.tasks.jobs.events_processed_hook')
@patch('awx.main.tasks.jobs.update_model')
def test_finalize_job_run_inventory_delay_exception(mock_update, mock_hook, mock_task_mgr, mock_wf_mgr, mock_inv_update, caplog):
    """Exception in inventory delay is logged and finalization continues."""
    instance = Mock()
    instance.host_status_counts = None
    instance.unifiedjob_blocked_jobs.exists.return_value = False
    instance.spawned_by_workflow = False
    instance.inventory_id = 42
    instance.log_format = 'job 1'
    mock_update.return_value = instance
    mock_inv_update.delay.side_effect = RuntimeError('celery error')

    cb = Mock()
    cb.get_delayed_update_fields.return_value = {}
    cb.wrapup_event_dispatched = True

    result = _finalize_job_run(Mock, pk=1, runner_callback=cb, status='successful')

    assert result is instance
    assert 'Error scheduling inventory computed fields update' in caplog.text


@patch('awx.main.tasks.jobs.update_inventory_computed_fields')
@patch('awx.main.tasks.jobs.ScheduleWorkflowManager')
@patch('awx.main.tasks.jobs.ScheduleTaskManager')
@patch('awx.main.tasks.jobs.events_processed_hook')
@patch('awx.main.tasks.jobs.update_model')
def test_finalize_job_run_calls_hook_on_host_counts(mock_update, mock_hook, mock_task_mgr, mock_wf_mgr, mock_inv_update):
    """events_processed_hook is called when host_status_counts is not None."""
    instance = Mock()
    instance.host_status_counts = {'ok': 1, 'failed': 0}
    instance.unifiedjob_blocked_jobs.exists.return_value = False
    instance.spawned_by_workflow = False
    instance.inventory_id = None
    mock_update.return_value = instance

    cb = Mock()
    cb.get_delayed_update_fields.return_value = {}
    cb.wrapup_event_dispatched = True

    _finalize_job_run(Mock, pk=1, runner_callback=cb, status='successful')

    mock_hook.assert_called_once_with(instance)


@patch('awx.main.tasks.jobs.update_inventory_computed_fields')
@patch('awx.main.tasks.jobs.ScheduleWorkflowManager')
@patch('awx.main.tasks.jobs.ScheduleTaskManager')
@patch('awx.main.tasks.jobs.events_processed_hook')
@patch('awx.main.tasks.jobs.update_model')
def test_finalize_job_run_calls_hook_on_wrapup_not_dispatched(mock_update, mock_hook, mock_task_mgr, mock_wf_mgr, mock_inv_update):
    """events_processed_hook is called when wrapup_event_dispatched is False."""
    instance = Mock()
    instance.host_status_counts = None
    instance.unifiedjob_blocked_jobs.exists.return_value = False
    instance.spawned_by_workflow = False
    instance.inventory_id = None
    mock_update.return_value = instance

    cb = Mock()
    cb.get_delayed_update_fields.return_value = {}
    cb.wrapup_event_dispatched = False

    _finalize_job_run(Mock, pk=1, runner_callback=cb, status='successful')

    mock_hook.assert_called_once_with(instance)


@patch('awx.main.tasks.jobs.update_inventory_computed_fields')
@patch('awx.main.tasks.jobs.ScheduleWorkflowManager')
@patch('awx.main.tasks.jobs.ScheduleTaskManager')
@patch('awx.main.tasks.jobs.events_processed_hook')
@patch('awx.main.tasks.jobs.update_model')
def test_finalize_job_run_skips_hook_when_no_counts_and_wrapup(mock_update, mock_hook, mock_task_mgr, mock_wf_mgr, mock_inv_update):
    """events_processed_hook is NOT called when counts=None AND wrapup_dispatched=True."""
    instance = Mock()
    instance.host_status_counts = None
    instance.unifiedjob_blocked_jobs.exists.return_value = False
    instance.spawned_by_workflow = False
    instance.inventory_id = None
    mock_update.return_value = instance

    cb = Mock()
    cb.get_delayed_update_fields.return_value = {}
    cb.wrapup_event_dispatched = True

    _finalize_job_run(Mock, pk=1, runner_callback=cb, status='successful')

    mock_hook.assert_not_called()


@patch('awx.main.tasks.jobs.update_inventory_computed_fields')
@patch('awx.main.tasks.jobs.ScheduleWorkflowManager')
@patch('awx.main.tasks.jobs.ScheduleTaskManager')
@patch('awx.main.tasks.jobs.events_processed_hook')
@patch('awx.main.tasks.jobs.update_model')
def test_finalize_job_run_calls_websocket_emit(mock_update, mock_hook, mock_task_mgr, mock_wf_mgr, mock_inv_update):
    """websocket_emit_status is called with the status."""
    instance = Mock()
    instance.host_status_counts = None
    instance.unifiedjob_blocked_jobs.exists.return_value = False
    instance.spawned_by_workflow = False
    instance.inventory_id = None
    mock_update.return_value = instance

    cb = Mock()
    cb.get_delayed_update_fields.return_value = {}
    cb.wrapup_event_dispatched = True

    _finalize_job_run(Mock, pk=1, runner_callback=cb, status='failed')

    instance.websocket_emit_status.assert_called_once_with('failed')


@patch('awx.main.tasks.jobs.update_inventory_computed_fields')
@patch('awx.main.tasks.jobs.ScheduleWorkflowManager')
@patch('awx.main.tasks.jobs.ScheduleTaskManager')
@patch('awx.main.tasks.jobs.events_processed_hook')
@patch('awx.main.tasks.jobs.update_model')
def test_finalize_job_run_logs_lifecycle(mock_update, mock_hook, mock_task_mgr, mock_wf_mgr, mock_inv_update):
    """log_lifecycle('finalize_run') is called."""
    instance = Mock()
    instance.host_status_counts = None
    instance.unifiedjob_blocked_jobs.exists.return_value = False
    instance.spawned_by_workflow = False
    instance.inventory_id = None
    mock_update.return_value = instance

    cb = Mock()
    cb.get_delayed_update_fields.return_value = {}
    cb.wrapup_event_dispatched = True

    _finalize_job_run(Mock, pk=1, runner_callback=cb, status='successful')

    instance.log_lifecycle.assert_called_once_with('finalize_run')


# ---------------------------------------------------------------------------
# populate_host_map — shared by the normal path and adoption
# ---------------------------------------------------------------------------


def test_populate_host_map_from_inventory_populates_host_map():
    """The adoption path sources host_map by fetching script_data itself."""
    cb = RunnerCallback(model=None)
    instance = Mock()
    instance.inventory_id = 42
    instance.inventory.get_script_data.return_value = {
        '_meta': {
            'hostvars': {
                'host1': {'remote_tower_id': 'ext-1'},
                'host2': {'remote_tower_id': 'ext-2'},
            }
        }
    }

    cb.populate_host_map_from_inventory(instance)

    assert cb.host_map == {'host1': 'ext-1', 'host2': 'ext-2'}


def test_populate_host_map_from_inventory_swallows_error():
    """If fetching inventory hosts raises, the exception is swallowed and host_map stays {}."""
    cb = RunnerCallback(model=None)
    instance = Mock()
    instance.inventory_id = 1
    instance.inventory.get_script_data.side_effect = Exception('DB error')

    cb.populate_host_map_from_inventory(instance)  # must not raise

    assert cb.host_map == {}


def test_populate_host_map_from_inventory_skips_job_without_inventory():
    """No inventory means no query — an inventory-less job must not hit get_script_data."""
    cb = RunnerCallback(model=None)
    instance = Mock()
    instance.inventory_id = None

    cb.populate_host_map_from_inventory(instance)

    assert cb.host_map == {}
    instance.inventory.get_script_data.assert_not_called()


def test_configure_for_job_does_not_touch_inventory():
    """host_map is populated by the call sites, so configure_for_job issues no inventory query."""
    cb = RunnerCallback(model=None)
    instance = Mock()
    instance.created = '2026-01-01'
    instance.spawned_by_workflow = False
    instance.inventory_id = 42

    cb.configure_for_job(instance, dedup_threshold=0)

    assert cb.host_map == {}
    instance.inventory.get_script_data.assert_not_called()


def test_inventory_script_params_matches_build_inventory():
    """Adoption must ask for the same script_data shape build_inventory writes, slicing included."""
    sliced = Mock(job_slice_number=2, job_slice_count=5)
    assert RunnerCallback.inventory_script_params(sliced) == {
        'hostvars': True,
        'towervars': True,
        'slice_number': 2,
        'slice_count': 5,
    }

    unsliced = Mock(spec=[])  # no job_slice_number attribute
    assert RunnerCallback.inventory_script_params(unsliced) == {'hostvars': True, 'towervars': True}


# ---------------------------------------------------------------------------
# _handle_work_error — edge cases and error paths
# ---------------------------------------------------------------------------


@patch('awx.main.tasks.receptor.logger')
def test_handle_work_error_no_output_no_detail(mock_logger):
    """When there's no receptor output and no detail, warning is logged."""
    res = namedtuple('result', ['status', 'rc'])('error', 1)
    receptor_ctl = Mock()
    receptor_ctl.simple_command.return_value = {
        'StateName': 'Succeeded',  # Not 'Failed', so no attempt to fetch work results
        'Detail': '',  # Empty detail
        'StdoutSize': 0,
    }

    receptor_job = AWXReceptorJob.__new__(AWXReceptorJob)
    receptor_job.unit_id = 'test-unit'
    receptor_job.task = Mock()
    receptor_job.task.instance = Mock()
    receptor_job.task.instance.log_format = 'job 1'
    receptor_job.task.runner_callback = Mock()
    receptor_job.task.runner_callback.extra_update_fields = {}
    receptor_job.task.runner_callback.event_ct = 0  # No events

    result = receptor_job._handle_work_error(receptor_ctl, res)

    assert result == res
    mock_logger.warning.assert_called()
    # Verify warning was logged for "No result details or output"
    assert any('No result details' in str(call) for call in mock_logger.warning.call_args_list)


@patch('awx.main.tasks.receptor.logger')
def test_handle_work_error_state_name_empty_string(mock_logger):
    """When state_name can't be determined, error path handles empty string gracefully."""
    res = namedtuple('result', ['status', 'rc'])('error', 1)
    receptor_ctl = Mock()
    # Simulate status command failure
    receptor_ctl.simple_command.side_effect = Exception('connection lost')

    receptor_job = AWXReceptorJob.__new__(AWXReceptorJob)
    receptor_job.unit_id = 'test-unit'
    receptor_job.task = Mock()
    receptor_job.task.instance = Mock()
    receptor_job.task.instance.log_format = 'job 1'
    receptor_job.task.runner_callback = Mock()
    receptor_job.task.runner_callback.extra_update_fields = {}
    receptor_job.task.runner_callback.event_ct = 5

    result = receptor_job._handle_work_error(receptor_ctl, res)

    assert result == res
    # Verify exception was logged
    mock_logger.exception.assert_called()


def test_handle_work_error_delay_update_with_receptor_output():
    """When receptor_output is collected, it's passed to delay_update."""
    res = namedtuple('result', ['status', 'rc'])('error', 1)
    receptor_ctl = Mock()
    resultfile = Mock()
    resultfile.readlines.return_value = [b'Error: connection refused\n']
    resultfile.close = Mock()
    resultsock = Mock()

    receptor_ctl.simple_command.return_value = {
        'StateName': 'Failed',
        'Detail': '',
        'StdoutSize': 500,
    }
    receptor_ctl.get_work_results.return_value = (resultsock, resultfile)

    receptor_job = AWXReceptorJob.__new__(AWXReceptorJob)
    receptor_job.unit_id = 'test-unit'
    receptor_job.task = Mock()
    receptor_job.task.instance = Mock()
    receptor_job.task.instance.log_format = 'job 1'
    receptor_job.task.runner_callback = Mock()
    receptor_job.task.runner_callback.extra_update_fields = {}
    receptor_job.task.runner_callback.event_ct = 0  # No events → fetch output

    result = receptor_job._handle_work_error(receptor_ctl, res)

    assert result == res
    # Verify delay_update was called with receptor output
    receptor_job.task.runner_callback.delay_update.assert_called_once()
    call_kwargs = receptor_job.task.runner_callback.delay_update.call_args[1]
    assert 'Worker output' in call_kwargs['result_traceback']
    assert 'connection refused' in call_kwargs['result_traceback']


def test_handle_work_error_delay_update_with_detail_fallback():
    """When there's no receptor output but detail is present, detail is used."""
    res = namedtuple('result', ['status', 'rc'])('error', 1)
    receptor_ctl = Mock()
    receptor_ctl.simple_command.return_value = {
        'StateName': 'Succeeded',  # Not 'Failed', so no attempt to fetch output
        'Detail': 'Permission denied',
        'StdoutSize': 100,
    }

    receptor_job = AWXReceptorJob.__new__(AWXReceptorJob)
    receptor_job.unit_id = 'test-unit'
    receptor_job.task = Mock()
    receptor_job.task.instance = Mock()
    receptor_job.task.instance.log_format = 'job 1'
    receptor_job.task.runner_callback = Mock()
    receptor_job.task.runner_callback.extra_update_fields = {}
    receptor_job.task.runner_callback.event_ct = 5

    result = receptor_job._handle_work_error(receptor_ctl, res)

    assert result == res
    # Verify delay_update was called with detail
    receptor_job.task.runner_callback.delay_update.assert_called_once()
    call_kwargs = receptor_job.task.runner_callback.delay_update.call_args[1]
    assert 'Receptor detail' in call_kwargs['result_traceback']
    assert 'Permission denied' in call_kwargs['result_traceback']


# ---------------------------------------------------------------------------
# Finding #2 Fix: Terminal State Check Before Adoption Finalization
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_adoption_deferred_when_stream_fails_but_unit_still_running():
    """Transient stream error should not finalize a Running unit.

    Finding #2: A results-stream error should not mark a healthy Running unit as failed.
    Only finalize if unit reaches terminal state (Succeeded/Failed/Canceled).
    """
    from awx.main.models import Job, JobTemplate, Organization

    org = Organization.objects.create(name='test_org')
    jt = JobTemplate.objects.create(name='test_jt', organization=org)
    job = Job.objects.create(job_template=jt, status='running')
    job.work_unit_id = 'test-unit-running'
    job.save()

    receptor_ctl = Mock()
    # Simulate get_work_results failure (transient network error)
    receptor_ctl.get_work_results.side_effect = ConnectionError("network timeout")
    # But status query succeeds and shows unit is Running
    receptor_ctl.simple_command.return_value = {'StateName': 'Running', 'ExitCode': None, 'Detail': ''}

    result = reattach_to_work_unit(job, receptor_ctl)

    assert result is False, "Adoption should be deferred when unit still Running"
    job.refresh_from_db()
    assert job.status == 'running', "Job should remain running after stream error"


@pytest.mark.django_db
def test_adoption_finalizes_when_stream_fails_but_unit_failed():
    """Stream error when unit is actually Failed should finalize as failed.

    Even if streaming fails, if status query shows Failed state, it's authoritative
    and we should finalize the job as failed.
    """
    from awx.main.models import Job, JobTemplate, Organization

    org = Organization.objects.create(name='test_org')
    jt = JobTemplate.objects.create(name='test_jt', organization=org)
    job = Job.objects.create(job_template=jt, status='running')
    job.work_unit_id = 'test-unit-failed'
    job.save()

    receptor_ctl = Mock()
    # Simulate get_work_results failure
    receptor_ctl.get_work_results.side_effect = ConnectionError("network timeout")
    # Status query shows unit is Failed
    receptor_ctl.simple_command.return_value = {'StateName': 'Failed', 'ExitCode': 1, 'Detail': 'execution failed'}

    result = reattach_to_work_unit(job, receptor_ctl)

    assert result is True, "Adoption should be finalized when unit is Failed"
    job.refresh_from_db()
    assert job.status == 'failed', "Job should be marked failed when unit Failed"


@pytest.mark.django_db
def test_adoption_deferred_when_stream_and_status_query_both_fail():
    """When both streaming and status query fail, adoption should defer (safe default).

    Cannot determine unit state → cannot finalize → defer for retry.
    """
    from awx.main.models import Job, JobTemplate, Organization

    org = Organization.objects.create(name='test_org')
    jt = JobTemplate.objects.create(name='test_jt', organization=org)
    job = Job.objects.create(job_template=jt, status='running')
    job.work_unit_id = 'test-unit-unknown'
    job.save()

    receptor_ctl = Mock()
    # Simulate get_work_results failure
    receptor_ctl.get_work_results.side_effect = ConnectionError("network timeout")
    # Status query also fails — can't determine state
    receptor_ctl.simple_command.side_effect = ConnectionError("receptor unreachable")

    result = reattach_to_work_unit(job, receptor_ctl)

    assert result is False, "Adoption should be deferred when state cannot be determined"
    job.refresh_from_db()
    assert job.status == 'running', "Job should remain running when state unknown"


@pytest.mark.django_db
def test_adoption_finalizes_when_stream_fails_but_unit_succeeded():
    """Stream error when unit is Succeeded should finalize as successful.

    Succeeded is a terminal state — safe to finalize as successful even if streaming failed.
    """
    from awx.main.models import Job, JobTemplate, Organization

    org = Organization.objects.create(name='test_org')
    jt = JobTemplate.objects.create(name='test_jt', organization=org)
    job = Job.objects.create(job_template=jt, status='running')
    job.work_unit_id = 'test-unit-succeeded'
    job.save()

    receptor_ctl = Mock()
    # Simulate get_work_results failure
    receptor_ctl.get_work_results.side_effect = ConnectionError("network timeout")
    # Status query shows unit is Succeeded
    receptor_ctl.simple_command.return_value = {'StateName': 'Succeeded', 'ExitCode': 0, 'Detail': ''}

    result = reattach_to_work_unit(job, receptor_ctl)

    assert result is True, "Adoption should be finalized when unit is Succeeded"
    job.refresh_from_db()
    assert job.status == 'successful', "Job should be marked successful when unit Succeeded"


# ---------------------------------------------------------------------------
# Stalled results stream (AAP-89602 follow-up)
#
# Receptor can adopt a work unit's metadata while its stdout monitor never manages to
# reach the execution node. The unit then reports a terminal state with a non-zero
# StdoutSize copied from the remote, while the local stdout file stays empty — so the
# results stream delivers nothing and never EOFs, and the dispatcher worker blocks
# forever. These cover the watchdog that breaks that deadlock.
# ---------------------------------------------------------------------------


def _stalling_reader(bytes_read=0, idle_for=999):
    """A _CountingReader-shaped stub that has read `bytes_read` and been idle `idle_for`s."""
    reader = Mock()
    reader.bytes_read = bytes_read
    reader.last_progress = time.monotonic() - idle_for
    return reader


def test_counting_reader_tallies_readline_and_read():
    inner = MagicMock()
    inner.readline.side_effect = [b'abc\n', b'de\n']
    inner.read.return_value = b'fghi'
    reader = _CountingReader(inner)

    assert reader.readline() == b'abc\n'
    assert reader.bytes_read == 4
    assert reader.readline() == b'de\n'
    assert reader.bytes_read == 7
    assert reader.read() == b'fghi'
    assert reader.bytes_read == 11


def test_counting_reader_empty_read_does_not_advance_progress():
    """An empty read is EOF, not progress — it must not reset the idle clock."""
    inner = MagicMock()
    inner.readline.return_value = b''
    reader = _CountingReader(inner)
    reader.last_progress = time.monotonic() - 500

    before = reader.last_progress
    assert reader.readline() == b''

    assert reader.bytes_read == 0
    assert reader.last_progress == before


def test_counting_reader_proxies_unknown_attributes():
    inner = MagicMock()
    inner.fileno.return_value = 7
    reader = _CountingReader(inner)

    assert reader.fileno() == 7
    reader.close()
    inner.close.assert_called_once()


def test_stream_is_stalled_false_before_idle_timeout():
    """Still receiving data — never ask receptor anything."""
    rj = _make_receptor_job()
    rj.stream_idle_timeout = 120
    ctl = Mock()

    assert rj._stream_is_stalled(ctl, _stalling_reader(bytes_read=10, idle_for=5)) is False
    ctl.simple_command.assert_not_called()


def test_stream_is_stalled_false_while_unit_still_running():
    """A running job may legitimately emit nothing for a long time."""
    rj = _make_receptor_job()
    rj.stream_idle_timeout = 120
    ctl = Mock()
    ctl.simple_command.return_value = {'StateName': 'Running', 'StdoutSize': 5000}

    assert rj._stream_is_stalled(ctl, _stalling_reader()) is False


def test_stream_is_stalled_false_when_all_bytes_received():
    """Terminal and idle, but we already have everything — this is normal end of stream."""
    rj = _make_receptor_job()
    rj.stream_idle_timeout = 120
    ctl = Mock()
    ctl.simple_command.return_value = {'StateName': 'Succeeded', 'StdoutSize': 5000}

    assert rj._stream_is_stalled(ctl, _stalling_reader(bytes_read=5000)) is False


def test_stream_is_stalled_false_when_status_query_raises():
    """Without a status we cannot prove a stall, so keep waiting rather than abandon."""
    rj = _make_receptor_job()
    rj.stream_idle_timeout = 120
    ctl = Mock()
    ctl.simple_command.side_effect = RuntimeError('socket closed')

    assert rj._stream_is_stalled(ctl, _stalling_reader()) is False


def test_stream_is_stalled_true_on_terminal_idle_short_read():
    """The real bug: Succeeded with StdoutSize 194807 and nothing delivered locally."""
    rj = _make_receptor_job()
    rj.stream_idle_timeout = 120
    ctl = Mock()
    ctl.simple_command.return_value = {'StateName': 'Succeeded', 'StdoutSize': 194807}

    assert rj._stream_is_stalled(ctl, _stalling_reader(bytes_read=0)) is True


def test_await_processor_without_timeout_never_polls_receptor():
    """Normal job submission must be completely untouched by the watchdog."""
    rj = _make_receptor_job()
    assert rj.stream_idle_timeout is None
    ctl = Mock()
    future = Mock()
    future.result.return_value = _Result(status='successful', rc=0)

    res = rj._await_processor(future, ctl, Mock(), Mock())

    assert res.status == 'successful'
    future.result.assert_called_once_with()
    ctl.simple_command.assert_not_called()
    assert rj.stream_stalled is False


def test_await_processor_shuts_down_socket_on_stall():
    rj = _make_receptor_job()
    rj.stream_idle_timeout = 120
    ctl = Mock()
    resultsock = Mock()
    stalled_res = _Result(status='error', rc=1)
    future = Mock()
    future.result.side_effect = [concurrent.futures.TimeoutError(), stalled_res]

    with patch.object(AWXReceptorJob, '_stream_is_stalled', return_value=True):
        res = rj._await_processor(future, ctl, Mock(), resultsock)

    assert rj.stream_stalled is True
    assert res.status == 'error'
    resultsock.shutdown.assert_called_once_with(socket.SHUT_RDWR)


def test_await_processor_keeps_waiting_while_not_stalled():
    """A slow but healthy stream must not be abandoned."""
    rj = _make_receptor_job()
    rj.stream_idle_timeout = 120
    good_res = _Result(status='successful', rc=0)
    future = Mock()
    future.result.side_effect = [concurrent.futures.TimeoutError(), good_res]
    resultsock = Mock()

    with patch.object(AWXReceptorJob, '_stream_is_stalled', return_value=False):
        res = rj._await_processor(future, Mock(), Mock(), resultsock)

    assert rj.stream_stalled is False
    assert res.status == 'successful'
    resultsock.shutdown.assert_not_called()


@patch('awx.main.tasks.jobs._finalize_job_run')
@patch('awx.main.tasks.receptor._compute_adoption_dedup', return_value=(0, set(), 0))
@patch('awx.main.tasks.receptor._adoption_stall_budget_exhausted', return_value=False)
@patch('awx.main.tasks.receptor.AWXReceptorJob._process_phase')
@patch('awx.main.tasks.receptor.AWXReceptorJob._receptor_release_work')
@patch('awx.main.tasks.receptor._get_or_create_private_data_dir', return_value='/tmp/adopt')
@patch('awx.main.tasks.receptor.shutil.rmtree')
def test_reattach_stalled_stream_within_budget_defers(mock_rmtree, mock_pdd, mock_release, mock_process, mock_budget, mock_dedup, mock_finalize):
    """Deferring keeps the unit alive so a later attempt can stream the full event set."""
    job = Mock()
    job.id = 1
    job.work_unit_id = 'unit-1'
    job.spawned_by_workflow = False
    job.status = 'running'
    job.started = None
    job.execution_node = 'ee-node'
    job.job_env = {}
    ctl = Mock()
    ctl.simple_command.return_value = {'StateName': 'Succeeded', 'StdoutSize': 194807}
    mock_process.return_value = _Result(status='error', rc=1)

    with patch.object(AWXReceptorJob, 'stream_stalled', True):
        result = reattach_to_work_unit(job, ctl)

    assert result is False, 'a stalled stream inside the budget must defer, not finalize'
    mock_release.assert_not_called()
    mock_finalize.assert_not_called()


@patch('awx.main.tasks.receptor._finalize_adopted_job')
@patch('awx.main.tasks.receptor.invoke_adoption_hooks', return_value=(True, {}))
@patch('awx.main.tasks.receptor._build_adoption_callback')
@patch('awx.main.tasks.receptor._compute_adoption_dedup', return_value=(0, set(), 0))
@patch('awx.main.tasks.receptor._adoption_stall_budget_exhausted', return_value=True)
@patch('awx.main.tasks.receptor.AWXReceptorJob._process_phase')
@patch('awx.main.tasks.receptor.AWXReceptorJob._receptor_release_work')
@patch('awx.main.tasks.receptor._get_or_create_private_data_dir', return_value='/tmp/adopt')
@patch('awx.main.tasks.receptor.shutil.rmtree')
def test_reattach_stalled_stream_past_budget_finalizes_from_unit_status(
    mock_rmtree, mock_pdd, mock_release, mock_process, mock_budget, mock_dedup, mock_callback, mock_hooks, mock_finalize
):
    """The truncated stream reads as 'error'; the unit status says the job succeeded.

    The unit status is the truthful source. Recording this job as failed — the behaviour
    before the stall branch existed — would be wrong, and releasing the unit would destroy
    the output that is still sitting on the execution node.
    """
    job = Mock()
    job.id = 1
    job.work_unit_id = 'unit-1'
    job.spawned_by_workflow = False
    job.status = 'running'
    job.started = None
    job.execution_node = 'ee-node'
    job.job_env = {}
    ctl = Mock()
    ctl.simple_command.return_value = {'StateName': 'Succeeded', 'ExitCode': 0, 'Detail': '', 'StdoutSize': 194807}
    mock_process.return_value = _Result(status='error', rc=1)

    with patch.object(AWXReceptorJob, 'stream_stalled', True):
        result = reattach_to_work_unit(job, ctl)

    assert result is True
    mock_release.assert_called_once()
    assert mock_finalize.call_args.kwargs['final_status'] == 'successful'
    assert mock_finalize.call_args.args[2] == 0, 'exit code must come from the unit, not the failed stream'

    explanation = mock_callback.return_value.delay_update.call_args.kwargs['job_explanation']
    assert 'could not be retrieved' in explanation


@patch('awx.main.tasks.receptor.settings')
def test_adoption_stall_budget_exhausted_uses_last_event_time(mock_settings):
    mock_settings.HADR_JOB_ADOPTION_TIMEOUT = 3600
    job = Mock()
    job.get_event_queryset.return_value.aggregate.return_value = {'created__max': now() - timedelta(seconds=7200)}

    assert _adoption_stall_budget_exhausted(job) is True


@patch('awx.main.tasks.receptor.settings')
def test_adoption_stall_budget_not_exhausted_for_recent_event(mock_settings):
    mock_settings.HADR_JOB_ADOPTION_TIMEOUT = 3600
    job = Mock()
    job.get_event_queryset.return_value.aggregate.return_value = {'created__max': now() - timedelta(seconds=60)}

    assert _adoption_stall_budget_exhausted(job) is False


@patch('awx.main.tasks.receptor.settings')
def test_adoption_stall_budget_falls_back_to_job_started(mock_settings):
    """A job that never emitted an event is measured from when it started."""
    mock_settings.HADR_JOB_ADOPTION_TIMEOUT = 3600
    job = Mock()
    job.get_event_queryset.return_value.aggregate.return_value = {'created__max': None}
    job.started = now() - timedelta(seconds=7200)

    assert _adoption_stall_budget_exhausted(job) is True


@patch('awx.main.tasks.receptor.settings')
def test_adoption_stall_budget_never_exhausted_without_timestamps(mock_settings):
    """No clock to measure against — defer rather than finalize on a guess."""
    mock_settings.HADR_JOB_ADOPTION_TIMEOUT = 3600
    job = Mock()
    job.get_event_queryset.return_value.aggregate.return_value = {'created__max': None}
    job.started = None

    assert _adoption_stall_budget_exhausted(job) is False


@patch('awx.main.tasks.receptor.connections')
@patch('awx.main.tasks.receptor.signal_callback', return_value=False)
def test_process_phase_breaks_out_of_a_stream_that_never_delivers(mock_signal, mock_connections):
    """Reproduces the production hang end-to-end through the real _process_phase.

    The unit reports Succeeded with StdoutSize 194807 while the local stdout file is
    empty, so the processor thread sits in readline() on a stream nobody will ever write
    to. Before the watchdog this wedged the dispatcher worker permanently.
    """
    rj = _make_receptor_job(unit_id='unit-stalled')
    rj.stream_idle_timeout = 0  # treat the stream as idle straight away
    rj.STREAM_POLL_INTERVAL = 0.05

    torn_down = threading.Event()

    inner = MagicMock()
    inner.readline.side_effect = lambda *a: b'' if torn_down.wait(10) else b''

    sock = Mock(spec=socket.socket)
    sock.shutdown.side_effect = lambda *a: torn_down.set()

    ctl = Mock()
    ctl.get_work_results.return_value = (sock, inner)
    ctl.simple_command.return_value = {'StateName': 'Succeeded', 'StdoutSize': 194807, 'Detail': 'exit status 0'}

    def fake_processor(reader):
        while reader.readline():
            pass
        return _Result(status='error', rc=1)

    rj.processor = fake_processor

    res = rj._process_phase(ctl)

    assert rj.stream_stalled is True, 'the watchdog must recognise a stream that will never deliver'
    assert res.status == 'error'
    sock.shutdown.assert_called_once_with(socket.SHUT_RDWR)
