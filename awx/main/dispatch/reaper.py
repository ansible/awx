import logging

from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from dispatcherd.publish import task as dispatcher_task

from awx.main.dispatch import get_task_queuename
from awx.main.models import Instance, UnifiedJob, WorkflowJob
from awx.main.utils import ScheduleTaskManager

logger = logging.getLogger('awx.main.dispatch')


def startup_reaping():
    """
    If this particular instance is starting, then we know that any running jobs are invalid
    so we will reap those jobs as a special action here
    """
    jobs = UnifiedJob.objects.filter(status='running', controller_node=Instance.objects.my_hostname())
    job_ids = []
    for j in jobs:
        job_ids.append(j.id)
        reap_job(
            j,
            'failed',
            job_explanation='Task was marked as running at system start up. The system must have not shut down properly, so it has been marked as failed.',
        )
    if job_ids:
        logger.error(f'Unified jobs {job_ids} were reaped on dispatch startup')


def reap_job(j, status, job_explanation=None):
    j.refresh_from_db(fields=['status', 'job_explanation'])
    status_before = j.status
    if status_before not in ('running', 'waiting'):
        # just in case, don't reap jobs that aren't running
        return
    j.status = status
    j.start_args = ''  # blank field to remove encrypted passwords
    if j.job_explanation:
        j.job_explanation += ' '  # Separate messages for readability
    if job_explanation is None:
        j.job_explanation += 'Task was marked as running but was not present in the job queue, so it has been marked as failed.'
    else:
        j.job_explanation += job_explanation
    j.save(update_fields=['status', 'start_args', 'job_explanation'])
    if hasattr(j, 'send_notification_templates'):
        j.send_notification_templates('failed')
    j.websocket_emit_status(status)
    logger.error(f'{j.log_format} is no longer {status_before}; reaping')


def get_orphaned_running_jobs_query(valid_execution_node_hostnames):
    """Get queryset for running jobs on orphaned execution nodes.

    Args:
        valid_execution_node_hostnames: Iterable of valid execution node hostnames

    Returns:
        QuerySet of running jobs on invalid execution nodes, excluding workflows
    """
    workflow_ctype_id = ContentType.objects.get_for_model(WorkflowJob).id
    return (
        UnifiedJob.objects.filter(
            status='running',
            execution_node__isnull=False,
        )
        .exclude(execution_node__in=valid_execution_node_hostnames)
        .exclude(polymorphic_ctype_id=workflow_ctype_id)
    )


def reap(instance=None, status='failed', job_explanation=None, excluded_uuids=None, ref_time=None):
    """
    Reap all jobs in running for this instance.
    """
    if instance is None:
        hostname = Instance.objects.my_hostname()
    else:
        hostname = instance.hostname
    workflow_ctype_id = ContentType.objects.get_for_model(WorkflowJob).id
    base_Q = Q(status='running') & (Q(execution_node=hostname) | Q(controller_node=hostname)) & ~Q(polymorphic_ctype_id=workflow_ctype_id)
    if ref_time:
        jobs = UnifiedJob.objects.filter(base_Q & Q(started__lte=ref_time))
    else:
        jobs = UnifiedJob.objects.filter(base_Q)
    if excluded_uuids:
        jobs = jobs.exclude(celery_task_id__in=excluded_uuids)
    for j in jobs:
        reap_job(j, status, job_explanation=job_explanation)


@dispatcher_task(queue=get_task_queuename, timeout=600, on_duplicate='queue_one')
def reap_orphaned_jobs():
    """Background task to reap running jobs on orphaned instances.

    Queries for running jobs referencing non-existent or unregistered
    execution nodes and reaps them. Runs independently to avoid passing
    large argument lists and to prevent saturating task manager cycle.
    """
    valid_execution_nodes = set(Instance.objects.filter(node_type__in=('hybrid', 'execution')).values_list('hostname', flat=True))

    orphaned_running = get_orphaned_running_jobs_query(valid_execution_nodes)

    logger.info(f'Reaping orphaned running jobs')
    for job in orphaned_running:
        if not job.is_container_group_task:
            reap_job(job, 'failed', job_explanation='Task execution node is not a registered instance')


@dispatcher_task(queue=get_task_queuename, timeout=600, on_duplicate='queue_one')
def reset_orphaned_waiting_jobs():
    """Background task to reset waiting jobs on orphaned controller instances.

    Queries for waiting jobs referencing non-existent or unregistered
    controller nodes and resets them to pending. Runs independently to
    avoid passing large argument lists and to prevent saturating task manager.
    """
    valid_controller_nodes = set(Instance.objects.filter(node_type__in=('hybrid', 'control')).values_list('hostname', flat=True))

    orphaned_waiting = UnifiedJob.objects.filter(status='waiting').exclude(controller_node__in=valid_controller_nodes)

    logger.info(f'Resetting orphaned waiting jobs to pending')
    for job in orphaned_waiting:
        job.status = 'pending'
        job.controller_node = ''
        job.execution_node = ''
        job.save(update_fields=['status', 'controller_node', 'execution_node'])

    # Trigger task manager to re-process these now-pending jobs
    ScheduleTaskManager().schedule()
