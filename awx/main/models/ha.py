# Copyright (c) 2014 Ansible, Inc.
# All Rights Reserved.

from django.db import models
from awx.main.managers import InstanceManager


class Instance(models.Model):
    """A model representing an Ansible Tower instance, primary or secondary,
    running against this database.
    """
    objects = InstanceManager()

    uuid = models.CharField(max_length=40, unique=True)
    primary = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'main'

    @property
    def role(self):
        """Return the role of this instance, as a string."""
        if self.primary:
            return 'primary'
        return 'secondary'
