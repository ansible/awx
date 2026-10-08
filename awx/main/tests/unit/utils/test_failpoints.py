import pathlib
import re
import signal
from unittest import mock

import pytest
import redis

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
    with _arm_in_memory({'job.before_finalize': {}}), mock.patch.object(failpoints, '_record_hit', return_value=('raise', {})):
        with pytest.raises(failpoints.FailpointError):
            failpoints.failpoint('job.before_finalize', job_id=1)


def test_raise_action_with_exception_class(settings):
    settings.AWX_FAILPOINTS_ENABLED = True
    with (
        _arm_in_memory({'health_check.redis_ping': {}}),
        mock.patch.object(failpoints, '_record_hit', return_value=('raise', {'exception': 'redis.exceptions.ConnectionError'})),
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
    with _arm_in_memory({'job.before_finalize': {}}), mock.patch.object(failpoints, '_record_hit', return_value=('sleep', {'seconds': 2})):
        with mock.patch.object(failpoints.time, 'sleep') as sleep:
            failpoints.failpoint('job.before_finalize')
    sleep.assert_called_once_with(2.0)


def test_kill_action_signals_self(settings):
    settings.AWX_FAILPOINTS_ENABLED = True
    with _arm_in_memory({'job.before_finalize': {}}), mock.patch.object(failpoints, '_record_hit', return_value=('kill', {})):
        with mock.patch.object(failpoints.os, 'kill') as kill:
            failpoints.failpoint('job.before_finalize')
    kill.assert_called_once_with(failpoints.os.getpid(), signal.SIGKILL)


def test_pause_action_delegates(settings):
    settings.AWX_FAILPOINTS_ENABLED = True
    with _arm_in_memory({'heartbeat.start': {}}), mock.patch.object(failpoints, '_record_hit', return_value=('pause', {'timeout': 5})):
        with mock.patch.object(failpoints, '_pause') as pause:
            failpoints.failpoint('heartbeat.start')
    pause.assert_called_once_with('heartbeat.start', {'timeout': 5})


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
