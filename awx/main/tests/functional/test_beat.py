import pytest
import mock
import datetime
from datetime import timedelta

from awx.main.beat import Beat

def find_entry(entries, name):
    for e in entries:
        if e.name == name:
            return e
    return None

@pytest.fixture(autouse=True)
def _disable_database_settings(mocker):
    m = mocker.patch('awx.conf.settings.SettingsWrapper.all_supported_settings', new_callable=mock.PropertyMock)
    m.return_value = []

@pytest.fixture
def epoch():
    return datetime.datetime(2000, 1, 1, 00, 00)

@pytest.fixture(autouse=True)
def mock_signal():
    mock.patch('awx.main.beat.signal.pause', lambda: True)
    signal = mock.patch('awx.main.beat.signal')
    return signal

@pytest.fixture
def schedules_simple(epoch):
    return {
        't1': {
            'task': 'task',
            'schedule': datetime.timedelta(seconds=3)
        },
        't2': {
            'task': 'task',
            'schedule': datetime.timedelta(seconds=1)
        },
        't3': {
            'task': 'task',
            'schedule': datetime.timedelta(seconds=12)
        }
    }

@pytest.fixture
def schedules_towerish(epoch):
    return {
        't1': {
            'task': 'task',
            'schedule': datetime.timedelta(seconds=20)
        },
        't2': {
            'task': 'task',
            'schedule': datetime.timedelta(seconds=30)
        },
        't3': {
            'task': 'task',
            'schedule': datetime.timedelta(seconds=30)
        }
    }

@pytest.fixture
def schedules_1(epoch):
    schedules = {
        't1': {
            'task': 'task',
            'schedule': datetime.timedelta(seconds=1)
        }
    }
    return schedules

@pytest.fixture
def schedules_thundering_heard(epoch):
    schedules = {
        't1': {
            'task': 'task',
            'schedule': datetime.timedelta(seconds=1)
        },
        't2': {
            'task': 'task',
            'schedule': datetime.timedelta(seconds=1)
        },
        't3': {
            'task': 'task',
            'schedule': datetime.timedelta(seconds=1)
        },
        't4': {
            'task': 'task',
            'schedule': datetime.timedelta(seconds=1)
        },
    }
    return schedules

def test_beat_startup(schedules_simple, epoch):
    beat = Beat(schedules_simple, epoch=epoch)
    beat.scheduler.epoch = epoch

    '''
    All schedules run at first beat
    '''
    beat.scheduler.get_time = lambda: epoch
    scheds = list(beat.scheduler.get_schedules_to_run())
    assert set(['t1', 't2', 't3']) == set([s.name for s in scheds])
    for s in scheds:
        assert epoch == s.last_exec_absolute

    '''
    Subsequently, no schedules should run for the same beat time
    '''
    beat.scheduler.get_time = lambda: epoch
    scheds = list(beat.scheduler.get_schedules_to_run())
    assert 0 == len(scheds), "All schedules ran, should not run again until time changes"

    '''
    Next beat runs the correct, 1 second schedule
    '''
    beat.scheduler.get_time = lambda: epoch + timedelta(seconds=1)
    scheds = list(beat.scheduler.get_schedules_to_run())
    assert set(['t2']) == set([s.name for s in scheds])
    assert epoch + timedelta(seconds=1) == scheds[0].last_exec_absolute

def test_beat_thundering_heard(schedules_thundering_heard, epoch):
    beat = Beat(schedules_thundering_heard, epoch=epoch)

    beat.scheduler.get_time = lambda: epoch + timedelta(seconds=1)
    scheds = list(beat.scheduler.get_schedules_to_run())
    assert 4 == len(scheds)
    beat.scheduler.get_time = lambda: epoch + timedelta(seconds=2)
    scheds = list(beat.scheduler.get_schedules_to_run())
    assert 4 == len(scheds)
    beat.scheduler.get_time = lambda: epoch + timedelta(seconds=3)
    scheds = list(beat.scheduler.get_schedules_to_run())
    assert 4 == len(scheds)

    scheds = list(beat.scheduler.get_schedules_to_run())
    assert 0 == len(scheds)

def test_beat_backlog(schedules_simple, epoch):
    beat = Beat(schedules_simple, epoch=epoch)

    beat.scheduler.get_time = lambda: epoch
    scheds = list(beat.scheduler.get_schedules_to_run())

    beat.scheduler.get_time = lambda: epoch + timedelta(seconds=10)
    scheds = list(beat.scheduler.get_schedules_to_run())
    assert set(['t1', 't2']) == set([s.name for s in scheds])
    assert epoch + timedelta(seconds=10) == scheds[0].last_exec_absolute
    assert epoch + timedelta(seconds=10) == scheds[1].last_exec_absolute

    assert [2, 9] == [find_entry(beat.scheduler.entries, 't1').periods_missed,
                      find_entry(beat.scheduler.entries, 't2').periods_missed]

def test_beat_boundaries(schedules_towerish, epoch):
    beat = Beat(schedules_towerish, epoch=epoch)

    beat.scheduler.get_time = lambda: epoch
    scheds = list(beat.scheduler.get_schedules_to_run())

    beat.scheduler.get_time = lambda: epoch + timedelta(seconds=20.10)
    scheds = list(beat.scheduler.get_schedules_to_run())
    assert set(['t1']) == set([s.name for s in scheds])
    assert 0 == find_entry(beat.scheduler.entries, 't1').periods_missed

    beat.scheduler.get_time = lambda: epoch + timedelta(seconds=29.99)
    scheds = list(beat.scheduler.get_schedules_to_run())
    assert 0 == len(scheds)

    beat.scheduler.get_time = lambda: epoch + timedelta(seconds=30.01)
    scheds = list(beat.scheduler.get_schedules_to_run())
    assert set(['t2', 't3']) == set([s.name for s in scheds])
