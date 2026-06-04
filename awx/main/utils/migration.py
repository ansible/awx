import logging

from django.db.migrations.executor import MigrationExecutor
from django.db import connections, DEFAULT_DB_ALIAS

logger = logging.getLogger('awx.main.utils.migration')


def is_database_synchronized(database=DEFAULT_DB_ALIAS):
    """Check if all migrations have been applied.
    Returns False if the database is unreachable.
    https://stackoverflow.com/questions/31838882/check-for-pending-django-migrations
    """
    try:
        connection = connections[database]
        connection.prepare_database()
        executor = MigrationExecutor(connection)
        targets = executor.loader.graph.leaf_nodes()
        return not executor.migration_plan(targets)
    except Exception:
        logger.warning("Database unavailable, assuming not synchronized.")
        return False
