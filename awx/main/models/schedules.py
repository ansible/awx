# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

import logging
import dateutil.rrule

# Django
from django.db import models
from django.db.models.query import QuerySet
from django.utils.timezone import now, make_aware, get_default_timezone

# AWX
from awx.main.models.base import *
from django.core.urlresolvers import reverse

logger = logging.getLogger('awx.main.models.schedule')

__all__ = ['Schedule']


class ScheduleFilterMethods(object):

    def enabled(self, enabled=True):
        return self.filter(enabled=enabled)

    def before(self, dt):
        return self.filter(next_run__lt=dt)

    def after(self, dt):
        return self.filter(next_run__gt=dt)

    def between(self, begin, end):
        return self.after(begin).before(end)


class ScheduleQuerySet(ScheduleFilterMethods, QuerySet):
    pass


class ScheduleManager(ScheduleFilterMethods, models.Manager):

    use_for_related_objects = True

    def get_query_set(self):
        return ScheduleQuerySet(self.model, using=self._db)


class Schedule(CommonModel):

    class Meta:
        app_label = 'main'
        ordering = ['-next_run']

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

    def __unicode__(self):
        return u'%s_t%s_%s_%s' % (self.name, self.unified_job_template.id, self.id, self.next_run)

    def get_absolute_url(self):
        return reverse('api:schedule_detail', args=(self.pk,))

    def update_computed_fields(self):
        future_rs = dateutil.rrule.rrulestr(self.rrule, forceset=True)
        next_run_actual = future_rs.after(now())

        self.next_run = next_run_actual
        if self.dtstart is None:
            self.dtstart = self.next_run
        if self.dtend is None and "until" in self.rrule.lower() or 'count' in self.rrule.lower():
            self.dtend = future_rs[-1]
        self.unified_job_template.update_computed_fields()

    def save(self, *args, **kwargs):
        # TODO: Check if new rrule, if so set dtstart and dtend to null
        self.update_computed_fields()
        super(Schedule, self).save(*args, **kwargs)
