# Copyright (c) 2015 Ansible, Inc. (formerly AnsibleWorks, Inc.)
# All Rights Reserved.

import re
import logging
import datetime
import dateutil.rrule

# Django
from django.db import models
from django.db.models.query import QuerySet
from django.utils.timezone import now, make_aware, get_default_timezone

# Django-JSONField
from jsonfield import JSONField

# AWX
from awx.main.models.base import * # noqa
from awx.main.utils import ignore_inventory_computed_fields, emit_websocket_notification
from django.core.urlresolvers import reverse

logger = logging.getLogger('awx.main.models.schedule')

__all__ = ['Schedule']


class ScheduleFilterMethods(object):

    def enabled(self, enabled=True):
        return self.filter(enabled=enabled, active=enabled)

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
    extra_data = JSONField(
        blank=True,
        default={}
    )

    def __unicode__(self):
        return u'%s_t%s_%s_%s' % (self.name, self.unified_job_template.id, self.id, self.next_run)

    def get_absolute_url(self):
        return reverse('api:schedule_detail', args=(self.pk,))

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
        emit_websocket_notification('/socket.io/schedules', 'schedule_changed', dict(id=self.id))
        with ignore_inventory_computed_fields():
            self.unified_job_template.update_computed_fields()

    def save(self, *args, **kwargs):
        self.update_computed_fields()
        super(Schedule, self).save(*args, **kwargs)
