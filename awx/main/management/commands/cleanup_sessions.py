import logging
from django.core import management
from django.core.management.base import BaseCommand

from django.contrib.sessions.models import Session


class Command(BaseCommand):

    def init_logging(self):
        log_levels = dict(enumerate([logging.ERROR, logging.INFO,
                                     logging.DEBUG, 0]))
        self.logger = logging.getLogger('awx.main.commands.cleanup_sessions')
        self.logger.setLevel(log_levels.get(self.verbosity, 0))
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
        self.logger.propagate = False

    def execute(self, *args, **options):
        self.verbosity = int(options.get('verbosity', 1))
        self.init_logging()
        total_sessions = Session.objects.all().count()
        management.call_command('clearsessions')
        self.logger.info("Expired Sessions deleted {}".format(total_sessions - Session.objects.all().count()))
