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
from django.db.models import Q
from django.utils.timezone import now

# AWX
from awx.main.models import Schedule, SystemJobTemplate
from awx.main.signals import disable_activity_stream, disable_computed_fields

from awx.main.utils.deletion import AWXCollector, pre_delete


class Command(BaseCommand):
    """
    Management command to cleanup old schedules.
    """

    help = 'Remove old schedules from the database.'

    def add_arguments(self, parser):
        parser.add_argument('--days', dest='days', type=int, default=90, metavar='N', help='Remove schedules inactive more than N days ago. Defaults to 90.')
        parser.add_argument('--dry-run', dest='dry_run', action='store_true', default=False, help='Dry run mode (show items that would ' 'be removed)')

    def cleanup_schedules(self):
        skipped, deleted = 0, 0

        batch_size = 1000000
        system_schedules = Schedule.objects.filter(unified_job_template__in=SystemJobTemplate.objects.all())
        active_schedules = Schedule.objects.enabled().after(now())

        while True:
            # get queryset for available schedules to remove
            qs = Schedule.objects.filter(Q(modified__lt=self.cutoff) | Q(next_run__isnull=True)).exclude(
                Q(pk__in=system_schedules) | Q(pk__in=active_schedules)
            )
            # get pk list for the first N (batch_size) objects
            pk_list = qs[0:batch_size].values_list('pk', flat=True)
            # You cannot delete queries with sql LIMIT set, so we must
            # create a new query from this pk_list
            qs_batch = Schedule.objects.filter(pk__in=pk_list)
            just_deleted = 0
            if not self.dry_run:

                del_query = pre_delete(qs_batch)
                collector = AWXCollector(del_query.db)
                collector.collect(del_query)
                _, models_deleted = collector.delete()
                if models_deleted:
                    just_deleted = models_deleted['main.Schedule']
                deleted += just_deleted
            else:
                just_deleted = 0  # break from loop, this is dry run
                deleted = qs.count()

            if just_deleted == 0:
                break

        skipped += (
            Schedule.objects.filter(Q(modified__gte=self.cutoff) | Q(next_run__isnull=True))
            .exclude(Q(pk__in=system_schedules) | Q(pk__in=active_schedules))
            .count()
        )
        return skipped, deleted

    def init_logging(self):
        log_levels = dict(enumerate([logging.ERROR, logging.INFO, logging.DEBUG, 0]))
        self.logger = logging.getLogger('awx.main.commands.cleanup_schedules')
        self.logger.setLevel(log_levels.get(self.verbosity, 0))
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
        self.logger.propagate = False

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

        with disable_activity_stream(), disable_computed_fields():
            skipped_partition, deleted_partition = self.cleanup_schedules()
            skipped = skipped_partition
            deleted = deleted_partition

            if self.dry_run:
                self.logger.log(99, 'Schedules: %d would be deleted, %d would be skipped.', deleted, skipped)
            else:
                self.logger.log(99, 'Schedules: %d deleted, %d skipped.', deleted, skipped)
