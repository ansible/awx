import pathlib
import re
import signal
from unittest import mock

import pytest
import redis
from django.core.management import call_command
from django.core.management.base import CommandError

from awx.main.utils import failpoints


@pytest.fixture(autouse=True)
def reset_state():
    failpoints._enabled = None
    failpoints._armed = {}
    failpoints._armed_at = 0.0
    yield
    failpoints._enabled = None
    failpoints._armed = {}
    failpoints._armed_at = 0.0


def _arm_in_memory(armed):
    """Bypass the database: pretend this armed set was just loaded."""
    return mock.patch.object(failpoints, '_load_armed', return_value=armed)


def test_disabled_is_inert_and_skips_registry_check(settings):
    settings.AWX_FAILPOINTS_ENABLED = False
    with mock.patch.object(failpoints, '_load_armed') as load:
        failpoints.failpoint('not.a.registered.name')
    load.assert_not_called()


def test_enabled_rejects_unregistered_name(settings):
    settings.AWX_FAILPOINTS_ENABLED = True
    with pytest.raises(KeyError, match='Unregistered failpoint'):
        failpoints.failpoint('not.a.registered.name')


def test_not_armed_does_nothing(settings):
    settings.AWX_FAILPOINTS_ENABLED = True
    with _arm_in_memory({}), mock.patch.object(failpoints, '_record_hit') as record:
        failpoints.failpoint('heartbeat.start')
    record.assert_not_called()


def test_match_filters_by_context(settings):
    settings.AWX_FAILPOINTS_ENABLED = True
    settings.CLUSTER_HOST_ID = 'awx-1'
    with _arm_in_memory({'heartbeat.start': {'node': 'awx-2'}}), mock.patch.object(failpoints, '_record_hit') as record:
        failpoints.failpoint('heartbeat.start')
    record.assert_not_called()

    with _arm_in_memory({'heartbeat.start': {'node': 'awx-1', 'periodic': 'True'}}), mock.patch.object(failpoints, '_record_hit', return_value=None) as record:
        failpoints.failpoint('heartbeat.start', periodic=True)
    record.assert_called_once()
    ctx = record.call_args[0][1]
    assert ctx['node'] == 'awx-1' and ctx['periodic'] is True and 'pid' in ctx


def test_raise_action(settings):
    settings.AWX_FAILPOINTS_ENABLED = True
    with _arm_in_memory({'job.before_finalize': {}}), mock.patch.object(failpoints, '_record_hit', return_value=('raise', {}, None)):
        with pytest.raises(failpoints.FailpointError):
            failpoints.failpoint('job.before_finalize', job_id=1)


def test_raise_action_with_exception_class(settings):
    settings.AWX_FAILPOINTS_ENABLED = True
    with (
        _arm_in_memory({'health_check.redis_ping': {}}),
        mock.patch.object(failpoints, '_record_hit', return_value=('raise', {'exception': 'redis.exceptions.ConnectionError'}, None)),
    ):
        with pytest.raises(redis.exceptions.ConnectionError):
            failpoints.failpoint('health_check.redis_ping')


def test_arm_rejects_non_exception_class():
    with pytest.raises(TypeError):
        failpoints.arm('heartbeat.start', 'raise', exception='os.path')
    with pytest.raises(AttributeError):
        failpoints.arm('heartbeat.start', 'raise', exception='redis.exceptions.NoSuchError')


def test_sleep_action(settings):
    settings.AWX_FAILPOINTS_ENABLED = True
    with _arm_in_memory({'job.before_finalize': {}}), mock.patch.object(failpoints, '_record_hit', return_value=('sleep', {'seconds': 2}, None)):
        with mock.patch.object(failpoints.time, 'sleep') as sleep:
            failpoints.failpoint('job.before_finalize')
    sleep.assert_called_once_with(2.0)


def test_kill_action_signals_self(settings):
    settings.AWX_FAILPOINTS_ENABLED = True
    with _arm_in_memory({'job.before_finalize': {}}), mock.patch.object(failpoints, '_record_hit', return_value=('kill', {}, None)):
        with mock.patch.object(failpoints.os, 'kill') as kill:
            failpoints.failpoint('job.before_finalize')
    kill.assert_called_once_with(failpoints.os.getpid(), signal.SIGKILL)


def test_pause_action_delegates(settings):
    settings.AWX_FAILPOINTS_ENABLED = True
    with _arm_in_memory({'heartbeat.start': {}}), mock.patch.object(failpoints, '_record_hit', return_value=('pause', {'timeout': 5}, 'gen-1')):
        with mock.patch.object(failpoints, '_pause') as pause:
            failpoints.failpoint('heartbeat.start')
    pause.assert_called_once()
    name, arg, armed_at, ctx = pause.call_args.args
    assert (name, arg, armed_at) == ('heartbeat.start', {'timeout': 5}, 'gen-1')
    assert {'node', 'pid'} <= set(ctx)


def test_hit_not_fired_continues(settings):
    settings.AWX_FAILPOINTS_ENABLED = True
    with _arm_in_memory({'heartbeat.start': {}}), mock.patch.object(failpoints, '_record_hit', return_value=None):
        with mock.patch.object(failpoints, '_pause') as pause:
            failpoints.failpoint('heartbeat.start')
    pause.assert_not_called()


def test_record_failure_never_fires(settings):
    settings.AWX_FAILPOINTS_ENABLED = True
    with _arm_in_memory({'heartbeat.start': {}}), mock.patch.object(failpoints, '_record_hit', side_effect=RuntimeError('db down')):
        with mock.patch.object(failpoints, '_pause') as pause:
            failpoints.failpoint('heartbeat.start')
    pause.assert_not_called()


def test_arm_validates_name_and_action():
    with pytest.raises(KeyError):
        failpoints.arm('nope', 'pause')
    with pytest.raises(ValueError):
        failpoints.arm('heartbeat.start', 'explode')


def test_every_call_site_is_registered():
    """Every failpoint('...') literal in the source tree must be in REGISTRY, and vice versa."""
    root = pathlib.Path(failpoints.__file__).resolve().parents[2]
    used = set()
    for path in root.rglob('*.py'):
        if 'tests' in path.parts:
            continue
        used |= set(re.findall(r"\bfailpoint\('([a-z_.]+)'", path.read_text(errors='ignore')))
    assert used - set(failpoints.REGISTRY) == set()
    assert set(failpoints.REGISTRY) - used == set()


def test_json_decodes_text_and_passes_dicts():
    assert failpoints._json('{"node": "awx-1"}') == {'node': 'awx-1'}
    assert failpoints._json({'a': 1}) == {'a': 1}
    assert failpoints._json(None) == {}
    assert failpoints._json('') == {}


def test_bad_match_never_crashes_call_site(settings):
    settings.AWX_FAILPOINTS_ENABLED = True
    with _arm_in_memory({'heartbeat.start': 'not-a-dict'}), mock.patch.object(failpoints, '_record_hit') as record:
        failpoints.failpoint('heartbeat.start')
    record.assert_not_called()


def test_return_value_says_whether_it_fired(settings):
    settings.AWX_FAILPOINTS_ENABLED = False
    assert failpoints.failpoint('heartbeat.force_lost', other='awx-1') is False
    settings.AWX_FAILPOINTS_ENABLED = True
    failpoints._enabled = None
    with _arm_in_memory({}):
        assert failpoints.failpoint('heartbeat.force_lost', other='awx-1') is False
    with _arm_in_memory({'heartbeat.force_lost': {}}), mock.patch.object(failpoints, '_record_hit', return_value=None):
        assert failpoints.failpoint('heartbeat.force_lost', other='awx-1') is False


def test_trigger_action_only_returns_true(settings):
    """trigger forces a decision at sites written as `if real_condition or failpoint(...)`."""
    settings.AWX_FAILPOINTS_ENABLED = True
    settings.CLUSTER_HOST_ID = 'awx-2'
    with (
        _arm_in_memory({'heartbeat.force_lost': {'other': 'awx-1'}}),
        mock.patch.object(failpoints, '_record_hit', return_value=('trigger', {}, None)) as record,
        mock.patch.object(failpoints, '_pause') as pause,
        mock.patch.object(failpoints.time, 'sleep') as sleep,
        mock.patch.object(failpoints.os, 'kill') as kill,
    ):
        assert failpoints.failpoint('heartbeat.force_lost', other='awx-3') is False
        assert failpoints.failpoint('heartbeat.force_lost', other='awx-1') is True
    record.assert_called_once()
    pause.assert_not_called()
    sleep.assert_not_called()
    kill.assert_not_called()


def test_arm_accepts_trigger():
    assert 'trigger' in failpoints.ACTIONS


class _Rows:
    """A fake cursor that answers the pause poll with one row per call."""

    def __init__(self, rows):
        self.rows = list(rows)
        self.polls = 0

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params):
        assert sql.startswith('SELECT released, armed_at')

    def fetchone(self):
        self.polls += 1
        return self.rows.pop(0)


@pytest.mark.parametrize(
    'rows, polls',
    [
        ([(False, 'gen-1', None), (True, 'gen-1', None)], 2),  # released
        ([(False, 'gen-1', None), None], 2),  # disarmed
        ([(False, 'gen-1', None), (False, 'gen-1', None), (False, 'gen-2', None)], 3),  # re-armed: the hold moves on
    ],
)
def test_pause_ends_on_release_disarm_or_rearm(rows, polls):
    cursor = _Rows(rows)
    with mock.patch.object(failpoints.connection, 'cursor', return_value=cursor), mock.patch.object(failpoints.time, 'sleep'):
        failpoints._pause('callback.event', {'timeout': 60}, 'gen-1')
    assert cursor.polls == polls


def test_pause_without_generation_ignores_rearm():
    cursor = _Rows([(False, 'gen-2', None), (True, 'gen-2', None)])
    with mock.patch.object(failpoints.connection, 'cursor', return_value=cursor), mock.patch.object(failpoints.time, 'sleep'):
        failpoints._pause('callback.event', {'timeout': 60})
    assert cursor.polls == 2


def test_record_snapshot_is_inert_when_disabled(settings):
    settings.AWX_FAILPOINTS_ENABLED = False
    with mock.patch.object(failpoints, 'ensure_tables') as ensure:
        failpoints.record_snapshot('host_map', 1, {'h1': 1})
    ensure.assert_not_called()


def test_record_snapshot_never_raises(settings):
    settings.AWX_FAILPOINTS_ENABLED = True
    with mock.patch.object(failpoints, 'ensure_tables', side_effect=RuntimeError('db down')):
        failpoints.record_snapshot('host_map', 1, {'h1': 1})


def test_pause_sleeps_until_a_scheduled_release():
    """A release scheduled for an instant: the holder sleeps until exactly that instant."""
    cursor = _Rows([(False, 'gen-1', None), (True, 'gen-1', 1000.75)])
    with (
        mock.patch.object(failpoints.connection, 'cursor', return_value=cursor),
        mock.patch.object(failpoints.time, 'sleep') as sleep,
        mock.patch.object(failpoints.time, 'time', return_value=1000.25),
    ):
        failpoints._pause('sweep.before_claim', {'timeout': 60}, 'gen-1')
    assert [c.args[0] for c in sleep.call_args_list] == [failpoints.PAUSE_POLL_SECONDS, 0.5]


def test_pause_past_schedule_resumes_at_once():
    cursor = _Rows([(True, 'gen-1', 1000.0)])
    with (
        mock.patch.object(failpoints.connection, 'cursor', return_value=cursor),
        mock.patch.object(failpoints.time, 'sleep') as sleep,
        mock.patch.object(failpoints.time, 'time', return_value=1000.2),
    ):
        failpoints._pause('sweep.before_claim', {'timeout': 60}, 'gen-1')
    sleep.assert_not_called()


class _Recorder:
    def __init__(self, rowcount=0):
        self.calls = []
        self.rowcount = rowcount

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self.calls.append((sql, params))


def test_resume_records_lateness_as_unfired_hit():
    cursor = _Recorder()
    with mock.patch.object(failpoints.connection, 'cursor', return_value=cursor), mock.patch.object(failpoints.time, 'time', return_value=1000.002):
        failpoints._resume_at('sweep.before_claim', 1000.0, {'node': 'awx-3', 'pid': 7, 'job_id': 5})
    ((sql, params),) = cursor.calls
    assert sql.startswith(f'INSERT INTO {failpoints.HIT_TABLE}')
    assert params[:3] == ['sweep.before_claim', 'awx-3', 7] and params[4] == 'resumed'
    assert '"late_ms": 2.0' in params[3]


def test_release_several_names_in_one_update():
    cursor = _Recorder(rowcount=2)
    with mock.patch.object(failpoints, 'ensure_tables'), mock.patch.object(failpoints.connection, 'cursor', return_value=cursor):
        n = failpoints.release('lost_instance.before_claim', 'sweep.before_claim', at=1234.5)
    assert n == 2
    ((sql, params),) = cursor.calls
    assert sql.startswith(f'UPDATE {failpoints.TABLE} SET released = true, release_at = %s WHERE name = ANY(%s)')
    assert params == [1234.5, ['lost_instance.before_claim', 'sweep.before_claim']]


def test_release_now_clears_any_schedule():
    cursor = _Recorder(rowcount=1)
    with mock.patch.object(failpoints, 'ensure_tables'), mock.patch.object(failpoints.connection, 'cursor', return_value=cursor):
        failpoints.release('heartbeat.start')
    assert cursor.calls[0][1] == [None, ['heartbeat.start']]


def test_release_needs_a_name():
    with pytest.raises(ValueError):
        failpoints.release()


def test_release_command_schedules_one_instant_for_all_names():
    with mock.patch.object(failpoints, 'release', return_value=2) as release, mock.patch('time.time', return_value=500.0):
        call_command('failpoint', 'release', 'lost_instance.before_claim', 'sweep.before_claim', '--in', '2', stdout=mock.MagicMock())
    release.assert_called_once_with('lost_instance.before_claim', 'sweep.before_claim', at=502.0)


def test_release_command_rejects_too_short_lead():
    with pytest.raises(CommandError):
        call_command('failpoint', 'release', 'sweep.before_claim', '--in', '0.1')


class _FlakyRows(_Rows):
    """The first poll fails as if the database restarted."""

    def execute(self, sql, params):
        if self.polls == 0 and not getattr(self, 'failed', False):
            self.failed = True
            raise failpoints.DatabaseError('server closed the connection unexpectedly')
        super().execute(sql, params)


def test_pause_survives_a_database_restart():
    cursor = _FlakyRows([(False, 'gen-1', None), (True, 'gen-1', None)])
    with (
        mock.patch.object(failpoints.connection, 'cursor', return_value=cursor),
        mock.patch.object(failpoints.connection, 'close') as close,
        mock.patch.object(failpoints.time, 'sleep'),
    ):
        failpoints._pause('adoption.before_finalize', {'timeout': 60}, 'gen-1')
    assert close.call_count == 1
    assert cursor.polls == 2
