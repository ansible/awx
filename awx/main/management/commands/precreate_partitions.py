from django.utils.timezone import now
from django.core.management.base import BaseCommand, CommandParser
from datetime import timedelta
from awx.main.utils.common import create_partition, unified_job_class_to_event_table_name
from awx.main.models import Job, SystemJob, ProjectUpdate, InventoryUpdate, AdHocCommand


class Command(BaseCommand):
    """Command used to precreate database partitions to avoid pg_dump locks"""

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('--count', dest='count', action='store', help='The amount of hours of partitions to create', type=int, default=1)

    def _create_partitioned_tables(self, count):
        tables = list()
        for model in (Job, SystemJob, ProjectUpdate, InventoryUpdate, AdHocCommand):
            tables.append(unified_job_class_to_event_table_name(model))
        start = now()
        while count > 0:
            for table in tables:
                create_partition(table, start)
                print(f'Created partitions for {table} {start}')
            start = start + timedelta(hours=1)
            count -= 1

    def handle(self, **options):
        self._create_partitioned_tables(count=options.get('count'))
