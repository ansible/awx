# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import os
from IPy import IP

# Django
from django.conf import settings

# AWX
from awx.main.models import Instance

def is_ha_environment():
    """Return True if this is an HA environment, and False
    otherwise.
    """
    # If there are two or more instances, then we are in an HA environment.
    if Instance.objects.count() > 1:
        return True

    # If the database is not local, then we are in an HA environment.
    host = settings.DATABASES['default'].get('HOST', 'localhost')

    # Is host special case 'localhost' ?
    if host is 'localhost':
        return False

    # Check if host is an absolute file (i.e. named socket)
    if os.path.isabs(host):
        return False

    # Is host a LOCAL or REMOTE ip address ?
    try:
        if IP(host).iptype() is 'LOOPBACK':
            return False
        else:
            return True
    except ValueError:
        pass

    # host may be a domain name like postgres.mycompany.com
    # Assume HA Environment
    return True
