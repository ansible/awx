import logging

from django.db.models import Q
from django.contrib.contenttypes.models import ContentType

from awx.main.models import Instance, UnifiedJob, WorkflowJob

logger = logging.getLogger('awx.main.dispatch')


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


def reap(instance=None, status='failed', job_explanation=None, excluded_uuids=None, ref_time=None):
    """Reap all running jobs for this instance.

    Per-job adopt-or-reap decisions (based on work_unit_id) belong in the caller's loop,
    not here as a queryset filter. See _process_startup_jobs and _process_running_jobs
    in awx.main.tasks.system for the unified loops that replaced undispatched_only filtering.
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
