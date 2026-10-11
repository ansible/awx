"""Adoption run end to end against a fake receptor work unit.

These tests drive the real reattach, streaming, dedup and finalize code. Only receptor
(FakeReceptorWork) and the callback-receiver queue (RecordingDispatcher) are replaced.
"""

from unittest import mock

import pytest

from awx.main.models import Job, JobEvent
from awx.main.tasks.receptor import reattach_to_work_unit
from awx.main.tasks.system import awx_receptor_workunit_reaper
from awx.main.tests.fake_receptor import FakeReceptorWork, FakeWorkUnit, RecordingDispatcher, make_events

UNIT = 'unit-1'


@pytest.fixture(autouse=True)
def adoption_env(settings, tmp_path):
    settings.AWX_ISOLATION_BASE_PATH = str(tmp_path)
    RecordingDispatcher.reset()
    # connections.close_all() would end the test's transaction; events go to the recorder instead of Redis.
    with (
        mock.patch('awx.main.tasks.receptor.connections'),
        mock.patch('awx.main.tasks.callback.CallbackQueueDispatcher', RecordingDispatcher),
        mock.patch('awx.main.tasks.jobs.ScheduleTaskManager'),
        mock.patch('awx.main.tasks.jobs.ScheduleWorkflowManager'),
        mock.patch('awx.main.models.unified_jobs.UnifiedJob.websocket_emit_status'),
    ):
        yield


@pytest.fixture
def running_job(me_inst):
    return Job.objects.create(controller_node=me_inst.hostname, execution_node='receptor-1', status='running', work_unit_id=UNIT)


def save_events(job, counters):
    for counter in counters:
        JobEvent.objects.create(job=job, counter=counter, event='runner_on_ok', job_created=job.created)


@pytest.mark.django_db
def test_finished_unit_is_replayed_and_finalized(running_job):
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(30))})

    assert reattach_to_work_unit(running_job, work) is True

    running_job.refresh_from_db()
    assert running_job.status == 'successful'
    assert RecordingDispatcher.counters() == list(range(1, 31))
    assert UNIT not in work.units, 'work unit released after finalize'


@pytest.mark.django_db
def test_events_already_saved_are_not_dispatched_again(running_job):
    save_events(running_job, range(1, 21))
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(30))})

    reattach_to_work_unit(running_job, work)

    assert RecordingDispatcher.counters() == list(range(21, 31))


@pytest.mark.django_db
def test_events_saved_out_of_order_are_skipped(running_job):
    # Parallel callback workers can commit counter 13 before 11 and 12.
    save_events(running_job, [*range(1, 11), 13])
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(20))})

    reattach_to_work_unit(running_job, work)

    assert RecordingDispatcher.counters() == [11, 12, *range(14, 21)]


@pytest.mark.django_db
def test_failed_playbook_finalizes_failed(running_job):
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10, failed_tasks=[5]), status='failed', exit_code=2)})

    reattach_to_work_unit(running_job, work)

    running_job.refresh_from_db()
    assert running_job.status == 'failed'


@pytest.mark.django_db
def test_unit_still_running_is_deferred(running_job):
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10), state='Running')})

    assert reattach_to_work_unit(running_job, work) is False

    running_job.refresh_from_db()
    assert running_job.status == 'running'
    assert RecordingDispatcher.dispatched == []
    assert UNIT in work.units


@pytest.mark.django_db
def test_unit_gone_is_deferred(running_job):
    # The unit was released, or the node lost it, before adoption.
    work = FakeReceptorWork()

    assert reattach_to_work_unit(running_job, work) is False

    running_job.refresh_from_db()
    assert running_job.status == 'running'


@pytest.mark.django_db
def test_stream_broken_mid_replay_fails_a_successful_unit(running_job):
    # The unit succeeded, but the results stream ends after 12 of 30 events.
    # Today the job is finalized failed, with only the events read before the break.
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(30), break_after=12)})

    reattach_to_work_unit(running_job, work)

    running_job.refresh_from_db()
    assert running_job.status == 'failed'
    assert RecordingDispatcher.counters() == list(range(1, 13))
    assert 'Unexpected empty line' in running_job.job_explanation


@pytest.mark.django_db
def test_workunit_reaper_releases_units_of_finished_jobs(me_inst, settings):
    settings.RECEPTOR_RELEASE_WORK = True
    finished = Job.objects.create(controller_node=me_inst.hostname, status='successful', work_unit_id='done')
    running = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='live')
    work = FakeReceptorWork({'done': FakeWorkUnit(), 'live': FakeWorkUnit(state='Running')})

    with (
        mock.patch('awx.main.tasks.system.get_receptor_ctl'),
        mock.patch('awx.main.tasks.system.ReceptorWork', return_value=work),
        mock.patch('awx.main.tasks.system.administrative_workunit_reaper'),
    ):
        awx_receptor_workunit_reaper()

    assert ('cancel', finished.work_unit_id) in work.calls
    assert finished.work_unit_id not in work.units
    assert running.work_unit_id in work.units
