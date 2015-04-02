# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import datetime
import logging
from optparse import make_option

# Django
from django.core.management.base import NoArgsCommand, CommandError
from django.db import transaction
from django.utils.timezone import now

# AWX
from awx.main.models import Job, AdHocCommand, ProjectUpdate, InventoryUpdate, SystemJob

class Command(NoArgsCommand):
    '''
    Management command to cleanup old jobs and project updates.
    '''

    help = 'Remove old jobs, project and inventory updates from the database.'

    option_list = NoArgsCommand.option_list + (
        make_option('--days', dest='days', type='int', default=90, metavar='N',
                    help='Remove jobs/updates executed more than N days ago'),
        make_option('--dry-run', dest='dry_run', action='store_true',
                    default=False, help='Dry run mode (show items that would '
                    'be removed)'),
        make_option('--jobs', dest='only_jobs', action='store_true',
                    default=False,
                    help='Only remove jobs'),
        make_option('--ad-hoc-commands', dest='only_ad_hoc_commands',
                    action='store_true', default=False,
                    help='Only remove ad hoc commands'),
        make_option('--project-updates', dest='only_project_updates',
                    action='store_true', default=False,
                    help='Only remove project updates'),
        make_option('--inventory-updates', dest='only_inventory_updates',
                    action='store_true', default=False,
                    help='Only remove inventory updates'),
        make_option('--management-jobs', default=False,
                    action='store_true', dest='only_management_jobs',
                    help='Only remove management jobs')
    )

    def cleanup_jobs(self):
        #jobs_qs = Job.objects.exclude(status__in=('pending', 'running'))
        #jobs_qs = jobs_qs.filter(created__lte=self.cutoff)
        for job in Job.objects.all():
            job_display = '"%s" (started %s, %d host summaries, %d events)' % \
                          (unicode(job), unicode(job.created),
                           job.job_host_summaries.count(), job.job_events.count())
            if job.status in ('pending', 'waiting', 'running'):
                action_text = 'would skip' if self.dry_run else 'skipping'
                self.logger.debug('%s %s job %s', action_text, job.status, job_display)
            elif job.created >= self.cutoff:
                action_text = 'would skip' if self.dry_run else 'skipping'
                self.logger.debug('%s %s', action_text, job_display)
            else:
                action_text = 'would delete' if self.dry_run else 'deleting'
                self.logger.info('%s %s', action_text, job_display)
                if not self.dry_run:
                    job.delete()

    def cleanup_ad_hoc_commands(self):
        for ad_hoc_command in AdHocCommand.objects.all():
            ad_hoc_command_display = '"%s" (started %s, %d events)' % \
                          (unicode(ad_hoc_command), unicode(ad_hoc_command.created),
                           ad_hoc_command.ad_hoc_command_events.count())
            if ad_hoc_command.status in ('pending', 'waiting', 'running'):
                action_text = 'would skip' if self.dry_run else 'skipping'
                self.logger.debug('%s %s ad hoc command %s', action_text, ad_hoc_command.status, ad_hoc_command_display)
            elif ad_hoc_command.created >= self.cutoff:
                action_text = 'would skip' if self.dry_run else 'skipping'
                self.logger.debug('%s %s', action_text, ad_hoc_command_display)
            else:
                action_text = 'would delete' if self.dry_run else 'deleting'
                self.logger.info('%s %s', action_text, ad_hoc_command_display)
                if not self.dry_run:
                    ad_hoc_command.delete()

    def cleanup_project_updates(self):
        for pu in ProjectUpdate.objects.all():
            pu_display = '"%s" (started %s)' % (unicode(pu), unicode(pu.created))
            if pu.status in ('pending', 'waiting', 'running'):
                action_text = 'would skip' if self.dry_run else 'skipping'
                self.logger.debug('%s %s project update %s', action_text, pu.status, pu_display)
            if pu in (pu.project.current_update, pu.project.last_update) and pu.project.scm_type:
                action_text = 'would skip' if self.dry_run else 'skipping'
                self.logger.debug('%s %s', action_text, pu_display)
            elif pu.created >= self.cutoff:
                action_text = 'would skip' if self.dry_run else 'skipping'
                self.logger.debug('%s %s', action_text, pu_display)
            else:
                action_text = 'would delete' if self.dry_run else 'deleting'
                self.logger.info('%s %s', action_text, pu_display)
                if not self.dry_run:
                    pu.delete()

    def cleanup_inventory_updates(self):
        for iu in InventoryUpdate.objects.all():
            iu_display = '"%s" (started %s)' % (unicode(iu), unicode(iu.created))
            if iu.status in ('pending', 'waiting', 'running'):
                action_text = 'would skip' if self.dry_run else 'skipping'
                self.logger.debug('%s %s inventory update %s', action_text, iu.status, iu_display)
            if iu in (iu.inventory_source.current_update, iu.inventory_source.last_update) and iu.inventory_source.source:
                action_text = 'would skip' if self.dry_run else 'skipping'
                self.logger.debug('%s %s', action_text, iu_display)
            elif iu.created >= self.cutoff:
                action_text = 'would skip' if self.dry_run else 'skipping'
                self.logger.debug('%s %s', action_text, iu_display)
            else:
                action_text = 'would delete' if self.dry_run else 'deleting'
                self.logger.info('%s %s', action_text, iu_display)
                if not self.dry_run:
                    iu.delete()

    def cleanup_management_jobs(self):
        for sj in SystemJob.objects.all():
            sj_display = '"%s" (started %s)' % (unicode(sj), unicode(sj.created))
            if sj.status in ('pending', 'waiting', 'running'):
                action_text = 'would skip' if self.dry_run else 'skipping'
                self.logger.debug('%s %s system_job %s', action_text, sj.status, sj_display)
            elif sj.created >= self.cutoff:
                action_text = 'would skip' if self.dry_run else 'skipping'
                self.logger.debug('%s %s', action_text, sj_display)
            else:
                action_text = 'would delete' if self.dry_run else 'deleting'
                self.logger.info('%s %s', action_text, sj_display)
                if not self.dry_run:
                    sj.delete()

    def init_logging(self):
        log_levels = dict(enumerate([logging.ERROR, logging.INFO,
                                     logging.DEBUG, 0]))
        self.logger = logging.getLogger('awx.main.commands.cleanup_jobs')
        self.logger.setLevel(log_levels.get(self.verbosity, 0))
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
        self.logger.propagate = False

    @transaction.atomic
    def handle_noargs(self, **options):
        self.verbosity = int(options.get('verbosity', 1))
        self.init_logging()
        self.days = int(options.get('days', 90))
        self.dry_run = bool(options.get('dry_run', False))
        try:
            self.cutoff = now() - datetime.timedelta(days=self.days)
        except OverflowError:
            raise CommandError('--days specified is too large. Try something less than 99999 (about 270 years).')
        model_names = ('jobs', 'ad_hoc_commands', 'project_updates', 'inventory_updates', 'management_jobs')
        models_to_cleanup = set()
        for m in model_names:
            if options.get('only_%s' % m, False):
                models_to_cleanup.add(m)
        if not models_to_cleanup:
            models_to_cleanup.update(model_names)
        for m in model_names:
            if m in models_to_cleanup:
                getattr(self, 'cleanup_%s' % m)()
