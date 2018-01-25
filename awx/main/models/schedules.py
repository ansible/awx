# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

import re
import logging
import datetime
import dateutil.rrule
from dateutil.tz import gettz, datetime_exists

# Django
from django.db import models
from django.db.models.query import QuerySet
from django.utils.timezone import now, make_aware
from django.utils.translation import ugettext_lazy as _

# AWX
from awx.api.versioning import reverse
from awx.main.models.base import * # noqa
from awx.main.models.jobs import LaunchTimeConfig
from awx.main.utils import ignore_inventory_computed_fields
from awx.main.consumers import emit_channel_notification

import pytz
import six


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


class Schedule(CommonModel, LaunchTimeConfig):

    TZID_REGEX = re.compile(
        "^(DTSTART;TZID=(?P<tzid>[^:]+)(?P<stamp>\:[0-9]+T[0-9]+))(?P<rrule> .*)$"
    )

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

    @classmethod
    def rrulestr(cls, rrule, **kwargs):
        """
        Apply our own custom rrule parsing logic.  This applies some extensions
        and limitations to parsing that are specific to our supported
        implementation.  Namely:

        * python-dateutil doesn't _natively_ support `DTSTART;TZID=`; this
          function parses out the TZID= component and uses it to produce the
          `tzinfos` keyword argument to `dateutil.rrule.rrulestr()`. In this
          way, we translate:

          DTSTART;TZID=America/New_York:20180601T120000 RRULE:FREQ=DAILY;INTERVAL=1

          ...into...

          DTSTART:20180601T120000TZID RRULE:FREQ=DAILY;INTERVAL=1

          ...and we pass a hint about the local timezone to dateutil's parser:
          `dateutil.rrule.rrulestr(rrule, {
              'tzinfos': {
                  'TZID': dateutil.tz.gettz('America/New_York')
                }
           })`

          it's possible that we can remove the custom code that performs this
          parsing if TZID= gains support in upstream dateutil:
          https://github.com/dateutil/dateutil/pull/615

        * RFC5545 specifies that: if the "DTSTART" property is specified as
          a date with local time (in our case, TZID=), then the UNTIL rule part
          MUST also be treated as a date with local time.  If the "DTSTART"
          property is specified as a date with UTC time (with a Z suffix),
          then the UNTIL rule part MUST be specified as a date with UTC time.

          this function provides additional parsing to translate RRULES like this:

          DTSTART;TZID=America/New_York:20180601T120000 RRULE:FREQ=DAILY;INTERVAL=1;UNTIL=20180602T170000

          ...into this (under the hood):

          DTSTART;TZID=America/New_York:20180601T120000 RRULE:FREQ=DAILY;INTERVAL=1;UNTIL=20180602T210000Z
        """
        source_rrule = rrule
        kwargs['tzinfos'] = {}
        match = cls.TZID_REGEX.match(rrule)
        if match is not None:
            rrule = cls.TZID_REGEX.sub("DTSTART\g<stamp>TZI\g<rrule>", rrule)
            timezone = gettz(match.group('tzid'))
            if 'until' in rrule.lower():
                # if DTSTART;TZID= is used, coerce "naive" UNTIL values
                # to the proper UTC date
                match_until = re.match(".*?(?P<until>UNTIL\=[0-9]+T[0-9]+)(?P<utcflag>Z?)", rrule)
                until_date = match_until.group('until').split("=")[1]
                if len(match_until.group('utcflag')):
                    raise ValueError(six.text_type(
                        _('invalid rrule `{}` includes TZINFO= stanza and UTC-based UNTIL clause').format(source_rrule)
                    ))  # noqa
                localized = make_aware(
                    datetime.datetime.strptime(until_date, "%Y%m%dT%H%M%S"),
                    timezone
                )
                utc = localized.astimezone(pytz.utc).strftime('%Y%m%dT%H%M%SZ')
                rrule = rrule.replace(match_until.group('until'), 'UNTIL={}'.format(utc))
            kwargs['tzinfos']['TZI'] = timezone
        x = dateutil.rrule.rrulestr(rrule, **kwargs)
        return x

    def __unicode__(self):
        return u'%s_t%s_%s_%s' % (self.name, self.unified_job_template.id, self.id, self.next_run)

    def get_absolute_url(self, request=None):
        return reverse('api:schedule_detail', kwargs={'pk': self.pk}, request=request)

    def get_job_kwargs(self):
        config_data = self.prompts_dict()
        job_kwargs, rejected, errors = self.unified_job_template._accept_or_ignore_job_kwargs(**config_data)
        if errors:
            logger.info('Errors creating scheduled job: {}'.format(errors))
        job_kwargs['_eager_fields'] = {'launch_type': 'scheduled', 'schedule': self}
        return job_kwargs

    def update_computed_fields(self):
        future_rs = Schedule.rrulestr(self.rrule, forceset=True)
        next_run_actual = future_rs.after(now())

        if next_run_actual is not None:
            if not datetime_exists(next_run_actual):
                # skip imaginary dates, like 2:30 on DST boundaries
                next_run_actual = future_rs.after(next_run_actual)
            next_run_actual = next_run_actual.astimezone(pytz.utc)

        self.next_run = next_run_actual
        try:
            self.dtstart = future_rs[0].astimezone(pytz.utc)
        except IndexError:
            self.dtstart = None
        self.dtend = None
        if 'until' in self.rrule.lower() or 'count' in self.rrule.lower():
            try:
                self.dtend = future_rs[-1].astimezone(pytz.utc)
            except IndexError:
                self.dtend = None
        emit_channel_notification('schedules-changed', dict(id=self.id, group_name='schedules'))
        with ignore_inventory_computed_fields():
            self.unified_job_template.update_computed_fields()

    def save(self, *args, **kwargs):
        self.update_computed_fields()
        super(Schedule, self).save(*args, **kwargs)
