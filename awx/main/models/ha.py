# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models, connection
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.utils.timezone import now, timedelta

import redis
from solo.models import SingletonModel

from awx import __version__ as awx_application_version
from awx.api.versioning import reverse
from awx.main.managers import InstanceManager, InstanceGroupManager
from awx.main.fields import JSONField
from awx.main.models.base import BaseModel, HasEditsMixin, prevent_search
from awx.main.models.unified_jobs import UnifiedJob
from awx.main.utils import get_cpu_capacity, get_mem_capacity, get_system_task_capacity
from awx.main.models.mixins import RelatedJobsMixin

__all__ = ('Instance', 'InstanceGroup', 'TowerScheduleState')


class HasPolicyEditsMixin(HasEditsMixin):
    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        r = super(BaseModel, self).__init__(*args, **kwargs)
        self._prior_values_store = self._get_fields_snapshot()
        return r

    def save(self, *args, **kwargs):
        super(BaseModel, self).save(*args, **kwargs)
        self._prior_values_store = self._get_fields_snapshot()

    def has_policy_changes(self):
        if not hasattr(self, 'POLICY_FIELDS'):
            raise RuntimeError('HasPolicyEditsMixin Model needs to set POLICY_FIELDS')
        new_values = self._get_fields_snapshot(fields_set=self.POLICY_FIELDS)
        return self._values_have_edits(new_values)


class Instance(HasPolicyEditsMixin, BaseModel):
    """A model representing an AWX instance running against this database."""

    objects = InstanceManager()

    uuid = models.CharField(max_length=40)
    hostname = models.CharField(max_length=250, unique=True)
    ip_address = models.CharField(
        blank=True,
        null=True,
        default=None,
        max_length=50,
        unique=True,
    )
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    version = models.CharField(max_length=120, blank=True)
    capacity = models.PositiveIntegerField(
        default=100,
        editable=False,
    )
    capacity_adjustment = models.DecimalField(default=Decimal(1.0), max_digits=3, decimal_places=2, validators=[MinValueValidator(0)])
    enabled = models.BooleanField(default=True)
    managed_by_policy = models.BooleanField(default=True)
    cpu = models.IntegerField(
        default=0,
        editable=False,
    )
    memory = models.BigIntegerField(
        default=0,
        editable=False,
    )
    cpu_capacity = models.IntegerField(
        default=0,
        editable=False,
    )
    mem_capacity = models.IntegerField(
        default=0,
        editable=False,
    )

    class Meta:
        app_label = 'main'
        ordering = ("hostname",)

    POLICY_FIELDS = frozenset(('managed_by_policy', 'hostname', 'capacity_adjustment'))

    def get_absolute_url(self, request=None):
        return reverse('api:instance_detail', kwargs={'pk': self.pk}, request=request)

    @property
    def consumed_capacity(self):
        return sum(x.task_impact for x in UnifiedJob.objects.filter(execution_node=self.hostname, status__in=('running', 'waiting')))

    @property
    def remaining_capacity(self):
        return self.capacity - self.consumed_capacity

    @property
    def role(self):
        # NOTE: TODO: Likely to repurpose this once standalone ramparts are a thing
        return "awx"

    @property
    def jobs_running(self):
        return UnifiedJob.objects.filter(
            execution_node=self.hostname,
            status__in=(
                'running',
                'waiting',
            ),
        ).count()

    @property
    def jobs_total(self):
        return UnifiedJob.objects.filter(execution_node=self.hostname).count()

    @staticmethod
    def choose_online_control_plane_node():
        return random.choice(Instance.objects.filter(enabled=True).exclude(version__startswith='ansible-runner-').values_list('hostname', flat=True))

    def is_lost(self, ref_time=None):
        if ref_time is None:
            ref_time = now()
        grace_period = 120
        return self.modified < ref_time - timedelta(seconds=grace_period)

    def is_receptor(self):
        return self.version.startswith('ansible-runner-')


class InstanceGroup(HasPolicyEditsMixin, BaseModel, RelatedJobsMixin):
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
    is_container_group = models.BooleanField(default=False)
    credential = models.ForeignKey(
        'Credential',
        related_name='%(class)ss',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    )
    pod_spec_override = prevent_search(
        models.TextField(
            blank=True,
            default='',
        )
    )
    policy_instance_percentage = models.IntegerField(default=0, help_text=_("Percentage of Instances to automatically assign to this group"))
    policy_instance_minimum = models.IntegerField(default=0, help_text=_("Static minimum number of Instances to automatically assign to this group"))
    policy_instance_list = JSONField(
        default=[], blank=True, help_text=_("List of exact-match Instances that will always be automatically assigned to this group")
    )

    POLICY_FIELDS = frozenset(('policy_instance_list', 'policy_instance_minimum', 'policy_instance_percentage'))

    def get_absolute_url(self, request=None):
        return reverse('api:instance_group_detail', kwargs={'pk': self.pk}, request=request)

    @property
    def capacity(self):
        return sum([inst.capacity for inst in self.instances.all()])

    @property
    def jobs_running(self):
        return UnifiedJob.objects.filter(status__in=('running', 'waiting'), instance_group=self).count()

    @property
    def jobs_total(self):
        return UnifiedJob.objects.filter(instance_group=self).count()

    '''
    RelatedJobsMixin
    '''

    def _get_related_jobs(self):
        return UnifiedJob.objects.filter(instance_group=self)

    class Meta:
        app_label = 'main'

    @staticmethod
    def fit_task_to_most_remaining_capacity_instance(task, instances):
        instance_most_capacity = None
        for i in instances:
            if i.remaining_capacity >= task.task_impact and (
                instance_most_capacity is None or i.remaining_capacity > instance_most_capacity.remaining_capacity
            ):
                instance_most_capacity = i
        return instance_most_capacity

    @staticmethod
    def find_largest_idle_instance(instances):
        largest_instance = None
        for i in instances:
            if i.jobs_running == 0:
                if largest_instance is None:
                    largest_instance = i
                elif i.capacity > largest_instance.capacity:
                    largest_instance = i
        return largest_instance

    def set_default_policy_fields(self):
        self.policy_instance_list = []
        self.policy_instance_minimum = 0
        self.policy_instance_percentage = 0


class TowerScheduleState(SingletonModel):
    schedule_last_run = models.DateTimeField(auto_now_add=True)


def schedule_policy_task():
    from awx.main.tasks import apply_cluster_membership_policies

    connection.on_commit(lambda: apply_cluster_membership_policies.apply_async())


@receiver(post_save, sender=InstanceGroup)
def on_instance_group_saved(sender, instance, created=False, raw=False, **kwargs):
    if created or instance.has_policy_changes():
        if not instance.is_container_group:
            schedule_policy_task()
    elif created or instance.is_container_group:
        instance.set_default_policy_fields()


@receiver(post_save, sender=Instance)
def on_instance_saved(sender, instance, created=False, raw=False, **kwargs):
    if created or instance.has_policy_changes():
        schedule_policy_task()


@receiver(post_delete, sender=InstanceGroup)
def on_instance_group_deleted(sender, instance, using, **kwargs):
    if not instance.is_container_group:
        schedule_policy_task()


@receiver(post_delete, sender=Instance)
def on_instance_deleted(sender, instance, using, **kwargs):
    schedule_policy_task()


class UnifiedJobTemplateInstanceGroupMembership(models.Model):

    unifiedjobtemplate = models.ForeignKey('UnifiedJobTemplate', on_delete=models.CASCADE)
    instancegroup = models.ForeignKey('InstanceGroup', on_delete=models.CASCADE)
    position = models.PositiveIntegerField(
        null=True,
        default=None,
        db_index=True,
    )


class OrganizationInstanceGroupMembership(models.Model):

    organization = models.ForeignKey('Organization', on_delete=models.CASCADE)
    instancegroup = models.ForeignKey('InstanceGroup', on_delete=models.CASCADE)
    position = models.PositiveIntegerField(
        null=True,
        default=None,
        db_index=True,
    )


class InventoryInstanceGroupMembership(models.Model):

    inventory = models.ForeignKey('Inventory', on_delete=models.CASCADE)
    instancegroup = models.ForeignKey('InstanceGroup', on_delete=models.CASCADE)
    position = models.PositiveIntegerField(
        null=True,
        default=None,
        db_index=True,
    )
