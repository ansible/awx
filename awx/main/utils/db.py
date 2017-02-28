# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved.

# Django database
from django.db.migrations.loader import MigrationLoader
from django.db import connection

# Python
import re


def get_tower_migration_version():
    loader = MigrationLoader(connection, ignore_no_migrations=True)
    v = '000'
    for app_name, migration_name in loader.applied_migrations:
        if app_name == 'main':
            version_captures = re.findall('^[0-9]{4}_v([0-9]{3})_', migration_name)
            if len(version_captures) == 1:
                migration_version = version_captures[0]
                if migration_version > v:
                    v = migration_version
    return v
