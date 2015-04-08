# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import hmac
import json
import logging

# Django
from django.conf import settings
from django.db import models
from django.utils.text import Truncator
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse

# Django-JSONField
from jsonfield import JSONField

# AWX
from awx.main.models.base import * # noqa
from awx.main.models.unified_jobs import * # noqa
from awx.main.utils import decrypt_field

logger = logging.getLogger('awx.main.models.ad_hoc_commands')

__all__ = ['AdHocCommand', 'AdHocCommandEvent']


class AdHocCommand(UnifiedJob):

    MODULE_NAME_CHOICES = [(x,x) for x in settings.AD_HOC_COMMANDS]

    class Meta(object):
        app_label = 'main'

    job_type = models.CharField(
        max_length=64,
        choices=JOB_TYPE_CHOICES,
        default='run',
    )
    inventory = models.ForeignKey(
        'Inventory',
        related_name='ad_hoc_commands',
        null=True,
        on_delete=models.SET_NULL,
    )
    limit = models.CharField(
        max_length=1024,
        blank=True,
        default='',
    )
    credential = models.ForeignKey(
        'Credential',
        related_name='ad_hoc_commands',
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    )
    module_name = models.CharField(
        max_length=1024,
        default='command',
        choices=MODULE_NAME_CHOICES,
        blank=True, # If blank, defaults to 'command'.
    )
    module_args = models.TextField(
        blank=True,
        default='',
    )
    forks = models.PositiveIntegerField(
        blank=True,
        default=0,
    )
    verbosity = models.PositiveIntegerField(
        blank=True,
        default=0,
    )
    become_enabled = models.BooleanField(
        default=False,
    )
    hosts = models.ManyToManyField(
        'Host',
        related_name='ad_hoc_commands',
        editable=False,
        through='AdHocCommandEvent',
    )

    def clean_credential(self):
        cred = self.credential
        if cred and cred.kind != 'ssh':
            raise ValidationError(
                'You must provide a machine / SSH credential.',
            )
        return cred

    def clean_limit(self):
        # FIXME: Future feature - check if no hosts would match and reject the
        # command, instead of having to run it to find out.
        return self.limit

    def clean_module_name(self):
        module_name = self.module_name.strip() or 'command'
        if module_name not in settings.AD_HOC_COMMANDS:
            raise ValidationError('Unsupported module for ad hoc commands.')
        return module_name

    def clean_module_args(self):
        module_args = self.module_args
        if self.module_name in ('command', 'shell') and not module_args:
            raise ValidationError('No argument passed to %s module.' % self.module_name)
        return module_args

    @property
    def passwords_needed_to_start(self):
        '''Return list of password field names needed to start the job.'''
        if self.credential:
            return self.credential.passwords_needed
        else:
            return []

    @classmethod
    def _get_parent_field_name(cls):
        return ''

    @classmethod
    def _get_task_class(cls):
        from awx.main.tasks import RunAdHocCommand
        return RunAdHocCommand

    def get_absolute_url(self):
        return reverse('api:ad_hoc_command_detail', args=(self.pk,))

    @property
    def task_auth_token(self):
        '''Return temporary auth token used for task requests via API.'''
        if self.status == 'running':
            h = hmac.new(settings.SECRET_KEY, self.created.isoformat())
            return '%d-%s' % (self.pk, h.hexdigest())

    def get_passwords_needed_to_start(self):
        return self.passwords_needed_to_start

    def is_blocked_by(self, obj):
        from awx.main.models import InventoryUpdate
        if type(obj) == InventoryUpdate:
            if self.inventory == obj.inventory_source.inventory:
                return True
        return False

    @property
    def task_impact(self):
        # NOTE: We sorta have to assume the host count matches and that forks default to 5
        from awx.main.models.inventory import Host
        count_hosts = Host.objects.filter(active=True, enabled=True, inventory__ad_hoc_commands__pk=self.pk).count()
        return min(count_hosts, 5 if self.forks == 0 else self.forks) * 10

    def generate_dependencies(self, active_tasks):
        from awx.main.models import InventoryUpdate
        if not self.inventory:
            return []
        inventory_sources = self.inventory.inventory_sources.filter(active=True, update_on_launch=True)
        inventory_sources_found = []
        dependencies = []
        for obj in active_tasks:
            if type(obj) == InventoryUpdate:
                if obj.inventory_source in inventory_sources:
                    inventory_sources_found.append(obj.inventory_source)
        # Skip updating any inventory sources that were already updated before
        # running this job (via callback inventory refresh).
        try:
            start_args = json.loads(decrypt_field(self, 'start_args'))
        except Exception:
            start_args = None
        start_args = start_args or {}
        inventory_sources_already_updated = start_args.get('inventory_sources_already_updated', [])
        if inventory_sources_already_updated:
            for source in inventory_sources.filter(pk__in=inventory_sources_already_updated):
                if source not in inventory_sources_found:
                    inventory_sources_found.append(source)
        if inventory_sources.count(): # and not has_setup_failures?  Probably handled as an error scenario in the task runner
            for source in inventory_sources:
                if source not in inventory_sources_found and source.needs_update_on_launch:
                    dependencies.append(source.create_inventory_update(launch_type='dependency'))
        return dependencies

    def copy(self):
        data = {}
        for field in ('job_type', 'inventory_id', 'limit', 'credential_id',
                      'module_name', 'module_args', 'forks', 'verbosity',
                      'become_enabled'):
            data[field] = getattr(self, field)
        return AdHocCommand.objects.create(**data)

    def save(self, *args, **kwargs):
        update_fields = kwargs.get('update_fields', [])
        if not self.name:
            self.name = Truncator(u': '.join(filter(None, (self.module_name, self.module_args)))).chars(512)
            if 'name' not in update_fields:
                update_fields.append('name')
        super(AdHocCommand, self).save(*args, **kwargs)


class AdHocCommandEvent(CreatedModifiedModel):
    '''
    An event/message logged from the ad hoc event callback for each host.
    '''

    EVENT_TYPES = [
        # (event, verbose name, failed)
        ('runner_on_failed', _('Host Failed'), True),
        ('runner_on_ok', _('Host OK'), False),
        ('runner_on_unreachable', _('Host Unreachable'), True),
        # Tower won't see no_hosts (check is done earlier without callback).
        #('runner_on_no_hosts', _('No Hosts Matched'), False),
        # Tower should probably never see skipped (no conditionals).
        #('runner_on_skipped', _('Host Skipped'), False),
        # Tower does not support async for ad hoc commands.
        #('runner_on_async_poll', _('Host Polling'), False),
        #('runner_on_async_ok', _('Host Async OK'), False),
        #('runner_on_async_failed', _('Host Async Failure'), True),
        # Tower does not yet support --diff mode
        #('runner_on_file_diff', _('File Difference'), False),
    ]
    FAILED_EVENTS = [x[0] for x in EVENT_TYPES if x[2]]
    EVENT_CHOICES = [(x[0], x[1]) for x in EVENT_TYPES]

    class Meta:
        app_label = 'main'
        unique_together = [('ad_hoc_command', 'host_name')]
        ordering = ('-pk',)

    ad_hoc_command = models.ForeignKey(
        'AdHocCommand',
        related_name='ad_hoc_command_events',
        on_delete=models.CASCADE,
        editable=False,
    )
    host = models.ForeignKey(
        'Host',
        related_name='ad_hoc_command_events',
        null=True,
        default=None,
        on_delete=models.SET_NULL,
        editable=False,
    )
    host_name = models.CharField(
        max_length=1024,
        default='',
        editable=False,
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
    counter = models.PositiveIntegerField(
        default=0,
    )

    def get_absolute_url(self):
        return reverse('api:ad_hoc_command_event_detail', args=(self.pk,))

    def __unicode__(self):
        return u'%s @ %s' % (self.get_event_display(), self.created.isoformat())

    def save(self, *args, **kwargs):
        from awx.main.models.inventory import Host
        # If update_fields has been specified, add our field names to it,
        # if it hasn't been specified, then we're just doing a normal save.
        update_fields = kwargs.get('update_fields', [])
        res = self.event_data.get('res', None)
        if self.event in self.FAILED_EVENTS:
            if not self.event_data.get('ignore_errors', False):
                self.failed = True
                if 'failed' not in update_fields:
                    update_fields.append('failed')
        if isinstance(res, dict) and res.get('changed', False):
            self.changed = True
            if 'changed' not in update_fields:
                update_fields.append('changed')
        self.host_name = self.event_data.get('host', '').strip()
        if 'host_name' not in update_fields:
            update_fields.append('host_name')
        try:
            if not self.host_id and self.host_name:
                host_qs = Host.objects.filter(inventory__ad_hoc_commands__id=self.ad_hoc_command_id, name=self.host_name)
                host_id = host_qs.only('id').values_list('id', flat=True)
                if host_id.exists():
                    self.host_id = host_id[0]
                    if 'host_id' not in update_fields:
                        update_fields.append('host_id')
        except (IndexError, AttributeError):
            pass
        super(AdHocCommandEvent, self).save(*args, **kwargs)
