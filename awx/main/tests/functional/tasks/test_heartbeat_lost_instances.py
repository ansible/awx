"""The heartbeat's handling of instances it judges lost, and of the jobs they were running.

Most tests run a small cluster as rows in the test database (see awx.main.tests.adoption_cluster):
ctrl-0 runs the heartbeat, ctrl-1 is its peer and receptor-1 is the execution node.

Tests marked xfail reproduce a defect found on devel and assert the behavior it should have.
Each names its Jira bug; when the bug is fixed the test passes, strict xfail fails the run, and
the marker comes off.

``GRACE`` is CLUSTER_NODE_HEARTBEAT_PERIOD * CLUSTER_NODE_MISSED_HEARTBEAT_TOLERANCE.

``TIMEOUT`` is HADR_JOB_ADOPTION_TIMEOUT.
"""

from unittest import mock

import pytest
from django.utils.timezone import now, timedelta

from awx.main.models import ActivityStream, HostMetric, Instance, InstanceGroup, Job, JobEvent, JobTemplate, ProjectUpdate, WorkflowJob, WorkflowJobNode
from awx.main.tasks.system import (
    _heartbeat_instance_management,
    adopt_job,
    awx_receptor_workunit_reaper,
)
from awx.main.tests.adoption_cluster import (
    EXEC,
    GRACE,
    PEER,
    THIS,
    UNIT,
    adoption_env,
    assert_playbook_not_left_running,
    configure,
    heartbeat,
    make_cluster,
    mesh,
    run_lost_instance_handling,
    running_job,
    running_unit,
    save_dispatched_events,
    stats_event,
)
from awx.main.tests.fake_clock import FakeClock
from awx.main.tests.fake_receptor import FakeReceptorWork, FakeWorkUnit, RecordingDispatcher, make_events

TIMEOUT = 300


@pytest.fixture(autouse=True)
def cluster(settings, tmp_path):
    """The cluster's settings, with everything adoption touches outside the database patched."""
    configure(settings)
    settings.HADR_JOB_ADOPTION_TIMEOUT = TIMEOUT
    with adoption_env(settings, tmp_path):
        yield


@pytest.fixture
def heartbeat_settings(settings):
    settings.CLUSTER_HOST_ID = 'ctrl-0'
    settings.AWX_AUTO_DEPROVISION_INSTANCES = False
    settings.CLUSTER_NODE_HEARTBEAT_PERIOD = 60
    settings.CLUSTER_NODE_MISSED_HEARTBEAT_TOLERANCE = 2
    return settings


def control_node(hostname, last_seen):
    return Instance.objects.create(hostname=hostname, node_type='control', node_state='ready', last_seen=last_seen)


def lost_hostnames(clock):
    """Run ctrl-0's heartbeat at clock() and return the peers it judges lost.

    ctrl-0 is alive: its own last heartbeat was written by its own clock.
    """
    Instance.objects.filter(hostname='ctrl-0').update(last_seen=clock())
    ctl = mock.MagicMock()
    ctl.simple_command.return_value = {'KnownConnectionCosts': {'ctrl-0': {'ctrl-1': 1}}, 'Advertisements': []}
    with (
        mock.patch('awx.main.tasks.system.get_receptor_ctl', return_value=ctl),
        mock.patch('awx.main.tasks.system.inspect_execution_and_hop_nodes'),
        mock.patch.object(Instance, 'local_health_check'),
    ):
        _, _, lost, _ = _heartbeat_instance_management(clock)
    return sorted(inst.hostname for inst in lost)


@pytest.mark.django_db
@pytest.mark.parametrize(
    'peer_clock_ahead, lost_after',
    [
        pytest.param(timedelta(0), GRACE, id='peer-clock-in-sync'),
        pytest.param(timedelta(minutes=5), 5 * 60 + GRACE, id='peer-clock-fast-then-died'),
    ],
)
def test_peer_is_lost_only_after_the_grace_period(heartbeat_settings, peer_clock_ahead, lost_after):
    """A silent peer is lost one second past its last_seen plus the grace period.

    ``peer-clock-fast-then-died``: ctrl-1 ran five minutes fast and then died. Its last_seen is in the
    future, so a correct judge only finds it lost once real time passes last_seen plus the grace period.
    """
    t = now()
    control_node('ctrl-0', t)
    control_node('ctrl-1', t + peer_clock_ahead)
    clock = FakeClock(t)

    clock.advance(lost_after)
    assert lost_hostnames(clock) == []
    clock.advance(1)
    assert lost_hostnames(clock) == ['ctrl-1']


@pytest.mark.xfail(strict=True, reason='AAP-96827: a controller with a fast clock marks a healthy peer lost')
@pytest.mark.django_db
def test_judge_with_a_fast_clock_does_not_find_a_healthy_peer_lost(heartbeat_settings):
    """Clock skew. ctrl-0's clock runs five minutes fast, so its own last_seen is five minutes ahead.
    ctrl-1 heartbeated just now by the correct clock and is healthy. Today ctrl-0 judges it by its own
    clock and finds it lost.
    """
    t = now()
    control_node('ctrl-0', t + timedelta(minutes=5))
    control_node('ctrl-1', t)

    assert lost_hostnames(FakeClock(t + timedelta(minutes=5))) == []


def peer_job(**fields):
    """A job controlled by ctrl-1 and running on receptor-1."""
    fields.setdefault('work_unit_id', UNIT)
    return Job.objects.create(controller_node=PEER, execution_node=EXEC, status='running', celery_task_id='peer-task', **fields)


@pytest.fixture
def job_of_peer():
    return peer_job()


@pytest.mark.xfail(strict=True, reason='AAP-96824: a controller that misses heartbeats is judged lost while it still runs its job')
@pytest.mark.django_db
def test_slow_controller_still_on_the_mesh_keeps_its_job(job_of_peer):
    """Slow controller. ctrl-1 has missed two heartbeats but is still connected on the receptor mesh
    and still streaming its job. Today ctrl-0 judges it lost from last_seen alone and marks the live job
    failed.
    """
    make_cluster()

    run_lost_instance_handling(mesh(PEER, EXEC))

    job_of_peer.refresh_from_db()
    assert job_of_peer.status == 'running'


@pytest.mark.django_db
def test_controller_gone_from_the_mesh_has_its_job_reaped(job_of_peer):
    """The case the slow-controller test must not break: a controller that is silent and gone from the mesh
    is lost, and its job is no longer reported as running.
    """
    make_cluster()

    assert run_lost_instance_handling(mesh(EXEC)) == [PEER]

    job_of_peer.refresh_from_db()
    assert job_of_peer.status == 'failed'


@pytest.mark.xfail(strict=True, reason='AAP-96848: a slow controller\'s job first notifies failed with no hosts, then successful')
@pytest.mark.django_db
def test_slow_controller_job_sends_no_failed_notification(job_of_peer):
    """Notification content. The reap of a live controller's job sends a failed notification with no
    hosts; the job later ends successful and notifies again.
    """
    make_cluster()

    with mock.patch.object(Job, 'send_notification_templates') as send:
        run_lost_instance_handling(mesh(PEER, EXEC))

    assert mock.call('failed') not in send.call_args_list


def assert_left_with(job, controller, task_id):
    job.refresh_from_db()
    assert (job.status, job.controller_node, job.celery_task_id) == ('running', controller, task_id)


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
        pytest.param(redis_blip, id='self-unavailable'),
        pytest.param(hybrid_redis_blip, id='resume-hybrid'),
        pytest.param(deprovisioned, id='deprovision-live-controller'),
        pytest.param(disabled, id='disable-live-controller'),
        pytest.param(draining, id='drain-live-controller'),
    ],
)
@pytest.mark.django_db
def test_live_controller_keeps_its_running_job(change):
    """ctrl-0 is alive and still streaming its job, but something other than a missed
    heartbeat changed its record: one failed Redis ping marked it unavailable, it was deprovisioned,
    disabled or set to drain. Neither ctrl-0 itself nor its peer may take the job: a second stream
    duplicates its events and notifications.
    """
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


@pytest.mark.django_db
def test_owner_back_after_both_controllers_were_lost_adopts_its_job_once():
    """Both controllers lost. Both were down past the grace period. When ctrl-0 comes back, its job is
    queued for adoption once, and the adoption replays only the events not yet saved.
    """
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
    """Capacity of a returning controller. ctrl-0 restarts within the grace period. Its instance keeps
    its capacity through the restart, so its startup adoption is not refused for lack of room.
    """
    make_cluster(peer_seconds_since_seen=0)
    Instance.objects.filter(hostname=THIS).update(capacity=616, last_seen=now() - timedelta(seconds=30))
    job = running_job(THIS)

    queued = heartbeat(THIS, mesh(PEER, EXEC), startup=True)

    assert queued == [job.id]
    assert Instance.objects.get(hostname=THIS).capacity > 0


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
        pytest.param(disabled_node, id='disabled-node'),
        pytest.param(full_node, id='node-with-no-room'),
    ],
)
@pytest.mark.django_db
def test_node_without_room_does_not_take_a_lost_controllers_job(make_room):
    """ctrl-1 is lost while its job runs. ctrl-0 is disabled, or already at its capacity. The
    task manager would not place work on it, so it must not take ctrl-1's job either: the claim would
    sit with no room to run the adoption.
    """
    make_cluster()
    job = running_job(PEER, task_id='peer-task')
    fillers = make_room()

    queued = heartbeat(THIS, mesh(EXEC), running_task_ids=fillers)

    assert queued == []
    job.refresh_from_db()
    assert job.controller_node == PEER


@pytest.mark.django_db
def test_project_update_of_a_lost_controller_is_not_adopted(project):
    """Orphaned dependency. A project update runs on its controller, so when ctrl-1 is lost there is
    no work unit left to adopt and the update is reaped. It stays a failed dependency of the job
    waiting on it, which is what makes the task manager fail that job rather than start it.
    """
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
    assert update.status == 'failed'
    assert list(dependent.dependent_jobs.all()) == [update]


@pytest.mark.xfail(strict=True, reason='AAP-96836: canceling many orphaned jobs marks them failed one by one instead of canceled')
@pytest.mark.django_db
def test_canceled_orphans_of_a_lost_controller_end_canceled():
    """Canceling many orphans at once. Twenty jobs of a dead controller were canceled while it was
    down. Today they are marked failed, "Job reaped due to instance shutdown".
    """
    make_cluster()
    canceled = [peer_job(work_unit_id=f'unit-{n}', cancel_flag=True) for n in range(20)]

    run_lost_instance_handling(mesh(EXEC))

    statuses = {job.status for job in Job.objects.filter(pk__in=[j.pk for j in canceled])}
    assert statuses == {'canceled'}


@pytest.mark.xfail(strict=True, reason='AAP-96840: canceling a sliced job leaves the orphaned slice failed with its playbook running')
@pytest.mark.django_db
def test_canceled_slice_of_a_lost_controller_ends_canceled_and_stops():
    """Canceling a sliced job. The parent was canceled, so the orphaned slice has cancel_flag set.
    Today it ends failed and its playbook runs to the end.
    """
    make_cluster()
    job = peer_job(job_slice_number=1, job_slice_count=2, cancel_flag=True)
    work = running_unit()

    run_lost_instance_handling(mesh(EXEC), work=work)

    job.refresh_from_db()
    assert job.status == 'canceled'
    assert ('cancel', UNIT) in work.calls


def job_of_template_without_simultaneous_runs():
    return peer_job(job_template=JobTemplate.objects.create(name='same-hosts', allow_simultaneous=False))


def job_in_workflow():
    workflow = WorkflowJob.objects.create(name='outer', status='running')
    job = peer_job()
    WorkflowJobNode.objects.create(workflow_job=workflow, job=job)
    return job


def job_in_limited_instance_group():
    return peer_job(instance_group=InstanceGroup.objects.create(name='limited', max_concurrent_jobs=2))


def xfail(bug, summary):
    return pytest.mark.xfail(strict=True, reason=f'{bug}: {summary}')


def xfail_playbook_left_running(bug):
    return pytest.mark.xfail(strict=True, reason=f'{bug}: a reaped job leaves its playbook running')


@pytest.mark.parametrize(
    'make_job',
    [
        pytest.param(job_of_template_without_simultaneous_runs, id='AAP-96832-same-hosts', marks=xfail_playbook_left_running('AAP-96832')),
        pytest.param(job_in_workflow, id='AAP-96833-nested-workflow', marks=xfail_playbook_left_running('AAP-96833')),
        pytest.param(job_of_template_without_simultaneous_runs, id='AAP-96834-relaunch', marks=xfail_playbook_left_running('AAP-96834')),
        pytest.param(job_in_limited_instance_group, id='AAP-96837-instance-group-limit', marks=xfail_playbook_left_running('AAP-96837')),
        pytest.param(peer_job, id='AAP-96841-execution-node-capacity', marks=xfail_playbook_left_running('AAP-96841')),
        pytest.param(job_in_workflow, id='AAP-96844-workflow-branch', marks=xfail_playbook_left_running('AAP-96844')),
        pytest.param(job_in_workflow, id='AAP-96845-set-stats-artifacts', marks=xfail_playbook_left_running('AAP-96845')),
    ],
)
@pytest.mark.django_db
def test_reaped_job_does_not_leave_its_playbook_running(make_job):
    """ctrl-1 is lost while its job runs on receptor-1, which is still up. Today the job is marked failed
    and nothing cancels its work unit, so the playbook runs on unobserved: the next launch overlaps it,
    it stops counting toward instance group and execution node limits, and a workflow takes the failure
    branch for a playbook that succeeds. Either the unit is canceled when the job is marked failed, or the
    job stays active until the unit ends.
    """
    make_cluster()
    job = make_job()
    work = running_unit()

    run_lost_instance_handling(mesh(EXEC), work=work)

    assert_playbook_not_left_running(job, work)


@pytest.mark.django_db
def test_waiting_jobs_of_a_lost_controller_return_to_pending():
    """Jobs waiting when the controller dies. They had not started, so they go back to the task manager
    and run once, elsewhere.
    """
    make_cluster()
    waiting = Job.objects.create(controller_node=PEER, execution_node=EXEC, status='waiting')

    run_lost_instance_handling(mesh(EXEC))

    waiting.refresh_from_db()
    assert waiting.status == 'pending'
    assert waiting.controller_node == ''
    assert waiting.execution_node == ''


def failed_hosts_can_be_relaunched_on(job, hosts):
    assert sorted(job.retry_qs('failed').values_list('name', flat=True)) == ['rs-h2']


def host_metrics_are_recorded(job, hosts):
    assert sorted(HostMetric.objects.values_list('hostname', flat=True)) == sorted(hosts)


def hosts_point_at_the_job(job, hosts):
    assert {name: host.latest_job for name, host in hosts.items()} == dict.fromkeys(hosts, job)


@pytest.mark.parametrize(
    'saved',
    [
        pytest.param(
            failed_hosts_can_be_relaunched_on,
            id='AAP-96839-relaunch-on-failed-hosts',
            marks=xfail('AAP-96839', 'a reaped job cannot be relaunched on its failed hosts'),
        ),
        pytest.param(host_metrics_are_recorded, id='AAP-96846-host-metrics', marks=xfail('AAP-96846', 'a reaped job records no host metrics')),
        pytest.param(hosts_point_at_the_job, id='AAP-96847-host-pointers', marks=xfail('AAP-96847', 'a reaped job leaves hosts showing the previous job')),
    ],
)
@pytest.mark.django_db
def test_stats_of_a_reaped_job_are_saved_when_its_unit_finishes(me_inst, settings, inventory, saved):
    """The job was marked failed while its playbook ran on, and the playbook then finished. Its stats
    event, which writes host summaries, host metrics and each host's last job, is never read: the work
    unit reaper cancels and releases the finished unit. So relaunch on failed hosts has no summaries to
    use, the hosts count nothing, and they keep pointing at the previous job.

    The playbook ran on three hosts and failed on rs-h2. Each case checks the result its own bug is
    about, once the events the unit's results produced are saved.
    """
    settings.RECEPTOR_RELEASE_WORK = True
    hostnames = ['rs-h1', 'rs-h2', 'rs-h3']
    hosts = {name: inventory.hosts.create(name=name) for name in hostnames}
    job = Job.objects.create(
        controller_node=me_inst.hostname,
        execution_node=EXEC,
        status='failed',
        work_unit_id=UNIT,
        inventory=inventory,
        job_explanation='Job reaped due to instance shutdown',
    )
    work = FakeReceptorWork({UNIT: FakeWorkUnit(stats_event(make_events(5), hostnames, failed=['rs-h2']))})

    with (
        mock.patch('awx.main.tasks.system.get_receptor_ctl'),
        mock.patch('awx.main.tasks.system.ReceptorWork', return_value=work),
        mock.patch('awx.main.tasks.system.administrative_workunit_reaper'),
    ):
        awx_receptor_workunit_reaper()
    save_dispatched_events()

    saved(job, hosts)


@pytest.mark.xfail(strict=True, reason='AAP-96849: the activity stream does not record that a job was reaped')
@pytest.mark.django_db
def test_reap_is_recorded_in_the_activity_stream():
    """Activity stream. Nothing records that a lost controller's job was marked failed, so an auditor
    cannot tell a reaped job from one whose playbook failed.
    """
    make_cluster()
    job = Job.objects.create(controller_node=PEER, execution_node=EXEC, status='running', work_unit_id=UNIT)
    entries_before = ActivityStream.objects.filter(job=job).count()

    run_lost_instance_handling(mesh(EXEC))

    job.refresh_from_db()
    assert job.status == 'failed'
    assert ActivityStream.objects.filter(job=job).count() > entries_before
