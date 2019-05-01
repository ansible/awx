import logging
from django.core import management
from django.core.management.base import BaseCommand

from awx.main.models import OAuth2AccessToken
from oauth2_provider.models import RefreshToken


class Command(BaseCommand):

    def init_logging(self):
        log_levels = dict(enumerate([logging.ERROR, logging.INFO,
                                     logging.DEBUG, 0]))
        self.logger = logging.getLogger('awx.main.commands.cleanup_tokens')
        self.logger.setLevel(log_levels.get(self.verbosity, 0))
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
        self.logger.propagate = False

    def execute(self, *args, **options):
        self.verbosity = int(options.get('verbosity', 1))
        self.init_logging()
        total_accesstokens = OAuth2AccessToken.objects.all().count()
        total_refreshtokens = RefreshToken.objects.all().count()
        management.call_command('cleartokens')
        self.logger.info("Expired OAuth 2 Access Tokens deleted: {}".format(total_accesstokens - OAuth2AccessToken.objects.all().count()))
        self.logger.info("Expired OAuth 2 Refresh Tokens deleted: {}".format(total_refreshtokens - RefreshToken.objects.all().count()))
