from datetime import timedelta
import logging

from django.db.models import Q
from django.utils.timezone import now as tz_now
from django.contrib.contenttypes.models import ContentType

from awx.main.models import Instance, UnifiedJob, WorkflowJob

logger = logging.getLogger('awx.main.dispatch')


def startup_reaping():
    """
    If this particular instance is starting, then we know that any running jobs are invalid
    so we will reap those jobs as a special action here
    """
    try:
        me = Instance.objects.me()
    except RuntimeError as e:
        logger.warning(f'Local instance is not registered, not running startup reaper: {e}')
        return
    jobs = UnifiedJob.objects.filter(status='running', controller_node=me.hostname)
    job_ids = []
    for j in jobs:
        job_ids.append(j.id)
        j.status = 'failed'
        j.start_args = ''
        j.job_explanation += 'Task was marked as running at system start up. The system must have not shut down properly, so it has been marked as failed.'
        j.save(update_fields=['status', 'start_args', 'job_explanation'])
        if hasattr(j, 'send_notification_templates'):
            j.send_notification_templates('failed')
        j.websocket_emit_status('failed')
    if job_ids:
        logger.error(f'Unified jobs {job_ids} were reaped on dispatch startup')


def reap_job(j, status):
    if UnifiedJob.objects.get(id=j.id).status not in ('running', 'waiting'):
        # just in case, don't reap jobs that aren't running
        return
    j.status = status
    j.start_args = ''  # blank field to remove encrypted passwords
    j.job_explanation += ' '.join(
        (
            'Task was marked as running but was not present in',
            'the job queue, so it has been marked as failed.',
        )
    )
    j.save(update_fields=['status', 'start_args', 'job_explanation'])
    if hasattr(j, 'send_notification_templates'):
        j.send_notification_templates('failed')
    j.websocket_emit_status(status)
    logger.error('{} is no longer running; reaping'.format(j.log_format))


def reap(instance=None, status='failed', excluded_uuids=[]):
    """
    Reap all jobs in waiting|running for this instance.
    """
    me = instance
    if me is None:
        try:
            me = Instance.objects.me()
        except RuntimeError as e:
            logger.warning(f'Local instance is not registered, not running reaper: {e}')
            return
    now = tz_now()
    workflow_ctype_id = ContentType.objects.get_for_model(WorkflowJob).id
    jobs = UnifiedJob.objects.filter(
        (Q(status='running') | Q(status='waiting', modified__lte=now - timedelta(seconds=60)))
        & (Q(execution_node=me.hostname) | Q(controller_node=me.hostname))
        & ~Q(polymorphic_ctype_id=workflow_ctype_id)
    ).exclude(celery_task_id__in=excluded_uuids)
    for j in jobs:
        reap_job(j, status)
