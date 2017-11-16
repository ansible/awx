# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.utils.timezone import now, timedelta

from solo.models import SingletonModel

from awx.api.versioning import reverse
from awx.main.managers import InstanceManager, InstanceGroupManager
from awx.main.fields import JSONField
from awx.main.models.inventory import InventoryUpdate
from awx.main.models.jobs import Job
from awx.main.models.projects import ProjectUpdate
from awx.main.models.unified_jobs import UnifiedJob

__all__ = ('Instance', 'InstanceGroup', 'JobOrigin', 'TowerScheduleState',)


class Instance(models.Model):
    """A model representing an AWX instance running against this database."""
    objects = InstanceManager()

    uuid = models.CharField(max_length=40)
    hostname = models.CharField(max_length=250, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    last_isolated_check = models.DateTimeField(
        null=True,
        editable=False,
        auto_now_add=True
    )
    version = models.CharField(max_length=24, blank=True)
    capacity = models.PositiveIntegerField(
        default=100,
        editable=False,
    )

    class Meta:
        app_label = 'main'

    def get_absolute_url(self, request=None):
        return reverse('api:instance_detail', kwargs={'pk': self.pk}, request=request)

    @property
    def consumed_capacity(self):
        return sum(x.task_impact for x in UnifiedJob.objects.filter(execution_node=self.hostname,
                                                                    status__in=('running', 'waiting')))

    @property
    def role(self):
        # NOTE: TODO: Likely to repurpose this once standalone ramparts are a thing
        return "awx"

    def is_lost(self, ref_time=None, isolated=False):
        if ref_time is None:
            ref_time = now()
        grace_period = 120
        if isolated:
            grace_period = settings.AWX_ISOLATED_PERIODIC_CHECK * 2
        return self.modified < ref_time - timedelta(seconds=grace_period)

    def is_controller(self):
        return Instance.objects.filter(rampart_groups__controller__instances=self).exists()


class InstanceGroup(models.Model):
    """A model representing a Queue/Group of AWX Instances."""
    objects = InstanceGroupManager()

    name = models.CharField(max_length=250, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    instances = models.ManyToManyField(
        'Instance',
        related_name='rampart_groups',
        editable=False,
        help_text=_('Instances that are members of this InstanceGroup'),
    )
    controller = models.ForeignKey(
        'InstanceGroup',
        related_name='controlled_groups',
        help_text=_('Instance Group to remotely control this group.'),
        editable=False,
        default=None,
        null=True
    )
    policy_instance_percentage = models.IntegerField(
        default=0,
        help_text=_("Percentage of Instances to automatically assign to this group")
    )
    policy_instance_minimum = models.IntegerField(
        default=0,
        help_text=_("Static minimum number of Instances to automatically assign to this group")
    )
    policy_instance_list = JSONField(
        default=[],
        blank=True,
        help_text=_("List of exact-match Instances that will always be automatically assigned to this group")
    )

    def get_absolute_url(self, request=None):
        return reverse('api:instance_group_detail', kwargs={'pk': self.pk}, request=request)

    @property
    def capacity(self):
        return sum([inst.capacity for inst in self.instances.all()])

    class Meta:
        app_label = 'main'


class TowerScheduleState(SingletonModel):
    schedule_last_run = models.DateTimeField(auto_now_add=True)


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


@receiver(post_save, sender=InstanceGroup)
def on_instance_group_saved(sender, instance, created=False, raw=False, **kwargs):
    if created:
        from awx.main.tasks import apply_cluster_membership_policies
        apply_cluster_membership_policies.apply_async(countdown=5)


@receiver(post_save, sender=Instance)
def on_instance_saved(sender, instance, created=False, raw=False, **kwargs):
    if created:
        from awx.main.tasks import apply_cluster_membership_policies
        apply_cluster_membership_policies.apply_async(countdown=5)


@receiver(post_delete, sender=InstanceGroup)
def on_instance_group_deleted(sender, instance, using, **kwargs):
    from awx.main.tasks import apply_cluster_membership_policies
    apply_cluster_membership_policies.apply_async(countdown=5)


@receiver(post_delete, sender=Instance)
def on_instance_deleted(sender, instance, using, **kwargs):
    from awx.main.tasks import apply_cluster_membership_policies
    apply_cluster_membership_policies.apply_async(countdown=5)


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
