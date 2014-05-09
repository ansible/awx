# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import datetime
import hashlib
import hmac
import json
import logging
import os
import re
import shlex
import uuid

# PyYAML
import yaml

# ZMQ
import zmq

# Django
from django.conf import settings
from django.db import models
from django.db.models import CASCADE, SET_NULL, PROTECT
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils.timezone import now, make_aware, get_default_timezone
from django.core.cache import cache

# AWX
from awx.main.fields import AutoOneToOneField
from awx.main.models.base import *
from awx.main.models.jobs import Job
from awx.main.models.unified_jobs import *
from awx.main.utils import encrypt_field, ignore_inventory_computed_fields

__all__ = ['Inventory', 'Host', 'Group', 'InventorySource', 'InventoryUpdate']

logger = logging.getLogger('awx.main.models.inventory')

class Inventory(CommonModel):
    '''
    an inventory source contains lists and hosts.
    '''

    class Meta:
        app_label = 'main'
        verbose_name_plural = _('inventories')
        unique_together = [('name', 'organization')]

    organization = models.ForeignKey(
        'Organization',
        related_name='inventories',
        help_text=_('Organization containing this inventory.'),
        on_delete=models.CASCADE,
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
        help_text=_('Total mumber of hosts in this inventory.'),
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

    def get_absolute_url(self):
        return reverse('api:inventory_detail', args=(self.pk,))

    def mark_inactive(self, save=True):
        '''
        When marking inventory inactive, also mark hosts and groups inactive.
        '''
        with ignore_inventory_computed_fields():
            for host in self.hosts.filter(active=True):
                host.mark_inactive()
            for group in self.groups.filter(active=True):
                group.mark_inactive(recompute=False)
            for inventory_source in self.inventory_sources.filter(active=True):
                inventory_source.mark_inactive()
        super(Inventory, self).mark_inactive(save=save)

    variables_dict = VarsDictProperty('variables')

    def update_computed_fields(self, update_groups=True, update_hosts=True):
        '''
        Update model fields that are computed from database relationships.
        '''
        logger.debug("Going to update inventory computed fields")
        if update_hosts:
            for host in self.hosts.filter(active=True):
                host.update_computed_fields(update_inventory=False,
                                            update_groups=False)
        if update_groups:
            for group in self.groups.filter(active=True):
                group.update_computed_fields()
        active_hosts = self.hosts.filter(active=True)
        failed_hosts = active_hosts.filter(has_active_failures=True)
        active_groups = self.groups.filter(active=True)
        failed_groups = active_groups.filter(has_active_failures=True)
        active_inventory_sources = self.inventory_sources.filter(active=True, source__in=CLOUD_INVENTORY_SOURCES)
        #failed_inventory_sources = active_inventory_sources.filter(last_update_failed=True)
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
        for field, value in computed_fields.items():
            if getattr(self, field) != value:
                setattr(self, field, value)
            else:
                computed_fields.pop(field)
        if computed_fields:
            self.save(update_fields=computed_fields.keys())
        logger.debug("Finished updating inventory computed fields")

    @property
    def root_groups(self):
        group_pks = self.groups.values_list('pk', flat=True)
        return self.groups.exclude(parents__pk__in=group_pks).distinct()


class Host(CommonModelNameNotUnique):
    '''
    A managed node
    '''

    class Meta:
        app_label = 'main'
        unique_together = (("name", "inventory"),) # FIXME: Add ('instance_id', 'inventory') after migration.

    inventory = models.ForeignKey(
        'Inventory',
        related_name='hosts',
        on_delete=models.CASCADE,
    )
    enabled = models.BooleanField(
        default=True,
        help_text=_('Is this host online and available for running jobs?'),
    )
    instance_id = models.CharField(
        max_length=100,
        blank=True,
        default='',
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

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('api:host_detail', args=(self.pk,))

    def mark_inactive(self, save=True):
        '''
        When marking hosts inactive, remove all associations to related
        inventory sources.
        '''
        super(Host, self).mark_inactive(save=save)
        self.inventory_sources.clear()
        self.clear_cached_values()

    def update_computed_fields(self, update_inventory=True, update_groups=True):
        '''
        Update model fields that are computed from database relationships.
        '''
        has_active_failures = bool(self.last_job_host_summary and
                                   self.last_job_host_summary.job.active and
                                   self.last_job_host_summary.failed)
        active_inventory_sources = self.inventory_sources.filter(active=True,
                                                                 source__in=CLOUD_INVENTORY_SOURCES)
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
        if update_groups:
            for group in self.all_groups.filter(active=True):
                group.update_computed_fields()
        if update_inventory:
            self.inventory.update_computed_fields(update_groups=False,
                                                  update_hosts=False)
        # Rebuild summary fields cache
        self.update_cached_values()
    variables_dict = VarsDictProperty('variables')

    @property
    def all_groups(self):
        '''
        Return all groups of which this host is a member, avoiding infinite
        recursion in the case of cyclical group relations.
        '''
        qs = self.groups.distinct()
        for group in self.groups.all():
            qs = qs | group.all_parents
        return qs

    def update_cached_values(self):
        cacheable_data = {"%s_all_groups" % self.id: [{'id': g.id, 'name': g.name} for g in self.all_groups.all()],
                          "%s_groups" % self.id: [{'id': g.id, 'name': g.name} for g in self.groups.all()],
                          "%s_recent_jobs" % self.id: [{'id': j.job.id, 'name': j.job.job_template.name, 'status': j.job.status, 'finished': j.job.finished} \
                                                       for j in self.job_host_summaries.all().order_by('-created')[:5]]}
        cache.set_many(cacheable_data)
        return cacheable_data

    def get_cached_summary_values(self):
        summary_data = cache.get_many(['%s_all_groups' % self.id, '%s_groups' % self.id, '%s_recent_jobs' % self.id])

        rebuild_cache = False
        for key in summary_data:
            if summary_data[key] is None:
                rebuild_cache = True
                break
        if rebuild_cache:
            summary_data = self.update_cached_values()
        summary_data_actual = dict(all_groups=summary_data['%s_all_groups' % self.id],
                                   groups=summary_data['%s_groups' % self.id],
                                   recent_jobs=summary_data['%s_recent_jobs' % self.id])
        return summary_data_actual

    def clear_cached_values(self):
        cache.delete_many(["%s_all_groups" % self.id, "%s_groups" % self.id, "%s_recent_jobs" % self.id])

    # Use .job_host_summaries.all() to get jobs affecting this host.
    # Use .job_events.all() to get events affecting this host.


class Group(CommonModelNameNotUnique):
    '''
    A group containing managed hosts.  A group or host may belong to multiple
    groups.
    '''

    class Meta:
        app_label = 'main'
        unique_together = (("name", "inventory"),)

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

    def get_absolute_url(self):
        return reverse('api:group_detail', args=(self.pk,))

    def mark_inactive_recursive(self, parent=None):
        def mark_actual(parent=parent):
            linked_children = [(parent, self)] + [(self, child) for child in self.children.all()]
            marked_groups = []
            marked_hosts = []
            for subgroup in linked_children:
                parent, group = subgroup
                if parent is not None:
                    group.parents.remove(parent)
                if group.parents.count() > 0:
                    continue
                for host in group.hosts.all():
                    host.groups.remove(group)
                    host_inv_sources = host.inventory_sources.all()
                    for inv_source in group.inventory_sources.all():
                        if inv_source in host_inv_sources:
                            host.inventory_sources.remove(inv_source)
                    if host.groups.count() < 1:
                        marked_hosts.append(host)
                for childgroup in group.children.all():
                    linked_children.append((group, childgroup))
                marked_groups.append(group)
            for group in marked_groups:
                group.mark_inactive()
            for host in marked_hosts:
                host.mark_inactive()
        with ignore_inventory_computed_fields():
            mark_actual()
        self.inventory.update_computed_fields()

    def mark_inactive(self, save=True, recompute=True):
        '''
        When marking groups inactive, remove all associations to related
        groups/hosts/inventory_sources.
        '''
        def mark_actual():
            super(Group, self).mark_inactive(save=save)
            self.inventory_source.mark_inactive(save=save)
            self.inventory_sources.clear()
            self.parents.clear()
            self.children.clear()
            self.hosts.clear()
        i = self.inventory

        if recompute:
            with ignore_inventory_computed_fields():
                mark_actual()
            i.update_computed_fields()
        else:
            mark_actual()

    def update_computed_fields(self):
        '''
        Update model fields that are computed from database relationships.
        '''
        active_hosts = self.all_hosts.filter(active=True)
        failed_hosts = active_hosts.filter(last_job_host_summary__job__active=True,
                                           last_job_host_summary__failed=True)
        active_groups = self.all_children.filter(active=True)
        # FIXME: May not be accurate unless we always update groups depth-first.
        failed_groups = active_groups.filter(has_active_failures=True)
        active_inventory_sources = self.inventory_sources.filter(active=True,
                                                                 source__in=CLOUD_INVENTORY_SOURCES)
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
        Return all parents of this group recursively, avoiding infinite
        recursion in the case of cyclical relations.  The group itself will be
        excluded unless there is a cycle leading back to it.
        '''
        except_pks = except_pks or set()
        except_pks.add(self.pk)
        qs = self.parents.distinct()
        for group in self.parents.exclude(pk__in=except_pks):
            qs = qs | group.get_all_parents(except_pks)
        return qs

    @property
    def all_parents(self):
        return self.get_all_parents()

    def get_all_children(self, except_pks=None):
        '''
        Return all children of this group recursively, avoiding infinite
        recursion in the case of cyclical relations.  The group itself will be
        excluded unless there is a cycle leading back to it.
        '''
        except_pks = except_pks or set()
        except_pks.add(self.pk)
        qs = self.children.distinct()
        for group in self.children.exclude(pk__in=except_pks):
            qs = qs | group.get_all_children(except_pks)
        return qs

    @property
    def all_children(self):
        return self.get_all_children()

    def get_all_hosts(self, except_group_pks=None):
        '''
        Return all hosts associated with this group or any of its children,
        avoiding infinite recursion in the case of cyclical group relations.
        '''
        except_group_pks = except_group_pks or set()
        except_group_pks.add(self.pk)
        qs = self.hosts.distinct()
        for group in self.children.exclude(pk__in=except_group_pks):
            qs = qs | group.get_all_hosts(except_group_pks)
        return qs

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


class InventorySourceOptions(BaseModel):
    '''
    Common fields for InventorySource and InventoryUpdate.
    '''

    SOURCE_CHOICES = [
        ('file', _('Local File, Directory or Script')),
        ('rax', _('Rackspace Cloud Servers')),
        ('ec2', _('Amazon EC2')),
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
        editable=False,
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
    overwrite = models.BooleanField(
        default=False,
        help_text=_('Overwrite local groups and hosts from remote inventory source.'),
    )
    overwrite_vars = models.BooleanField(
        default=False,
        help_text=_('Overwrite local variables from remote inventory source.'),
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
    def get_rax_region_choices(cls):
        # Not possible to get rax regions without first authenticating, so use
        # list from settings.
        regions = list(getattr(settings, 'RAX_REGION_CHOICES', []))
        regions.insert(0, ('ALL', 'All'))
        return regions

    def clean_credential(self):
        if not self.source:
            return None
        cred = self.credential
        if cred:
            if self.source == 'ec2' and cred.kind != 'aws':
                raise ValidationError('Credential kind must be "aws" for an '
                                      '"ec2" source')
            if self.source == 'rax' and cred.kind != 'rax':
                raise ValidationError('Credential kind must be "rax" for a '
                                    '"rax" source')
        elif self.source in ('ec2', 'rax'):
            raise ValidationError('Credential is required for a cloud source')
        return cred

    def clean_source_regions(self):
        regions = self.source_regions
        if self.source == 'ec2':
            valid_regions = [x[0] for x in self.get_ec2_region_choices()]
            region_transform = lambda x: x.strip().lower()
        elif self.source == 'rax':
            valid_regions = [x[0] for x in self.get_rax_region_choices()]
            region_transform = lambda x: x.strip().upper()
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
            raise ValidationError('Invalid %s region%s: %s' % (self.source,
                                  '' if len(invalid_regions) == 1 else 's',
                                  ', '.join(invalid_regions)))
        return ','.join(regions)

    source_vars_dict = VarsDictProperty('source_vars')


class InventorySource(UnifiedJobTemplate, InventorySourceOptions):

    class Meta:
        app_label = 'main'

    inventory = models.ForeignKey(
        'Inventory',
        related_name='inventory_sources',
        null=True,
        default=None,
        editable=False,
        on_delete=models.CASCADE,
    )
    group = AutoOneToOneField(
        'Group',
        related_name='inventory_source',
        null=True,
        default=None,
        editable=False,
        on_delete=models.CASCADE,
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
        return ['name', 'description', 'source', 'source_path', 'source_vars',
                'credential', 'source_regions', 'overwrite', 'overwrite_vars']

    def save(self, *args, **kwargs):
        new_instance = bool(self.pk)
        # If update_fields has been specified, add our field names to it,
        # if it hasn't been specified, then we're just doing a normal save.
        update_fields = kwargs.get('update_fields', [])
        # Update inventory from group (if available).
        if self.group and not self.inventory:
            self.inventory = self.group.inventory
            if 'inventory' not in update_fields:
                update_fields.append('inventory')
        # Set name automatically.
        replace_text = '__replace_%s__' % now()
        old_name_re = re.compile(r'^inventory_source \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}.*?$')
        if not self.name or old_name_re.match(self.name):
            if self.inventory and self.group:
                self.name = '%s (%s)' % (self.group.name, self.inventory.name)
            elif self.inventory and self.pk:
                self.name = '%s (%s)' % (self.inventory.name, self.pk)
            elif self.inventory:
                self.name = '%s (%s)' % (self.inventory.name, replace_text)
            elif self.pk:
                self.name = 'inventory source (%s)' % self.pk
            else:
                self.name = 'inventory source (%s)' % replace_text
            if 'name' not in update_fields:
                update_fields.append('name')
        # Do the actual save.
        super(InventorySource, self).save(*args, **kwargs)
        # Add the PK to the name if only attached to an inventory (no group).
        if new_instance and self.inventory and replace_text in self.name:
            self.name = self.name.replace(replace_text, str(self.pk))
            self.save(update_fields=['name'])

    def _get_current_status(self):
        if self.source:
            if self.current_job:
                return 'running'
            elif not self.last_job:
                return 'never updated'
            elif self.last_job_failed:
                return 'failed'
            else:
                return 'successful'
        else:
            return 'none'

    def get_absolute_url(self):
        return reverse('api:inventory_source_detail', args=(self.pk,))

    def _can_update(self):
        return bool(self.source in CLOUD_INVENTORY_SOURCES)

    def create_inventory_update(self, **kwargs):
        return self.create_unified_job(**kwargs)

    @property
    def needs_update_on_launch(self):
        if self.active and self.source and self.update_on_launch:
            if not self.last_job_run:
                return True
            if (self.last_job_run + datetime.timedelta(seconds=self.update_cache_timeout)) <= now():
                return True
        return False

    def clean_source(self):
        source = self.source
        if source and self.group:
            qs = self.group.inventory_sources.filter(source__in=CLOUD_INVENTORY_SOURCES, active=True, group__active=True)
            existing_sources = qs.exclude(pk=self.pk)
            if existing_sources.count():
                s = u', '.join([x.group.name for x in existing_sources])
                raise ValidationError('Unable to configure this item for cloud sync. It is already managed by %s.' % s)
        return source


class InventoryUpdate(UnifiedJob, InventorySourceOptions):
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

    @classmethod
    def _get_parent_field_name(cls):
        return 'inventory_source'

    @classmethod
    def _get_task_class(cls):
        from awx.main.tasks import RunInventoryUpdate
        return RunInventoryUpdate

    def socketio_emit_data(self):
        if self.inventory_source.group is not None:
            return dict(group_id=self.inventory_source.group.id)

    def save(self, *args, **kwargs):
        update_fields = kwargs.get('update_fields', [])
        if bool('license' in self.result_stdout and
                'exceeded' in self.result_stdout and not self.license_error):
            self.license_error = True
            if 'license_error' not in update_fields:
                update_fields.append('license_error')
        super(InventoryUpdate, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('api:inventory_update_detail', args=(self.pk,))

    def is_blocked_by(self, obj):
        if type(obj) == InventoryUpdate:
            if self.inventory_source.inventory == obj.inventory_source.inventory:
                return True
        if type(obj) == Job:
            if self.inventory_source.inventory == obj.inventory:
                return True
        return False

    @property
    def task_impact(self):
        return 50
