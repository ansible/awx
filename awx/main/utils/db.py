# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved.

import logging
from itertools import chain

from django.core.cache import cache
from django.db.migrations.executor import MigrationExecutor
from django.db import connection


logger = logging.getLogger('awx.main.utils.db')


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


def migration_in_progress_check_or_relase():
    '''A memcache flag is raised (set to True) to inform cluster
    that a migration is ongoing see main.apps.MainConfig.ready
    if the flag is True then the flag is removed on this instance if
        models-db consistency is observed
    effective value of migration flag is returned
    '''
    migration_in_progress = cache.get('migration_in_progress', False)
    if migration_in_progress:
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        if not bool(plan):
            logger.info('Detected that migration finished, migration flag taken down.')
            cache.delete('migration_in_progress')
            migration_in_progress = False
    return migration_in_progress
