"""Failure scenarios devel already handles correctly, kept as regression guards.

Each test asserts what devel does today in a scenario where cross-controller adoption
(AAP-89602) has been seen to go wrong: a peer taking a live controller's job, a node
claiming work it has no room for, an unreachable work unit finishing a job twice, or
replayed output that differs from a normal run. They pass on devel, so a change that
breaks one of them reintroduces a failure found with the failpoint harness.

Heartbeats run through cluster_node_heartbeat, the dispatcher's entry point, so any
new path it gains (an orphan sweep, for example) runs in these tests too.
"""

import pytest
from django.utils.timezone import now, timedelta

from awx.api.versioning import reverse

from awx.main.models import Instance, Inventory, Job, JobEvent, ProjectUpdate
from awx.main.tasks.system import adopt_job
from awx.main.tests.adoption_cluster import (
    EXEC,
    GRACE,
    PEER,
    THIS,
    UNIT,
    adoption_env,
    configure,
    heartbeat,
    make_cluster,
    mesh,
    save_dispatched_events,
)
from awx.main.tests.fake_clock import FakeClock
from awx.main.tests.fake_receptor import FakeReceptorWork, FakeWorkUnit, RecordingDispatcher, make_events

TIMEOUT = 300  # HADR_JOB_ADOPTION_TIMEOUT


@pytest.fixture(autouse=True)
def env(settings, tmp_path):
    configure(settings)
    settings.HADR_JOB_ADOPTION_TIMEOUT = TIMEOUT
    with adoption_env(settings, tmp_path):
        yield


def running_job(controller, execution_node=EXEC, task_id='job-task', **fields):
    fields.setdefault('work_unit_id', UNIT)
    return Job.objects.create(
        controller_node=controller,
        execution_node=execution_node,
        status='running',
        celery_task_id=task_id,
        started=now() - timedelta(seconds=60),
        **fields,
    )


def assert_left_with(job, controller, task_id):
    job.refresh_from_db()
    assert (job.status, job.controller_node, job.celery_task_id) == ('running', controller, task_id)


# ── A live controller keeps its job ───────────────────────────────────────────


def redis_blip(this):
    return False


def hybrid_redis_blip(this):
    Instance.objects.filter(pk=this.pk).update(node_type='hybrid')
    return False


def deprovisioned(this):
    this.delete()
    return True


def disabled(this):
    Instance.objects.filter(pk=this.pk).update(enabled=False)
    return True


def draining(this):
    Instance.objects.filter(pk=this.pk).update(node_state='deprovisioning')
    return True


@pytest.mark.parametrize(
    'change',
    [
        pytest.param(redis_blip, id='2.2-self-unavailable'),
        pytest.param(hybrid_redis_blip, id='2.3-resume-hybrid'),
        pytest.param(deprovisioned, id='2.4-deprovision-live-controller'),
        pytest.param(disabled, id='4.8-disable-live-controller'),
        pytest.param(draining, id='4.8-drain-live-controller'),
    ],
)
@pytest.mark.django_db
def test_live_controller_keeps_its_running_job(change):
    # 2.2, 2.3, 2.4, 4.8. ctrl-0 is alive and still streaming its job, but something
    # other than a missed heartbeat changed its record: one failed Redis ping marked it
    # unavailable, it was deprovisioned, disabled or set to drain. Neither ctrl-0 itself
    # nor its peer may take the job: a second stream duplicates its events and
    # notifications.
    this, _ = make_cluster(peer_seconds_since_seen=0)
    hybrid = change is hybrid_redis_blip
    job = running_job(THIS, execution_node=THIS if hybrid else EXEC)
    redis_up = change(this)

    queued = []
    if Instance.objects.filter(hostname=THIS).exists():
        queued += heartbeat(THIS, mesh(PEER, EXEC), running_task_ids=['job-task'], redis_up=redis_up)
    for _ in range(3):
        queued += heartbeat(PEER, mesh(THIS, EXEC))

    assert queued == []
    assert_left_with(job, THIS, 'job-task')


# ── A controller coming back ──────────────────────────────────────────────────


@pytest.mark.django_db
def test_owner_back_after_both_controllers_were_lost_adopts_its_job_once():
    # 2.5 Both controllers lost. Both were down past the grace period. When ctrl-0 comes
    # back, its job is queued for adoption once, and the adoption replays only the
    # events not yet saved.
    t = now()
    Instance.objects.create(hostname=THIS, node_type='control', node_state='ready', capacity=100, last_seen=t - timedelta(seconds=GRACE + 30))
    Instance.objects.create(hostname=PEER, node_type='control', node_state='ready', capacity=100, last_seen=t - timedelta(seconds=GRACE + 30))
    Instance.objects.create(hostname=EXEC, node_type='execution', node_state='ready', last_seen=t)
    job = running_job(THIS)
    for counter in range(1, 13):
        JobEvent.objects.create(job=job, counter=counter, event='runner_on_ok', job_created=job.created)

    queued = heartbeat(THIS, mesh(EXEC), startup=True)
    queued += heartbeat(THIS, mesh(EXEC))

    assert queued == [job.id]
    adopt_job(job.id, open_work=lambda: FakeReceptorWork({UNIT: FakeWorkUnit(make_events(30))}))
    job.refresh_from_db()
    assert job.status == 'successful'
    assert RecordingDispatcher.counters() == list(range(13, 31))


@pytest.mark.django_db
def test_restarted_controller_keeps_its_capacity_and_adopts_its_job():
    # 4.19 Capacity of a returning controller. ctrl-0 restarts within the grace period.
    # Its instance keeps its capacity through the restart, so its startup adoption is
    # not refused for lack of room.
    make_cluster(peer_seconds_since_seen=0)
    Instance.objects.filter(hostname=THIS).update(capacity=616, last_seen=now() - timedelta(seconds=30))
    job = running_job(THIS)

    queued = heartbeat(THIS, mesh(PEER, EXEC), startup=True)

    assert queued == [job.id]
    assert Instance.objects.get(hostname=THIS).capacity > 0


# ── Claims a node must not make ───────────────────────────────────────────────


def disabled_node():
    Instance.objects.filter(hostname=THIS).update(enabled=False, capacity=0)
    return []


def full_node():
    Instance.objects.filter(hostname=THIS).update(capacity=1)
    for n in range(2):
        running_job(THIS, task_id=f'filler-{n}', work_unit_id=f'filler-unit-{n}', task_impact=1)
    return ['filler-0', 'filler-1']


@pytest.mark.parametrize(
    'make_room',
    [
        pytest.param(disabled_node, id='4.3-disabled-node'),
        pytest.param(full_node, id='4.9-node-with-no-room'),
    ],
)
@pytest.mark.django_db
def test_node_without_room_does_not_take_a_lost_controllers_job(make_room):
    # 4.3, 4.9. ctrl-1 is lost while its job runs. ctrl-0 is disabled, or already at its
    # capacity. The task manager would not place work on it, so it must not take ctrl-1's
    # job either: the claim would sit with no room to run the adoption.
    make_cluster()
    job = running_job(PEER, task_id='peer-task')
    fillers = make_room()

    queued = heartbeat(THIS, mesh(EXEC), running_task_ids=fillers)

    assert queued == []
    job.refresh_from_db()
    assert job.controller_node == PEER


@pytest.mark.django_db
def test_project_update_of_a_lost_controller_is_not_adopted(project):
    # 4.10 Orphaned dependency. A project update runs on its controller, so when ctrl-1
    # is lost there is no work unit left to adopt. The job waiting on the update must
    # not start while the update is unresolved.
    make_cluster()
    update = ProjectUpdate.objects.create(
        project=project, status='running', controller_node=PEER, execution_node=PEER, celery_task_id='update-task', work_unit_id='update-unit'
    )
    dependent = Job.objects.create(status='pending', project=project)
    dependent.dependent_jobs.add(update)

    queued = heartbeat(THIS, mesh(EXEC))

    assert queued == []
    update.refresh_from_db()
    assert update.controller_node == PEER
    dependent.refresh_from_db()
    assert dependent.status == 'pending'


# ── An unreachable work unit ──────────────────────────────────────────────────


@pytest.mark.django_db
def test_unreachable_unit_is_waited_for_then_failed_once(me_inst):
    # 3.9 Adopter can't reach the execution node. While the unit can't be read, adoption
    # waits: the job stays running and the unit is kept. Past the adoption deadline the
    # job is failed. Once failed, a later adoption that can reach the unit again must not
    # replay it into a second result.
    clock = FakeClock()
    job = running_job(me_inst.hostname)
    unit = FakeWorkUnit(make_events(10), status_error=RuntimeError('no route to receptor-1'))
    work = FakeReceptorWork({UNIT: unit})

    for _ in range(2):
        adopt_job(job.id, open_work=lambda: work, clock=clock)
        clock.advance(60)
    job.refresh_from_db()
    assert job.status == 'running'
    assert ('release', UNIT) not in work.calls

    clock.advance(TIMEOUT)
    adopt_job(job.id, open_work=lambda: work, clock=clock)
    unit.status_error = None
    adopt_job(job.id, open_work=lambda: work, clock=clock)

    job.refresh_from_db()
    assert job.status == 'failed'
    assert RecordingDispatcher.dispatched == []


# ── Deleting an orphaned job ──────────────────────────────────────────────────


@pytest.mark.django_db
def test_orphaned_job_and_its_inventory_cannot_be_deleted(delete, admin_user, inventory):
    # 3.11 Deleting the job or inventory during adoption. A job whose controller is lost
    # is still running, so the API refuses to delete it or its inventory.
    make_cluster()
    job = running_job(PEER, inventory=inventory)

    delete(reverse('api:job_detail', kwargs={'pk': job.pk}), admin_user, expect=403)
    delete(reverse('api:inventory_detail', kwargs={'pk': inventory.pk}), admin_user, expect=409)


# ── What an adopted job records ───────────────────────────────────────────────


@pytest.mark.xfail(strict=True, reason='devel: an adopted job that timed out does not say so (bug not filed yet)')
@pytest.mark.django_db
def test_adopted_job_that_timed_out_says_so(me_inst):
    # 4.2 Job timeout while orphaned. The timeout is enforced on the execution node, so
    # the unit ends with runner status "timeout". The adopted job must say it timed out,
    # as a normal run does, so an operator can tell a timeout from a playbook failure.
    job = running_job(me_inst.hostname)
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10), status='timeout', state='Failed')})

    adopt_job(job.id, open_work=lambda: work)

    job.refresh_from_db()
    assert job.status == 'failed'
    assert 'timeout' in job.job_explanation


def stats_event(events, hostnames, failed=()):
    events[-1]['event_data'] = {
        'ok': {name: 1 for name in hostnames if name not in failed},
        'failures': {name: 1 for name in failed},
        'changed': {},
        'dark': {},
        'processed': {name: 1 for name in hostnames},
        'skipped': {},
    }
    return events


@pytest.mark.django_db
def test_adopted_slice_maps_only_its_own_hosts(me_inst, inventory):
    # 5.3 Job slicing. Slice 1 of 2 over five hosts runs fp-h1, fp-h3 and fp-h5. The
    # host map adoption rebuilds, which the stats event carries into host summaries,
    # holds that share of the inventory and no other.
    hosts = {name: inventory.hosts.create(name=name) for name in ('fp-h1', 'fp-h2', 'fp-h3', 'fp-h4', 'fp-h5')}
    job = running_job(me_inst.hostname, inventory=inventory, job_slice_number=1, job_slice_count=2)
    work = FakeReceptorWork({UNIT: FakeWorkUnit(stats_event(make_events(5), ['fp-h1', 'fp-h3', 'fp-h5']))})

    adopt_job(job.id, open_work=lambda: work)

    stats = next(event for event in RecordingDispatcher.dispatched if event.get('event') == 'playbook_on_stats')
    assert stats['host_map'] == {name: hosts[name].id for name in ('fp-h1', 'fp-h3', 'fp-h5')}


@pytest.mark.django_db
def test_adopted_job_updates_host_pointers_and_inventory_counts(me_inst, inventory):
    # 5.11 Host pointers and inventory counts. After an adopted job's stats are saved,
    # each host points at this job, only the failed host is flagged, and the inventory's
    # counts are recomputed, as after a normal run.
    hostnames = ['dc-h1', 'dc-h2', 'dc-h3']
    hosts = {name: inventory.hosts.create(name=name) for name in hostnames}
    job = running_job(me_inst.hostname, inventory=inventory)
    work = FakeReceptorWork({UNIT: FakeWorkUnit(stats_event(make_events(5), hostnames, failed=['dc-h2']))})

    adopt_job(job.id, open_work=lambda: work)
    save_dispatched_events()

    for name, host in hosts.items():
        assert host.latest_job == job, name
        assert host.latest_summary.failed == (name == 'dc-h2'), name
    inventory.refresh_from_db()
    assert (inventory.total_hosts, inventory.hosts_with_active_failures, inventory.has_active_failures) == (3, 1, True)


@pytest.mark.django_db
def test_adopted_job_maps_constructed_hosts_like_a_normal_run(me_inst, inventory, organization):
    # 5.13 Constructed inventories. A job on a constructed inventory maps each host name
    # to the constructed host, as a normal run does.
    source = inventory.hosts.create(name='ci-h1')
    constructed = Inventory.objects.create(name='constructed', kind='constructed', organization=organization)
    constructed.input_inventories.add(inventory)
    constructed_host = constructed.hosts.create(name='ci-h1', instance_id=str(source.id))
    job = running_job(me_inst.hostname, inventory=constructed)
    work = FakeReceptorWork({UNIT: FakeWorkUnit(stats_event(make_events(3), ['ci-h1']))})

    adopt_job(job.id, open_work=lambda: work)

    stats = next(event for event in RecordingDispatcher.dispatched if event.get('event') == 'playbook_on_stats')
    assert stats['host_map'] == {'ci-h1': constructed_host.id}


@pytest.mark.django_db
def test_adopted_job_output_has_no_gaps_or_overlaps(me_inst):
    # 5.14 Stdout line numbers. The adopter replays the runner's own stream, so once the
    # replayed events are saved the job's output covers every line once, in order.
    job = running_job(me_inst.hostname)
    events = make_events(40)
    for event in events[:12]:
        JobEvent.objects.create(job=job, job_created=job.created, **{k: event[k] for k in ('counter', 'event', 'stdout', 'start_line', 'end_line', 'uuid')})
    work = FakeReceptorWork({UNIT: FakeWorkUnit(events)})

    adopt_job(job.id, open_work=lambda: work)
    save_dispatched_events()

    saved = list(JobEvent.objects.filter(job=job).order_by('start_line').values_list('counter', 'start_line', 'end_line'))
    assert [counter for counter, _, _ in saved] == list(range(1, 41))
    assert all(saved[i][2] == saved[i + 1][1] for i in range(len(saved) - 1))


@pytest.mark.django_db
def test_events_deleted_during_replay_stay_deleted(me_inst):
    # 5.21 Event cleanup during replay. The job's saved events are deleted after the
    # adopter read what was already saved. The replay skips everything at or below that
    # point, so the deleted events stay deleted, and the job still finishes.
    job = running_job(me_inst.hostname)
    for counter in range(1, 25):
        JobEvent.objects.create(job=job, counter=counter, event='runner_on_ok', job_created=job.created)
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(82))})
    real_results = work.results

    def cleanup_then_results(unit_id, startpos=None):
        JobEvent.objects.filter(job_id=job.id).delete()
        return real_results(unit_id, startpos)

    work.results = cleanup_then_results
    adopt_job(job.id, open_work=lambda: work)

    job.refresh_from_db()
    assert job.status == 'successful'
    assert RecordingDispatcher.counters() == list(range(25, 83))
