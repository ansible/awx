# Copyright (c) 2014 Ansible, Inc.
# All Rights Reserved.

from django.db import models

from awx.main.managers import InstanceManager
from awx.main.models import UnifiedJob


class Instance(models.Model):
    """A model representing an Ansible Tower instance, primary or secondary,
    running against this database.
    """
    objects = InstanceManager()

    uuid = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField(protocol='both', unpack_ipv4=True)
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


class JobOrigin(models.Model):
    """A model representing the relationship between a unified job and
    the instance that was responsible for starting that job.

    It may be possible that a job has no origin (the common reason for this
    being that the job was started on Tower < 2.1 before origins were a thing).
    This is fine, and code should be able to handle it. A job with no origin
    is always assumed to *not* have the current instance as its origin.
    """
    unified_job = models.ForeignKey(UnifiedJob)
    instance = models.ForeignKey(Instance)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'main'
