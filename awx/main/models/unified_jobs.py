# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
from io import StringIO
import datetime
import codecs
import json
import logging
import os
import re
import socket
import subprocess
import tempfile
from collections import OrderedDict

# Django
from django.conf import settings
from django.db import models, connection
from django.core.exceptions import NON_FIELD_ERRORS
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now
from django.utils.encoding import smart_text
from django.contrib.contenttypes.models import ContentType

# REST Framework
from rest_framework.exceptions import ParseError

# Django-Polymorphic
from polymorphic.models import PolymorphicModel

# AWX
from awx.main.models.base import (
    CommonModelNameNotUnique,
    PasswordFieldsModel,
    NotificationFieldsModel,
    prevent_search
)
from awx.main.dispatch import get_local_queuename
from awx.main.dispatch.control import Control as ControlDispatcher
from awx.main.registrar import activity_stream_registrar
from awx.main.models.mixins import ResourceMixin, TaskManagerUnifiedJobMixin
from awx.main.utils import (
    camelcase_to_underscore, get_model_for_type,
    encrypt_dict, decrypt_field, _inventory_updates,
    copy_model_by_class, copy_m2m_relationships,
    get_type_for_model, parse_yaml_or_json, getattr_dne,
    polymorphic, schedule_task_manager
)
from awx.main.constants import ACTIVE_STATES, CAN_CANCEL
from awx.main.redact import UriCleaner, REPLACE_STR
from awx.main.consumers import emit_channel_notification
from awx.main.fields import JSONField, AskForField, OrderedManyToManyField

__all__ = ['UnifiedJobTemplate', 'UnifiedJob', 'StdoutMaxBytesExceeded']

logger = logging.getLogger('awx.main.models.unified_jobs')

# NOTE: ACTIVE_STATES moved to constants because it is used by parent modules


class UnifiedJobTemplate(PolymorphicModel, CommonModelNameNotUnique, NotificationFieldsModel):
    '''
    Concrete base class for unified job templates.
    '''

    # status inherits from related jobs. Thus, status must be able to be set to any status that a job status is settable to.
    JOB_STATUS_CHOICES = [
        ('new', _('New')),                  # Job has been created, but not started.
        ('pending', _('Pending')),          # Job is pending Task Manager processing (blocked by dependency req, capacity or a concurrent job)
        ('waiting', _('Waiting')),          # Job has been assigned to run on a specific node (and is about to run).
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

    class Meta:
        app_label = 'main'
        ordering = ('name',)
        # unique_together here is intentionally commented out. Please make sure sub-classes of this model
        # contain at least this uniqueness restriction: SOFT_UNIQUE_TOGETHER = [('polymorphic_ctype', 'name')]
        #unique_together = [('polymorphic_ctype', 'name', 'organization')]

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
        on_delete=polymorphic.SET_NULL,
    )
    status = models.CharField(
        max_length=32,
        choices=ALL_STATUS_CHOICES,
        default='ok',
        editable=False,
    )
    organization = models.ForeignKey(
        'Organization',
        blank=True,
        null=True,
        on_delete=polymorphic.SET_NULL,
        related_name='%(class)ss',
        help_text=_('The organization used to determine access to this template.'),
    )
    credentials = models.ManyToManyField(
        'Credential',
        related_name='%(class)ss',
    )
    labels = models.ManyToManyField(
        "Label",
        blank=True,
        related_name='%(class)s_labels'
    )
    instance_groups = OrderedManyToManyField(
        'InstanceGroup',
        blank=True,
        through='UnifiedJobTemplateInstanceGroupMembership'
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
        related_schedules = self.schedules.filter(enabled=True, next_run__isnull=False).order_by('-next_run')
        new_next_schedule = related_schedules.first()
        if new_next_schedule:
            if new_next_schedule.pk == self.next_schedule_id and new_next_schedule.next_run == self.next_job_run:
                return  # no-op, common for infrequent schedules
            self.next_schedule = new_next_schedule
            self.next_job_run = new_next_schedule.next_run
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

    @property
    def notification_templates(self):
        '''
        Return notification_templates relevant to this Unified Job Template
        '''
        # NOTE: Derived classes should implement
        from awx.main.models.notifications import NotificationTemplate
        return NotificationTemplate.objects.none()

    def create_unified_job(self, **kwargs):
        '''
        Create a new unified job based on this unified job template.
        '''
        new_job_passwords = kwargs.pop('survey_passwords', {})
        eager_fields = kwargs.pop('_eager_fields', None)

        # automatically encrypt survey fields
        if hasattr(self, 'survey_spec') and getattr(self, 'survey_enabled', False):
            password_list = self.survey_password_variables()
            encrypt_dict(kwargs.get('extra_vars', {}), password_list)

        unified_job_class = self._get_unified_job_class()
        fields = self._get_unified_job_field_names()
        parent_field_name = None
        if "_unified_job_class" in kwargs:
            # Special case where spawned job is different type than usual
            # Only used for slice jobs
            unified_job_class = kwargs.pop("_unified_job_class")
            fields = unified_job_class._get_unified_job_field_names() & fields
            parent_field_name = kwargs.pop('_parent_field_name')

        unallowed_fields = set(kwargs.keys()) - set(fields)
        validated_kwargs = kwargs.copy()
        if unallowed_fields:
            if parent_field_name is None:
                logger.warn('Fields {} are not allowed as overrides to spawn from {}.'.format(
                    ', '.join(unallowed_fields), self
                ))
            for f in unallowed_fields:
                validated_kwargs.pop(f)

        unified_job = copy_model_by_class(self, unified_job_class, fields, validated_kwargs)

        if eager_fields:
            for fd, val in eager_fields.items():
                setattr(unified_job, fd, val)

        # NOTE: slice workflow jobs _get_parent_field_name method
        # is not correct until this is set
        if not parent_field_name:
            parent_field_name = unified_job._get_parent_field_name()
        setattr(unified_job, parent_field_name, self)

        # For JobTemplate-based jobs with surveys, add passwords to list for perma-redaction
        if hasattr(self, 'survey_spec') and getattr(self, 'survey_enabled', False):
            for password in self.survey_password_variables():
                new_job_passwords[password] = REPLACE_STR
        if new_job_passwords:
            unified_job.survey_passwords = new_job_passwords
            kwargs['survey_passwords'] = new_job_passwords  # saved in config object for relaunch

        from awx.main.signals import disable_activity_stream, activity_stream_create
        with disable_activity_stream():
            # Don't emit the activity stream record here for creation,
            # because we haven't attached important M2M relations yet, like
            # credentials and labels
            unified_job.save()

        # Labels and credentials copied here
        if validated_kwargs.get('credentials'):
            Credential = UnifiedJob._meta.get_field('credentials').related_model
            cred_dict = Credential.unique_dict(self.credentials.all())
            prompted_dict = Credential.unique_dict(validated_kwargs['credentials'])
            # combine prompted credentials with JT
            cred_dict.update(prompted_dict)
            validated_kwargs['credentials'] = [cred for cred in cred_dict.values()]
            kwargs['credentials'] = validated_kwargs['credentials']

        with disable_activity_stream():
            copy_m2m_relationships(self, unified_job, fields, kwargs=validated_kwargs)

        if 'extra_vars' in validated_kwargs:
            unified_job.handle_extra_data(validated_kwargs['extra_vars'])

        # Create record of provided prompts for relaunch and rescheduling
        unified_job.create_config_from_prompts(kwargs, parent=self)

        # manually issue the create activity stream entry _after_ M2M relations
        # have been associated to the UJ
        if unified_job.__class__ in activity_stream_registrar.models:
            activity_stream_create(None, unified_job, True)

        return unified_job

    @classmethod
    def get_ask_mapping(cls):
        '''
        Creates dictionary that maps the unified job field (keys)
        to the field that enables prompting for the field (values)
        '''
        mapping = {}
        for field in cls._meta.fields:
            if isinstance(field, AskForField):
                mapping[field.allows_field] = field.name
        return mapping

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

    def _accept_or_ignore_job_kwargs(self, _exclude_errors=(), **kwargs):
        '''
        Override in subclass if template accepts _any_ prompted params
        '''
        errors = {}
        if kwargs:
            for field_name in kwargs.keys():
                errors[field_name] = [_("Field is not allowed on launch.")]
        return ({}, kwargs, errors)

    def accept_or_ignore_variables(self, data, errors=None, _exclude_errors=(), extra_passwords=None):
        '''
        If subclasses accept any `variables` or `extra_vars`, they should
        define _accept_or_ignore_variables to place those variables in the accepted dict,
        according to the acceptance rules of the template.
        '''
        if errors is None:
            errors = {}
        if not isinstance(data, dict):
            try:
                data = parse_yaml_or_json(data, silent_failure=False)
            except ParseError as exc:
                errors['extra_vars'] = [str(exc)]
                return ({}, data, errors)
        if hasattr(self, '_accept_or_ignore_variables'):
            # SurveyJobTemplateMixin cannot override any methods because of
            # resolution order, forced by how metaclass processes fields,
            # thus the need for hasattr check
            if extra_passwords:
                return self._accept_or_ignore_variables(
                    data, errors, _exclude_errors=_exclude_errors, extra_passwords=extra_passwords)
            else:
                return self._accept_or_ignore_variables(data, errors, _exclude_errors=_exclude_errors)
        elif data:
            errors['extra_vars'] = [
                _('Variables {list_of_keys} provided, but this template cannot accept variables.'.format(
                    list_of_keys=', '.join(data.keys())))]
        return ({}, data, errors)


class UnifiedJobTypeStringMixin(object):
    @classmethod
    def get_instance_by_type(cls, job_type, job_id):
        model = get_model_for_type(job_type)
        if not model:
            return None
        return model.objects.get(id=job_id)

    def model_to_str(self):
        return camelcase_to_underscore(self.__class__.__name__)


class UnifiedJobDeprecatedStdout(models.Model):

    class Meta:
        managed = False
        db_table = 'main_unifiedjob'

    result_stdout_text = models.TextField(
        null=True,
        editable=False,
    )


class StdoutMaxBytesExceeded(Exception):

    def __init__(self, total, supported):
        self.total = total
        self.supported = supported


class UnifiedJob(PolymorphicModel, PasswordFieldsModel, CommonModelNameNotUnique,
                 UnifiedJobTypeStringMixin, TaskManagerUnifiedJobMixin):
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
        ('webhook', _('Webhook')),          # Job was started from a webhook event.
        ('sync', _('Sync')),                # Job was started from a project sync.
        ('scm', _('SCM Update'))            # Job was created as an Inventory SCM sync.
    ]

    PASSWORD_FIELDS = ('start_args',)

    class Meta:
        app_label = 'main'
        ordering = ('id',)

    old_pk = models.PositiveIntegerField(
        null=True,
        default=None,
        editable=False,
    )
    emitted_events = models.PositiveIntegerField(
        default=0,
        editable=False,
    )
    unified_job_template = models.ForeignKey(
        'UnifiedJobTemplate',
        null=True, # Some jobs can be run without a template.
        default=None,
        editable=False,
        related_name='%(class)s_unified_jobs',
        on_delete=polymorphic.SET_NULL,
    )
    created = models.DateTimeField(
        default=None,
        editable=False,
        db_index=True,  # add an index, this is a commonly queried field
    )
    launch_type = models.CharField(
        max_length=20,
        choices=LAUNCH_TYPE_CHOICES,
        default='manual',
        editable=False,
        db_index=True
    )
    schedule = models.ForeignKey( # Which schedule entry was responsible for starting this job.
        'Schedule',
        null=True,
        default=None,
        editable=False,
        on_delete=polymorphic.SET_NULL,
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
    controller_node = models.TextField(
        blank=True,
        default='',
        editable=False,
        help_text=_("The instance that managed the isolated execution environment."),
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
        db_index=True,
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
    dependencies_processed = models.BooleanField(
        default=False,
        editable=False,
        help_text=_("If True, the task manager has already processed potential dependencies for this job.")
    )
    finished = models.DateTimeField(
        null=True,
        default=None,
        editable=False,
        help_text=_("The date and time the job finished execution."),
        db_index=True,
    )
    canceled_on = models.DateTimeField(
        null=True,
        default=None,
        editable=False,
        help_text=_("The date and time when the cancel request was sent."),
        db_index=True,
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
        default=dict,
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
        on_delete=polymorphic.SET_NULL,
        help_text=_('The Instance group the job was run under'),
    )
    organization = models.ForeignKey(
        'Organization',
        blank=True,
        null=True,
        on_delete=polymorphic.SET_NULL,
        related_name='%(class)ss',
        help_text=_('The organization used to determine access to this unified job.'),
    )
    credentials = models.ManyToManyField(
        'Credential',
        related_name='%(class)ss',
    )

    def get_absolute_url(self, request=None):
        RealClass = self.get_real_instance_class()
        if RealClass != UnifiedJob:
            return RealClass.get_absolute_url(RealClass(pk=self.pk), request=request)
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

    @property
    def can_run_containerized(self):
        return False

    def _get_parent_field_name(self):
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

    def __str__(self):
        return u'%s-%s-%s' % (self.created, self.id, self.status)

    @property
    def log_format(self):
        return '{} {} ({})'.format(get_type_for_model(type(self)), self.id, self.status)

    def _get_parent_instance(self):
        return getattr(self, self._get_parent_field_name(), None)

    def _update_parent_instance_no_save(self, parent_instance, update_fields=None):
        if update_fields is None:
            update_fields = []

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
        
        if self.cancel_flag and not self.canceled_on:
            # Record the 'canceled' time.
            self.canceled_on = now()
            if 'canceled_on' not in update_fields:
                update_fields.append('canceled_on')
        # Okay; we're done. Perform the actual save.
        result = super(UnifiedJob, self).save(*args, **kwargs)

        # If status changed, update the parent instance.
        if self.status != status_before:
            # Update parent outside of the transaction for Job w/ allow_simultaneous=True
            # This dodges lock contention at the expense of the foreign key not being
            # completely correct.
            if getattr(self, 'allow_simultaneous', False):
                connection.on_commit(self._update_parent_instance)
            else:
                self._update_parent_instance()

        # Done.
        return result

    def copy_unified_job(self, _eager_fields=None, **new_prompts):
        '''
        Returns saved object, including related fields.
        Create a copy of this unified job for the purpose of relaunch
        '''
        unified_job_class = self.__class__
        unified_jt_class = self._get_unified_job_template_class()
        parent_field_name = self._get_parent_field_name()
        fields = unified_jt_class._get_unified_job_field_names() | set([parent_field_name])

        create_data = {}
        if _eager_fields:
            create_data = _eager_fields.copy()
        create_data["launch_type"] = "relaunch"

        prompts = self.launch_prompts()
        if self.unified_job_template and (prompts is not None):
            prompts.update(new_prompts)
            prompts['_eager_fields'] = create_data
            unified_job = self.unified_job_template.create_unified_job(**prompts)
        else:
            unified_job = copy_model_by_class(self, unified_job_class, fields, {})
            for fd, val in create_data.items():
                setattr(unified_job, fd, val)
            unified_job.save()

            # Labels copied here
            from awx.main.signals import disable_activity_stream
            with disable_activity_stream():
                copy_m2m_relationships(self, unified_job, fields)

        return unified_job

    def launch_prompts(self):
        '''
        Return dictionary of prompts job was launched with
        returns None if unknown
        '''
        JobLaunchConfig = self._meta.get_field('launch_config').related_model
        try:
            config = self.launch_config
            return config.prompts_dict()
        except JobLaunchConfig.DoesNotExist:
            return None

    def create_config_from_prompts(self, kwargs, parent=None):
        '''
        Create a launch configuration entry for this job, given prompts
        returns None if it can not be created
        '''
        JobLaunchConfig = self._meta.get_field('launch_config').related_model
        config = JobLaunchConfig(job=self)
        if parent is None:
            parent = getattr(self, self._get_parent_field_name())
        if parent is None:
            return
        valid_fields = list(parent.get_ask_mapping().keys())
        # Special cases allowed for workflows
        if hasattr(self, 'extra_vars'):
            valid_fields.extend(['survey_passwords', 'extra_vars'])
        else:
            kwargs.pop('survey_passwords', None)
        for field_name, value in kwargs.items():
            if field_name not in valid_fields:
                raise Exception('Unrecognized launch config field {}.'.format(field_name))
            if field_name == 'credentials':
                continue
            key = field_name
            if key == 'extra_vars':
                key = 'extra_data'
            setattr(config, key, value)
        config.save()

        job_creds = set(kwargs.get('credentials', []))
        if 'credentials' in [field.name for field in parent._meta.get_fields()]:
            job_creds = job_creds - set(parent.credentials.all())
        if job_creds:
            config.credentials.add(*job_creds)
        return config

    @property
    def event_class(self):
        raise NotImplementedError()

    @property
    def job_type_name(self):
        return self.get_real_instance_class()._meta.verbose_name.replace(' ', '_')

    @property
    def result_stdout_text(self):
        related = UnifiedJobDeprecatedStdout.objects.get(pk=self.pk)
        return related.result_stdout_text or ''

    @result_stdout_text.setter
    def result_stdout_text(self, value):
        # TODO: remove this method once all stdout is based on jobevents
        # (because it won't be used for writing anymore)
        related = UnifiedJobDeprecatedStdout.objects.get(pk=self.pk)
        related.result_stdout_text = value
        related.save()

    @property
    def event_parent_key(self):
        tablename = self._meta.db_table
        return {
            'main_job': 'job_id',
            'main_adhoccommand': 'ad_hoc_command_id',
            'main_projectupdate': 'project_update_id',
            'main_inventoryupdate': 'inventory_update_id',
            'main_systemjob': 'system_job_id',
        }[tablename]

    def get_event_queryset(self):
        return self.event_class.objects.filter(**{self.event_parent_key: self.id})

    @property
    def event_processing_finished(self):
        '''
        Returns True / False, whether all events from job have been saved
        '''
        if self.status in ACTIVE_STATES:
            return False  # tally of events is only available at end of run
        try:
            event_qs = self.get_event_queryset()
        except NotImplementedError:
            return True  # Model without events, such as WFJT
        return self.emitted_events == event_qs.count()

    def result_stdout_raw_handle(self, enforce_max_bytes=True):
        """
        This method returns a file-like object ready to be read which contains
        all stdout for the UnifiedJob.

        If the size of the file is greater than
        `settings.STDOUT_MAX_BYTES_DISPLAY`, a StdoutMaxBytesExceeded exception
        will be raised.
        """
        max_supported = settings.STDOUT_MAX_BYTES_DISPLAY

        if enforce_max_bytes:
            # If enforce_max_bytes is True, we're not grabbing the whole file,
            # just the first <settings.STDOUT_MAX_BYTES_DISPLAY> bytes;
            # in this scenario, it's probably safe to use a StringIO.
            fd = StringIO()
        else:
            # If enforce_max_bytes = False, that means they're downloading
            # the entire file.  To avoid ballooning memory, let's write the
            # stdout content to a temporary disk location
            if not os.path.exists(settings.JOBOUTPUT_ROOT):
                os.makedirs(settings.JOBOUTPUT_ROOT)
            fd = tempfile.NamedTemporaryFile(
                mode='w',
                prefix='{}-{}-'.format(self.model_to_str(), self.pk),
                suffix='.out',
                dir=settings.JOBOUTPUT_ROOT,
                encoding='utf-8'
            )
            from awx.main.tasks import purge_old_stdout_files  # circular import
            purge_old_stdout_files.apply_async()

        # Before the addition of event-based stdout, older versions of
        # awx stored stdout as raw text blobs in a certain database column
        # (`main_unifiedjob.result_stdout_text`)
        # For older installs, this data still exists in the database; check for
        # it and use if it exists
        legacy_stdout_text = self.result_stdout_text
        if legacy_stdout_text:
            if enforce_max_bytes and len(legacy_stdout_text) > max_supported:
                raise StdoutMaxBytesExceeded(len(legacy_stdout_text), max_supported)
            fd.write(legacy_stdout_text)
            if hasattr(fd, 'name'):
                fd.flush()
                return codecs.open(fd.name, 'r', encoding='utf-8')
            else:
                # we just wrote to this StringIO, so rewind it
                fd.seek(0)
                return fd
        else:
            # Note: the code in this block _intentionally_ does not use the
            # Django ORM because of the potential size (many MB+) of
            # `main_jobevent.stdout`; we *do not* want to generate queries
            # here that construct model objects by fetching large gobs of
            # data (and potentially ballooning memory usage); instead, we
            # just want to write concatenated values of a certain column
            # (`stdout`) directly to a file

            with connection.cursor() as cursor:

                if enforce_max_bytes:
                    # detect the length of all stdout for this UnifiedJob, and
                    # if it exceeds settings.STDOUT_MAX_BYTES_DISPLAY bytes,
                    # don't bother actually fetching the data
                    total = self.get_event_queryset().aggregate(
                        total=models.Sum(models.Func(models.F('stdout'), function='LENGTH'))
                    )['total'] or 0
                    if total > max_supported:
                        raise StdoutMaxBytesExceeded(total, max_supported)

                # psycopg2's copy_expert writes bytes, but callers of this
                # function assume a str-based fd will be returned; decode
                # .write() calls on the fly to maintain this interface
                _write = fd.write
                fd.write = lambda s: _write(smart_text(s))

                cursor.copy_expert(
                    "copy (select stdout from {} where {}={} and stdout != '' order by start_line) to stdout".format(
                        self._meta.db_table + 'event',
                        self.event_parent_key,
                        self.id
                    ),
                    fd
                )

                if hasattr(fd, 'name'):
                    # If we're dealing with a physical file, use `sed` to clean
                    # up escaped line sequences
                    fd.flush()
                    subprocess.Popen("sed -i 's/\\\\r\\\\n/\\n/g' {}".format(fd.name), shell=True).wait()
                    return codecs.open(fd.name, 'r', encoding='utf-8')
                else:
                    # If we're dealing with an in-memory string buffer, use
                    # string.replace()
                    fd = StringIO(fd.getvalue().replace('\\r\\n', '\n'))
                    return fd

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

    def _result_stdout_raw_limited(self, start_line=0, end_line=None, redact_sensitive=True, escape_ascii=False):
        return_buffer = StringIO()
        if end_line is not None:
            end_line = int(end_line)
        stdout_lines = self.result_stdout_raw_handle().readlines()
        absolute_end = len(stdout_lines)
        for line in stdout_lines[int(start_line):end_line]:
            return_buffer.write(line)
        if int(start_line) < 0:
            start_actual = len(stdout_lines) + int(start_line)
            end_actual = len(stdout_lines)
        else:
            start_actual = int(start_line)
            if end_line is not None:
                end_actual = min(int(end_line), len(stdout_lines))
            else:
                end_actual = len(stdout_lines)

        return_buffer = return_buffer.getvalue()
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
    def workflow_job_id(self):
        workflow_job = self.get_workflow_job()
        if workflow_job:
            return workflow_job.pk
        return None

    @property
    def spawned_by_workflow(self):
        return self.launch_type == 'workflow'

    def get_workflow_job(self):
        if self.spawned_by_workflow:
            try:
                return self.unified_job_node.workflow_job
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

    def get_passwords_needed_to_start(self):
        return []

    def handle_extra_data(self, extra_data):
        if hasattr(self, 'extra_vars') and extra_data:
            extra_data_dict = {}
            try:
                extra_data_dict = parse_yaml_or_json(extra_data, silent_failure=False)
            except Exception as e:
                logger.warn("Exception deserializing extra vars: " + str(e))
            evars = self.extra_vars_dict
            evars.update(extra_data_dict)
            self.update_fields(extra_vars=json.dumps(evars))

    @property
    def can_start(self):
        return bool(self.status in ('new', 'waiting'))

    @property
    def can_schedule(self):
        if getattr(self, 'passwords_needed_to_start', None):
            return False
        if getattr(self, 'inventory', None) is None:
            return False
        JobLaunchConfig = self._meta.get_field('launch_config').related_model
        try:
            self.launch_config
            if self.unified_job_template is None:
                return False
            return True
        except JobLaunchConfig.DoesNotExist:
            return False

    @property
    def task_impact(self):
        raise NotImplementedError # Implement in subclass.

    def websocket_emit_data(self):
        ''' Return extra data that should be included when submitting data to the browser over the websocket connection '''
        websocket_data = dict(type=self.job_type_name)
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
            elif status in ['successful', 'failed', 'canceled'] and self.finished:
                status_data['finished'] = datetime.datetime.strftime(self.finished, "%Y-%m-%dT%H:%M:%S.%fZ")
            status_data.update(self.websocket_emit_data())
            status_data['group_name'] = 'jobs'
            if getattr(self, 'unified_job_template_id', None):
                status_data['unified_job_template_id'] = self.unified_job_template_id
            emit_channel_notification('jobs-status_changed', status_data)

            if self.spawned_by_workflow:
                status_data['group_name'] = "workflow_events"
                status_data['workflow_job_template_id'] = self.unified_job_template.id
                emit_channel_notification('workflow_events-' + str(self.workflow_job_id), status_data)
        except IOError:  # includes socket errors
            logger.exception('%s failed to emit channel msg about status change', self.log_format)

    def websocket_emit_status(self, status):
        connection.on_commit(lambda: self._websocket_emit_status(status))
        if hasattr(self, 'update_webhook_status'):
            connection.on_commit(lambda: self.update_webhook_status(status))

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

        # verify that any associated credentials aren't missing required field data
        missing_credential_inputs = []
        for credential in self.credentials.all():
            defined_fields = credential.credential_type.defined_fields
            for required in credential.credential_type.inputs.get('required', []):
                if required in defined_fields and not credential.has_input(required):
                    missing_credential_inputs.append(required)

        if missing_credential_inputs:
            self.job_explanation = '{} cannot start because Credential {} does not provide one or more required fields ({}).'.format(
                self._meta.verbose_name.title(),
                credential.name,
                ', '.join(sorted(missing_credential_inputs))
            )
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

        # Save the pending status, and inform the SocketIO listener.
        self.update_fields(start_args=json.dumps(kwargs), status='pending')
        self.websocket_emit_status("pending")

        schedule_task_manager()

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
    def actually_running(self):
        # returns True if the job is running in the appropriate dispatcher process
        running = False
        if all([
            self.status == 'running',
            self.celery_task_id,
            self.execution_node
        ]):
            # If the job is marked as running, but the dispatcher
            # doesn't know about it (or the dispatcher doesn't reply),
            # then cancel the job
            timeout = 5
            try:
                running = self.celery_task_id in ControlDispatcher(
                    'dispatcher', self.controller_node or self.execution_node
                ).running(timeout=timeout)
            except (socket.timeout, RuntimeError):
                logger.error('could not reach dispatcher on {} within {}s'.format(
                    self.execution_node, timeout
                ))
                running = False
        return running

    @property
    def can_cancel(self):
        return bool(self.status in CAN_CANCEL)

    def _build_job_explanation(self):
        if not self.job_explanation:
            return 'Previous Task Canceled: {"job_type": "%s", "job_name": "%s", "job_id": "%s"}' % \
                   (self.model_to_str(), self.name, self.id)
        return None

    def cancel(self, job_explanation=None, is_chain=False):
        if self.can_cancel:
            if not is_chain:
                for x in self.get_jobs_fail_chain():
                    x.cancel(job_explanation=self._build_job_explanation(), is_chain=True)

            if not self.cancel_flag:
                self.cancel_flag = True
                self.start_args = ''  # blank field to remove encrypted passwords
                cancel_fields = ['cancel_flag', 'start_args']
                if self.status in ('pending', 'waiting', 'new'):
                    self.status = 'canceled'
                    cancel_fields.append('status')
                if self.status == 'running' and not self.actually_running:
                    self.status = 'canceled'
                    cancel_fields.append('status')
                if job_explanation is not None:
                    self.job_explanation = job_explanation
                    cancel_fields.append('job_explanation')
                self.save(update_fields=cancel_fields)
                self.websocket_emit_status("canceled")
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

    def awx_meta_vars(self):
        '''
        The result of this method is used as extra_vars of a job launched
        by AWX, for purposes of client playbook hooks
        '''
        r = {}
        for name in ('awx', 'tower'):
            r['{}_job_id'.format(name)] = self.pk
            r['{}_job_launch_type'.format(name)] = self.launch_type

        created_by = getattr_dne(self, 'created_by')

        wj = self.get_workflow_job()
        if wj:
            schedule = getattr_dne(wj, 'schedule')
            for name in ('awx', 'tower'):
                r['{}_workflow_job_id'.format(name)] = wj.pk
                r['{}_workflow_job_name'.format(name)] = wj.name
                if schedule:
                    r['{}_parent_job_schedule_id'.format(name)] = schedule.pk
                    r['{}_parent_job_schedule_name'.format(name)] = schedule.name

        if not created_by:
            schedule = getattr_dne(self, 'schedule')
            if schedule:
                for name in ('awx', 'tower'):
                    r['{}_schedule_id'.format(name)] = schedule.pk
                    r['{}_schedule_name'.format(name)] = schedule.name

        if created_by:
            for name in ('awx', 'tower'):
                r['{}_user_id'.format(name)] = created_by.pk
                r['{}_user_name'.format(name)] = created_by.username
                r['{}_user_email'.format(name)] = created_by.email
                r['{}_user_first_name'.format(name)] = created_by.first_name
                r['{}_user_last_name'.format(name)] = created_by.last_name

        inventory = getattr_dne(self, 'inventory')
        if inventory:
            for name in ('awx', 'tower'):
                r['{}_inventory_id'.format(name)] = inventory.pk
                r['{}_inventory_name'.format(name)] = inventory.name

        return r

    def get_queue_name(self):
        return self.controller_node or self.execution_node or get_local_queuename()

    def is_isolated(self):
        return bool(self.controller_node)

    @property
    def is_containerized(self):
        return False
