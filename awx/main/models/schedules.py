# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

import logging
import dateutil.rrule

# Django
from django.db import models
from django.utils.timezone import now, make_aware, get_default_timezone

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
        editable=False,
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

    def update_dt_elements(self):
        future_rs = dateutil.rrule.rrulestr(self.rrule, forceset=True)
        next_run_actual = future_rs.after(now())

        self.next_run = next_run_actual
        if self.dtstart is None:
            self.dtstart = self.next_run
        if "until" in self.rrule.lower() or 'count' in self.rrule.lower():
            self.dtend = future_rs[-1]

    def save(self, *args, **kwargs):
        self.update_dt_elements()
        super(Schedule, self).save(*args, **kwargs)
        # update template next run details
