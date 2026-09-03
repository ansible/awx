"""Unit tests for receptor job adoption (same-controller restart reattach).

Covers:
  - reattach_to_work_unit: all branch paths
  - AWXReceptorJob._process_phase / _handle_work_error: all branch paths
  - receptor_config_exists
  - _get_or_create_private_data_dir
  - should_update_config FileNotFoundError path
"""

import socket
from collections import namedtuple
from unittest.mock import MagicMock, Mock, patch

import pytest

from awx.main.tasks.receptor import (
    AWXReceptorJob,
    _AdoptionTask,
    _configure_runner_callback,
    _get_adoption_exit_code,
    _get_or_create_private_data_dir,
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


@patch('awx.main.tasks.receptor.AWXReceptorJob._process_phase')
@patch('awx.main.tasks.receptor.AWXReceptorJob._receptor_release_work')
@patch('awx.main.tasks.receptor._get_or_create_private_data_dir', return_value='/tmp/adopt')
@patch('awx.main.tasks.receptor.shutil.rmtree')
def test_reattach_sets_job_created_on_callback(mock_rmtree, mock_pdd, mock_release, mock_process):
    """callback.job_created must be set so events are stored with the correct timestamp."""
    job = Mock()
    job.id = 1
    job.work_unit_id = 'unit-1'
    job.created = '2026-01-01T00:00:00Z'
    job.spawned_by_workflow = False
    job.get_event_queryset.return_value.values_list.return_value = []
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


@patch('awx.main.tasks.receptor.AWXReceptorJob._process_phase')
@patch('awx.main.tasks.receptor.AWXReceptorJob._receptor_release_work')
@patch('awx.main.tasks.receptor._get_or_create_private_data_dir', return_value='/tmp/adopt')
@patch('awx.main.tasks.receptor.shutil.rmtree')
def test_reattach_releases_work_unit_on_success(mock_rmtree, mock_pdd, mock_release, mock_process):
    """_receptor_release_work must be called after successful _process_phase."""
    job = Mock()
    job.id = 1
    job.work_unit_id = 'unit-1'
    job.spawned_by_workflow = False
    job.get_event_queryset.return_value.values_list.return_value = []
    job.status = 'successful'
    ctl = Mock()
    ctl.simple_command.return_value = {'StateName': 'Succeeded', 'ExitCode': 0, 'Detail': ''}

    reattach_to_work_unit(job, ctl)

    mock_release.assert_called_once()


@patch('awx.main.tasks.receptor.AWXReceptorJob._process_phase', side_effect=RuntimeError('network failure'))
@patch('awx.main.tasks.receptor.AWXReceptorJob._receptor_release_work')
@patch('awx.main.tasks.receptor._get_or_create_private_data_dir', return_value='/tmp/adopt')
@patch('awx.main.tasks.receptor.shutil.rmtree')
def test_reattach_releases_work_unit_on_failure(mock_rmtree, mock_pdd, mock_release, mock_process):
    """_receptor_release_work must run even when _process_phase raises (finally block).
    The job is still finalized using exit_code so result is True, not False.
    """
    job = Mock()
    job.id = 1
    job.work_unit_id = 'unit-1'
    job.spawned_by_workflow = False
    job.started = None  # avoids datetime arithmetic in elapsed calculation
    job.get_event_queryset.return_value.values_list.return_value = []
    job.status = 'running'
    ctl = Mock()
    ctl.simple_command.return_value = {'StateName': 'Succeeded', 'ExitCode': 0, 'Detail': ''}

    result = reattach_to_work_unit(job, ctl)

    assert result is True  # finalized via exit_code
    assert job.status == 'successful'
    mock_release.assert_called_once()


# ---------------------------------------------------------------------------
# reattach_to_work_unit — spawned_by_workflow=True → parent_workflow_job_id set
# ---------------------------------------------------------------------------


@patch('awx.main.tasks.receptor.AWXReceptorJob._process_phase')
@patch('awx.main.tasks.receptor.AWXReceptorJob._receptor_release_work')
@patch('awx.main.tasks.receptor._get_or_create_private_data_dir', return_value='/tmp/adopt')
@patch('awx.main.tasks.receptor.shutil.rmtree')
def test_reattach_sets_parent_workflow_job_id_when_workflow_child(mock_rmtree, mock_pdd, mock_release, mock_process):
    """callback.parent_workflow_job_id must be set for workflow-child jobs so events are
    correctly associated with their parent workflow in the event stream."""
    job = Mock()
    job.id = 1
    job.work_unit_id = 'unit-1'
    job.created = '2026-01-01T00:00:00Z'
    job.spawned_by_workflow = True
    job.get_workflow_job.return_value.id = 999
    job.get_event_queryset.return_value.values_list.return_value = []
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


@patch('awx.main.tasks.receptor.AWXReceptorJob._process_phase')
@patch('awx.main.tasks.receptor.AWXReceptorJob._receptor_release_work')
@patch('awx.main.tasks.receptor._get_or_create_private_data_dir', return_value='/tmp/adopt')
@patch('awx.main.tasks.receptor.shutil.rmtree')
def test_reattach_workflow_job_lookup_exception_swallowed(mock_rmtree, mock_pdd, mock_release, mock_process):
    """If get_workflow_job() raises, adoption must still complete (bare except: pass)."""
    job = Mock()
    job.id = 1
    job.work_unit_id = 'unit-1'
    job.created = '2026-01-01T00:00:00Z'
    job.spawned_by_workflow = True
    job.get_workflow_job.side_effect = Exception('workflow lookup failed')
    job.get_event_queryset.return_value.values_list.return_value = []
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

    _configure_runner_callback(cb, instance, safe_env={'KEY': 'val'}, persisted_counters={1, 2})

    assert cb.instance is instance
    assert cb.job_created == str(instance.created)
    assert cb.safe_env == {'KEY': 'val'}
    assert cb.persisted_counters == {1, 2}


def test_configure_runner_callback_safe_env_defaults_to_empty_dict():
    from awx.main.tasks.callback import RunnerCallback

    cb = RunnerCallback(model=None)
    instance = Mock()
    instance.created = '2026-01-01'
    instance.spawned_by_workflow = False

    _configure_runner_callback(cb, instance)

    assert cb.safe_env == {}
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


@patch('awx.main.tasks.receptor.AWXReceptorJob._process_phase')
@patch('awx.main.tasks.receptor.AWXReceptorJob._receptor_release_work')
@patch('awx.main.tasks.receptor._get_or_create_private_data_dir', return_value='/tmp/adopt')
@patch('awx.main.tasks.receptor.shutil.rmtree')
def test_reattach_non_workflow_job_no_parent_id(mock_rmtree, mock_pdd, mock_release, mock_process):
    """callback.parent_workflow_job_id is NOT set for non-workflow jobs."""
    job = Mock()
    job.id = 1
    job.work_unit_id = 'unit-1'
    job.created = '2026-01-01T00:00:00Z'
    job.spawned_by_workflow = False
    job.get_event_queryset.return_value.values_list.return_value = []
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
