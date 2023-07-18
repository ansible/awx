from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
from awx.main.tasks.host_metrics import HostMetricTask


class Command(BaseCommand):
    """
    Run soft/hard-deleting of HostMetrics
    """

    help = 'Run soft/hard-deleting of HostMetrics'

    def add_arguments(self, parser):
        parser.add_argument('--soft', type=int, nargs='?', default=None, const=0, help='Threshold in months for soft-deleting')
        parser.add_argument('--hard', type=int, nargs='?', default=None, const=0, help='Threshold in months for hard-deleting')

    def handle(self, *args, **options):
        soft_threshold = options.get('soft')
        hard_threshold = options.get('hard')

        if soft_threshold is None and hard_threshold is None:
            return _("Specify either --soft or --hard argument")

        HostMetricTask().cleanup(soft_threshold=soft_threshold, hard_threshold=hard_threshold)
