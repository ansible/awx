# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import json
import logging
import re
import shlex
import os
import os.path

# PyYAML
import yaml

# Django
from django.conf import settings
from django.db import models
from django.db import transaction
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django.contrib.contenttypes.models import ContentType
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
from awx.main.utils import decrypt_field, get_type_for_model

__all__ = ['UnifiedJobTemplate', 'UnifiedJob']

logger = logging.getLogger('awx.main.models.unified_jobs')


class UnifiedJobTemplate(PolymorphicModel, CommonModelNameNotUnique):
    '''
    Concrete base class for unified job templates.
    '''

    STATUS_CHOICES = [
        # Common to all:
        ('never updated', 'Never Updated'),     # A job has never been run using this template.
        ('running', 'Running'),                 # A job is currently running (or pending/waiting) using this template.
        ('failed', 'Failed'),                   # The last completed job using this template failed (failed, error, canceled).
        ('successful', 'Successful'),           # The last completed job using this template succeeded.
        # For Project only:
        ('ok', 'OK'),                           # Project is not configured for SCM and path exists.
        ('missing', 'Missing'),                 # Project path does not exist.
        # For Inventory Source only:
        ('none', _('No External Source')),      # Inventory source is not configured to update from an external source.
        # No longer used for Project / Inventory Source:
        ('updating', _('Updating')),            # Same as running.
    ]

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
        choices=STATUS_CHOICES,
        default='ok',
        editable=False,
    )

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
        super(UnifiedJobTemplate, self).mark_inactive(save=save)

    def save(self, *args, **kwargs):
        # If update_fields has been specified, add our field names to it,
        # if it hasn't been specified, then we're just doing a normal save.
        update_fields = kwargs.get('update_fields', [])
        # Update status and last_updated fields.
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

    def create_unified_job(self, **kwargs):
        '''
        Create a new unified job based on this unified job template.
        '''
        save_unified_job = kwargs.pop('save', True)
        unified_job_class = self._get_unified_job_class()
        parent_field_name = unified_job_class._get_parent_field_name()
        kwargs.pop('%s_id' % parent_field_name, None)
        kwargs[parent_field_name] = self
        for field_name in self._get_unified_job_field_names():
            if field_name in kwargs:
                continue
            # Foreign keys can be specified as field_name or field_name_id.
            if hasattr(self, '%s_id' % field_name) and ('%s_id' % field_name) in kwargs:
                continue
            kwargs[field_name] = getattr(self, field_name)
        unified_job = unified_job_class(**kwargs)
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
        # If update_fields has been specified, add our field names to it,
        # if it hasn't been specified, then we're just doing a normal save.
        update_fields = kwargs.get('update_fields', [])
        # Get status before save...
        status_before = self.status or 'new'
        if self.pk:
            self_before = self.__class__.objects.get(pk=self.pk)
            if self_before.status != self.status:
                status_before = self_before.status
        failed = bool(self.status in ('failed', 'error', 'canceled'))
        if self.failed != failed:
            self.failed = failed
            if 'failed' not in update_fields:
                update_fields.append('failed')
        if self.status == 'running' and not self.started:
            self.started = now()
            if 'started' not in update_fields:
                update_fields.append('started')
        if self.status in ('successful', 'failed', 'error', 'canceled') and not self.finished:
            self.finished = now()
            if 'finished' not in update_fields:
                update_fields.append('finished')
        if self.started and self.finished and not self.elapsed:
            td = self.finished - self.started
            elapsed = (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / (10**6 * 1.0)
        else:
            elapsed = 0.0
        if self.elapsed != elapsed:
            self.elapsed = str(elapsed)
            if 'elapsed' not in update_fields:
                update_fields.append('elapsed')
        if self.unified_job_template != self._get_parent_instance():
            self.unified_job_template = self._get_parent_instance()
            if 'unified_job_template' not in update_fields:
                update_fields.append('unified_job_template')
        super(UnifiedJob, self).save(*args, **kwargs)
        # If status changed, update parent instance....
        if self.status != status_before:
            self._update_parent_instance()

    def delete(self):
        if self.result_stdout_file != "":
            try:
                os.remove(self.result_stdout_file)
            except Exception, e:
                pass
        super(UnifiedJob, self).delete()

    @property
    def result_stdout_raw(self):
        if self.result_stdout_file != "":
            if not os.path.exists(self.result_stdout_file):
                return "stdout capture is missing"
            with open(self.result_stdout_file, "r") as stdout_fd:
                return stdout_fd.read()
        else:
            return self.result_stdout_text

    @property
    def result_stdout(self):
        ansi_escape = re.compile(r'\x1b[^m]*m')
        return ansi_escape.sub('', self.result_stdout_raw)

    @property
    def celery_task(self):
        try:
            if self.celery_task_id:
                return TaskMeta.objects.get(task_id=self.celery_task_id)
        except TaskMeta.DoesNotExist:
            pass

    def get_passwords_needed_to_start(self):
        return []

    @property
    def can_start(self):
        return bool(self.status in ('new', 'waiting'))

    @property
    def task_impact(self):
        raise NotImplementedError # Implement in subclass.

    def is_blocked_by(self, task_object):
        ''' Given another task object determine if this task would be blocked by it '''
        raise NotImplementedError # Implement in subclass.

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
            self.job_explanation = u'Missing needed fields: %s' % missing_fields
            self.save(update_fields=['job_explanation'])
            return False
        task_class().apply_async((self.pk,), opts, link_error=error_callback)
        return True

    def signal_start(self, **kwargs):
        '''
        Notify the task runner system to begin work on this task.
        '''
        from awx.main.tasks import notify_task_runner
        if hasattr(settings, 'CELERY_UNIT_TEST'):
            return self.start(None, **kwargs)
        if not self.can_start:
            return False
        needed = self.get_passwords_needed_to_start()
        opts = dict([(field, kwargs.get(field, '')) for field in needed])
        if not all(opts.values()):
            return False
        self.update_fields(start_args=json.dumps(kwargs), status='pending')
        task_type = get_type_for_model(self)
        # notify_task_runner.delay(dict(task_type=task_type, id=self.id, metadata=kwargs))
        return True

    @property
    def can_cancel(self):
        return bool(self.status in ('pending', 'waiting', 'running'))

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
        except: # FIXME: Log this exception!
            if settings.DEBUG:
                raise

    def cancel(self):
        if self.can_cancel:
            if not self.cancel_flag:
                self.cancel_flag = True
                self.save(update_fields=['cancel_flag'])
            if settings.BROKER_URL.startswith('amqp://'):
                self._force_cancel()
        return self.cancel_flag
