"""
Daily cleanup job.

Can be run as a cronjob to clean out old data from the database (only expired
sessions at the moment).
"""

from django_extensions.management.jobs import DailyJob


class Job(DailyJob):
    help = "Cache (db) cleanup Job"

    def execute(self):
        from django.conf import settings
        from django.db import transaction
        import os

        try:
            from django.utils import timezone
        except ImportError:
            timezone = None

        if hasattr(settings, 'CACHES') and timezone:
            from django.core.cache import get_cache
            from django.db import router, connections

            for cache_name, cache_options in settings.CACHES.iteritems():
                if cache_options['BACKEND'].endswith("DatabaseCache"):
                    cache = get_cache(cache_name)
                    db = router.db_for_write(cache.cache_model_class)
                    cursor = connections[db].cursor()
                    now = timezone.now()
                    cache._cull(db, cursor, now)
                    transaction.commit_unless_managed(using=db)
            return

        if hasattr(settings, 'CACHE_BACKEND'):
            if settings.CACHE_BACKEND.startswith('db://'):
                from django.db import connection
                os.environ['TZ'] = settings.TIME_ZONE
                table_name = settings.CACHE_BACKEND[5:]
                cursor = connection.cursor()
                cursor.execute(
                    "DELETE FROM %s WHERE %s < current_timestamp;" % (
                        connection.ops.quote_name(table_name),
                        connection.ops.quote_name('expires')
                    )
                )
                transaction.commit_unless_managed()
