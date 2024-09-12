from django.db.migrations.executor import MigrationExecutor
from django.db import connections, DEFAULT_DB_ALIAS


def is_database_synchronized(database=DEFAULT_DB_ALIAS):
    """_summary_
    Ensure all migrations have ran
    https://stackoverflow.com/questions/31838882/check-for-pending-django-migrations
    """
    connection = connections[database]
    connection.prepare_database()
    executor = MigrationExecutor(connection)
    targets = executor.loader.graph.leaf_nodes()
    return not executor.migration_plan(targets)
