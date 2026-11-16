"""Failure scenarios about the data a job leaves behind after adoption or a reap (write-up section 5).

Tests marked xfail reproduce a defect found on devel and assert the behavior it should have.
"""

import json
import os
from unittest import mock

import pytest

from django.utils.timezone import now

from awx.main.models import ActivityStream, InventorySource, InventoryUpdate, Job
from awx.main.tasks.adoption import invoke_adoption_hooks
from awx.main.tasks.receptor import reattach_to_work_unit
from awx.main.tasks.system import adopt_job, awx_receptor_workunit_reaper
from awx.main.tests.adoption_cluster import EXEC, PEER, UNIT, adoption_env, configure, make_cluster, mesh, run_lost_instance_handling
from awx.main.tests.fake_receptor import FakeReceptorWork, FakeWorkUnit, RecordingDispatcher, make_events


@pytest.fixture(autouse=True)
def env(settings, tmp_path):
    configure(settings)
    with adoption_env(settings, tmp_path):
        yield


def xfail(bug, summary):
    return pytest.mark.xfail(strict=True, reason=f'{bug}: {summary}')


# ── A reaped job's own result ─────────────────────────────────────────────────


@pytest.mark.parametrize(
    'bug',
    [
        pytest.param('AAP-96839', id='AAP-96839-relaunch-on-failed-hosts', marks=xfail('AAP-96839', 'a reaped job cannot be relaunched on its failed hosts')),
        pytest.param('AAP-96846', id='AAP-96846-host-metrics', marks=xfail('AAP-96846', 'a reaped job records no host metrics')),
        pytest.param('AAP-96847', id='AAP-96847-host-pointers', marks=xfail('AAP-96847', 'a reaped job leaves hosts showing the previous job')),
    ],
)
@pytest.mark.django_db
def test_stats_of_a_reaped_job_are_saved_when_its_unit_finishes(me_inst, settings, bug):
    # 4.20, 5.10, 5.12. The job was marked failed while its playbook ran on, and the
    # playbook then finished. Its stats event, which writes host summaries, host metrics
    # and each host's last job, is never read: the work unit reaper cancels and releases
    # the finished unit. So relaunch on failed hosts has no summaries to use, the hosts
    # count nothing, and they keep pointing at the previous job.
    settings.RECEPTOR_RELEASE_WORK = True
    Job.objects.create(
        controller_node=me_inst.hostname, execution_node=EXEC, status='failed', work_unit_id=UNIT, job_explanation='Job reaped due to instance shutdown'
    )
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10))})

    with (
        mock.patch('awx.main.tasks.system.get_receptor_ctl'),
        mock.patch('awx.main.tasks.system.ReceptorWork', return_value=work),
        mock.patch('awx.main.tasks.system.administrative_workunit_reaper'),
    ):
        awx_receptor_workunit_reaper()

    assert 'playbook_on_stats' in [event.get('event') for event in RecordingDispatcher.dispatched]


# ── Host ids on replayed events ───────────────────────────────────────────────


def host_events(hostnames):
    """Runner events for one task on each host, then the stats event."""
    events = make_events(len(hostnames) + 2)
    for event, hostname in zip(events[1:-1], hostnames):
        event['event_data'] = {'host': hostname}
    return events


def _orphaned_job_over_five_hosts(me_inst, inventory, original_controller):
    hosts = {name: inventory.hosts.create(name=name) for name in ('fp-h1', 'fp-h2', 'fp-h3', 'fp-h4', 'fp-h5')}
    job = Job.objects.create(
        controller_node=original_controller or me_inst.hostname,
        status='running',
        started=now(),
        work_unit_id=UNIT,
        inventory=inventory,
        job_env={'host_count': len(hosts)},
    )
    if original_controller:
        # The claim a peer controller makes before publishing adopt_job_async: controller_node
        # is rewritten to the claiming node before adopt_job ever runs.
        job.controller_node = me_inst.hostname
        job.save(update_fields=['controller_node'])
    return hosts, job


def _adopt(job, hosts):
    work = FakeReceptorWork({UNIT: FakeWorkUnit(host_events(list(hosts)))})
    adopt_job(job.id, open_work=lambda: work)
    return work


def _replayed_host_ids(job, hosts):
    _adopt(job, hosts)
    return {event['host_name']: event.get('host_id') for event in RecordingDispatcher.dispatched if event.get('host_name')}


@pytest.mark.parametrize('original_controller', [None, PEER], ids=['same-node-resume', 'cross-controller-claim'])
@pytest.mark.django_db
def test_replayed_events_keep_the_host_ids_of_an_unchanged_inventory(me_inst, inventory, original_controller):
    # 5.2 Host map. A normal run saves the inventory's host count when the job starts. If the
    # inventory is unchanged when the job is adopted, adoption rebuilds the host map from it and
    # replayed events carry the ids the job started with. reattach_to_work_unit is one function
    # shared by every adoption path, so the cross-controller claim is covered here too.
    hosts, job = _orphaned_job_over_five_hosts(me_inst, inventory, original_controller)

    assert _replayed_host_ids(job, hosts) == {name: host.id for name, host in hosts.items()}


@pytest.mark.parametrize('original_controller', [None, PEER], ids=['same-node-resume', 'cross-controller-claim'])
@pytest.mark.django_db
def test_replayed_events_of_a_changed_inventory_carry_no_host_ids(me_inst, inventory, original_controller):
    # 5.2 Host map after an inventory change. The ids saved at start can no longer be told apart
    # from the inventory's, so adoption does not guess: while the job was orphaned a host was
    # deleted, one was recreated under the same name and one was disabled, and no replayed event
    # gets a host id (AAP-100937).
    hosts, job = _orphaned_job_over_five_hosts(me_inst, inventory, original_controller)

    hosts['fp-h2'].delete()
    hosts['fp-h3'].delete()
    inventory.hosts.create(name='fp-h3')
    hosts['fp-h4'].enabled = False
    hosts['fp-h4'].save()

    assert _replayed_host_ids(job, hosts) == {name: None for name in hosts}


def _change_the_inventory(inventory, hosts):
    hosts['fp-h2'].delete()


@pytest.mark.django_db
def test_a_job_whose_inventory_changed_runs_to_the_end_and_fails(me_inst, inventory):
    # 5.2 Host map, AAP-100937. The unit is not stopped, its output is replayed (with no host
    # ids), and the job ends failed with the reason, so no host result lands on the wrong host.
    hosts, job = _orphaned_job_over_five_hosts(me_inst, inventory, None)
    _change_the_inventory(inventory, hosts)

    with mock.patch('awx.main.tasks.receptor.invoke_adoption_hooks', wraps=invoke_adoption_hooks) as hooks:
        work = _adopt(job, hosts)

    job.refresh_from_db()
    assert job.status == 'failed'
    assert 'could not be matched to the inventory' in job.job_explanation
    assert 'hosts were added or removed' in job.job_explanation
    assert ('cancel', UNIT) not in work.calls
    assert hooks.call_args.args[3] == 'failed'  # post-run hooks, and the fact cache with them, only run for 'successful'
    assert [event for event in RecordingDispatcher.dispatched if event.get('host_name')]


@pytest.mark.django_db
def test_a_pod_attached_by_a_new_unit_is_left_to_finish_and_the_job_failed(me_inst, inventory):
    hosts, job = _orphaned_job_over_five_hosts(me_inst, inventory, None)
    _change_the_inventory(inventory, hosts)
    work = FakeReceptorWork({UNIT: FakeWorkUnit(host_events(list(hosts)))})

    reattach_to_work_unit(job, work, pod_name='automation-job-1-abcde')

    job.refresh_from_db()
    assert job.status == 'failed'
    assert 'hosts were added or removed' in job.job_explanation
    assert ('cancel', UNIT) not in work.calls


@pytest.mark.django_db
def test_a_job_whose_inventory_is_unchanged_is_adopted_as_before(me_inst, inventory):
    hosts, job = _orphaned_job_over_five_hosts(me_inst, inventory, None)

    work = _adopt(job, hosts)

    job.refresh_from_db()
    assert job.status == 'successful'
    assert 'could not be matched' not in job.job_explanation
    assert ('cancel', UNIT) not in work.calls


@pytest.mark.django_db
def test_a_job_canceled_while_orphaned_stays_canceled_when_its_inventory_changed(me_inst, inventory):
    hosts, job = _orphaned_job_over_five_hosts(me_inst, inventory, None)
    job.cancel_flag = True
    job.save(update_fields=['cancel_flag'])
    _change_the_inventory(inventory, hosts)

    work = _adopt(job, hosts)

    job.refresh_from_db()
    assert job.status == 'canceled'
    assert 'could not be matched' not in job.job_explanation
    assert work.calls.count(('cancel', UNIT)) == 1  # the cancel flag's own, not a second one


# ── What records a reap ───────────────────────────────────────────────────────


@pytest.mark.xfail(strict=True, reason='AAP-96849: the activity stream does not record that a job was reaped')
@pytest.mark.django_db
def test_reap_is_recorded_in_the_activity_stream():
    # 5.16 Activity stream. Nothing records that a lost controller's job was marked
    # failed, so an auditor cannot tell a reaped job from one whose playbook failed. A
    # job that ran on its controller is still reaped when that hybrid node is lost: its
    # playbook went down with it, so there is nothing to adopt.
    make_cluster()
    job = Job.objects.create(controller_node=PEER, execution_node=PEER, status='running', work_unit_id=UNIT)
    entries_before = ActivityStream.objects.filter(job=job).count()

    run_lost_instance_handling(mesh(EXEC))

    job.refresh_from_db()
    assert job.status == 'failed'
    assert ActivityStream.objects.filter(job=job).count() > entries_before


# ── Files left on disk ────────────────────────────────────────────────────────


@pytest.mark.xfail(strict=True, reason='AAP-96852: a resumed job\'s original private data directory stays on disk after it ends')
@pytest.mark.django_db
def test_resumed_job_removes_its_original_private_data_dir(me_inst, settings):
    # 5.20 Credentials left on disk. The job's private data directory from before the
    # restart holds its inventory and extra variables. Adoption works in a new directory
    # and removes only that one, so the original stays until cleanup_images_and_files,
    # which runs every 3 hours, finds it older than 60 minutes.
    job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id=UNIT)
    original = os.path.join(settings.AWX_ISOLATION_BASE_PATH, f'awx_{job.pk}_before_restart')
    os.makedirs(os.path.join(original, 'env'))
    with open(os.path.join(original, 'env', 'extravars'), 'w') as f:
        json.dump({'survey_password': 'secret'}, f)
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10))})

    adopt_job(job.id, open_work=lambda: work)

    job.refresh_from_db()
    assert job.status == 'successful'
    assert not os.path.exists(original), f'{original} is still on disk'


# ── What a job's playbook leaves in its artifacts ─────────────────────────────


def _fact_cache_job(me_inst, inventory):
    host = inventory.hosts.create(name='fc-h1')
    job = Job.objects.create(
        controller_node=me_inst.hostname,
        status='running',
        started=now(),
        work_unit_id=UNIT,
        inventory=inventory,
        use_fact_cache=True,
        job_env={'host_count': 1},
    )
    facts = {'ansible_distribution': 'RedHat'}
    artifacts = {
        # Written before the playbook ran, so older than the facts it then gathered.
        'host_cache_summary.json': (json.dumps({'last_write_time': 0, 'hosts_cached': {host.name: False}}), 60),
        f'fact_cache/{host.name}': json.dumps(facts),
    }
    return host, job, facts, FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10), artifacts=artifacts)})


@pytest.mark.django_db
def test_adopted_job_saves_the_facts_its_playbook_gathered(me_inst, inventory):
    # 5.4 Fact caching. The playbook gathered facts after the controller restarted; they
    # come back in the unit's artifacts, and the adopter saves them on the hosts as a
    # normal run would.
    host, job, facts, work = _fact_cache_job(me_inst, inventory)

    adopt_job(job.id, open_work=lambda: work)

    job.refresh_from_db()
    host.refresh_from_db()
    assert job.status == 'successful'
    assert host.ansible_facts == facts


@pytest.mark.django_db
def test_adopted_job_whose_inventory_changed_saves_no_facts(me_inst, inventory):
    # 5.4 + 5.2. The facts would go to a host that may now be another one, so the job fails and
    # the post-run hooks, the fact cache with them, never run.
    host, job, facts, work = _fact_cache_job(me_inst, inventory)
    inventory.hosts.create(name='fc-h2')

    adopt_job(job.id, open_work=lambda: work)

    job.refresh_from_db()
    host.refresh_from_db()
    assert job.status == 'failed'
    assert not host.ansible_facts


@pytest.mark.django_db
def test_adopted_inventory_update_imports_what_it_discovered(me_inst, inventory):
    # 5.4 Other job types. An inventory update's result is the inventory it discovered,
    # left in its artifacts as output.json; the adopter imports it as a normal run would.
    source = InventorySource.objects.create(name='src', inventory=inventory, source='ec2')
    update = InventoryUpdate.objects.create(
        inventory_source=source, inventory=inventory, source='ec2', controller_node=me_inst.hostname, status='running', work_unit_id=UNIT
    )
    discovered = {'all': {'hosts': ['iu-h1']}, '_meta': {'hostvars': {'iu-h1': {}}}}
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(3), artifacts={'output.json': json.dumps(discovered)})})

    adopt_job(update.id, open_work=lambda: work)

    update.refresh_from_db()
    assert update.status == 'successful', update.job_explanation
    assert inventory.hosts.filter(name='iu-h1').exists()
