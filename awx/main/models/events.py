import datetime
import logging
from collections import defaultdict

from django.conf import settings
from django.db import models, DatabaseError
from django.utils.dateparse import parse_datetime
from django.utils.text import Truncator
from django.utils.timezone import utc
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_text

from awx.api.versioning import reverse
from awx.main.fields import JSONField
from awx.main.models.base import CreatedModifiedModel
from awx.main.utils import ignore_inventory_computed_fields

analytics_logger = logging.getLogger('awx.analytics.job_events')

logger = logging.getLogger('awx.main.models.events')


__all__ = ['JobEvent', 'ProjectUpdateEvent', 'AdHocCommandEvent',
           'InventoryUpdateEvent', 'SystemJobEvent']


def sanitize_event_keys(kwargs, valid_keys):
    # Sanity check: Don't honor keys that we don't recognize.
    for key in list(kwargs.keys()):
        if key not in valid_keys:
            kwargs.pop(key)

    # Truncate certain values over 1k
    for key in [
        'play', 'role', 'task', 'playbook'
    ]:
        if isinstance(kwargs.get('event_data', {}).get(key), str):
            if len(kwargs['event_data'][key]) > 1024:
                kwargs['event_data'][key] = Truncator(kwargs['event_data'][key]).chars(1024)


def create_host_status_counts(event_data):
    host_status = {}
    host_status_keys = ['skipped', 'ok', 'changed', 'failures', 'dark']

    for key in host_status_keys:
        for host in event_data.get(key, {}):
            host_status[host] = key

    host_status_counts = defaultdict(lambda: 0)

    for value in host_status.values():
        host_status_counts[value] += 1

    return dict(host_status_counts)


class BasePlaybookEvent(CreatedModifiedModel):
    '''
    An event/message logged from a playbook callback for each host.
    '''

    VALID_KEYS = [
        'event', 'event_data', 'playbook', 'play', 'role', 'task', 'created',
        'counter', 'uuid', 'stdout', 'parent_uuid', 'start_line', 'end_line',
        'verbosity'
    ]

    class Meta:
        abstract = True

    # Playbook events will be structured to form the following hierarchy:
    # - playbook_on_start (once for each playbook file)
    #   - playbook_on_vars_prompt (for each play, but before play starts, we
    #     currently don't handle responding to these prompts)
    #   - playbook_on_play_start (once for each play)
    #     - playbook_on_import_for_host (not logged, not used for v2)
    #     - playbook_on_not_import_for_host (not logged, not used for v2)
    #     - playbook_on_no_hosts_matched
    #     - playbook_on_no_hosts_remaining
    #     - playbook_on_include (only v2 - only used for handlers?)
    #     - playbook_on_setup (not used for v2)
    #       - runner_on*
    #     - playbook_on_task_start (once for each task within a play)
    #       - runner_on_failed
    #       - runner_on_ok
    #       - runner_on_error (not used for v2)
    #       - runner_on_skipped
    #       - runner_on_unreachable
    #       - runner_on_no_hosts (not used for v2)
    #       - runner_on_async_poll (not used for v2)
    #       - runner_on_async_ok (not used for v2)
    #       - runner_on_async_failed (not used for v2)
    #       - runner_on_file_diff (v2 event is v2_on_file_diff)
    #       - runner_item_on_ok (v2 only)
    #       - runner_item_on_failed (v2 only)
    #       - runner_item_on_skipped (v2 only)
    #       - runner_retry (v2 only)
    #     - playbook_on_notify (once for each notification from the play, not used for v2)
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
        (3, 'runner_item_on_ok', _('Item OK'), False),
        (3, 'runner_item_on_failed', _('Item Failed'), True),
        (3, 'runner_item_on_skipped', _('Item Skipped'), False),
        (3, 'runner_retry', _('Host Retry'), False),
        # Tower does not yet support --diff mode.
        (3, 'runner_on_file_diff', _('File Difference'), False),
        (0, 'playbook_on_start', _('Playbook Started'), False),
        (2, 'playbook_on_notify', _('Running Handlers'), False),
        (2, 'playbook_on_include', _('Including File'), False),
        (2, 'playbook_on_no_hosts_matched', _('No Hosts Matched'), False),
        (2, 'playbook_on_no_hosts_remaining', _('No Hosts Remaining'), False),
        (2, 'playbook_on_task_start', _('Task Started'), False),
        # Tower does not yet support vars_prompt (and will probably hang :)
        (1, 'playbook_on_vars_prompt', _('Variables Prompted'), False),
        (2, 'playbook_on_setup', _('Gathering Facts'), False),
        (2, 'playbook_on_import_for_host', _('internal: on Import for Host'), False),
        (2, 'playbook_on_not_import_for_host', _('internal: on Not Import for Host'), False),
        (1, 'playbook_on_play_start', _('Play Started'), False),
        (1, 'playbook_on_stats', _('Playbook Complete'), False),

        # Additional event types for captured stdout not directly related to
        # playbook or runner events.
        (0, 'debug', _('Debug'), False),
        (0, 'verbose', _('Verbose'), False),
        (0, 'deprecated', _('Deprecated'), False),
        (0, 'warning', _('Warning'), False),
        (0, 'system_warning', _('System Warning'), False),
        (0, 'error', _('Error'), True),
    ]
    FAILED_EVENTS = [x[1] for x in EVENT_TYPES if x[3]]
    EVENT_CHOICES = [(x[1], x[2]) for x in EVENT_TYPES]
    LEVEL_FOR_EVENT = dict([(x[1], x[0]) for x in EVENT_TYPES])

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
    playbook = models.CharField(
        max_length=1024,
        default='',
        editable=False,
    )
    play = models.CharField(
        max_length=1024,
        default='',
        editable=False,
    )
    role = models.CharField(
        max_length=1024,
        default='',
        editable=False,
    )
    task = models.CharField(
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
    created = models.DateTimeField(
        null=True,
        default=None,
        editable=False,
        db_index=True,
    )

    @property
    def event_level(self):
        return self.LEVEL_FOR_EVENT.get(self.event, 0)

    def get_host_status_counts(self):
        return create_host_status_counts(getattr(self, 'event_data', {}))

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

        # Change display for runner events triggered by async polling.  Some of
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

    def _update_from_event_data(self):
        # Update event model fields from event data.
        updated_fields = set()
        event_data = self.event_data
        res = event_data.get('res', None)
        if self.event in self.FAILED_EVENTS and not event_data.get('ignore_errors', False):
            self.failed = True
            updated_fields.add('failed')
        if isinstance(res, dict):
            if res.get('changed', False):
                self.changed = True
                updated_fields.add('changed')
        if self.event == 'playbook_on_stats':
            try:
                failures_dict = event_data.get('failures', {})
                dark_dict = event_data.get('dark', {})
                self.failed = bool(sum(failures_dict.values()) +
                                   sum(dark_dict.values()))
                updated_fields.add('failed')
                changed_dict = event_data.get('changed', {})
                self.changed = bool(sum(changed_dict.values()))
                updated_fields.add('changed')
            except (AttributeError, TypeError):
                pass
        for field in ('playbook', 'play', 'task', 'role'):
            value = force_text(event_data.get(field, '')).strip()
            if value != getattr(self, field):
                setattr(self, field, value)
                updated_fields.add(field)
        return updated_fields

    @classmethod
    def create_from_data(cls, **kwargs):
        pk = None
        for key in ('job_id', 'project_update_id'):
            if key in kwargs:
                pk = key
        if pk is None:
            # payload must contain either a job_id or a project_update_id
            return

        # Convert the datetime for the job event's creation appropriately,
        # and include a time zone for it.
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

        sanitize_event_keys(kwargs, cls.VALID_KEYS)
        job_event = cls.objects.create(**kwargs)
        analytics_logger.info('Event data saved.', extra=dict(python_objects=dict(job_event=job_event)))
        return job_event

    @property
    def job_verbosity(self):
        return 0

    def save(self, *args, **kwargs):
        # If update_fields has been specified, add our field names to it,
        # if it hasn't been specified, then we're just doing a normal save.
        update_fields = kwargs.get('update_fields', [])
        # Update model fields and related objects unless we're only updating
        # failed/changed flags triggered from a child event.
        from_parent_update = kwargs.pop('from_parent_update', False)
        if not from_parent_update:
            # Update model fields from event data.
            updated_fields = self._update_from_event_data()
            for field in updated_fields:
                if field not in update_fields:
                    update_fields.append(field)

            # Update host related field from host_name.
            if hasattr(self, 'job') and not self.host_id and self.host_name:
                host_qs = self.job.inventory.hosts.filter(name=self.host_name)
                host_id = host_qs.only('id').values_list('id', flat=True).first()
                if host_id != self.host_id:
                    self.host_id = host_id
                    if 'host_id' not in update_fields:
                        update_fields.append('host_id')
        super(BasePlaybookEvent, self).save(*args, **kwargs)

        # Update related objects after this event is saved.
        if hasattr(self, 'job') and not from_parent_update:
            if getattr(settings, 'CAPTURE_JOB_EVENT_HOSTS', False):
                self._update_hosts()
            if self.parent_uuid:
                kwargs = {}
                if self.changed is True:
                    kwargs['changed'] = True
                if self.failed is True:
                    kwargs['failed'] = True
                if kwargs:
                    JobEvent.objects.filter(job_id=self.job_id, uuid=self.parent_uuid).update(**kwargs)

            if self.event == 'playbook_on_stats':
                hostnames = self._hostnames()
                self._update_host_summary_from_stats(hostnames)
                try:
                    self.job.inventory.update_computed_fields()
                except DatabaseError:
                    logger.exception('Computed fields database error saving event {}'.format(self.pk))



class JobEvent(BasePlaybookEvent):
    '''
    An event/message logged from the callback when running a job.
    '''

    VALID_KEYS = BasePlaybookEvent.VALID_KEYS + ['job_id']

    class Meta:
        app_label = 'main'
        ordering = ('pk',)
        index_together = [
            ('job', 'event'),
            ('job', 'uuid'),
            ('job', 'start_line'),
            ('job', 'end_line'),
            ('job', 'parent_uuid'),
        ]

    job = models.ForeignKey(
        'Job',
        related_name='job_events',
        on_delete=models.CASCADE,
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
    parent = models.ForeignKey(
        'self',
        related_name='children',
        null=True,
        default=None,
        on_delete=models.SET_NULL,
        editable=False,
    )
    parent_uuid = models.CharField(
        max_length=1024,
        default='',
        editable=False,
    )

    def get_absolute_url(self, request=None):
        return reverse('api:job_event_detail', kwargs={'pk': self.pk}, request=request)

    def __str__(self):
        return u'%s @ %s' % (self.get_event_display2(), self.created.isoformat())

    def _update_from_event_data(self):
        # Update job event hostname
        updated_fields = super(JobEvent, self)._update_from_event_data()
        value = force_text(self.event_data.get('host', '')).strip()
        if value != getattr(self, 'host_name'):
            setattr(self, 'host_name', value)
            updated_fields.add('host_name')
        return updated_fields

    def _update_hosts(self, extra_host_pks=None):
        # Update job event hosts m2m from host_name, propagate to parent events.
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
        qs = self.job.inventory.hosts.all()
        qs = qs.filter(models.Q(name__in=hostnames) | models.Q(pk__in=extra_host_pks))
        qs = qs.exclude(job_events__pk=self.id).only('id')
        for host in qs:
            self.hosts.add(host)
        if self.parent_uuid:
            parent = JobEvent.objects.filter(uuid=self.parent_uuid)
            if parent.exists():
                parent = parent[0]
                parent._update_hosts(qs.values_list('id', flat=True))

    def _hostnames(self):
        hostnames = set()
        try:
            for stat in ('changed', 'dark', 'failures', 'ok', 'processed', 'skipped'):
                hostnames.update(self.event_data.get(stat, {}).keys())
        except AttributeError:  # In case event_data or v isn't a dict.
            pass
        return hostnames

    def _update_host_summary_from_stats(self, hostnames):
        with ignore_inventory_computed_fields():
            if not self.job or not self.job.inventory:
                logger.info('Event {} missing job or inventory, host summaries not updated'.format(self.pk))
                return
            qs = self.job.inventory.hosts.filter(name__in=hostnames)
            job = self.job
            for host in hostnames:
                host_stats = {}
                for stat in ('changed', 'dark', 'failures', 'ignored', 'ok', 'processed', 'rescued', 'skipped'):
                    try:
                        host_stats[stat] = self.event_data.get(stat, {}).get(host, 0)
                    except AttributeError:  # in case event_data[stat] isn't a dict.
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

    @property
    def job_verbosity(self):
        return self.job.verbosity


class ProjectUpdateEvent(BasePlaybookEvent):

    VALID_KEYS = BasePlaybookEvent.VALID_KEYS + ['project_update_id']

    class Meta:
        app_label = 'main'
        ordering = ('pk',)
        index_together = [
            ('project_update', 'event'),
            ('project_update', 'uuid'),
            ('project_update', 'start_line'),
            ('project_update', 'end_line'),
        ]

    project_update = models.ForeignKey(
        'ProjectUpdate',
        related_name='project_update_events',
        on_delete=models.CASCADE,
        editable=False,
    )

    @property
    def host_name(self):
        return 'localhost'


class BaseCommandEvent(CreatedModifiedModel):
    '''
    An event/message logged from a command for each host.
    '''

    VALID_KEYS = [
        'event_data', 'created', 'counter', 'uuid', 'stdout', 'start_line',
        'end_line', 'verbosity'
    ]

    class Meta:
        abstract = True

    event_data = JSONField(
        blank=True,
        default={},
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

    def __str__(self):
        return u'%s @ %s' % (self.get_event_display(), self.created.isoformat())

    @classmethod
    def create_from_data(cls, **kwargs):
        # Convert the datetime for the event's creation
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

        sanitize_event_keys(kwargs, cls.VALID_KEYS)
        return cls.objects.create(**kwargs)

    def get_event_display(self):
        '''
        Needed for __unicode__
        '''
        return self.event

    def get_host_status_counts(self):
        return create_host_status_counts(getattr(self, 'event_data', {}))


class AdHocCommandEvent(BaseCommandEvent):

    VALID_KEYS = BaseCommandEvent.VALID_KEYS + ['ad_hoc_command_id', 'event']

    class Meta:
        app_label = 'main'
        ordering = ('-pk',)
        index_together = [
            ('ad_hoc_command', 'event'),
            ('ad_hoc_command', 'uuid'),
            ('ad_hoc_command', 'start_line'),
            ('ad_hoc_command', 'end_line'),
        ]

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

    event = models.CharField(
        max_length=100,
        choices=EVENT_CHOICES,
    )
    failed = models.BooleanField(
        default=False,
        editable=False,
    )
    changed = models.BooleanField(
        default=False,
        editable=False,
    )
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

    def get_absolute_url(self, request=None):
        return reverse('api:ad_hoc_command_event_detail', kwargs={'pk': self.pk}, request=request)

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


class InventoryUpdateEvent(BaseCommandEvent):

    VALID_KEYS = BaseCommandEvent.VALID_KEYS + ['inventory_update_id']

    class Meta:
        app_label = 'main'
        ordering = ('-pk',)
        index_together = [
            ('inventory_update', 'uuid'),
            ('inventory_update', 'start_line'),
            ('inventory_update', 'end_line'),
        ]

    inventory_update = models.ForeignKey(
        'InventoryUpdate',
        related_name='inventory_update_events',
        on_delete=models.CASCADE,
        editable=False,
    )

    @property
    def event(self):
        return 'verbose'

    @property
    def failed(self):
        return False

    @property
    def changed(self):
        return False


class SystemJobEvent(BaseCommandEvent):

    VALID_KEYS = BaseCommandEvent.VALID_KEYS + ['system_job_id']

    class Meta:
        app_label = 'main'
        ordering = ('-pk',)
        index_together = [
            ('system_job', 'uuid'),
            ('system_job', 'start_line'),
            ('system_job', 'end_line'),
        ]

    system_job = models.ForeignKey(
        'SystemJob',
        related_name='system_job_events',
        on_delete=models.CASCADE,
        editable=False,
    )

    @property
    def event(self):
        return 'verbose'

    @property
    def failed(self):
        return False

    @property
    def changed(self):
        return False
