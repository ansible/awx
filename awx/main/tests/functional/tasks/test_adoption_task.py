"""The adoption task, run end to end against FakeReceptorWork and a FakeClock.

These replace #16669 tests that patched get_receptor_ctl, reattach_to_work_unit or
AWXReceptorJob and asserted on receptorctl command strings. Here adopt_job runs for real:
the claim check, the capacity bound, the stall budgets, the reattach and the finalize.
Each test sets the unit's behavior on the fake and the time on the clock, then checks the
job's outcome and the operations the adoption performed on the unit.
"""

import logging
from unittest import mock

import pytest
from django.core.cache import cache
from django.utils.timezone import now, timedelta

from awx.main.models import Job, JobEvent
from awx.main.tasks.receptor import ReceptorWork, _adoption_stall_key, reattach_to_work_unit
from awx.main.tasks.system import adopt_job, adopt_job_async
from awx.main.tests.adoption_cluster import adoption_env
from awx.main.tests.fake_clock import FakeClock
from awx.main.tests.fake_receptor import FakeReceptorWork, FakeWorkUnit, RecordingDispatcher, make_events

TIMEOUT = 3600  # HADR_JOB_ADOPTION_TIMEOUT
UNIT = 'unit-1'
EXEC = 'receptor-1'


@pytest.fixture(autouse=True)
def env(settings, tmp_path):
    settings.HADR_JOB_ADOPTION_TIMEOUT = TIMEOUT
    # The stall budgets keep their start times in the cache, which outlives a test's database.
    cache.clear()
    with adoption_env(settings, tmp_path):
        yield


def orphan(me_inst, unit=UNIT, started_ago=60, **fields):
    """A running job this controller owns, orphaned by a restart."""
    fields.setdefault('execution_node', '')
    return Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id=unit, started=now() - timedelta(seconds=started_ago), **fields)


def unreachable():
    return FakeWorkUnit(make_events(10), status_error=RuntimeError('work unit unreachable'))


# ── An unreachable unit ───────────────────────────────────────────────────────


@pytest.mark.django_db
def test_unit_unreachable_past_the_budget_is_failed_and_its_failed_cancel_only_warns(me_inst, caplog):
    job = orphan(me_inst, started_ago=7200)
    work = FakeReceptorWork({UNIT: unreachable()})
    clock = FakeClock()

    adopt_job(job.id, open_work=lambda: work, clock=clock)
    clock.advance(TIMEOUT + 1)
    with caplog.at_level(logging.WARNING, logger='awx.main.tasks.system'):
        adopt_job(job.id, open_work=lambda: work, clock=clock)

    job.refresh_from_db()
    assert job.status == 'failed'
    assert 'HADR_JOB_ADOPTION_TIMEOUT' in job.job_explanation
    assert ('cancel', UNIT) in work.calls, 'the unit is canceled on a best-effort basis'
    assert not any(call[0] == 'results' for call in work.calls), 'an unreachable unit is never streamed'
    # The cancel is expected to fail on an unreachable unit, so it warns without a traceback.
    assert any('Failed to cancel work unit' in r.getMessage() for r in caplog.records)
    assert not any(r.exc_info for r in caplog.records)


@pytest.mark.django_db
def test_first_unreachable_query_spares_a_quiet_job(me_inst):
    # quiet-deadline: the last event is old because the playbook is quiet, not because it died.
    job = orphan(me_inst, started_ago=7200)
    JobEvent.objects.create(job=job, counter=10, event='runner_on_ok', job_created=job.created)
    JobEvent.objects.filter(job=job).update(created=now() - timedelta(seconds=TIMEOUT * 2))
    work = FakeReceptorWork({UNIT: unreachable()})

    adopt_job(job.id, open_work=lambda: work, clock=FakeClock())

    job.refresh_from_db()
    assert job.status == 'running', 'a single failed status query must defer, not fail the job'
    assert ('cancel', UNIT) not in work.calls, 'the live work unit must not be canceled'


@pytest.mark.django_db
def test_a_reachable_unit_restarts_the_unreachable_budget(me_inst):
    job = orphan(me_inst)
    unit = unreachable()
    work = FakeReceptorWork({UNIT: unit})
    clock = FakeClock()

    adopt_job(job.id, open_work=lambda: work, clock=clock)
    assert cache.get(_adoption_stall_key(job, 'unreachable')) is not None

    unit.status_error = None
    clock.advance(TIMEOUT - 1)
    adopt_job(job.id, open_work=lambda: work, clock=clock)

    assert cache.get(_adoption_stall_key(job, 'unreachable')) is None
    job.refresh_from_db()
    assert job.status == 'successful'


@pytest.mark.django_db
def test_adoption_that_raises_is_swallowed_and_still_closes_the_connection(me_inst):
    job = orphan(me_inst)
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10))})

    with mock.patch('awx.main.tasks.system.reattach_to_work_unit', side_effect=RuntimeError('network failure')):
        adopt_job(job.id, open_work=lambda: work)  # must not raise

    assert work.calls[-1] == ('close',)


@pytest.mark.django_db
def test_connection_is_closed_even_when_failing_the_job_raises(me_inst):
    job = orphan(me_inst, started_ago=7200)
    work = FakeReceptorWork({UNIT: unreachable()})
    clock = FakeClock()
    adopt_job(job.id, open_work=lambda: work, clock=clock)
    clock.advance(TIMEOUT + 1)

    with mock.patch('awx.main.tasks.system.reaper.reap_job', side_effect=RuntimeError('reap failed')):
        with pytest.raises(RuntimeError):
            adopt_job(job.id, open_work=lambda: work, clock=clock)

    assert work.calls[-1] == ('close',)


@pytest.mark.django_db
def test_a_failing_close_is_swallowed(me_inst):
    class CloseFails(FakeReceptorWork):
        def close(self):
            raise RuntimeError('socket already closed')

    job = orphan(me_inst)

    adopt_job(job.id, open_work=lambda: CloseFails({UNIT: FakeWorkUnit(make_events(10))}))  # must not raise

    job.refresh_from_db()
    assert job.status == 'successful'


# ── A reachable unit is streamed, never timed out ────────────────────────────


@pytest.mark.django_db
@pytest.mark.parametrize(
    'unit_fields, expected',
    [
        ({'state': 'Pending'}, 'successful'),
        ({'state': 'Running'}, 'successful'),
        ({}, 'successful'),  # Succeeded
        ({'status': 'failed', 'exit_code': 2}, 'failed'),
        ({'remote_only': True}, 'successful'),  # only the execution node holds it: 'Adopted', no StateName
    ],
    ids=['pending', 'running', 'succeeded', 'failed', 'adopted-from-execution-node'],
)
def test_a_reachable_unit_is_streamed_however_long_the_job_was_orphaned(me_inst, unit_fields, expected):
    # Orphaned for twice the timeout with no recent events: a reachable unit is still streamed.
    job = orphan(me_inst, started_ago=TIMEOUT * 2, execution_node=EXEC)
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10), **unit_fields)})

    adopt_job(job.id, open_work=lambda: work, clock=FakeClock())

    job.refresh_from_db()
    assert job.status == expected
    assert RecordingDispatcher.counters() == list(range(1, 11))


@pytest.mark.django_db
def test_unit_status_is_read_once_before_streaming(me_inst):
    job = orphan(me_inst)
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10))})

    adopt_job(job.id, open_work=lambda: work)

    assert work.calls.count(('status', UNIT)) == 1


# ── Ownership and cancels ─────────────────────────────────────────────────────


@pytest.mark.django_db
def test_job_already_finished_is_not_adopted(me_inst):
    job = orphan(me_inst)
    Job.objects.filter(pk=job.pk).update(status='successful')
    opened = mock.Mock()

    adopt_job(job.id, open_work=opened)

    opened.assert_not_called()


@pytest.mark.django_db
def test_job_claimed_from_a_lost_controller_is_adopted(me_inst):
    # The claim moved controller_node here before the adoption was published.
    job = Job.objects.create(controller_node='lost-host', status='running', work_unit_id=UNIT, execution_node=EXEC)
    Job.objects.filter(pk=job.pk).update(controller_node=me_inst.hostname)
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10))})

    adopt_job(job.id, open_work=lambda: work)

    job.refresh_from_db()
    assert job.status == 'successful'


@pytest.mark.django_db
def test_cancel_issued_while_the_job_was_orphaned_is_carried_out_by_the_adopter(me_inst):
    # cancel-orphan: the cancel signal reached a dead controller; only cancel_flag survived.
    job = orphan(me_inst, cancel_flag=True)
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10), state='Running')})

    adopt_job(job.id, open_work=lambda: work)

    assert ('cancel', UNIT) in work.calls, 'the live work unit must be stopped'
    job.refresh_from_db()
    assert job.status == 'canceled'


@pytest.mark.django_db
def test_work_unit_of_an_uncanceled_job_is_left_running(me_inst):
    job = orphan(me_inst)
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10), state='Running')})

    adopt_job(job.id, open_work=lambda: work)

    assert ('cancel', UNIT) not in work.calls
    job.refresh_from_db()
    assert job.status == 'successful'


# ── When streaming fails, the unit's status decides ──────────────────────────


@pytest.mark.parametrize(
    'unit_fields, expected',
    [
        ({'exit_code': 0}, 'successful'),
        ({'detail': 'not-a-number'}, 'successful'),  # Succeeded with no usable exit code
        ({'status': 'failed', 'detail': 'exit status 2'}, 'failed'),  # exit code parsed from Detail
        ({'status': 'failed', 'detail': ''}, 'failed'),
    ],
    ids=['succeeded-exit-0', 'succeeded-unparseable-detail', 'failed-exit-code-in-detail', 'failed-no-detail'],
)
@pytest.mark.django_db
def test_stream_that_cannot_be_read_is_finalized_from_the_unit_status(me_inst, unit_fields, expected):
    job = orphan(me_inst)
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10), results_error=RuntimeError('stream broke'), **unit_fields)})

    assert reattach_to_work_unit(job, work) is True

    job.refresh_from_db()
    assert job.status == expected


@pytest.mark.django_db
def test_unit_whose_status_cannot_be_read_is_left_alone(me_inst):
    job = orphan(me_inst)
    work = FakeReceptorWork({UNIT: unreachable()})

    assert reattach_to_work_unit(job, work) is False

    job.refresh_from_db()
    assert job.status == 'running'
    assert UNIT in work.units


@pytest.mark.django_db
def test_job_finalized_while_streaming_is_not_written_again(me_inst):
    job = orphan(me_inst)

    class FinalizedMidStream(FakeReceptorWork):
        def results(self, unit_id, startpos=None):
            Job.objects.filter(pk=job.pk).update(status='failed', job_explanation='finalized elsewhere')
            return super().results(unit_id, startpos)

    reattach_to_work_unit(job, FinalizedMidStream({UNIT: FakeWorkUnit(make_events(10))}))

    job.refresh_from_db()
    assert (job.status, job.job_explanation) == ('failed', 'finalized elsewhere')


# ── Capacity ──────────────────────────────────────────────────────────────────


def owned_running_jobs(me_inst, count):
    """`count` running jobs this controller owns; returns the last."""
    return [orphan(me_inst, unit=f'unit-slot-{i}') for i in range(count)][-1]


@pytest.mark.django_db
@pytest.mark.parametrize(
    'capacity, adopted',
    [
        (2, False),  # three owned jobs, room for two: over capacity, deferred
        (100, True),  # well within capacity
        (3, True),  # the job under consideration is already counted, so it exactly fills
        (0, True),  # draining or unsized: not "room for nothing"
    ],
    ids=['over-capacity', 'within-capacity', 'exactly-full', 'draining'],
)
def test_capacity_bounds_adoption(me_inst, settings, capacity, adopted):
    settings.AWX_CONTROL_NODE_TASK_IMPACT = 1
    me_inst.capacity = capacity
    job = owned_running_jobs(me_inst, 3)
    work = FakeReceptorWork({job.work_unit_id: FakeWorkUnit(make_events(10))})

    adopt_job(job.id, open_work=lambda: work)

    job.refresh_from_db()
    assert job.status == ('successful' if adopted else 'running')
    assert bool(work.calls) is adopted, 'a deferral happens before the connection is opened'


@pytest.mark.django_db
def test_adoption_proceeds_when_capacity_cannot_be_read(me_inst):
    job = owned_running_jobs(me_inst, 3)
    work = FakeReceptorWork({job.work_unit_id: FakeWorkUnit(make_events(10))})

    with mock.patch.object(type(me_inst).objects, 'me', side_effect=RuntimeError('no instance row')):
        adopt_job(job.id, open_work=lambda: work)

    job.refresh_from_db()
    assert job.status == 'successful'


@pytest.mark.django_db
def test_capacity_is_read_without_a_dispatcher_round_trip(me_inst, settings):
    settings.AWX_CONTROL_NODE_TASK_IMPACT = 1
    me_inst.capacity = 100
    job = owned_running_jobs(me_inst, 20)

    with mock.patch('awx.main.tasks.system.get_control_from_settings') as control:
        adopt_job(job.id, open_work=lambda: FakeReceptorWork({job.work_unit_id: FakeWorkUnit(make_events(10))}))

    control.assert_not_called()


@pytest.mark.django_db
class TestCapacityDeadline:
    """A claimed job holds capacity while it waits for capacity, so the wait must end."""

    @pytest.fixture(autouse=True)
    def no_room(self):
        with mock.patch('awx.main.tasks.system._adoption_slot_available', return_value=False) as slot:
            yield slot

    def test_job_waiting_past_the_budget_is_failed_without_opening_a_connection(self, me_inst):
        job = orphan(me_inst, started_ago=7200)
        opened = mock.Mock()
        clock = FakeClock()

        adopt_job(job.id, open_work=opened, clock=clock)
        clock.advance(TIMEOUT + 1)
        adopt_job(job.id, open_work=opened, clock=clock)

        job.refresh_from_db()
        assert job.status == 'failed'
        opened.assert_not_called()

    def test_first_wait_of_a_long_running_job_is_left_running(self, me_inst):
        # Started two hours ago is not two hours of waiting for capacity.
        job = orphan(me_inst, started_ago=7200)

        adopt_job(job.id, open_work=mock.Mock(), clock=FakeClock())

        job.refresh_from_db()
        assert job.status == 'running'

    def test_wait_within_the_budget_is_left_running(self, me_inst):
        job = orphan(me_inst)
        clock = FakeClock()

        adopt_job(job.id, open_work=mock.Mock(), clock=clock)
        clock.advance(TIMEOUT)
        adopt_job(job.id, open_work=mock.Mock(), clock=clock)

        job.refresh_from_db()
        assert job.status == 'running'

    def test_a_free_slot_restarts_the_budget(self, me_inst, no_room):
        job = orphan(me_inst)
        adopt_job(job.id, open_work=mock.Mock(), clock=FakeClock())
        assert cache.get(_adoption_stall_key(job, 'capacity')) is not None

        no_room.return_value = True
        adopt_job(job.id, open_work=lambda: FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10))}))

        assert cache.get(_adoption_stall_key(job, 'capacity')) is None


# ── The dispatcher task's wiring ──────────────────────────────────────────────


@pytest.mark.django_db
@pytest.mark.parametrize(
    'kwargs',
    [{'owner_task_id': 'adoption-task'}, {'source_controller': 'ctrl-0', 'owner_task_id': 'adoption-task'}, {}],
    ids=['current', 'earlier-aap-89602-build', 'pre-aap-89602-controller'],
)
def test_task_streams_from_this_controllers_receptor(me_inst, kwargs):
    # Every message shape a controller in a rolling upgrade may publish is accepted.
    job = orphan(me_inst)
    ctl = mock.Mock()

    with mock.patch('awx.main.tasks.system.adopt_job') as adopt, mock.patch('awx.main.tasks.system.get_receptor_ctl', return_value=ctl):
        adopt_job_async(job.id, **kwargs)
        work = adopt.call_args.kwargs['open_work']()

    assert adopt.call_args.args == (job.id,)
    assert adopt.call_args.kwargs['owner_task_id'] == kwargs.get('owner_task_id')
    assert isinstance(work, ReceptorWork) and work.receptor_ctl is ctl
