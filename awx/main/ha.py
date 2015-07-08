# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# AWX
from awx.main.models import Instance

def is_ha_environment():
    """Return True if this is an HA environment, and False
    otherwise.
    """
    # If there are two or more instances, then we are in an HA environment.
    if Instance.objects.count() > 1:
        return True
    return False
