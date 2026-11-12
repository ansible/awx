"""Failure scenarios in the adoption lifecycle: claim, stream, finalize (write-up section 3).

Tests marked xfail reproduce a defect found on devel and assert the behavior it should
have. The others guard behavior devel already gets right.
"""

from unittest import mock

import pytest
from django.db import DatabaseError
from django.utils.timezone import now, timedelta

from awx.main.models import Job, JobEvent
from awx.main.tasks import jobs
from awx.main.tasks.receptor import AWXReceptorJob
from awx.main.tasks.system import adopt_job
from awx.main.tests.adoption_cluster import EXEC, PEER, THIS, UNIT, adoption_env, configure, heartbeat, make_cluster, mesh, save_dispatched_events
from awx.main.tests.fake_clock import FakeClock
from awx.main.tests.fake_receptor import FakeReceptorWork, FakeWorkUnit, RecordingDispatcher, make_events

TIMEOUT = 300  # HADR_JOB_ADOPTION_TIMEOUT


@pytest.fixture(autouse=True)
def env(settings, tmp_path):
    settings.HADR_JOB_ADOPTION_TIMEOUT = TIMEOUT
    with adoption_env(settings, tmp_path):
        yield


@pytest.fixture
def orphan(me_inst):
    """A running job this controller lost track of, started a minute ago."""
    return Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id=UNIT, started=now() - timedelta(seconds=60))


def save_events(job, counters, created=None):
    for counter in counters:
        JobEvent.objects.create(job=job, counter=counter, event='runner_on_ok', job_created=job.created)
    if created:
        JobEvent.objects.filter(job=job).update(created=created)


@pytest.mark.xfail(strict=True, reason='AAP-96828: an error while finalizing a resumed job releases its unit and strands the job')
@pytest.mark.django_db
def test_finalize_error_is_retried_on_the_next_adoption(orphan):
    # 3.5 Finalize strand. The first adoption streams the whole unit, then finalization
    # raises. Today the unit is released anyway, so the next adoption finds nothing and the
    # job stays running until the adoption timeout fails it.
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10))})
    real_finalize = jobs._finalize_job_run
    attempts = []

    def finalize_fails_once(*args, **kwargs):
        attempts.append(1)
        if len(attempts) == 1:
            raise DatabaseError('connection lost during finalize')
        return real_finalize(*args, **kwargs)

    with mock.patch('awx.main.tasks.jobs._finalize_job_run', side_effect=finalize_fails_once):
        adopt_job(orphan.id, open_work=lambda: work)
        adopt_job(orphan.id, open_work=lambda: work)

    orphan.refresh_from_db()
    assert orphan.status == 'successful'


@pytest.mark.django_db
def test_quiet_job_whose_unit_is_still_running_is_not_failed(orphan):
    # 3.6 Quiet deadline (AAP-96829). The playbook is in a long task with no output, so its
    # last event is older than HADR_JOB_ADOPTION_TIMEOUT, but receptor reports the unit
    # running. Devel measures the deadline from the last event and fails the job while the
    # playbook keeps running. A reachable unit is never timed out: it is streamed live.
    clock = FakeClock()
    save_events(orphan, range(1, 6), created=clock() - timedelta(seconds=TIMEOUT + 60))
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10), state='Running')})

    adopt_job(orphan.id, open_work=lambda: work, clock=clock)

    orphan.refresh_from_db()
    assert orphan.status == 'successful'
    assert ('cancel', UNIT) not in work.calls
    assert RecordingDispatcher.counters() == list(range(6, 11))


@pytest.mark.django_db
def test_adoption_survives_repeated_restarts_and_replays_each_event_once(orphan):
    # 3.7 Three restarts during one job. Each adoption streams the running unit until its
    # controller shuts down and detaches; the next replays only the events not yet saved.
    # Once the unit finishes, the job is finalized, and every event was sent exactly once.
    clock = FakeClock()
    save_events(orphan, range(1, 13), created=clock())
    unit = FakeWorkUnit(make_events(30), state='Running')
    work = FakeReceptorWork({UNIT: unit})
    real_process_phase = AWXReceptorJob._process_phase
    sent = []

    def shut_down_after(event_count):
        def process_phase(receptor_job, stream_work):
            unit.break_after = event_count
            real_process_phase(receptor_job, stream_work)
            receptor_job.detached = True  # the controller is shutting down
            return None

        return process_phase

    for event_count in (16, 22, 27):
        with mock.patch.object(AWXReceptorJob, '_process_phase', shut_down_after(event_count)):
            adopt_job(orphan.id, open_work=lambda: work, clock=clock)
        orphan.refresh_from_db()
        assert orphan.status == 'running'
        sent += RecordingDispatcher.counters()
        save_dispatched_events()
        RecordingDispatcher.reset()
        clock.advance(60)

    unit.break_after = None
    unit.state = 'Succeeded'
    adopt_job(orphan.id, open_work=lambda: work, clock=clock)
    sent += RecordingDispatcher.counters()

    orphan.refresh_from_db()
    assert orphan.status == 'successful'
    assert sent == list(range(13, 31))


@pytest.mark.django_db
def test_large_replay_sends_every_event_once(orphan):
    # 5.8 Large replay. A 20,000 event unit with the first 500 already saved.
    save_events(orphan, range(1, 501))
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(20000))})

    adopt_job(orphan.id, open_work=lambda: work)

    orphan.refresh_from_db()
    assert orphan.status == 'successful'
    assert RecordingDispatcher.counters() == list(range(501, 20001))


@pytest.mark.django_db
def test_claimed_job_whose_adoption_never_ran_is_queued_again(settings):
    # 3.2 Claim committed, adoption never queued. ctrl-0 claims a lost controller's job and
    # publishes its adoption, but the adoption never runs: the message was lost, or ctrl-0's
    # dispatcher restarted first. The claim made the job ctrl-0's, so its next heartbeat
    # finds it orphaned and queues the adoption again, under a newer claim.
    configure(settings)
    make_cluster()
    job = Job.objects.create(
        controller_node=PEER, execution_node=EXEC, status='running', work_unit_id=UNIT, celery_task_id='peer-task', started=now() - timedelta(seconds=60)
    )

    assert job.id in heartbeat(THIS, mesh(EXEC))
    job.refresh_from_db()
    first_claim = job.celery_task_id
    assert job.controller_node == THIS

    assert job.id in heartbeat(THIS, mesh(EXEC))
    job.refresh_from_db()
    assert job.celery_task_id != first_claim, 'the earlier adoption, if it ever runs, finds it no longer owns the job'
    assert job.status == 'running'
