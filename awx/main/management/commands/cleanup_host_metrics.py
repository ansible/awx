from django.core.management.base import BaseCommand
from django.conf import settings
from awx.main.tasks.host_metrics import HostMetricTask


class Command(BaseCommand):
    """
    This command provides cleanup task for HostMetric model.
    There are two modes, which run in following order:
    - soft cleanup
    - - Perform soft-deletion of all host metrics last automated 12 months ago or before.
        This is the same as issuing a DELETE request to /api/v2/host_metrics/N/ for all host metrics that match the criteria.
    - - updates columns delete, deleted_counter and last_deleted
    - hard cleanup
    - - Permanently erase from the database all host metrics last automated 36 months ago or before.
        This operation happens after the soft deletion has finished.
    """

    help = 'Run soft and hard-deletion of HostMetrics'

    def handle(self, *args, **options):
        HostMetricTask().cleanup(soft_threshold=settings.CLEANUP_HOST_METRICS_SOFT_THRESHOLD, hard_threshold=settings.CLEANUP_HOST_METRICS_HARD_THRESHOLD)
