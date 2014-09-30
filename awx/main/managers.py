# Copyright (c) 2014 Ansible, Inc.
# All Rights Reserved.

from django.conf import settings
from django.db import models
from django.utils.functional import cached_property


class InstanceManager(models.Manager):
    """A custom manager class for the Instance model.

    Provides "table-level" methods including getting the currently active
    instance or role.
    """
    @cached_property
    def me(self):
        """Return the currently active instance."""
        return self.get(uuid=settings.SYSTEM_UUID)

    @cached_property
    def my_role(self):
        """Return the role of the currently active instance, as a string
        ('primary' or 'secondary').
        """
        if self.me.primary:
            return 'primary'
        return 'secondary'
