# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

from decimal import Decimal
import logging
import os

from django.core.validators import MinValueValidator
from django.db import models, connection
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils.timezone import now, timedelta

import redis
from solo.models import SingletonModel

from awx import __version__ as awx_application_version
from awx.api.versioning import reverse
from awx.main.fields import JSONBlob
from awx.main.managers import InstanceManager, UUID_DEFAULT
from awx.main.constants import JOB_FOLDER_PREFIX
from awx.main.models.base import BaseModel, HasEditsMixin, prevent_search
from awx.main.models.unified_jobs import UnifiedJob
from awx.main.utils.common import get_corrected_cpu, get_cpu_effective_capacity, get_corrected_memory, get_mem_effective_capacity
from awx.main.models.mixins import RelatedJobsMixin

# ansible-runner
from ansible_runner.utils.capacity import get_cpu_count, get_mem_in_bytes

__all__ = ('Instance', 'InstanceGroup', 'InstanceLink', 'TowerScheduleState')

logger = logging.getLogger('awx.main.models.ha')


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


class InstanceLink(BaseModel):
    source = models.ForeignKey('Instance', on_delete=models.CASCADE, related_name='+')
    target = models.ForeignKey('Instance', on_delete=models.CASCADE, related_name='reverse_peers')

    class States(models.TextChoices):
        ADDING = 'adding', _('Adding')
        ESTABLISHED = 'established', _('Established')
        REMOVING = 'removing', _('Removing')

    link_state = models.CharField(choices=States.choices, default=States.ESTABLISHED, max_length=16)

    class Meta:
        unique_together = ('source', 'target')


class Instance(HasPolicyEditsMixin, BaseModel):
    """A model representing an AWX instance running against this database."""

    objects = InstanceManager()

    # Fields set in instance registration
    uuid = models.CharField(max_length=40, default=UUID_DEFAULT)
    hostname = models.CharField(max_length=250, unique=True)
    ip_address = models.CharField(
        blank=True,
        null=True,
        default=None,
        max_length=50,
        unique=True,
    )
    # Auto-fields, implementation is different from BaseModel
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    # Fields defined in health check or heartbeat
    version = models.CharField(max_length=120, blank=True)
    cpu = models.DecimalField(
        default=Decimal(0.0),
        max_digits=4,
        decimal_places=1,
        editable=False,
    )
    memory = models.BigIntegerField(
        default=0,
        editable=False,
        help_text=_('Total system memory of this instance in bytes.'),
    )
    errors = models.TextField(
        default='',
        blank=True,
        editable=False,
        help_text=_('Any error details from the last health check.'),
    )
    last_seen = models.DateTimeField(
        null=True,
        editable=False,
        help_text=_('Last time instance ran its heartbeat task for main cluster nodes. Last known connection to receptor mesh for execution nodes.'),
    )
    last_health_check = models.DateTimeField(
        null=True,
        editable=False,
        help_text=_('Last time a health check was ran on this instance to refresh cpu, memory, and capacity.'),
    )
    # Capacity management
    capacity = models.PositiveIntegerField(
        default=100,
        editable=False,
    )
    capacity_adjustment = models.DecimalField(default=Decimal(1.0), max_digits=3, decimal_places=2, validators=[MinValueValidator(0)])
    enabled = models.BooleanField(default=True)
    managed_by_policy = models.BooleanField(default=True)

    cpu_capacity = models.IntegerField(
        default=0,
        editable=False,
    )
    mem_capacity = models.IntegerField(
        default=0,
        editable=False,
    )

    class Types(models.TextChoices):
        CONTROL = 'control', _("Control plane node")
        EXECUTION = 'execution', _("Execution plane node")
        HYBRID = 'hybrid', _("Controller and execution")
        HOP = 'hop', _("Message-passing node, no execution capability")

    node_type = models.CharField(default=Types.HYBRID, choices=Types.choices, max_length=16)

    class States(models.TextChoices):
        PROVISIONING = 'provisioning', _('Provisioning')
        PROVISION_FAIL = 'provision-fail', _('Provisioning Failure')
        INSTALLED = 'installed', _('Installed')
        READY = 'ready', _('Ready')
        UNAVAILABLE = 'unavailable', _('Unavailable')
        DEPROVISIONING = 'deprovisioning', _('De-provisioning')
        DEPROVISION_FAIL = 'deprovision-fail', _('De-provisioning Failure')

    node_state = models.CharField(choices=States.choices, default=States.READY, max_length=16)

    peers = models.ManyToManyField('self', symmetrical=False, through=InstanceLink, through_fields=('source', 'target'))

    class Meta:
        app_label = 'main'
        ordering = ("hostname",)

    POLICY_FIELDS = frozenset(('managed_by_policy', 'hostname', 'capacity_adjustment'))

    def get_absolute_url(self, request=None):
        return reverse('api:instance_detail', kwargs={'pk': self.pk}, request=request)

    @property
    def consumed_capacity(self):
        capacity_consumed = 0
        if self.node_type in ('hybrid', 'execution'):
            capacity_consumed += sum(x.task_impact for x in UnifiedJob.objects.filter(execution_node=self.hostname, status__in=('running', 'waiting')))
        if self.node_type in ('hybrid', 'control'):
            capacity_consumed += sum(
                settings.AWX_CONTROL_NODE_TASK_IMPACT for x in UnifiedJob.objects.filter(controller_node=self.hostname, status__in=('running', 'waiting'))
            )
        return capacity_consumed

    @property
    def remaining_capacity(self):
        return self.capacity - self.consumed_capacity

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

    def get_cleanup_task_kwargs(self, **kwargs):
        """
        Produce options to use for the command: ansible-runner worker cleanup
        returns a dict that is passed to the python interface for the runner method corresponding to that command
        any kwargs will override that key=value combination in the returned dict
        """
        vargs = dict()
        if settings.AWX_CLEANUP_PATHS:
            vargs['file_pattern'] = os.path.join(settings.AWX_ISOLATION_BASE_PATH, JOB_FOLDER_PREFIX % '*') + '*'
        vargs.update(kwargs)
        if not isinstance(vargs.get('grace_period'), int):
            vargs['grace_period'] = 60  # grace period of 60 minutes, need to set because CLI default will not take effect
        if 'exclude_strings' not in vargs and vargs.get('file_pattern'):
            active_pks = list(
                UnifiedJob.objects.filter(
                    (models.Q(execution_node=self.hostname) | models.Q(controller_node=self.hostname)) & models.Q(status__in=('running', 'waiting'))
                ).values_list('pk', flat=True)
            )
            if active_pks:
                vargs['exclude_strings'] = [JOB_FOLDER_PREFIX % job_id for job_id in active_pks]
        if 'remove_images' in vargs or 'image_prune' in vargs:
            vargs.setdefault('process_isolation_executable', 'podman')
        return vargs

    def is_lost(self, ref_time=None):
        if self.last_seen is None:
            return True
        if ref_time is None:
            ref_time = now()
        grace_period = settings.CLUSTER_NODE_HEARTBEAT_PERIOD * 2
        if self.node_type in ('execution', 'hop'):
            grace_period += settings.RECEPTOR_SERVICE_ADVERTISEMENT_PERIOD
        return self.last_seen < ref_time - timedelta(seconds=grace_period)

    def mark_offline(self, update_last_seen=False, perform_save=True, errors=''):
        if self.cpu_capacity == 0 and self.mem_capacity == 0 and self.capacity == 0 and self.errors == errors and (not update_last_seen):
            return
        self.cpu_capacity = self.mem_capacity = self.capacity = 0
        self.errors = errors
        if update_last_seen:
            self.last_seen = now()

        if perform_save:
            update_fields = ['capacity', 'cpu_capacity', 'mem_capacity', 'errors']
            if update_last_seen:
                update_fields += ['last_seen']
            self.save(update_fields=update_fields)

    def set_capacity_value(self):
        """Sets capacity according to capacity adjustment rule (no save)"""
        if self.enabled and self.node_type != 'hop':
            lower_cap = min(self.mem_capacity, self.cpu_capacity)
            higher_cap = max(self.mem_capacity, self.cpu_capacity)
            self.capacity = lower_cap + (higher_cap - lower_cap) * self.capacity_adjustment
        else:
            self.capacity = 0

    def refresh_capacity_fields(self):
        """Update derived capacity fields from cpu and memory (no save)"""
        if self.node_type == 'hop':
            self.cpu_capacity = 0
            self.mem_capacity = 0  # formula has a non-zero offset, so we make sure it is 0 for hop nodes
        else:
            self.cpu_capacity = get_cpu_effective_capacity(self.cpu)
            self.mem_capacity = get_mem_effective_capacity(self.memory)
        self.set_capacity_value()

    def save_health_data(self, version=None, cpu=0, memory=0, uuid=None, update_last_seen=False, errors=''):
        update_fields = ['errors']
        if self.node_type != 'hop':
            self.last_health_check = now()
            update_fields.append('last_health_check')

        if update_last_seen:
            self.last_seen = self.last_health_check
            update_fields.append('last_seen')

        if uuid is not None and self.uuid != uuid:
            if self.uuid is not None:
                logger.warning(f'Self-reported uuid of {self.hostname} changed from {self.uuid} to {uuid}')
            self.uuid = uuid
            update_fields.append('uuid')

        if version is not None and self.version != version:
            self.version = version
            update_fields.append('version')

        new_cpu = get_corrected_cpu(cpu)
        if new_cpu != self.cpu:
            self.cpu = new_cpu
            update_fields.append('cpu')

        new_memory = get_corrected_memory(memory)
        if new_memory != self.memory:
            self.memory = new_memory
            update_fields.append('memory')

        if not errors:
            self.refresh_capacity_fields()
            self.errors = ''
        else:
            self.mark_offline(perform_save=False, errors=errors)
        update_fields.extend(['cpu_capacity', 'mem_capacity', 'capacity'])

        # disabling activity stream will avoid extra queries, which is important for heatbeat actions
        from awx.main.signals import disable_activity_stream

        with disable_activity_stream():
            self.save(update_fields=update_fields)

    def local_health_check(self):
        """Only call this method on the instance that this record represents"""
        errors = None
        try:
            # if redis is down for some reason, that means we can't persist
            # playbook event data; we should consider this a zero capacity event
            redis.Redis.from_url(settings.BROKER_URL).ping()
        except redis.ConnectionError:
            errors = _('Failed to connect ot Redis')

        self.save_health_data(awx_application_version, get_cpu_count(), get_mem_in_bytes(), update_last_seen=True, errors=errors)


class InstanceGroup(HasPolicyEditsMixin, BaseModel, RelatedJobsMixin):
    """A model representing a Queue/Group of AWX Instances."""

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
    policy_instance_list = JSONBlob(
        default=list, blank=True, help_text=_("List of exact-match Instances that will always be automatically assigned to this group")
    )

    POLICY_FIELDS = frozenset(('policy_instance_list', 'policy_instance_minimum', 'policy_instance_percentage'))

    def get_absolute_url(self, request=None):
        return reverse('api:instance_group_detail', kwargs={'pk': self.pk}, request=request)

    @property
    def capacity(self):
        return sum(inst.capacity for inst in self.instances.all())

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

    def set_default_policy_fields(self):
        self.policy_instance_list = []
        self.policy_instance_minimum = 0
        self.policy_instance_percentage = 0


class TowerScheduleState(SingletonModel):
    schedule_last_run = models.DateTimeField(auto_now_add=True)


def schedule_policy_task():
    from awx.main.tasks.system import apply_cluster_membership_policies

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
