"""Path A (awx): Receptor results-stream teardown before release.

These tests encode the behaviour the fix must provide. They fail on the current
devel tree and pass with the fix.
"""

import threading
import time
from unittest import mock

import pytest

from awx.main.tasks import receptor


class FakeSock:
    def __init__(self, events, fail_second_shutdown=False):
        self.events = events
        self.shutdown_calls = 0
        self.fail_second_shutdown = fail_second_shutdown

    def shutdown(self, how):
        self.shutdown_calls += 1
        if self.fail_second_shutdown and self.shutdown_calls > 1:
            raise OSError(107, 'Transport endpoint is not connected')
        self.events.append('sock-shutdown')

    def close(self):
        self.events.append('sock-close')


class FakeResultFile:
    def __init__(self, events):
        self.events = events

    def close(self):
        self.events.append('file-close')


def make_process_phase_job(result):
    job = receptor.AWXReceptorJob.__new__(receptor.AWXReceptorJob)
    job.task = mock.Mock()
    job.task.runner_callback.extra_update_fields = {}
    job.runner_params = {}
    job.unit_id = 'unit-1'
    job.processor = mock.Mock(return_value=result)
    return job


def make_ctl(events):
    sock = FakeSock(events)
    resultfile = FakeResultFile(events)
    ctl = mock.Mock()
    ctl.get_work_results.return_value = (sock, resultfile)

    def simple_command(command):
        if command.startswith('work release'):
            events.append('release')
        elif command.startswith('work force-release'):
            events.append('force-release')
        elif command.startswith('work cancel'):
            events.append('cancel')
        return {}

    ctl.simple_command.side_effect = simple_command
    return ctl


def run_process_phase(job, ctl, signal=False):
    with (
        mock.patch.object(receptor.connections, 'close_all'),
        mock.patch.object(receptor, 'signal_callback', return_value=signal),
    ):
        return job._process_phase(ctl)


def test_process_phase_closes_results_on_success():
    events = []
    ctl = make_ctl(events)
    job = make_process_phase_job(mock.Mock(status='successful', rc=0))

    res = run_process_phase(job, ctl)

    assert res.status == 'successful'
    assert 'sock-shutdown' in events
    assert 'file-close' in events
    assert 'sock-close' in events
    assert events.index('sock-shutdown') < events.index('sock-close')


def test_results_teardown_precedes_work_release():
    events = []
    ctl = make_ctl(events)
    job = make_process_phase_job(mock.Mock(status='successful', rc=0))

    run_process_phase(job, ctl)
    job._receptor_release_work(ctl, 'successful')

    assert 'release' in events
    assert 'sock-shutdown' in events
    assert 'sock-close' in events
    assert events.index('sock-shutdown') < events.index('release')
    assert events.index('file-close') < events.index('release')
    assert events.index('sock-close') < events.index('release')


def test_cancel_path_tears_down_exactly_once():
    events = []
    ctl = make_ctl(events)
    job = make_process_phase_job(mock.Mock(status='canceled', rc=1))

    res = run_process_phase(job, ctl, signal=True)

    assert res.status == 'canceled'
    assert 'cancel' in events
    assert events.count('sock-shutdown') == 1
    assert events.count('sock-close') == 1
    assert 'file-close' in events


def test_error_path_closes_both_results_streams():
    """_process_phase closes the first stream and _handle_work_error closes its own."""
    first_events, second_events = [], []
    ctl = make_ctl(first_events)
    first_sock = FakeSock(first_events)
    first_file = FakeResultFile(first_events)
    second_sock = FakeSock(second_events)
    second_file = FakeResultFile(second_events)
    second_file.readlines = lambda: [b'boom\n']
    ctl.get_work_results.side_effect = [(first_sock, first_file), (second_sock, second_file)]

    def simple_command(command):
        if command.startswith('work status'):
            return {'StateName': 'Failed', 'StdoutSize': 5}
        return {}

    ctl.simple_command.side_effect = simple_command
    job = make_process_phase_job(mock.Mock(status='error', rc=1))
    job.task.runner_callback.event_ct = 0

    res = run_process_phase(job, ctl)

    assert res.status == 'error'
    assert 'sock-shutdown' in first_events
    assert 'file-close' in first_events
    assert 'sock-close' in first_events
    assert 'sock-shutdown' in second_events
    assert 'file-close' in second_events
    assert 'sock-close' in second_events


def test_adoption_process_phase_closes_before_release():
    """reattach_to_work_unit calls _process_phase standalone, then releases."""
    events = []
    ctl = make_ctl(events)
    job = make_process_phase_job(mock.Mock(status='successful', rc=0))

    run_process_phase(job, ctl)
    with mock.patch.object(receptor, '_finalize_adopted_job', return_value=None):
        job._receptor_release_work(ctl, 'successful')

    assert 'release' in events
    assert events.index('sock-shutdown') < events.index('release')
    assert events.index('file-close') < events.index('release')
    assert events.index('sock-close') < events.index('release')


def test_close_results_closes_socket_after_shutdown():
    events = []
    receptor.AWXReceptorJob._close_results(FakeSock(events), FakeResultFile(events))

    assert events == ['sock-shutdown', 'file-close', 'sock-close']


def test_close_results_swallows_teardown_errors():
    class BadSock:
        def shutdown(self, how):
            raise OSError(107, 'Transport endpoint is not connected')

        def close(self):
            raise ValueError('already closed')

    class BadFile:
        def close(self):
            raise OSError(9, 'Bad file descriptor')

    receptor.AWXReceptorJob._close_results(BadSock(), BadFile())
    receptor.AWXReceptorJob._close_results(None, None)


def test_cancel_path_unblocks_blocked_processor():
    """Cancel must yank the socket before joining the processor thread.

    A processor blocked on a slow/unreachable remote EN must not keep the
    dispatcher worker waiting for the executor join.
    """
    started = threading.Event()
    unblock = threading.Event()

    def blocking_processor(_resultfile):
        started.set()
        # Simulates a reader blocked on a slow remote EN. Only the socket
        # shutdown can release it.
        unblock.wait(timeout=5)
        return mock.Mock(status='successful', rc=0)

    def signal():
        started.wait(timeout=5)
        return True

    events = []
    ctl = make_ctl(events)
    sock = FakeSock(events)
    orig_shutdown = sock.shutdown

    def shutdown(how):
        orig_shutdown(how)
        unblock.set()

    sock.shutdown = shutdown
    ctl.get_work_results.return_value = (sock, FakeResultFile(events))

    job = make_process_phase_job(None)
    job.processor = blocking_processor

    start = time.monotonic()
    with (
        mock.patch.object(receptor.connections, 'close_all'),
        mock.patch.object(receptor, 'signal_callback', side_effect=signal),
    ):
        res = job._process_phase(ctl)
    elapsed = time.monotonic() - start

    assert started.is_set()
    assert res.status == 'canceled'
    assert elapsed < 3, f'cancel path waited {elapsed:.1f}s on the processor join'


def test_cancel_path_closes_stream_when_work_cancel_fails():
    """A failing work cancel must not re-open the executor-join hang."""
    started = threading.Event()
    unblock = threading.Event()

    def blocking_processor(_resultfile):
        started.set()
        unblock.wait(timeout=5)
        return mock.Mock(status='successful', rc=0)

    def signal():
        started.wait(timeout=5)
        return True

    events = []
    ctl = make_ctl(events)
    ctl.simple_command.side_effect = RuntimeError('control socket is gone')
    sock = FakeSock(events)
    orig_shutdown = sock.shutdown

    def shutdown(how):
        orig_shutdown(how)
        unblock.set()

    sock.shutdown = shutdown
    ctl.get_work_results.return_value = (sock, FakeResultFile(events))

    job = make_process_phase_job(None)
    job.processor = blocking_processor

    start = time.monotonic()
    with (
        mock.patch.object(receptor.connections, 'close_all'),
        mock.patch.object(receptor, 'signal_callback', side_effect=signal),
        pytest.raises(RuntimeError, match='control socket is gone'),
    ):
        job._process_phase(ctl)
    elapsed = time.monotonic() - start

    assert 'sock-shutdown' in events
    assert 'sock-close' in events
    assert elapsed < 3, f'cancel path waited {elapsed:.1f}s on the processor join after work cancel failed'


def test_reattach_to_work_unit_orders_teardown_before_finalize_and_release():
    """The adoption caller must tear down, then finalize, then release."""
    events = []
    ctl = make_ctl(events)
    job = mock.Mock(work_unit_id='unit-1', id=1, pk=1)
    receptor_job = make_process_phase_job(mock.Mock(status='successful', rc=0))
    receptor_job.unit_id = 'unit-1'

    def finalize(*_args, **_kwargs):
        events.append('finalize')

    with (
        mock.patch.object(receptor.connections, 'close_all'),
        mock.patch.object(receptor, 'signal_callback', return_value=False),
        mock.patch.object(receptor, '_compute_adoption_dedup', return_value=(0, [])),
        mock.patch.object(receptor, '_build_adoption_callback', return_value=mock.Mock()),
        mock.patch.object(receptor, '_get_or_create_private_data_dir', return_value='/tmp/adoption'),
        mock.patch.object(receptor, '_AdoptionTask', return_value=mock.Mock()),
        mock.patch.object(receptor, 'AWXReceptorJob', return_value=receptor_job),
        mock.patch.object(receptor, '_finalize_adopted_job', side_effect=finalize),
        mock.patch.object(receptor.shutil, 'rmtree'),
    ):
        assert receptor.reattach_to_work_unit(job, ctl) is True

    assert 'finalize' in events
    assert 'release' in events
    assert events.index('sock-shutdown') < events.index('finalize')
    assert events.index('sock-close') < events.index('finalize')
    assert events.index('finalize') < events.index('release')
