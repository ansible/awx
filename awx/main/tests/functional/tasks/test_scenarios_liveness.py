"""Failure scenarios about when a controller is really gone (write-up section 2).

Tests marked xfail reproduce a defect found on devel and assert the behavior it should
have. Each names its Jira bug; when the bug is fixed the test passes, strict xfail fails
the run, and the marker comes off.
"""

from unittest import mock

import pytest
from django.utils.timezone import now, timedelta

from awx.main.models import Instance, Job
from awx.main.tests.adoption_cluster import EXEC, GRACE, PEER, THIS, UNIT, configure, make_cluster, mesh, run_lost_instance_handling


@pytest.fixture(autouse=True)
def cluster_settings(settings):
    configure(settings)


@pytest.fixture
def peer_job():
    """A job controlled by ctrl-1 and running on receptor-1."""
    return Job.objects.create(controller_node=PEER, execution_node=EXEC, status='running', work_unit_id=UNIT, celery_task_id='peer-task')


@pytest.mark.django_db
def test_slow_controller_still_on_the_mesh_keeps_its_job(peer_job):
    # 2.1 Slow controller. ctrl-1 has missed two heartbeats but is still connected on the
    # receptor mesh and still streaming its job. ctrl-0 judges it lost from last_seen
    # alone: devel marks the live job failed, and cross-controller adoption takes it over
    # instead. Either way ctrl-1 loses a job it is still running.
    make_cluster()

    run_lost_instance_handling(mesh(PEER, EXEC))

    peer_job.refresh_from_db()
    assert peer_job.status == 'running'
    assert peer_job.controller_node == PEER


@pytest.mark.django_db
def test_control_peer_on_the_mesh_is_not_handled_as_lost(peer_job):
    make_cluster()

    assert run_lost_instance_handling(mesh(PEER, EXEC)) == []


@pytest.mark.django_db
def test_unreadable_mesh_keeps_the_last_seen_judgement(peer_job):
    make_cluster()

    assert run_lost_instance_handling(None) == [PEER]


@pytest.mark.django_db
def test_kubernetes_control_peer_on_the_mesh_keeps_the_last_seen_judgement(settings, peer_job):
    # K8s control pods are not peered on the mesh, so mesh presence says nothing about them.
    settings.IS_K8S = True
    make_cluster()

    assert run_lost_instance_handling(mesh(PEER, EXEC)) == [PEER]


@pytest.mark.django_db
def test_controller_gone_from_the_mesh_has_its_job_adopted(peer_job):
    # The case the slow-controller test must not break: a controller that is silent and
    # gone from the mesh is lost. Its job ran on receptor-1, which is still up, so ctrl-0
    # takes it over rather than reporting it failed.
    make_cluster()

    assert run_lost_instance_handling(mesh(EXEC)) == [PEER]

    peer_job.refresh_from_db()
    assert peer_job.status == 'running'
    assert peer_job.controller_node == THIS


@pytest.mark.django_db
def test_hung_dispatcher_control_peer_eventually_loses_its_job(peer_job, settings):
    # A regression from cd85ff2e03 (AAP-96824). ctrl-1's receptor stays up, so it
    # keeps its mesh connection, but its dispatcher is hung: nothing on ctrl-1 writes its
    # last_seen or runs the health check that would mark it unavailable. Unbounded mesh
    # presence protects it forever, unlike the slow-controller case, which is only a few
    # missed heartbeats. Past HADR_JOB_ADOPTION_TIMEOUT the mesh must stop protecting it, so
    # its job is taken over instead of staying stranded.
    settings.HADR_JOB_ADOPTION_TIMEOUT = 300
    make_cluster(peer_seconds_since_seen=GRACE + settings.HADR_JOB_ADOPTION_TIMEOUT + 60)

    assert run_lost_instance_handling(mesh(PEER, EXEC)) == [PEER]

    peer_job.refresh_from_db()
    assert peer_job.status == 'running'
    assert peer_job.controller_node == THIS


@pytest.mark.django_db
def test_slow_controller_job_sends_no_failed_notification(peer_job):
    # 5.15 Notification content (AAP-96848). On devel the reap of a live controller's job
    # sends a failed notification with no hosts; the job later ends successful and
    # notifies again. Taking the job over sends nothing; only its final status notifies.
    make_cluster()

    with mock.patch.object(Job, 'send_notification_templates') as send:
        run_lost_instance_handling(mesh(PEER, EXEC))

    assert mock.call('failed') not in send.call_args_list


@pytest.mark.django_db
def test_execution_node_still_on_the_mesh_keeps_its_jobs():
    # 2.11 False lost-node report. receptor-1 missed its check-ins, so its last_seen is
    # stale, but ctrl-0 is still connected to it on the mesh and ctrl-0's own job is still
    # running there. The mesh gate defers only control nodes, so receptor-1 is handled as
    # lost; the job is ctrl-0's own, so the reap leaves it to ctrl-0's run task.
    make_cluster()
    Instance.objects.filter(hostname=EXEC).update(last_seen=now() - timedelta(seconds=GRACE + 600))
    job = Job.objects.create(controller_node=THIS, execution_node=EXEC, status='running', work_unit_id=UNIT, celery_task_id='job-task', started=now())

    run_lost_instance_handling(mesh(PEER, EXEC))

    job.refresh_from_db()
    assert job.status == 'running'


def routed(*nodes):
    """Receptor status as ctrl-0 sees it, with a route to each node in nodes."""
    return {**mesh(PEER, EXEC), 'RoutingTable': {node: {'NextHop': node, 'Cost': 1} for node in nodes}}


@pytest.fixture
def peer_job_on_stale_exec(peer_job):
    """ctrl-1 is healthy and runs a job on receptor-1, whose last_seen is long past the grace period."""
    make_cluster(peer_seconds_since_seen=0)
    Instance.objects.filter(hostname=EXEC).update(last_seen=now() - timedelta(seconds=GRACE + 600))
    return peer_job


@pytest.mark.django_db
def test_peer_job_on_execution_node_with_a_route_is_not_reaped(peer_job_on_stale_exec):
    # 2.11 False lost-node report, another controller's job (AAP-99475). receptor-1's last_seen is
    # stale but ctrl-0 has a route to it, so it is not lost; reaping ctrl-1's job there kills a
    # playbook that is still running (cluster false-lost, jobs 1058 and 1059).
    assert run_lost_instance_handling(routed(THIS, PEER, EXEC)) == []

    peer_job_on_stale_exec.refresh_from_db()
    assert peer_job_on_stale_exec.status == 'running'
    assert peer_job_on_stale_exec.controller_node == PEER
    assert Instance.objects.get(hostname=EXEC).node_state == 'ready'


@pytest.mark.django_db
def test_peer_job_on_execution_node_without_a_route_is_reaped(peer_job_on_stale_exec):
    # The route is what keeps a node alive: with no route to receptor-1 the stale last_seen is believed.
    assert run_lost_instance_handling(routed(THIS, PEER)) == [EXEC]

    peer_job_on_stale_exec.refresh_from_db()
    assert peer_job_on_stale_exec.status == 'failed'


@pytest.mark.django_db
def test_unreadable_routing_table_keeps_the_last_seen_judgement_for_an_execution_node(peer_job_on_stale_exec):
    # No table says nothing about the node, so only the declining checks may rely on it.
    assert run_lost_instance_handling(mesh(PEER, EXEC)) == [EXEC]

    peer_job_on_stale_exec.refresh_from_db()
    assert peer_job_on_stale_exec.status == 'failed'
