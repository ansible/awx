"""Unit tests for container-group job adoption (AAP-89602 / 89607, register item 3).

A container-group job has no execution node: its receptor work unit lives in the dying
controller's own EE sidecar and dies with it. The job *pod*, however, is a separate
Kubernetes object that survives, and the k8s log API serves the same byte stream receptor
would have relayed. These tests cover the triage that decides what can be recovered from
that pod.
"""

import io
from datetime import datetime, timedelta, timezone
from unittest.mock import DEFAULT, Mock, patch

import pytest

from awx.main.tasks.container_groups import (
    PodState,
    adopt_container_group_job,
    attach_to_streaming_pod,
    classify_job_pod,
    delete_job_pod,
    find_job_pod,
    harvest_terminal_pod,
    open_pod_log_stream,
    pod_exit_code,
    pod_has_output,
    requeue_wedged_job,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

NOW = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
WEDGE_TIMEOUT = 300


def _pod(phase='Running', started_ago=10, name='automation-job-42-abcde', exit_code=None):
    """Build a pod dict shaped like the kubernetes client's ``.to_dict()`` output."""
    status = {'phase': phase, 'start_time': NOW - timedelta(seconds=started_ago)}
    if exit_code is not None:
        status['container_statuses'] = [{'state': {'terminated': {'exit_code': exit_code}}}]
    return {
        'metadata': {
            'name': name,
            'namespace': 'aap',
            'creation_timestamp': NOW - timedelta(seconds=started_ago),
            'labels': {'ansible-awx-job-id': '42'},
        },
        'status': status,
    }


def _job(job_id=42):
    job = Mock()
    job.id = job_id
    job.pk = job_id
    job.is_container_group_task = True
    job.log_format = f'job {job_id}'
    return job


def _classify(pod, has_output=False, started_ago=None):
    return classify_job_pod(pod, has_output=has_output, wedge_timeout=WEDGE_TIMEOUT, reference_time=NOW)


# ---------------------------------------------------------------------------
# classify_job_pod — the four-way triage
# ---------------------------------------------------------------------------


def test_classify_absent_pod():
    """No pod means nothing survived; the job is genuinely lost."""
    assert _classify(None) == PodState.ABSENT


@pytest.mark.parametrize('phase', ['Succeeded', 'Failed'])
def test_classify_terminal_pod(phase):
    """A finished pod still serves its full log — harvest it, do not re-run it."""
    assert _classify(_pod(phase=phase, exit_code=0 if phase == 'Succeeded' else 2)) == PodState.TERMINAL


@pytest.mark.parametrize('phase', ['Running', 'Pending'])
def test_classify_running_pod_with_output_is_streaming(phase):
    """Output proves ansible-runner got its private data dir and is doing work."""
    assert _classify(_pod(phase=phase), has_output=True) == PodState.STREAMING


@pytest.mark.parametrize('phase', ['Running', 'Pending'])
def test_classify_silent_pod_past_the_timeout_is_wedged(phase):
    """Silence past the timeout means stdin never completed; the worker will never run."""
    pod = _pod(phase=phase, started_ago=WEDGE_TIMEOUT + 1)
    assert _classify(pod, has_output=False) == PodState.WEDGED


@pytest.mark.parametrize('phase', ['Running', 'Pending'])
def test_classify_silent_pod_within_the_timeout_waits(phase):
    """A young silent pod is indistinguishable from a slow start — do not condemn it."""
    pod = _pod(phase=phase, started_ago=WEDGE_TIMEOUT - 1)
    assert _classify(pod, has_output=False) == PodState.WAITING


def test_classify_silent_pod_exactly_at_the_timeout_waits():
    """The boundary is exclusive: only strictly past the budget is wedged."""
    assert _classify(_pod(started_ago=WEDGE_TIMEOUT), has_output=False) == PodState.WAITING


def test_classify_unknown_phase_waits_rather_than_condemning():
    """Phase 'Unknown' means the kubelet is unreachable, which says nothing about the pod."""
    pod = _pod(phase='Unknown', started_ago=WEDGE_TIMEOUT * 10)
    assert _classify(pod, has_output=False) == PodState.WAITING


def test_classify_falls_back_to_creation_timestamp_when_unstarted():
    """A pod that never started has no start_time; age still has to be computable."""
    pod = _pod(phase='Pending', started_ago=WEDGE_TIMEOUT + 1)
    del pod['status']['start_time']
    assert _classify(pod, has_output=False) == PodState.WEDGED


def test_classify_without_any_timestamp_waits():
    """No timestamp means no measurable age, so there is no deadline to be past."""
    pod = _pod(phase='Running')
    del pod['status']['start_time']
    del pod['metadata']['creation_timestamp']
    assert _classify(pod, has_output=False) == PodState.WAITING


def test_classify_terminal_beats_output_check():
    """A terminal pod is harvested whether or not the cheap output probe saw anything."""
    assert _classify(_pod(phase='Succeeded', exit_code=0), has_output=False) == PodState.TERMINAL


# ---------------------------------------------------------------------------
# pod_exit_code
# ---------------------------------------------------------------------------


def test_pod_exit_code_prefers_the_terminated_container_state():
    assert pod_exit_code(_pod(phase='Failed', exit_code=137)) == 137


def test_pod_exit_code_zero_is_honored_not_treated_as_missing():
    """0 is falsy; a naive `or` fallback would turn a success into a failure."""
    assert pod_exit_code(_pod(phase='Succeeded', exit_code=0)) == 0


def test_pod_exit_code_falls_back_to_phase_when_container_status_is_gone():
    assert pod_exit_code(_pod(phase='Succeeded')) == 0
    assert pod_exit_code(_pod(phase='Failed')) == 1


def test_pod_exit_code_ignores_a_container_that_is_not_terminated():
    """A running sidecar has no terminated state; fall back rather than crash."""
    pod = _pod(phase='Failed')
    pod['status']['container_statuses'] = [{'state': {'running': {}}}]
    assert pod_exit_code(pod) == 1


# ---------------------------------------------------------------------------
# find_job_pod
# ---------------------------------------------------------------------------


@patch('awx.main.tasks.container_groups.PodManager')
def test_find_job_pod_selects_on_both_awx_labels(mock_pm_cls):
    """Scoping to this install as well as this job id keeps co-tenant pods out."""
    pm = mock_pm_cls.return_value
    pm.namespace = 'aap'
    pm.kube_api.list_namespaced_pod.return_value.to_dict.return_value = {'items': [_pod()]}

    with patch('awx.main.tasks.container_groups.settings') as mock_settings:
        mock_settings.INSTALL_UUID = 'uuid-1'
        mock_settings.AWX_CONTAINER_GROUP_K8S_API_TIMEOUT = 10
        find_job_pod(_job(42))

    selector = pm.kube_api.list_namespaced_pod.call_args.kwargs['label_selector']
    assert 'ansible-awx-job-id=42' in selector
    assert 'ansible-awx=uuid-1' in selector


@patch('awx.main.tasks.container_groups.PodManager')
def test_find_job_pod_returns_none_when_the_pod_is_gone(mock_pm_cls):
    pm = mock_pm_cls.return_value
    pm.namespace = 'aap'
    pm.kube_api.list_namespaced_pod.return_value.to_dict.return_value = {'items': []}
    assert find_job_pod(_job(42)) is None


@patch('awx.main.tasks.container_groups.PodManager')
def test_find_job_pod_returns_the_newest_when_a_retry_left_a_stale_pod(mock_pm_cls):
    """Pod names carry a random generateName suffix, so a relaunch can leave two."""
    old = _pod(name='automation-job-42-old', started_ago=9000)
    new = _pod(name='automation-job-42-new', started_ago=5)
    pm = mock_pm_cls.return_value
    pm.namespace = 'aap'
    pm.kube_api.list_namespaced_pod.return_value.to_dict.return_value = {'items': [old, new]}
    assert find_job_pod(_job(42))['metadata']['name'] == 'automation-job-42-new'


# ---------------------------------------------------------------------------
# pod_has_output — the cheap probe that separates STREAMING from WEDGED
# ---------------------------------------------------------------------------


def _log_response(body):
    """An unpreloaded urllib3 response, which is what the real client hands back.

    Earlier versions of these tests stubbed the call with a plain ``str``, which is why the
    ``b''`` bug below went unnoticed: the mock was friendlier than the client.
    """
    return Mock(data=body)


@patch('awx.main.tasks.container_groups.PodManager')
def test_pod_has_output_reads_only_one_line(mock_pm_cls):
    """The probe runs on every heartbeat for every orphan; it must stay cheap."""
    pm = mock_pm_cls.return_value
    pm.namespace = 'aap'
    pm.kube_api.read_namespaced_pod_log.return_value = _log_response(b'{"event": "playbook_on_start"}\n')
    assert pod_has_output(_job(42), 'automation-job-42-abcde') is True
    assert pm.kube_api.read_namespaced_pod_log.call_args.kwargs['tail_lines'] == 1


@patch('awx.main.tasks.container_groups.PodManager')
def test_pod_has_output_false_on_empty_and_whitespace(mock_pm_cls):
    pm = mock_pm_cls.return_value
    pm.namespace = 'aap'
    for empty in (b'', b'\n', b'   '):
        pm.kube_api.read_namespaced_pod_log.return_value = _log_response(empty)
        assert pod_has_output(_job(42), 'automation-job-42-abcde') is False


@patch('awx.main.tasks.container_groups.PodManager')
def test_pod_has_output_does_not_preload_content(mock_pm_cls):
    """Regression: with preloading, an empty log deserializes to the string "b''".

    The kube client declares this endpoint as returning ``str`` and so applies ``str()`` to
    the raw body. ``str(b'')`` is ``"b''"`` — three truthy characters — so every silent pod
    looked like it was producing output, WEDGED became unreachable, and wedged container-group
    jobs ran forever instead of being reaped. Asking for the unparsed response is the fix, so
    assert on the flag rather than only on the return value.
    """
    pm = mock_pm_cls.return_value
    pm.namespace = 'aap'
    pm.kube_api.read_namespaced_pod_log.return_value = _log_response(b'')
    assert pod_has_output(_job(42), 'automation-job-42-abcde') is False
    assert pm.kube_api.read_namespaced_pod_log.call_args.kwargs['_preload_content'] is False
    pm.kube_api.read_namespaced_pod_log.return_value.release_conn.assert_called_once()


@patch('awx.main.tasks.container_groups.PodManager')
def test_pod_has_output_propagates_api_errors(mock_pm_cls):
    """Swallowing this would read as 'no output' and condemn a healthy pod to deletion."""
    pm = mock_pm_cls.return_value
    pm.namespace = 'aap'
    pm.kube_api.read_namespaced_pod_log.side_effect = RuntimeError('api down')
    with pytest.raises(RuntimeError):
        pod_has_output(_job(42), 'automation-job-42-abcde')


# ---------------------------------------------------------------------------
# open_pod_log_stream
# ---------------------------------------------------------------------------


@patch('awx.main.tasks.container_groups.PodManager')
def test_open_pod_log_stream_is_unbuffered_and_undecoded(mock_pm_cls):
    """The ansible-runner Processor readline()s raw bytes; preloading would buffer the
    whole log into memory and break follow."""
    pm = mock_pm_cls.return_value
    pm.namespace = 'aap'
    open_pod_log_stream(_job(42), 'automation-job-42-abcde', follow=True)
    kwargs = pm.kube_api.read_namespaced_pod_log.call_args.kwargs
    assert kwargs['_preload_content'] is False
    assert kwargs['follow'] is True


@patch('awx.main.tasks.container_groups.PodManager')
def test_open_pod_log_stream_does_not_follow_a_terminal_pod(mock_pm_cls):
    pm = mock_pm_cls.return_value
    pm.namespace = 'aap'
    open_pod_log_stream(_job(42), 'automation-job-42-abcde', follow=False)
    assert pm.kube_api.read_namespaced_pod_log.call_args.kwargs['follow'] is False


# ---------------------------------------------------------------------------
# delete_job_pod — closes the wedged-pod quota leak
# ---------------------------------------------------------------------------


@patch('awx.main.tasks.container_groups.PodManager')
def test_delete_job_pod_deletes_in_the_group_namespace(mock_pm_cls):
    pm = mock_pm_cls.return_value
    pm.namespace = 'aap'
    assert delete_job_pod(_job(42), 'automation-job-42-abcde') is True
    kwargs = pm.kube_api.delete_namespaced_pod.call_args.kwargs
    assert kwargs['name'] == 'automation-job-42-abcde'
    assert kwargs['namespace'] == 'aap'


@patch('awx.main.tasks.container_groups.PodManager')
def test_delete_job_pod_reports_failure_rather_than_raising(mock_pm_cls):
    """Deletion is best-effort cleanup on the reaper path; it must not abort the sweep."""
    pm = mock_pm_cls.return_value
    pm.namespace = 'aap'
    pm.kube_api.delete_namespaced_pod.side_effect = RuntimeError('api down')
    assert delete_job_pod(_job(42), 'automation-job-42-abcde') is False


# ---------------------------------------------------------------------------
# adopt_container_group_job — the orchestration
# ---------------------------------------------------------------------------


@pytest.fixture
def adoption_env():
    """Patch every collaborator of adopt_container_group_job and hand back the mocks."""
    targets = [
        'find_job_pod',
        'pod_has_output',
        'classify_job_pod',
        'harvest_terminal_pod',
        'attach_to_streaming_pod',
        'delete_job_pod',
        'requeue_wedged_job',
        'budget_exhausted',
        'reap_job',
    ]
    with patch.multiple('awx.main.tasks.container_groups', **{t: DEFAULT for t in targets}) as mocks:
        mocks['find_job_pod'].return_value = _pod()
        mocks['pod_has_output'].return_value = False
        mocks['budget_exhausted'].return_value = False
        mocks['harvest_terminal_pod'].return_value = True
        yield mocks


def test_absent_pod_within_budget_defers(adoption_env):
    """The pod may simply not have been created yet when the controller died."""
    adoption_env['find_job_pod'].return_value = None
    adoption_env['classify_job_pod'].return_value = PodState.ABSENT

    assert adopt_container_group_job(_job()) is False
    adoption_env['reap_job'].assert_not_called()


def test_absent_pod_past_budget_fails_the_job(adoption_env):
    """Nothing brings a deleted pod back, so the job converges on the shared deadline."""
    adoption_env['find_job_pod'].return_value = None
    adoption_env['classify_job_pod'].return_value = PodState.ABSENT
    adoption_env['budget_exhausted'].return_value = True

    job = _job()
    assert adopt_container_group_job(job) is True
    assert adoption_env['reap_job'].call_args[0][1] == 'failed'


def test_waiting_pod_defers_without_touching_the_job(adoption_env):
    adoption_env['classify_job_pod'].return_value = PodState.WAITING

    assert adopt_container_group_job(_job()) is False
    adoption_env['reap_job'].assert_not_called()
    adoption_env['delete_job_pod'].assert_not_called()


def test_streaming_pod_is_attached_to_rather_than_waited_out(adoption_env):
    """A live pod is taken over now. Deferring until it went terminal would hold every event
    back to the end of the job and leave it uncancelable in the meantime."""
    adoption_env['classify_job_pod'].return_value = PodState.STREAMING
    adoption_env['attach_to_streaming_pod'].return_value = True

    pod = _pod()
    adoption_env['find_job_pod'].return_value = pod
    job = _job()

    assert adopt_container_group_job(job) is True
    adoption_env['harvest_terminal_pod'].assert_not_called()
    assert adoption_env['attach_to_streaming_pod'].call_args[0][:3] == (job, pod['metadata']['name'], pod)


def test_streaming_pod_is_never_subject_to_the_adoption_deadline(adoption_env):
    """A pod producing output is making progress. Applying the orphan deadline here would
    fail a perfectly healthy long-running job just because adoption emits no events."""
    adoption_env['classify_job_pod'].return_value = PodState.STREAMING
    adoption_env['attach_to_streaming_pod'].return_value = False
    adoption_env['budget_exhausted'].return_value = True

    assert adopt_container_group_job(_job()) is False
    adoption_env['reap_job'].assert_not_called()


def test_streaming_attach_is_given_the_callers_control_connection(adoption_env):
    """adopt_job_async already holds one. Opening a second would leak a socket per heartbeat."""
    adoption_env['classify_job_pod'].return_value = PodState.STREAMING
    adoption_env['attach_to_streaming_pod'].return_value = False
    ctl = Mock()

    adopt_container_group_job(_job(), receptor_ctl=ctl)

    assert adoption_env['attach_to_streaming_pod'].call_args[1]['receptor_ctl'] is ctl


def test_wedged_pod_is_deleted_and_its_job_requeued(adoption_env):
    """The worker blocked before the playbook ran, so a re-run has nothing to undo."""
    adoption_env['classify_job_pod'].return_value = PodState.WEDGED

    job = _job()
    assert adopt_container_group_job(job) is True
    adoption_env['delete_job_pod'].assert_called_once()
    adoption_env['requeue_wedged_job'].assert_called_once_with(job)
    adoption_env['reap_job'].assert_not_called()


def test_wedged_pod_that_cannot_be_deleted_is_not_requeued(adoption_env):
    """Requeuing on a failed delete would leave two pods carrying the same job-id label,
    and find_job_pod could then pick either one."""
    adoption_env['classify_job_pod'].return_value = PodState.WEDGED
    adoption_env['delete_job_pod'].return_value = False

    assert adopt_container_group_job(_job()) is False
    adoption_env['requeue_wedged_job'].assert_not_called()


def test_terminal_pod_is_harvested(adoption_env):
    adoption_env['classify_job_pod'].return_value = PodState.TERMINAL

    job = _job()
    assert adopt_container_group_job(job) is True
    assert adoption_env['harvest_terminal_pod'].call_args[0][0] is job


def test_terminal_harvest_failure_defers_rather_than_guessing(adoption_env):
    """A harvest that could not read the log must leave the job running and retryable;
    finalizing here would record a status with no output to back it."""
    adoption_env['classify_job_pod'].return_value = PodState.TERMINAL
    adoption_env['harvest_terminal_pod'].return_value = False

    assert adopt_container_group_job(_job()) is False
    adoption_env['reap_job'].assert_not_called()


def test_kubernetes_api_failure_defers_and_leaves_the_job_alone(adoption_env):
    """An unreachable API says nothing about the pod; the next heartbeat tries again."""
    adoption_env['find_job_pod'].side_effect = RuntimeError('api down')

    assert adopt_container_group_job(_job()) is False
    adoption_env['reap_job'].assert_not_called()
    adoption_env['delete_job_pod'].assert_not_called()


def test_output_probe_failure_defers_instead_of_classifying_as_wedged(adoption_env):
    """pod_has_output raising must never be read as 'no output' — that deletes a live pod."""
    adoption_env['pod_has_output'].side_effect = RuntimeError('api down')

    assert adopt_container_group_job(_job()) is False
    adoption_env['delete_job_pod'].assert_not_called()


def test_output_probe_is_skipped_for_a_terminal_pod(adoption_env):
    """A finished pod is harvested regardless, so do not spend an API call asking."""
    adoption_env['find_job_pod'].return_value = _pod(phase='Succeeded', exit_code=0)
    adoption_env['classify_job_pod'].return_value = PodState.TERMINAL

    adopt_container_group_job(_job())
    adoption_env['pod_has_output'].assert_not_called()


# ---------------------------------------------------------------------------
# attach_to_streaming_pod — take over a live pod through a fresh work unit
# ---------------------------------------------------------------------------


@pytest.fixture
def attach_env():
    targets = ['AWXReceptorJob', 'reattach_to_work_unit', 'UnifiedJob', 'get_receptor_ctl', 'read_receptor_config']
    with patch.multiple('awx.main.tasks.container_groups', **{t: DEFAULT for t in targets}) as mocks:
        mocks['AWXReceptorJob'].return_value.submit_pod_attach.return_value = 'new-unit-id'
        mocks['reattach_to_work_unit'].return_value = True
        yield mocks


def test_attach_submits_a_unit_for_the_pod_in_its_own_namespace(attach_env):
    ctl = Mock()
    pod = _pod()

    attach_to_streaming_pod(_job(), pod['metadata']['name'], pod, receptor_ctl=ctl)

    submit = attach_env['AWXReceptorJob'].return_value.submit_pod_attach
    assert submit.call_args[0] == (ctl, 'automation-job-42-abcde', 'aap')


def test_attach_repoints_the_job_at_the_unit_it_now_owns(attach_env):
    """The old work_unit_id names a unit in a controller pod that no longer exists. Until it
    is replaced, `work cancel` has nothing to reach and the next heartbeat re-does this."""
    job = _job()

    attach_to_streaming_pod(job, 'automation-job-42-abcde', _pod(), receptor_ctl=Mock())

    assert attach_env['UnifiedJob'].objects.filter.call_args.kwargs == {'pk': 42}
    assert attach_env['UnifiedJob'].objects.filter.return_value.update.call_args.kwargs == {'work_unit_id': 'new-unit-id'}
    assert job.work_unit_id == 'new-unit-id'


def test_attach_hands_off_to_the_ordinary_adoption_path(attach_env):
    """Everything after the submit — dedup, the stall watchdog, finalize, release — is the
    mesh path. Re-implementing any of it here is how the two drift apart."""
    ctl = Mock()
    ctl.simple_command.return_value = {'StateName': 'Running'}
    job = _job()

    assert attach_to_streaming_pod(job, 'automation-job-42-abcde', _pod(), receptor_ctl=ctl) is True

    ctl.simple_command.assert_called_once_with('work status new-unit-id')
    assert attach_env['reattach_to_work_unit'].call_args[0] == (job, ctl)
    assert attach_env['reattach_to_work_unit'].call_args.kwargs['unit_status'] == {'StateName': 'Running'}


def test_attach_defers_when_the_submit_fails_and_leaves_the_job_alone(attach_env):
    """No pod is created by a failed submit, so this says nothing about the job."""
    attach_env['AWXReceptorJob'].return_value.submit_pod_attach.side_effect = RuntimeError('receptor is down')

    assert attach_to_streaming_pod(_job(), 'automation-job-42-abcde', _pod(), receptor_ctl=Mock()) is False
    attach_env['UnifiedJob'].objects.filter.assert_not_called()
    attach_env['reattach_to_work_unit'].assert_not_called()


def test_attach_does_not_close_a_control_connection_it_was_handed(attach_env):
    ctl = Mock()
    attach_to_streaming_pod(_job(), 'automation-job-42-abcde', _pod(), receptor_ctl=ctl)
    ctl.close.assert_not_called()


def test_attach_closes_the_control_connection_it_opened_itself(attach_env):
    ctl = attach_env['get_receptor_ctl'].return_value

    attach_to_streaming_pod(_job(), 'automation-job-42-abcde', _pod())

    ctl.close.assert_called_once()


# ---------------------------------------------------------------------------
# requeue_wedged_job
# ---------------------------------------------------------------------------


@patch('awx.main.tasks.container_groups.UnifiedJob')
def test_requeue_clears_the_identifiers_that_mark_a_job_as_dispatched(mock_uj):
    """Leaving work_unit_id set would make the requeued job look orphaned to the next
    heartbeat, which would try to adopt the unit that just failed to exist."""
    requeue_wedged_job(_job(42))

    updates = mock_uj.objects.filter.return_value.update.call_args.kwargs
    assert updates['status'] == 'pending'
    assert updates['work_unit_id'] == ''
    assert updates['controller_node'] == ''
    assert updates['execution_node'] == ''


@patch('awx.main.tasks.container_groups.UnifiedJob')
def test_requeue_only_touches_a_job_that_is_still_running(mock_uj):
    """Another controller may have finalized it between triage and here."""
    requeue_wedged_job(_job(42))
    assert mock_uj.objects.filter.call_args.kwargs == {'pk': 42, 'status': 'running'}


# ---------------------------------------------------------------------------
# harvest_terminal_pod — real ansible-runner Processor over a real byte stream
# ---------------------------------------------------------------------------

POD_LOG = (
    b'{"status": "starting", "runner_ident": "42"}\n'
    b'{"uuid": "a", "counter": 1, "event": "playbook_on_start", "stdout": ""}\n'
    b'{"uuid": "b", "counter": 2, "event": "runner_on_ok", "stdout": "ok: [localhost]"}\n'
    b'{"uuid": "c", "counter": 3, "event": "playbook_on_stats", "stdout": "PLAY RECAP"}\n'
    b'{"status": "successful", "runner_ident": "42"}\n'
    b'{"eof": true}\n'
)


@pytest.fixture
def harvest_env(tmp_path):
    """Patch only what touches the database, so the byte stream really is processed."""
    callback = Mock()
    callback.event_handler = Mock(return_value=False)
    callback.status_handler = Mock(return_value=False)
    callback.artifacts_handler = Mock()
    callback.finished_callback = Mock()

    # DEFAULT sentinels, not explicit Mocks: patch.multiple only hands back a dict of the
    # mocks it created itself, so passing values yields an empty dict and no way to assert.
    targets = [
        '_compute_adoption_dedup',
        '_build_adoption_callback',
        '_get_or_create_private_data_dir',
        'invoke_adoption_hooks',
        '_finalize_adopted_job',
        'open_pod_log_stream',
    ]
    with patch.multiple('awx.main.tasks.container_groups', **{t: DEFAULT for t in targets}) as mocks:
        mocks['_compute_adoption_dedup'].return_value = (0, set(), 0)
        mocks['_build_adoption_callback'].return_value = callback
        mocks['_get_or_create_private_data_dir'].return_value = str(tmp_path)
        mocks['invoke_adoption_hooks'].return_value = (True, None)
        mocks['callback'] = callback
        yield mocks


def test_harvest_feeds_the_pod_log_through_the_runner_processor(harvest_env):
    """The pod log is byte-for-byte what receptor would have relayed, so the same
    process streamer has to be able to consume it straight from the k8s API."""
    harvest_env['open_pod_log_stream'].return_value = io.BytesIO(POD_LOG)

    assert harvest_terminal_pod(_job(), 'automation-job-42-abcde', _pod(phase='Succeeded', exit_code=0)) is True

    replayed = [call.args[0]['event'] for call in harvest_env['callback'].event_handler.call_args_list]
    assert replayed == ['playbook_on_start', 'runner_on_ok', 'playbook_on_stats']


def test_harvest_finalizes_with_the_status_the_playbook_reported(harvest_env):
    harvest_env['open_pod_log_stream'].return_value = io.BytesIO(POD_LOG)

    harvest_terminal_pod(_job(), 'automation-job-42-abcde', _pod(phase='Succeeded', exit_code=0))

    kwargs = harvest_env['_finalize_adopted_job'].call_args.kwargs
    assert kwargs['final_status'] == 'successful'


def test_harvest_falls_back_to_the_pod_exit_code_on_a_truncated_log(harvest_env):
    """kubelet rotates container logs, so a chatty job can lose the start of its own log and
    the Processor then reports 'error' for a job that actually succeeded. The exit code
    survives rotation; trusting the stream here would record a false failure."""
    harvest_env['open_pod_log_stream'].return_value = io.BytesIO(b'not json at all\n')

    harvest_terminal_pod(_job(), 'automation-job-42-abcde', _pod(phase='Succeeded', exit_code=0))

    assert harvest_env['_finalize_adopted_job'].call_args.kwargs['final_status'] == 'successful'


def test_harvest_reports_a_failed_pod_as_failed_when_the_log_is_unusable(harvest_env):
    harvest_env['open_pod_log_stream'].return_value = io.BytesIO(b'')

    harvest_terminal_pod(_job(), 'automation-job-42-abcde', _pod(phase='Failed', exit_code=2))

    assert harvest_env['_finalize_adopted_job'].call_args.kwargs['final_status'] == 'failed'


def test_harvest_defers_and_cleans_up_when_the_log_cannot_be_read(harvest_env, tmp_path):
    """An unreadable log is a connection problem, not a verdict — finalizing here would
    record a status with no output behind it."""
    harvest_env['open_pod_log_stream'].side_effect = RuntimeError('api down')

    assert harvest_terminal_pod(_job(), 'automation-job-42-abcde', _pod(phase='Succeeded', exit_code=0)) is False
    harvest_env['_finalize_adopted_job'].assert_not_called()
    assert not tmp_path.exists(), 'private_data_dir leaked'


def test_harvest_carries_persisted_event_count_into_the_callback(harvest_env):
    """Without this the replayed job reports only the events this pass emitted, so a job
    partly streamed before the controller died ends up with a short event count."""
    harvest_env['_compute_adoption_dedup'].return_value = (7, {8, 9}, 9)
    harvest_env['open_pod_log_stream'].return_value = io.BytesIO(POD_LOG)

    harvest_terminal_pod(_job(), 'automation-job-42-abcde', _pod(phase='Succeeded', exit_code=0))

    assert harvest_env['callback'].event_ct == 9
