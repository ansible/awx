from django.core.management.base import BaseCommand
from awx.main.tasks.host_metrics import HostMetricInventoryCountTask


class Command(BaseCommand):
    help = 'Populate HostMetric.used_in_inventories with the count of inventories each host belongs to'

    def handle(self, *args, **options):
        rows = HostMetricInventoryCountTask.update_counts()
        self.stdout.write(f'Updated {rows} HostMetric records')
