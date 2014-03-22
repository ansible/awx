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

# AWX
from awx.main.models.base import *
from awx.main.utils import encrypt_field, decrypt_field

# Celery
from celery import chain

logger = logging.getLogger('awx.main.models.jobs')

__all__ = ['JobTemplate', 'Job', 'JobHostSummary', 'JobEvent']


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
    cloud_credential = models.ForeignKey(
        'Credential',
        related_name='job_templates_as_cloud_credential+',
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

    def clean_credential(self):
        cred = self.credential
        if cred and cred.kind != 'ssh':
            raise ValidationError('Credential kind must be "ssh"')
        return cred

    def clean_cloud_credential(self):
        cred = self.cloud_credential
        if cred and cred.kind not in ('aws', 'rax'):
            raise ValidationError('Cloud credential kind must be "aws" or '
                                  '"rax"')
        return cred

    def create_job(self, **kwargs):
        '''
        Create a new job based on this template.
        '''
        save_job = kwargs.pop('save', True)
        kwargs['job_template'] = self
        kwargs.setdefault('job_type', self.job_type)
        kwargs.setdefault('inventory', self.inventory)
        kwargs.setdefault('project', self.project)
        kwargs.setdefault('playbook', self.playbook)
        kwargs.setdefault('credential', self.credential)
        kwargs.setdefault('cloud_credential', self.cloud_credential)
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
        return reverse('api:job_template_detail', args=(self.pk,))

    def can_start_without_user_input(self):
        '''
        Return whether job template can be used to start a new job without
        requiring any user input.
        '''
        needed = []
        if self.credential:
            for pw in self.credential.passwords_needed:
                if pw == 'password':
                    needed.append('ssh_password')
                else:
                    needed.append(pw)
        return bool(self.credential and not len(needed))

class Job(CommonTask):
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
    cloud_credential = models.ForeignKey(
        'Credential',
        related_name='jobs_as_cloud_credential+',
        blank=True,
        null=True,
        default=None,
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
    launch_type = models.CharField(
        max_length=20,
        choices=LAUNCH_TYPE_CHOICES,
        default='manual',
        editable=False,
    )
    hosts = models.ManyToManyField(
        'Host',
        related_name='jobs',
        blank=True,
        editable=False,
        through='JobHostSummary',
    )

    def clean_credential(self):
        cred = self.credential
        if cred and cred.kind != 'ssh':
            raise ValidationError('Credential kind must be "ssh"')
        return cred

    def clean_cloud_credential(self):
        cred = self.cloud_credential
        if cred and cred.kind not in ('aws', 'rax'):
            raise ValidationError('Cloud credential kind must be "aws" or '
                                  '"rax"')
        return cred

    def get_absolute_url(self):
        return reverse('api:job_detail', args=(self.pk,))

    extra_vars_dict = VarsDictProperty('extra_vars', True)

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
            for pw in self.credential.passwords_needed:
                if pw == 'password':
                    needed.append('ssh_password')
                else:
                    needed.append(pw)
        return needed

    def _get_task_class(self):
        from awx.main.tasks import RunJob
        return RunJob

    def _get_passwords_needed_to_start(self):
        return self.passwords_needed_to_start

    def _get_hosts(self, **kwargs):
        from awx.main.models.inventory import Host
        kwargs['job_host_summaries__job__pk'] = self.pk
        return Host.objects.filter(**kwargs)

    def is_blocked_by(self, obj):
        from awx.main.models import InventoryUpdate, ProjectUpdate
        if type(obj) == Job:
            if obj.job_template == self.job_template:
                return True
            return False
        if type(obj) == InventoryUpdate:
            for i_s in self.inventory.inventory_sources.filter(active=True):
                if i_s == obj.inventory_source:
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
        if not project_found and self.project.scm_update_on_launch:
            dependencies.append(self.project.project_updates.create())
        if inventory_sources.count(): # and not has_setup_failures?  Probably handled as an error scenario in the task runner
            for source in inventory_sources:
                if not source in inventory_sources_found:
                    dependencies.append(source.inventory_updates.create())
        return dependencies

    def signal_start(self, **kwargs):
        from awx.main.tasks import notify_task_runner
        if hasattr(settings, 'CELERY_UNIT_TEST'):
            return self.start(None, **kwargs)
        if not self.can_start:
            return False
        needed = self._get_passwords_needed_to_start()
        opts = dict([(field, kwargs.get(field, '')) for field in needed])
        if not all(opts.values()):
            return False

        json_args = json.dumps(kwargs)
        self.start_args = json_args
        self.save()
        self.start_args = encrypt_field(self, 'start_args')
        self.save()
        notify_task_runner.delay(dict(task_type="ansible_playbook", id=self.id))
        return True

    def start(self, error_callback, **kwargs):
        from awx.main.tasks import handle_work_error
        task_class = self._get_task_class()
        if not self.can_start:
            return False
        needed = self._get_passwords_needed_to_start()
        try:
            stored_args = json.loads(decrypt_field(self, 'start_args'))
        except Exception, e:
            stored_args = None
        if stored_args is None or stored_args == '':
            opts = dict([(field, kwargs.get(field, '')) for field in needed])
        else:
            opts = dict([(field, stored_args.get(field, '')) for field in needed])
        if not all(opts.values()):
            return False
        task_class().apply_async((self.pk,), opts, link_error=error_callback)
        return True

class JobHostSummary(BaseModel):
    '''
    Per-host statistics for each job.
    '''

    class Meta:
        app_label = 'main'
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
        return reverse('api:job_host_summary_detail', args=(self.pk,))

    def save(self, *args, **kwargs):
        # If update_fields has been specified, add our field names to it,
        # if it hasn't been specified, then we're just doing a normal save.
        update_fields = kwargs.get('update_fields', [])
        self.failed = bool(self.dark or self.failures)
        update_fields.append('failed')
        super(JobHostSummary, self).save(*args, **kwargs)
        self.update_host_last_job_summary()

    def update_host_last_job_summary(self):
        update_fields = []
        if self.host.last_job_id != self.job_id:
            self.host.last_job_id = self.job_id
            update_fields.append('last_job_id')
        if self.host.last_job_host_summary_id != self.id:
            self.host.last_job_host_summary_id = self.id
            update_fields.append('last_job_host_summary_id')
        if update_fields:
            self.host.save(update_fields=update_fields)
        #self.host.update_computed_fields()

class JobEvent(BaseModel):
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
        #auto_now_add=True,
        editable=False,
        default=None,
    )
    modified = models.DateTimeField(
        #auto_now=True,
        editable=False,
        default=None,
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
        return reverse('api:job_event_detail', args=(self.pk,))

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
        # Only update job event hierarchy and related models during post
        # processing (after running job).
        post_process = kwargs.pop('post_process', False)
        if post_process:
            try:
                if not self.host_id and self.event_data.get('host', ''):
                    host_qs = Host.objects.filter(inventory__jobs__id=self.job_id, name=self.event_data['host'])
                    self.host_id = host_qs.only('id').values_list('id', flat=True)[0]
                    if 'host_id' not in update_fields:
                        update_fields.append('host_id')
            except (IndexError, AttributeError):
                pass
            self.parent = self._find_parent()
            if 'parent' not in update_fields:
                update_fields.append('parent')
        # Manually perform auto_now_add and auto_now logic (to allow overriding
        # created timestamp for queued job events).
        if not self.pk and not self.created:
            self.created = now()
            if 'created' not in update_fields:
                update_fields.append('created')
        self.modified = now()
        if 'modified' not in update_fields:
            update_fields.append('modified')
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
        if self.event_data.get('host', ''):
            hostnames.add(self.event_data['host'])
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
        from awx.main.signals import ignore_inventory_computed_fields
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
            for host in qs.only('id', 'name'):
                host_stats = {}
                for stat in ('changed', 'dark', 'failures', 'ok', 'processed', 'skipped'):
                    try:
                        host_stats[stat] = self.event_data.get(stat, {}).get(host.name, 0)
                    except AttributeError: # in case event_data[stat] isn't a dict.
                        pass
                host_summary, created = job.job_host_summaries.get_or_create(host=host, defaults=host_stats)
                if not created:
                    update_fields = []
                    for stat, value in host_stats.items():
                        if getattr(host_summary, stat) != value:
                            setattr(host_summary, stat, value)
                            update_fields.append(stat)
                    if update_fields:
                        host_summary.save(update_fields=update_fields)
            job.inventory.update_computed_fields()

