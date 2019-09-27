from datetime import timedelta
import logging

from django.db.models import Q
from django.utils.timezone import now as tz_now
from django.contrib.contenttypes.models import ContentType

from awx.main.models import Instance, UnifiedJob, WorkflowJob

logger = logging.getLogger('awx.main.dispatch')


def reap_job(j, status):
    if UnifiedJob.objects.get(id=j.id).status not in ('running', 'waiting'):
        # just in case, don't reap jobs that aren't running
        return
    j.status = status
    j.start_args = ''  # blank field to remove encrypted passwords
    j.job_explanation += ' '.join((
        'Task was marked as running in Tower but was not present in',
        'the job queue, so it has been marked as failed.',
    ))
    j.save(update_fields=['status', 'start_args', 'job_explanation'])
    if hasattr(j, 'send_notification_templates'):
        j.send_notification_templates('failed')
    j.websocket_emit_status(status)
    logger.error(
        '{} is no longer running; reaping'.format(j.log_format)
    )


def reap(instance=None, status='failed', excluded_uuids=[]):
    '''
    Reap all jobs in waiting|running for this instance.
    '''
    me = instance
    if me is None:
        (changed, me) = Instance.objects.get_or_register()
        if changed:
            logger.info("Registered tower node '{}'".format(me.hostname))
    now = tz_now()
    workflow_ctype_id = ContentType.objects.get_for_model(WorkflowJob).id
    jobs = UnifiedJob.objects.filter(
        (
            Q(status='running') |
            Q(status='waiting', modified__lte=now - timedelta(seconds=60))
        ) & (
            Q(execution_node=me.hostname) |
            Q(controller_node=me.hostname)
        ) & ~Q(polymorphic_ctype_id=workflow_ctype_id)
    ).exclude(celery_task_id__in=excluded_uuids)
    for j in jobs:
        reap_job(j, status)
