# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

import sys

from django.db import models
from django.conf import settings


class HostManager(models.Manager):
    """Custom manager class for Hosts model."""

    def active_count(self):
        """Return count of active, unique hosts for licensing."""
        try:
            return self.order_by('name').distinct('name').count()
        except NotImplementedError: # For unit tests only, SQLite doesn't support distinct('name')
            return len(set(self.values_list('name', flat=True)))

class InstanceManager(models.Manager):
    """A custom manager class for the Instance model.

    Provides "table-level" methods including getting the currently active
    instance or role.
    """
    def me(self):
        """Return the currently active instance."""
        # If we are running unit tests, return a stub record.
        if settings.IS_TESTING(sys.argv):
            return self.model(id=1,
                              hostname='localhost',
                              uuid='00000000-0000-0000-0000-000000000000')

        node = self.filter(hostname=settings.CLUSTER_HOST_ID)
        if node.exists():
            return node[0]
        raise RuntimeError("No instance found with the current cluster host id")

    def my_role(self):
        # NOTE: TODO: Likely to repurpose this once standalone ramparts are a thing
        return "tower"
