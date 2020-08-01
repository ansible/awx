# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import datetime
import time
import json
import logging
import re
import copy
import os.path
from urllib.parse import urljoin
import yaml

# Django
from django.conf import settings
from django.db import models, connection
from django.utils.translation import ugettext_lazy as _
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from django.utils.encoding import iri_to_uri
from django.db.models import Q

# REST Framework
from rest_framework.exceptions import ParseError

# AWX
from awx.api.versioning import reverse
from awx.main.constants import CLOUD_PROVIDERS
from awx.main.consumers import emit_channel_notification
from awx.main.fields import (
    ImplicitRoleField,
    JSONBField,
    SmartFilterField,
    OrderedManyToManyField,
)
from awx.main.managers import HostManager
from awx.main.models.base import (
    BaseModel,
    CommonModelNameNotUnique,
    VarsDictProperty,
    CLOUD_INVENTORY_SOURCES,
    prevent_search, accepts_json
)
from awx.main.models.events import InventoryUpdateEvent
from awx.main.models.unified_jobs import UnifiedJob, UnifiedJobTemplate
from awx.main.models.mixins import (
    ResourceMixin,
    TaskManagerInventoryUpdateMixin,
    RelatedJobsMixin,
    CustomVirtualEnvMixin,
)
from awx.main.models.notifications import (
    NotificationTemplate,
    JobNotificationMixin,
)
from awx.main.models.credential.injectors import _openstack_data
from awx.main.utils import _inventory_updates, region_sorting
from awx.main.utils.safe_yaml import sanitize_jinja


__all__ = ['Inventory', 'Host', 'Group', 'InventorySource', 'InventoryUpdate',
           'CustomInventoryScript', 'SmartInventoryMembership']

logger = logging.getLogger('awx.main.models.inventory')


class Inventory(CommonModelNameNotUnique, ResourceMixin, RelatedJobsMixin):
    '''
    an inventory source contains lists and hosts.
    '''

    FIELDS_TO_PRESERVE_AT_COPY = ['hosts', 'groups', 'instance_groups']
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
    variables = accepts_json(models.TextField(
        blank=True,
        default='',
        help_text=_('Inventory variables in JSON or YAML format.'),
    ))
    has_active_failures = models.BooleanField(
        default=False,
        editable=False,
        help_text=_('This field is deprecated and will be removed in a future release. '
                    'Flag indicating whether any hosts in this inventory have failed.'),
    )
    total_hosts = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text=_('This field is deprecated and will be removed in a future release. '
                    'Total number of hosts in this inventory.'),
    )
    hosts_with_active_failures = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text=_('This field is deprecated and will be removed in a future release. '
                    'Number of hosts in this inventory with active failures.'),
    )
    total_groups = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text=_('This field is deprecated and will be removed in a future release. '
                    'Total number of groups in this inventory.'),
    )
    has_inventory_sources = models.BooleanField(
        default=False,
        editable=False,
        help_text=_('This field is deprecated and will be removed in a future release. '
                    'Flag indicating whether this inventory has any external inventory sources.'),
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
    instance_groups = OrderedManyToManyField(
        'InstanceGroup',
        blank=True,
        through='InventoryInstanceGroupMembership',
    )
    admin_role = ImplicitRoleField(
        parent_role='organization.inventory_admin_role',
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

    @staticmethod
    def parse_slice_params(slice_str):
        m = re.match(r"slice(?P<number>\d+)of(?P<step>\d+)", slice_str)
        if not m:
            raise ParseError(_('Could not parse subset as slice specification.'))
        number = int(m.group('number'))
        step = int(m.group('step'))
        if number > step:
            raise ParseError(_('Slice number must be less than total number of slices.'))
        elif number < 1:
            raise ParseError(_('Slice number must be 1 or higher.'))
        return (number, step)

    def get_script_data(self, hostvars=False, towervars=False, show_all=False, slice_number=1, slice_count=1):
        hosts_kw = dict()
        if not show_all:
            hosts_kw['enabled'] = True
        fetch_fields = ['name', 'id', 'variables', 'inventory_id']
        if towervars:
            fetch_fields.append('enabled')
        hosts = self.hosts.filter(**hosts_kw).order_by('name').only(*fetch_fields)
        if slice_count > 1 and slice_number > 0:
            offset = slice_number - 1
            hosts = hosts[offset::slice_count]

        data = dict()
        all_group = data.setdefault('all', dict())
        all_hostnames = set(host.name for host in hosts)

        if self.variables_dict:
            all_group['vars'] = self.variables_dict

        if self.kind == 'smart':
            all_group['hosts'] = [host.name for host in hosts]
        else:
            # Keep track of hosts that are members of a group
            grouped_hosts = set([])

            # Build in-memory mapping of groups and their hosts.
            group_hosts_qs = Group.hosts.through.objects.filter(
                group__inventory_id=self.id,
                host__inventory_id=self.id
            ).values_list('group_id', 'host_id', 'host__name')
            group_hosts_map = {}
            for group_id, host_id, host_name in group_hosts_qs:
                if host_name not in all_hostnames:
                    continue  # host might not be in current shard
                group_hostnames = group_hosts_map.setdefault(group_id, [])
                group_hostnames.append(host_name)
                grouped_hosts.add(host_name)

            # Build in-memory mapping of groups and their children.
            group_parents_qs = Group.parents.through.objects.filter(
                from_group__inventory_id=self.id,
                to_group__inventory_id=self.id,
            ).values_list('from_group_id', 'from_group__name', 'to_group_id')
            group_children_map = {}
            for from_group_id, from_group_name, to_group_id in group_parents_qs:
                group_children = group_children_map.setdefault(to_group_id, [])
                group_children.append(from_group_name)

            # Add ungrouped hosts to all group
            all_group['hosts'] = [host.name for host in hosts if host.name not in grouped_hosts]

            # Now use in-memory maps to build up group info.
            all_group_names = []
            for group in self.groups.only('name', 'id', 'variables', 'inventory_id'):
                group_info = dict()
                if group.id in group_hosts_map:
                    group_info['hosts'] = group_hosts_map[group.id]
                if group.id in group_children_map:
                    group_info['children'] = group_children_map[group.id]
                group_vars = group.variables_dict
                if group_vars:
                    group_info['vars'] = group_vars
                if group_info:
                    data[group.name] = group_info
                all_group_names.append(group.name)

            # add all groups as children of all group, includes empty groups
            if all_group_names:
                all_group['children'] = all_group_names

        if hostvars:
            data.setdefault('_meta', dict())
            data['_meta'].setdefault('hostvars', dict())
            for host in hosts:
                data['_meta']['hostvars'][host.name] = host.variables_dict
                if towervars:
                    tower_dict = dict(remote_tower_enabled=str(host.enabled).lower(),
                                      remote_tower_id=host.id)
                    data['_meta']['hostvars'][host.name].update(tower_dict)

        return data

    def update_computed_fields(self):
        '''
        Update model fields that are computed from database relationships.
        '''
        logger.debug("Going to update inventory computed fields, pk={0}".format(self.pk))
        start_time = time.time()
        active_hosts = self.hosts
        failed_hosts = active_hosts.filter(last_job_host_summary__failed=True)
        active_groups = self.groups
        if self.kind == 'smart':
            active_groups = active_groups.none()
        if self.kind == 'smart':
            active_inventory_sources = self.inventory_sources.none()
        else:
            active_inventory_sources = self.inventory_sources.filter(source__in=CLOUD_INVENTORY_SOURCES)
        failed_inventory_sources = active_inventory_sources.filter(last_job_failed=True)
        computed_fields = {
            'has_active_failures': bool(failed_hosts.count()),
            'total_hosts': active_hosts.count(),
            'hosts_with_active_failures': failed_hosts.count(),
            'total_groups': active_groups.count(),
            'has_inventory_sources': bool(active_inventory_sources.count()),
            'total_inventory_sources': active_inventory_sources.count(),
            'inventory_sources_with_failures': failed_inventory_sources.count(),
        }
        # CentOS python seems to have issues clobbering the inventory on poor timing during certain operations
        iobj = Inventory.objects.get(id=self.id)
        for field, value in list(computed_fields.items()):
            if getattr(iobj, field) != value:
                setattr(iobj, field, value)
                # update in-memory object
                setattr(self, field, value)
            else:
                computed_fields.pop(field)
        if computed_fields:
            iobj.save(update_fields=computed_fields.keys())
        logger.debug("Finished updating inventory computed fields, pk={0}, in "
                     "{1:.3f} seconds".format(self.pk, time.time() - start_time))

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
        if (self.kind == 'smart' and 'host_filter' in kwargs.get('update_fields', ['host_filter']) and
                connection.vendor != 'sqlite'):
            # Minimal update of host_count for smart inventory host filter changes
            self.update_computed_fields()

    def delete(self, *args, **kwargs):
        self._update_host_smart_inventory_memeberships()
        super(Inventory, self).delete(*args, **kwargs)

    '''
    RelatedJobsMixin
    '''
    def _get_related_jobs(self):
        return UnifiedJob.objects.non_polymorphic().filter(
            Q(job__inventory=self) |
            Q(inventoryupdate__inventory=self) |
            Q(adhoccommand__inventory=self)
        )


class SmartInventoryMembership(BaseModel):
    '''
    A lookup table for Host membership in Smart Inventory
    '''

    class Meta:
        app_label = 'main'
        unique_together = (('host', 'inventory'),)

    inventory = models.ForeignKey('Inventory', related_name='+', on_delete=models.CASCADE)
    host = models.ForeignKey('Host', related_name='+', on_delete=models.CASCADE)


class Host(CommonModelNameNotUnique, RelatedJobsMixin):
    '''
    A managed node
    '''

    FIELDS_TO_PRESERVE_AT_COPY = [
        'name', 'description', 'groups', 'inventory', 'enabled', 'instance_id', 'variables'
    ]

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
    variables = accepts_json(models.TextField(
        blank=True,
        default='',
        help_text=_('Host variables in JSON or YAML format.'),
    ))
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
    inventory_sources = models.ManyToManyField(
        'InventorySource',
        related_name='hosts',
        editable=False,
        help_text=_('Inventory source(s) that created or modified this host.'),
    )
    ansible_facts = JSONBField(
        blank=True,
        default=dict,
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

    def get_absolute_url(self, request=None):
        return reverse('api:host_detail', kwargs={'pk': self.pk}, request=request)

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

    def clean_name(self):
        try:
            sanitize_jinja(self.name)
        except ValueError as e:
            raise ValidationError(str(e) + ": {}".format(self.name))
        return self.name

    def save(self, *args, **kwargs):
        self._update_host_smart_inventory_memeberships()
        super(Host, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self._update_host_smart_inventory_memeberships()
        super(Host, self).delete(*args, **kwargs)

    '''
    RelatedJobsMixin
    '''
    def _get_related_jobs(self):
        return self.inventory._get_related_jobs()


class Group(CommonModelNameNotUnique, RelatedJobsMixin):
    '''
    A group containing managed hosts.  A group or host may belong to multiple
    groups.
    '''

    FIELDS_TO_PRESERVE_AT_COPY = [
        'name', 'description', 'inventory', 'children', 'parents', 'hosts', 'variables'
    ]

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
    variables = accepts_json(models.TextField(
        blank=True,
        default='',
        help_text=_('Group variables in JSON or YAML format.'),
    ))
    hosts = models.ManyToManyField(
        'Host',
        related_name='groups',
        blank=True,
        help_text=_('Hosts associated directly with this group.'),
    )
    inventory_sources = models.ManyToManyField(
        'InventorySource',
        related_name='groups',
        editable=False,
        help_text=_('Inventory source(s) that created or modified this group.'),
    )

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

    '''
    RelatedJobsMixin
    '''
    def _get_related_jobs(self):
        return UnifiedJob.objects.non_polymorphic().filter(
            Q(job__inventory=self.inventory) |
            Q(inventoryupdate__inventory_source__groups=self)
        )


class InventorySourceOptions(BaseModel):
    '''
    Common fields for InventorySource and InventoryUpdate.
    '''

    injectors = dict()

    SOURCE_CHOICES = [
        ('file', _('File, Directory or Script')),
        ('scm', _('Sourced from a Project')),
        ('ec2', _('Amazon EC2')),
        ('gce', _('Google Compute Engine')),
        ('azure_rm', _('Microsoft Azure Resource Manager')),
        ('vmware', _('VMware vCenter')),
        ('satellite6', _('Red Hat Satellite 6')),
        ('openstack', _('OpenStack')),
        ('rhv', _('Red Hat Virtualization')),
        ('tower', _('Ansible Tower')),
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
        blank=False,
        default=None,
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
        return sorted(regions, key=region_sorting)

    @classmethod
    def get_ec2_group_by_choices(cls):
        return [
            ('ami_id', _('Image ID')),
            ('availability_zone', _('Availability Zone')),
            ('aws_account', _('Account')),
            ('instance_id', _('Instance ID')),
            ('instance_state', _('Instance State')),
            ('platform', _('Platform')),
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
        return sorted(regions, key=region_sorting)

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
        return sorted(regions, key=region_sorting)

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
    def get_rhv_region_choices(self):
        """No region supprt"""
        return [('all', 'All')]

    @classmethod
    def get_tower_region_choices(self):
        """No region supprt"""
        return [('all', 'All')]

    @staticmethod
    def cloud_credential_validation(source, cred):
        if not source:
            return None
        if cred and source not in ('custom', 'scm'):
            # If a credential was provided, it's important that it matches
            # the actual inventory source being used (Amazon requires Amazon
            # credentials; Rackspace requires Rackspace credentials; etc...)
            if source.replace('ec2', 'aws') != cred.kind:
                return _('Cloud-based inventory sources (such as %s) require '
                         'credentials for the matching cloud service.') % source
        # Allow an EC2 source to omit the credential.  If Tower is running on
        # an EC2 instance with an IAM Role assigned, boto will use credentials
        # from the instance metadata instead of those explicitly provided.
        elif source in CLOUD_PROVIDERS and source != 'ec2':
            return _('Credential is required for a cloud source.')
        elif source == 'custom' and cred and cred.credential_type.kind in ('scm', 'ssh', 'insights', 'vault'):
            return _(
                'Credentials of type machine, source control, insights and vault are '
                'disallowed for custom inventory sources.'
            )
        elif source == 'scm' and cred and cred.credential_type.kind in ('insights', 'vault'):
            return _(
                'Credentials of type insights and vault are '
                'disallowed for scm inventory sources.'
            )
        return None

    def get_cloud_credential(self):
        """Return the credential which is directly tied to the inventory source type.
        """
        credential = None
        for cred in self.credentials.all():
            if self.source in CLOUD_PROVIDERS:
                if cred.kind == self.source.replace('ec2', 'aws'):
                    credential = cred
                    break
            else:
                # these need to be returned in the API credential field
                if cred.credential_type.kind != 'vault':
                    credential = cred
                    break
        return credential

    def get_extra_credentials(self):
        """Return all credentials that are not used by the inventory source injector.
        These are all credentials that should run their own inject_credential logic.
        """
        special_cred = None
        if self.source in CLOUD_PROVIDERS:
            # these have special injection logic associated with them
            special_cred = self.get_cloud_credential()
        extra_creds = []
        for cred in self.credentials.all():
            if special_cred is None or cred.pk != special_cred.pk:
                extra_creds.append(cred)
        return extra_creds

    @property
    def credential(self):
        cred = self.get_cloud_credential()
        if cred is not None:
            return cred.pk

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
        instance_filters = str(self.instance_filters or '')
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
        elif self.source in ('vmware', 'tower'):
            return instance_filters
        else:
            return ''

    def clean_group_by(self):
        group_by = str(self.group_by or '')
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


class InventorySource(UnifiedJobTemplate, InventorySourceOptions, CustomVirtualEnvMixin, RelatedJobsMixin):

    SOFT_UNIQUE_TOGETHER = [('polymorphic_ctype', 'name', 'inventory')]

    class Meta:
        app_label = 'main'
        ordering = ('inventory', 'name')

    inventory = models.ForeignKey(
        'Inventory',
        related_name='inventory_sources',
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
        return set(f.name for f in InventorySourceOptions._meta.fields) | set(
            ['name', 'description', 'organization', 'credentials', 'inventory']
        )

    def save(self, *args, **kwargs):
        # if this is a new object, inherit organization from its inventory
        if not self.pk and self.inventory and self.inventory.organization_id and not self.organization_id:
            self.organization_id = self.inventory.organization_id

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
                self.inventory.update_computed_fields()

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
        elif self.source == 'file':
            return False
        elif self.source == 'ec2':
            # Permit credential-less ec2 updates to allow IAM roles
            return True
        elif self.source == 'gce':
            # These updates will hang if correct credential is not supplied
            credential = self.get_cloud_credential()
            return bool(credential and credential.kind == 'gce')
        return True

    def create_inventory_update(self, **kwargs):
        return self.create_unified_job(**kwargs)

    def create_unified_job(self, **kwargs):
        # Use special name, if name not already specified
        if self.inventory:
            if '_eager_fields' not in kwargs:
                kwargs['_eager_fields'] = {}
            if 'name' not in kwargs['_eager_fields']:
                name = '{} - {}'.format(self.inventory.name, self.name)
                name_field = self._meta.get_field('name')
                if len(name) > name_field.max_length:
                    name = name[:name_field.max_length]
                kwargs['_eager_fields']['name'] = name
        return super(InventorySource, self).create_unified_job(**kwargs)

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
        started_notification_templates = list(base_notification_templates
                                              .filter(unifiedjobtemplate_notification_templates_for_started__in=[self]))
        success_notification_templates = list(base_notification_templates
                                              .filter(unifiedjobtemplate_notification_templates_for_success__in=[self]))
        if self.inventory.organization is not None:
            error_notification_templates = set(error_notification_templates + list(base_notification_templates
                                               .filter(organization_notification_templates_for_errors=self.inventory.organization)))
            started_notification_templates = set(started_notification_templates + list(base_notification_templates
                                                 .filter(organization_notification_templates_for_started=self.inventory.organization)))
            success_notification_templates = set(success_notification_templates + list(base_notification_templates
                                                 .filter(organization_notification_templates_for_success=self.inventory.organization)))
        return dict(error=list(error_notification_templates),
                    started=list(started_notification_templates),
                    success=list(success_notification_templates))

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

    def clean_source_path(self):
        if self.source != 'scm' and self.source_path:
            raise ValidationError(_("Cannot set source_path if not SCM type."))
        return self.source_path

    '''
    RelatedJobsMixin
    '''
    def _get_related_jobs(self):
        return InventoryUpdate.objects.filter(inventory_source=self)


class InventoryUpdate(UnifiedJob, InventorySourceOptions, JobNotificationMixin, TaskManagerInventoryUpdateMixin, CustomVirtualEnvMixin):
    '''
    Internal job for tracking inventory updates from external sources.
    '''

    class Meta:
        app_label = 'main'
        ordering = ('inventory', 'name')

    inventory = models.ForeignKey(
        'Inventory',
        related_name='inventory_updates',
        null=True,
        default=None,
        on_delete=models.DO_NOTHING,
    )
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
    org_host_limit_error = models.BooleanField(
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

    def _get_parent_field_name(self):
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

        return websocket_data

    def get_absolute_url(self, request=None):
        return reverse('api:inventory_update_detail', kwargs={'pk': self.pk}, request=request)

    def get_ui_url(self):
        return urljoin(settings.TOWER_URL_BASE, "/#/jobs/inventory/{}".format(self.pk))

    def get_actual_source_path(self):
        '''Alias to source_path that combines with project path for for SCM file based sources'''
        if self.inventory_source_id is None or self.inventory_source.source_project_id is None:
            return self.source_path
        return os.path.join(
            self.inventory_source.source_project.get_project_path(check_if_exists=False),
            self.source_path)

    @property
    def event_class(self):
        return InventoryUpdateEvent

    @property
    def task_impact(self):
        return 1

    # InventoryUpdate credential required
    # Custom and SCM InventoryUpdate credential not required
    @property
    def can_start(self):
        if not super(InventoryUpdate, self).can_start:
            return False
        elif not self.inventory_source or not self.inventory_source._can_update():
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
        else:
            inventory_groups = []
        selected_groups = inventory_groups + organization_groups
        if not selected_groups:
            return self.global_instance_groups
        return selected_groups

    @property
    def ansible_virtualenv_path(self):
        if self.inventory_source and self.inventory_source.custom_virtualenv:
            return self.inventory_source.custom_virtualenv
        if self.inventory_source and self.inventory_source.source_project:
            project = self.inventory_source.source_project
            if project and project.custom_virtualenv:
                return project.custom_virtualenv
        return settings.ANSIBLE_VENV_PATH

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


class PluginFileInjector(object):
    plugin_name = None  # Ansible core name used to reference plugin
    # base injector should be one of None, "managed", or "template"
    # this dictates which logic to borrow from playbook injectors
    base_injector = None
    # every source should have collection, these are for the collection name
    namespace = None
    collection = None
    collection_migration = '2.9'  # Starting with this version, we use collections

    def __init__(self, ansible_version):
        # This is InventoryOptions instance, could be source or inventory update
        self.ansible_version = ansible_version

    @property
    def filename(self):
        """Inventory filename for using the inventory plugin
        This is created dynamically, but the auto plugin requires this exact naming
        """
        return '{0}.yml'.format(self.plugin_name)

    def inventory_as_dict(self, inventory_update, private_data_dir):
        """Default implementation of inventory plugin file contents.
        There are some valid cases when all parameters can be obtained from
        the environment variables, example "plugin: linode" is valid
        ideally, however, some options should be filled from the inventory source data
        """
        if self.plugin_name is None:
            raise NotImplementedError('At minimum the plugin name is needed for inventory plugin use.')
        proper_name = f'{self.namespace}.{self.collection}.{self.plugin_name}'
        return {'plugin': proper_name}

    def inventory_contents(self, inventory_update, private_data_dir):
        """Returns a string that is the content for the inventory file for the inventory plugin
        """
        return yaml.safe_dump(
            self.inventory_as_dict(inventory_update, private_data_dir),
            default_flow_style=False,
            width=1000
        )

    def build_env(self, inventory_update, env, private_data_dir, private_data_files):
        injector_env = self.get_plugin_env(inventory_update, private_data_dir, private_data_files)
        env.update(injector_env)
        # Preserves current behavior for Ansible change in default planned for 2.10
        env['ANSIBLE_TRANSFORM_INVALID_GROUP_CHARS'] = 'never'
        return env

    def _get_shared_env(self, inventory_update, private_data_dir, private_data_files):
        """By default, we will apply the standard managed_by_tower injectors
        """
        injected_env = {}
        credential = inventory_update.get_cloud_credential()
        # some sources may have no credential, specifically ec2
        if credential is None:
            return injected_env
        if self.base_injector in ('managed', 'template'):
            injected_env['INVENTORY_UPDATE_ID'] = str(inventory_update.pk)  # so injector knows this is inventory
        if self.base_injector == 'managed':
            from awx.main.models.credential import injectors as builtin_injectors
            cred_kind = inventory_update.source.replace('ec2', 'aws')
            if cred_kind in dir(builtin_injectors):
                getattr(builtin_injectors, cred_kind)(credential, injected_env, private_data_dir)
        elif self.base_injector == 'template':
            safe_env = injected_env.copy()
            args = []
            credential.credential_type.inject_credential(
                credential, injected_env, safe_env, args, private_data_dir
            )
            # NOTE: safe_env is handled externally to injector class by build_safe_env static method
            # that means that managed_by_tower injectors must only inject detectable env keys
            # enforcement of this is accomplished by tests
        return injected_env

    def get_plugin_env(self, inventory_update, private_data_dir, private_data_files):
        env = self._get_shared_env(inventory_update, private_data_dir, private_data_files)
        env['ANSIBLE_COLLECTIONS_PATHS'] = settings.AWX_ANSIBLE_COLLECTIONS_PATHS
        return env

    def build_private_data(self, inventory_update, private_data_dir):
        return self.build_plugin_private_data(inventory_update, private_data_dir)

    def build_plugin_private_data(self, inventory_update, private_data_dir):
        return None


class azure_rm(PluginFileInjector):
    plugin_name = 'azure_rm'
    base_injector = 'managed'
    namespace = 'azure'
    collection = 'azcollection'

    def get_plugin_env(self, *args, **kwargs):
        ret = super(azure_rm, self).get_plugin_env(*args, **kwargs)
        # We need native jinja2 types so that tags can give JSON null value
        ret['ANSIBLE_JINJA2_NATIVE'] = str(True)
        return ret

    def inventory_as_dict(self, inventory_update, private_data_dir):
        ret = super(azure_rm, self).inventory_as_dict(inventory_update, private_data_dir)

        source_vars = inventory_update.source_vars_dict

        ret['fail_on_template_errors'] = False

        group_by_hostvar = {
            'location': {'prefix': '', 'separator': '', 'key': 'location'},
            'tag': {'prefix': '', 'separator': '', 'key': 'tags.keys() | list if tags else []'},
            # Introduced with https://github.com/ansible/ansible/pull/53046
            'security_group': {'prefix': '', 'separator': '', 'key': 'security_group'},
            'resource_group': {'prefix': '', 'separator': '', 'key': 'resource_group'},
            # Note, os_family was not documented correctly in script, but defaulted to grouping by it
            'os_family': {'prefix': '', 'separator': '', 'key': 'os_disk.operating_system_type'}
        }
        # by default group by everything
        # always respect user setting, if they gave it
        group_by = [
            grouping_name for grouping_name in group_by_hostvar
            if source_vars.get('group_by_{}'.format(grouping_name), True)
        ]
        ret['keyed_groups'] = [group_by_hostvar[grouping_name] for grouping_name in group_by]
        if 'tag' in group_by:
            # Nasty syntax to reproduce "key_value" group names in addition to "key"
            ret['keyed_groups'].append({
                'prefix': '', 'separator': '',
                'key': r'dict(tags.keys() | map("regex_replace", "^(.*)$", "\1_") | list | zip(tags.values() | list)) if tags else []'
            })

        # Compatibility content
        # TODO: add proper support for instance_filters non-specific to compatibility
        # TODO: add proper support for group_by non-specific to compatibility
        # Dashes were not configurable in azure_rm.py script, we do not want unicode, so always use this
        ret['use_contrib_script_compatible_sanitization'] = True
        # use same host names as script
        ret['plain_host_names'] = True
        # By default the script did not filter hosts
        ret['default_host_filters'] = []
        # User-given host filters
        user_filters = []
        old_filterables = [
            ('resource_groups', 'resource_group'),
            ('tags', 'tags')
            # locations / location would be an entry
            # but this would conflict with source_regions
        ]
        for key, loc in old_filterables:
            value = source_vars.get(key, None)
            if value and isinstance(value, str):
                # tags can be list of key:value pairs
                #  e.g. 'Creator:jmarshall, peanutbutter:jelly'
                # or tags can be a list of keys
                #  e.g. 'Creator, peanutbutter'
                if key == "tags":
                    # grab each key value pair
                    for kvpair in value.split(','):
                        # split into key and value
                        kv = kvpair.split(':')
                        # filter out any host that does not have key
                        # in their tags.keys() variable
                        user_filters.append('"{}" not in tags.keys()'.format(kv[0].strip()))
                        # if a value is provided, check that the key:value pair matches
                        if len(kv) > 1:
                            user_filters.append('tags["{}"] != "{}"'.format(kv[0].strip(), kv[1].strip()))
                else:
                    user_filters.append('{} not in {}'.format(
                        loc, value.split(',')
                    ))
        if user_filters:
            ret.setdefault('exclude_host_filters', [])
            ret['exclude_host_filters'].extend(user_filters)

        ret['conditional_groups'] = {'azure': True}
        ret['hostvar_expressions'] = {
            'provisioning_state': 'provisioning_state | title',
            'computer_name': 'name',
            'type': 'resource_type',
            'private_ip': 'private_ipv4_addresses[0] if private_ipv4_addresses else None',
            'public_ip': 'public_ipv4_addresses[0] if public_ipv4_addresses else None',
            'public_ip_name': 'public_ip_name if public_ip_name is defined else None',
            'public_ip_id': 'public_ip_id if public_ip_id is defined else None',
            'tags': 'tags if tags else None'
        }
        # Special functionality from script
        if source_vars.get('use_private_ip', False):
            ret['hostvar_expressions']['ansible_host'] = 'private_ipv4_addresses[0]'
        # end compatibility content

        if inventory_update.source_regions and 'all' not in inventory_update.source_regions:
            # initialize a list for this section in inventory file
            ret.setdefault('exclude_host_filters', [])
            # make a python list of the regions we will use
            python_regions = [x.strip() for x in inventory_update.source_regions.split(',')]
            # convert that list in memory to python syntax in a string
            # now put that in jinja2 syntax operating on hostvar key "location"
            # and put that as an entry in the exclusions list
            ret['exclude_host_filters'].append("location not in {}".format(repr(python_regions)))
        return ret


class ec2(PluginFileInjector):
    plugin_name = 'aws_ec2'
    base_injector = 'managed'
    namespace = 'amazon'
    collection = 'aws'

    def get_plugin_env(self, *args, **kwargs):
        ret = super(ec2, self).get_plugin_env(*args, **kwargs)
        # We need native jinja2 types so that ec2_state_code will give integer
        ret['ANSIBLE_JINJA2_NATIVE'] = str(True)
        return ret

    def _compat_compose_vars(self):
        return {
            # vars that change
            'ec2_block_devices': (
                "dict(block_device_mappings | map(attribute='device_name') | list | zip(block_device_mappings "
                "| map(attribute='ebs.volume_id') | list))"
            ),
            'ec2_dns_name': 'public_dns_name',
            'ec2_group_name': 'placement.group_name',
            'ec2_instance_profile': 'iam_instance_profile | default("")',
            'ec2_ip_address': 'public_ip_address',
            'ec2_kernel': 'kernel_id | default("")',
            'ec2_monitored':  "monitoring.state in ['enabled', 'pending']",
            'ec2_monitoring_state': 'monitoring.state',
            'ec2_placement': 'placement.availability_zone',
            'ec2_ramdisk': 'ramdisk_id | default("")',
            'ec2_reason': 'state_transition_reason',
            'ec2_security_group_ids': "security_groups | map(attribute='group_id') | list |  join(',')",
            'ec2_security_group_names': "security_groups | map(attribute='group_name') | list |  join(',')",
            'ec2_tag_Name': 'tags.Name',
            'ec2_state': 'state.name',
            'ec2_state_code': 'state.code',
            'ec2_state_reason': 'state_reason.message if state_reason is defined else ""',
            'ec2_sourceDestCheck': 'source_dest_check | default(false) | lower | string',  # snake_case syntax intended
            'ec2_account_id': 'owner_id',
            # vars that just need ec2_ prefix
            'ec2_ami_launch_index': 'ami_launch_index | string',
            'ec2_architecture': 'architecture',
            'ec2_client_token': 'client_token',
            'ec2_ebs_optimized': 'ebs_optimized',
            'ec2_hypervisor': 'hypervisor',
            'ec2_image_id': 'image_id',
            'ec2_instance_type': 'instance_type',
            'ec2_key_name': 'key_name',
            'ec2_launch_time': r'launch_time | regex_replace(" ", "T") | regex_replace("(\+)(\d\d):(\d)(\d)$", ".\g<2>\g<3>Z")',
            'ec2_platform': 'platform | default("")',
            'ec2_private_dns_name': 'private_dns_name',
            'ec2_private_ip_address': 'private_ip_address',
            'ec2_public_dns_name': 'public_dns_name',
            'ec2_region': 'placement.region',
            'ec2_root_device_name': 'root_device_name',
            'ec2_root_device_type': 'root_device_type',
            # many items need blank defaults because the script tended to keep a common schema
            'ec2_spot_instance_request_id': 'spot_instance_request_id | default("")',
            'ec2_subnet_id': 'subnet_id | default("")',
            'ec2_virtualization_type': 'virtualization_type',
            'ec2_vpc_id': 'vpc_id | default("")',
            # same as ec2_ip_address, the script provided this
            'ansible_host': 'public_ip_address',
            # new with https://github.com/ansible/ansible/pull/53645
            'ec2_eventsSet': 'events | default("")',
            'ec2_persistent': 'persistent | default(false)',
            'ec2_requester_id': 'requester_id | default("")'
        }

    def inventory_as_dict(self, inventory_update, private_data_dir):
        ret = super(ec2, self).inventory_as_dict(inventory_update, private_data_dir)

        keyed_groups = []
        group_by_hostvar = {
            'ami_id': {'prefix': '', 'separator': '', 'key': 'image_id', 'parent_group': 'images'},
            # 2 entries for zones for same groups to establish 2 parentage trees
            'availability_zone': {'prefix': '', 'separator': '', 'key': 'placement.availability_zone', 'parent_group': 'zones'},
            'aws_account': {'prefix': '', 'separator': '', 'key': 'ec2_account_id', 'parent_group': 'accounts'},  # composed var
            'instance_id': {'prefix': '', 'separator': '', 'key': 'instance_id', 'parent_group': 'instances'},  # normally turned off
            'instance_state': {'prefix': 'instance_state', 'key': 'ec2_state', 'parent_group': 'instance_states'},  # composed var
            # ec2_platform is a composed var, but group names do not match up to hostvar exactly
            'platform': {'prefix': 'platform', 'key': 'platform | default("undefined")', 'parent_group': 'platforms'},
            'instance_type': {'prefix': 'type', 'key': 'instance_type', 'parent_group': 'types'},
            'key_pair': {'prefix': 'key', 'key': 'key_name', 'parent_group': 'keys'},
            'region': {'prefix': '', 'separator': '', 'key': 'placement.region', 'parent_group': 'regions'},
            # Security requires some ninja jinja2 syntax, credit to s-hertel
            'security_group': {'prefix': 'security_group', 'key': 'security_groups | map(attribute="group_name")', 'parent_group': 'security_groups'},
            # tags cannot be parented in exactly the same way as the script due to
            # https://github.com/ansible/ansible/pull/53812
            'tag_keys': [
                {'prefix': 'tag', 'key': 'tags', 'parent_group': 'tags'},
                {'prefix': 'tag', 'key': 'tags.keys()', 'parent_group': 'tags'}
            ],
            # 'tag_none': None,  # grouping by no tags isn't a different thing with plugin
            # naming is redundant, like vpc_id_vpc_8c412cea, but intended
            'vpc_id': {'prefix': 'vpc_id', 'key': 'vpc_id', 'parent_group': 'vpcs'},
        }
        # -- same-ish as script here --
        group_by = [x.strip().lower() for x in inventory_update.group_by.split(',') if x.strip()]
        for choice in inventory_update.get_ec2_group_by_choices():
            value = bool((group_by and choice[0] in group_by) or (not group_by and choice[0] != 'instance_id'))
            # -- end sameness to script --
            if value:
                this_keyed_group = group_by_hostvar.get(choice[0], None)
                # If a keyed group syntax does not exist, there is nothing we can do to get this group
                if this_keyed_group is not None:
                    if isinstance(this_keyed_group, list):
                        keyed_groups.extend(this_keyed_group)
                    else:
                        keyed_groups.append(this_keyed_group)
        # special case, this parentage is only added if both zones and regions are present
        if not group_by or ('region' in group_by and 'availability_zone' in group_by):
            keyed_groups.append({'prefix': '', 'separator': '', 'key': 'placement.availability_zone', 'parent_group': '{{ placement.region }}'})

        source_vars = inventory_update.source_vars_dict
        # This is a setting from the script, hopefully no one used it
        # if true, it replaces dashes, but not in region / loc names
        replace_dash = bool(source_vars.get('replace_dash_in_groups', True))
        # Compatibility content
        legacy_regex = {
            True: r"[^A-Za-z0-9\_]",
            False: r"[^A-Za-z0-9\_\-]"  # do not replace dash, dash is allowed
        }[replace_dash]
        list_replacer = 'map("regex_replace", "{rx}", "_") | list'.format(rx=legacy_regex)
        # this option, a plugin option, will allow dashes, but not unicode
        # when set to False, unicode will be allowed, but it was not allowed by script
        # thus, we always have to use this option, and always use our custom regex
        ret['use_contrib_script_compatible_sanitization'] = True
        for grouping_data in keyed_groups:
            if grouping_data['key'] in ('placement.region', 'placement.availability_zone'):
                # us-east-2 is always us-east-2 according to ec2.py
                # no sanitization in region-ish groups for the script standards, ever ever
                continue
            if grouping_data['key'] == 'tags':
                # dict jinja2 transformation
                grouping_data['key'] = 'dict(tags.keys() | {replacer} | zip(tags.values() | {replacer}))'.format(
                    replacer=list_replacer
                )
            elif grouping_data['key'] == 'tags.keys()' or grouping_data['prefix'] == 'security_group':
                # list jinja2 transformation
                grouping_data['key'] += ' | {replacer}'.format(replacer=list_replacer)
            else:
                # string transformation
                grouping_data['key'] += ' | regex_replace("{rx}", "_")'.format(rx=legacy_regex)
        # end compatibility content

        if source_vars.get('iam_role_arn', None):
            ret['iam_role_arn'] = source_vars['iam_role_arn']

        # This was an allowed ec2.ini option, also plugin option, so pass through
        if source_vars.get('boto_profile', None):
            ret['boto_profile'] = source_vars['boto_profile']

        elif not replace_dash:
            # Using the plugin, but still want dashes allowed
            ret['use_contrib_script_compatible_sanitization'] = True

        if source_vars.get('nested_groups') is False:
            for this_keyed_group in keyed_groups:
                this_keyed_group.pop('parent_group', None)

        if keyed_groups:
            ret['keyed_groups'] = keyed_groups

        # Instance ID not part of compat vars, because of settings.EC2_INSTANCE_ID_VAR
        compose_dict = {'ec2_id': 'instance_id'}
        inst_filters = {}

        # Compatibility content
        compose_dict.update(self._compat_compose_vars())
        # plugin provides "aws_ec2", but not this which the script gave
        ret['groups'] = {'ec2': True}
        if source_vars.get('hostname_variable') is not None:
            hnames = []
            for expr in source_vars.get('hostname_variable').split(','):
                if expr == 'public_dns_name':
                    hnames.append('dns-name')
                elif not expr.startswith('tag:') and '_' in expr:
                    hnames.append(expr.replace('_', '-'))
                else:
                    hnames.append(expr)
            ret['hostnames'] = hnames
        else:
            # public_ip as hostname is non-default plugin behavior, script behavior
            ret['hostnames'] = [
                'network-interface.addresses.association.public-ip',
                'dns-name',
                'private-dns-name'
            ]
        # The script returned only running state by default, the plugin does not
        # https://docs.aws.amazon.com/cli/latest/reference/ec2/describe-instances.html#options
        # options: pending | running | shutting-down | terminated | stopping | stopped
        inst_filters['instance-state-name'] = ['running']
        # end compatibility content

        if source_vars.get('destination_variable') or source_vars.get('vpc_destination_variable'):
            for fd in ('destination_variable', 'vpc_destination_variable'):
                if source_vars.get(fd):
                    compose_dict['ansible_host'] = source_vars.get(fd)
                    break

        if compose_dict:
            ret['compose'] = compose_dict

        if inventory_update.instance_filters:
            # logic used to live in ec2.py, now it belongs to us. Yay more code?
            filter_sets = [f for f in inventory_update.instance_filters.split(',') if f]

            for instance_filter in filter_sets:
                # AND logic not supported, unclear how to...
                instance_filter = instance_filter.strip()
                if not instance_filter or '=' not in instance_filter:
                    continue
                filter_key, filter_value = [x.strip() for x in instance_filter.split('=', 1)]
                if not filter_key:
                    continue
                inst_filters[filter_key] = filter_value

        if inst_filters:
            ret['filters'] = inst_filters

        if inventory_update.source_regions and 'all' not in inventory_update.source_regions:
            ret['regions'] = inventory_update.source_regions.split(',')

        return ret


class gce(PluginFileInjector):
    plugin_name = 'gcp_compute'
    base_injector = 'managed'
    namespace = 'google'
    collection = 'cloud'

    def get_plugin_env(self, *args, **kwargs):
        ret = super(gce, self).get_plugin_env(*args, **kwargs)
        # We need native jinja2 types so that ip addresses can give JSON null value
        ret['ANSIBLE_JINJA2_NATIVE'] = str(True)
        return ret

    def _compat_compose_vars(self):
        # missing: gce_image, gce_uuid
        # https://github.com/ansible/ansible/issues/51884
        return {
            'gce_description': 'description if description else None',
            'gce_machine_type': 'machineType',
            'gce_name': 'name',
            'gce_network': 'networkInterfaces[0].network.name',
            'gce_private_ip': 'networkInterfaces[0].networkIP',
            'gce_public_ip': 'networkInterfaces[0].accessConfigs[0].natIP | default(None)',
            'gce_status': 'status',
            'gce_subnetwork': 'networkInterfaces[0].subnetwork.name',
            'gce_tags': 'tags.get("items", [])',
            'gce_zone': 'zone',
            'gce_metadata': 'metadata.get("items", []) | items2dict(key_name="key", value_name="value")',
            # NOTE: image hostvar is enabled via retrieve_image_info option
            'gce_image': 'image',
            # We need this as long as hostnames is non-default, otherwise hosts
            # will not be addressed correctly, was returned in script
            'ansible_ssh_host': 'networkInterfaces[0].accessConfigs[0].natIP | default(networkInterfaces[0].networkIP)'
        }

    def inventory_as_dict(self, inventory_update, private_data_dir):
        ret = super(gce, self).inventory_as_dict(inventory_update, private_data_dir)
        credential = inventory_update.get_cloud_credential()

        # auth related items
        ret['projects'] = [credential.get_input('project', default='')]
        ret['auth_kind'] = "serviceaccount"

        filters = []
        # TODO: implement gce group_by options
        # gce never processed the group_by field, if it had, we would selectively
        # apply those options here, but it did not, so all groups are added here
        keyed_groups = [
            # the jinja2 syntax is duplicated with compose
            # https://github.com/ansible/ansible/issues/51883
            {'prefix': 'network', 'key': 'gce_subnetwork'},  # composed var
            {'prefix': '', 'separator': '', 'key': 'gce_private_ip'},  # composed var
            {'prefix': '', 'separator': '', 'key': 'gce_public_ip'},  # composed var
            {'prefix': '', 'separator': '', 'key': 'machineType'},
            {'prefix': '', 'separator': '', 'key': 'zone'},
            {'prefix': 'tag', 'key': 'gce_tags'},  # composed var
            {'prefix': 'status', 'key': 'status | lower'},
            # NOTE: image hostvar is enabled via retrieve_image_info option
            {'prefix': '', 'separator': '', 'key': 'image'},
        ]
        # This will be used as the gce instance_id, must be universal, non-compat
        compose_dict = {'gce_id': 'id'}

        # Compatibility content
        # TODO: proper group_by and instance_filters support, irrelevant of compat mode
        # The gce.py script never sanitized any names in any way
        ret['use_contrib_script_compatible_sanitization'] = True
        # Perform extra API query to get the image hostvar
        ret['retrieve_image_info'] = True
        # Add in old hostvars aliases
        compose_dict.update(self._compat_compose_vars())
        # Non-default names to match script
        ret['hostnames'] = ['name', 'public_ip', 'private_ip']
        # end compatibility content

        if keyed_groups:
            ret['keyed_groups'] = keyed_groups
        if filters:
            ret['filters'] = filters
        if compose_dict:
            ret['compose'] = compose_dict
        if inventory_update.source_regions and 'all' not in inventory_update.source_regions:
            ret['zones'] = inventory_update.source_regions.split(',')
        return ret


class vmware(PluginFileInjector):
    plugin_name = 'vmware_vm_inventory'
    base_injector = 'managed'
    namespace = 'community'
    collection = 'vmware'

    def inventory_as_dict(self, inventory_update, private_data_dir):
        ret = super(vmware, self).inventory_as_dict(inventory_update, private_data_dir)
        ret['strict'] = False
        # Documentation of props, see
        # https://github.com/ansible/ansible/blob/devel/docs/docsite/rst/scenario_guides/vmware_scenarios/vmware_inventory_vm_attributes.rst
        UPPERCASE_PROPS = [
            "availableField",
            "configIssue",
            "configStatus",
            "customValue",  # optional
            "datastore",
            "effectiveRole",
            "guestHeartbeatStatus",  # optional
            "layout",  # optional
            "layoutEx",  # optional
            "name",
            "network",
            "overallStatus",
            "parentVApp",  # optional
            "permission",
            "recentTask",
            "resourcePool",
            "rootSnapshot",
            "snapshot",  # optional
            "triggeredAlarmState",
            "value"
        ]
        NESTED_PROPS = [
            "capability",
            "config",
            "guest",
            "runtime",
            "storage",
            "summary",  # repeat of other properties
        ]
        ret['properties'] = UPPERCASE_PROPS + NESTED_PROPS
        ret['compose'] = {'ansible_host': 'guest.ipAddress'}  # default value
        ret['compose']['ansible_ssh_host'] = ret['compose']['ansible_host']
        # the ansible_uuid was unique every host, every import, from the script
        ret['compose']['ansible_uuid'] = '99999999 | random | to_uuid'
        for prop in UPPERCASE_PROPS:
            if prop == prop.lower():
                continue
            ret['compose'][prop.lower()] = prop
        ret['with_nested_properties'] = True
        # ret['property_name_format'] = 'lower_case'  # only dacrystal/topic/vmware-inventory-plugin-property-format

        # process custom options
        vmware_opts = dict(inventory_update.source_vars_dict.items())
        if inventory_update.instance_filters:
            vmware_opts.setdefault('host_filters', inventory_update.instance_filters)
        if inventory_update.group_by:
            vmware_opts.setdefault('groupby_patterns', inventory_update.group_by)

        alias_pattern = vmware_opts.get('alias_pattern')
        if alias_pattern:
            ret.setdefault('hostnames', [])
            for alias in alias_pattern.split(','):  # make best effort
                striped_alias = alias.replace('{', '').replace('}', '').strip()  # make best effort
                if not striped_alias:
                    continue
                ret['hostnames'].append(striped_alias)

        host_pattern = vmware_opts.get('host_pattern')  # not working in script
        if host_pattern:
            stripped_hp = host_pattern.replace('{', '').replace('}', '').strip()  # make best effort
            ret['compose']['ansible_host'] = stripped_hp
            ret['compose']['ansible_ssh_host'] = stripped_hp

        host_filters = vmware_opts.get('host_filters')
        if host_filters:
            ret.setdefault('filters', [])
            for hf in host_filters.split(','):
                striped_hf = hf.replace('{', '').replace('}', '').strip()  # make best effort
                if not striped_hf:
                    continue
                ret['filters'].append(striped_hf)
        else:
            # default behavior filters by power state
            ret['filters'] = ['runtime.powerState == "poweredOn"']

        groupby_patterns = vmware_opts.get('groupby_patterns')
        ret.setdefault('keyed_groups', [])
        if groupby_patterns:
            for pattern in groupby_patterns.split(','):
                stripped_pattern = pattern.replace('{', '').replace('}', '').strip()  # make best effort
                ret['keyed_groups'].append({
                    'prefix': '', 'separator': '',
                    'key': stripped_pattern
                })
        else:
            # default groups from script
            for entry in ('config.guestId', '"templates" if config.template else "guests"'):
                ret['keyed_groups'].append({
                    'prefix': '', 'separator': '',
                    'key': entry
                })

        return ret


class openstack(PluginFileInjector):
    plugin_name = 'openstack'
    namespace = 'openstack'
    collection = 'cloud'

    def _get_clouds_dict(self, inventory_update, cred, private_data_dir):
        openstack_data = _openstack_data(cred)

        openstack_data['clouds']['devstack']['private'] = inventory_update.source_vars_dict.get('private', True)
        ansible_variables = {
            'use_hostnames': True,
            'expand_hostvars': False,
            'fail_on_errors': True,
        }
        provided_count = 0
        for var_name in ansible_variables:
            if var_name in inventory_update.source_vars_dict:
                ansible_variables[var_name] = inventory_update.source_vars_dict[var_name]
                provided_count += 1
        if provided_count:
            # Must we provide all 3 because the user provides any 1 of these??
            # this probably results in some incorrect mangling of the defaults
            openstack_data['ansible'] = ansible_variables
        return openstack_data

    def build_plugin_private_data(self, inventory_update, private_data_dir):
        credential = inventory_update.get_cloud_credential()
        private_data = {'credentials': {}}

        openstack_data = self._get_clouds_dict(inventory_update, credential, private_data_dir)
        private_data['credentials'][credential] = yaml.safe_dump(
            openstack_data, default_flow_style=False, allow_unicode=True
        )
        return private_data

    def inventory_as_dict(self, inventory_update, private_data_dir):
        def use_host_name_for_name(a_bool_maybe):
            if not isinstance(a_bool_maybe, bool):
                # Could be specified by user via "host" or "uuid"
                return a_bool_maybe
            elif a_bool_maybe:
                return 'name'  # plugin default
            else:
                return 'uuid'

        ret = super(openstack, self).inventory_as_dict(inventory_update, private_data_dir)
        ret['fail_on_errors'] = True
        ret['expand_hostvars'] = True
        ret['inventory_hostname'] = use_host_name_for_name(False)
        # Note: mucking with defaults will break import integrity
        # For the plugin, we need to use the same defaults as the old script
        # or else imports will conflict. To find script defaults you have
        # to read source code of the script.
        #
        # Script Defaults                           Plugin Defaults
        # 'use_hostnames': False,                   'name' (True)
        # 'expand_hostvars': True,                  'no' (False)
        # 'fail_on_errors': True,                   'no' (False)
        #
        # These are, yet again, different from ansible_variables in script logic
        # but those are applied inconsistently
        source_vars = inventory_update.source_vars_dict
        for var_name in ['expand_hostvars', 'fail_on_errors']:
            if var_name in source_vars:
                ret[var_name] = source_vars[var_name]
        if 'use_hostnames' in source_vars:
            ret['inventory_hostname'] = use_host_name_for_name(source_vars['use_hostnames'])
        return ret

    def get_plugin_env(self, inventory_update, private_data_dir, private_data_files):
        env = super(openstack, self).get_plugin_env(inventory_update, private_data_dir, private_data_files)
        credential = inventory_update.get_cloud_credential()
        cred_data = private_data_files['credentials']
        env['OS_CLIENT_CONFIG_FILE'] = cred_data[credential]
        return env


class rhv(PluginFileInjector):
    """ovirt uses the custom credential templating, and that is all
    """
    plugin_name = 'ovirt'
    base_injector = 'template'
    initial_version = '2.9'
    namespace = 'ovirt'
    collection = 'ovirt'

    def inventory_as_dict(self, inventory_update, private_data_dir):
        ret = super(rhv, self).inventory_as_dict(inventory_update, private_data_dir)
        ret['ovirt_insecure'] = False  # Default changed from script
        # TODO: process strict option upstream
        ret['compose'] = {
            'ansible_host': '(devices.values() | list)[0][0] if devices else None'
        }
        ret['keyed_groups'] = []
        for key in ('cluster', 'status'):
            ret['keyed_groups'].append({'prefix': key, 'separator': '_', 'key': key})
        ret['keyed_groups'].append({'prefix': 'tag', 'separator': '_', 'key': 'tags'})
        ret['ovirt_hostname_preference'] = ['name', 'fqdn']
        source_vars = inventory_update.source_vars_dict
        for key, value in source_vars.items():
            if key == 'plugin':
                continue
            ret[key] = value
        return ret


class satellite6(PluginFileInjector):
    plugin_name = 'foreman'
    namespace = 'theforeman'
    collection = 'foreman'

    def get_plugin_env(self, inventory_update, private_data_dir, private_data_files):
        # this assumes that this is merged
        # https://github.com/ansible/ansible/pull/52693
        credential = inventory_update.get_cloud_credential()
        ret = super(satellite6, self).get_plugin_env(inventory_update, private_data_dir, private_data_files)
        if credential:
            ret['FOREMAN_SERVER'] = credential.get_input('host', default='')
            ret['FOREMAN_USER'] = credential.get_input('username', default='')
            ret['FOREMAN_PASSWORD'] = credential.get_input('password', default='')
        return ret

    def inventory_as_dict(self, inventory_update, private_data_dir):
        ret = super(satellite6, self).inventory_as_dict(inventory_update, private_data_dir)
        ret['validate_certs'] = False

        group_patterns = '[]'
        group_prefix = 'foreman_'
        want_hostcollections = False
        want_ansible_ssh_host = False
        want_facts = True

        foreman_opts = inventory_update.source_vars_dict.copy()
        for k, v in foreman_opts.items():
            if k == 'satellite6_group_patterns' and isinstance(v, str):
                group_patterns = v
            elif k == 'satellite6_group_prefix' and isinstance(v, str):
                group_prefix = v
            elif k == 'satellite6_want_hostcollections' and isinstance(v, bool):
                want_hostcollections = v
            elif k == 'satellite6_want_ansible_ssh_host' and isinstance(v, bool):
                want_ansible_ssh_host = v
            elif k == 'satellite6_want_facts' and isinstance(v, bool):
                want_facts = v
            # add backwards support for ssl_verify
            # plugin uses new option, validate_certs, instead
            elif k == 'ssl_verify' and isinstance(v, bool):
                ret['validate_certs'] = v
            else:
                ret[k] = str(v)

        # Compatibility content
        group_by_hostvar = {
            "environment":           {"prefix": "{}environment_".format(group_prefix),
                                      "separator": "",
                                      "key": "foreman['environment_name'] | lower | regex_replace(' ', '') | "
                                             "regex_replace('[^A-Za-z0-9_]', '_') | regex_replace('none', '')"},
            "location":              {"prefix": "{}location_".format(group_prefix),
                                      "separator": "",
                                      "key": "foreman['location_name'] | lower | regex_replace(' ', '') | regex_replace('[^A-Za-z0-9_]', '_')"},
            "organization":          {"prefix": "{}organization_".format(group_prefix),
                                      "separator": "",
                                      "key": "foreman['organization_name'] | lower | regex_replace(' ', '') | regex_replace('[^A-Za-z0-9_]', '_')"},
            "lifecycle_environment": {"prefix": "{}lifecycle_environment_".format(group_prefix),
                                      "separator": "",
                                      "key": "foreman['content_facet_attributes']['lifecycle_environment_name'] | "
                                             "lower | regex_replace(' ', '') | regex_replace('[^A-Za-z0-9_]', '_')"},
            "content_view":          {"prefix": "{}content_view_".format(group_prefix),
                                      "separator": "",
                                      "key": "foreman['content_facet_attributes']['content_view_name'] | "
                                             "lower | regex_replace(' ', '') | regex_replace('[^A-Za-z0-9_]', '_')"}
        }

        ret['legacy_hostvars'] = True  # convert hostvar structure to the form used by the script
        ret['want_params'] = True
        ret['group_prefix'] = group_prefix
        ret['want_hostcollections'] = want_hostcollections
        ret['want_facts'] = want_facts

        if want_ansible_ssh_host:
            ret['compose'] = {'ansible_ssh_host': "foreman['ip6'] | default(foreman['ip'], true)"}
        ret['keyed_groups'] = [group_by_hostvar[grouping_name] for grouping_name in group_by_hostvar]

        def form_keyed_group(group_pattern):
            """
            Converts foreman group_pattern to
            inventory plugin keyed_group

            e.g. {app_param}-{tier_param}-{dc_param}
                 becomes
                 "%s-%s-%s" | format(app_param, tier_param, dc_param)
            """
            if type(group_pattern) is not str:
                return None
            params = re.findall('{[^}]*}', group_pattern)
            if len(params) == 0:
                return None

            param_names = []
            for p in params:
                param_names.append(p[1:-1].strip())  # strip braces and space

            # form keyed_group key by
            # replacing curly braces with '%s'
            # (for use with jinja's format filter)
            key = group_pattern
            for p in params:
                key = key.replace(p, '%s', 1)

            # apply jinja filter to key
            key = '"{}" | format({})'.format(key, ', '.join(param_names))

            keyed_group = {'key': key,
                           'separator': ''}
            return keyed_group

        try:
            group_patterns = json.loads(group_patterns)

            if type(group_patterns) is list:
                for group_pattern in group_patterns:
                    keyed_group = form_keyed_group(group_pattern)
                    if keyed_group:
                        ret['keyed_groups'].append(keyed_group)
        except json.JSONDecodeError:
            logger.warning('Could not parse group_patterns. Expected JSON-formatted string, found: {}'
                           .format(group_patterns))

        return ret


class tower(PluginFileInjector):
    plugin_name = 'tower'
    base_injector = 'template'
    namespace = 'awx'
    collection = 'awx'

    def inventory_as_dict(self, inventory_update, private_data_dir):
        ret = super(tower, self).inventory_as_dict(inventory_update, private_data_dir)
        # Credentials injected as env vars, same as script
        try:
            # plugin can take an actual int type
            identifier = int(inventory_update.instance_filters)
        except ValueError:
            # inventory_id could be a named URL
            identifier = iri_to_uri(inventory_update.instance_filters)
        ret['inventory_id'] = identifier
        ret['include_metadata'] = True  # used for license check
        return ret


for cls in PluginFileInjector.__subclasses__():
    InventorySourceOptions.injectors[cls.__name__] = cls
