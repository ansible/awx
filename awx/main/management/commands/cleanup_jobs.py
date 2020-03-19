# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import datetime
import logging


# Django
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.timezone import now

# AWX
from awx.main.models import (
    Job, AdHocCommand, ProjectUpdate, InventoryUpdate,
    SystemJob, WorkflowJob, Notification
)
from awx.main.signals import (
    disable_activity_stream,
    disable_computed_fields
)

from awx.main.management.commands.deletion import AWXCollector, pre_delete


class Command(BaseCommand):
    '''
    Management command to cleanup old jobs and project updates.
    '''

    help = 'Remove old jobs, project and inventory updates from the database.'

    def add_arguments(self, parser):
        parser.add_argument('--days', dest='days', type=int, default=90, metavar='N',
                            help='Remove jobs/updates executed more than N days ago. Defaults to 90.')
        parser.add_argument('--dry-run', dest='dry_run', action='store_true',
                            default=False, help='Dry run mode (show items that would '
                            'be removed)')
        parser.add_argument('--jobs', dest='only_jobs', action='store_true',
                            default=False,
                            help='Remove jobs')
        parser.add_argument('--ad-hoc-commands', dest='only_ad_hoc_commands',
                            action='store_true', default=False,
                            help='Remove ad hoc commands')
        parser.add_argument('--project-updates', dest='only_project_updates',
                            action='store_true', default=False,
                            help='Remove project updates')
        parser.add_argument('--inventory-updates', dest='only_inventory_updates',
                            action='store_true', default=False,
                            help='Remove inventory updates')
        parser.add_argument('--management-jobs', default=False,
                            action='store_true', dest='only_management_jobs',
                            help='Remove management jobs')
        parser.add_argument('--notifications', dest='only_notifications',
                            action='store_true', default=False,
                            help='Remove notifications')
        parser.add_argument('--workflow-jobs', default=False,
                            action='store_true', dest='only_workflow_jobs',
                            help='Remove workflow jobs')


    def cleanup_jobs(self):
        skipped, deleted = 0, 0

        batch_size = 1000000

        while True:
            # get queryset for available jobs to remove
            qs = Job.objects.filter(created__lt=self.cutoff).exclude(status__in=['pending', 'waiting', 'running'])
            # get pk list for the first N (batch_size) objects
            pk_list = qs[0:batch_size].values_list('pk')
            # You cannot delete queries with sql LIMIT set, so we must
            # create a new query from this pk_list
            qs_batch = Job.objects.filter(pk__in=pk_list)
            just_deleted = 0
            if not self.dry_run:
                del_query = pre_delete(qs_batch)
                collector = AWXCollector(del_query.db)
                collector.collect(del_query)
                _, models_deleted = collector.delete()
                if models_deleted:
                    just_deleted = models_deleted['main.Job']
                deleted += just_deleted
            else:
                just_deleted = 0 # break from loop, this is dry run
                deleted = qs.count()

            if just_deleted == 0:
                break

        skipped += (Job.objects.filter(created__gte=self.cutoff) | Job.objects.filter(status__in=['pending', 'waiting', 'running'])).count()
        return skipped, deleted

    def cleanup_ad_hoc_commands(self):
        skipped, deleted = 0, 0
        ad_hoc_commands = AdHocCommand.objects.filter(created__lt=self.cutoff)
        for ad_hoc_command in ad_hoc_commands.iterator():
            ad_hoc_command_display = '"%s" (%d events)' % \
                (str(ad_hoc_command),
                 ad_hoc_command.ad_hoc_command_events.count())
            if ad_hoc_command.status in ('pending', 'waiting', 'running'):
                action_text = 'would skip' if self.dry_run else 'skipping'
                self.logger.debug('%s %s ad hoc command %s', action_text, ad_hoc_command.status, ad_hoc_command_display)
                skipped += 1
            else:
                action_text = 'would delete' if self.dry_run else 'deleting'
                self.logger.info('%s %s', action_text, ad_hoc_command_display)
                if not self.dry_run:
                    ad_hoc_command.delete()
                deleted += 1

        skipped += AdHocCommand.objects.filter(created__gte=self.cutoff).count()
        return skipped, deleted

    def cleanup_project_updates(self):
        skipped, deleted = 0, 0
        project_updates = ProjectUpdate.objects.filter(created__lt=self.cutoff)
        for pu in project_updates.iterator():
            pu_display = '"%s" (type %s)' % (str(pu), str(pu.launch_type))
            if pu.status in ('pending', 'waiting', 'running'):
                action_text = 'would skip' if self.dry_run else 'skipping'
                self.logger.debug('%s %s project update %s', action_text, pu.status, pu_display)
                skipped += 1
            elif pu in (pu.project.current_update, pu.project.last_update) and pu.project.scm_type:
                action_text = 'would skip' if self.dry_run else 'skipping'
                self.logger.debug('%s %s', action_text, pu_display)
                skipped += 1
            else:
                action_text = 'would delete' if self.dry_run else 'deleting'
                self.logger.info('%s %s', action_text, pu_display)
                if not self.dry_run:
                    pu.delete()
                deleted += 1

        skipped += ProjectUpdate.objects.filter(created__gte=self.cutoff).count()
        return skipped, deleted

    def cleanup_inventory_updates(self):
        skipped, deleted = 0, 0
        inventory_updates = InventoryUpdate.objects.filter(created__lt=self.cutoff)
        for iu in inventory_updates.iterator():
            iu_display = '"%s" (source %s)' % (str(iu), str(iu.source))
            if iu.status in ('pending', 'waiting', 'running'):
                action_text = 'would skip' if self.dry_run else 'skipping'
                self.logger.debug('%s %s inventory update %s', action_text, iu.status, iu_display)
                skipped += 1
            elif iu in (iu.inventory_source.current_update, iu.inventory_source.last_update) and iu.inventory_source.source:
                action_text = 'would skip' if self.dry_run else 'skipping'
                self.logger.debug('%s %s', action_text, iu_display)
                skipped += 1
            else:
                action_text = 'would delete' if self.dry_run else 'deleting'
                self.logger.info('%s %s', action_text, iu_display)
                if not self.dry_run:
                    iu.delete()
                deleted += 1

        skipped += InventoryUpdate.objects.filter(created__gte=self.cutoff).count()
        return skipped, deleted

    def cleanup_management_jobs(self):
        skipped, deleted = 0, 0
        system_jobs = SystemJob.objects.filter(created__lt=self.cutoff)
        for sj in system_jobs.iterator():
            sj_display = '"%s" (type %s)' % (str(sj), str(sj.job_type))
            if sj.status in ('pending', 'waiting', 'running'):
                action_text = 'would skip' if self.dry_run else 'skipping'
                self.logger.debug('%s %s system_job %s', action_text, sj.status, sj_display)
                skipped += 1
            else:
                action_text = 'would delete' if self.dry_run else 'deleting'
                self.logger.info('%s %s', action_text, sj_display)
                if not self.dry_run:
                    sj.delete()
                deleted += 1

        skipped += SystemJob.objects.filter(created__gte=self.cutoff).count()
        return skipped, deleted

    def init_logging(self):
        log_levels = dict(enumerate([logging.ERROR, logging.INFO,
                                     logging.DEBUG, 0]))
        self.logger = logging.getLogger('awx.main.commands.cleanup_jobs')
        self.logger.setLevel(log_levels.get(self.verbosity, 0))
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
        self.logger.propagate = False

    def cleanup_workflow_jobs(self):
        skipped, deleted = 0, 0
        workflow_jobs = WorkflowJob.objects.filter(created__lt=self.cutoff)
        for workflow_job in workflow_jobs.iterator():
            workflow_job_display = '"{}" ({} nodes)'.format(
                str(workflow_job),
                workflow_job.workflow_nodes.count())
            if workflow_job.status in ('pending', 'waiting', 'running'):
                action_text = 'would skip' if self.dry_run else 'skipping'
                self.logger.debug('%s %s job %s', action_text, workflow_job.status, workflow_job_display)
                skipped += 1
            else:
                action_text = 'would delete' if self.dry_run else 'deleting'
                self.logger.info('%s %s', action_text, workflow_job_display)
                if not self.dry_run:
                    workflow_job.delete()
                deleted += 1

        skipped += WorkflowJob.objects.filter(created__gte=self.cutoff).count()
        return skipped, deleted

    def cleanup_notifications(self):
        skipped, deleted = 0, 0
        notifications = Notification.objects.filter(created__lt=self.cutoff)
        for notification in notifications.iterator():
            notification_display = '"{}" (started {}, {} type, {} sent)'.format(
                str(notification), str(notification.created),
                notification.notification_type, notification.notifications_sent)
            if notification.status in ('pending',):
                action_text = 'would skip' if self.dry_run else 'skipping'
                self.logger.debug('%s %s notification %s', action_text, notification.status, notification_display)
                skipped += 1
            else:
                action_text = 'would delete' if self.dry_run else 'deleting'
                self.logger.info('%s %s', action_text, notification_display)
                if not self.dry_run:
                    notification.delete()
                deleted += 1

        skipped += Notification.objects.filter(created__gte=self.cutoff).count()
        return skipped, deleted

    @transaction.atomic
    def handle(self, *args, **options):
        self.verbosity = int(options.get('verbosity', 1))
        self.init_logging()
        self.days = int(options.get('days', 90))
        self.dry_run = bool(options.get('dry_run', False))
        try:
            self.cutoff = now() - datetime.timedelta(days=self.days)
        except OverflowError:
            raise CommandError('--days specified is too large. Try something less than 99999 (about 270 years).')
        model_names = ('jobs', 'ad_hoc_commands', 'project_updates', 'inventory_updates',
                       'management_jobs', 'workflow_jobs', 'notifications')
        models_to_cleanup = set()
        for m in model_names:
            if options.get('only_%s' % m, False):
                models_to_cleanup.add(m)
        if not models_to_cleanup:
            models_to_cleanup.update(model_names)
        with disable_activity_stream(), disable_computed_fields():
            for m in model_names:
                if m in models_to_cleanup:
                    skipped, deleted = getattr(self, 'cleanup_%s' % m)()
                    if self.dry_run:
                        self.logger.log(99, '%s: %d would be deleted, %d would be skipped.', m.replace('_', ' '), deleted, skipped)
                    else:
                        self.logger.log(99, '%s: %d deleted, %d skipped.', m.replace('_', ' '), deleted, skipped)
