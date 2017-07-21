# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

import re
import logging
import datetime
import dateutil.rrule
import json

# Django
from django.db import models
from django.db.models.query import QuerySet
from django.utils.timezone import now, make_aware, get_default_timezone
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError

# AWX
from awx.api.versioning import reverse
from awx.main.models.base import * # noqa
from awx.main.utils import ignore_inventory_computed_fields
from awx.main.consumers import emit_channel_notification
from awx.main.fields import JSONField

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

    def get_queryset(self):
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
        help_text=_("Enables processing of this schedule.")
    )
    dtstart = models.DateTimeField(
        null=True,
        default=None,
        editable=False,
        help_text=_("The first occurrence of the schedule occurs on or after this time.")
    )
    dtend = models.DateTimeField(
        null=True,
        default=None,
        editable=False,
        help_text=_("The last occurrence of the schedule occurs before this time, aftewards the schedule expires.")
    )
    rrule = models.CharField(
        max_length=255,
        help_text=_("A value representing the schedules iCal recurrence rule.")
    )
    next_run = models.DateTimeField(
        null=True,
        default=None,
        editable=False,
        help_text=_("The next time that the scheduled action will run.")
    )
    extra_data = JSONField(
        blank=True,
        default={}
    )

    # extra_data is actually a string with a JSON payload in it. This
    # is technically OK because a string is a valid JSON. One day we will
    # enforce non-string JSON.
    def _clean_extra_data_system_jobs(self):
        extra_data = self.extra_data
        if not isinstance(extra_data, dict):
            try:
                extra_data = json.loads(self.extra_data)
            except:
                raise ValidationError(_("Expected JSON"))

        if extra_data and 'days' in extra_data:
            try:
                if type(extra_data['days']) is bool:
                    raise ValueError
                if float(extra_data['days']) != int(extra_data['days']):
                    raise ValueError
                days = int(extra_data['days'])
                if days < 0:
                    raise ValueError
            except ValueError:
                raise ValidationError(_("days must be a positive integer."))
        return self.extra_data

    def clean_extra_data(self):
        if not self.unified_job_template:
            return self.extra_data

        # Compare class by string name because it's hard to import SystemJobTemplate
        if type(self.unified_job_template).__name__ is not 'SystemJobTemplate':
            return self.extra_data

        return self._clean_extra_data_system_jobs()

    def __unicode__(self):
        return u'%s_t%s_%s_%s' % (self.name, self.unified_job_template.id, self.id, self.next_run)

    def get_absolute_url(self, request=None):
        return reverse('api:schedule_detail', kwargs={'pk': self.pk}, request=request)

    def update_computed_fields(self):
        future_rs = dateutil.rrule.rrulestr(self.rrule, forceset=True)
        next_run_actual = future_rs.after(now())

        self.next_run = next_run_actual
        try:
            self.dtstart = future_rs[0]
        except IndexError:
            self.dtstart = None
        self.dtend = None
        if 'until' in self.rrule.lower():
            match_until = re.match(".*?(UNTIL\=[0-9]+T[0-9]+Z)", self.rrule)
            until_date = match_until.groups()[0].split("=")[1]
            self.dtend = make_aware(datetime.datetime.strptime(until_date, "%Y%m%dT%H%M%SZ"), get_default_timezone())
        if 'count' in self.rrule.lower():
            self.dtend = future_rs[-1]
        emit_channel_notification('schedules-changed', dict(id=self.id, group_name='schedules'))
        with ignore_inventory_computed_fields():
            self.unified_job_template.update_computed_fields()

    def save(self, *args, **kwargs):
        self.update_computed_fields()
        super(Schedule, self).save(*args, **kwargs)
