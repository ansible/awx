# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved.

import psycopg
from typing import Union
from copy import deepcopy

from awx.settings.application_name import set_application_name

from django.conf import settings
from django.db import DEFAULT_DB_ALIAS, connection
from django.db.backends.postgresql.base import DatabaseWrapper as PsycopgDatabaseWrapper


def set_connection_name(function):
    set_application_name(settings.DATABASES, settings.CLUSTER_HOST_ID, function=function)


def bulk_update_sorted_by_id(model, objects, fields, batch_size=1000):
    """
    Perform a sorted bulk update on model instances to avoid database deadlocks.

    This function was introduced to prevent deadlocks observed in the AWX Controller
    when concurrent jobs attempt to update different fields on the same `main_hosts` table.
    Specifically, deadlocks occurred when one process updated `last_job_id` while another
    simultaneously updated `ansible_facts`.

    By sorting updates ID, we ensure a consistent update order,
    which helps avoid the row-level locking contention that can lead to deadlocks
    in PostgreSQL when multiple processes are involved.

    Returns:
        int: The number of rows affected by the update.
    """
    objects = [obj for obj in objects if obj.id is not None]
    if not objects:
        return 0  # Return 0 when nothing is updated

    sorted_objects = sorted(objects, key=lambda obj: obj.id)
    return model.objects.bulk_update(sorted_objects, fields, batch_size=batch_size)


# Django settings.DATABASES['alias'] dictionary type
dj_db_dict = dict[str, Union[str, int]]


def psycopg_connection_from_django(**kwargs) -> psycopg.Connection:
    "Compatibility with dispatcher connection factory, just returns the Django connection"
    return connection.connection


def psycopg_kwargs_from_settings_dict(settings_dict: dj_db_dict) -> dict:
    """Return psycopg connection creation kwargs given Django db settings info
    :param dict setting_dict: DATABASES in Django settings
    :return: kwargs that can be passed to psycopg.connect, or connection classes"""
    psycopg_params = PsycopgDatabaseWrapper(settings_dict).get_connection_params().copy()
    psycopg_params.pop('cursor_factory', None)
    psycopg_params.pop('context', None)
    return psycopg_params


def psycopg_conn_string_from_settings_dict(settings_dict: dj_db_dict) -> str:
    conn_params = psycopg_kwargs_from_settings_dict(settings_dict)
    return psycopg.conninfo.make_conninfo(**conn_params)


def combine_settings_dict(settings_dict1: dj_db_dict, settings_dict2: dj_db_dict, **extra_options) -> dj_db_dict:
    """Given two Django settings dictionaries, combine them and return a new settings_dict"""
    settings_dict = deepcopy(settings_dict1)
    settings_dict['OPTIONS'] = deepcopy(settings_dict.get('OPTIONS', {}))

    # These extra options are used by AWX to set application_name
    settings_dict['OPTIONS'].update(extra_options)

    # Apply overrides specifically for the listener connection
    for k, v in settings_dict2.items():
        if k != 'OPTIONS':
            settings_dict[k] = v

    for k, v in settings_dict2.get('OPTIONS', {}).items():
        settings_dict['OPTIONS'][k] = v

    return settings_dict


def get_pg_notify_params(alias: str = DEFAULT_DB_ALIAS, **extra_options) -> dict:
    pg_notify_overrides = {}
    if hasattr(settings, 'PG_NOTIFY_DATABASES'):
        pg_notify_overrides = settings.PG_NOTIFY_DATABASES.get(alias, {})
    elif hasattr(settings, 'LISTENER_DATABASES'):
        pg_notify_overrides = settings.LISTENER_DATABASES.get(alias, {})

    settings_dict = combine_settings_dict(settings.DATABASES[alias], pg_notify_overrides, **extra_options)

    # Reuse the Django postgres DB backend to create params for the psycopg library
    psycopg_params = psycopg_kwargs_from_settings_dict(settings_dict)

    return psycopg_params
