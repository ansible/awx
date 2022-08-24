import contextlib
import json
import logging
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import connection
from rest_framework.exceptions import PermissionDenied

import insights_analytics_collector as base

from awx.conf.license import get_license
from awx.main.models import Job
from awx.main.access import access_registry
from awx.main.analytics import collectors
from awx.main.analytics.package import Package
from awx.main.analytics.collection_json import CollectionJSON
from awx.main.utils import datetime_hook
from awx.main.utils.pglock import advisory_lock

logger = logging.getLogger('awx.main.analytics')


class AnalyticsCollector(base.Collector):
    def __init__(self, collection_type=base.Collector.SCHEDULED_COLLECTION, collector_module=collectors):
        super(AnalyticsCollector, self).__init__(collection_type=collection_type, collector_module=collector_module, logger=logger)

    def _is_valid_license(self):
        try:
            if get_license().get('license_type', 'UNLICENSED') == 'open':
                return False
            access_registry[Job](None).check_license()
        except PermissionDenied:
            logger.exception("A valid license was not found:")
            return False
        return True

    def _is_shipping_configured(self):
        if self.is_shipping_enabled():
            if not settings.INSIGHTS_TRACKING_STATE:
                logger.log(self.log_level, "Insights for Ansible Automation Platform not enabled. " "Use --dry-run to gather locally without sending.")
                return False

            if not (settings.AUTOMATION_ANALYTICS_URL and settings.REDHAT_USERNAME and settings.REDHAT_PASSWORD):
                logger.log(self.log_level, "Not gathering analytics, configuration is invalid. " "Use --dry-run to gather locally without sending.")
                return False

        return True

    @staticmethod
    def db_connection():
        return connection

    @classmethod
    def registered_collectors(cls, module=None):
        from awx.main.analytics import collectors

        return base.Collector.registered_collectors(collectors)

    @contextlib.contextmanager
    def _pg_advisory_lock(self, key, wait=False):
        """Use awx specific implementation to pass tests with sqlite3"""
        with advisory_lock(key, wait=wait) as lock:
            yield lock

    def _last_gathering(self):
        return settings.AUTOMATION_ANALYTICS_LAST_GATHER

    def _load_last_gathered_entries(self):
        from awx.conf.models import Setting

        last_entries = Setting.objects.filter(key='AUTOMATION_ANALYTICS_LAST_ENTRIES').first()
        last_gathered_entries = json.loads((last_entries.value if last_entries is not None else '') or '{}', object_hook=datetime_hook)
        return last_gathered_entries

    def _save_last_gathered_entries(self, last_gathered_entries):
        settings.AUTOMATION_ANALYTICS_LAST_ENTRIES = json.dumps(last_gathered_entries, cls=DjangoJSONEncoder)

    def _save_last_gather(self):
        from awx.main.signals import disable_activity_stream

        with disable_activity_stream():
            if not settings.AUTOMATION_ANALYTICS_LAST_GATHER or self.gather_until > settings.AUTOMATION_ANALYTICS_LAST_GATHER:
                # `AUTOMATION_ANALYTICS_LAST_GATHER` is set whether collection succeeds or fails;
                # if collection fails because of a persistent, underlying issue and we do not set last_gather,
                # we risk the collectors hitting an increasingly greater workload while the underlying issue
                # remains unresolved. Put simply, if collection fails, we just move on.

                # All that said, `AUTOMATION_ANALYTICS_LAST_GATHER` plays a much smaller role in determining
                # what is actually collected than it used to; collectors now mostly rely on their respective entry
                # under `last_entries` to determine what should be collected.
                settings.AUTOMATION_ANALYTICS_LAST_GATHER = self.gather_until

    @staticmethod
    def _package_class():
        return Package

    @staticmethod
    def _collection_json_class():
        return CollectionJSON
