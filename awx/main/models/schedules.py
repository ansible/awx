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
    def rrulestr(cls, rrule, fast_forward=True, **kwargs):
        """
        Apply our own custom rrule parsing requirements
        """
        rrule = Schedule.coerce_naive_until(rrule)
        kwargs['forceset'] = True
        x = dateutil.rrule.rrulestr(rrule, tzinfos=UTC_TIMEZONES, **kwargs)

        for r in x._rrule:
            if r._dtstart and r._dtstart.tzinfo is None:
                raise ValueError('A valid TZID must be provided (e.g., America/New_York)')

        # Fast forward is a way for us to limit the number of events in the rruleset
        # If we are fastforwading and we don't have a count limited rule that is minutely or hourley
        # We will modify the start date of the rule to last week to prevent a large number of entries
        if fast_forward:
            try:
                # All rules in a ruleset will have the same dtstart value
                #   so lets compare the first event to now to see if its > 7 days old
                first_event = x[0]
                if (now() - first_event).days > 7:
                    for rule in x._rrule:
                        # If any rule has a minutely or hourly rule without a count...
                        if rule._freq in [dateutil.rrule.MINUTELY, dateutil.rrule.HOURLY] and not rule._count:
                            # hourly/minutely rrules with far-past DTSTART values
                            # are *really* slow to precompute
                            # start *from* one week ago to speed things up drastically
                            new_start = (now() - datetime.timedelta(days=7)).strftime('%Y%m%d')
                            # Now we want to repalce the DTSTART:<value>T with the new date (which includes the T)
                            new_rrule = re.sub('(DTSTART[^:]*):[^T]+T', r'\1:{0}T'.format(new_start), rrule)
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
