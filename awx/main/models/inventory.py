# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import datetime
import logging
import re
import copy
from urlparse import urljoin
import os.path

# Django
from django.conf import settings
from django.db import models, connection
from django.utils.translation import ugettext_lazy as _
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from django.db.models import Q

# AWX
from awx.api.versioning import reverse
from awx.main.constants import CLOUD_PROVIDERS
from awx.main.consumers import emit_channel_notification
from awx.main.fields import (
    ImplicitRoleField,
    JSONBField,
    SmartFilterField,
)
from awx.main.managers import HostManager
from awx.main.models.base import * # noqa
from awx.main.models.unified_jobs import * # noqa
from awx.main.models.mixins import ResourceMixin, TaskManagerInventoryUpdateMixin
from awx.main.models.notifications import (
    NotificationTemplate,
    JobNotificationMixin,
)
from awx.main.utils import _inventory_updates

__all__ = ['Inventory', 'Host', 'Group', 'InventorySource', 'InventoryUpdate',
           'CustomInventoryScript', 'SmartInventoryMembership']

logger = logging.getLogger('awx.main.models.inventory')


class Inventory(CommonModelNameNotUnique, ResourceMixin):
    '''
    an inventory source contains lists and hosts.
    '''

    KIND_CHOICES = [
        ('', _('Hosts have a direct link to this inventory.')),
        ('smart', _('Hosts for inventory generated using the host_filter property.')),
    ]

    class Meta:
        app_label = 'main'
        verbose_name_plural = _('inventories')
        unique_together = [('name', 'organization')]
        ordering = ('name',)

    organization = models.ForeignKey(
        'Organization',
        related_name='inventories',
        help_text=_('Organization containing this inventory.'),
        on_delete=models.SET_NULL,
        null=True,
    )
    variables = models.TextField(
        blank=True,
        default='',
        help_text=_('Inventory variables in JSON or YAML format.'),
    )
    has_active_failures = models.BooleanField(
        default=False,
        editable=False,
        help_text=_('Flag indicating whether any hosts in this inventory have failed.'),
    )
    total_hosts = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text=_('Total number of hosts in this inventory.'),
    )
    hosts_with_active_failures = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text=_('Number of hosts in this inventory with active failures.'),
    )
    total_groups = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text=_('Total number of groups in this inventory.'),
    )
    groups_with_active_failures = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text=_('Number of groups in this inventory with active failures.'),
    )
    has_inventory_sources = models.BooleanField(
        default=False,
        editable=False,
        help_text=_('Flag indicating whether this inventory has any external inventory sources.'),
    )
    total_inventory_sources = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text=_('Total number of external inventory sources configured within this inventory.'),
    )
    inventory_sources_with_failures = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text=_('Number of external inventory sources in this inventory with failures.'),
    )
    kind = models.CharField(
        max_length=32,
        choices=KIND_CHOICES,
        blank=True,
        default='',
        help_text=_('Kind of inventory being represented.'),
    )
    host_filter = SmartFilterField(
        blank=True,
        null=True,
        default=None,
        help_text=_('Filter that will be applied to the hosts of this inventory.'),
    )
    instance_groups = models.ManyToManyField(
        'InstanceGroup',
        blank=True,
    )
    admin_role = ImplicitRoleField(
        parent_role='organization.admin_role',
    )
    update_role = ImplicitRoleField(
        parent_role='admin_role',
    )
    adhoc_role = ImplicitRoleField(
        parent_role='admin_role',
    )
    use_role = ImplicitRoleField(
        parent_role='adhoc_role',
    )
    read_role = ImplicitRoleField(parent_role=[
        'organization.auditor_role',
        'update_role',
        'use_role',
        'admin_role',
    ])
    insights_credential = models.ForeignKey(
        'Credential',
        related_name='insights_inventories',
        help_text=_('Credentials to be used by hosts belonging to this inventory when accessing Red Hat Insights API.'),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        default=None,
    )
    pending_deletion = models.BooleanField(
        default=False,
        editable=False,
        help_text=_('Flag indicating the inventory is being deleted.'),
    )


    def get_absolute_url(self, request=None):
        return reverse('api:inventory_detail', kwargs={'pk': self.pk}, request=request)

    variables_dict = VarsDictProperty('variables')

    def get_group_hosts_map(self):
        '''
        Return dictionary mapping group_id to set of child host_id's.
        '''
        # FIXME: Cache this mapping?
        group_hosts_kw = dict(group__inventory_id=self.pk, host__inventory_id=self.pk)
        group_hosts_qs = Group.hosts.through.objects.filter(**group_hosts_kw)
        group_hosts_qs = group_hosts_qs.values_list('group_id', 'host_id')
        group_hosts_map = {}
        for group_id, host_id in group_hosts_qs:
            group_host_ids = group_hosts_map.setdefault(group_id, set())
            group_host_ids.add(host_id)
        return group_hosts_map

    def get_group_parents_map(self):
        '''
        Return dictionary mapping group_id to set of parent group_id's.
        '''
        # FIXME: Cache this mapping?
        group_parents_kw = dict(from_group__inventory_id=self.pk, to_group__inventory_id=self.pk)
        group_parents_qs = Group.parents.through.objects.filter(**group_parents_kw)
        group_parents_qs = group_parents_qs.values_list('from_group_id', 'to_group_id')
        group_parents_map = {}
        for from_group_id, to_group_id in group_parents_qs:
            group_parents = group_parents_map.setdefault(from_group_id, set())
            group_parents.add(to_group_id)
        return group_parents_map

    def get_group_children_map(self):
        '''
        Return dictionary mapping group_id to set of child group_id's.
        '''
        # FIXME: Cache this mapping?
        group_parents_kw = dict(from_group__inventory_id=self.pk, to_group__inventory_id=self.pk)
        group_parents_qs = Group.parents.through.objects.filter(**group_parents_kw)
        group_parents_qs = group_parents_qs.values_list('from_group_id', 'to_group_id')
        group_children_map = {}
        for from_group_id, to_group_id in group_parents_qs:
            group_children = group_children_map.setdefault(to_group_id, set())
            group_children.add(from_group_id)
        return group_children_map

    def update_host_computed_fields(self):
        '''
        Update computed fields for all hosts in this inventory.
        '''
        hosts_to_update = {}
        hosts_qs = self.hosts
        # Define queryset of all hosts with active failures.
        hosts_with_active_failures = hosts_qs.filter(last_job_host_summary__isnull=False, last_job_host_summary__failed=True).values_list('pk', flat=True)
        # Find all hosts that need the has_active_failures flag set.
        hosts_to_set = hosts_qs.filter(has_active_failures=False, pk__in=hosts_with_active_failures)
        for host_pk in hosts_to_set.values_list('pk', flat=True):
            host_updates = hosts_to_update.setdefault(host_pk, {})
            host_updates['has_active_failures'] = True
        # Find all hosts that need the has_active_failures flag cleared.
        hosts_to_clear = hosts_qs.filter(has_active_failures=True).exclude(pk__in=hosts_with_active_failures)
        for host_pk in hosts_to_clear.values_list('pk', flat=True):
            host_updates = hosts_to_update.setdefault(host_pk, {})
            host_updates['has_active_failures'] = False
        # Define queryset of all hosts with cloud inventory sources.
        hosts_with_cloud_inventory = hosts_qs.filter(inventory_sources__source__in=CLOUD_INVENTORY_SOURCES).values_list('pk', flat=True)
        # Find all hosts that need the has_inventory_sources flag set.
        hosts_to_set = hosts_qs.filter(has_inventory_sources=False, pk__in=hosts_with_cloud_inventory)
        for host_pk in hosts_to_set.values_list('pk', flat=True):
            host_updates = hosts_to_update.setdefault(host_pk, {})
            host_updates['has_inventory_sources'] = True
        # Find all hosts that need the has_inventory_sources flag cleared.
        hosts_to_clear = hosts_qs.filter(has_inventory_sources=True).exclude(pk__in=hosts_with_cloud_inventory)
        for host_pk in hosts_to_clear.values_list('pk', flat=True):
            host_updates = hosts_to_update.setdefault(host_pk, {})
            host_updates['has_inventory_sources'] = False
        # Now apply updates to hosts where needed (in batches).
        all_update_pks = hosts_to_update.keys()
        for offset in xrange(0, len(all_update_pks), 500):
            update_pks = all_update_pks[offset:(offset + 500)]
            for host in hosts_qs.filter(pk__in=update_pks):
                host_updates = hosts_to_update[host.pk]
                for field, value in host_updates.items():
                    setattr(host, field, value)
                host.save(update_fields=host_updates.keys())

    def update_group_computed_fields(self):
        '''
        Update computed fields for all active groups in this inventory.
        '''
        group_children_map = self.get_group_children_map()
        group_hosts_map = self.get_group_hosts_map()
        active_host_pks = set(self.hosts.values_list('pk', flat=True))
        failed_host_pks = set(self.hosts.filter(last_job_host_summary__failed=True).values_list('pk', flat=True))
        # active_group_pks = set(self.groups.values_list('pk', flat=True))
        failed_group_pks = set() # Update below as we check each group.
        groups_with_cloud_pks = set(self.groups.filter(inventory_sources__source__in=CLOUD_INVENTORY_SOURCES).values_list('pk', flat=True))
        groups_to_update = {}

        # Build list of group pks to check, starting with the groups at the
        # deepest level within the tree.
        root_group_pks = set(self.root_groups.values_list('pk', flat=True))
        group_depths = {} # pk: max_depth

        def update_group_depths(group_pk, current_depth=0):
            max_depth = group_depths.get(group_pk, -1)
            # Arbitrarily limit depth to avoid hitting Python recursion limit (which defaults to 1000).
            if current_depth > 100:
                return
            if current_depth > max_depth:
                group_depths[group_pk] = current_depth
            for child_pk in group_children_map.get(group_pk, set()):
                update_group_depths(child_pk, current_depth + 1)
        for group_pk in root_group_pks:
            update_group_depths(group_pk)
        group_pks_to_check = [x[1] for x in sorted([(v,k) for k,v in group_depths.items()], reverse=True)]

        for group_pk in group_pks_to_check:
            # Get all children and host pks for this group.
            parent_pks_to_check = set([group_pk])
            parent_pks_checked = set()
            child_pks = set()
            host_pks = set()
            while parent_pks_to_check:
                for parent_pk in list(parent_pks_to_check):
                    c_ids = group_children_map.get(parent_pk, set())
                    child_pks.update(c_ids)
                    parent_pks_to_check.remove(parent_pk)
                    parent_pks_checked.add(parent_pk)
                    parent_pks_to_check.update(c_ids - parent_pks_checked)
                    h_ids = group_hosts_map.get(parent_pk, set())
                    host_pks.update(h_ids)
            # Define updates needed for this group.
            group_updates = groups_to_update.setdefault(group_pk, {})
            group_updates.update({
                'total_hosts': len(active_host_pks & host_pks),
                'has_active_failures': bool(failed_host_pks & host_pks),
                'hosts_with_active_failures': len(failed_host_pks & host_pks),
                'total_groups': len(child_pks),
                'groups_with_active_failures': len(failed_group_pks & child_pks),
                'has_inventory_sources': bool(group_pk in groups_with_cloud_pks),
            })
            if group_updates['has_active_failures']:
                failed_group_pks.add(group_pk)

        # Now apply updates to each group as needed (in batches).
        all_update_pks = groups_to_update.keys()
        for offset in xrange(0, len(all_update_pks), 500):
            update_pks = all_update_pks[offset:(offset + 500)]
            for group in self.groups.filter(pk__in=update_pks):
                group_updates = groups_to_update[group.pk]
                for field, value in group_updates.items():
                    if getattr(group, field) != value:
                        setattr(group, field, value)
                    else:
                        group_updates.pop(field)
                if group_updates:
                    group.save(update_fields=group_updates.keys())

    def update_computed_fields(self, update_groups=True, update_hosts=True):
        '''
        Update model fields that are computed from database relationships.
        '''
        logger.debug("Going to update inventory computed fields")
        if update_hosts:
            self.update_host_computed_fields()
        if update_groups:
            self.update_group_computed_fields()
        active_hosts = self.hosts
        failed_hosts = active_hosts.filter(has_active_failures=True)
        active_groups = self.groups
        failed_groups = active_groups.filter(has_active_failures=True)
        active_inventory_sources = self.inventory_sources.filter(source__in=CLOUD_INVENTORY_SOURCES)
        failed_inventory_sources = active_inventory_sources.filter(last_job_failed=True)
        computed_fields = {
            'has_active_failures': bool(failed_hosts.count()),
            'total_hosts': active_hosts.count(),
            'hosts_with_active_failures': failed_hosts.count(),
            'total_groups': active_groups.count(),
            'groups_with_active_failures': failed_groups.count(),
            'has_inventory_sources': bool(active_inventory_sources.count()),
            'total_inventory_sources': active_inventory_sources.count(),
            'inventory_sources_with_failures': failed_inventory_sources.count(),
        }
        # CentOS python seems to have issues clobbering the inventory on poor timing during certain operations
        iobj = Inventory.objects.get(id=self.id)
        for field, value in computed_fields.items():
            if getattr(iobj, field) != value:
                setattr(iobj, field, value)
            else:
                computed_fields.pop(field)
        if computed_fields:
            iobj.save(update_fields=computed_fields.keys())
        logger.debug("Finished updating inventory computed fields")

    def websocket_emit_status(self, status):
        connection.on_commit(lambda: emit_channel_notification(
            'inventories-status_changed',
            {'group_name': 'inventories', 'inventory_id': self.id, 'status': status}
        ))

    @property
    def root_groups(self):
        group_pks = self.groups.values_list('pk', flat=True)
        return self.groups.exclude(parents__pk__in=group_pks).distinct()

    def clean_insights_credential(self):
        if self.kind == 'smart' and self.insights_credential:
            raise ValidationError(_("Assignment not allowed for Smart Inventory"))
        if self.insights_credential and self.insights_credential.credential_type.kind != 'insights':
            raise ValidationError(_("Credential kind must be 'insights'."))
        return self.insights_credential

    @transaction.atomic
    def schedule_deletion(self, user_id=None):
        from awx.main.tasks import delete_inventory
        from awx.main.signals import activity_stream_delete
        if self.pending_deletion is True:
            raise RuntimeError("Inventory is already pending deletion.")
        self.pending_deletion = True
        self.save(update_fields=['pending_deletion'])
        self.jobtemplates.clear()
        activity_stream_delete(Inventory, self, inventory_delete_flag=True)
        self.websocket_emit_status('pending_deletion')
        delete_inventory.delay(self.pk, user_id)

    def _update_host_smart_inventory_memeberships(self):
        if self.kind == 'smart' and settings.AWX_REBUILD_SMART_MEMBERSHIP:
            def on_commit():
                from awx.main.tasks import update_host_smart_inventory_memberships
                update_host_smart_inventory_memberships.delay()
            connection.on_commit(on_commit)

    def save(self, *args, **kwargs):
        self._update_host_smart_inventory_memeberships()
        super(Inventory, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self._update_host_smart_inventory_memeberships()
        super(Inventory, self).delete(*args, **kwargs)


class SmartInventoryMembership(BaseModel):
    '''
    A lookup table for Host membership in Smart Inventory
    '''

    class Meta:
        app_label = 'main'
        unique_together = (('host', 'inventory'),)

    inventory = models.ForeignKey('Inventory', related_name='+', on_delete=models.CASCADE)
    host = models.ForeignKey('Host', related_name='+', on_delete=models.CASCADE)


class Host(CommonModelNameNotUnique):
    '''
    A managed node
    '''

    class Meta:
        app_label = 'main'
        unique_together = (("name", "inventory"),) # FIXME: Add ('instance_id', 'inventory') after migration.
        ordering = ('name',)

    inventory = models.ForeignKey(
        'Inventory',
        related_name='hosts',
        on_delete=models.CASCADE,
    )
    smart_inventories = models.ManyToManyField(
        'Inventory',
        related_name='+',
        through='SmartInventoryMembership',
    )
    enabled = models.BooleanField(
        default=True,
        help_text=_('Is this host online and available for running jobs?'),
    )
    instance_id = models.CharField(
        max_length=1024,
        blank=True,
        default='',
        help_text=_('The value used by the remote inventory source to uniquely identify the host'),
    )
    variables = models.TextField(
        blank=True,
        default='',
        help_text=_('Host variables in JSON or YAML format.'),
    )
    last_job = models.ForeignKey(
        'Job',
        related_name='hosts_as_last_job+',
        null=True,
        default=None,
        editable=False,
        on_delete=models.SET_NULL,
    )
    last_job_host_summary = models.ForeignKey(
        'JobHostSummary',
        related_name='hosts_as_last_job_summary+',
        blank=True,
        null=True,
        default=None,
        editable=False,
        on_delete=models.SET_NULL,
    )
    has_active_failures  = models.BooleanField(
        default=False,
        editable=False,
        help_text=_('Flag indicating whether the last job failed for this host.'),
    )
    has_inventory_sources = models.BooleanField(
        default=False,
        editable=False,
        help_text=_('Flag indicating whether this host was created/updated from any external inventory sources.'),
    )
    inventory_sources = models.ManyToManyField(
        'InventorySource',
        related_name='hosts',
        editable=False,
        help_text=_('Inventory source(s) that created or modified this host.'),
    )
    ansible_facts = JSONBField(
        blank=True,
        default={},
        help_text=_('Arbitrary JSON structure of most recent ansible_facts, per-host.'),
    )
    ansible_facts_modified = models.DateTimeField(
        default=None,
        editable=False,
        null=True,
        help_text=_('The date and time ansible_facts was last modified.'),
    )
    insights_system_id = models.TextField(
        blank=True,
        default=None,
        null=True,
        db_index=True,
        help_text=_('Red Hat Insights host unique identifier.'),
    )

    objects = HostManager()

    def __unicode__(self):
        return self.name

    def get_absolute_url(self, request=None):
        return reverse('api:host_detail', kwargs={'pk': self.pk}, request=request)

    def update_computed_fields(self, update_inventory=True, update_groups=True):
        '''
        Update model fields that are computed from database relationships.
        '''
        has_active_failures = bool(self.last_job_host_summary and
                                   self.last_job_host_summary.failed)
        active_inventory_sources = self.inventory_sources.filter(source__in=CLOUD_INVENTORY_SOURCES)
        computed_fields = {
            'has_active_failures': has_active_failures,
            'has_inventory_sources': bool(active_inventory_sources.count()),
        }
        for field, value in computed_fields.items():
            if getattr(self, field) != value:
                setattr(self, field, value)
            else:
                computed_fields.pop(field)
        if computed_fields:
            self.save(update_fields=computed_fields.keys())
        # Groups and inventory may also need to be updated when host fields
        # change.
        # NOTE: I think this is no longer needed
        # if update_groups:
        #     for group in self.all_groups:
        #         group.update_computed_fields()
        # if update_inventory:
        #     self.inventory.update_computed_fields(update_groups=False,
        #                                           update_hosts=False)
        # Rebuild summary fields cache
    variables_dict = VarsDictProperty('variables')

    @property
    def all_groups(self):
        '''
        Return all groups of which this host is a member, avoiding infinite
        recursion in the case of cyclical group relations.
        '''
        group_parents_map = self.inventory.get_group_parents_map()
        group_pks = set(self.groups.values_list('pk', flat=True))
        child_pks_to_check = set()
        child_pks_to_check.update(group_pks)
        child_pks_checked = set()
        while child_pks_to_check:
            for child_pk in list(child_pks_to_check):
                p_ids = group_parents_map.get(child_pk, set())
                group_pks.update(p_ids)
                child_pks_to_check.remove(child_pk)
                child_pks_checked.add(child_pk)
                child_pks_to_check.update(p_ids - child_pks_checked)
        return Group.objects.filter(pk__in=group_pks).distinct()

    # Use .job_host_summaries.all() to get jobs affecting this host.
    # Use .job_events.all() to get events affecting this host.

    '''
    We don't use timestamp, but we may in the future.
    '''
    def update_ansible_facts(self, module, facts, timestamp=None):
        if module == "ansible":
            self.ansible_facts.update(facts)
        else:
            self.ansible_facts[module] = facts
        self.save()

    def get_effective_host_name(self):
        '''
        Return the name of the host that will be used in actual ansible
        command run.
        '''
        host_name = self.name
        if 'ansible_ssh_host' in self.variables_dict:
            host_name = self.variables_dict['ansible_ssh_host']
        if 'ansible_host' in self.variables_dict:
            host_name = self.variables_dict['ansible_host']
        return host_name

    def _update_host_smart_inventory_memeberships(self):
        if settings.AWX_REBUILD_SMART_MEMBERSHIP:
            def on_commit():
                from awx.main.tasks import update_host_smart_inventory_memberships
                update_host_smart_inventory_memberships.delay()
            connection.on_commit(on_commit)

    def save(self, *args, **kwargs):
        self._update_host_smart_inventory_memeberships()
        super(Host, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self._update_host_smart_inventory_memeberships()
        super(Host, self).delete(*args, **kwargs)


class Group(CommonModelNameNotUnique):
    '''
    A group containing managed hosts.  A group or host may belong to multiple
    groups.
    '''

    class Meta:
        app_label = 'main'
        unique_together = (("name", "inventory"),)
        ordering = ('name',)

    inventory = models.ForeignKey(
        'Inventory',
        related_name='groups',
        on_delete=models.CASCADE,
    )
    # Can also be thought of as: parents == member_of, children == members
    parents = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='children',
        blank=True,
    )
    variables = models.TextField(
        blank=True,
        default='',
        help_text=_('Group variables in JSON or YAML format.'),
    )
    hosts = models.ManyToManyField(
        'Host',
        related_name='groups',
        blank=True,
        help_text=_('Hosts associated directly with this group.'),
    )
    total_hosts = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text=_('Total number of hosts directly or indirectly in this group.'),
    )
    has_active_failures = models.BooleanField(
        default=False,
        editable=False,
        help_text=_('Flag indicating whether this group has any hosts with active failures.'),
    )
    hosts_with_active_failures = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text=_('Number of hosts in this group with active failures.'),
    )
    total_groups = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text=_('Total number of child groups contained within this group.'),
    )
    groups_with_active_failures = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text=_('Number of child groups within this group that have active failures.'),
    )
    has_inventory_sources = models.BooleanField(
        default=False,
        editable=False,
        help_text=_('Flag indicating whether this group was created/updated from any external inventory sources.'),
    )
    inventory_sources = models.ManyToManyField(
        'InventorySource',
        related_name='groups',
        editable=False,
        help_text=_('Inventory source(s) that created or modified this group.'),
    )

    def __unicode__(self):
        return self.name

    def get_absolute_url(self, request=None):
        return reverse('api:group_detail', kwargs={'pk': self.pk}, request=request)

    @transaction.atomic
    def delete_recursive(self):
        from awx.main.utils import ignore_inventory_computed_fields
        from awx.main.tasks import update_inventory_computed_fields
        from awx.main.signals import disable_activity_stream, activity_stream_delete


        def mark_actual():
            all_group_hosts = Group.hosts.through.objects.select_related("host", "group").filter(group__inventory=self.inventory)
            group_hosts = {'groups': {}, 'hosts': {}}
            all_group_parents = Group.parents.through.objects.select_related("from_group", "to_group").filter(from_group__inventory=self.inventory)
            group_children = {}
            group_parents = {}
            marked_hosts = []
            marked_groups = [self.id]

            for pairing in all_group_hosts:
                if pairing.group_id not in group_hosts['groups']:
                    group_hosts['groups'][pairing.group_id] = []
                if pairing.host_id not in group_hosts['hosts']:
                    group_hosts['hosts'][pairing.host_id] = []
                group_hosts['groups'][pairing.group_id].append(pairing.host_id)
                group_hosts['hosts'][pairing.host_id].append(pairing.group_id)

            for pairing in all_group_parents:
                if pairing.to_group_id not in group_children:
                    group_children[pairing.to_group_id] = []
                if pairing.from_group_id not in group_parents:
                    group_parents[pairing.from_group_id] = []
                group_children[pairing.to_group_id].append(pairing.from_group_id)
                group_parents[pairing.from_group_id].append(pairing.to_group_id)

            linked_children = [(self.id, g) for g in group_children[self.id]] if self.id in group_children else []

            if self.id in group_hosts['groups']:
                for host in copy.copy(group_hosts['groups'][self.id]):
                    group_hosts['hosts'][host].remove(self.id)
                    group_hosts['groups'][self.id].remove(host)
                    if len(group_hosts['hosts'][host]) < 1:
                        marked_hosts.append(host)

            for subgroup in linked_children:
                parent, group = subgroup
                group_parents[group].remove(parent)
                group_children[parent].remove(group)
                if len(group_parents[group]) > 0:
                    continue
                for host in copy.copy(group_hosts['groups'].get(group, [])):
                    group_hosts['hosts'][host].remove(group)
                    group_hosts['groups'][group].remove(host)
                    if len(group_hosts['hosts'][host]) < 1:
                        marked_hosts.append(host)
                if group in group_children:
                    for direct_child in group_children[group]:
                        linked_children.append((group, direct_child))
                marked_groups.append(group)
            Group.objects.filter(id__in=marked_groups).delete()
            Host.objects.filter(id__in=marked_hosts).delete()
            update_inventory_computed_fields.delay(self.inventory.id)
        with ignore_inventory_computed_fields():
            with disable_activity_stream():
                mark_actual()
            activity_stream_delete(None, self)

    def update_computed_fields(self):
        '''
        Update model fields that are computed from database relationships.
        '''
        active_hosts = self.all_hosts
        failed_hosts = active_hosts.filter(last_job_host_summary__failed=True)
        active_groups = self.all_children
        # FIXME: May not be accurate unless we always update groups depth-first.
        failed_groups = active_groups.filter(has_active_failures=True)
        active_inventory_sources = self.inventory_sources.filter(source__in=CLOUD_INVENTORY_SOURCES)
        computed_fields = {
            'total_hosts': active_hosts.count(),
            'has_active_failures': bool(failed_hosts.count()),
            'hosts_with_active_failures': failed_hosts.count(),
            'total_groups': active_groups.count(),
            'groups_with_active_failures': failed_groups.count(),
            'has_inventory_sources': bool(active_inventory_sources.count()),
        }
        for field, value in computed_fields.items():
            if getattr(self, field) != value:
                setattr(self, field, value)
            else:
                computed_fields.pop(field)
        if computed_fields:
            self.save(update_fields=computed_fields.keys())

    variables_dict = VarsDictProperty('variables')

    def get_all_parents(self, except_pks=None):
        '''
        Return all parents of this group recursively.  The group itself will
        be excluded unless there is a cycle leading back to it.
        '''
        group_parents_map = self.inventory.get_group_parents_map()
        child_pks_to_check = set([self.pk])
        child_pks_checked = set()
        parent_pks = set()
        while child_pks_to_check:
            for child_pk in list(child_pks_to_check):
                p_ids = group_parents_map.get(child_pk, set())
                parent_pks.update(p_ids)
                child_pks_to_check.remove(child_pk)
                child_pks_checked.add(child_pk)
                child_pks_to_check.update(p_ids - child_pks_checked)
        return Group.objects.filter(pk__in=parent_pks).distinct()

    @property
    def all_parents(self):
        return self.get_all_parents()

    def get_all_children(self, except_pks=None):
        '''
        Return all children of this group recursively.  The group itself will
        be excluded unless there is a cycle leading back to it.
        '''
        group_children_map = self.inventory.get_group_children_map()
        parent_pks_to_check = set([self.pk])
        parent_pks_checked = set()
        child_pks = set()
        while parent_pks_to_check:
            for parent_pk in list(parent_pks_to_check):
                c_ids = group_children_map.get(parent_pk, set())
                child_pks.update(c_ids)
                parent_pks_to_check.remove(parent_pk)
                parent_pks_checked.add(parent_pk)
                parent_pks_to_check.update(c_ids - parent_pks_checked)
        return Group.objects.filter(pk__in=child_pks).distinct()

    @property
    def all_children(self):
        return self.get_all_children()

    def get_all_hosts(self, except_group_pks=None):
        '''
        Return all hosts associated with this group or any of its children.
        '''
        group_children_map = self.inventory.get_group_children_map()
        group_hosts_map = self.inventory.get_group_hosts_map()
        parent_pks_to_check = set([self.pk])
        parent_pks_checked = set()
        host_pks = set()
        while parent_pks_to_check:
            for parent_pk in list(parent_pks_to_check):
                c_ids = group_children_map.get(parent_pk, set())
                parent_pks_to_check.remove(parent_pk)
                parent_pks_checked.add(parent_pk)
                parent_pks_to_check.update(c_ids - parent_pks_checked)
                h_ids = group_hosts_map.get(parent_pk, set())
                host_pks.update(h_ids)
        return Host.objects.filter(pk__in=host_pks).distinct()

    @property
    def all_hosts(self):
        return self.get_all_hosts()

    @property
    def job_host_summaries(self):
        from awx.main.models.jobs import JobHostSummary
        return JobHostSummary.objects.filter(host__in=self.all_hosts)

    @property
    def job_events(self):
        from awx.main.models.jobs import JobEvent
        return JobEvent.objects.filter(host__in=self.all_hosts)

    @property
    def ad_hoc_commands(self):
        from awx.main.models.ad_hoc_commands import AdHocCommand
        return AdHocCommand.objects.filter(hosts__in=self.all_hosts)


class InventorySourceOptions(BaseModel):
    '''
    Common fields for InventorySource and InventoryUpdate.
    '''

    SOURCE_CHOICES = [
        ('', _('Manual')),
        ('file', _('File, Directory or Script')),
        ('scm', _('Sourced from a Project')),
        ('ec2', _('Amazon EC2')),
        ('gce', _('Google Compute Engine')),
        ('azure_rm', _('Microsoft Azure Resource Manager')),
        ('vmware', _('VMware vCenter')),
        ('satellite6', _('Red Hat Satellite 6')),
        ('cloudforms', _('Red Hat CloudForms')),
        ('openstack', _('OpenStack')),
        ('custom', _('Custom Script')),
    ]

    # From the options of the Django management base command
    INVENTORY_UPDATE_VERBOSITY_CHOICES = [
        (0, '0 (WARNING)'),
        (1, '1 (INFO)'),
        (2, '2 (DEBUG)'),
    ]

    # Use tools/scripts/get_ec2_filter_names.py to build this list.
    INSTANCE_FILTER_NAMES = [
        "architecture",
        "association.allocation-id",
        "association.association-id",
        "association.ip-owner-id",
        "association.public-ip",
        "availability-zone",
        "block-device-mapping.attach-time",
        "block-device-mapping.delete-on-termination",
        "block-device-mapping.device-name",
        "block-device-mapping.status",
        "block-device-mapping.volume-id",
        "client-token",
        "dns-name",
        "group-id",
        "group-name",
        "hypervisor",
        "iam-instance-profile.arn",
        "image-id",
        "instance-id",
        "instance-lifecycle",
        "instance-state-code",
        "instance-state-name",
        "instance-type",
        "instance.group-id",
        "instance.group-name",
        "ip-address",
        "kernel-id",
        "key-name",
        "launch-index",
        "launch-time",
        "monitoring-state",
        "network-interface-private-dns-name",
        "network-interface.addresses.association.ip-owner-id",
        "network-interface.addresses.association.public-ip",
        "network-interface.addresses.primary",
        "network-interface.addresses.private-ip-address",
        "network-interface.attachment.attach-time",
        "network-interface.attachment.attachment-id",
        "network-interface.attachment.delete-on-termination",
        "network-interface.attachment.device-index",
        "network-interface.attachment.instance-id",
        "network-interface.attachment.instance-owner-id",
        "network-interface.attachment.status",
        "network-interface.availability-zone",
        "network-interface.description",
        "network-interface.group-id",
        "network-interface.group-name",
        "network-interface.mac-address",
        "network-interface.network-interface.id",
        "network-interface.owner-id",
        "network-interface.requester-id",
        "network-interface.requester-managed",
        "network-interface.source-destination-check",
        "network-interface.status",
        "network-interface.subnet-id",
        "network-interface.vpc-id",
        "owner-id",
        "placement-group-name",
        "platform",
        "private-dns-name",
        "private-ip-address",
        "product-code",
        "product-code.type",
        "ramdisk-id",
        "reason",
        "requester-id",
        "reservation-id",
        "root-device-name",
        "root-device-type",
        "source-dest-check",
        "spot-instance-request-id",
        "state-reason-code",
        "state-reason-message",
        "subnet-id",
        "tag-key",
        "tag-value",
        "tenancy",
        "virtualization-type",
        "vpc-id"
    ]

    class Meta:
        abstract = True

    source = models.CharField(
        max_length=32,
        choices=SOURCE_CHOICES,
        blank=True,
        default='',
    )
    source_path = models.CharField(
        max_length=1024,
        blank=True,
        default='',
    )
    source_script = models.ForeignKey(
        'CustomInventoryScript',
        null=True,
        default=None,
        blank=True,
        on_delete=models.SET_NULL,
    )
    source_vars = models.TextField(
        blank=True,
        default='',
        help_text=_('Inventory source variables in YAML or JSON format.'),
    )
    credential = models.ForeignKey(
        'Credential',
        related_name='%(class)ss',
        null=True,
        default=None,
        blank=True,
        on_delete=models.SET_NULL,
    )
    source_regions = models.CharField(
        max_length=1024,
        blank=True,
        default='',
    )
    instance_filters = models.CharField(
        max_length=1024,
        blank=True,
        default='',
        help_text=_('Comma-separated list of filter expressions (EC2 only). Hosts are imported when ANY of the filters match.'),
    )
    group_by = models.CharField(
        max_length=1024,
        blank=True,
        default='',
        help_text=_('Limit groups automatically created from inventory source (EC2 only).'),
    )
    overwrite = models.BooleanField(
        default=False,
        help_text=_('Overwrite local groups and hosts from remote inventory source.'),
    )
    overwrite_vars = models.BooleanField(
        default=False,
        help_text=_('Overwrite local variables from remote inventory source.'),
    )
    timeout = models.IntegerField(
        blank=True,
        default=0,
        help_text=_("The amount of time (in seconds) to run before the task is canceled."),
    )
    verbosity = models.PositiveIntegerField(
        choices=INVENTORY_UPDATE_VERBOSITY_CHOICES,
        blank=True,
        default=1,
    )

    @classmethod
    def get_ec2_region_choices(cls):
        ec2_region_names = getattr(settings, 'EC2_REGION_NAMES', {})
        ec2_name_replacements = {
            'us': 'US',
            'ap': 'Asia Pacific',
            'eu': 'Europe',
            'sa': 'South America',
        }
        import boto.ec2
        regions = [('all', 'All')]
        for region in boto.ec2.regions():
            label = ec2_region_names.get(region.name, '')
            if not label:
                label_parts = []
                for part in region.name.split('-'):
                    part = ec2_name_replacements.get(part.lower(), part.title())
                    label_parts.append(part)
                label = ' '.join(label_parts)
            regions.append((region.name, label))
        return regions

    @classmethod
    def get_ec2_group_by_choices(cls):
        return [
            ('ami_id', _('Image ID')),
            ('availability_zone', _('Availability Zone')),
            ('aws_account', _('Account')),
            ('instance_id', _('Instance ID')),
            ('instance_state', _('Instance State')),
            ('instance_type', _('Instance Type')),
            ('key_pair', _('Key Name')),
            ('region', _('Region')),
            ('security_group', _('Security Group')),
            ('tag_keys', _('Tags')),
            ('tag_none', _('Tag None')),
            ('vpc_id', _('VPC ID')),
        ]

    @classmethod
    def get_gce_region_choices(self):
        """Return a complete list of regions in GCE, as a list of
        two-tuples.
        """
        # It's not possible to get a list of regions from GCE without
        # authenticating first.  Therefore, use a list from settings.
        regions = list(getattr(settings, 'GCE_REGION_CHOICES', []))
        regions.insert(0, ('all', 'All'))
        return regions

    @classmethod
    def get_azure_rm_region_choices(self):
        """Return a complete list of regions in Microsoft Azure, as a list of
        two-tuples.
        """
        # It's not possible to get a list of regions from Azure without
        # authenticating first (someone reading these might think there's
        # a pattern here!).  Therefore, you guessed it, use a list from
        # settings.
        regions = list(getattr(settings, 'AZURE_RM_REGION_CHOICES', []))
        regions.insert(0, ('all', 'All'))
        return regions

    @classmethod
    def get_vmware_region_choices(self):
        """Return a complete list of regions in VMware, as a list of two-tuples
        (but note that VMware doesn't actually have regions!).
        """
        return [('all', 'All')]

    @classmethod
    def get_openstack_region_choices(self):
        """I don't think openstack has regions"""
        return [('all', 'All')]

    @classmethod
    def get_satellite6_region_choices(self):
        """Red Hat Satellite 6 region choices (not implemented)"""
        return [('all', 'All')]

    @classmethod
    def get_cloudforms_region_choices(self):
        """Red Hat CloudForms region choices (not implemented)"""
        return [('all', 'All')]

    def clean_credential(self):
        if not self.source:
            return None
        cred = self.credential
        if cred and self.source not in ('custom', 'scm'):
            # If a credential was provided, it's important that it matches
            # the actual inventory source being used (Amazon requires Amazon
            # credentials; Rackspace requires Rackspace credentials; etc...)
            if self.source.replace('ec2', 'aws') != cred.kind:
                raise ValidationError(
                    _('Cloud-based inventory sources (such as %s) require '
                      'credentials for the matching cloud service.') % self.source
                )
        # Allow an EC2 source to omit the credential.  If Tower is running on
        # an EC2 instance with an IAM Role assigned, boto will use credentials
        # from the instance metadata instead of those explicitly provided.
        elif self.source in CLOUD_PROVIDERS and self.source != 'ec2':
            raise ValidationError(_('Credential is required for a cloud source.'))
        elif self.source == 'custom' and cred and cred.credential_type.kind in ('scm', 'ssh', 'insights', 'vault'):
            raise ValidationError(_(
                'Credentials of type machine, source control, insights and vault are '
                'disallowed for custom inventory sources.'
            ))
        return cred

    def clean_source_regions(self):
        regions = self.source_regions

        if self.source in CLOUD_PROVIDERS:
            get_regions = getattr(self, 'get_%s_region_choices' % self.source)
            valid_regions = [x[0] for x in get_regions()]
            region_transform = lambda x: x.strip().lower()
        else:
            return ''
        all_region = region_transform('all')
        valid_regions = [region_transform(x) for x in valid_regions]
        regions = [region_transform(x) for x in regions.split(',') if x.strip()]
        if all_region in regions:
            return all_region
        invalid_regions = []
        for r in regions:
            if r not in valid_regions and r not in invalid_regions:
                invalid_regions.append(r)
        if invalid_regions:
            raise ValidationError(_('Invalid %(source)s region: %(region)s') % {
                'source': self.source, 'region': ', '.join(invalid_regions)})
        return ','.join(regions)

    source_vars_dict = VarsDictProperty('source_vars')

    def clean_instance_filters(self):
        instance_filters = unicode(self.instance_filters or '')
        if self.source == 'ec2':
            invalid_filters = []
            instance_filter_re = re.compile(r'^((tag:.+)|([a-z][a-z\.-]*[a-z]))=.*$')
            for instance_filter in instance_filters.split(','):
                instance_filter = instance_filter.strip()
                if not instance_filter:
                    continue
                if not instance_filter_re.match(instance_filter):
                    invalid_filters.append(instance_filter)
                    continue
                instance_filter_name = instance_filter.split('=', 1)[0]
                if instance_filter_name.startswith('tag:'):
                    continue
                if instance_filter_name not in self.INSTANCE_FILTER_NAMES:
                    invalid_filters.append(instance_filter)
            if invalid_filters:
                raise ValidationError(_('Invalid filter expression: %(filter)s') %
                                      {'filter': ', '.join(invalid_filters)})
            return instance_filters
        elif self.source == 'vmware':
            return instance_filters
        else:
            return ''

    def clean_group_by(self):
        group_by = unicode(self.group_by or '')
        if self.source == 'ec2':
            get_choices = getattr(self, 'get_%s_group_by_choices' % self.source)
            valid_choices = [x[0] for x in get_choices()]
            choice_transform = lambda x: x.strip().lower()
            valid_choices = [choice_transform(x) for x in valid_choices]
            choices = [choice_transform(x) for x in group_by.split(',') if x.strip()]
            invalid_choices = []
            for c in choices:
                if c not in valid_choices and c not in invalid_choices:
                    invalid_choices.append(c)
            if invalid_choices:
                raise ValidationError(_('Invalid group by choice: %(choice)s') %
                                      {'choice': ', '.join(invalid_choices)})
            return ','.join(choices)
        elif self.source == 'vmware':
            return group_by
        else:
            return ''


class InventorySource(UnifiedJobTemplate, InventorySourceOptions):

    SOFT_UNIQUE_TOGETHER = [('polymorphic_ctype', 'name', 'inventory')]

    class Meta:
        app_label = 'main'

    inventory = models.ForeignKey(
        'Inventory',
        related_name='inventory_sources',
        null=True,
        default=None,
        on_delete=models.CASCADE,
    )

    deprecated_group = models.OneToOneField(
        'Group',
        related_name='deprecated_inventory_source',
        null=True,
        default=None,
        on_delete=models.CASCADE,
    )

    source_project = models.ForeignKey(
        'Project',
        related_name='scm_inventory_sources',
        help_text=_('Project containing inventory file used as source.'),
        on_delete=models.CASCADE,
        blank=True,
        default=None,
        null=True
    )
    scm_last_revision = models.CharField(
        max_length=1024,
        blank=True,
        default='',
        editable=False,
    )
    update_on_project_update = models.BooleanField(
        default=False,
    )
    update_on_launch = models.BooleanField(
        default=False,
    )
    update_cache_timeout = models.PositiveIntegerField(
        default=0,
    )

    @classmethod
    def _get_unified_job_class(cls):
        return InventoryUpdate

    @classmethod
    def _get_unified_job_field_names(cls):
        return ['name', 'description', 'source', 'source_path', 'source_script', 'source_vars', 'schedule',
                'credential', 'source_regions', 'instance_filters', 'group_by', 'overwrite', 'overwrite_vars',
                'timeout', 'verbosity', 'launch_type', 'source_project_update',]

    def save(self, *args, **kwargs):
        # If update_fields has been specified, add our field names to it,
        # if it hasn't been specified, then we're just doing a normal save.
        update_fields = kwargs.get('update_fields', [])
        is_new_instance = not bool(self.pk)

        # Set name automatically. Include PK (or placeholder) to make sure the names are always unique.
        replace_text = '__replace_%s__' % now()
        old_name_re = re.compile(r'^inventory_source \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}.*?$')
        if not self.name or old_name_re.match(self.name) or '__replace_' in self.name:
            group_name = getattr(self, 'v1_group_name', '')
            if self.inventory and self.pk:
                self.name = '%s (%s - %s)' % (group_name, self.inventory.name, self.pk)
            elif self.inventory:
                self.name = '%s (%s - %s)' % (group_name, self.inventory.name, replace_text)
            elif not is_new_instance:
                self.name = 'inventory source (%s)' % self.pk
            else:
                self.name = 'inventory source (%s)' % replace_text
            if 'name' not in update_fields:
                update_fields.append('name')
        # Reset revision if SCM source has changed parameters
        if self.source=='scm' and not is_new_instance:
            before_is = self.__class__.objects.get(pk=self.pk)
            if before_is.source_path != self.source_path or before_is.source_project_id != self.source_project_id:
                # Reset the scm_revision if file changed to force update
                self.scm_last_revision = ''
                if 'scm_last_revision' not in update_fields:
                    update_fields.append('scm_last_revision')

        # Do the actual save.
        super(InventorySource, self).save(*args, **kwargs)

        # Add the PK to the name.
        if replace_text in self.name:
            self.name = self.name.replace(replace_text, str(self.pk))
            super(InventorySource, self).save(update_fields=['name'])
        if self.source=='scm' and is_new_instance and self.update_on_project_update:
            # Schedule a new Project update if one is not already queued
            if self.source_project and not self.source_project.project_updates.filter(
                    status__in=['new', 'pending', 'waiting']).exists():
                self.update()
        if not getattr(_inventory_updates, 'is_updating', False):
            if self.inventory is not None:
                self.inventory.update_computed_fields(update_groups=False, update_hosts=False)

    def _get_current_status(self):
        if self.source:
            if self.current_job and self.current_job.status:
                return self.current_job.status
            elif not self.last_job:
                return 'never updated'
            # inherit the child job status
            else:
                return self.last_job.status
        else:
            return 'none'

    def get_absolute_url(self, request=None):
        return reverse('api:inventory_source_detail', kwargs={'pk': self.pk}, request=request)

    def _can_update(self):
        if self.source == 'custom':
            return bool(self.source_script)
        elif self.source == 'scm':
            return bool(self.source_project)
        else:
            return bool(self.source in CLOUD_INVENTORY_SOURCES)

    def create_inventory_update(self, **kwargs):
        return self.create_unified_job(**kwargs)

    @property
    def cache_timeout_blocked(self):
        if not self.last_job_run:
            return False
        if (self.last_job_run + datetime.timedelta(seconds=self.update_cache_timeout)) > now():
            return True
        return False

    @property
    def needs_update_on_launch(self):
        if self.source and self.update_on_launch:
            if not self.last_job_run:
                return True
            if (self.last_job_run + datetime.timedelta(seconds=self.update_cache_timeout)) <= now():
                return True
        return False

    @property
    def notification_templates(self):
        base_notification_templates = NotificationTemplate.objects
        error_notification_templates = list(base_notification_templates
                                            .filter(unifiedjobtemplate_notification_templates_for_errors__in=[self]))
        success_notification_templates = list(base_notification_templates
                                              .filter(unifiedjobtemplate_notification_templates_for_success__in=[self]))
        any_notification_templates = list(base_notification_templates
                                          .filter(unifiedjobtemplate_notification_templates_for_any__in=[self]))
        if self.inventory.organization is not None:
            error_notification_templates = set(error_notification_templates + list(base_notification_templates
                                               .filter(organization_notification_templates_for_errors=self.inventory.organization)))
            success_notification_templates = set(success_notification_templates + list(base_notification_templates
                                                 .filter(organization_notification_templates_for_success=self.inventory.organization)))
            any_notification_templates = set(any_notification_templates + list(base_notification_templates
                                             .filter(organization_notification_templates_for_any=self.inventory.organization)))
        return dict(error=list(error_notification_templates),
                    success=list(success_notification_templates),
                    any=list(any_notification_templates))

    def clean_source(self):  # TODO: remove in 3.3
        source = self.source
        if source and self.deprecated_group:
            qs = self.deprecated_group.inventory_sources.filter(source__in=CLOUD_INVENTORY_SOURCES)
            existing_sources = qs.exclude(pk=self.pk)
            if existing_sources.count():
                s = u', '.join([x.deprecated_group.name for x in existing_sources])
                raise ValidationError(_('Unable to configure this item for cloud sync. It is already managed by %s.') % s)
        return source

    def clean_update_on_project_update(self):
        if self.update_on_project_update is True and \
                self.source == 'scm' and \
                InventorySource.objects.filter(
                    Q(inventory=self.inventory,
                        update_on_project_update=True, source='scm') &
                    ~Q(id=self.id)).exists():
            raise ValidationError(_("More than one SCM-based inventory source with update on project update per-inventory not allowed."))
        return self.update_on_project_update

    def clean_update_on_launch(self):
        if self.update_on_project_update is True and \
                self.source == 'scm' and \
                self.update_on_launch is True:
            raise ValidationError(_("Cannot update SCM-based inventory source on launch if set to update on project update. "
                                    "Instead, configure the corresponding source project to update on launch."))
        return self.update_on_launch

    def clean_overwrite_vars(self):
        if self.source == 'scm' and not self.overwrite_vars:
            raise ValidationError(_("SCM type sources must set `overwrite_vars` to `true`."))
        return self.overwrite_vars

    def clean_source_path(self):
        if self.source != 'scm' and self.source_path:
            raise ValidationError(_("Cannot set source_path if not SCM type."))
        return self.source_path


class InventoryUpdate(UnifiedJob, InventorySourceOptions, JobNotificationMixin, TaskManagerInventoryUpdateMixin):
    '''
    Internal job for tracking inventory updates from external sources.
    '''

    class Meta:
        app_label = 'main'

    inventory_source = models.ForeignKey(
        'InventorySource',
        related_name='inventory_updates',
        editable=False,
        on_delete=models.CASCADE,
    )
    license_error = models.BooleanField(
        default=False,
        editable=False,
    )
    source_project_update = models.ForeignKey(
        'ProjectUpdate',
        related_name='scm_inventory_updates',
        help_text=_('Inventory files from this Project Update were used for the inventory update.'),
        on_delete=models.CASCADE,
        blank=True,
        default=None,
        null=True
    )

    @classmethod
    def _get_parent_field_name(cls):
        return 'inventory_source'

    @classmethod
    def _get_task_class(cls):
        from awx.main.tasks import RunInventoryUpdate
        return RunInventoryUpdate

    def _global_timeout_setting(self):
        return 'DEFAULT_INVENTORY_UPDATE_TIMEOUT'

    def websocket_emit_data(self):
        websocket_data = super(InventoryUpdate, self).websocket_emit_data()
        websocket_data.update(dict(inventory_source_id=self.inventory_source.pk))

        if self.inventory_source.inventory is not None:
            websocket_data.update(dict(inventory_id=self.inventory_source.inventory.pk))

        if self.inventory_source.deprecated_group is not None:  # TODO: remove in 3.3
            websocket_data.update(dict(group_id=self.inventory_source.deprecated_group.id))
        return websocket_data

    def save(self, *args, **kwargs):
        update_fields = kwargs.get('update_fields', [])
        inventory_source = self.inventory_source
        if inventory_source.inventory and self.name == inventory_source.name:
            self.name = inventory_source.inventory.name
            if 'name' not in update_fields:
                update_fields.append('name')
        super(InventoryUpdate, self).save(*args, **kwargs)

    def get_absolute_url(self, request=None):
        return reverse('api:inventory_update_detail', kwargs={'pk': self.pk}, request=request)

    def get_ui_url(self):
        return urljoin(settings.TOWER_URL_BASE, "/#/inventory_sync/{}".format(self.pk))

    def get_actual_source_path(self):
        '''Alias to source_path that combines with project path for for SCM file based sources'''
        if self.inventory_source_id is None or self.inventory_source.source_project_id is None:
            return self.source_path
        return os.path.join(
            self.inventory_source.source_project.get_project_path(check_if_exists=False),
            self.source_path)

    @property
    def task_impact(self):
        return 50

    # InventoryUpdate credential required
    # Custom and SCM InventoryUpdate credential not required
    @property
    def can_start(self):
        if not super(InventoryUpdate, self).can_start:
            return False

        if (self.source not in ('custom', 'ec2', 'scm') and
                not (self.credential)):
            return False
        elif self.source == 'scm' and not self.inventory_source.source_project:
            return False
        elif self.source == 'file':
            return False
        return True

    '''
    JobNotificationMixin
    '''
    def get_notification_templates(self):
        return self.inventory_source.notification_templates

    def get_notification_friendly_name(self):
        return "Inventory Update"

    @property
    def preferred_instance_groups(self):
        if self.inventory_source.inventory is not None and self.inventory_source.inventory.organization is not None:
            organization_groups = [x for x in self.inventory_source.inventory.organization.instance_groups.all()]
        else:
            organization_groups = []
        if self.inventory_source.inventory is not None:
            inventory_groups = [x for x in self.inventory_source.inventory.instance_groups.all()]
        selected_groups = inventory_groups + organization_groups
        if not selected_groups:
            return self.global_instance_groups
        return selected_groups

    def cancel(self, job_explanation=None, is_chain=False):
        res = super(InventoryUpdate, self).cancel(job_explanation=job_explanation, is_chain=is_chain)
        if res:
            if self.launch_type != 'scm' and self.source_project_update:
                self.source_project_update.cancel(job_explanation=job_explanation)
        return res


class CustomInventoryScript(CommonModelNameNotUnique, ResourceMixin):

    class Meta:
        app_label = 'main'
        unique_together = [('name', 'organization')]
        ordering = ('name',)

    script = prevent_search(models.TextField(
        blank=True,
        default='',
        help_text=_('Inventory script contents'),
    ))
    organization = models.ForeignKey(
        'Organization',
        related_name='custom_inventory_scripts',
        help_text=_('Organization owning this inventory script'),
        blank=False,
        null=True,
        on_delete=models.SET_NULL,
    )

    admin_role = ImplicitRoleField(
        parent_role='organization.admin_role',
    )
    read_role = ImplicitRoleField(
        parent_role=['organization.auditor_role', 'organization.member_role', 'admin_role'],
    )

    def get_absolute_url(self, request=None):
        return reverse('api:inventory_script_detail', kwargs={'pk': self.pk}, request=request)
