# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import logging
from urllib.parse import urljoin

# Django
from django.conf import settings
from django.db import models
from django.utils.text import Truncator
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError

# AWX
from awx.api.versioning import reverse
from awx.main.models.base import (
    prevent_search, AD_HOC_JOB_TYPE_CHOICES, VERBOSITY_CHOICES, VarsDictProperty
)
from awx.main.models.events import AdHocCommandEvent
from awx.main.models.unified_jobs import UnifiedJob
from awx.main.models.notifications import JobNotificationMixin, NotificationTemplate

logger = logging.getLogger('awx.main.models.ad_hoc_commands')

__all__ = ['AdHocCommand']


class AdHocCommand(UnifiedJob, JobNotificationMixin):

    class Meta(object):
        app_label = 'main'
        ordering = ('id',)

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
    limit = models.TextField(
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
        if type(self.module_name) is not str:
            raise ValidationError(_("Invalid type for ad hoc command"))
        module_name = self.module_name.strip() or 'command'
        if module_name not in settings.AD_HOC_COMMANDS:
            raise ValidationError(_('Unsupported module for ad hoc commands.'))
        return module_name

    def clean_module_args(self):
        if type(self.module_args) is not str:
            raise ValidationError(_("Invalid type for ad hoc command"))
        module_args = self.module_args
        if self.module_name in ('command', 'shell') and not module_args:
            raise ValidationError(_('No argument passed to %s module.') % self.module_name)
        return module_args

    @property
    def event_class(self):
        return AdHocCommandEvent

    @property
    def passwords_needed_to_start(self):
        '''Return list of password field names needed to start the job.'''
        if self.credential:
            return self.credential.passwords_needed
        else:
            return []

    def _get_parent_field_name(self):
        return ''

    @classmethod
    def _get_task_class(cls):
        from awx.main.tasks import RunAdHocCommand
        return RunAdHocCommand

    @classmethod
    def supports_isolation(cls):
        return True

    @property
    def is_containerized(self):
        return bool(self.instance_group and self.instance_group.is_containerized)

    @property
    def can_run_containerized(self):
        return True

    def get_absolute_url(self, request=None):
        return reverse('api:ad_hoc_command_detail', kwargs={'pk': self.pk}, request=request)

    def get_ui_url(self):
        return urljoin(settings.TOWER_URL_BASE, "/#/jobs/command/{}".format(self.pk))

    @property
    def notification_templates(self):
        all_orgs = set()
        for h in self.hosts.all():
            all_orgs.add(h.inventory.organization)
        active_templates = dict(error=set(),
                                success=set(),
                                started=set())
        base_notification_templates = NotificationTemplate.objects
        for org in all_orgs:
            for templ in base_notification_templates.filter(organization_notification_templates_for_errors=org):
                active_templates['error'].add(templ)
            for templ in base_notification_templates.filter(organization_notification_templates_for_success=org):
                active_templates['success'].add(templ)
            for templ in base_notification_templates.filter(organization_notification_templates_for_started=org):
                active_templates['started'].add(templ)
        active_templates['error'] = list(active_templates['error'])
        active_templates['success'] = list(active_templates['success'])
        active_templates['started'] = list(active_templates['started'])
        return active_templates

    def get_passwords_needed_to_start(self):
        return self.passwords_needed_to_start

    @property
    def task_impact(self):
        # NOTE: We sorta have to assume the host count matches and that forks default to 5
        from awx.main.models.inventory import Host
        count_hosts = Host.objects.filter( enabled=True, inventory__ad_hoc_commands__pk=self.pk).count()
        return min(count_hosts, 5 if self.forks == 0 else self.forks) + 1

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
