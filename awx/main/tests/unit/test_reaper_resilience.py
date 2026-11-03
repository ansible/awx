"""Path B (awx): receptor work-unit reaper resilience.

These tests encode the behaviour the fix must provide. They fail on the current
devel tree and pass with the fix: a per-unit failure must not abort the pass, a
dead receptorctl socket must be re-established, and a stale unit that is still
listed must be force-released.
"""

from unittest import mock

from awx.main.tasks import receptor, system


class FakeCtl:
    def __init__(
        self,
        work_list,
        fail_cancel=(),
        fail_release=(),
        fail_release_local=(),
        fail_release_transient=(),
        fail_force_release=(),
        fail_connection=(),
        connect_error=None,
    ):
        self.work_list = work_list
        self.fail_cancel = set(fail_cancel)
        self.fail_release = set(fail_release)
        self.fail_release_local = set(fail_release_local)
        self.fail_release_transient = set(fail_release_transient)
        self.fail_force_release = set(fail_force_release)
        self.fail_connection = set(fail_connection)
        self.connect_error = connect_error
        self.connection_dead = False
        self.connects = 0
        self.calls = []

    def connect(self):
        self.connects += 1
        if self.connect_error is not None:
            raise self.connect_error

    def simple_command(self, command):
        self.calls.append(command)
        if self.connection_dead:
            raise ValueError('Socket path does not exist: /run/receptor.sock')
        parts = command.split()
        if len(parts) == 3 and parts[0] == 'work':
            unit = parts[2]
            if unit in self.fail_connection:
                self.connection_dead = True
                raise ValueError('Socket path does not exist: /run/receptor.sock')
            if parts[1] == 'cancel' and unit in self.fail_cancel:
                raise RuntimeError(f'error cancelling remote unit:  unknown work unit {unit}')
            if parts[1] == 'release' and unit in self.fail_release_local:
                raise RuntimeError(f'unknown work unit {unit}')
            if parts[1] == 'release' and unit in self.fail_release:
                # Receptor reports a remote-gone release through the cancel path.
                raise RuntimeError(f'error cancelling remote unit:  unknown work unit {unit}')
            if parts[1] == 'release' and unit in self.fail_release_transient:
                raise ConnectionError('socket died mid-command')
            if parts[1] == 'force-release' and unit in self.fail_force_release:
                raise RuntimeError(f'error force-releasing unit {unit}')
        if command == 'work list':
            return dict(self.work_list)
        return {}


def make_jobs(*unit_ids):
    return [mock.Mock(work_unit_id=unit, log_format=f'job {unit}') for unit in unit_ids]


def run_reaper(ctl, jobs, extra_ctl=None):
    qs = mock.MagicMock()
    qs.exclude.return_value = jobs
    ctl_factory = mock.Mock(side_effect=[ctl, extra_ctl] if extra_ctl else [ctl])
    with (
        mock.patch.object(system, 'get_receptor_ctl', ctl_factory),
        mock.patch.object(system, 'administrative_workunit_reaper') as admin,
        mock.patch.object(system.UnifiedJob, 'objects') as objects,
    ):
        objects.filter.return_value = qs
        system.awx_receptor_workunit_reaper()
    return ctl_factory, admin


def test_reaper_continues_after_one_bad_unit():
    ctl = FakeCtl({'unit-a': {}, 'unit-b': {}, 'unit-c': {}}, fail_cancel={'unit-a'})
    _, admin = run_reaper(ctl, make_jobs('unit-a', 'unit-b', 'unit-c'))

    assert 'work release unit-b' in ctl.calls
    assert 'work release unit-c' in ctl.calls
    admin.assert_called_once()


def test_reaper_reestablishes_connection_after_socket_failure():
    dead = FakeCtl({'unit-a': {}, 'unit-b': {}}, fail_connection={'unit-a'})
    live = FakeCtl({'unit-a': {}, 'unit-b': {}})

    ctl_factory, admin = run_reaper(dead, make_jobs('unit-a', 'unit-b'), extra_ctl=live)

    assert ctl_factory.call_count == 2
    assert 'work release unit-a' in live.calls
    assert 'work release unit-b' in live.calls
    admin.assert_called_once()


def test_reaper_force_releases_when_remote_unit_is_gone():
    ctl = FakeCtl({'unit-a': {}}, fail_release={'unit-a'})
    _, admin = run_reaper(ctl, make_jobs('unit-a'))

    assert 'work release unit-a' in ctl.calls
    assert 'work force-release unit-a' in ctl.calls
    admin.assert_called_once()


def test_reaper_does_not_force_release_when_local_unit_is_gone():
    """A local lookup miss means the proxy directory is already gone."""
    ctl = FakeCtl({'unit-a': {}}, fail_release_local={'unit-a'})
    _, admin = run_reaper(ctl, make_jobs('unit-a'))

    assert 'work release unit-a' in ctl.calls
    assert 'work force-release unit-a' not in ctl.calls
    admin.assert_called_once()


def test_administrative_reaper_continues_after_one_bad_unit():
    work_list = {
        'unit-a': {'ExtraData': '--worker-info', 'StateName': 'Succeeded'},
        'unit-b': {'ExtraData': '--worker-info', 'StateName': 'Succeeded'},
    }
    ctl = FakeCtl(work_list, fail_release={'unit-a'}, fail_force_release={'unit-a'})

    with mock.patch.object(receptor, 'get_receptor_ctl', return_value=ctl):
        receptor.administrative_workunit_reaper(work_list=work_list)

    assert 'work release unit-a' in ctl.calls
    assert 'work release unit-b' in ctl.calls
    assert 'work force-release unit-a' in ctl.calls


def test_administrative_reaper_no_socket_is_noop():
    with mock.patch.object(receptor, 'get_receptor_ctl', side_effect=FileNotFoundError):
        receptor.administrative_workunit_reaper()


def test_administrative_reaper_work_list_failure_returns():
    ctl = mock.Mock()
    ctl.simple_command.side_effect = ValueError('Socket path does not exist')
    with mock.patch.object(receptor, 'get_receptor_ctl', return_value=ctl):
        receptor.administrative_workunit_reaper()


def test_reaper_stops_pass_when_reconnect_fails():
    dead = FakeCtl({'unit-a': {}, 'unit-b': {}}, fail_connection={'unit-a'})
    qs = mock.MagicMock()
    qs.exclude.return_value = make_jobs('unit-a', 'unit-b')
    ctl_factory = mock.Mock(side_effect=[dead, FileNotFoundError('no socket')])

    with (
        mock.patch.object(system, 'get_receptor_ctl', ctl_factory),
        mock.patch.object(system, 'administrative_workunit_reaper') as admin,
        mock.patch.object(system.UnifiedJob, 'objects') as objects,
    ):
        objects.filter.return_value = qs
        system.awx_receptor_workunit_reaper()

    admin.assert_called_once()
    assert ctl_factory.call_count == 2


def test_reaper_releases_after_reconnect_retry_fails():
    dead = FakeCtl({'unit-a': {}}, fail_connection={'unit-a'})
    live = FakeCtl({'unit-a': {}}, fail_cancel={'unit-a'}, fail_release={'unit-a'})

    _, admin = run_reaper(dead, make_jobs('unit-a'), extra_ctl=live)

    assert 'work force-release unit-a' in live.calls
    admin.assert_called_once()


def test_reaper_does_not_force_release_on_transient_failure():
    """A transient release failure must not delete the local proxy.

    The first failure triggers a reconnect; the replacement controller fails
    the retry and then release_work_unit's own release, and must not be
    force-released.
    """
    ctl = FakeCtl({'unit-a': {}}, fail_release_transient={'unit-a'})
    retry = FakeCtl({'unit-a': {}}, fail_release_transient={'unit-a'})
    _, admin = run_reaper(ctl, make_jobs('unit-a'), extra_ctl=retry)

    assert 'work release unit-a' in ctl.calls
    # Reconnect retry plus the release_work_unit attempt.
    assert retry.calls.count('work release unit-a') == 2
    assert 'work force-release unit-a' not in retry.calls
    admin.assert_called_once()


def test_reaper_stops_pass_when_reconnect_client_cannot_connect():
    """A lazy replacement client must be connected before retrying a unit."""
    dead = FakeCtl({'unit-a': {}, 'unit-b': {}}, fail_connection={'unit-a'})
    unreachable = FakeCtl({'unit-a': {}, 'unit-b': {}}, connect_error=ValueError('Socket path does not exist'))

    ctl_factory, admin = run_reaper(dead, make_jobs('unit-a', 'unit-b'), extra_ctl=unreachable)

    assert ctl_factory.call_count == 2
    assert unreachable.connects == 1
    # No command was attempted through the unusable replacement client.
    assert unreachable.calls == []
    admin.assert_called_once()


def test_reaper_work_list_oserror_returns():
    """A connection lost while listing units must not abort the task."""
    ctl = FakeCtl({})
    ctl.simple_command = mock.Mock(side_effect=OSError('socket closed mid-command'))
    ctl_factory = mock.Mock(return_value=ctl)

    with (
        mock.patch.object(system, 'get_receptor_ctl', ctl_factory),
        mock.patch.object(system, 'administrative_workunit_reaper') as admin,
        mock.patch.object(system.UnifiedJob, 'objects') as objects,
    ):
        system.awx_receptor_workunit_reaper()

    admin.assert_not_called()
    objects.filter.assert_not_called()


def test_release_work_unit_local_gone_is_a_noop():
    """A local lookup miss means the proxy directory is already gone."""
    ctl = FakeCtl({'unit-a': {}}, fail_release_local={'unit-a'})

    assert receptor.release_work_unit(ctl, 'unit-a', {'unit-a': {}}) is True
    assert 'work release unit-a' in ctl.calls
    assert 'work force-release unit-a' not in ctl.calls


def test_release_work_unit_remote_gone_force_releases():
    """Only the remote-gone error justifies removing the stale local proxy."""
    ctl = FakeCtl({'unit-a': {}}, fail_release={'unit-a'})

    assert receptor.release_work_unit(ctl, 'unit-a', {'unit-a': {}}) is True
    assert 'work force-release unit-a' in ctl.calls
