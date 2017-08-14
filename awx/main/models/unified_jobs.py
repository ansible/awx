# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import codecs
import json
import logging
import re
import os
import os.path
from collections import OrderedDict
from StringIO import StringIO

# Django
from django.conf import settings
from django.db import models, connection
from django.core.exceptions import NON_FIELD_ERRORS
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now
from django.utils.encoding import smart_text
from django.apps import apps
from django.contrib.contenttypes.models import ContentType

# Django-Polymorphic
from polymorphic.models import PolymorphicModel

# Django-Celery
from djcelery.models import TaskMeta

# AWX
from awx.main.models.base import * # noqa
from awx.main.models.schedules import Schedule
from awx.main.models.mixins import ResourceMixin, TaskManagerUnifiedJobMixin
from awx.main.utils import (
    decrypt_field, _inventory_updates,
    copy_model_by_class, copy_m2m_relationships,
    get_type_for_model
)
from awx.main.redact import UriCleaner, REPLACE_STR
from awx.main.consumers import emit_channel_notification
from awx.main.fields import JSONField

__all__ = ['UnifiedJobTemplate', 'UnifiedJob']

logger = logging.getLogger('awx.main.models.unified_jobs')

CAN_CANCEL = ('new', 'pending', 'waiting', 'running')
ACTIVE_STATES = CAN_CANCEL


class UnifiedJobTemplate(PolymorphicModel, CommonModelNameNotUnique, NotificationFieldsModel):
    '''
    Concrete base class for unified job templates.
    '''

    # status inherits from related jobs. Thus, status must be able to be set to any status that a job status is settable to.
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

    COMMON_STATUS_CHOICES = JOB_STATUS_CHOICES + [
        ('never updated', _('Never Updated')),     # A job has never been run using this template.
    ]

    PROJECT_STATUS_CHOICES = COMMON_STATUS_CHOICES + [
        ('ok', _('OK')),                           # Project is not configured for SCM and path exists.
        ('missing', _('Missing')),                 # Project path does not exist.
    ]

    INVENTORY_SOURCE_STATUS_CHOICES = COMMON_STATUS_CHOICES + [
        ('none', _('No External Source')),      # Inventory source is not configured to update from an external source.
    ]

    JOB_TEMPLATE_STATUS_CHOICES = COMMON_STATUS_CHOICES

    DEPRECATED_STATUS_CHOICES = [
        # No longer used for Project / Inventory Source:
        ('updating', _('Updating')),            # Same as running.
    ]

    ALL_STATUS_CHOICES = OrderedDict(PROJECT_STATUS_CHOICES + INVENTORY_SOURCE_STATUS_CHOICES + JOB_TEMPLATE_STATUS_CHOICES + DEPRECATED_STATUS_CHOICES).items()

    # NOTE: Working around a django-polymorphic issue: https://github.com/django-polymorphic/django-polymorphic/issues/229
    _base_manager = models.Manager()

    class Meta:
        app_label = 'main'
        # unique_together here is intentionally commented out. Please make sure sub-classes of this model
        # contain at least this uniqueness restriction: SOFT_UNIQUE_TOGETHER = [('polymorphic_ctype', 'name')]
        #unique_together = [('polymorphic_ctype', 'name')]

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
    labels = models.ManyToManyField(
        "Label",
        blank=True,
        related_name='%(class)s_labels'
    )
    instance_groups = models.ManyToManyField(
        'InstanceGroup',
        blank=True,
    )

    def get_absolute_url(self, request=None):
        real_instance = self.get_real_instance()
        if real_instance != self:
            return real_instance.get_absolute_url(request=request)
        else:
            return ''

    def unique_error_message(self, model_class, unique_check):
        # If polymorphic_ctype is part of a unique check, return a list of the
        # remaining fields instead of the error message.
        if len(unique_check) >= 2 and 'polymorphic_ctype' in unique_check:
            return [x for x in unique_check if x != 'polymorphic_ctype']
        else:
            return super(UnifiedJobTemplate, self).unique_error_message(model_class, unique_check)

    @classmethod
    def invalid_user_capabilities_prefetch_models(cls):
        if cls != UnifiedJobTemplate:
            return []
        return ['project', 'inventorysource', 'systemjobtemplate']

    @classmethod
    def _submodels_with_roles(cls):
        ujt_classes = [c for c in cls.__subclasses__()
                       if c._meta.model_name not in ['inventorysource', 'systemjobtemplate']]
        ct_dict = ContentType.objects.get_for_models(*ujt_classes)
        return [ct.id for ct in ct_dict.values()]

    @classmethod
    def accessible_pk_qs(cls, accessor, role_field):
        '''
        A re-implementation of accessible pk queryset for the "normal" unified JTs.
        Does not return inventory sources or system JTs, these should
        be handled inside of get_queryset where it is utilized.
        '''
        # do not use this if in a subclass
        if cls != UnifiedJobTemplate:
            return super(UnifiedJobTemplate, cls).accessible_pk_qs(accessor, role_field)
        return ResourceMixin._accessible_pk_qs(
            cls, accessor, role_field, content_types=cls._submodels_with_roles())

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
        try:
            super(UnifiedJobTemplate, self).save(*args, **kwargs)
        except ValueError:
            # A fix for https://trello.com/c/S4rU1F21
            # Does not resolve the root cause. Tis merely a bandaid.
            if 'scm_delete_on_next_update' in update_fields:
                update_fields.remove('scm_delete_on_next_update')
                super(UnifiedJobTemplate, self).save(*args, **kwargs)


    def _get_current_status(self):
        # Override in subclasses as needed.
        if self.current_job and self.current_job.status:
            return self.current_job.status
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

    @property
    def notification_templates(self):
        '''
        Return notification_templates relevant to this Unified Job Template
        '''
        # NOTE: Derived classes should implement
        return NotificationTemplate.objects.none()

    def create_unified_job(self, **kwargs):
        '''
        Create a new unified job based on this unified job template.
        '''
        unified_job_class = self._get_unified_job_class()
        fields = self._get_unified_job_field_names()
        unified_job = copy_model_by_class(self, unified_job_class, fields, kwargs)

        eager_fields = kwargs.get('_eager_fields', None)
        if eager_fields:
            for fd, val in eager_fields.items():
                setattr(unified_job, fd, val)

        # Set the unified job template back-link on the job
        parent_field_name = unified_job_class._get_parent_field_name()
        setattr(unified_job, parent_field_name, self)

        # For JobTemplate-based jobs with surveys, add passwords to list for perma-redaction
        if hasattr(self, 'survey_spec') and getattr(self, 'survey_enabled', False):
            password_list = self.survey_password_variables()
            hide_password_dict = getattr(unified_job, 'survey_passwords', {})
            for password in password_list:
                hide_password_dict[password] = REPLACE_STR
            unified_job.survey_passwords = hide_password_dict

        unified_job.save()

        # Labels and extra credentials copied here
        from awx.main.signals import disable_activity_stream
        with disable_activity_stream():
            copy_m2m_relationships(self, unified_job, fields, kwargs=kwargs)
        return unified_job

    @classmethod
    def _get_unified_jt_copy_names(cls):
        return cls._get_unified_job_field_names()

    def copy_unified_jt(self):
        '''
        Returns saved object, including related fields.
        Create a copy of this unified job template.
        '''
        unified_jt_class = self.__class__
        fields = self._get_unified_jt_copy_names()
        unified_jt = copy_model_by_class(self, unified_jt_class, fields, {})

        time_now = now()
        unified_jt.name = unified_jt.name.split('@', 1)[0] + ' @ ' + time_now.strftime('%I:%M:%S %p')

        unified_jt.save()
        copy_m2m_relationships(self, unified_jt, fields)
        return unified_jt


class UnifiedJobTypeStringMixin(object):
    @classmethod
    def _underscore_to_camel(cls, word):
        return ''.join(x.capitalize() or '_' for x in word.split('_'))

    @classmethod
    def _camel_to_underscore(cls, word):
        return re.sub('(?!^)([A-Z]+)', r'_\1', word).lower()

    @classmethod
    def _model_type(cls, job_type):
        # Django >= 1.9
        #app = apps.get_app_config('main')
        model_str = cls._underscore_to_camel(job_type)
        try:
            return apps.get_model('main', model_str)
        except LookupError:
            print("Lookup model error")
            return None

    @classmethod
    def get_instance_by_type(cls, job_type, job_id):
        model = cls._model_type(job_type)
        if not model:
            return None
        return model.objects.get(id=job_id)

    def model_to_str(self):
        return UnifiedJobTypeStringMixin._camel_to_underscore(self.__class__.__name__)


class UnifiedJob(PolymorphicModel, PasswordFieldsModel, CommonModelNameNotUnique, UnifiedJobTypeStringMixin, TaskManagerUnifiedJobMixin):
    '''
    Concrete base class for unified job run by the task engine.
    '''

    STATUS_CHOICES = UnifiedJobTemplate.JOB_STATUS_CHOICES

    LAUNCH_TYPE_CHOICES = [
        ('manual', _('Manual')),            # Job was started manually by a user.
        ('relaunch', _('Relaunch')),        # Job was started via relaunch.
        ('callback', _('Callback')),        # Job was started via host callback.
        ('scheduled', _('Scheduled')),      # Job was started from a schedule.
        ('dependency', _('Dependency')),    # Job was started as a dependency of another job.
        ('workflow', _('Workflow')),        # Job was started from a workflow job.
        ('sync', _('Sync')),                # Job was started from a project sync.
        ('scm', _('SCM Update'))            # Job was created as an Inventory SCM sync.
    ]

    PASSWORD_FIELDS = ('start_args',)

    # NOTE: Working around a django-polymorphic issue: https://github.com/django-polymorphic/django-polymorphic/issues/229
    _base_manager = models.Manager()

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
    execution_node = models.TextField(
        blank=True,
        default='',
        editable=False,
        help_text=_("The node the job executed on."),
    )
    notifications = models.ManyToManyField(
        'Notification',
        editable=False,
        related_name='%(class)s_notifications',
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
        help_text=_("The date and time the job was queued for starting."),
    )
    finished = models.DateTimeField(
        null=True,
        default=None,
        editable=False,
        help_text=_("The date and time the job finished execution."),
    )
    elapsed = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        editable=False,
        help_text=_("Elapsed time in seconds that the job ran."),
    )
    job_args = prevent_search(models.TextField(
        blank=True,
        default='',
        editable=False,
    ))
    job_cwd = models.CharField(
        max_length=1024,
        blank=True,
        default='',
        editable=False,
    )
    job_env = prevent_search(JSONField(
        blank=True,
        default={},
        editable=False,
    ))
    job_explanation = models.TextField(
        blank=True,
        default='',
        editable=False,
        help_text=_("A status field to indicate the state of the job if it wasn't able to run and capture stdout"),
    )
    start_args = prevent_search(models.TextField(
        blank=True,
        default='',
        editable=False,
    ))
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
    labels = models.ManyToManyField(
        "Label",
        blank=True,
        related_name='%(class)s_labels'
    )
    instance_group = models.ForeignKey(
        'InstanceGroup',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
        help_text=_('The Rampart/Instance group the job was run under'),
    )

    def get_absolute_url(self, request=None):
        real_instance = self.get_real_instance()
        if real_instance != self:
            return real_instance.get_absolute_url(request=request)
        else:
            return ''

    def get_ui_url(self):
        real_instance = self.get_real_instance()
        if real_instance != self:
            return real_instance.get_ui_url()
        else:
            return ''

    @classmethod
    def _get_task_class(cls):
        raise NotImplementedError # Implement in subclasses.

    @classmethod
    def supports_isolation(cls):
        return False

    @classmethod
    def _get_parent_field_name(cls):
        return 'unified_job_template' # Override in subclasses.

    @classmethod
    def _get_unified_job_template_class(cls):
        '''
        Return subclass of UnifiedJobTemplate that applies to this unified job.
        '''
        raise NotImplementedError # Implement in subclass.

    def _global_timeout_setting(self):
        "Override in child classes, None value indicates this is not configurable"
        return None

    def _resources_sufficient_for_launch(self):
        return True

    def __unicode__(self):
        return u'%s-%s-%s' % (self.created, self.id, self.status)

    @property
    def log_format(self):
        return '{} {} ({})'.format(get_type_for_model(type(self)), self.id, self.status)

    def _get_parent_instance(self):
        return getattr(self, self._get_parent_field_name(), None)

    def _update_parent_instance_no_save(self, parent_instance, update_fields=[]):
        def parent_instance_set(key, val):
            setattr(parent_instance, key, val)
            if key not in update_fields:
                update_fields.append(key)

        if parent_instance:
            if self.status in ('pending', 'waiting', 'running'):
                if parent_instance.current_job != self:
                    parent_instance_set('current_job', self)
                # Update parent with all the 'good' states of it's child
                if parent_instance.status != self.status:
                    parent_instance_set('status', self.status)
            elif self.status in ('successful', 'failed', 'error', 'canceled'):
                if parent_instance.current_job == self:
                    parent_instance_set('current_job', None)
                parent_instance_set('last_job', self)
                parent_instance_set('last_job_failed', self.failed)

        return update_fields

    def _update_parent_instance(self):
        parent_instance = self._get_parent_instance()
        if parent_instance:
            update_fields = self._update_parent_instance_no_save(parent_instance)
            parent_instance.save(update_fields=update_fields)

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

        # If we have a start and finished time, and haven't already calculated
        # out the time that elapsed, do so.
        if self.started and self.finished and not self.elapsed:
            td = self.finished - self.started
            elapsed = (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10 ** 6) / (10 ** 6 * 1.0)
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
            except Exception:
                pass
        super(UnifiedJob, self).delete()

    def copy_unified_job(self):
        '''
        Returns saved object, including related fields.
        Create a copy of this unified job for the purpose of relaunch
        '''
        unified_job_class = self.__class__
        unified_jt_class = self._get_unified_job_template_class()
        parent_field_name = unified_job_class._get_parent_field_name()

        fields = unified_jt_class._get_unified_job_field_names() + [parent_field_name]
        unified_job = copy_model_by_class(self, unified_job_class, fields, {})
        unified_job.launch_type = 'relaunch'
        unified_job.save()

        # Labels coppied here
        copy_m2m_relationships(self, unified_job, fields)
        return unified_job

    def result_stdout_raw_handle(self, attempt=0):
        """Return a file-like object containing the standard out of the
        job's result.
        """
        msg = {
            'pending': 'Waiting for results...',
            'missing': 'stdout capture is missing',
        }
        if self.result_stdout_text:
            return StringIO(self.result_stdout_text)
        else:
            if not os.path.exists(self.result_stdout_file) or os.stat(self.result_stdout_file).st_size < 1:
                return StringIO(msg['missing' if self.finished else 'pending'])

            # There is a potential timing issue here, because another
            # process may be deleting the stdout file after it is written
            # to the database.
            #
            # Therefore, if we get an IOError (which generally means the
            # file does not exist), reload info from the database and
            # try again.
            try:
                return codecs.open(self.result_stdout_file, "r",
                                   encoding='utf-8')
            except IOError:
                if attempt < 3:
                    self.result_stdout_text = type(self).objects.get(id=self.id).result_stdout_text
                    return self.result_stdout_raw_handle(attempt=attempt + 1)
                else:
                    return StringIO(msg['missing' if self.finished else 'pending'])

    def _escape_ascii(self, content):
        # Remove ANSI escape sequences used to embed event data.
        content = re.sub(r'\x1b\[K(?:[A-Za-z0-9+/=]+\x1b\[\d+D)+\x1b\[K', '', content)
        # Remove ANSI color escape sequences.
        content = re.sub(r'\x1b[^m]*m', '', content)
        return content

    def _result_stdout_raw(self, redact_sensitive=False, escape_ascii=False):
        content = self.result_stdout_raw_handle().read()
        if redact_sensitive:
            content = UriCleaner.remove_sensitive(content)
        if escape_ascii:
            content = self._escape_ascii(content)
        return content

    @property
    def result_stdout_raw(self):
        return self._result_stdout_raw()

    @property
    def result_stdout(self):
        return self._result_stdout_raw(escape_ascii=True)

    @property
    def result_stdout_size(self):
        try:
            return os.stat(self.result_stdout_file).st_size
        except:
            return len(self.result_stdout)

    def _result_stdout_raw_limited(self, start_line=0, end_line=None, redact_sensitive=True, escape_ascii=False):
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

        if redact_sensitive:
            return_buffer = UriCleaner.remove_sensitive(return_buffer)
        if escape_ascii:
            return_buffer = self._escape_ascii(return_buffer)

        return return_buffer, start_actual, end_actual, absolute_end

    def result_stdout_raw_limited(self, start_line=0, end_line=None, redact_sensitive=False):
        return self._result_stdout_raw_limited(start_line, end_line, redact_sensitive)

    def result_stdout_limited(self, start_line=0, end_line=None, redact_sensitive=False):
        return self._result_stdout_raw_limited(start_line, end_line, redact_sensitive, escape_ascii=True)

    @property
    def spawned_by_workflow(self):
        return self.launch_type == 'workflow'

    @property
    def workflow_job_id(self):
        if self.spawned_by_workflow:
            try:
                return self.unified_job_node.workflow_job.pk
            except UnifiedJob.unified_job_node.RelatedObjectDoesNotExist:
                pass
        return None

    @property
    def workflow_node_id(self):
        if self.spawned_by_workflow:
            try:
                return self.unified_job_node.pk
            except UnifiedJob.unified_job_node.RelatedObjectDoesNotExist:
                pass
        return None

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
        if hasattr(self, 'extra_vars'):
            extra_vars = {}
            if isinstance(extra_data, dict):
                extra_vars = extra_data
            elif extra_data is None:
                return
            else:
                if extra_data == "":
                    return
                try:
                    extra_vars = json.loads(extra_data)
                except Exception as e:
                    logger.warn("Exception deserializing extra vars: " + str(e))
            evars = self.extra_vars_dict
            evars.update(extra_vars)
            self.update_fields(extra_vars=json.dumps(evars))

    @property
    def can_start(self):
        return bool(self.status in ('new', 'waiting'))

    @property
    def task_impact(self):
        raise NotImplementedError # Implement in subclass.

    def websocket_emit_data(self):
        ''' Return extra data that should be included when submitting data to the browser over the websocket connection '''
        websocket_data = dict()
        if self.spawned_by_workflow:
            websocket_data.update(dict(workflow_job_id=self.workflow_job_id,
                                       workflow_node_id=self.workflow_node_id))
        return websocket_data

    def _websocket_emit_status(self, status):
        try:
            status_data = dict(unified_job_id=self.id, status=status)
            if status == 'waiting':
                if self.instance_group:
                    status_data['instance_group_name'] = self.instance_group.name
                else:
                    status_data['instance_group_name'] = None
            status_data.update(self.websocket_emit_data())
            status_data['group_name'] = 'jobs'
            emit_channel_notification('jobs-status_changed', status_data)

            if self.spawned_by_workflow:
                status_data['group_name'] = "workflow_events"
                emit_channel_notification('workflow_events-' + str(self.workflow_job_id), status_data)
        except IOError:  # includes socket errors
            logger.exception('%s failed to emit channel msg about status change', self.log_format)

    def websocket_emit_status(self, status):
        connection.on_commit(lambda: self._websocket_emit_status(status))

    def notification_data(self):
        return dict(id=self.id,
                    name=self.name,
                    url=self.get_ui_url(),
                    created_by=smart_text(self.created_by),
                    started=self.started.isoformat() if self.started is not None else None,
                    finished=self.finished.isoformat() if self.finished is not None else None,
                    status=self.status,
                    traceback=self.result_traceback)

    def pre_start(self, **kwargs):
        if not self.can_start:
            self.job_explanation = u'%s is not in a startable state: %s, expecting one of %s' % (self._meta.verbose_name, self.status, str(('new', 'waiting')))
            self.save(update_fields=['job_explanation'])
            return (False, None)

        needed = self.get_passwords_needed_to_start()
        try:
            start_args = json.loads(decrypt_field(self, 'start_args'))
        except Exception:
            start_args = None

        if start_args in (None, ''):
            start_args = kwargs

        opts = dict([(field, start_args.get(field, '')) for field in needed])

        if not all(opts.values()):
            missing_fields = ', '.join([k for k,v in opts.items() if not v])
            self.job_explanation = u'Missing needed fields: %s.' % missing_fields
            self.save(update_fields=['job_explanation'])
            return (False, None)

        if 'extra_vars' in kwargs:
            self.handle_extra_data(kwargs['extra_vars'])

        return (True, opts)

    def start_celery_task(self, opts, error_callback, success_callback, queue):
        kwargs = {
            'link_error': error_callback,
            'link': success_callback,
            'queue': None,
            'task_id': None,
        }
        if not self.celery_task_id:
            raise RuntimeError("Expected celery_task_id to be set on model.")
        kwargs['task_id'] = self.celery_task_id
        task_class = self._get_task_class()
        from awx.main.models.ha import InstanceGroup
        ig = InstanceGroup.objects.get(name=queue)
        args = [self.pk]
        if ig.controller_id:
            if self.supports_isolation():  # case of jobs and ad hoc commands
                isolated_instance = ig.instances.order_by('-capacity').first()
                args.append(isolated_instance.hostname)
            else:  # proj & inv updates, system jobs run on controller
                queue = ig.controller.name
        kwargs['queue'] = queue
        task_class().apply_async(args, opts, **kwargs)

    def start(self, error_callback, success_callback, **kwargs):
        '''
        Start the task running via Celery.
        '''
        (res, opts) = self.pre_start(**kwargs)
        if res:
            self.start_celery_task(opts, error_callback, success_callback)
        return res

    def signal_start(self, **kwargs):
        """Notify the task runner system to begin work on this task."""

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
        if 'extra_vars' in kwargs:
            self.handle_extra_data(kwargs['extra_vars'])

        # Sanity check: If we are running unit tests, then run synchronously.
        if getattr(settings, 'CELERY_UNIT_TEST', False):
            return self.start(None, None, **kwargs)

        # Save the pending status, and inform the SocketIO listener.
        self.update_fields(start_args=json.dumps(kwargs), status='pending')
        self.websocket_emit_status("pending")

        from awx.main.scheduler.tasks import run_job_launch
        connection.on_commit(lambda: run_job_launch.delay(self.id))

        # Each type of unified job has a different Task class; get the
        # appropirate one.
        # task_type = get_type_for_model(self)

        # Actually tell the task runner to run this task.
        # FIXME: This will deadlock the task runner
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
                self.websocket_emit_status("canceled")
        except: # FIXME: Log this exception!
            if settings.DEBUG:
                raise

    def _build_job_explanation(self):
        if not self.job_explanation:
            return 'Previous Task Canceled: {"job_type": "%s", "job_name": "%s", "job_id": "%s"}' % \
                   (self.model_to_str(), self.name, self.id)
        return None

    def cancel(self, job_explanation=None, is_chain=False):
        if self.can_cancel:
            if not is_chain:
                map(lambda x: x.cancel(job_explanation=self._build_job_explanation(), is_chain=True), self.get_jobs_fail_chain())

            if not self.cancel_flag:
                self.cancel_flag = True
                cancel_fields = ['cancel_flag']
                if self.status in ('pending', 'waiting', 'new'):
                    self.status = 'canceled'
                    cancel_fields.append('status')
                if job_explanation is not None:
                    self.job_explanation = job_explanation
                    cancel_fields.append('job_explanation')
                self.save(update_fields=cancel_fields)
                self.websocket_emit_status("canceled")
            if settings.BROKER_URL.startswith('amqp://'):
                self._force_cancel()
        return self.cancel_flag

    @property
    def preferred_instance_groups(self):
        '''
        Return Instance/Rampart Groups preferred by this unified job templates
        '''
        if not self.unified_job_template:
            return []
        template_groups = [x for x in self.unified_job_template.instance_groups.all()]
        return template_groups

    @property
    def global_instance_groups(self):
        from awx.main.models.ha import InstanceGroup
        default_instance_group = InstanceGroup.objects.filter(name='tower')
        if default_instance_group.exists():
            return [default_instance_group.first()]
        return []
