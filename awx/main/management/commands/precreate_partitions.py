from django.conf import settings
from django.utils.timezone import now
from django.core.management.base import BaseCommand, CommandParser
from datetime import timedelta
from awx.main.utils.common import create_partition


class Command(BaseCommand):
    """Command used to precreate database partitions to avoid pg_dump locks"""

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('--count', dest='count', action='store', help='The amount of hours of partitions to create', type=int)

    def _create_partitioned_tables(self, count):
        start = now()
        while count > 0:
            for table in ("main_inventoryupdateevent", "main_jobevent", "main_projectupdateevent", "main_systemjobevent"):
                create_partition(table, start)
                print(f'Creating partitions for {table} {start}')
            start = start + timedelta(hours=1)
            count -= 1

    def handle(self, **options):
        self._create_partitioned_tables(options.get('count', 1))
