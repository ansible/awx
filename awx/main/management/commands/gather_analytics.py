import logging
from awx.main.analytics import gather, ship
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    '''
    Gather AWX analytics data
    '''

    help = 'Gather AWX analytics data'

    def add_arguments(self, parser):
        parser.add_argument('--ship', dest='ship', action='store_true',
                            help='Enable to ship metrics via insights-client')

    def init_logging(self):
        self.logger = logging.getLogger('awx.main.analytics')
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
        self.logger.propagate = False

    def handle(self, *args, **options):
        tgz = gather()
        self.logger.debug(tgz)
        if options.get('ship'):
            ship(tgz)
