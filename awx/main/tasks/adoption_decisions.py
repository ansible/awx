"""Decisions the heartbeat makes about lost instances and orphaned jobs.

Nothing in this module touches the database, receptor or the dispatcher. The heartbeat in
awx.main.tasks.system gathers state, asks these functions what to do, and carries out the
answer. Keeping the decisions separate lets them be tested with plain objects, without a
cluster, and gives cross-controller adoption (AAP-89602) one place to change each rule.

Jobs and instances are read only through attributes, so model instances and simple
stand-ins in tests both work.
"""

from enum import Enum

from django.utils.timezone import timedelta

from awx.main.constants import RECEPTOR_SUBMIT_STARTED


class JobAction(str, Enum):
    SKIP = 'skip'
    ADOPT = 'adopt'
    REAP = 'reap'
    DEFER = 'defer'  # adoptable, but not here and not now; left for another controller
    REQUEUE = 'requeue'  # never reached an execution environment; back to pending


class LostInstanceAction(str, Enum):
    DEPROVISION = 'deprovision'
    MARK_OFFLINE = 'mark_offline'
    NONE = 'none'


def find_lost_instances(instance_list, this_hostname, ref_time):
    """Split peers into (lost, remaining). This instance is never lost here; it is judged separately."""
    lost = []
    remaining = []
    for inst in instance_list:
        if inst.hostname != this_hostname and inst.is_lost(ref_time=ref_time):
            lost.append(inst)
        else:
            remaining.append(inst)
    return lost, remaining


def live_controller_hostnames(instances, ref_time, grace_seconds, mesh_hostnames=()):
    """Hostnames of the controllers the orphan sweep must not take jobs from.

    An instance is live while it is ready or installed, or draining (deprovisioning), which
    still runs its jobs. It also stays live while unavailable if it checked in within
    grace_seconds of ref_time: one failed Redis ping marks a running controller unavailable
    with a recent last_seen, and sweeping its jobs then had the controller and its peers all
    stream them (AAP-96708). A controller that leaves on purpose back-dates its last_seen past
    the grace period, so its jobs are swept at once.

    A controller with no row at all was deprovisioned, which says nothing about whether it is
    still running. mesh_hostnames are the nodes on the receptor mesh; one of them without a row
    is still live. A controller that has a row is judged by its row alone, so a departure it
    announced is not held up while its connection lingers.
    """
    cutoff = ref_time - timedelta(seconds=grace_seconds)
    live = set()
    with_rows = set()
    for inst in instances:
        with_rows.add(inst.hostname)
        if inst.node_state in ('ready', 'installed', 'deprovisioning') or (
            inst.node_state == 'unavailable' and inst.last_seen is not None and inst.last_seen >= cutoff
        ):
            live.add(inst.hostname)
    return live | (set(mesh_hostnames) - with_rows)


def mesh_hostnames(mesh_status):
    """The nodes receptor's routing table names, from its status: every node with a known route.

    A node that left the mesh stays in the table as a key with no connections, so a key counts
    only if it has some.
    """
    costs = (mesh_status or {}).get('KnownConnectionCosts') or {}
    names = set()
    for node, peers in costs.items():
        if peers:
            names.add(node)
            names.update(peers)
    return names


def drop_mesh_connected_control_nodes(lost_instances, on_mesh, ref_time, timeout_seconds):
    """Remove the lost control and hybrid nodes that are still on the receptor mesh.

    A control node on the mesh is alive however stale its last_seen, up to timeout_seconds:
    that is what lets a controller that only missed heartbeats keep its job. Past
    timeout_seconds the mesh stops protecting it. A hung dispatcher keeps its mesh
    connections but never writes its own last_seen and never runs the health check that
    marks it unavailable, so without this bound mesh presence alone would protect it
    forever. timeout_seconds is HADR_JOB_ADOPTION_TIMEOUT, the same bound every other
    stalled-adoption wait already uses, so this does not add a second knob.

    Execution and hop nodes pass through unaffected; drop_routed_remote_nodes judges them.
    """
    cutoff = ref_time - timedelta(seconds=timeout_seconds)
    return [
        inst
        for inst in lost_instances
        if inst.node_type in ('execution', 'hop') or inst.hostname not in on_mesh or inst.last_seen is None or inst.last_seen < cutoff
    ]


def routed_hostnames(mesh_status):
    """The nodes this node can reach right now: its routing table.

    KnownConnectionCosts is the gossiped graph and keeps a cut-off node for a while after the
    route is gone (gist 3.9: the sweep claimed 5 s after the route went), so reachability is
    read from RoutingTable, the table receptor forwards by. None when the status has no table.
    """
    table = (mesh_status or {}).get('RoutingTable')
    return None if table is None else set(table)


def gate_lost_instances(lost_instances, mesh_ready):
    """Return the lost instances that may be handled now.

    While the receptor mesh is re-establishing, a control node may only look lost, so its
    handling waits for a later heartbeat. Execution and hop nodes don't depend on mesh
    consensus and are handled either way.

    mesh_ready is a callable, asked only when something is lost.
    """
    if not lost_instances:
        return []
    if mesh_ready():
        return list(lost_instances)
    return [inst for inst in lost_instances if inst.node_type in ('execution', 'hop')]


def drop_routed_remote_nodes(lost_instances, routed):
    """Remove the execution and hop nodes this node has a route to from the lost ones.

    last_seen only says no controller saw a fresh advertisement lately. A route says the node is
    there now, and reaping the jobs of a node that is there kills playbooks that still run (2.11).
    A node that is really gone loses its route within seconds. An unreadable routing table
    (None) says nothing, so the last_seen judgement stands.
    """
    if routed is None:
        return list(lost_instances)
    return [inst for inst in lost_instances if inst.node_type not in ('execution', 'hop') or inst.hostname not in routed]


def execution_node_reachable(execution_node, routed):
    """Does this node have a route to the job's execution node?

    A container group job has no execution_node, and an unreadable routing table (None) says nothing,
    so both count as reachable: the check only ever declines on positive evidence.
    """
    return not execution_node or routed is None or execution_node in routed


def submitted_to_receptor(job):
    """Did a controller start to submit this job to receptor? receptor may then run its unit with no work_unit_id saved."""
    return bool((getattr(job, 'job_env', None) or {}).get(RECEPTOR_SUBMIT_STARTED))


def is_requeueable(job):
    """May this job go back to pending and run again?

    Not with launch_type='sync' (inline project/inventory updates): the task manager never
    dispatches one, so a requeued one stays pending forever. Not once it was submitted to
    receptor: receptor starts the unit before it replies with the id, so a controller lost
    before it saved work_unit_id leaves a playbook running, and a requeue would run it twice
    (gist 4.5, AAP-99320).
    """
    return getattr(job, 'launch_type', None) != 'sync' and not submitted_to_receptor(job)


def reap_explanation(job, default=None):
    """The job_explanation for reaping job: a warning when its playbook may still run, else default."""
    if job.work_unit_id or not submitted_to_receptor(job):
        return default
    return (
        f'Controller was lost while it submitted the job; its playbook may still be running on '
        f'{job.execution_node or "its execution node"} and its result is lost.'
    )


def lost_instance_job_action(job, lost_hostname, slot_available, route_available=lambda: True):
    """What to do with a running job whose controller or execution node was lost.

    A job dispatched to receptor whose controller was lost is adopted if its playbook ran on
    another node, which outlived the controller. It is deferred instead when this controller
    has no room or no route to its execution node: it stays owned by the lost controller, so
    another controller's orphan sweep still finds it. A job that never reached an execution environment goes back to pending,
    and so does a started job of the lost controller that has no work unit, unless a cancel was requested. Anything else is reaped.

    slot_available and route_available are callables, asked only for a job that would be adopted.
    """
    if job.work_unit_id and job.controller_node == lost_hostname and job.execution_node != lost_hostname:
        return JobAction.ADOPT if route_available() and slot_available() else JobAction.DEFER
    if is_requeueable(job) and not job.work_unit_id and (not job.started or (job.controller_node == lost_hostname and not getattr(job, 'cancel_flag', False))):
        return JobAction.REQUEUE
    return JobAction.REAP


def lost_instance_disposition(inst, auto_deprovision):
    """What to do with the lost instance itself once its jobs are handled."""
    if auto_deprovision and inst.node_type == 'control':
        return LostInstanceAction.DEPROVISION
    if inst.node_state == 'ready':
        return LostInstanceAction.MARK_OFFLINE
    return LostInstanceAction.NONE


def adoption_slot_available(capacity, remaining_capacity, headroom_needed=0):
    """Is there room on this controller for one more adoption?

    An adoption is the one dispatcher task that occupies its worker for the whole remaining
    runtime of a job, because it streams that job's events. A controller inheriting a large
    instance's jobs would otherwise fill the pool with adoptions and starve the heartbeat,
    at which point the rest of the cluster declares *this* controller lost too and the
    cascade repeats. Jobs over the bound are simply not adopted this cycle: they stay running
    and claimed by us, so the next heartbeat re-queues them.

    Control capacity is that bound. It already prices exactly this cost — one
    AWX_CONTROL_NODE_TASK_IMPACT per running job we are the controller_node for — and an
    adopted job is controlled by us, so it is already in consumed_capacity. That makes the
    two adoption shapes fall out correctly without a second knob: re-adopting our own jobs
    after a restart is net zero, because those jobs counted against us before we died and
    still do, while inheriting a dead peer's jobs is genuinely new load and is throttled
    against the same number that bounds normally dispatched work. Operators tune it with the
    capacity_adjustment slider they already use.

    After a claim the job being considered is itself counted, so remaining_capacity == 0
    means it is the one that exactly fills us. That is the default, headroom_needed=0.

    Callers that ask *before* claiming pass headroom_needed=AWX_CONTROL_NODE_TASK_IMPACT,
    because their job is not in consumed_capacity yet and a controller sitting at exactly
    capacity would otherwise take one job too many. The lost-instance path is the one such
    caller: it has to decline rather than claim, so that a job it cannot hold stays owned by
    the dead controller and remains visible to another node's orphan sweep.

    Zero capacity means draining or not yet sized by the capacity job, not "no room";
    consumed_capacity is not meaningful against it, so it does not block adoption.
    """
    if not capacity:
        return True
    return remaining_capacity >= headroom_needed


def room_for_another_controllers_job(enabled, capacity, remaining_capacity, headroom_needed=0):
    """May this controller take a job from a controller that was lost?

    Stricter than adoption_slot_available, which governs a controller's own jobs. A disabled
    controller, or one with no capacity (draining or not yet sized), is not one the task
    manager would place work on, so it takes no one else's either (4.3). Declining is safe:
    the job stays owned by the lost controller, where another controller's sweep finds it.
    """
    if not enabled or not capacity:
        return False
    return remaining_capacity >= headroom_needed


def startup_job_action(job):
    """At startup, a running job this controller owns is adopted if it was dispatched to receptor, else reaped."""
    if job.work_unit_id:
        return JobAction.ADOPT
    return JobAction.REAP


def running_job_action(job, this_hostname, active_task_ids, ref_time, workflow_ctype_id, live_controller_hostnames):
    """On a periodic heartbeat, what to do with a job that may have been orphaned on this instance.

    A job is left alone unless it is running, belongs to this instance as controller or
    execution node, is not a workflow, started before ref_time, and no dispatcher task is
    tracking it. Such an orphan is adopted when this instance controls it and it was
    dispatched to receptor, and put back to pending when it never got a work unit. One that
    another instance controls is left alone too: a live controller handles its own jobs, and a
    dispatched job of a dead controller is the orphan sweep's to adopt. Anything else is reaped.
    """
    if job.status != 'running':
        return JobAction.SKIP
    if this_hostname not in (job.controller_node, job.execution_node):
        return JobAction.SKIP
    if job.polymorphic_ctype_id == workflow_ctype_id:
        return JobAction.SKIP
    if active_task_ids and job.celery_task_id in active_task_ids:
        return JobAction.SKIP
    if ref_time and (job.started is None or job.started > ref_time):
        return JobAction.SKIP
    if job.work_unit_id and job.controller_node == this_hostname:
        return JobAction.ADOPT
    if is_requeueable(job) and not job.work_unit_id and job.controller_node == this_hostname and not getattr(job, 'cancel_flag', False):
        # Claimed by this controller but never given a work unit, e.g. it was swept from a killed
        # controller before dispatch got that far. Nothing reached an EE, so run it again.
        return JobAction.REQUEUE
    if job.controller_node != this_hostname and (job.controller_node in live_controller_hostnames or job.work_unit_id):
        return JobAction.SKIP
    return JobAction.REAP


def stall_budget_exhausted(stalled_since, last_event_time, ref_time, timeout_seconds):
    """True if an adoption that cannot make progress has been stalled too long to keep retrying.

    stalled_since is when this controller first recorded the stall, or None if it has no
    record; that is when the budget starts, not the job's last event. A playbook can run
    for longer than the timeout without emitting an event, and measuring from that event
    failed such a job on its first transient error after a controller restart (AAP-96829).
    An event saved after the stall began proves progress, so the newer of the two is used.
    With no record the budget is never exhausted: losing it only defers longer.
    """
    if stalled_since is None:
        return False
    if last_event_time and last_event_time > stalled_since:
        stalled_since = last_event_time
    return stalled_since < ref_time - timedelta(seconds=timeout_seconds)
