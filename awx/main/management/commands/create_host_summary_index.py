from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Creates composite index (host_id, id DESC) on main_jobhostsummary to improve host list query performance.'

    INDEX_NAME = 'main_jobhostsumm_host_id_desc'
    TABLE_NAME = 'main_jobhostsummary'

    def _index_status(self):
        """Check whether the index exists in pg_class and whether it is valid.

        Returns:
            'valid'   - index exists and is usable; no action needed.
            'invalid' - index exists but was left in an invalid state by a
                        previous failed CREATE INDEX CONCURRENTLY; must be
                        dropped before retrying.
            None      - index does not exist; safe to create.
        """
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT pg_index.indisvalid FROM pg_class JOIN pg_index ON pg_class.oid = pg_index.indexrelid WHERE pg_class.relname = %s",
                [self.INDEX_NAME],
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return 'valid' if row[0] else 'invalid'

    def handle(self, *args, **options):
        status = self._index_status()

        if status == 'valid':
            self.stdout.write(f"Index {self.INDEX_NAME} already exists, nothing to do.")
            return

        if status == 'invalid':
            self.stdout.write(f"Dropping invalid index {self.INDEX_NAME} from a previous failed attempt...")
            with connection.cursor() as cursor:
                cursor.execute(f"DROP INDEX IF EXISTS {self.INDEX_NAME}")

        self.stdout.write(f"Creating index {self.INDEX_NAME} on {self.TABLE_NAME} (host_id, id DESC) concurrently...")

        # CREATE INDEX CONCURRENTLY cannot run inside a transaction.
        connection.ensure_connection()
        old_autocommit = connection.connection.autocommit
        connection.connection.autocommit = True
        try:
            with connection.cursor() as cursor:
                # Disable statement_timeout for this session — the customer may
                # have set ALTER ROLE ... SET statement_timeout which would kill
                # the index build on large tables.
                cursor.execute("SET statement_timeout = 0")
                cursor.execute(f"CREATE INDEX CONCURRENTLY {self.INDEX_NAME} ON {self.TABLE_NAME} (host_id, id DESC)")
        finally:
            connection.connection.autocommit = old_autocommit

        self.stdout.write(f"Index {self.INDEX_NAME} created successfully.")
