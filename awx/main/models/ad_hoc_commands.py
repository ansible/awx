# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import datetime
import hashlib
import hmac
import logging
from urlparse import urljoin

# Django
from django.conf import settings
from django.db import models
from django.utils.dateparse import parse_datetime
from django.utils.text import Truncator
from django.utils.timezone import utc
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError

# AWX
from awx.api.versioning import reverse
from awx.main.models.base import * # noqa
from awx.main.models.unified_jobs import * # noqa
from awx.main.models.notifications import JobNotificationMixin, NotificationTemplate
from awx.main.fields import JSONField

logger = logging.getLogger('awx.main.models.ad_hoc_commands')

__all__ = ['AdHocCommand', 'AdHocCommandEvent']


class AdHocCommand(UnifiedJob, JobNotificationMixin):

    class Meta(object):
        app_label = 'main'

    diff_mode = models.BooleanField(
        default=False,
    )
    job_type = models.CharField(
        max_length=64,
        choices=AD_HOC_JOB_TYPE_CHOICES,
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
        default='',
        blank=True,
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
        choices=VERBOSITY_CHOICES,
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
    extra_vars = prevent_search(models.TextField(
        blank=True,
        default='',
    ))

    extra_vars_dict = VarsDictProperty('extra_vars', True)

    def clean_inventory(self):
        inv = self.inventory
        if not inv:
            raise ValidationError(_('No valid inventory.'))
        return inv

    def clean_credential(self):
        cred = self.credential
        if cred and cred.kind != 'ssh':
            raise ValidationError(
                _('You must provide a machine / SSH credential.'),
            )
        return cred

    def clean_limit(self):
        # FIXME: Future feature - check if no hosts would match and reject the
        # command, instead of having to run it to find out.
        return self.limit

    def clean_module_name(self):
        if type(self.module_name) not in (str, unicode):
            raise ValidationError(_("Invalid type for ad hoc command"))
        module_name = self.module_name.strip() or 'command'
        if module_name not in settings.AD_HOC_COMMANDS:
            raise ValidationError(_('Unsupported module for ad hoc commands.'))
        return module_name

    def clean_module_args(self):
        if type(self.module_args) not in (str, unicode):
            raise ValidationError(_("Invalid type for ad hoc command"))
        module_args = self.module_args
        if self.module_name in ('command', 'shell') and not module_args:
            raise ValidationError(_('No argument passed to %s module.') % self.module_name)
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

    @classmethod
    def supports_isolation(cls):
        return True

    def get_absolute_url(self, request=None):
        return reverse('api:ad_hoc_command_detail', kwargs={'pk': self.pk}, request=request)

    def get_ui_url(self):
        return urljoin(settings.TOWER_URL_BASE, "/#/ad_hoc_commands/{}".format(self.pk))

    @property
    def task_auth_token(self):
        '''Return temporary auth token used for task requests via API.'''
        if self.status == 'running':
            h = hmac.new(settings.SECRET_KEY, self.created.isoformat(), digestmod=hashlib.sha1)
            return '%d-%s' % (self.pk, h.hexdigest())

    @property
    def notification_templates(self):
        all_orgs = set()
        for h in self.hosts.all():
            all_orgs.add(h.inventory.organization)
        active_templates = dict(error=set(),
                                success=set(),
                                any=set())
        base_notification_templates = NotificationTemplate.objects
        for org in all_orgs:
            for templ in base_notification_templates.filter(organization_notification_templates_for_errors=org):
                active_templates['error'].add(templ)
            for templ in base_notification_templates.filter(organization_notification_templates_for_success=org):
                active_templates['success'].add(templ)
            for templ in base_notification_templates.filter(organization_notification_templates_for_any=org):
                active_templates['any'].add(templ)
        active_templates['error'] = list(active_templates['error'])
        active_templates['any'] = list(active_templates['any'])
        active_templates['success'] = list(active_templates['success'])
        return active_templates

    def get_passwords_needed_to_start(self):
        return self.passwords_needed_to_start

    @property
    def task_impact(self):
        # NOTE: We sorta have to assume the host count matches and that forks default to 5
        from awx.main.models.inventory import Host
        count_hosts = Host.objects.filter( enabled=True, inventory__ad_hoc_commands__pk=self.pk).count()
        return min(count_hosts, 5 if self.forks == 0 else self.forks) * 10

    def copy(self):
        data = {}
        for field in ('job_type', 'inventory_id', 'limit', 'credential_id',
                      'module_name', 'module_args', 'forks', 'verbosity',
                      'extra_vars', 'become_enabled', 'diff_mode'):
            data[field] = getattr(self, field)
        return AdHocCommand.objects.create(**data)

    def save(self, *args, **kwargs):
        update_fields = kwargs.get('update_fields', [])
        if not self.name:
            self.name = Truncator(u': '.join(filter(None, (self.module_name, self.module_args)))).chars(512)
            if 'name' not in update_fields:
                update_fields.append('name')
        super(AdHocCommand, self).save(*args, **kwargs)

    @property
    def preferred_instance_groups(self):
        if self.inventory is not None and self.inventory.organization is not None:
            organization_groups = [x for x in self.inventory.organization.instance_groups.all()]
        else:
            organization_groups = []
        if self.inventory is not None:
            inventory_groups = [x for x in self.inventory.instance_groups.all()]
        else:
            inventory_groups = []
        selected_groups = inventory_groups + organization_groups
        if not selected_groups:
            return self.global_instance_groups
        return selected_groups

    '''
    JobNotificationMixin
    '''
    def get_notification_templates(self):
        return self.notification_templates

    def get_notification_friendly_name(self):
        return "AdHoc Command"


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
        # ('runner_on_no_hosts', _('No Hosts Matched'), False),
        # Tower will see skipped (when running in check mode for a module that
        # does not support check mode).
        ('runner_on_skipped', _('Host Skipped'), False),
        # Tower does not support async for ad hoc commands (not used in v2).
        # ('runner_on_async_poll', _('Host Polling'), False),
        # ('runner_on_async_ok', _('Host Async OK'), False),
        # ('runner_on_async_failed', _('Host Async Failure'), True),
        # Tower does not yet support --diff mode.
        # ('runner_on_file_diff', _('File Difference'), False),

        # Additional event types for captured stdout not directly related to
        # runner events.
        ('debug', _('Debug'), False),
        ('verbose', _('Verbose'), False),
        ('deprecated', _('Deprecated'), False),
        ('warning', _('Warning'), False),
        ('system_warning', _('System Warning'), False),
        ('error', _('Error'), False),
    ]
    FAILED_EVENTS = [x[0] for x in EVENT_TYPES if x[2]]
    EVENT_CHOICES = [(x[0], x[1]) for x in EVENT_TYPES]

    class Meta:
        app_label = 'main'
        ordering = ('-pk',)
        index_together = [
            ('ad_hoc_command', 'event'),
            ('ad_hoc_command', 'uuid'),
            ('ad_hoc_command', 'start_line'),
            ('ad_hoc_command', 'end_line'),
        ]

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
    uuid = models.CharField(
        max_length=1024,
        default='',
        editable=False,
    )
    counter = models.PositiveIntegerField(
        default=0,
        editable=False,
    )
    stdout = models.TextField(
        default='',
        editable=False,
    )
    verbosity = models.PositiveIntegerField(
        default=0,
        editable=False,
    )
    start_line = models.PositiveIntegerField(
        default=0,
        editable=False,
    )
    end_line = models.PositiveIntegerField(
        default=0,
        editable=False,
    )

    def get_absolute_url(self, request=None):
        return reverse('api:ad_hoc_command_event_detail', kwargs={'pk': self.pk}, request=request)

    def __unicode__(self):
        return u'%s @ %s' % (self.get_event_display(), self.created.isoformat())

    def save(self, *args, **kwargs):
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
        if not self.host_id and self.host_name:
            host_qs = self.ad_hoc_command.inventory.hosts.filter(name=self.host_name)
            try:
                host_id = host_qs.only('id').values_list('id', flat=True)
                if host_id.exists():
                    self.host_id = host_id[0]
                    if 'host_id' not in update_fields:
                        update_fields.append('host_id')
            except (IndexError, AttributeError):
                pass
        super(AdHocCommandEvent, self).save(*args, **kwargs)

    @classmethod
    def create_from_data(self, **kwargs):
        # Convert the datetime for the ad hoc command event's creation
        # appropriately, and include a time zone for it.
        #
        # In the event of any issue, throw it out, and Django will just save
        # the current time.
        try:
            if not isinstance(kwargs['created'], datetime.datetime):
                kwargs['created'] = parse_datetime(kwargs['created'])
            if not kwargs['created'].tzinfo:
                kwargs['created'] = kwargs['created'].replace(tzinfo=utc)
        except (KeyError, ValueError):
            kwargs.pop('created', None)

        # Sanity check: Don't honor keys that we don't recognize.
        valid_keys = {'ad_hoc_command_id', 'event', 'event_data', 'created',
                      'counter', 'uuid', 'stdout', 'start_line', 'end_line',
                      'verbosity'}
        for key in kwargs.keys():
            if key not in valid_keys:
                kwargs.pop(key)

        return AdHocCommandEvent.objects.create(**kwargs)
