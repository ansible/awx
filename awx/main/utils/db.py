# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved.

from typing import Optional

from awx.settings.application_name import set_application_name
from awx import MODE

from django.conf import settings
from django.db import connection


def set_connection_name(function):
    set_application_name(settings.DATABASES, settings.CLUSTER_HOST_ID, function=function)


MIN_PG_VERSION = 12


def db_requirement_violations() -> Optional[str]:
    if connection.vendor == 'postgresql':

        # enforce the postgres version is a minimum of 12 (we need this for partitioning); if not, then terminate program with exit code of 1
        # In the future if we require a feature of a version of postgres > 12 this should be updated to reflect that.
        # The return of connection.pg_version is something like 12013
        major_version = connection.pg_version // 10000
        if major_version < MIN_PG_VERSION:
            return f"At a minimum, postgres version {MIN_PG_VERSION} is required, found {major_version}\n"

        return None
    else:
        if MODE == 'production':
            return f"Running server with '{connection.vendor}' type database is not supported\n"
        return None
