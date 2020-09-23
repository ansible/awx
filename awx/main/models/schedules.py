# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

import datetime
import logging
import re

import dateutil.rrule
import dateutil.parser
from dateutil.tz import datetime_exists, tzutc
from dateutil.zoneinfo import get_zonefile_instance

# Django
from django.db import models
from django.db.models.query import QuerySet
from django.utils.timezone import now, make_aware
from django.utils.translation import ugettext_lazy as _

# AWX
from awx.api.versioning import reverse
from awx.main.models.base import PrimordialModel
from awx.main.models.jobs import LaunchTimeConfig
from awx.main.utils import ignore_inventory_computed_fields
from awx.main.consumers import emit_channel_notification

import pytz


logger = logging.getLogger('awx.main.models.schedule')

__all__ = ['Schedule']


UTC_TIMEZONES = {x: tzutc() for x in dateutil.parser.parserinfo().UTCZONE}


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


class Schedule(PrimordialModel, LaunchTimeConfig):

    class Meta:
        app_label = 'main'
        ordering = ['-next_run']
        unique_together = ('unified_job_template', 'name')

    objects = ScheduleManager()

    unified_job_template = models.ForeignKey(
        'UnifiedJobTemplate',
        related_name='schedules',
        on_delete=models.CASCADE,
    )
    name = models.CharField(
        max_length=512,
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
    def get_zoneinfo(self):
        return sorted(get_zonefile_instance().zones)

    @property
    def timezone(self):
        utc = tzutc()
        all_zones = Schedule.get_zoneinfo()
        all_zones.sort(key = lambda x: -len(x))
        for r in Schedule.rrulestr(self.rrule)._rrule:
            if r._dtstart:
                tzinfo = r._dtstart.tzinfo
                if tzinfo is utc:
                    return 'UTC'
                fname = getattr(tzinfo, '_filename', None)
                if fname:
                    for zone in all_zones:
                        if fname.endswith(zone):
                            return zone
        logger.warn('Could not detect valid zoneinfo for {}'.format(self.rrule))
        return ''

    @property
    def until(self):
        # The UNTIL= datestamp (if any) coerced from UTC to the local naive time
        # of the DTSTART
        for r in Schedule.rrulestr(self.rrule)._rrule:
            if r._until:
                local_until = r._until.astimezone(r._dtstart.tzinfo)
                naive_until = local_until.replace(tzinfo=None)
                return naive_until.isoformat()
        return ''

    @classmethod
    def coerce_naive_until(cls, rrule):
        #
        # RFC5545 specifies that the UNTIL rule part MUST ALWAYS be a date
        # with UTC time.  This is extra work for API implementers because
        # it requires them to perform DTSTART local -> UTC datetime coercion on
        # POST and UTC -> DTSTART local coercion on GET.
        #
        # This block of code is a departure from the RFC.  If you send an
        # rrule like this to the API (without a Z on the UNTIL):
        #
        # DTSTART;TZID=America/New_York:20180502T150000 RRULE:FREQ=HOURLY;INTERVAL=1;UNTIL=20180502T180000
        #
        # ...we'll assume that the naive UNTIL is intended to match the DTSTART
        # timezone (America/New_York), and so we'll coerce to UTC _for you_
        # automatically.
        #
        if 'until=' in rrule.lower():
            # if DTSTART;TZID= is used, coerce "naive" UNTIL values
            # to the proper UTC date
            match_until = re.match(r".*?(?P<until>UNTIL\=[0-9]+T[0-9]+)(?P<utcflag>Z?)", rrule)
            if not len(match_until.group('utcflag')):
                # rrule = DTSTART;TZID=America/New_York:20200601T120000 RRULE:...;UNTIL=20200601T170000

                # Find the UNTIL=N part of the string
                # naive_until = UNTIL=20200601T170000
                naive_until = match_until.group('until')

                # What is the DTSTART timezone for:
                # DTSTART;TZID=America/New_York:20200601T120000 RRULE:...;UNTIL=20200601T170000Z
                # local_tz = tzfile('/usr/share/zoneinfo/America/New_York')
                local_tz = dateutil.rrule.rrulestr(
                    rrule.replace(naive_until, naive_until + 'Z'),
                    tzinfos=UTC_TIMEZONES
                )._dtstart.tzinfo

                # Make a datetime object with tzinfo=<the DTSTART timezone>
                # localized_until = datetime.datetime(2020, 6, 1, 17, 0, tzinfo=tzfile('/usr/share/zoneinfo/America/New_York'))
                localized_until = make_aware(
                    datetime.datetime.strptime(re.sub('^UNTIL=', '', naive_until), "%Y%m%dT%H%M%S"),
                    local_tz
                )

                # Coerce the datetime to UTC and format it as a string w/ Zulu format
                # utc_until = UNTIL=20200601T220000Z
                utc_until = 'UNTIL=' + localized_until.astimezone(pytz.utc).strftime('%Y%m%dT%H%M%SZ')

                # rrule was:    DTSTART;TZID=America/New_York:20200601T120000 RRULE:...;UNTIL=20200601T170000
                # rrule is now: DTSTART;TZID=America/New_York:20200601T120000 RRULE:...;UNTIL=20200601T220000Z
                rrule = rrule.replace(naive_until, utc_until)
        return rrule

    @classmethod
    def rrulestr(cls, rrule, fast_forward=True, **kwargs):
        """
        Apply our own custom rrule parsing requirements
        """
        rrule = Schedule.coerce_naive_until(rrule)
        kwargs['forceset'] = True
        x = dateutil.rrule.rrulestr(rrule, tzinfos=UTC_TIMEZONES, **kwargs)

        for r in x._rrule:
            if r._dtstart and r._dtstart.tzinfo is None:
                raise ValueError(
                    'A valid TZID must be provided (e.g., America/New_York)'
                )

        if (
            fast_forward and
            ('MINUTELY' in rrule or 'HOURLY' in rrule) and
            'COUNT=' not in rrule
        ):
            try:
                first_event = x[0]
                # If the first event was over a week ago...
                if (now() - first_event).days > 7:
                    # hourly/minutely rrules with far-past DTSTART values
                    # are *really* slow to precompute
                    # start *from* one week ago to speed things up drastically
                    dtstart = x._rrule[0]._dtstart.strftime(':%Y%m%dT')
                    new_start = (now() - datetime.timedelta(days=7)).strftime(':%Y%m%dT')
                    new_rrule = rrule.replace(dtstart, new_start)
                    return Schedule.rrulestr(new_rrule, fast_forward=False)
            except IndexError:
                pass
        return x

    def __str__(self):
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

    def update_computed_fields_no_save(self):
        affects_fields = ['next_run', 'dtstart', 'dtend']
        starting_values = {}
        for field_name in affects_fields:
            starting_values[field_name] = getattr(self, field_name)

        future_rs = Schedule.rrulestr(self.rrule)

        if self.enabled:
            next_run_actual = future_rs.after(now())
            if next_run_actual is not None:
                if not datetime_exists(next_run_actual):
                    # skip imaginary dates, like 2:30 on DST boundaries
                    next_run_actual = future_rs.after(next_run_actual)
                next_run_actual = next_run_actual.astimezone(pytz.utc)
        else:
            next_run_actual = None

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

        changed = any(getattr(self, field_name) != starting_values[field_name] for field_name in affects_fields)
        return changed

    def update_computed_fields(self):
        changed = self.update_computed_fields_no_save()
        if not changed:
            return
        emit_channel_notification('schedules-changed', dict(id=self.id, group_name='schedules'))
        # Must save self here before calling unified_job_template computed fields
        # in order for that method to be correct
        # by adding modified to update fields, we avoid updating modified time
        super(Schedule, self).save(update_fields=['next_run', 'dtstart', 'dtend', 'modified'])
        with ignore_inventory_computed_fields():
            self.unified_job_template.update_computed_fields()

    def save(self, *args, **kwargs):
        self.rrule = Schedule.coerce_naive_until(self.rrule)
        changed = self.update_computed_fields_no_save()
        if changed and 'update_fields' in kwargs:
            for field_name in ['next_run', 'dtstart', 'dtend']:
                if field_name not in kwargs['update_fields']:
                    kwargs['update_fields'].append(field_name)
        super(Schedule, self).save(*args, **kwargs)
        if changed:
            with ignore_inventory_computed_fields():
                self.unified_job_template.update_computed_fields()

    def delete(self, *args, **kwargs):
        ujt = self.unified_job_template
        r = super(Schedule, self).delete(*args, **kwargs)
        if ujt:
            with ignore_inventory_computed_fields():
                ujt.update_computed_fields()
        return r
