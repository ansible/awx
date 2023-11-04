# Python
import logging

# Django
from django.db.models import Q
from django.core.management.base import BaseCommand
from django.utils.timezone import now

# AWX
from awx.main.models import Schedule, SystemJobTemplate


class Command(BaseCommand):
    """
    Management command to cleanup old schedules.
    """

    help = 'Remove old schedules from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            dest='days',
            type=int,
            default=90,
            metavar='N',
            help='Remove schedules with no next run and that have not been modified for N days (system job schedules are excluded)',
        )
        parser.add_argument('--dry-run', dest='dry_run', action='store_true', default=False, help='Dry run mode (show schedules that would be removed)')
        parser.add_argument(
            '--batch-size', dest='batch_size', type=int, default=500, metavar='X', help='Remove schedules in batch of X schedules. Defaults to 500.'
        )

    def init_logging(self):
        log_levels = dict(enumerate([logging.ERROR, logging.INFO, logging.DEBUG, 0]))
        self.logger = logging.getLogger('awx.main.commands.cleanup_schedules')
        self.logger.setLevel(log_levels.get(self.verbosity, 0))
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
        self.logger.propagate = False

    def cleanup_schedules(self):
        schedules_to_delete = (
            Schedule.objects.filter(Q(next_run__isnull=True), Q(modified__lt=self.cutoff))
            .exclude(unified_job_template__in=SystemJobTemplate.objects.all())
            .values_list('pk', flat=True)
        )

        deleted = len(schedules_to_delete)
        skipped = Schedule.objects.all().count() - deleted

        if self.dry_run:
            self.logger.info(f"{deleted} schedules would be deleted, {skipped} schedules would be skipped.")
            return

        for batch_idx, batch_start in enumerate(range(0, len(schedules_to_delete), self.batch_size)):
            pk_to_delete = schedules_to_delete[batch_start : batch_start + self.batch_size]
            Schedule.objects.filter(pk__in=pk_to_delete).delete()
            self.logger.info(f"Batch {batch_idx+1} deleted {len(pk_to_delete)} schedules")

        self.logger.info(f"Deleted {deleted} schedules in total, skipped {skipped} schedules.")

    def handle(self, *args, **options):
        self.verbosity = int(options.get('verbosity', 1))
        self.init_logging()
        self.days = int(options.get('days', 90))
        self.cutoff = now() - datetime.timedelta(days=self.days)
        self.dry_run = bool(options.get('dry_run', False))
        self.batch_size = int(options.get('batch_size', 500))
        self.cleanup_schedules()
