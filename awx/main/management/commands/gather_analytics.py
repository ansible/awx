import logging
from awx.main.analytics import gather, ship
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    '''
    Gather AWX analytics data
    '''

    help = 'Gather AWX analytics data'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', dest='dry-run', action='store_true',
                            help='Gather analytics without shipping. Works even if analytics are disabled in settings.')
        parser.add_argument('--ship', dest='ship', action='store_true',
                            help='Enable to ship metrics to the Red Hat Cloud')

    def init_logging(self):
        self.logger = logging.getLogger('awx.main.analytics')
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
        self.logger.propagate = False

    def handle(self, *args, **options):
        self.init_logging()
        opt_ship = options.get('ship')
        opt_dry_run = options.get('dry-run')
        if opt_ship and opt_dry_run:
            self.logger.error('Both --ship and --dry-run cannot be processed at the same time.')
            return
        tgz = gather(collection_type='manual' if not opt_dry_run else 'dry-run')
        if tgz:
            self.logger.debug(tgz)
        if opt_ship:
            ship(tgz)
