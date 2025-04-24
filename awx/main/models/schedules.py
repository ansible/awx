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
from django.utils.translation import gettext_lazy as _

# AWX
from awx.api.versioning import reverse
from awx.main.fields import OrderedManyToManyField
from awx.main.models.base import PrimordialModel
from awx.main.models.jobs import LaunchTimeConfig
from awx.main.utils import ignore_inventory_computed_fields
from awx.main.consumers import emit_channel_notification

import pytz


logger = logging.getLogger('awx.main.models.schedule')

__all__ = ['Schedule']


UTC_TIMEZONES = {x: tzutc() for x in dateutil.parser.parserinfo().UTCZONE}


def _assert_timezone_id_is_valid(rrules) -> None:
    broken_rrules = [str(rrule) for rrule in rrules if rrule._dtstart and rrule._dtstart.tzinfo is None]
    if not broken_rrules:
        return
    raise ValueError(
        f'A valid TZID must be provided (e.g., America/New_York). Invalid: {broken_rrules}',
    ) from None


def _fast_forward_rrules(rrules, ref_dt=None):
    for i, rule in enumerate(rrules):
        rrules[i] = _fast_forward_rrule(rule, ref_dt=ref_dt)
    return rrules


def _fast_forward_rrule(rrule, ref_dt=None):
    '''
    Utility to fast forward an rrule, maintaining consistency in the resulting
    occurrences.

    Uses the .replace() method to update the rrule with a newer dtstart
    The operation ensures that the original occurrences (based on the original dtstart)
    will match the occurrences after changing the dtstart.

    All datetime operations (subtracting dates and adding timedeltas) should be
    in UTC to avoid DST issues. As such, the rrule dtstart is converted to UTC
    then back to the original timezone at the end.

    Returns a new rrule with a new dtstart
    '''

    if rrule._freq not in {dateutil.rrule.HOURLY, dateutil.rrule.MINUTELY}:
        return rrule

    if rrule._count:
        return rrule

    if ref_dt is None:
        ref_dt = now()

    ref_dt = ref_dt.astimezone(datetime.timezone.utc)

    rrule_dtstart_utc = rrule._dtstart.astimezone(datetime.timezone.utc)
    if rrule_dtstart_utc > ref_dt:
        return rrule

    interval = rrule._interval if rrule._interval else 1
    if rrule._freq == dateutil.rrule.HOURLY:
        interval *= 60 * 60
    elif rrule._freq == dateutil.rrule.MINUTELY:
        interval *= 60

    # if after converting to seconds the interval is still a fraction,
    # just return original rrule
    if isinstance(interval, float) and not interval.is_integer():
        return rrule

    seconds_since_dtstart = (ref_dt - rrule_dtstart_utc).total_seconds()

    # it is important to fast forward by a number that is divisible by
    # interval. For example, if interval is 7 hours, we fast forward by 7, 14, 21, etc. hours.
    # Otherwise, the occurrences after the fast forward might not match the ones before.
    # x // y is integer division, lopping off any remainder, so that we get the outcome we want.
    interval_aligned_offset = datetime.timedelta(seconds=(seconds_since_dtstart // interval) * interval)
    new_start = rrule_dtstart_utc + interval_aligned_offset
    new_rrule = rrule.replace(dtstart=new_start.astimezone(rrule._dtstart.tzinfo))
    return new_rrule


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
        ordering = [models.F('next_run').desc(nulls_last=True), 'id']
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
    enabled = models.BooleanField(default=True, help_text=_("Enables processing of this schedule."))
    dtstart = models.DateTimeField(null=True, default=None, editable=False, help_text=_("The first occurrence of the schedule occurs on or after this time."))
    dtend = models.DateTimeField(
        null=True, default=None, editable=False, help_text=_("The last occurrence of the schedule occurs before this time, aftewards the schedule expires.")
    )
    rrule = models.TextField(help_text=_("A value representing the schedules iCal recurrence rule."))
    next_run = models.DateTimeField(null=True, default=None, editable=False, help_text=_("The next time that the scheduled action will run."))
    instance_groups = OrderedManyToManyField(
        'InstanceGroup',
        related_name='schedule_instance_groups',
        blank=True,
        editable=False,
        through='ScheduleInstanceGroupMembership',
    )

    @classmethod
    def get_zoneinfo(cls):
        return sorted(get_zonefile_instance().zones)

    @classmethod
    def get_zoneinfo_links(cls):
        return_val = {}
        zone_instance = get_zonefile_instance()
        for zone_name in zone_instance.zones:
            if str(zone_name) != str(zone_instance.zones[zone_name]._filename):
                return_val[zone_name] = zone_instance.zones[zone_name]._filename
        return return_val

    @property
    def timezone(self):
        utc = tzutc()
        # All rules in a ruleset will have the same dtstart so we can just take the first rule
        tzinfo = Schedule.rrulestr(self.rrule)._rrule[0]._dtstart.tzinfo
        if tzinfo is utc:
            return 'UTC'
        all_zones = Schedule.get_zoneinfo()
        all_zones.sort(key=lambda x: -len(x))
        fname = getattr(tzinfo, '_filename', None)
        if fname:
            for zone in all_zones:
                if fname.endswith(zone):
                    return zone
        logger.warning('Could not detect valid zoneinfo for {}'.format(self.rrule))
        return ''

    @property
    # TODO: How would we handle multiple until parameters? The UI is currently using this on the edit screen of a schedule
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

        # Find the DTSTART rule or raise an error, its usually the first rule but that is not strictly enforced
        start_date_rule = re.sub(r'^.*(DTSTART[^\s]+)\s.*$', r'\1', rrule)
        if not start_date_rule:
            raise ValueError('A DTSTART field needs to be in the rrule')

        rules = re.split(r'\s+', rrule)
        for index in range(0, len(rules)):
            rule = rules[index]
            if 'until=' in rule.lower():
                # if DTSTART;TZID= is used, coerce "naive" UNTIL values
                # to the proper UTC date
                match_until = re.match(r".*?(?P<until>UNTIL\=[0-9]+T[0-9]+)(?P<utcflag>Z?)", rule)
                if not len(match_until.group('utcflag')):
                    # rule = DTSTART;TZID=America/New_York:20200601T120000 RRULE:...;UNTIL=20200601T170000

                    # Find the UNTIL=N part of the string
                    # naive_until = UNTIL=20200601T170000
                    naive_until = match_until.group('until')

                    # What is the DTSTART timezone for:
                    # DTSTART;TZID=America/New_York:20200601T120000 RRULE:...;UNTIL=20200601T170000Z
                    # local_tz = tzfile('/usr/share/zoneinfo/America/New_York')
                    # We are going to construct a 'dummy' rule for parsing which will include the DTSTART and the rest of the rule
                    temp_rule = "{} {}".format(start_date_rule, rule.replace(naive_until, naive_until + 'Z'))
                    # If the rule is an EX rule we have to add an RRULE to it because an EX rule alone will not manifest into a ruleset
                    if rule.lower().startswith('ex'):
                        temp_rule = "{} {}".format(temp_rule, 'RRULE:FREQ=MINUTELY;INTERVAL=1;UNTIL=20380601T170000Z')
                    local_tz = dateutil.rrule.rrulestr(temp_rule, tzinfos=UTC_TIMEZONES, **{'forceset': True})._rrule[0]._dtstart.tzinfo

                    # Make a datetime object with tzinfo=<the DTSTART timezone>
                    # localized_until = datetime.datetime(2020, 6, 1, 17, 0, tzinfo=tzfile('/usr/share/zoneinfo/America/New_York'))
                    localized_until = make_aware(datetime.datetime.strptime(re.sub('^UNTIL=', '', naive_until), "%Y%m%dT%H%M%S"), local_tz)

                    # Coerce the datetime to UTC and format it as a string w/ Zulu format
                    # utc_until = UNTIL=20200601T220000Z
                    utc_until = 'UNTIL=' + localized_until.astimezone(pytz.utc).strftime('%Y%m%dT%H%M%SZ')

                    # rule was:    DTSTART;TZID=America/New_York:20200601T120000 RRULE:...;UNTIL=20200601T170000
                    # rule is now: DTSTART;TZID=America/New_York:20200601T120000 RRULE:...;UNTIL=20200601T220000Z
                    rules[index] = rule.replace(naive_until, utc_until)
        return " ".join(rules)

    @classmethod
    def rrulestr(cls, rrule, ref_dt=None, **kwargs):
        """
        Apply our own custom rrule parsing requirements
        """
        rrule = Schedule.coerce_naive_until(rrule)
        kwargs['forceset'] = True
        rruleset = dateutil.rrule.rrulestr(rrule, tzinfos=UTC_TIMEZONES, **kwargs)

        _assert_timezone_id_is_valid(rruleset._rrule)
        _assert_timezone_id_is_valid(rruleset._exrule)

        # Fast forward is a way for us to limit the number of events in the rruleset
        # If we are fast forwarding and we don't have a count limited rule that is minutely or hourly
        # We will modify the start date of the rule to bring as close to the current date as possible
        # Even though the API restricts each rrule to have the same dtstart, each rrule in the rruleset
        # can fast forward to a difference dtstart. This is required in order to get stable occurrences.
        rruleset._rrule = _fast_forward_rrules(rruleset._rrule, ref_dt=ref_dt)
        rruleset._exrule = _fast_forward_rrules(rruleset._exrule, ref_dt=ref_dt)

        return rruleset

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

    def get_end_date(ruleset):
        # if we have a complex ruleset with a lot of options getting the last index of the ruleset can take some time
        # And a ruleset without a count/until can come back as datetime.datetime(9999, 12, 31, 15, 0, tzinfo=tzfile('US/Eastern'))
        # So we are going to do a quick scan to make sure we would have an end date
        for a_rule in ruleset._rrule:
            # if this rule does not have until or count in it then we have no end date
            if not a_rule._until and not a_rule._count:
                return None

        # If we made it this far we should have an end date and can ask the ruleset what the last date is
        # However, if the until/count is before dtstart we will get an IndexError when trying to get [-1]
        try:
            return ruleset[-1].astimezone(pytz.utc)
        except IndexError:
            return None

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
        if not self.dtstart:
            try:
                self.dtstart = future_rs[0].astimezone(pytz.utc)
            except IndexError:
                self.dtstart = None
        self.dtend = Schedule.get_end_date(future_rs)

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
