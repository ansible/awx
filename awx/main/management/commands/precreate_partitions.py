from django.conf import settings
from django.utils.timezone import now
from django.core.management.base import BaseCommand
from datetime import timedelta
from awx.main.utils.common import create_partition


class Command(BaseCommand):
    """Command used to precreate database partitions to avoid pg_dump locks"""

    def _create_partitioned_tables(self):
        start = now()
        next_hour = start + timedelta(hours=1)
        for table in ("main_inventoryupdateevent", "main_jobevent", "main_projectupdateevent", "main_systemjobevent"):
            create_partition(table, start)
            create_partition(table, next_hour)

    def handle(self, **options):
        self._create_partitioned_tables()
