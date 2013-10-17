# Copyright (c) 2013 AnsibleWorks, Inc.
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

# Django
from django.conf import settings
from django.db import models
from django.db.models import CASCADE, SET_NULL, PROTECT
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils.timezone import now, make_aware, get_default_timezone

# Django-JSONField
from jsonfield import JSONField

# Django-Taggit
from taggit.managers import TaggableManager

# Django-Celery
from djcelery.models import TaskMeta

# AWX
from awx.main.compat import slugify
from awx.main.fields import AutoOneToOneField
from awx.main.utils import encrypt_field, decrypt_field

__all__ = ['PrimordialModel', 'Organization', 'Team', 'Project',
           'ProjectUpdate', 'Credential', 'Inventory', 'Host', 'Group',
           'InventorySource', 'InventoryUpdate', 'Permission', 'JobTemplate',
           'Job', 'JobHostSummary', 'JobEvent', 'AuthToken',
           'PERM_INVENTORY_ADMIN', 'PERM_INVENTORY_READ',
           'PERM_INVENTORY_WRITE', 'PERM_INVENTORY_DEPLOY',
           'PERM_INVENTORY_CHECK', 'JOB_STATUS_CHOICES',
           'CLOUD_INVENTORY_SOURCES']

logger = logging.getLogger('awx.main.models')

# TODO: reporting model TBD

PERM_INVENTORY_ADMIN  = 'admin'
PERM_INVENTORY_READ   = 'read'
PERM_INVENTORY_WRITE  = 'write'
PERM_INVENTORY_DEPLOY = 'run'
PERM_INVENTORY_CHECK  = 'check'

JOB_TYPE_CHOICES = [
    (PERM_INVENTORY_DEPLOY, _('Run')),
    (PERM_INVENTORY_CHECK, _('Check')),
]

# FIXME: TODO: make sure all of these are used and consistent
PERMISSION_TYPE_CHOICES = [
    (PERM_INVENTORY_READ, _('Read Inventory')),
    (PERM_INVENTORY_WRITE, _('Edit Inventory')),
    (PERM_INVENTORY_ADMIN, _('Administrate Inventory')),
    (PERM_INVENTORY_DEPLOY, _('Deploy To Inventory')),
    (PERM_INVENTORY_CHECK, _('Deploy To Inventory (Dry Run)')),
]

JOB_STATUS_CHOICES = [
    ('new', _('New')),                  # Job has been created, but not started.
    ('pending', _('Pending')),          # Job has been queued, but is not yet running.
    ('waiting', _('Waiting')),          # Job is waiting on an update/dependency.
    ('running', _('Running')),          # Job is currently running.
    ('successful', _('Successful')),    # Job completed successfully.
    ('failed', _('Failed')),            # Job completed, but with failures.
    ('error', _('Error')),              # The job was unable to run.
    ('canceled', _('Canceled')),        # The job was canceled before completion.
]

CLOUD_INVENTORY_SOURCES = ['ec2', 'rackspace']

class PrimordialModel(models.Model):
    '''
    common model for all object types that have these standard fields
    must use a subclass CommonModel or CommonModelNameNotUnique though
    as this lacks a name field.
    '''

    class Meta:
        abstract = True

    description   = models.TextField(blank=True, default='')
    created       = models.DateTimeField(auto_now_add=True)
    modified      = models.DateTimeField(auto_now=True, default=now)
    created_by    = models.ForeignKey('auth.User',
                                      related_name='%s(class)s_created+',
                                      default=None, null=True, editable=False,
                                      on_delete=models.SET_NULL)
    modified_by   = models.ForeignKey('auth.User',
                                      related_name='%s(class)s_modified+',
                                      default=None, null=True, editable=False,
                                      on_delete=models.SET_NULL)
    active        = models.BooleanField(default=True)

    tags = TaggableManager(blank=True)

    def __unicode__(self):
        if hasattr(self, 'name'):
            return unicode("%s-%s"% (self.name, self.id))
        else:
            return u'%s-%s' % (self._meta.verbose_name, self.id)

    def save(self, *args, **kwargs):
        # For compatibility with Django 1.4.x, attempt to handle any calls to
        # save that pass update_fields.
        try:
            super(PrimordialModel, self).save(*args, **kwargs)
        except TypeError:
            if 'update_fields' not in kwargs:
                raise
            kwargs.pop('update_fields')
            super(PrimordialModel, self).save(*args, **kwargs)

    def mark_inactive(self, save=True):
        '''Use instead of delete to rename and mark inactive.'''

        if self.active:
            if 'name' in self._meta.get_all_field_names():
                self.name   = "_deleted_%s_%s" % (now().isoformat(), self.name)
            self.active = False
            if save:
                self.save()

class CommonModel(PrimordialModel):
    ''' a base model where the name is unique '''

    class Meta:
        abstract = True

    name          = models.CharField(max_length=512, unique=True)

class CommonModelNameNotUnique(PrimordialModel):
    ''' a base model where the name is not unique '''

    class Meta:
        abstract = True

    name          = models.CharField(max_length=512, unique=False)

class Organization(CommonModel):
    '''
    organizations are the basic unit of multi-tenancy divisions
    '''

    class Meta:
        app_label = 'main'

    users    = models.ManyToManyField('auth.User', blank=True, related_name='organizations')
    admins   = models.ManyToManyField('auth.User', blank=True, related_name='admin_of_organizations')
    projects = models.ManyToManyField('Project', blank=True, related_name='organizations')

    def get_absolute_url(self):
        return reverse('main:organization_detail', args=(self.pk,))

    def __unicode__(self):
        return self.name

class Inventory(CommonModel):
    '''
    an inventory source contains lists and hosts.
    '''

    class Meta:
        app_label = 'main'
        verbose_name_plural = _('inventories')
        unique_together = (("name", "organization"),)

    organization = models.ForeignKey(
        Organization,
        null=False,
        related_name='inventories',
        help_text=_('Organization containing this inventory.'),
    )
    variables = models.TextField(
        blank=True,
        default='',
        null=True,
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
        return reverse('main:inventory_detail', args=(self.pk,))

    def mark_inactive(self, save=True):
        '''
        When marking inventory inactive, also mark hosts and groups inactive.
        '''
        super(Inventory, self).mark_inactive(save=save)
        for host in self.hosts.filter(active=True):
            host.mark_inactive()
        for group in self.groups.filter(active=True):
            group.mark_inactive()
            group.inventory_source.mark_inactive()
        for inventory_source in self.inventory_sources.filter(active=True):
            inventory_source.mark_inactive()

    @property
    def variables_dict(self):
        try:
            return json.loads(self.variables.strip() or '{}')
        except ValueError:
            return yaml.safe_load(self.variables)

    def update_computed_fields(self, update_groups=True, update_hosts=True):
        '''
        Update model fields that are computed from database relationships.
        '''
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
        failed_inventory_sources = active_inventory_sources.filter(last_update_failed=True)
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
        unique_together = (("name", "inventory"),)

    inventory = models.ForeignKey(
        'Inventory',
        null=False,
        related_name='hosts',
    )
    enabled = models.BooleanField(
        default=True,
        help_text=_('Is this host online and available for running jobs?'),
    )
    variables = models.TextField(
        blank=True,
        default='',
        help_text=_('Host variables in JSON or YAML format.'),
    )
    last_job = models.ForeignKey(
        'Job',
        related_name='hosts_as_last_job+',
        blank=True,
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
        blank=True,
        editable=False,
        help_text=_('Inventory source(s) that created or modified this host.'),
    )

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('main:host_detail', args=(self.pk,))

    def mark_inactive(self, save=True):
        '''
        When marking hosts inactive, remove all associations to related
        inventory sources.
        '''
        super(Host, self).mark_inactive(save=save)
        self.inventory_sources.clear()

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

    @property
    def variables_dict(self):
        try:
            return json.loads(self.variables.strip() or '{}')
        except ValueError:
            return yaml.safe_load(self.variables)

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
        null=False,
        related_name='groups',
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
        blank=True,
        editable=False,
        help_text=_('Inventory source(s) that created or modified this group.'),
    )

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('main:group_detail', args=(self.pk,))

    def mark_inactive(self, save=True):
        '''
        When marking groups inactive, remove all associations to related
        groups/hosts/inventory_sources.
        '''
        super(Group, self).mark_inactive(save=save)
        self.inventory_source.mark_inactive(save=save)
        self.inventory_sources.clear()
        self.parents.clear()
        self.children.clear()
        self.hosts.clear()

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

    @property
    def variables_dict(self):
        try:
            return json.loads(self.variables.strip() or '{}')
        except ValueError:
            return yaml.safe_load(self.variables)

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
        return JobHostSummary.objects.filter(host__in=self.all_hosts)

    @property
    def job_events(self):
        return JobEvent.objects.filter(host__in=self.all_hosts)

class InventorySource(PrimordialModel):

    SOURCE_CHOICES = [
        ('file', _('Local File, Directory or Script')),
        ('rackspace', _('Rackspace Cloud Servers')),
        ('ec2', _('Amazon EC2')),
    ]

    PASSWORD_FIELDS = ('source_password',)

    INVENTORY_SOURCE_STATUS_CHOICES = [
        ('none', _('No External Source')),
        ('never updated', _('Never Updated')),
        ('updating', _('Updating')),
        ('failed', _('Failed')),
        ('successful', _('Successful')),
    ]

    inventory = models.ForeignKey(
        'Inventory',
        related_name='inventory_sources',
        null=True,
        default=None,
        editable=False,
    )
    group = AutoOneToOneField(
        'Group',
        related_name='inventory_source',
        blank=True,
        null=True,
        default=None,
        editable=False,
    )
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
    )
    source_username = models.CharField(
        max_length=1024,
        blank=True,
        default='',
    )
    source_password = models.CharField(
        max_length=1024,
        blank=True,
        default='',
    )
    source_regions = models.CharField(
        max_length=1024,
        blank=True,
        default='',
    )
    source_tags = models.CharField(
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
    update_on_launch = models.BooleanField(
        default=False,
    )
    update_interval = models.PositiveIntegerField(
        default=0,
        help_text=_('If nonzero, inventory source will be updated every N minutes.'),
    )
    current_update = models.ForeignKey(
        'InventoryUpdate',
        null=True,
        default=None,
        editable=False,
        related_name='inventory_source_as_current_update+',
    )
    last_update = models.ForeignKey(
        'InventoryUpdate',
        null=True,
        default=None,
        editable=False,
        related_name='inventory_source_as_last_update+',
    )
    last_update_failed = models.BooleanField(
        default=False,
        editable=False,
    )
    last_updated = models.DateTimeField(
        null=True,
        default=None,
        editable=False,
    )
    status = models.CharField(
        max_length=32,
        choices=INVENTORY_SOURCE_STATUS_CHOICES,
        default='none',
        editable=False,
        null=True,
    )

    def save(self, *args, **kwargs):
        new_instance = not bool(self.pk)
        # If update_fields has been specified, add our field names to it,
        # if it hasn't been specified, then we're just doing a normal save.
        update_fields = kwargs.get('update_fields', [])
        # When first saving to the database, don't store any password field
        # values, but instead save them until after the instance is created.
        if new_instance:
            for field in self.PASSWORD_FIELDS:
                value = getattr(self, field, '')
                setattr(self, '_saved_%s' % field, value)
                setattr(self, field, '')
        # Otherwise, store encrypted values to the database.
        else:
            for field in self.PASSWORD_FIELDS:
                encrypted = encrypt_field(self, field, True)
                if getattr(self, field) != encrypted:
                    setattr(self, field, encrypted)
                    if field not in update_fields:
                        update_fields.append(field)
        # Update status and last_updated fields.
        updated_fields = self.set_status_and_last_updated(save=False)
        for field in updated_fields:
            if field not in update_fields:
                update_fields.append(field)
        # Update inventory from group (if available).
        if self.group and not self.inventory:
            self.inventory = self.group.inventory
            if 'inventory' not in update_fields:
                update_fields.append('inventory')
        # Do the actual save.
        super(InventorySource, self).save(*args, **kwargs)
        # After saving a new instance for the first time (to get a primary
        # key), set the password fields and save again.
        if new_instance:
            update_fields=[]
            for field in self.PASSWORD_FIELDS:
                saved_value = getattr(self, '_saved_%s' % field, '')
                if getattr(self, field) != saved_value:
                    setattr(self, field, saved_value)
                    update_fields.append(field)
            if update_fields:
                self.save(update_fields=update_fields)

    @property
    def needs_source_password(self):
        return self.source and self.source_password == 'ASK'

    @property
    def source_passwords_needed(self):
        needed = []
        for field in ('source_password',):
            if getattr(self, 'needs_%s' % field):
                needed.append(field)
        return needed

    def set_status_and_last_updated(self, save=True):
        # Determine current status.
        if self.source:
            if self.current_update:
                status = 'updating'
            elif not self.last_update:
                status = 'never updated'
            elif self.last_update_failed:
                status = 'failed'
            else:
                status = 'successful'
        else:
            status = 'none'
        # Determine current last_updated timestamp.
        last_updated = None
        if self.source and self.last_update:
            last_updated = self.last_update.modified
        # Update values if changed.
        update_fields = []
        if self.status != status:
            self.status = status
            update_fields.append('status')
        if self.last_updated != last_updated:
            self.last_updated = last_updated
            update_fields.append('last_updated')
        if save and update_fields:
            self.save(update_fields=update_fields)
        return update_fields

    @property
    def can_update(self):
        # FIXME: Prevent update when another one is active!
        return bool(self.source)

    def update(self, **kwargs):
        if self.can_update:
            needed = self.source_passwords_needed
            opts = dict([(field, kwargs.get(field, '')) for field in needed])
            if not all(opts.values()):
                return
            inventory_update = self.inventory_updates.create()
            inventory_update.start(**opts)
            return inventory_update

    def get_absolute_url(self):
        return reverse('main:inventory_source_detail', args=(self.pk,))

class InventoryUpdate(PrimordialModel):
    '''
    Internal job for tracking inventory updates from external sources.
    '''

    class Meta:
        app_label = 'main'

    inventory_source = models.ForeignKey(
        'InventorySource',
        related_name='inventory_updates',
        on_delete=models.CASCADE,
        editable=False,
    )
    cancel_flag = models.BooleanField(
        blank=True,
        default=False,
        editable=False,
    )
    status = models.CharField(
        max_length=20,
        choices=JOB_STATUS_CHOICES,
        default='new',
        editable=False,
    )
    failed = models.BooleanField(
        default=False,
        editable=False,
    )
    job_args = models.TextField(
        blank=True,
        default='',
        editable=False,
    )
    job_cwd = models.CharField(
        max_length=1024,
        blank=True,
        default='',
        editable=False,
    )
    job_env = JSONField(
        blank=True,
        default={},
        editable=False,
    )
    result_stdout = models.TextField(
        blank=True,
        default='',
        editable=False,
    )
    result_traceback = models.TextField(
        blank=True,
        default='',
        editable=False,
    )
    celery_task_id = models.CharField(
        max_length=100,
        blank=True,
        default='',
        editable=False,
    )

    def __unicode__(self):
        return u'%s-%s-%s' % (self.created, self.id, self.status)

    def save(self, *args, **kwargs):
        # Get status before save...
        status_before = self.status or 'new'
        if self.pk:
            inventory_update_before = InventoryUpdate.objects.get(pk=self.pk)
            if inventory_update_before.status != self.status:
                status_before = inventory_update_before.status
        self.failed = bool(self.status in ('failed', 'error', 'canceled'))
        super(InventoryUpdate, self).save(*args, **kwargs)
        # If status changed, update inventory.
        if self.status != status_before:
            if self.status in ('pending', 'waiting', 'running'):
                inventory_source = self.inventory_source
                if inventory_source.current_update != self:
                    inventory_source.current_update = self
                    inventory_source.save(update_fields=['current_update'])
            elif self.status in ('successful', 'failed', 'error', 'canceled'):
                inventory_source = self.inventory_source
                if inventory_source.current_update == self:
                    inventory_source.current_update = None
                inventory_source.last_update = self
                inventory_source.last_update_failed = self.failed
                inventory_source.save(update_fields=['current_update', 'last_update',
                                            'last_update_failed'])

    def get_absolute_url(self):
        return reverse('main:inventory_update_detail', args=(self.pk,))

    @property
    def celery_task(self):
        try:
            if self.celery_task_id:
                return TaskMeta.objects.get(task_id=self.celery_task_id)
        except TaskMeta.DoesNotExist:
            pass

    @property
    def can_start(self):
        return bool(self.status == 'new')

    def start(self, **kwargs):
        from awx.main.tasks import RunInventoryUpdate
        needed = self.inventory_source.source_passwords_needed
        opts = dict([(field, kwargs.get(field, '')) for field in needed])
        if not all(opts.values()):
            return False
        self.status = 'pending'
        self.save(update_fields=['status'])
        task_result = RunInventoryUpdate().delay(self.pk, **opts)
        # Reload inventory update from database so we don't clobber results
        # from RunInventoryUpdate (mainly from tests when using Django 1.4.x).
        inventory_update = InventoryUpdate.objects.get(pk=self.pk)
        # The TaskMeta instance in the database isn't created until the worker
        # starts processing the task, so we can only store the task ID here.
        inventory_update.celery_task_id = task_result.task_id
        inventory_update.save(update_fields=['celery_task_id'])
        return True

    @property
    def can_cancel(self):
        return bool(self.status in ('pending', 'waiting', 'running'))

    def cancel(self):
        if self.can_cancel:
            if not self.cancel_flag:
                self.cancel_flag = True
                self.save(update_fields=['cancel_flag'])
        return self.cancel_flag

class Credential(CommonModelNameNotUnique):
    '''
    A credential contains information about how to talk to a remote set of hosts
    Usually this is a SSH key location, and possibly an unlock password.
    If used with sudo, a sudo password should be set if required.
    '''

    PASSWORD_FIELDS = ('ssh_password', 'ssh_key_data', 'ssh_key_unlock', 'sudo_password')

    class Meta:
        app_label = 'main'

    user            = models.ForeignKey('auth.User', null=True, default=None, blank=True, on_delete=SET_NULL, related_name='credentials')
    team            = models.ForeignKey('Team', null=True, default=None, blank=True, on_delete=SET_NULL, related_name='credentials')

    ssh_username = models.CharField(
        blank=True,
        default='',
        max_length=1024,
        verbose_name=_('SSH username'),
        help_text=_('SSH username for a job using this credential.'),
    )
    ssh_password = models.CharField(
        blank=True,
        default='',
        max_length=1024,
        verbose_name=_('SSH password'),
        help_text=_('SSH password (or "ASK" to prompt the user).'),
    )
    ssh_key_data = models.TextField(
        blank=True,
        default='',
        verbose_name=_('SSH private key'),
        help_text=_('RSA or DSA private key to be used instead of password.'),
    )
    ssh_key_unlock = models.CharField(
        max_length=1024,
        blank=True,
        default='',
        verbose_name=_('SSH key unlock'),
        help_text=_('Passphrase to unlock SSH private key if encrypted (or '
                    '"ASK" to prompt the user).'),
    )
    sudo_username = models.CharField(
        max_length=1024,
        blank=True,
        default='',
        help_text=_('Sudo username for a job using this credential.'),
    )
    sudo_password = models.CharField(
        max_length=1024,
        blank=True,
        default='',
        help_text=_('Sudo password (or "ASK" to prompt the user).'),
    )

    @property
    def needs_ssh_password(self):
        return not self.ssh_key_data and self.ssh_password == 'ASK'

    @property
    def needs_ssh_key_unlock(self):
        return 'ENCRYPTED' in decrypt_field(self, 'ssh_key_data') and \
            (not self.ssh_key_unlock or self.ssh_key_unlock == 'ASK')

    @property
    def needs_sudo_password(self):
        return self.sudo_password == 'ASK'
    
    @property
    def passwords_needed(self):
        needed = []
        for field in ('ssh_password', 'sudo_password', 'ssh_key_unlock'):
            if getattr(self, 'needs_%s' % field):
                needed.append(field)
        return needed

    def get_absolute_url(self):
        return reverse('main:credential_detail', args=(self.pk,))

    def save(self, *args, **kwargs):
        new_instance = not bool(self.pk)
        # When first saving to the database, don't store any password field
        # values, but instead save them until after the instance is created.
        if new_instance:
            for field in self.PASSWORD_FIELDS:
                value = getattr(self, field, '')
                setattr(self, '_saved_%s' % field, value)
                setattr(self, field, '')
        # Otherwise, store encrypted values to the database.
        else:
            # If update_fields has been specified, add our field names to it,
            # if hit hasn't been specified, then we're just doing a normal save.
            update_fields = kwargs.get('update_fields', [])
            for field in self.PASSWORD_FIELDS:
                encrypted = encrypt_field(self, field, bool(field != 'ssh_key_data'))
                setattr(self, field, encrypted)
                if field not in update_fields:
                    update_fields.append(field)
        super(Credential, self).save(*args, **kwargs)
        # After saving a new instance for the first time, set the password
        # fields and save again.
        if new_instance:
            update_fields=[]
            for field in self.PASSWORD_FIELDS:
                saved_value = getattr(self, '_saved_%s' % field, '')
                setattr(self, field, saved_value)
                update_fields.append(field)
            self.save(update_fields=update_fields)

class Team(CommonModel):
    '''
    A team is a group of users that work on common projects.
    '''

    class Meta:
        app_label = 'main'

    projects        = models.ManyToManyField('Project', blank=True, related_name='teams')
    users           = models.ManyToManyField('auth.User', blank=True, related_name='teams')
    organization    = models.ForeignKey('Organization', blank=False, null=True, on_delete=SET_NULL, related_name='teams')

    def get_absolute_url(self):
        return reverse('main:team_detail', args=(self.pk,))

class Project(CommonModel):
    '''
    A project represents a playbook git repo that can access a set of inventories
    '''

    PROJECT_STATUS_CHOICES = [
        ('ok', 'OK'),
        ('missing', 'Missing'),
        ('never updated', 'Never Updated'),
        ('updating', 'Updating'),
        ('failed', 'Failed'),
        ('successful', 'Successful'),
    ]
        
    PASSWORD_FIELDS = ('scm_password', 'scm_key_data', 'scm_key_unlock')

    SCM_TYPE_CHOICES = [
        ('', _('Manual')),
        ('git', _('Git')),
        ('hg', _('Mercurial')),
        ('svn', _('Subversion')),
    ]
    
    # this is not part of the project, but managed with perms
    # inventories      = models.ManyToManyField('Inventory', blank=True, related_name='projects')

    # Project files must be available on the server in folders directly
    # beneath the path specified by settings.PROJECTS_ROOT.  There is no way
    # via the API to upload/update a project or its playbooks; this must be
    # done by other means for now.

    @classmethod
    def get_local_path_choices(cls):
        if os.path.exists(settings.PROJECTS_ROOT):
            paths = [x for x in os.listdir(settings.PROJECTS_ROOT)
                     if os.path.isdir(os.path.join(settings.PROJECTS_ROOT, x))
                     and not x.startswith('.') and not x.startswith('_')]
            qs = Project.objects.filter(active=True)
            used_paths = qs.values_list('local_path', flat=True)
            return [x for x in paths if x not in used_paths]
        else:
            return []

    local_path = models.CharField(
        max_length=1024,
        blank=True,
        help_text=_('Local path (relative to PROJECTS_ROOT) containing '
                    'playbooks and related files for this project.')
    )

    scm_type = models.CharField(
        max_length=8,
        choices=SCM_TYPE_CHOICES,
        blank=True,
        null=True,
        default='',
        verbose_name=_('SCM Type'),
    )
    scm_url = models.CharField(
        max_length=1024,
        blank=True,
        null=True,
        default='',
        verbose_name=_('SCM URL'),
    )
    scm_branch = models.CharField(
        max_length=256,
        blank=True,
        null=True,
        default='',
        verbose_name=_('SCM Branch'),
        help_text=_('Specific branch, tag or commit to checkout.'),
    )
    scm_clean = models.BooleanField(
        default=False,
    )
    scm_delete_on_update = models.BooleanField(
        default=False,
    )
    scm_delete_on_next_update = models.BooleanField(
        default=False,
        editable=False,
    )
    scm_update_on_launch = models.BooleanField(
        default=False,
    )
    scm_username = models.CharField(
        blank=True,
        null=True,
        default='',
        max_length=256,
        verbose_name=_('Username'),
        help_text=_('SCM username for this project.'),
    )
    scm_password = models.CharField(
        blank=True,
        null=True,
        default='',
        max_length=1024,
        verbose_name=_('Password'),
        help_text=_('SCM password (or "ASK" to prompt the user).'),
    )
    scm_key_data = models.TextField(
        blank=True,
        null=True,
        default='',
        verbose_name=_('SSH private key'),
        help_text=_('RSA or DSA private key to be used instead of password.'),
    )
    scm_key_unlock = models.CharField(
        max_length=1024,
        null=True,
        blank=True,
        default='',
        verbose_name=_('SSH key unlock'),
        help_text=_('Passphrase to unlock SSH private key if encrypted (or '
                    '"ASK" to prompt the user).'),
    )
    current_update = models.ForeignKey(
        'ProjectUpdate',
        null=True,
        default=None,
        editable=False,
        related_name='project_as_current_update+',
    )
    last_update = models.ForeignKey(
        'ProjectUpdate',
        null=True,
        default=None,
        editable=False,
        related_name='project_as_last_update+',
    )
    last_update_failed = models.BooleanField(
        default=False,
        editable=False,
    )
    last_updated = models.DateTimeField(
        null=True,
        default=None,
        editable=False,
    )
    status = models.CharField(
        max_length=32,
        choices=PROJECT_STATUS_CHOICES,
        default='ok',
        editable=False,
        null=True,
    )

    def save(self, *args, **kwargs):
        new_instance = not bool(self.pk)
        # If update_fields has been specified, add our field names to it,
        # if it hasn't been specified, then we're just doing a normal save.
        update_fields = kwargs.get('update_fields', [])
        # When first saving to the database, don't store any password field
        # values, but instead save them until after the instance is created.
        if new_instance:
            for field in self.PASSWORD_FIELDS:
                value = getattr(self, field, '')
                setattr(self, '_saved_%s' % field, value)
                setattr(self, field, '')
        # Otherwise, store encrypted values to the database.
        else:
            for field in self.PASSWORD_FIELDS:
                encrypted = encrypt_field(self, field, bool(field != 'scm_key_data'))
                if getattr(self, field) != encrypted:
                    setattr(self, field, encrypted)
                    if field not in update_fields:
                        update_fields.append(field)
        # Check if scm_type or scm_url changes.
        if self.pk:
            project_before = Project.objects.get(pk=self.pk)
            if project_before.scm_type != self.scm_type or project_before.scm_url != self.scm_url:
                self.scm_delete_on_next_update = True
                if 'scm_delete_on_next_update' not in update_fields:
                    update_fields.append('scm_delete_on_next_update')
        # Create auto-generated local path if project uses SCM.
        if self.pk and self.scm_type and not self.local_path.startswith('_'):
            slug_name = slugify(unicode(self.name)).replace(u'-', u'_')
            self.local_path = u'_%d__%s' % (self.pk, slug_name)
            if 'local_path' not in update_fields:
                update_fields.append('local_path')
        # Update status and last_updated fields.
        updated_fields = self.set_status_and_last_updated(save=False)
        for field in updated_fields:
            if field not in update_fields:
                update_fields.append(field)
        # Do the actual save.
        super(Project, self).save(*args, **kwargs)
        # After saving a new instance for the first time (to get a primary
        # key), set the password fields and save again.
        if new_instance:
            update_fields=[]
            # Generate local_path for SCM after initial save (so we have a PK).
            if self.scm_type and not self.local_path.startswith('_'):
                update_fields.append('local_path')
            for field in self.PASSWORD_FIELDS:
                saved_value = getattr(self, '_saved_%s' % field, '')
                if getattr(self, field) != saved_value:
                    setattr(self, field, saved_value)
                    update_fields.append(field)
            if update_fields:
                self.save(update_fields=update_fields)
        # If we just created a new project with SCM and it doesn't require any
        # passwords to update, start the initial update.
        if new_instance and self.scm_type and not self.scm_passwords_needed:
            self.update()

    @property
    def needs_scm_password(self):
        return self.scm_type and not self.scm_key_data and \
            self.scm_password == 'ASK'

    @property
    def needs_scm_key_unlock(self):
        return self.scm_type and self.scm_key_data and \
            'ENCRYPTED' in decrypt_field(self, 'scm_key_data') and \
            (not self.scm_key_unlock or self.scm_key_unlock == 'ASK')

    @property
    def scm_passwords_needed(self):
        needed = []
        for field in ('scm_password', 'scm_key_unlock'):
            if getattr(self, 'needs_%s' % field):
                needed.append(field)
        return needed

    def set_status_and_last_updated(self, save=True):
        # Determine current status.
        if self.scm_type:
            if self.current_update:
                status = 'updating'
            elif not self.last_update:
                status = 'never updated'
            elif self.last_update_failed:
                status = 'failed'
            elif not self.get_project_path():
                status = 'missing'
            else:
                status = 'successful'
        elif not self.get_project_path():
            status = 'missing'
        else:
            status = 'ok'
        # Determine current last_updated timestamp.
        last_updated = None
        if self.scm_type and self.last_update:
            last_updated = self.last_update.modified
        else:
            project_path = self.get_project_path()
            if project_path:
                try:
                    mtime = os.path.getmtime(project_path)
                    dt = datetime.datetime.fromtimestamp(mtime)
                    last_updated = make_aware(dt, get_default_timezone())
                except os.error:
                    pass
        # Update values if changed.
        update_fields = []
        if self.status != status:
            self.status = status
            update_fields.append('status')
        if self.last_updated != last_updated:
            self.last_updated = last_updated
            update_fields.append('last_updated')
        if save and update_fields:
            self.save(update_fields=update_fields)
        return update_fields

    @property
    def can_update(self):
        # FIXME: Prevent update when another one is active!
        return bool(self.scm_type)# and not self.current_update)

    def update(self, **kwargs):
        if self.can_update:
            needed = self.scm_passwords_needed
            opts = dict([(field, kwargs.get(field, '')) for field in needed])
            if not all(opts.values()):
                return
            project_update = self.project_updates.create()
            project_update.start(**opts)
            return project_update

    def get_absolute_url(self):
        return reverse('main:project_detail', args=(self.pk,))

    def get_project_path(self, check_if_exists=True):
        local_path = os.path.basename(self.local_path)
        if local_path and not local_path.startswith('.'):
            proj_path = os.path.join(settings.PROJECTS_ROOT, local_path)
            if not check_if_exists or os.path.exists(proj_path):
                return proj_path

    @property
    def playbooks(self):
        valid_re = re.compile(r'^\s*?-?\s*?(?:hosts|include):\s*?.*?$')
        results = []
        project_path = self.get_project_path()
        if project_path:
            for dirpath, dirnames, filenames in os.walk(project_path):
                for filename in filenames:
                    if os.path.splitext(filename)[-1] != '.yml':
                        continue
                    playbook = os.path.join(dirpath, filename)
                    # Filter files that do not have either hosts or top-level
                    # includes. Use regex to allow files with invalid YAML to
                    # show up.
                    matched = False
                    try:
                        for line in file(playbook):
                            if valid_re.match(line):
                                matched = True
                    except IOError:
                        continue
                    if not matched:
                        continue
                    playbook = os.path.relpath(playbook, project_path)
                    # Filter files in a roles subdirectory.
                    if 'roles' in playbook.split(os.sep):
                        continue
                    # Filter files in a tasks subdirectory.
                    if 'tasks' in playbook.split(os.sep):
                        continue
                    results.append(playbook)
        return results

class ProjectUpdate(PrimordialModel):
    '''
    Internal job for tracking project updates from SCM.
    '''

    class Meta:
        app_label = 'main'

    project = models.ForeignKey(
        'Project',
        related_name='project_updates',
        on_delete=models.CASCADE,
        editable=False,
    )
    cancel_flag = models.BooleanField(
        blank=True,
        default=False,
        editable=False,
    )
    status = models.CharField(
        max_length=20,
        choices=JOB_STATUS_CHOICES,
        default='new',
        editable=False,
    )
    failed = models.BooleanField(
        default=False,
        editable=False,
    )
    job_args = models.TextField(
        blank=True,
        default='',
        editable=False,
    )
    job_cwd = models.CharField(
        max_length=1024,
        blank=True,
        default='',
        editable=False,
    )
    job_env = JSONField(
        blank=True,
        default={},
        editable=False,
    )
    result_stdout = models.TextField(
        blank=True,
        default='',
        editable=False,
    )
    result_traceback = models.TextField(
        blank=True,
        default='',
        editable=False,
    )
    celery_task_id = models.CharField(
        max_length=100,
        blank=True,
        default='',
        editable=False,
    )

    def __unicode__(self):
        return u'%s-%s-%s' % (self.created, self.id, self.status)

    def save(self, *args, **kwargs):
        # Get status before save...
        status_before = self.status or 'new'
        if self.pk:
            project_update_before = ProjectUpdate.objects.get(pk=self.pk)
            if project_update_before.status != self.status:
                status_before = project_update_before.status
        self.failed = bool(self.status in ('failed', 'error', 'canceled'))
        super(ProjectUpdate, self).save(*args, **kwargs)
        # If status changed, update project.
        if self.status != status_before:
            if self.status in ('pending', 'waiting', 'running'):
                project = self.project
                if project.current_update != self:
                    project.current_update = self
                    project.save(update_fields=['current_update'])
            elif self.status in ('successful', 'failed', 'error', 'canceled'):
                project = self.project
                if project.current_update == self:
                    project.current_update = None
                project.last_update = self
                project.last_update_failed = self.failed
                if not self.failed and project.scm_delete_on_next_update:
                    project.scm_delete_on_next_update = False
                project.save(update_fields=['current_update', 'last_update',
                                            'last_update_failed',
                                            'scm_delete_on_next_update'])

    def get_absolute_url(self):
        return reverse('main:project_update_detail', args=(self.pk,))

    @property
    def celery_task(self):
        try:
            if self.celery_task_id:
                return TaskMeta.objects.get(task_id=self.celery_task_id)
        except TaskMeta.DoesNotExist:
            pass

    @property
    def can_start(self):
        return bool(self.status == 'new')

    def start(self, **kwargs):
        from awx.main.tasks import RunProjectUpdate
        needed = self.project.scm_passwords_needed
        opts = dict([(field, kwargs.get(field, '')) for field in needed])
        if not all(opts.values()):
            return False
        self.status = 'pending'
        self.save(update_fields=['status'])
        task_result = RunProjectUpdate().delay(self.pk, **opts)
        # Reload project update from database so we don't clobber results
        # from RunProjectUpdate (mainly from tests when using Django 1.4.x).
        project_update = ProjectUpdate.objects.get(pk=self.pk)
        # The TaskMeta instance in the database isn't created until the worker
        # starts processing the task, so we can only store the task ID here.
        project_update.celery_task_id = task_result.task_id
        project_update.save(update_fields=['celery_task_id'])
        return True

    @property
    def can_cancel(self):
        return bool(self.status in ('pending', 'waiting', 'running'))

    def cancel(self):
        if self.can_cancel:
            if not self.cancel_flag:
                self.cancel_flag = True
                self.save(update_fields=['cancel_flag'])
        return self.cancel_flag

class Permission(CommonModelNameNotUnique):
    '''
    A permission allows a user, project, or team to be able to use an inventory source.
    '''

    class Meta:
        app_label = 'main'

    # permissions are granted to either a user or a team:
    user            = models.ForeignKey('auth.User', null=True, on_delete=SET_NULL, blank=True, related_name='permissions')
    team            = models.ForeignKey('Team', null=True, on_delete=SET_NULL, blank=True, related_name='permissions')

    # to be used against a project or inventory (or a project and inventory in conjunction):
    project         = models.ForeignKey('Project', null=True, on_delete=SET_NULL, blank=True, related_name='permissions')
    inventory       = models.ForeignKey('Inventory', null=True, on_delete=SET_NULL, related_name='permissions')

    # permission system explanation:
    #
    # for example, user A on inventory X has write permissions                 (PERM_INVENTORY_WRITE)
    #              team C on inventory X has read permissions                  (PERM_INVENTORY_READ)
    #              team C on inventory X and project Y has launch permissions  (PERM_INVENTORY_DEPLOY)
    #              team C on inventory X and project Z has dry run permissions (PERM_INVENTORY_CHECK)
    #
    # basically for launching, permissions can be awarded to the whole inventory source or just the inventory source
    # in context of a given project.
    #
    # the project parameter is not used when dealing with READ, WRITE, or ADMIN permissions.

    permission_type = models.CharField(max_length=64, choices=PERMISSION_TYPE_CHOICES)

    def __unicode__(self):
        return unicode("Permission(name=%s,ON(user=%s,team=%s),FOR(project=%s,inventory=%s,type=%s))" % (
            self.name,
            self.user,
            self.team,
            self.project,
            self.inventory,
            self.permission_type
        ))

    def get_absolute_url(self):
        return reverse('main:permission_detail', args=(self.pk,))

# TODO: other job types (later)

class JobTemplate(CommonModel):
    '''
    A job template is a reusable job definition for applying a project (with
    playbook) to an inventory source with a given credential.
    '''

    class Meta:
        app_label = 'main'

    job_type = models.CharField(
        max_length=64,
        choices=JOB_TYPE_CHOICES,
    )
    inventory = models.ForeignKey(
        'Inventory',
        related_name='job_templates',
        null=True,
        on_delete=models.SET_NULL,
    )
    project = models.ForeignKey(
        'Project',
        related_name='job_templates',
        null=True,
        on_delete=models.SET_NULL,
    )
    playbook = models.CharField(
        max_length=1024,
        default='',
    )
    credential = models.ForeignKey(
        'Credential',
        related_name='job_templates',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    )
    forks = models.PositiveIntegerField(
        blank=True,
        default=0,
    )
    limit = models.CharField(
        max_length=1024,
        blank=True,
        default='',
    )
    verbosity = models.PositiveIntegerField(
        blank=True,
        default=0,
    )
    extra_vars = models.TextField(
        blank=True,
        default='',
    )
    job_tags = models.CharField(
        max_length=1024,
        blank=True,
        default='',
    )
    host_config_key = models.CharField(
        max_length=1024,
        blank=True,
        default='',
    )

    def create_job(self, **kwargs):
        '''
        Create a new job based on this template.
        '''
        save_job = kwargs.pop('save', True)
        kwargs['job_template'] = self
        # Create new name with timestamp format to match jobs launched by the UI.
        new_name = '%s %s' % (self.name, now().strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
        new_name = new_name[:-4] + 'Z'
        kwargs.setdefault('name', new_name)
        kwargs.setdefault('description', self.description)
        kwargs.setdefault('job_type', self.job_type)
        kwargs.setdefault('inventory', self.inventory)
        kwargs.setdefault('project', self.project)
        kwargs.setdefault('playbook', self.playbook)
        kwargs.setdefault('credential', self.credential)
        kwargs.setdefault('forks', self.forks)
        kwargs.setdefault('limit', self.limit)
        kwargs.setdefault('verbosity', self.verbosity)
        kwargs.setdefault('extra_vars', self.extra_vars)
        kwargs.setdefault('job_tags', self.job_tags)
        job = Job(**kwargs)
        if save_job:
            job.save()
        return job

    def get_absolute_url(self):
        return reverse('main:job_template_detail', args=(self.pk,))

    def can_start_without_user_input(self):
        '''
        Return whether job template can be used to start a new job without
        requiring any user input.
        '''
        needed = []
        if self.credential:
            needed.extend(self.credential.passwords_needed)
        if self.project.scm_update_on_launch:
            needed.extend(self.project.scm_passwords_needed)
        for inventory_source in self.inventory.inventory_sources.filter(active=True, update_on_launch=True):
            for pw in inventory_source.source_passwords_needed:
                if pw not in needed:
                    needed.append(pw)
        return bool(self.credential and not len(needed))

class Job(CommonModelNameNotUnique):
    '''
    A job applies a project (with playbook) to an inventory source with a given
    credential.  It represents a single invocation of ansible-playbook with the
    given parameters.
    '''

    LAUNCH_TYPE_CHOICES = [
        ('manual', _('Manual')),
        ('callback', _('Callback')),
        ('scheduled', _('Scheduled')),
    ]

    class Meta:
        app_label = 'main'

    job_template = models.ForeignKey(
        'JobTemplate',
        related_name='jobs',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    )
    job_type = models.CharField(
        max_length=64,
        choices=JOB_TYPE_CHOICES,
    )
    inventory = models.ForeignKey(
        'Inventory',
        related_name='jobs',
        null=True,
        on_delete=models.SET_NULL,
    )
    credential = models.ForeignKey(
        'Credential',
        related_name='jobs',
        null=True,
        on_delete=models.SET_NULL,
    )
    project = models.ForeignKey(
        'Project',
        related_name='jobs',
        null=True,
        on_delete=models.SET_NULL,
    )
    playbook = models.CharField(
        max_length=1024,
    )
    forks = models.PositiveIntegerField(
        blank=True,
        default=0,
    )
    limit = models.CharField(
        max_length=1024,
        blank=True,
        default='',
    )
    verbosity = models.PositiveIntegerField(
        blank=True,
        default=0,
    )
    extra_vars = models.TextField(
        blank=True,
        default='',
    )
    job_tags = models.CharField(
        max_length=1024,
        blank=True,
        default='',
    )
    cancel_flag = models.BooleanField(
        blank=True,
        default=False,
        editable=False,
    )
    launch_type = models.CharField(
        max_length=20,
        choices=LAUNCH_TYPE_CHOICES,
        default='manual',
        editable=False,
    )
    status = models.CharField(
        max_length=20,
        choices=JOB_STATUS_CHOICES,
        default='new',
        editable=False,
    )
    failed = models.BooleanField(
        default=False,
        editable=False,
    )
    job_args = models.TextField(
        blank=True,
        default='',
        editable=False,
    )
    job_cwd = models.CharField(
        max_length=1024,
        blank=True,
        default='',
        editable=False,
    )
    job_env = JSONField(
        blank=True,
        default={},
        editable=False,
    )
    result_stdout = models.TextField(
        blank=True,
        default='',
        editable=False,
    )
    result_traceback = models.TextField(
        blank=True,
        default='',
        editable=False,
    )
    celery_task_id = models.CharField(
        max_length=100,
        blank=True,
        default='',
        editable=False,
    )
    hosts = models.ManyToManyField(
        'Host',
        related_name='jobs',
        blank=True,
        editable=False,
        through='JobHostSummary',
    )

    def get_absolute_url(self):
        return reverse('main:job_detail', args=(self.pk,))

    def __unicode__(self):
        return u'%s-%s-%s' % (self.name, self.id, self.status)

    def save(self, *args, **kwargs):
        self.failed = bool(self.status in ('failed', 'error', 'canceled'))
        super(Job, self).save(*args, **kwargs)

    @property
    def extra_vars_dict(self):
        '''Return extra_vars as a dictionary.'''
        extra_vars = self.extra_vars.encode('utf-8')
        try:
            return json.loads(extra_vars.strip() or '{}')
        except ValueError:
            pass
        try:
            return yaml.safe_load(extra_vars)
        except yaml.YAMLError:
            pass
        d = {}
        for kv in [x.decode('utf-8') for x in shlex.split(extra_vars, posix=True)]:
            if '=' in kv:
                k, v = kv.split('=', 1)
                d[k] = v
        return d

    @property
    def celery_task(self):
        try:
            if self.celery_task_id:
                return TaskMeta.objects.get(task_id=self.celery_task_id)
        except TaskMeta.DoesNotExist:
            pass

    @property
    def task_auth_token(self):
        '''Return temporary auth token used for task requests via API.'''
        if self.status == 'running':
            h = hmac.new(settings.SECRET_KEY, self.created.isoformat())
            return '%d-%s' % (self.pk, h.hexdigest())

    @property
    def passwords_needed_to_start(self):
        '''Return list of password field names needed to start the job.'''
        needed = []
        if self.credential:
            needed.extend(self.credential.passwords_needed)
        if self.project.scm_update_on_launch:
            needed.extend(self.project.scm_passwords_needed)
        for inventory_source in self.inventory.inventory_sources.filter(active=True, update_on_launch=True):
            for pw in inventory_source.source_passwords_needed:
                if pw not in needed:
                    needed.append(pw)
        return needed

    @property
    def can_start(self):
        return bool(self.status == 'new')

    def start(self, **kwargs):
        from awx.main.tasks import RunJob
        if not self.can_start:
            return False
        needed = self.passwords_needed_to_start
        opts = dict([(field, kwargs.get(field, '')) for field in needed])
        if not all(opts.values()):
            return False
        self.status = 'pending'
        self.save(update_fields=['status'])
        task_result = RunJob().delay(self.pk, **opts)
        # Reload job from database so we don't clobber results from RunJob
        # (mainly from tests when using Django 1.4.x).
        job = Job.objects.get(pk=self.pk)
        # The TaskMeta instance in the database isn't created until the worker
        # starts processing the task, so we can only store the task ID here.
        job.celery_task_id = task_result.task_id
        job.save(update_fields=['celery_task_id'])
        return True

    @property
    def can_cancel(self):
        return bool(self.status in ('pending', 'waiting', 'running'))

    def cancel(self):
        if self.can_cancel:
            if not self.cancel_flag:
                self.cancel_flag = True
                self.save(update_fields=['cancel_flag'])
        return self.cancel_flag

    @property
    def successful_hosts(self):
        return Host.objects.filter(job_host_summaries__job__pk=self.pk,
                                   job_host_summaries__ok__gt=0)

    @property
    def failed_hosts(self):
        return Host.objects.filter(job_host_summaries__job__pk=self.pk,
                                   job_host_summaries__failures__gt=0)

    @property
    def changed_hosts(self):
        return Host.objects.filter(job_host_summaries__job__pk=self.pk,
                                   job_host_summaries__changed__gt=0)

    @property
    def dark_hosts(self):
        return Host.objects.filter(job_host_summaries__job__pk=self.pk,
                                   job_host_summaries__dark__gt=0)

    @property
    def unreachable_hosts(self):
        return self.dark_hosts

    @property
    def skipped_hosts(self):
        return Host.objects.filter(job_host_summaries__job__pk=self.pk,
                                   job_host_summaries__skipped__gt=0)

    @property
    def processed_hosts(self):
        return Host.objects.filter(job_host_summaries__job__pk=self.pk,
                                   job_host_summaries__processed__gt=0)

class JobHostSummary(models.Model):
    '''
    Per-host statistics for each job.
    '''

    class Meta:
        unique_together = [('job', 'host')]
        verbose_name_plural = _('job host summaries')
        ordering = ('-pk',)

    job = models.ForeignKey(
        'Job',
        related_name='job_host_summaries',
        on_delete=models.CASCADE,
        editable=False,
    )
    host = models.ForeignKey('Host',
        related_name='job_host_summaries',
        on_delete=models.CASCADE,
        editable=False,
    )
    created = models.DateTimeField(
        auto_now_add=True,
        default=now,
    )
    modified = models.DateTimeField(
        auto_now=True,
        default=now,
    )

    changed = models.PositiveIntegerField(default=0, editable=False)
    dark = models.PositiveIntegerField(default=0, editable=False)
    failures = models.PositiveIntegerField(default=0, editable=False)
    ok = models.PositiveIntegerField(default=0, editable=False)
    processed = models.PositiveIntegerField(default=0, editable=False)
    skipped = models.PositiveIntegerField(default=0, editable=False)
    failed = models.BooleanField(default=False, editable=False)

    def __unicode__(self):
        return '%s changed=%d dark=%d failures=%d ok=%d processed=%d skipped=%s' % \
            (self.host.name, self.changed, self.dark, self.failures, self.ok,
             self.processed, self.skipped)

    def get_absolute_url(self):
        return reverse('main:job_host_summary_detail', args=(self.pk,))

    def save(self, *args, **kwargs):
        self.failed = bool(self.dark or self.failures)
        super(JobHostSummary, self).save(*args, **kwargs)
        self.update_host_last_job_summary()

    def update_host_last_job_summary(self):
        update_fields = []
        if self.host.last_job != self.job:
            self.host.last_job = self.job
            update_fields.append('last_job')
        if self.host.last_job_host_summary != self:
            self.host.last_job_host_summary = self
            update_fields.append('last_job_host_summary')
        if update_fields:
            self.host.save(update_fields=update_fields)
        self.host.update_computed_fields()

class JobEvent(models.Model):
    '''
    An event/message logged from the callback when running a job.
    '''

    # Playbook events will be structured to form the following hierarchy:
    # - playbook_on_start (once for each playbook file)
    #   - playbook_on_vars_prompt (for each play, but before play starts, we
    #     currently don't handle responding to these prompts)
    #   - playbook_on_play_start
    #     - playbook_on_import_for_host
    #     - playbook_on_not_import_for_host
    #     - playbook_on_no_hosts_matched
    #     - playbook_on_no_hosts_remaining
    #     - playbook_on_setup
    #       - runner_on*
    #     - playbook_on_task_start
    #       - runner_on_failed
    #       - runner_on_ok
    #       - runner_on_error
    #       - runner_on_skipped
    #       - runner_on_unreachable
    #       - runner_on_no_hosts
    #       - runner_on_async_poll
    #       - runner_on_async_ok
    #       - runner_on_async_failed
    #       - runner_on_file_diff
    #     - playbook_on_notify
    #   - playbook_on_stats

    EVENT_TYPES = [
        # (level, event, verbose name, failed)
        (3, 'runner_on_failed', _('Host Failed'), True),
        (3, 'runner_on_ok', _('Host OK'), False),
        (3, 'runner_on_error', _('Host Failure'), True),
        (3, 'runner_on_skipped', _('Host Skipped'), False),
        (3, 'runner_on_unreachable', _('Host Unreachable'), True),
        (3, 'runner_on_no_hosts', _('No Hosts Remaining'), False),
        (3, 'runner_on_async_poll', _('Host Polling'), False),
        (3, 'runner_on_async_ok', _('Host Async OK'), False),
        (3, 'runner_on_async_failed', _('Host Async Failure'), True),
        # AWX does not yet support --diff mode
        (3, 'runner_on_file_diff', _('File Difference'), False),
        (0, 'playbook_on_start', _('Playbook Started'), False),
        (2, 'playbook_on_notify', _('Running Handlers'), False),
        (2, 'playbook_on_no_hosts_matched', _('No Hosts Matched'), False),
        (2, 'playbook_on_no_hosts_remaining', _('No Hosts Remaining'), False),
        (2, 'playbook_on_task_start', _('Task Started'), False),
        # AWX does not yet support vars_prompt (and will probably hang :)
        (1, 'playbook_on_vars_prompt', _('Variables Prompted'), False),
        (2, 'playbook_on_setup', _('Gathering Facts'), False),
        # callback will not record this
        (2, 'playbook_on_import_for_host', _('internal: on Import for Host'), False),
        # callback will not record this
        (2, 'playbook_on_not_import_for_host', _('internal: on Not Import for Host'), False),
        (1, 'playbook_on_play_start', _('Play Started'), False),
        (1, 'playbook_on_stats', _('Playbook Complete'), False),
    ]
    FAILED_EVENTS = [x[1] for x in EVENT_TYPES if x[3]]
    EVENT_CHOICES = [(x[1], x[2]) for x in EVENT_TYPES]
    LEVEL_FOR_EVENT = dict([(x[1], x[0]) for x in EVENT_TYPES])

    class Meta:
        app_label = 'main'
        ordering = ('pk',)

    job = models.ForeignKey(
        'Job',
        related_name='job_events',
        on_delete=models.CASCADE,
        editable=False,
    )
    created = models.DateTimeField(
        auto_now_add=True,
        default=now,
    )
    modified = models.DateTimeField(
        auto_now=True,
        default=now,
    )
    event = models.CharField(
        max_length=100,
        choices=EVENT_CHOICES,
    )
    event_data = JSONField(
        blank=True,
        default={},
    )
    failed = models.BooleanField(
        default=False,
        editable=False,
    )
    changed = models.BooleanField(
        default=False,
        editable=False,
    )
    host = models.ForeignKey(
        'Host',
        related_name='job_events_as_primary_host',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
        editable=False,
    )
    hosts = models.ManyToManyField(
        'Host',
        related_name='job_events',
        blank=True,
        editable=False,
    )
    play = models.CharField(
        max_length=1024,
        blank=True,
        default='',
        editable=False,
    )
    task = models.CharField(
        max_length=1024,
        blank=True,
        default='',
        editable=False,
    )
    parent = models.ForeignKey(
        'self',
        related_name='children',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
        editable=False,
    )

    def get_absolute_url(self):
        return reverse('main:job_event_detail', args=(self.pk,))

    def __unicode__(self):
        return u'%s @ %s' % (self.get_event_display(), self.created.isoformat())

    @property
    def event_level(self):
        return self.LEVEL_FOR_EVENT.get(self.event, 0)

    def get_event_display2(self):
        msg = self.get_event_display()
        if self.event == 'playbook_on_play_start':
            if self.play is not None:
                msg = "%s (%s)" % (msg, self.play)
        elif self.event == 'playbook_on_task_start':
            if self.task is not None:
                msg = "%s (%s)" % (msg, self.task)

        # Change display for runner events trigged by async polling.  Some of
        # these events may not show in most cases, due to filterting them out
        # of the job event queryset returned to the user.
        res = self.event_data.get('res', {})
        # Fix for existing records before we had added the workaround on save
        # to change async_ok to async_failed.
        if self.event == 'runner_on_async_ok':
            try:
                if res.get('failed', False) or res.get('rc', 0) != 0:
                    msg = 'Host Async Failed'
            except (AttributeError, TypeError):
                pass
        # Runner events with ansible_job_id are part of async starting/polling.
        if self.event in ('runner_on_ok', 'runner_on_failed'):
            try:
                module_name = res['invocation']['module_name']
                job_id = res['ansible_job_id']
            except (TypeError, KeyError, AttributeError):
                module_name = None
                job_id = None
            if module_name and job_id:
                if module_name == 'async_status':
                    msg = 'Host Async Checking'
                else:
                    msg = 'Host Async Started'
        # Handle both 1.2 on_failed and 1.3+ on_async_failed events when an
        # async task times out.
        if self.event in ('runner_on_failed', 'runner_on_async_failed'):
            try:
                if res['msg'] == 'timed out':
                    msg = 'Host Async Timeout'
            except (TypeError, KeyError, AttributeError):
                pass
        return msg

    def _find_parent(self):
        parent_events = set()
        if self.event in ('playbook_on_play_start', 'playbook_on_stats',
                          'playbook_on_vars_prompt'):
            parent_events.add('playbook_on_start')
        elif self.event in ('playbook_on_notify', 'playbook_on_setup',
                            'playbook_on_task_start',
                            'playbook_on_no_hosts_matched',
                            'playbook_on_no_hosts_remaining',
                            'playbook_on_import_for_host',
                            'playbook_on_not_import_for_host'):
            parent_events.add('playbook_on_play_start')
        elif self.event.startswith('runner_on_'):
            parent_events.add('playbook_on_setup')
            parent_events.add('playbook_on_task_start')
        if parent_events:
            try:
                qs = self.job.job_events.all()
                if self.pk:
                    qs = qs.filter(pk__lt=self.pk, event__in=parent_events)
                else:
                    qs = qs.filter(event__in=parent_events)
                return qs.order_by('-pk')[0]
            except IndexError:
                pass
        return None

    def save(self, *args, **kwargs):
        res = self.event_data.get('res', None)
        # Workaround for Ansible 1.2, where the runner_on_async_ok event is
        # created even when the async task failed. Change the event to be
        # correct.
        if self.event == 'runner_on_async_ok':
            try:
                if res.get('failed', False) or res.get('rc', 0) != 0:
                    self.event = 'runner_on_async_failed'
            except (AttributeError, TypeError):
                pass
        if self.event in self.FAILED_EVENTS:
            if not self.event_data.get('ignore_errors', False):
                self.failed = True
        if isinstance(res, dict) and res.get('changed', False):
            self.changed = True
        if self.event == 'playbook_on_stats':
            try:
                failures_dict = self.event_data.get('failures', {})
                dark_dict = self.event_data.get('dark', {})
                self.failed = bool(sum(failures_dict.values()) + 
                                   sum(dark_dict.values()))
                changed_dict = self.event_data.get('changed', {})
                self.changed = bool(sum(changed_dict.values()))
            except (AttributeError, TypeError):
                pass
        try:
            if not self.host and self.event_data.get('host', ''):
                self.host = self.job.inventory.hosts.get(name=self.event_data['host'])
        except (Host.DoesNotExist, AttributeError):
            pass
        self.play = self.event_data.get('play', '')
        self.task = self.event_data.get('task', '')
        self.parent = self._find_parent()
        super(JobEvent, self).save(*args, **kwargs)
        self.update_parent_failed_and_changed()
        self.update_hosts()
        self.update_host_summary_from_stats()

    def update_parent_failed_and_changed(self):
        # Propagage failed and changed flags to parent events.
        if self.parent:
            parent = self.parent
            save_parent = False
            if self.failed and not parent.failed:
                parent.failed = True
                save_parent = True
            if self.changed and not parent.changed:
                parent.changed = True
                save_parent = True
            if save_parent:
                parent.save()
                parent.update_parent_failed_and_changed()

    def update_hosts(self, extra_hosts=None):
        extra_hosts = extra_hosts or []
        hostnames = set()
        if self.event_data.get('host', ''):
            hostnames.add(self.event_data['host'])
        if self.event == 'playbook_on_stats':
            try:
                for v in self.event_data.values():
                    hostnames.update(v.keys())
            except AttributeError: # In case event_data or v isn't a dict.
                pass
        for hostname in hostnames:
            try:
                host = self.job.inventory.hosts.get(name=hostname)
            except Host.DoesNotExist:
                continue
            self.hosts.add(host)
        for host in extra_hosts:
            self.hosts.add(host)
        if self.parent:
            self.parent.update_hosts(self.hosts.all())

    def update_host_summary_from_stats(self):
        if self.event != 'playbook_on_stats':
            return
        hostnames = set()
        try:
            for v in self.event_data.values():
                hostnames.update(v.keys())
        except AttributeError: # In case event_data or v isn't a dict.
            pass
        for hostname in hostnames:
            try:
                host = self.job.inventory.hosts.get(name=hostname)
            except Host.DoesNotExist:
                continue
            host_summary = self.job.job_host_summaries.get_or_create(host=host)[0]
            host_summary_changed = False
            for stat in ('changed', 'dark', 'failures', 'ok', 'processed', 'skipped'):
                try:
                    value = self.event_data.get(stat, {}).get(hostname, 0)
                    if getattr(host_summary, stat) != value:
                        setattr(host_summary, stat, value)
                        host_summary_changed = True
                except AttributeError: # in case event_data[stat] isn't a dict.
                    pass
            if host_summary_changed:
                host_summary.save()

class Profile(models.Model):
    '''
    Profile model related to User object. Currently stores LDAP DN for users
    loaded from LDAP.
    '''

    created = models.DateTimeField(
        auto_now_add=True,
    )
    modified = models.DateTimeField(
        auto_now=True,
    )
    user = AutoOneToOneField(
        'auth.User',
        related_name='profile',
        editable=False,
    )
    ldap_dn = models.CharField(
        max_length=1024,
        default='',
    )

class AuthToken(models.Model):
    '''
    Custom authentication tokens per user with expiration and request-specific
    data.
    '''
    
    key = models.CharField(max_length=40, primary_key=True)
    user = models.ForeignKey('auth.User', related_name='auth_tokens',
                             on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    expires = models.DateTimeField(default=now)
    request_hash = models.CharField(max_length=40, blank=True, default='')

    @classmethod
    def get_request_hash(cls, request):
        h = hashlib.sha1()
        h.update(settings.SECRET_KEY)
        for header in settings.REMOTE_HOST_HEADERS:
            value = request.META.get(header, '').strip()
            if value:
                h.update(value)
        h.update(request.META.get('HTTP_USER_AGENT', ''))
        return h.hexdigest()

    def save(self, *args, **kwargs):
        if not self.pk:
            self.refresh(save=False)
        if not self.key:
            self.key = self.generate_key()
        return super(AuthToken, self).save(*args, **kwargs)

    def refresh(self, save=True):
        if not self.pk or not self.expired:
            self.expires = now() + datetime.timedelta(seconds=settings.AUTH_TOKEN_EXPIRATION)
            if save:
                self.save()

    def invalidate(self, save=True):
        if not self.expired:
            self.expires = now() - datetime.timedelta(seconds=1)
            if save:
                self.save()

    def generate_key(self):
        unique = uuid.uuid4()
        return hmac.new(unique.bytes, digestmod=hashlib.sha1).hexdigest()

    @property
    def expired(self):
        return bool(self.expires < now())

    def __unicode__(self):
        return self.key

# TODO: reporting (MPD)

# Add mark_inactive method to User model.
def user_mark_inactive(user, save=True):
    '''Use instead of delete to rename and mark users inactive.'''
    if user.is_active:
        # Set timestamp to datetime.isoformat() but without the time zone
        # offse to stay withint the 30 character username limit.
        deleted_ts = now().strftime('%Y-%m-%dT%H:%M:%S.%f')
        user.username = '_d_%s' % deleted_ts
        user.is_active = False
        if save:
            user.save()
User.add_to_class('mark_inactive', user_mark_inactive)

# Add custom methods to User model for permissions checks.
from awx.main.access import *
User.add_to_class('get_queryset', get_user_queryset)
User.add_to_class('can_access', check_user_access)

# Monkeypatch Django serializer to ignore django-taggit fields (which break
# the dumpdata command; see https://github.com/alex/django-taggit/issues/155).
from django.core.serializers.python import Serializer as _PythonSerializer
_original_handle_m2m_field = _PythonSerializer.handle_m2m_field
def _new_handle_m2m_field(self, obj, field):
    try:
        field.rel.through._meta
    except AttributeError:
        return
    return _original_handle_m2m_field(self, obj, field)
_PythonSerializer.handle_m2m_field = _new_handle_m2m_field

# Import signal handlers only after models have been defined.
import awx.main.signals
