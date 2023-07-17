from awx.main.models import HostMetric
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    """
    Run soft-deleting of HostMetrics
    """

    help = 'Run soft-deleting of HostMetrics'

    def add_arguments(self, parser):
        parser.add_argument('--months-ago', type=int, dest='months-ago', action='store', help='Threshold in months for soft-deleting')

    def handle(self, *args, **options):
        months_ago = options.get('months-ago') or None

        if not months_ago:
            months_ago = getattr(settings, 'CLEANUP_HOST_METRICS_SOFT_THRESHOLD', 12)

        HostMetric.cleanup_task(months_ago)
