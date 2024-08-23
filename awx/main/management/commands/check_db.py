# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

import sys

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    """Checks connection to the database, and prints out connection info if not connected"""

    def handle(self, *args, **options):
        if connection.vendor == 'postgres':

            with connection.cursor() as cursor:
                cursor.execute("SELECT version()")
                version = str(cursor.fetchone()[0])

            # enforce the postgres version is a minimum of 12 (we need this for partitioning); if not, then terminate program with exit code of 1
            # In the future if we require a feature of a version of postgres > 12 this should be updated to reflect that.
            # The return of connection.pg_version is something like 12013
            if (connection.pg_version // 10000) < 12:
                self.stderr.write(f"At a minimum, postgres version 12 is required, found {version}\n")
                sys.exit(1)

            return "Database Version: {}".format(version)
        else:
            self.stderr.write(f"Running server with '{connection.vendor}' type database is not supported\n")
            sys.exit(1)
