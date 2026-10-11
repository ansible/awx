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


class JobAction(str, Enum):
    SKIP = 'skip'
    ADOPT = 'adopt'
    REAP = 'reap'


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


def gate_lost_instances(lost_instances, mesh_ready):
    """Return the lost instances that may be handled now.

    While the receptor mesh is re-establishing, a control node may only look lost, so its
    handling waits for a later heartbeat. Execution and hop nodes don't depend on mesh
    consensus and are handled either way.
    """
    if mesh_ready:
        return list(lost_instances)
    return [inst for inst in lost_instances if inst.node_type in ('execution', 'hop')]


def lost_instance_job_action(job):
    """What to do with a running job whose controller or execution node was lost.

    AAP-89602: cross-controller adoption for dispatched jobs will return ADOPT here
    once ansible/receptor#1564 merges. Until then every such job is reaped.
    """
    return JobAction.REAP


def lost_instance_disposition(inst, auto_deprovision):
    """What to do with the lost instance itself once its jobs are handled."""
    if auto_deprovision and inst.node_type == 'control':
        return LostInstanceAction.DEPROVISION
    if inst.node_state == 'ready':
        return LostInstanceAction.MARK_OFFLINE
    return LostInstanceAction.NONE


def startup_job_action(job):
    """At startup, a running job this controller owns is adopted if it was dispatched to receptor, else reaped."""
    if job.work_unit_id:
        return JobAction.ADOPT
    return JobAction.REAP


def running_job_action(job, this_hostname, active_task_ids, ref_time, workflow_ctype_id):
    """On a periodic heartbeat, what to do with a job that may have been orphaned on this instance.

    A job is left alone unless it is running, belongs to this instance as controller or
    execution node, is not a workflow, started before ref_time, and no dispatcher task is
    tracking it. Such an orphan is adopted when this instance controls it and it was
    dispatched to receptor; otherwise it is reaped.
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
    return JobAction.REAP


def adoption_deadline_passed(last_event_time, started, ref_time, timeout_seconds):
    """True if a job has been silent too long to adopt.

    Silence is measured from the last saved event, or from the start when there are no
    events. A job with neither is never past the deadline.
    """
    orphaned_since = last_event_time or started
    if not orphaned_since:
        return False
    return orphaned_since < ref_time - timedelta(seconds=timeout_seconds)
