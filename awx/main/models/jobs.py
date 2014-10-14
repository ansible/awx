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
from django.db.models import Q
from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils.timezone import now, make_aware, get_default_timezone

# Django-JSONField
from jsonfield import JSONField

# Django-Polymorphic
from polymorphic import PolymorphicModel

# AWX
from awx.main.constants import CLOUD_PROVIDERS
from awx.main.models.base import *
from awx.main.models.unified_jobs import *
from awx.main.utils import encrypt_field, decrypt_field, ignore_inventory_computed_fields
from awx.main.utils import emit_websocket_notification

# Celery
from celery import chain

logger = logging.getLogger('awx.main.models.jobs')

__all__ = ['JobTemplate', 'Job', 'JobHostSummary', 'JobEvent', 'SystemJobOptions', 'SystemJobTemplate', 'SystemJob']


class JobOptions(BaseModel):
    '''
    Common options for job templates and jobs.
    '''

    class Meta:
        abstract = True

    job_type = models.CharField(
        max_length=64,
        choices=JOB_TYPE_CHOICES,
    )
    inventory = models.ForeignKey(
        'Inventory',
        related_name='%(class)ss',
        null=True,
        on_delete=models.SET_NULL,
    )
    project = models.ForeignKey(
        'Project',
        related_name='%(class)ss',
        null=True,
        on_delete=models.SET_NULL,
    )
    playbook = models.CharField(
        max_length=1024,
        default='',
    )
    credential = models.ForeignKey(
        'Credential',
        related_name='%(class)ss',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    )
    cloud_credential = models.ForeignKey(
        'Credential',
        related_name='%(class)ss_as_cloud_credential+',
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
    force_handlers = models.BooleanField(
        blank=True,
        default=False,
    )
    skip_tags = models.CharField(
        max_length=1024,
        blank=True,
        default='',
    )
    start_at_task = models.CharField(
        max_length=1024,
        blank=True,
        default='',
    )

    extra_vars_dict = VarsDictProperty('extra_vars', True)

    def clean_credential(self):
        cred = self.credential
        if cred and cred.kind != 'ssh':
            raise ValidationError(
                'You must provide a machine / SSH credential.',
            )
        return cred

    def clean_cloud_credential(self):
        cred = self.cloud_credential
        if cred and cred.kind not in CLOUD_PROVIDERS + ('aws',):
            raise ValidationError(
                'Must provide a credential for a cloud provider, such as '
                'Amazon Web Services or Rackspace.',
            )
        return cred

    @property
    def passwords_needed_to_start(self):
        '''Return list of password field names needed to start the job.'''
        needed = []
        if self.credential:
            for pw in self.credential.passwords_needed:
                if pw == 'password':
                    needed.append('ssh_password')
                else:
                    needed.append(pw)
        return needed


class JobTemplate(UnifiedJobTemplate, JobOptions):
    '''
    A job template is a reusable job definition for applying a project (with
    playbook) to an inventory source with a given credential.
    '''

    class Meta:
        app_label = 'main'
        ordering = ('name',)

    host_config_key = models.CharField(
        max_length=1024,
        blank=True,
        default='',
    )

    ask_variables_on_launch = models.BooleanField(
        blank=True,
        default=False,
    )

    survey_enabled = models.BooleanField(
        default=False,
    )

    survey_spec = JSONField(
        blank=True,
        default={},
    )

    @classmethod
    def _get_unified_job_class(cls):
        return Job

    @classmethod
    def _get_unified_job_field_names(cls):
        return ['name', 'description', 'job_type', 'inventory', 'project',
                'playbook', 'credential', 'cloud_credential', 'forks',
                'limit', 'verbosity', 'extra_vars', 'job_tags',
                'force_handlers', 'skip_tags', 'start_at_task']

    def create_job(self, **kwargs):
        '''
        Create a new job based on this template.
        '''
        return self.create_unified_job(**kwargs)

    def get_absolute_url(self):
        return reverse('api:job_template_detail', args=(self.pk,))

    def can_start_without_user_input(self):
        '''
        Return whether job template can be used to start a new job without
        requiring any user input.
        '''
        return bool(self.credential and not len(self.passwords_needed_to_start) and not len(self.variables_needed_to_start))

    @property
    def variables_needed_to_start(self):
        vars = []
        if self.survey_enabled and 'spec' in self.survey_spec:
            for survey_element in self.survey_spec['spec']:
                if survey_element['required']:
                    vars.append(survey_element['variable'])
        return vars

    def survey_variable_validation(self, data):
        errors = []
        if not self.survey_enabled:
            return errors
        if 'name' not in self.survey_spec:
            errors.append("'name' missing from survey spec")
        if 'description' not in self.survey_spec:
            errors.append("'description' missing from survey spec")
        for survey_element in self.survey_spec["spec"]:
            if survey_element['variable'] not in data and \
               survey_element['required']:
                errors.append("'%s' value missing" % survey_element['variable'])
            elif survey_element['type'] in ["textarea", "text"]:
                if survey_element['variable'] in data:
                    if 'min' in survey_element and survey_element['min'] != "" and len(data[survey_element['variable']]) < survey_element['min']:
                        errors.append("'%s' value %s is too small (must be at least %s)" %
                                      (survey_element['variable'], data[survey_element['variable']], survey_element['min']))
                    if 'max' in survey_element and survey_element['max'] != "" and len(data[survey_element['variable']]) > survey_element['max']:
                        errors.append("'%s' value %s is too large (must be no more than%s)" %
                                      (survey_element['variable'], data[survey_element['variable']], survey_element['max']))
            elif survey_element['type'] == 'integer':
                if survey_element['variable'] in data:
                    if 'min' in survey_element and survey_element['min'] != "" and survey_element['variable'] in data and \
                       data[survey_element['variable']] < survey_element['min']:
                        errors.append("'%s' value %s is too small (must be at least %s)" %
                                      (survey_element['variable'], data[survey_element['variable']], survey_element['min']))
                    if 'max' in survey_element and survey_element['max'] != "" and survey_element['variable'] in data and \
                       data[survey_element['variable']] > survey_element['max']:
                        errors.append("'%s' value %s is too large (must be no more than%s)" %
                                      (survey_element['variable'], data[survey_element['variable']], survey_element['max']))
                    if type(data[survey_element['variable']]) != int:
                        errors.append("Value %s for %s expected to be an integer" % (data[survey_element['variable']],
                                                                                     survey_element['variable']))
            elif survey_element['type'] == 'float':
                if survey_element['variable'] in data:
                    if 'min' in survey_element and survey_element['min'] != "" and data[survey_element['variable']] < survey_element['min']:
                        errors.append("'%s' value %s is too small (must be at least %s)" %
                                      (survey_element['variable'], data[survey_element['variable']], survey_element['min']))
                    if 'max' in survey_element and survey_element['max'] != "" and data[survey_element['variable']] > survey_element['max']:
                        errors.append("'%s' value %s is too large (must be no more than%s)" %
                                      (survey_element['variable'], data[survey_element['variable']], survey_element['max']))
                    if type(data[survey_element['variable']]) not in (float, int):
                        errors.append("Value %s for %s expected to be a numeric type" % (data[survey_element['variable']],
                                                                                  survey_element['variable']))
            elif survey_element['type'] == 'multiselect':
                if survey_element['variable'] in data:
                    if type(data[survey_element['variable']]) != list:
                        errors.append("'%s' value is expected to be a list" % survey_element['variable'])
                    else:
                        for val in data[survey_element['variable']]:
                            if val not in survey_element['choices']:
                                errors.append("Value %s for %s expected to be one of %s" % (val, survey_element['variable'],
                                                                                            survey_element['choices']))
            elif survey_element['type'] == 'multiplechoice':
                if survey_element['variable'] in data:
                    if data[survey_element['variable']] not in survey_element['choices']:
                        errors.append("Value %s for %s expected to be one of %s" % (data[survey_element['variable']],
                                                                                    survey_element['variable'],
                                                                                    survey_element['choices']))
        return errors


    def _can_update(self):
        return self.can_start_without_user_input()


class Job(UnifiedJob, JobOptions):
    '''
    A job applies a project (with playbook) to an inventory source with a given
    credential.  It represents a single invocation of ansible-playbook with the
    given parameters.
    '''

    class Meta:
        app_label = 'main'
        ordering = ('id',)

    job_template = models.ForeignKey(
        'JobTemplate',
        related_name='jobs',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    )
    hosts = models.ManyToManyField(
        'Host',
        related_name='jobs',
        editable=False,
        through='JobHostSummary',
    )

    @classmethod
    def _get_parent_field_name(cls):
        return 'job_template'

    @classmethod
    def _get_task_class(cls):
        from awx.main.tasks import RunJob
        return RunJob

    def get_absolute_url(self):
        return reverse('api:job_detail', args=(self.pk,))

    @property
    def task_auth_token(self):
        '''Return temporary auth token used for task requests via API.'''
        if self.status == 'running':
            h = hmac.new(settings.SECRET_KEY, self.created.isoformat())
            return '%d-%s' % (self.pk, h.hexdigest())

    @property
    def ask_variables_on_launch(self):
        if self.job_template is not None:
            return self.job_template.ask_variables_on_launch
        return False

    def get_passwords_needed_to_start(self):
        return self.passwords_needed_to_start

    def _get_hosts(self, **kwargs):
        from awx.main.models.inventory import Host
        kwargs['job_host_summaries__job__pk'] = self.pk
        return Host.objects.filter(**kwargs)

    def is_blocked_by(self, obj):
        from awx.main.models import InventoryUpdate, ProjectUpdate
        if type(obj) == Job:
            if obj.job_template is not None and obj.job_template == self.job_template:
                if obj.launch_type == 'callback' and self.launch_type == 'callback':
                    if obj.limit != self.limit:
                        return False
                return True
            return False
        if type(obj) == InventoryUpdate:
            if self.inventory == obj.inventory_source.inventory:
                return True
            return False
        if type(obj) == ProjectUpdate:
            if obj.project == self.project:
                return True
            return False
        return False

    @property
    def task_impact(self):
        # NOTE: We sorta have to assume the host count matches and that forks default to 5
        from awx.main.models.inventory import Host
        if self.launch_type == 'callback':
            count_hosts = 1
        else:
            count_hosts = Host.objects.filter(inventory__jobs__pk=self.pk).count()
        return min(count_hosts, 5 if self.forks == 0 else self.forks) * 10

    @property
    def successful_hosts(self):
        return self._get_hosts(job_host_summaries__ok__gt=0)

    @property
    def failed_hosts(self):
        return self._get_hosts(job_host_summaries__failures__gt=0)

    @property
    def changed_hosts(self):
        return self._get_hosts(job_host_summaries__changed__gt=0)

    @property
    def dark_hosts(self):
        return self._get_hosts(job_host_summaries__dark__gt=0)

    @property
    def unreachable_hosts(self):
        return self.dark_hosts

    @property
    def skipped_hosts(self):
        return self._get_hosts(job_host_summaries__skipped__gt=0)

    @property
    def processed_hosts(self):
        return self._get_hosts(job_host_summaries__processed__gt=0)

    def generate_dependencies(self, active_tasks):
        from awx.main.models import InventoryUpdate, ProjectUpdate
        inventory_sources = self.inventory.inventory_sources.filter(active=True, update_on_launch=True)
        project_found = False
        inventory_sources_found = []
        dependencies = []
        for obj in active_tasks:
            if type(obj) == ProjectUpdate:
                if obj.project == self.project:
                    project_found = True
            if type(obj) == InventoryUpdate:
                if obj.inventory_source in inventory_sources:
                    inventory_sources_found.append(obj.inventory_source)
        # Skip updating any inventory sources that were already updated before
        # running this job (via callback inventory refresh).
        try:
            start_args = json.loads(decrypt_field(self, 'start_args'))
        except Exception, e:
            start_args = None
        start_args = start_args or {}
        inventory_sources_already_updated = start_args.get('inventory_sources_already_updated', [])
        if inventory_sources_already_updated:
            for source in inventory_sources.filter(pk__in=inventory_sources_already_updated):
                if source not in inventory_sources_found:
                    inventory_sources_found.append(source)
        if not project_found and self.project.needs_update_on_launch:
            dependencies.append(self.project.create_project_update(launch_type='dependency'))
        if inventory_sources.count(): # and not has_setup_failures?  Probably handled as an error scenario in the task runner
            for source in inventory_sources:
                if not source in inventory_sources_found and source.needs_update_on_launch:
                    dependencies.append(source.create_inventory_update(launch_type='dependency'))
        return dependencies

    def handle_extra_data(self, extra_data):
        if extra_data == "":
            return
        try:
            evars = json.loads(self.extra_vars)
        except Exception, e:
            return
        if evars is None:
            evars = extra_data
        else:
            evars.update(extra_data)
        self.update_fields(extra_vars=json.dumps(evars))

    def copy(self):
        presets = {}
        for kw in self.job_template._get_unified_job_field_names():
            presets[kw] = getattr(self, kw)
        return self.job_template.create_unified_job(**presets)

class JobHostSummary(CreatedModifiedModel):
    '''
    Per-host statistics for each job.
    '''

    class Meta:
        app_label = 'main'
        unique_together = [('job', 'host_name')]
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
        return reverse('api:job_host_summary_detail', args=(self.pk,))

    def save(self, *args, **kwargs):
        # If update_fields has been specified, add our field names to it,
        # if it hasn't been specified, then we're just doing a normal save.
        if self.host is not None:
            self.host_name = self.host.name
        update_fields = kwargs.get('update_fields', [])
        self.failed = bool(self.dark or self.failures)
        update_fields.append('failed')
        super(JobHostSummary, self).save(*args, **kwargs)
        self.update_host_last_job_summary()

    def update_host_last_job_summary(self):
        update_fields = []
        if self.host is None:
            return
        if self.host.last_job_id != self.job_id:
            self.host.last_job_id = self.job_id
            update_fields.append('last_job_id')
        if self.host.last_job_host_summary_id != self.id:
            self.host.last_job_host_summary_id = self.id
            update_fields.append('last_job_host_summary_id')
        if update_fields:
            self.host.save(update_fields=update_fields)
        #self.host.update_computed_fields()


class JobEvent(CreatedModifiedModel):
    '''
    An event/message logged from the callback when running a job.
    '''

    # Playbook events will be structured to form the following hierarchy:
    # - playbook_on_start (once for each playbook file)
    #   - playbook_on_vars_prompt (for each play, but before play starts, we
    #     currently don't handle responding to these prompts)
    #   - playbook_on_play_start (once for each play)
    #     - playbook_on_import_for_host
    #     - playbook_on_not_import_for_host
    #     - playbook_on_no_hosts_matched
    #     - playbook_on_no_hosts_remaining
    #     - playbook_on_setup
    #       - runner_on*
    #     - playbook_on_task_start (once for each task within a play)
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
    #     - playbook_on_notify (once for each notification from the play)
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
    hosts = models.ManyToManyField(
        'Host',
        related_name='job_events',
        editable=False,
    )
    play = models.CharField(
        max_length=1024,
        default='',
        editable=False,
    )
    role = models.CharField( # FIXME: Determine from callback or task name.
        max_length=1024,
        default='',
        editable=False,
    )
    task = models.CharField(
        max_length=1024,
        default='',
        editable=False,
    )
    parent = models.ForeignKey(
        'self',
        related_name='children',
        null=True,
        default=None,
        on_delete=models.SET_NULL,
        editable=False,
    )
    counter = models.PositiveIntegerField(
        default=0,
    )


    def get_absolute_url(self):
        return reverse('api:job_event_detail', args=(self.pk,))

    def __unicode__(self):
        return u'%s @ %s' % (self.get_event_display2(), self.created.isoformat())

    @property
    def event_level(self):
        return self.LEVEL_FOR_EVENT.get(self.event, 0)

    def get_event_display2(self):
        msg = self.get_event_display()
        if self.event == 'playbook_on_play_start':
            if self.play:
                msg = "%s (%s)" % (msg, self.play)
        elif self.event == 'playbook_on_task_start':
            if self.task:
                if self.event_data.get('is_conditional', False):
                    msg = 'Handler Notified'
                if self.role:
                    msg = '%s (%s | %s)' % (msg, self.role, self.task)
                else:
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
                qs = JobEvent.objects.filter(job_id=self.job_id)
                if self.pk:
                    qs = qs.filter(pk__lt=self.pk, event__in=parent_events)
                else:
                    qs = qs.filter(event__in=parent_events)
                return qs.order_by('-pk')[0]
            except IndexError:
                pass
        return None

    def save(self, *args, **kwargs):
        from awx.main.models.inventory import Host
        # If update_fields has been specified, add our field names to it,
        # if it hasn't been specified, then we're just doing a normal save.
        update_fields = kwargs.get('update_fields', [])
        # Skip normal checks on save if we're only updating failed/changed
        # flags triggered from a child event.
        from_parent_update = kwargs.pop('from_parent_update', False)
        if not from_parent_update:
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
                    if 'failed' not in update_fields:
                        update_fields.append('failed')
            if isinstance(res, dict) and res.get('changed', False):
                self.changed = True
                if 'changed' not in update_fields:
                    update_fields.append('changed')
            if self.event == 'playbook_on_stats':
                try:
                    failures_dict = self.event_data.get('failures', {})
                    dark_dict = self.event_data.get('dark', {})
                    self.failed = bool(sum(failures_dict.values()) + 
                                       sum(dark_dict.values()))
                    if 'failed' not in update_fields:
                        update_fields.append('failed')
                    changed_dict = self.event_data.get('changed', {})
                    self.changed = bool(sum(changed_dict.values()))
                    if 'changed' not in update_fields:
                        update_fields.append('changed')
                except (AttributeError, TypeError):
                    pass
            self.play = self.event_data.get('play', '').strip()
            if 'play' not in update_fields:
                update_fields.append('play')
            self.task = self.event_data.get('task', '').strip()
            if 'task' not in update_fields:
                update_fields.append('task')
            self.role = self.event_data.get('role', '').strip()
            if 'role' not in update_fields:
                update_fields.append('role')
            self.host_name = self.event_data.get('host', '').strip()
            if 'host_name' not in update_fields:
                update_fields.append('host_name')
        # Only update job event hierarchy and related models during post
        # processing (after running job).
        post_process = kwargs.pop('post_process', False)
        if post_process:
            try:
                if not self.host_id and self.host_name:
                    host_qs = Host.objects.filter(inventory__jobs__id=self.job_id, name=self.host_name)
                    host_id = host_qs.only('id').values_list('id', flat=True)
                    if host_id.exists():
                        self.host_id = host_id[0]
                        if 'host_id' not in update_fields:
                            update_fields.append('host_id')
            except (IndexError, AttributeError):
                pass
            if self.parent is None:
                self.parent = self._find_parent()
            if 'parent' not in update_fields:
                update_fields.append('parent')
        super(JobEvent, self).save(*args, **kwargs)
        if post_process and not from_parent_update:
            self.update_parent_failed_and_changed()
            # FIXME: The update_hosts() call (and its queries) are the current
            # performance bottleneck....
            if getattr(settings, 'CAPTURE_JOB_EVENT_HOSTS', False):
                self.update_hosts()
            self.update_host_summary_from_stats()

    def update_parent_failed_and_changed(self):
        # Propagage failed and changed flags to parent events.
        if self.parent:
            parent = self.parent
            update_fields = []
            if self.failed and not parent.failed:
                parent.failed = True
                update_fields.append('failed')
            if self.changed and not parent.changed:
                parent.changed = True
                update_fields.append('changed')
            if update_fields:
                parent.save(update_fields=update_fields, from_parent_update=True)
                parent.update_parent_failed_and_changed()

    def update_hosts(self, extra_host_pks=None):
        from awx.main.models.inventory import Host
        extra_host_pks = set(extra_host_pks or [])
        hostnames = set()
        if self.host_name:
            hostnames.add(self.host_name)
        if self.event == 'playbook_on_stats':
            try:
                for v in self.event_data.values():
                    hostnames.update(v.keys())
            except AttributeError: # In case event_data or v isn't a dict.
                pass
        qs = Host.objects.filter(inventory__jobs__id=self.job_id)
        qs = qs.filter(Q(name__in=hostnames) | Q(pk__in=extra_host_pks))
        qs = qs.exclude(job_events__pk=self.id)
        for host in qs.only('id'):
            self.hosts.add(host)
        if self.parent:
            self.parent.update_hosts(self.hosts.only('id').values_list('id', flat=True))

    def update_host_summary_from_stats(self):
        from awx.main.models.inventory import Host
        if self.event != 'playbook_on_stats':
            return
        hostnames = set()
        try:
            for v in self.event_data.values():
                hostnames.update(v.keys())
        except AttributeError: # In case event_data or v isn't a dict.
            pass
        with ignore_inventory_computed_fields():
            qs = Host.objects.filter(inventory__jobs__id=self.job_id,
                                     name__in=hostnames)
            job = self.job
            #for host in qs.only('id', 'name'):
            for host in hostnames:
                host_stats = {}
                for stat in ('changed', 'dark', 'failures', 'ok', 'processed', 'skipped'):
                    try:
                        host_stats[stat] = self.event_data.get(stat, {}).get(host, 0)
                    except AttributeError: # in case event_data[stat] isn't a dict.
                        pass
                if qs.filter(name=host).exists():
                    host_actual = qs.get(name=host)
                    host_summary, created = job.job_host_summaries.get_or_create(host=host_actual, host_name=host_actual.name, defaults=host_stats)
                else:
                    host_summary, created = job.job_host_summaries.get_or_create(host_name=host, defaults=host_stats)
                if not created:
                    update_fields = []
                    for stat, value in host_stats.items():
                        if getattr(host_summary, stat) != value:
                            setattr(host_summary, stat, value)
                            update_fields.append(stat)
                    if update_fields:
                        host_summary.save(update_fields=update_fields)
            job.inventory.update_computed_fields()
            emit_websocket_notification('/socket.io/jobs', 'summary_complete', dict(unified_job_id=job.id))

class SystemJobOptions(BaseModel):
    '''
    Common fields for SystemJobTemplate and SystemJob.
    '''

    SYSTEM_JOB_TYPE = [
        ('cleanup_jobs', _('Remove jobs older than a certain number of days')),
        ('cleanup_activitystream', _('Remove activity stream entries older than a certain number of days')),
        ('cleanup_deleted', _('Purge previously deleted items from the database')),
    ]

    class Meta:
        abstract = True

    job_type = models.CharField(
        max_length=32,
        choices=SYSTEM_JOB_TYPE,
        blank=True,
        default='',
    )

class SystemJobTemplate(UnifiedJobTemplate, SystemJobOptions):

    class Meta:
        app_label = 'main'

    @classmethod
    def _get_unified_job_class(cls):
        return SystemJob

    @classmethod
    def _get_unified_job_field_names(cls):
        return ['name', 'description', 'job_type']

    def get_absolute_url(self):
        return reverse('api:system_job_template_detail', args=(self.pk,))


class SystemJob(UnifiedJob, SystemJobOptions):

    class Meta:
        app_label = 'main'
        ordering = ('id',)

    system_job_template = models.ForeignKey(
        'SystemJobTemplate',
        related_name='jobs',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    )

    @classmethod
    def _get_parent_field_name(cls):
        return 'system_job_template'

    @classmethod
    def _get_task_class(cls):
        from awx.main.tasks import RunSystemJob
        return RunSystemJob

    def socketio_emit_data(self):
        return {}

    def get_absolute_url(self):
        return reverse('api:system_job_detail', args=(self.pk,))

    def is_blocked_by(self, obj):
        return True

    @property
    def task_impact(self):
        return 150
