# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved.

from copy import deepcopy

from django.db.backends.postgresql.base import DatabaseWrapper as PsycopgDatabaseWrapper
from django.conf import settings
from django.db.utils import DEFAULT_DB_ALIAS

from awx.settings.application_name import set_application_name, get_application_name


def set_connection_name(function):
    set_application_name(settings.DATABASES, settings.CLUSTER_HOST_ID, function=function)


def get_listener_params(alias=DEFAULT_DB_ALIAS):
    settings_dict = deepcopy(settings.DATABASES[alias])
    settings_dict['OPTIONS'] = deepcopy(settings_dict.get('OPTIONS', {}))

    # Modify the application name to distinguish from other connections the process might use
    settings_dict['OPTIONS']['application_name'] = get_application_name(settings.CLUSTER_HOST_ID, function='listener')

    # Apply overrides specifically for the listener connection
    for k, v in settings.LISTENER_DATABASES.get(alias, {}).items():
        if k != 'OPTIONS':
            settings_dict[k] = v
    for k, v in settings.LISTENER_DATABASES.get(alias, {}).get('OPTIONS', {}).items():
        settings_dict['OPTIONS'][k] = v

    # Reuse the Django postgres DB backend to create params for the psycopg library
    psycopg_params = PsycopgDatabaseWrapper(settings_dict).get_connection_params()
    psycopg_params['autocommit'] = True

    return psycopg_params
