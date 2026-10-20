# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from awx.main.utils.db import db_requirement_violations


class Command(BaseCommand):
    """Checks connection to the database, and prints out connection info if not connected"""

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = str(cursor.fetchone()[0])

        violations = db_requirement_violations()
        if violations:
            raise CommandError(violations)

        return "Database Version: {}".format(version)
