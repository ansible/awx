# Copyright (c) 2014 Ansible, Inc.
# All Rights Reserved.

import sys

from django.conf import settings
from django.db import models


class HostManager(models.Manager):
    """Custom manager class for Hosts model."""

    def active_count(self):
        """Return count of active, unique hosts for licensing."""
        try:
            return self.filter(active=True, inventory__active=True).distinct('name').count()
        except NotImplementedError: # For unit tests only, SQLite doesn't support distinct('name')
            return len(set(self.filter(active=True, inventory__active=True).values_list('name', flat=True)))

class InstanceManager(models.Manager):
    """A custom manager class for the Instance model.

    Provides "table-level" methods including getting the currently active
    instance or role.
    """
    def me(self):
        """Return the currently active instance."""
        # If we are running unit tests, return a stub record.
        if len(sys.argv) >= 2 and sys.argv[1] == 'test':
            return self.model(id=1, primary=True,
                              uuid='00000000-0000-0000-0000-000000000000')

        # Return the appropriate record from the database.
        return self.get(uuid=settings.SYSTEM_UUID)

    def my_role(self):
        """Return the role of the currently active instance, as a string
        ('primary' or 'secondary').
        """
        # If we are running unit tests, we are primary, because reasons.
        if len(sys.argv) >= 2 and sys.argv[1] == 'test':
            return 'primary'

        # Check if this instance is primary; if so, return "primary", otherwise
        # "secondary".
        if self.me().primary:
            return 'primary'
        return 'secondary'

    def primary(self):
        """Return the primary instance."""
        # If we are running unit tests, return a stub record.
        if len(sys.argv) >= 2 and sys.argv[1] == 'test':
            return self.model(id=1, primary=True,
                              uuid='00000000-0000-0000-0000-000000000000')

        # Return the appropriate record from the database.
        return self.get(primary=True)
