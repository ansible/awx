# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import datetime
import time
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
from awx.main.utils import _inventory_updates
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
    enabled_var = models.TextField(
        blank=True,
        default='',
        help_text=_('Retrieve the enabled state from the given dict of host '
                    'variables. The enabled variable may be specified as "foo.bar", '
                    'in which case the lookup will traverse into nested dicts, '
                    'equivalent to: from_dict.get("foo", {}).get("bar", default)'),
    )
    enabled_value = models.TextField(
        blank=True,
        default='',
        help_text=_('Only used when enabled_var is set. Value when the host is '
                    'considered enabled. For example if enabled_var="status.power_state"'
                    'and enabled_value="powered_on" with host variables:'
                    '{'
                    '   "status": {'
                    '     "power_state": "powered_on",'
                    '     "created": "2020-08-04T18:13:04+00:00",'
                    '     "healthy": true'
                    '    },'
                    '    "name": "foobar",'
                    '    "ip_address": "192.168.2.1"'
                    '}'
                    'The host would be marked enabled. If power_state where any '
                    'value other than powered_on then the host would be disabled '
                    'when imported into Tower. If the key is not found then the '
                    'host will be enabled'),
    )
    host_filter = models.TextField(
        blank=True,
        default='',
        help_text=_('Regex where only matching hosts will be imported into Tower.'),
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


    source_vars_dict = VarsDictProperty('source_vars')


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

    @classmethod
    def get_proper_name(cls):
        if cls.plugin_name is None:
            return None
        return f'{cls.namespace}.{cls.collection}.{cls.plugin_name}'

    @property
    def filename(self):
        """Inventory filename for using the inventory plugin
        This is created dynamically, but the auto plugin requires this exact naming
        """
        return '{0}.yml'.format(self.plugin_name)

    def inventory_contents(self, inventory_update, private_data_dir):
        """Returns a string that is the content for the inventory file for the inventory plugin
        """
        return yaml.safe_dump(
            self.inventory_as_dict(inventory_update, private_data_dir),
            default_flow_style=False,
            width=1000
        )

    def inventory_as_dict(self, inventory_update, private_data_dir):
        source_vars = dict(inventory_update.source_vars_dict) # make a copy
        proper_name = self.get_proper_name()
        '''
        None conveys that we should use the user-provided plugin.
        Note that a plugin value of '' should still be overridden.
        '''
        if proper_name is not None:
            source_vars['plugin'] = proper_name
        return source_vars

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

    def inventory_as_dict(self, inventory_update, private_data_dir):
        ret = super().inventory_as_dict(inventory_update, private_data_dir)
        credential = inventory_update.get_cloud_credential()
        # InventorySource.source_vars take precedence over ENV vars
        if 'projects' not in ret:
            ret['projects'] = [credential.get_input('project', default='')]
        return ret


class vmware(PluginFileInjector):
    plugin_name = 'vmware_vm_inventory'
    base_injector = 'managed'
    namespace = 'community'
    collection = 'vmware'


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


class tower(PluginFileInjector):
    plugin_name = 'tower'
    base_injector = 'template'
    namespace = 'awx'
    collection = 'awx'


for cls in PluginFileInjector.__subclasses__():
    InventorySourceOptions.injectors[cls.__name__] = cls
