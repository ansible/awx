# Copyright (c) 2014 Ansible, Inc.
# All Rights Reserved.

from django.conf import settings

from awx.main.models import Instance


def is_ha_environment():
    """Return True if this is an HA environment, and False
    otherwise.
    """
    # If there are two or more instances, then we are in an HA environment.
    if Instance.objects.count() > 1:
        return True

    # If the database is not local, then we are in an HA environment.
    host = settings.DATABASES['default'].get('host', 'localhost')
    if host and host.lower() not in ('127.0.0.1', 'localhost'):
        return True

    # We are not in an HA environment.
    return False
