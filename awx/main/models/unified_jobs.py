# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import codecs
import json
import logging
import re
import shlex
import os
import os.path
from StringIO import StringIO

# PyYAML
import yaml

# Django
from django.conf import settings
from django.db import models
from django.db import transaction
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django.contrib.contenttypes.models import ContentType
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now

# Django-JSONField
from jsonfield import JSONField

# Django-Polymorphic
from polymorphic import PolymorphicModel

# Django-Celery
from djcelery.models import TaskMeta

# AWX
from awx.main.models.base import *
from awx.main.models.schedules import Schedule
from awx.main.utils import decrypt_field, get_type_for_model, emit_websocket_notification, _inventory_updates

__all__ = ['UnifiedJobTemplate', 'UnifiedJob']

logger = logging.getLogger('awx.main.models.unified_jobs')

CAN_CANCEL = ('new', 'pending', 'waiting', 'running')


class UnifiedJobTemplate(PolymorphicModel, CommonModelNameNotUnique):
    '''
    Concrete base class for unified job templates.
    '''

    COMMON_STATUS_CHOICES = [
        ('never updated', 'Never Updated'),     # A job has never been run using this template.
        ('running', 'Running'),                 # A job is currently running (or pending/waiting) using this template.
        ('failed', 'Failed'),                   # The last completed job using this template failed (failed, error, canceled).
        ('successful', 'Successful'),           # The last completed job using this template succeeded.
    ]

    PROJECT_STATUS_CHOICES = COMMON_STATUS_CHOICES + [
        ('ok', 'OK'),                           # Project is not configured for SCM and path exists.
        ('missing', 'Missing'),                 # Project path does not exist.
    ]

    INVENTORY_SOURCE_STATUS_CHOICES = COMMON_STATUS_CHOICES + [
        ('none', _('No External Source')),      # Inventory source is not configured to update from an external source.
    ]

    JOB_TEMPLATE_STATUS_CHOICES = COMMON_STATUS_CHOICES

    DEPRECATED_STATUS_CHOICES = [
        # No longer used for Project / Inventory Source:
        ('updating', _('Updating')),            # Same as running.
    ]

    ALL_STATUS_CHOICES = SortedDict(PROJECT_STATUS_CHOICES + INVENTORY_SOURCE_STATUS_CHOICES + JOB_TEMPLATE_STATUS_CHOICES + DEPRECATED_STATUS_CHOICES).items()

    class Meta:
        app_label = 'main'
        unique_together = [('polymorphic_ctype', 'name')]

    old_pk = models.PositiveIntegerField(
        null=True,
        default=None,
        editable=False,
    )
    current_job = models.ForeignKey(
        'UnifiedJob',
        null=True,
        default=None,
        editable=False,
        related_name='%(class)s_as_current_job+',
        on_delete=models.SET_NULL,
    )
    last_job = models.ForeignKey(
        'UnifiedJob',
        null=True,
        default=None,
        editable=False,
        related_name='%(class)s_as_last_job+',
        on_delete=models.SET_NULL,
    )
    last_job_failed = models.BooleanField(
        default=False,
        editable=False,
    )
    last_job_run = models.DateTimeField(
        null=True,
        default=None,
        editable=False,
    )
    has_schedules = models.BooleanField(
        default=False,
        editable=False,
    )
    #on_missed_schedule = models.CharField(
    #    max_length=32,
    #    choices=[],
    #)
    next_job_run = models.DateTimeField(
        null=True,
        default=None,
        editable=False,
    )
    next_schedule = models.ForeignKey( # Schedule entry responsible for next_job_run.
        'Schedule',
        null=True,
        default=None,
        editable=False,
        related_name='%(class)s_as_next_schedule+',
        on_delete=models.SET_NULL,
    )
    status = models.CharField(
        max_length=32,
        choices=ALL_STATUS_CHOICES,
        default='ok',
        editable=False,
    )

    def get_absolute_url(self):
        real_instance = self.get_real_instance()
        if real_instance != self:
            return real_instance.get_absolute_url()
        else:
            return ''

    def unique_error_message(self, model_class, unique_check):
        # If polymorphic_ctype is part of a unique check, return a list of the
        # remaining fields instead of the error message.
        if len(unique_check) >= 2 and 'polymorphic_ctype' in unique_check:
            return [x for x in unique_check if x != 'polymorphic_ctype']
        else:
            return super(UnifiedJobTemplate, self).unique_error_message(model_class, unique_check)

    def _perform_unique_checks(self, unique_checks):
        # Handle the list of unique fields returned above. Replace with an
        # appropriate error message for the remaining field(s) in the unique
        # check and cleanup the errors dictionary.
        errors = super(UnifiedJobTemplate, self)._perform_unique_checks(unique_checks)
        for key, msgs in errors.items():
            if key != NON_FIELD_ERRORS:
                continue
            for msg in msgs:
                if isinstance(msg, (list, tuple)):
                    if len(msg) == 1:
                        new_key = msg[0]
                    else:
                        new_key = NON_FIELD_ERRORS
                    model_class = self.get_real_concrete_instance_class()
                    errors.setdefault(new_key, []).append(self.unique_error_message(model_class, msg))
            errors[key] = [x for x in msgs if not isinstance(x, (list, tuple))]
        for key, msgs in errors.items():
            if not msgs:
                del errors[key]
        return errors

    def validate_unique(self, exclude=None):
        # Make sure we set the polymorphic_ctype before validating, and omit
        # it from the list of excluded fields.
        self.pre_save_polymorphic()
        if exclude and 'polymorphic_ctype' in exclude:
            exclude = [x for x in exclude if x != 'polymorphic_ctype']
        return super(UnifiedJobTemplate, self).validate_unique(exclude)

    @property   # Alias for backwards compatibility.
    def current_update(self):
        return self.current_job

    @property   # Alias for backwards compatibility.
    def last_update(self):
        return self.last_job

    @property   # Alias for backwards compatibility.
    def last_update_failed(self):
        return self.last_job_failed

    @property   # Alias for backwards compatibility.
    def last_updated(self):
        return self.last_job_run

    def update_computed_fields(self):
        related_schedules = Schedule.objects.filter(enabled=True, unified_job_template=self, next_run__isnull=False).order_by('-next_run')
        if related_schedules.exists():
            self.next_schedule = related_schedules[0]
            self.next_job_run = related_schedules[0].next_run
            self.save(update_fields=['next_schedule', 'next_job_run'])

    def mark_inactive(self, save=True):
        '''
        When marking a unified job template inactive, also mark its schedules
        inactive.
        '''
        for schedule in self.schedules.filter(active=True):
            schedule.mark_inactive()
            schedule.enabled = False
            schedule.save()
        super(UnifiedJobTemplate, self).mark_inactive(save=save)

    def save(self, *args, **kwargs):
        # If update_fields has been specified, add our field names to it,
        # if it hasn't been specified, then we're just doing a normal save.
        update_fields = kwargs.get('update_fields', [])
        # Update status and last_updated fields.
        if not getattr(_inventory_updates, 'is_updating', False):
            updated_fields = self._set_status_and_last_job_run(save=False)
            for field in updated_fields:
                if field not in update_fields:
                    update_fields.append(field)
        # Do the actual save.
        super(UnifiedJobTemplate, self).save(*args, **kwargs)

    def _get_current_status(self):
        # Override in subclasses as needed.
        if self.current_job:
            return 'running'
        elif not self.last_job:
            return 'never updated'
        elif self.last_job_failed:
            return 'failed'
        else:
            return 'successful'

    def _get_last_job_run(self):
        # Override in subclasses as needed.
        if self.last_job:
            return self.last_job.finished

    def _set_status_and_last_job_run(self, save=True):
        status = self._get_current_status()
        last_job_run = self._get_last_job_run()
        return self.update_fields(status=status, last_job_run=last_job_run,
                                  save=save)

    def _can_update(self):
        # Override in subclasses as needed.
        return False

    @property
    def can_update(self):
        return self._can_update()

    def update(self, **kwargs):
        if self.can_update:
            unified_job = self.create_unified_job()
            unified_job.signal_start(**kwargs)
            return unified_job

    @classmethod
    def _get_unified_job_class(cls):
        '''
        Return subclass of UnifiedJob that is created from this template.
        '''
        raise NotImplementedError # Implement in subclass.

    @classmethod
    def _get_unified_job_field_names(cls):
        '''
        Return field names that should be copied from template to new job.
        '''
        raise NotImplementedError # Implement in subclass.

    def _update_unified_job_kwargs(self, **kwargs):
        '''
        Hook for subclasses to update kwargs.
        '''
        return kwargs   # Override if needed in subclass.

    def create_unified_job(self, **kwargs):
        '''
        Create a new unified job based on this unified job template.
        '''
        save_unified_job = kwargs.pop('save', True)
        unified_job_class = self._get_unified_job_class()
        parent_field_name = unified_job_class._get_parent_field_name()
        kwargs.pop('%s_id' % parent_field_name, None)
        create_kwargs = {}
        create_kwargs[parent_field_name] = self
        for field_name in self._get_unified_job_field_names():
            # Foreign keys can be specified as field_name or field_name_id.
            id_field_name = '%s_id' % field_name
            if hasattr(self, id_field_name):
                if field_name in kwargs:
                    value = kwargs[field_name]
                elif id_field_name in kwargs:
                    value = kwargs[id_field_name]
                else:
                    value = getattr(self, id_field_name)
                if hasattr(value, 'id'):
                    value = value.id
                create_kwargs[id_field_name] = value
            elif field_name in kwargs:
                create_kwargs[field_name] = kwargs[field_name]
            elif hasattr(self, field_name):
                create_kwargs[field_name] = getattr(self, field_name)
        kwargs = self._update_unified_job_kwargs(**create_kwargs)
        unified_job = unified_job_class(**create_kwargs)
        if save_unified_job:
            unified_job.save()
        return unified_job


class UnifiedJob(PolymorphicModel, PasswordFieldsModel, CommonModelNameNotUnique):
    '''
    Concrete base class for unified job run by the task engine.
    '''

    STATUS_CHOICES = [
        ('new', _('New')),                  # Job has been created, but not started.
        ('pending', _('Pending')),          # Job has been queued, but is not yet running.
        ('waiting', _('Waiting')),          # Job is waiting on an update/dependency.
        ('running', _('Running')),          # Job is currently running.
        ('successful', _('Successful')),    # Job completed successfully.
        ('failed', _('Failed')),            # Job completed, but with failures.
        ('error', _('Error')),              # The job was unable to run.
        ('canceled', _('Canceled')),        # The job was canceled before completion.
    ]

    LAUNCH_TYPE_CHOICES = [
        ('manual', _('Manual')),            # Job was started manually by a user.
        ('callback', _('Callback')),        # Job was started via host callback.
        ('scheduled', _('Scheduled')),      # Job was started from a schedule.
        ('dependency', _('Dependency')),    # Job was started as a dependency of another job.
    ]

    PASSWORD_FIELDS = ('start_args',)

    class Meta:
        app_label = 'main'

    old_pk = models.PositiveIntegerField(
        null=True,
        default=None,
        editable=False,
    )
    unified_job_template = models.ForeignKey(
        'UnifiedJobTemplate',
        null=True, # Some jobs can be run without a template.
        default=None,
        editable=False,
        related_name='%(class)s_unified_jobs',
        on_delete=models.SET_NULL,
    )
    launch_type = models.CharField(
        max_length=20,
        choices=LAUNCH_TYPE_CHOICES,
        default='manual',
        editable=False,
    )
    schedule = models.ForeignKey( # Which schedule entry was responsible for starting this job.
        'Schedule',
        null=True,
        default=None,
        editable=False,
        on_delete=models.SET_NULL,
    )
    dependent_jobs = models.ManyToManyField(
        'self',
        editable=False,
        related_name='%(class)s_blocked_jobs+',
    )
    cancel_flag = models.BooleanField(
        blank=True,
        default=False,
        editable=False,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        editable=False,
    )
    failed = models.BooleanField(
        default=False,
        editable=False,
    )
    started = models.DateTimeField(
        null=True,
        default=None,
        editable=False,
    )
    finished = models.DateTimeField(
        null=True,
        default=None,
        editable=False,
    )
    elapsed = models.DecimalField(
        max_digits=12,
        decimal_places=3,
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
    job_explanation = models.TextField(
        blank=True,
        default='',
        editable=False,
    )
    start_args = models.TextField(
        blank=True,
        default='',
        editable=False,
    )
    result_stdout_text = models.TextField(
        blank=True,
        default='',
        editable=False,
    )
    result_stdout_file = models.TextField( # FilePathfield?
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

    def get_absolute_url(self):
        real_instance = self.get_real_instance()
        if real_instance != self:
            return real_instance.get_absolute_url()
        else:
            return ''

    @classmethod
    def _get_task_class(cls):
        raise NotImplementedError # Implement in subclasses.

    @classmethod
    def _get_parent_field_name(cls):
        return 'unified_job_template' # Override in subclasses.

    def __unicode__(self):
        return u'%s-%s-%s' % (self.created, self.id, self.status)

    def _get_parent_instance(self):
        return getattr(self, self._get_parent_field_name())

    def _update_parent_instance(self):
        parent_instance = self._get_parent_instance()
        if parent_instance:
            if self.status in ('pending', 'waiting', 'running'):
                if parent_instance.current_job != self:
                    parent_instance.current_job = self
                    parent_instance.save(update_fields=['current_job'])
            elif self.status in ('successful', 'failed', 'error', 'canceled'):
                if parent_instance.current_job == self:
                    parent_instance.current_job = None
                parent_instance.last_job = self
                parent_instance.last_job_failed = self.failed
                parent_instance.save(update_fields=['current_job',
                                                    'last_job',
                                                    'last_job_failed'])

    def save(self, *args, **kwargs):
        """Save the job, with current status, to the database.
        Ensure that all data is consistent before doing so.
        """
        # If update_fields has been specified, add our field names to it,
        # if it hasn't been specified, then we're just doing a normal save.
        update_fields = kwargs.get('update_fields', [])

        # Get status before save...
        status_before = self.status or 'new'

        # If this job already exists in the database, retrieve a copy of
        # the job in its prior state.
        if self.pk:
            self_before = self.__class__.objects.get(pk=self.pk)
            if self_before.status != self.status:
                status_before = self_before.status

        # Sanity check: Is this a failure? Ensure that the failure value
        # matches the status.
        failed = bool(self.status in ('failed', 'error', 'canceled'))
        if self.failed != failed:
            self.failed = failed
            if 'failed' not in update_fields:
                update_fields.append('failed')

        # Sanity check: Has the job just started? If so, mark down its start
        # time.
        if self.status == 'running' and not self.started:
            self.started = now()
            if 'started' not in update_fields:
                update_fields.append('started')

        # Sanity check: Has the job just completed? If so, mark down its
        # completion time, and record its output to the database.
        if self.status in ('successful', 'failed', 'error', 'canceled') and not self.finished:
            # Record the `finished` time.
            self.finished = now()
            if 'finished' not in update_fields:
                update_fields.append('finished')

            # Take the output from the filesystem and record it in the
            # database.
            stdout = self.result_stdout_raw_handle()
            if not isinstance(stdout, StringIO):
                self.result_stdout_text = stdout.read()
                if 'result_stdout_text' not in update_fields:
                    update_fields.append('result_stdout_text')

                # Attempt to delete the job output from the filesystem if it
                # was moved to the database.
                if self.result_stdout_file:
                    try:
                        os.remove(self.result_stdout_file)
                        self.result_stdout_file = ''
                        if 'result_stdout_file' not in update_fields:
                            update_fields.append('result_stdout_file')
                    except:
                        pass  # Meh. We don't care that much.

        # If we have a start and finished time, and haven't already calculated
        # out the time that elapsed, do so.
        if self.started and self.finished and not self.elapsed:
            td = self.finished - self.started
            elapsed = (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / (10**6 * 1.0)
        else:
            elapsed = 0.0
        if self.elapsed != elapsed:
            self.elapsed = str(elapsed)
            if 'elapsed' not in update_fields:
                update_fields.append('elapsed')

        # Ensure that the job template information is current.
        if self.unified_job_template != self._get_parent_instance():
            self.unified_job_template = self._get_parent_instance()
            if 'unified_job_template' not in update_fields:
                update_fields.append('unified_job_template')

        # Okay; we're done. Perform the actual save.
        result = super(UnifiedJob, self).save(*args, **kwargs)

        # If status changed, update the parent instance.
        if self.status != status_before:
            self._update_parent_instance()

        # Done.
        return result

    def delete(self):
        if self.result_stdout_file != "":
            try:
                os.remove(self.result_stdout_file)
            except Exception, e:
                pass
        super(UnifiedJob, self).delete()

    def result_stdout_raw_handle(self):
        """Return a file-like object containing the standard out of the
        job's result.
        """
        if self.result_stdout_text:
            return StringIO(self.result_stdout_text)
        else:
            if not os.path.exists(self.result_stdout_file):
                return StringIO("stdout capture is missing")
            return codecs.open(self.result_stdout_file, "r", encoding='utf-8')

    @property
    def result_stdout_raw(self):
        return self.result_stdout_raw_handle().read()

    @property
    def result_stdout(self):
        ansi_escape = re.compile(r'\x1b[^m]*m')
        return ansi_escape.sub('', self.result_stdout_raw)

    def result_stdout_raw_limited(self, start_line=0, end_line=None):
        return_buffer = u""
        if end_line is not None:
            end_line = int(end_line)
        stdout_lines = self.result_stdout_raw_handle().readlines()
        absolute_end = len(stdout_lines)
        for line in stdout_lines[int(start_line):end_line]:
            return_buffer += line
        if int(start_line) < 0:
            start_actual = len(stdout_lines) + int(start_line)
            end_actual = len(stdout_lines)
        else:
            start_actual = int(start_line)
            if end_line is not None:
                end_actual = min(int(end_line), len(stdout_lines))
            else:
                end_actual = len(stdout_lines)
        return return_buffer, start_actual, end_actual, absolute_end

    def result_stdout_limited(self, start_line=0, end_line=None):
        ansi_escape = re.compile(r'\x1b[^m]*m')
        content, start, end, absolute_end = self.result_stdout_raw_limited(start_line, end_line)
        return ansi_escape.sub('', content), start, end, absolute_end

    @property
    def celery_task(self):
        try:
            if self.celery_task_id:
                return TaskMeta.objects.get(task_id=self.celery_task_id)
        except TaskMeta.DoesNotExist:
            pass

    def get_passwords_needed_to_start(self):
        return []

    def handle_extra_data(self, extra_data):
        return

    @property
    def can_start(self):
        return bool(self.status in ('new', 'waiting'))

    @property
    def task_impact(self):
        raise NotImplementedError # Implement in subclass.

    def is_blocked_by(self, task_object):
        ''' Given another task object determine if this task would be blocked by it '''
        raise NotImplementedError # Implement in subclass.

    def socketio_emit_data(self):
        ''' Return extra data that should be included when submitting data to the browser over the websocket connection '''
        return {}

    def socketio_emit_status(self, status):
        status_data = dict(unified_job_id=self.id, status=status)
        status_data.update(self.socketio_emit_data())
        emit_websocket_notification('/socket.io/jobs', 'status_changed', status_data)

    def generate_dependencies(self, active_tasks):
        ''' Generate any tasks that the current task might be dependent on given a list of active
            tasks that might preclude creating one'''
        return []

    def start(self, error_callback, **kwargs):
        '''
        Start the task running via Celery.
        '''
        task_class = self._get_task_class()
        if not self.can_start:
            self.job_explanation = u'%s is not in a startable status: %s, expecting one of %s' % (self._meta.verbose_name, self.status, str(('new', 'waiting')))
            self.save(update_fields=['job_explanation'])
            return False
        needed = self.get_passwords_needed_to_start()
        try:
            start_args = json.loads(decrypt_field(self, 'start_args'))
        except Exception, e:
            start_args = None
        if start_args in (None, ''):
            start_args = kwargs
        opts = dict([(field, start_args.get(field, '')) for field in needed])
        if not all(opts.values()):
            missing_fields = ', '.join([k for k,v in opts.items() if not v])
            self.job_explanation = u'Missing needed fields: %s.' % missing_fields
            self.save(update_fields=['job_explanation'])
            return False
        task_class().apply_async((self.pk,), opts, link_error=error_callback)
        return True

    def signal_start(self, **kwargs):
        """Notify the task runner system to begin work on this task."""

        # Sanity check: If we are running unit tests, then run synchronously.
        if getattr(settings, 'CELERY_UNIT_TEST', False):
            return self.start(None, **kwargs)

        # Sanity check: Are we able to start the job? If not, do not attempt
        # to do so.
        if not self.can_start:
            return False

        # Get any passwords or other data that are prerequisites to running
        # the job.
        needed = self.get_passwords_needed_to_start()
        opts = dict([(field, kwargs.get(field, '')) for field in needed])
        if not all(opts.values()):
            return False
        extra_data = dict([(field, kwargs[field]) for field in kwargs
                           if field not in needed])
        self.handle_extra_data(extra_data)

        # Save the pending status, and inform the SocketIO listener.
        self.update_fields(start_args=json.dumps(kwargs), status='pending')
        self.socketio_emit_status("pending")

        # Each type of unified job has a different Task class; get the
        # appropirate one.
        task_type = get_type_for_model(self)

        # Actually tell the task runner to run this task.
        # NOTE: This will deadlock the task runner
        #from awx.main.tasks import notify_task_runner
        #notify_task_runner.delay({'id': self.id, 'metadata': kwargs,
        #                          'task_type': task_type})

        # Done!
        return True

    @property
    def can_cancel(self):
        return bool(self.status in CAN_CANCEL)

    def _force_cancel(self):
        # Update the status to 'canceled' if we can detect that the job
        # really isn't running (i.e. celery has crashed or forcefully
        # killed the worker).
        task_statuses = ('STARTED', 'SUCCESS', 'FAILED', 'RETRY', 'REVOKED')
        try:
            taskmeta = self.celery_task
            if not taskmeta or taskmeta.status not in task_statuses:
                return
            from celery import current_app
            i = current_app.control.inspect()
            for v in (i.active() or {}).values():
                if taskmeta.task_id in [x['id'] for x in v]:
                    return
            for v in (i.reserved() or {}).values():
                if taskmeta.task_id in [x['id'] for x in v]:
                    return
            for v in (i.revoked() or {}).values():
                if taskmeta.task_id in [x['id'] for x in v]:
                    return
            for v in (i.scheduled() or {}).values():
                if taskmeta.task_id in [x['id'] for x in v]:
                    return
            instance = self.__class__.objects.get(pk=self.pk)
            if instance.can_cancel:
                instance.status = 'canceled'
                update_fields = ['status']
                if not instance.job_explanation:
                    instance.job_explanation = 'Forced cancel'
                    update_fields.append('job_explanation')
                instance.save(update_fields=update_fields)
                self.socketio_emit_status("canceled")
        except: # FIXME: Log this exception!
            if settings.DEBUG:
                raise

    def cancel(self):
        if self.can_cancel:
            if not self.cancel_flag:
                self.cancel_flag = True
                self.status = 'canceled'
                self.save(update_fields=['cancel_flag', 'status'])
                self.socketio_emit_status("canceled")
            if settings.BROKER_URL.startswith('amqp://'):
                self._force_cancel()
        return self.cancel_flag
