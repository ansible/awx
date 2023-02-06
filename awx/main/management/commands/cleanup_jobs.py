# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import datetime
import logging
import pytz
import re


# Django
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, connection
from django.db.models import Min, Max
from django.db.models.signals import pre_save, post_save, pre_delete, post_delete, m2m_changed
from django.utils.timezone import now

# AWX
from awx.main.models import Job, AdHocCommand, ProjectUpdate, InventoryUpdate, SystemJob, WorkflowJob, Notification


def unified_job_class_to_event_table_name(job_class):
    return f'main_{job_class().event_class.__name__.lower()}'


def partition_table_name(job_class, dt):
    suffix = dt.replace(microsecond=0, second=0, minute=0).strftime('%Y%m%d_%H')

    event_tbl_name = unified_job_class_to_event_table_name(job_class)
    event_tbl_name += f'_{suffix}'
    return event_tbl_name


def partition_name_dt(part_name):
    """
    part_name examples:
        main_jobevent_20210318_09
        main_projectupdateevent_20210318_11
        main_inventoryupdateevent_20210318_03
    """
    if '_unpartitioned' in part_name:
        return None
    p = re.compile('([a-z]+)_([a-z]+)_([0-9]+)_([0-9][0-9])')
    m = p.match(part_name)
    if not m:
        return m
    dt_str = f"{m.group(3)}_{m.group(4)}"
    dt = datetime.datetime.strptime(dt_str, '%Y%m%d_%H').replace(tzinfo=pytz.UTC)
    return dt


def dt_to_partition_name(tbl_name, dt):
    return f"{tbl_name}_{dt.strftime('%Y%m%d_%H')}"


class DeleteMeta:
    def __init__(self, logger, job_class, cutoff, dry_run):
        self.logger = logger
        self.job_class = job_class
        self.cutoff = cutoff
        self.dry_run = dry_run

        self.jobs_qs = None  # Set in by find_jobs_to_delete()

        self.parts_no_drop = set()  # Set in identify_excluded_partitions()
        self.parts_to_drop = set()  # Set in find_partitions_to_drop()
        self.jobs_pk_list = []  # Set in find_jobs_to_delete()
        self.jobs_to_delete_count = 0  # Set in find_jobs_to_delete()
        self.jobs_no_delete_count = 0  # Set in find_jobs_to_delete()

    def find_jobs_to_delete(self):
        self.jobs_qs = self.job_class.objects.filter(created__lt=self.cutoff).values_list('pk', 'status', 'created')
        for pk, status, created in self.jobs_qs:
            if status not in ['pending', 'waiting', 'running']:
                self.jobs_to_delete_count += 1
                self.jobs_pk_list.append(pk)
        self.jobs_no_delete_count = (
            self.job_class.objects.filter(created__gte=self.cutoff) | self.job_class.objects.filter(status__in=['pending', 'waiting', 'running'])
        ).count()

    def identify_excluded_partitions(self):
        part_drop = {}

        for pk, status, created in self.jobs_qs:
            part_key = partition_table_name(self.job_class, created)
            if status in ['pending', 'waiting', 'running']:
                part_drop[part_key] = False
            else:
                part_drop.setdefault(part_key, True)

        # Note that parts_no_drop _may_ contain the names of partitions that don't exist
        # This can happen when the cleanup of _unpartitioned_* logic leaves behind jobs with status pending, waiting, running. The find_jobs_to_delete() will
        # pick these jobs up.
        self.parts_no_drop = {k for k, v in part_drop.items() if v is False}

    def delete_jobs(self):
        if not self.dry_run:
            self.job_class.objects.filter(pk__in=self.jobs_pk_list).delete()

    def find_partitions_to_drop(self):
        tbl_name = unified_job_class_to_event_table_name(self.job_class)

        with connection.cursor() as cursor:
            query = "SELECT inhrelid::regclass::text AS child FROM pg_catalog.pg_inherits"
            query += f" WHERE inhparent = '{tbl_name}'::regclass"
            query += f" AND TO_TIMESTAMP(LTRIM(inhrelid::regclass::text, '{tbl_name}_'), 'YYYYMMDD_HH24') < '{self.cutoff}'"
            query += " ORDER BY inhrelid::regclass::text"

            cursor.execute(query)
            partitions_from_db = [r[0] for r in cursor.fetchall()]

        partitions_dt = [partition_name_dt(p) for p in partitions_from_db if not None]
        partitions_dt = [p for p in partitions_dt if not None]

        # convert datetime partition back to string partition
        partitions_maybe_drop = {dt_to_partition_name(tbl_name, dt) for dt in partitions_dt}

        # Do not drop partition if there is a job that will not be deleted pointing at it
        self.parts_to_drop = partitions_maybe_drop - self.parts_no_drop

    def drop_partitions(self):
        if len(self.parts_to_drop) > 0:
            parts_to_drop = list(self.parts_to_drop)
            parts_to_drop.sort()  # sort it to make reading it easier for humans
            parts_to_drop_str = ','.join(parts_to_drop)
            if self.dry_run:
                self.logger.debug(f"Would drop event partition(s) {parts_to_drop_str}")
            else:
                self.logger.debug(f"Dropping event partition(s) {parts_to_drop_str}")

            if not self.dry_run:
                with connection.cursor() as cursor:
                    cursor.execute(f"DROP TABLE {parts_to_drop_str}")
        else:
            self.logger.debug("No event partitions to drop")

    def delete(self):
        self.find_jobs_to_delete()
        self.identify_excluded_partitions()
        self.find_partitions_to_drop()
        self.drop_partitions()
        self.delete_jobs()
        return (self.jobs_no_delete_count, self.jobs_to_delete_count)


class Command(BaseCommand):
    """
    Management command to cleanup old jobs and project updates.
    """

    help = 'Remove old jobs, project and inventory updates from the database.'

    def add_arguments(self, parser):
        parser.add_argument('--days', dest='days', type=int, default=90, metavar='N', help='Remove jobs/updates executed more than N days ago. Defaults to 90.')
        parser.add_argument('--dry-run', dest='dry_run', action='store_true', default=False, help='Dry run mode (show items that would ' 'be removed)')
        parser.add_argument('--jobs', dest='only_jobs', action='store_true', default=False, help='Remove jobs')
        parser.add_argument('--ad-hoc-commands', dest='only_ad_hoc_commands', action='store_true', default=False, help='Remove ad hoc commands')
        parser.add_argument('--project-updates', dest='only_project_updates', action='store_true', default=False, help='Remove project updates')
        parser.add_argument('--inventory-updates', dest='only_inventory_updates', action='store_true', default=False, help='Remove inventory updates')
        parser.add_argument('--management-jobs', default=False, action='store_true', dest='only_management_jobs', help='Remove management jobs')
        parser.add_argument('--notifications', dest='only_notifications', action='store_true', default=False, help='Remove notifications')
        parser.add_argument('--workflow-jobs', default=False, action='store_true', dest='only_workflow_jobs', help='Remove workflow jobs')

    def init_logging(self):
        log_levels = dict(enumerate([logging.ERROR, logging.INFO, logging.DEBUG, 0]))
        self.logger = logging.getLogger('awx.main.commands.cleanup_jobs')
        self.logger.setLevel(log_levels.get(self.verbosity, 0))
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
        self.logger.propagate = False

    def cleanup(self, job_class):
        delete_meta = DeleteMeta(self.logger, job_class, self.cutoff, self.dry_run)
        skipped, deleted = delete_meta.delete()

        return (delete_meta.jobs_no_delete_count, delete_meta.jobs_to_delete_count)

    def cleanup_jobs_partition(self):
        return self.cleanup(Job)

    def cleanup_ad_hoc_commands_partition(self):
        return self.cleanup(AdHocCommand)

    def cleanup_project_updates_partition(self):
        return self.cleanup(ProjectUpdate)

    def cleanup_inventory_updates_partition(self):
        return self.cleanup(InventoryUpdate)

    def cleanup_management_jobs_partition(self):
        return self.cleanup(SystemJob)

    def cleanup_workflow_jobs_partition(self):
        delete_meta = DeleteMeta(self.logger, WorkflowJob, self.cutoff, self.dry_run)

        delete_meta.find_jobs_to_delete()
        delete_meta.delete_jobs()
        return (delete_meta.jobs_no_delete_count, delete_meta.jobs_to_delete_count)

    def _cascade_delete_job_events(self, model, pk_list):
        if pk_list:
            with connection.cursor() as cursor:
                tblname = unified_job_class_to_event_table_name(model)

                pk_list_csv = ','.join(map(str, pk_list))
                rel_name = model().event_parent_key
                cursor.execute(f"DELETE FROM _unpartitioned_{tblname} WHERE {rel_name} IN ({pk_list_csv})")

    def cleanup_jobs(self):
        batch_size = 100000

        # Hack to avoid doing N+1 queries as each item in the Job query set does
        # an individual query to get the underlying UnifiedJob.
        Job.polymorphic_super_sub_accessors_replaced = True

        skipped = (Job.objects.filter(created__gte=self.cutoff) | Job.objects.filter(status__in=['pending', 'waiting', 'running'])).count()

        qs = Job.objects.select_related('unifiedjob_ptr').filter(created__lt=self.cutoff).exclude(status__in=['pending', 'waiting', 'running'])
        if self.dry_run:
            deleted = qs.count()
            return skipped, deleted

        deleted = 0
        info = qs.aggregate(min=Min('id'), max=Max('id'))
        if info['min'] is not None:
            for start in range(info['min'], info['max'] + 1, batch_size):
                qs_batch = qs.filter(id__gte=start, id__lte=start + batch_size)
                pk_list = qs_batch.values_list('id', flat=True)

                _, results = qs_batch.delete()
                deleted += results['main.Job']
                self._cascade_delete_job_events(Job, pk_list)

        return skipped, deleted

    def cleanup_ad_hoc_commands(self):
        skipped, deleted = 0, 0
        ad_hoc_commands = AdHocCommand.objects.filter(created__lt=self.cutoff)
        pk_list = []
        for ad_hoc_command in ad_hoc_commands.iterator():
            ad_hoc_command_display = '"%s" (%d events)' % (str(ad_hoc_command), ad_hoc_command.ad_hoc_command_events.count())
            if ad_hoc_command.status in ('pending', 'waiting', 'running'):
                action_text = 'would skip' if self.dry_run else 'skipping'
                self.logger.debug('%s %s ad hoc command %s', action_text, ad_hoc_command.status, ad_hoc_command_display)
                skipped += 1
            else:
                action_text = 'would delete' if self.dry_run else 'deleting'
                self.logger.info('%s %s', action_text, ad_hoc_command_display)
                if not self.dry_run:
                    pk_list.append(ad_hoc_command.pk)
                    ad_hoc_command.delete()
                deleted += 1

        if not self.dry_run:
            self._cascade_delete_job_events(AdHocCommand, pk_list)

        skipped += AdHocCommand.objects.filter(created__gte=self.cutoff).count()
        return skipped, deleted

    def cleanup_project_updates(self):
        skipped, deleted = 0, 0
        project_updates = ProjectUpdate.objects.filter(created__lt=self.cutoff)
        pk_list = []
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
                    pk_list.append(pu.pk)
                    pu.delete()
                deleted += 1

        if not self.dry_run:
            self._cascade_delete_job_events(ProjectUpdate, pk_list)

        skipped += ProjectUpdate.objects.filter(created__gte=self.cutoff).count()
        return skipped, deleted

    def cleanup_inventory_updates(self):
        skipped, deleted = 0, 0
        inventory_updates = InventoryUpdate.objects.filter(created__lt=self.cutoff)
        pk_list = []
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
                    pk_list.append(iu.pk)
                    iu.delete()
                deleted += 1

        if not self.dry_run:
            self._cascade_delete_job_events(InventoryUpdate, pk_list)

        skipped += InventoryUpdate.objects.filter(created__gte=self.cutoff).count()
        return skipped, deleted

    def cleanup_management_jobs(self):
        skipped, deleted = 0, 0
        system_jobs = SystemJob.objects.filter(created__lt=self.cutoff)
        pk_list = []
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
                    pk_list.append(sj.pk)
                    sj.delete()
                deleted += 1

        if not self.dry_run:
            self._cascade_delete_job_events(SystemJob, pk_list)

        skipped += SystemJob.objects.filter(created__gte=self.cutoff).count()
        return skipped, deleted

    def cleanup_workflow_jobs(self):
        skipped, deleted = 0, 0
        workflow_jobs = WorkflowJob.objects.filter(created__lt=self.cutoff)
        for workflow_job in workflow_jobs.iterator():
            workflow_job_display = '"{}" ({} nodes)'.format(str(workflow_job), workflow_job.workflow_nodes.count())
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
                str(notification), str(notification.created), notification.notification_type, notification.notifications_sent
            )
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

        model_names = ('jobs', 'ad_hoc_commands', 'project_updates', 'inventory_updates', 'management_jobs', 'workflow_jobs', 'notifications')
        models_to_cleanup = set()
        for m in model_names:
            if options.get('only_%s' % m, False):
                models_to_cleanup.add(m)
        if not models_to_cleanup:
            models_to_cleanup.update(model_names)

        # Completely disconnect all signal handlers.  This is very aggressive,
        # but it will be ok since this command is run in its own process.  The
        # core of the logic is borrowed from Signal.disconnect().
        for s in (pre_save, post_save, pre_delete, post_delete, m2m_changed):
            with s.lock:
                del s.receivers[:]
                s.sender_receivers_cache.clear()

        for m in model_names:
            if m not in models_to_cleanup:
                continue

            skipped, deleted = getattr(self, 'cleanup_%s' % m)()

            func = getattr(self, 'cleanup_%s_partition' % m, None)
            if func:
                skipped_partition, deleted_partition = func()
                skipped += skipped_partition
                deleted += deleted_partition

            if self.dry_run:
                self.logger.log(99, '%s: %d would be deleted, %d would be skipped.', m.replace('_', ' '), deleted, skipped)
            else:
                self.logger.log(99, '%s: %d deleted, %d skipped.', m.replace('_', ' '), deleted, skipped)
