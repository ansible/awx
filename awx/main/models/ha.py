# Copyright (c) 2015 Ansible, Inc. (formerly AnsibleWorks, Inc.)
# All Rights Reserved.

import functools

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from awx.main.managers import InstanceManager
from awx.main.models.inventory import InventoryUpdate
from awx.main.models.jobs import Job
from awx.main.models.projects import ProjectUpdate
from awx.main.models.unified_jobs import UnifiedJob, CAN_CANCEL

__all__ = ('Instance', 'JobOrigin')


class Instance(models.Model):
    """A model representing an Ansible Tower instance, primary or secondary,
    running against this database.
    """
    objects = InstanceManager()

    uuid = models.CharField(max_length=40, unique=True)
    hostname = models.CharField(max_length=250, unique=True)
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

    @functools.wraps(models.Model.save)
    def save(self, *args, **kwargs):
        """Save the instance. If this is a secondary instance, then ensure
        that any currently-running jobs that this instance started are
        canceled.
        """
        # Perform the normal save.
        result = super(Instance, self).save(*args, **kwargs)

        # If this is not a primary instance, then kill any jobs that this
        # instance was responsible for starting.
        if not self.primary:
            for job in UnifiedJob.objects.filter(job_origin__instance=self,
                                                 status__in=CAN_CANCEL):
                job.cancel()

        # Return back the original result.
        return result


class JobOrigin(models.Model):
    """A model representing the relationship between a unified job and
    the instance that was responsible for starting that job.

    It may be possible that a job has no origin (the common reason for this
    being that the job was started on Tower < 2.1 before origins were a thing).
    This is fine, and code should be able to handle it. A job with no origin
    is always assumed to *not* have the current instance as its origin.
    """
    unified_job = models.OneToOneField(UnifiedJob, related_name='job_origin')
    instance = models.ForeignKey(Instance)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'main'


# Unfortunately, the signal can't just be connected against UnifiedJob; it
# turns out that creating a model's subclass doesn't fire the signal for the
# superclass model.
@receiver(post_save, sender=InventoryUpdate)
@receiver(post_save, sender=Job)
@receiver(post_save, sender=ProjectUpdate)
def on_job_create(sender, instance, created=False, raw=False, **kwargs):
    """When a new job is created, save a record of its origin (the machine
    that started the job).
    """
    # Sanity check: We only want to create a JobOrigin record in cases where
    # we are making a new record, and in normal situations.
    #
    # In other situations, we simply do nothing.
    if raw or not created:
        return

    # Create the JobOrigin record, which attaches to the current instance
    # (which started the job).
    job_origin, new = JobOrigin.objects.get_or_create(
        instance=Instance.objects.me(),
        unified_job=instance,
    )
