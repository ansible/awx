# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved
import logging
import sys

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from awx.main.utils.subscriptions import (
    SubscriptionManager,
    SubscriptionManagerSettingsError,
    SubscriptionManagerRefreshError,
    logger as subscriptions_logger,
)


class Command(BaseCommand):
    """Refresh and save RHSM or Satellite entitlement certificate for Tower."""
    help = 'Refresh and save RHSM or Satellite entitlement certificate for Tower.'

    def set_logging_level(self, logger, level):
        log_levels = dict(enumerate([logging.WARNING, logging.INFO,
                                     logging.DEBUG, 0]))
        logger.setLevel(log_levels.get(level, 0))

    def handle(self, *args, **options):
        self.verbosity = int(options.get('verbosity', 1))

        self.set_logging_level(subscriptions_logger, self.verbosity)

        try:
            params = SubscriptionManager.get_init_params()
            submgr = SubscriptionManager(*params)
            submgr.refresh_entitlement_certs_and_save()
        except SubscriptionManagerSettingsError as e:
            raise CommandError(e.error_msgs)
        except SubscriptionManagerRefreshError as e:
            raise CommandError(e)

        return 'Successfully refreshed your Tower entitlement certificate.'
