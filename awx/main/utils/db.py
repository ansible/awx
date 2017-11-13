# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved.

# Django database
from django.db.migrations.loader import MigrationLoader
from django.db import connection

# Python
from itertools import chain
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


def get_all_field_names(model):
    # Implements compatibility with _meta.get_all_field_names
    # See: https://docs.djangoproject.com/en/1.11/ref/models/meta/#migrating-from-the-old-api
    return list(set(chain.from_iterable(
        (field.name, field.attname) if hasattr(field, 'attname') else (field.name,)
        for field in model._meta.get_fields()
        # For complete backwards compatibility, you may want to exclude
        # GenericForeignKey from the results.
        if not (field.many_to_one and field.related_model is None)
    )))
