from django.core.management.base import BaseCommand
from awx.main.tasks.host_metrics import HostMetricInventoryCountTask


class Command(BaseCommand):
    """Populate stored host metric inventory counts on demand."""

    help = 'Populate HostMetric.used_in_inventories with the count of inventories each host belongs to'

    def handle(self, *args, **options):
        """Run the inventory count refresh and print how many rows changed."""
        rows = HostMetricInventoryCountTask.update_counts()
        self.stdout.write(f'Updated {rows} HostMetric records')
