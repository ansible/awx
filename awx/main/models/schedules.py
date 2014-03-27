# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

import logging
import dateutil

# Django
from django.db import models

# AWX
from awx.main.models.base import *
from django.core.urlresolvers import reverse

logger = logging.getLogger('awx.main.models.schedule')

__all__ = ['Schedule']

class ScheduleManager(models.Manager):
    pass

class Schedule(CommonModel):

    class Meta:
        app_label = 'main'

    objects = ScheduleManager()

    unified_job_template = models.ForeignKey(
        'UnifiedJobTemplate',
        related_name='schedules',
        on_delete=models.CASCADE,
    )
    enabled = models.BooleanField(
        default=True,
    )
    dtstart = models.DateTimeField(
        null=True,
        default=None,
        editable=True,
    )
    dtend = models.DateTimeField(
        null=True,
        default=None,
        editable=False,
    )
    rrule = models.CharField(
        max_length=255,
    )
    next_run = models.DateTimeField(
        null=True,
        default=None,
        editable=False,
    )

    def get_absolute_url(self):
        return reverse('api:schedule_list')
        #return reverse('api:schedule_detail', args=(self.pk,))

    def save(self, *args, **kwargs):
        super(Schedule, self).save(*args, **kwargs)
