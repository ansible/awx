# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import json
import logging
import shlex
import os
import os.path

# PyYAML
import yaml

# Django
from django.conf import settings
from django.db import models
from django.db import transaction
from django.core.exceptions import ValidationError
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

logger = logging.getLogger('awx.main.models.unified_jobs')


class UnifiedJobTemplate(PolymorphicModel, CommonModelNameNotUnique):
    '''
    Concrete base class for unified job templates.
    '''

    STATUS_CHOICES = [
        # from Project
        ('ok', 'OK'),
        ('missing', 'Missing'),
        ('never updated', 'Never Updated'),
        ('running', 'Running'),
        ('failed', 'Failed'),
        ('successful', 'Successful'),
        # from InventorySource
        ('none', _('No External Source')),
        ('never updated', _('Never Updated')),
        ('updating', _('Updating')),
        #('failed', _('Failed')),
        #('successful', _('Successful')),
    ]


    class Meta:
        app_label = 'main'
        unique_together = [('polymorphic_ctype', 'name')]

    old_pk = models.PositiveIntegerField(
        null=True,
        default=None,
        editable=False,
    )
    current_job = models.ForeignKey( # alias for current_update
        'UnifiedJob',
        null=True,
        default=None,
        editable=False,
        related_name='%(class)s_as_current_job+',
    )
    last_job = models.ForeignKey( # alias for last_update
        'UnifiedJob',
        null=True,
        default=None,
        editable=False,
        related_name='%(class)s_as_last_job+',
    )
    last_job_failed = models.BooleanField( # alias for last_update_failed
        default=False,
        editable=False,
    )
    last_job_run = models.DateTimeField( # alias for last_updated
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
    next_job_run = models.DateTimeField( # FIXME: Calculate from schedule.
        null=True,
        default=None,
        editable=False,
    )
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default='ok',
        editable=False,
    )
    
    # FIXME: Include code common to Project/InventorySource/JobTemplate


class UnifiedJob(PolymorphicModel, PrimordialModel):
    '''
    Concrete base class for unified job run by the task engine.
    '''

    LAUNCH_TYPE_CHOICES = [
        ('manual', _('Manual')),
        ('callback', _('Callback')),
        ('scheduled', _('Scheduled')),
        ('dependency', _('Dependency')),
    ]

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
    )
    launch_type = models.CharField(
        max_length=20,
        choices=LAUNCH_TYPE_CHOICES,
        default='manual',
        editable=False,
    )
    schedule = models.ForeignKey(
        'Schedule',
        null=True,
        default=None,
        editable=False,
    )
    depends_on = models.ManyToManyField(
        'self',
        editable=False,
        related_name='%(class)s_blocked_by+',
    )

    cancel_flag = models.BooleanField(
        blank=True,
        default=False,
        editable=False,
    )
    status = models.CharField(
        max_length=20,
        choices=TASK_STATUS_CHOICES,
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
    # FIXME: Add methods from CommonTask.
