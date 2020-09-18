from datetime import datetime, timedelta
from contextlib import contextmanager

from django.utils.timezone import now
from django.db.utils import IntegrityError
from unittest import mock
import pytest
import pytz

from awx.main.models import JobTemplate, Schedule, ActivityStream

from crum import impersonate


@pytest.fixture
def job_template(inventory, project):
    # need related resources set for these tests
    return JobTemplate.objects.create(
        name='test-job_template',
        inventory=inventory,
        project=project
    )


@pytest.mark.django_db
class TestComputedFields:

    # expired in 2015, so next_run should not be populated
    dead_rrule = "DTSTART;TZID=UTC:20140520T190000 RRULE:FREQ=YEARLY;INTERVAL=1;BYMONTH=1;BYMONTHDAY=1;UNTIL=20150530T000000Z"
    continuing_rrule = "DTSTART;TZID=UTC:20140520T190000 RRULE:FREQ=YEARLY;INTERVAL=1;BYMONTH=1;BYMONTHDAY=1"

    @property
    def distant_rrule(self):
        # this rule should produce a next_run, but it should not overlap with test run time
        this_year = now().year
        return "DTSTART;TZID=UTC:{}0520T190000 RRULE:FREQ=YEARLY;INTERVAL=1;BYMONTH=1;BYMONTHDAY=1;UNTIL={}0530T000000Z".format(
            this_year + 1, this_year + 2
        )

    @contextmanager
    def assert_no_unwanted_stuff(self, schedule, act_stream=True, sch_assert=True):
        """These changes are not wanted for any computed fields update
        of schedules, so we make the assertions for all of the tests here
        """
        original_sch_modified = schedule.modified
        original_sch_modified_by = schedule.modified_by
        original_ujt_modified = schedule.unified_job_template.modified
        original_ujt_modified_by = schedule.unified_job_template.modified_by
        original_AS_entries = ActivityStream.objects.count()
        yield None
        if sch_assert:
            schedule.refresh_from_db()
            assert schedule.modified == original_sch_modified
            assert schedule.modified_by == original_sch_modified_by
        # a related schedule update should not change JT modified time
        schedule.unified_job_template.refresh_from_db()
        assert schedule.unified_job_template.modified == original_ujt_modified
        assert schedule.unified_job_template.modified_by == original_ujt_modified_by
        if act_stream:
            assert ActivityStream.objects.count() == original_AS_entries, (
                ActivityStream.objects.order_by('-timestamp').first().changes
            )

    def test_computed_fields_modified_by_retained(self, job_template, admin_user):
        with impersonate(admin_user):
            s = Schedule.objects.create(
                name='Some Schedule',
                rrule='DTSTART:20300112T210000Z RRULE:FREQ=DAILY;INTERVAL=1',
                unified_job_template=job_template
            )
        assert s.created_by == admin_user
        with self.assert_no_unwanted_stuff(s):
            s.update_computed_fields()  # modification done by system here
        s.save()
        assert s.modified_by == admin_user

    def test_computed_fields_no_op(self, job_template):
        s = Schedule.objects.create(
            name='Some Schedule',
            rrule=self.dead_rrule,
            unified_job_template=job_template,
            enabled=True
        )
        with self.assert_no_unwanted_stuff(s):
            assert s.next_run is None
            assert s.dtend is not None
            prior_dtend = s.dtend
            s.update_computed_fields()
            assert s.next_run is None
            assert s.dtend == prior_dtend

    def test_computed_fields_time_change(self, job_template):
        s = Schedule.objects.create(
            name='Some Schedule',
            rrule=self.continuing_rrule,
            unified_job_template=job_template,
            enabled=True
        )
        with self.assert_no_unwanted_stuff(s):
            # force update of next_run, as if schedule re-calculation had not happened
            # since this time
            old_next_run = datetime(2009, 3, 13, tzinfo=pytz.utc)
            Schedule.objects.filter(pk=s.pk).update(next_run=old_next_run)
            s.next_run = old_next_run
            prior_modified = s.modified
            with mock.patch('awx.main.models.schedules.emit_channel_notification'):
                s.update_computed_fields()
            assert s.next_run != old_next_run
            assert s.modified == prior_modified

    def test_computed_fields_turning_on(self, job_template):
        s = Schedule.objects.create(
            name='Some Schedule',
            rrule=self.distant_rrule,
            unified_job_template=job_template,
            enabled=False
        )
        # we expect 1 activity stream entry for changing enabled field
        with self.assert_no_unwanted_stuff(s, act_stream=False):
            assert s.next_run is None
            assert job_template.next_schedule is None
            s.enabled = True
            s.save(update_fields=['enabled'])
            assert s.next_run is not None
            assert job_template.next_schedule == s

    def test_computed_fields_turning_on_via_rrule(self, job_template):
        s = Schedule.objects.create(
            name='Some Schedule',
            rrule=self.dead_rrule,
            unified_job_template=job_template
        )
        with self.assert_no_unwanted_stuff(s, act_stream=False):
            assert s.next_run is None
            assert job_template.next_schedule is None
            s.rrule = self.distant_rrule
            with mock.patch('awx.main.models.schedules.emit_channel_notification'):
                s.update_computed_fields()
            assert s.next_run is not None
            assert job_template.next_schedule == s

    def test_computed_fields_turning_off_by_deleting(self, job_template):
        s1 = Schedule.objects.create(
            name='first schedule',
            rrule=self.distant_rrule,
            unified_job_template=job_template
        )
        s2 = Schedule.objects.create(
            name='second schedule',
            rrule=self.distant_rrule,
            unified_job_template=job_template
        )
        assert job_template.next_schedule in [s1, s2]
        if job_template.next_schedule == s1:
            expected_schedule = s2
        else:
            expected_schedule = s1
        with self.assert_no_unwanted_stuff(expected_schedule, act_stream=False, sch_assert=False):
            job_template.next_schedule.delete()
        job_template.refresh_from_db()
        assert job_template.next_schedule == expected_schedule


@pytest.mark.django_db
@pytest.mark.parametrize('freq, delta', (
    ('MINUTELY', 1),
    ('HOURLY', 1)
))
def test_past_week_rrule(job_template, freq, delta):
    # see: https://github.com/ansible/awx/issues/8071
    recent = (datetime.utcnow() - timedelta(days=3))
    recent = recent.replace(hour=0, minute=0, second=0, microsecond=0)
    recent_dt = recent.strftime('%Y%m%d')
    rrule = f'DTSTART;TZID=America/New_York:{recent_dt}T000000 RRULE:FREQ={freq};INTERVAL={delta};COUNT=5'  # noqa
    sched = Schedule.objects.create(
        name='example schedule',
        rrule=rrule,
        unified_job_template=job_template
    )
    first_event = sched.rrulestr(sched.rrule)[0]
    assert first_event.replace(tzinfo=None) == recent


@pytest.mark.django_db
@pytest.mark.parametrize('freq, delta', (
    ('MINUTELY', 1),
    ('HOURLY', 1)
))
def test_really_old_dtstart(job_template, freq, delta):
    # see: https://github.com/ansible/awx/issues/8071
    # If an event is per-minute/per-hour and was created a *really long*
    # time ago, we should just bump forward to start counting "in the last week"
    rrule = f'DTSTART;TZID=America/New_York:20150101T000000 RRULE:FREQ={freq};INTERVAL={delta}'  # noqa
    sched = Schedule.objects.create(
        name='example schedule',
        rrule=rrule,
        unified_job_template=job_template
    )
    last_week = (datetime.utcnow() - timedelta(days=7)).date()
    first_event = sched.rrulestr(sched.rrule)[0]
    assert last_week == first_event.date()

    # the next few scheduled events should be the next minute/hour incremented
    next_five_events = list(sched.rrulestr(sched.rrule).xafter(now(), count=5))

    assert next_five_events[0] > now()
    last = None
    for event in next_five_events:
        if last:
            assert event == last + (
                timedelta(minutes=1) if freq == 'MINUTELY' else timedelta(hours=1)
            )
        last = event


@pytest.mark.django_db
def test_repeats_forever(job_template):
    s = Schedule(
        name='Some Schedule',
        rrule='DTSTART:20300112T210000Z RRULE:FREQ=DAILY;INTERVAL=1',
        unified_job_template=job_template
    )
    s.save()
    assert str(s.next_run) == str(s.dtstart) == '2030-01-12 21:00:00+00:00'
    assert s.dtend is None


@pytest.mark.django_db
def test_no_recurrence_utc(job_template):
    s = Schedule(
        name='Some Schedule',
        rrule='DTSTART:20300112T210000Z RRULE:FREQ=DAILY;INTERVAL=1;COUNT=1',
        unified_job_template=job_template
    )
    s.save()
    assert str(s.next_run) == str(s.dtstart) == str(s.dtend) == '2030-01-12 21:00:00+00:00'


@pytest.mark.django_db
def test_no_recurrence_est(job_template):
    s = Schedule(
        name='Some Schedule',
        rrule='DTSTART;TZID=America/New_York:20300112T210000 RRULE:FREQ=DAILY;INTERVAL=1;COUNT=1',
        unified_job_template=job_template
    )
    s.save()
    assert str(s.next_run) == str(s.dtstart) == str(s.dtend) == '2030-01-13 02:00:00+00:00'


@pytest.mark.django_db
def test_next_run_utc(job_template):
    s = Schedule(
        name='Some Schedule',
        rrule='DTSTART:20300112T210000Z RRULE:FREQ=MONTHLY;INTERVAL=1;BYDAY=SA;BYSETPOS=1;COUNT=4',
        unified_job_template=job_template
    )
    s.save()
    assert str(s.next_run) == '2030-02-02 21:00:00+00:00'
    assert str(s.next_run) == str(s.dtstart)
    assert str(s.dtend) == '2030-05-04 21:00:00+00:00'


@pytest.mark.django_db
def test_next_run_est(job_template):
    s = Schedule(
        name='Some Schedule',
        rrule='DTSTART;TZID=America/New_York:20300112T210000 RRULE:FREQ=MONTHLY;INTERVAL=1;BYDAY=SA;BYSETPOS=1;COUNT=4',
        unified_job_template=job_template
    )
    s.save()

    assert str(s.next_run) == '2030-02-03 02:00:00+00:00'
    assert str(s.next_run) == str(s.dtstart)

    # March 10, 2030 is when DST takes effect in NYC
    assert str(s.dtend) == '2030-05-05 01:00:00+00:00'


@pytest.mark.django_db
def test_year_boundary(job_template):
    rrule = 'DTSTART;TZID=America/New_York:20301231T230000 RRULE:FREQ=YEARLY;INTERVAL=1;BYMONTH=12;BYMONTHDAY=31;COUNT=4'  # noqa
    s = Schedule(
        name='Some Schedule',
        rrule=rrule,
        unified_job_template=job_template
    )
    s.save()

    assert str(s.next_run) == '2031-01-01 04:00:00+00:00'  # UTC = +5 EST
    assert str(s.next_run) == str(s.dtstart)
    assert str(s.dtend) == '2034-01-01 04:00:00+00:00'  # UTC = +5 EST


@pytest.mark.django_db
def test_leap_year_day(job_template):
    rrule = 'DTSTART;TZID=America/New_York:20320229T050000 RRULE:FREQ=YEARLY;INTERVAL=1;BYMONTH=02;BYMONTHDAY=29;COUNT=2'  # noqa
    s = Schedule(
        name='Some Schedule',
        rrule=rrule,
        unified_job_template=job_template
    )
    s.save()

    assert str(s.next_run) == '2032-02-29 10:00:00+00:00'  # UTC = +5 EST
    assert str(s.next_run) == str(s.dtstart)
    assert str(s.dtend) == '2036-02-29 10:00:00+00:00'  # UTC = +5 EST


@pytest.mark.django_db
@pytest.mark.parametrize('until, dtend', [
    ['20300602T170000Z', '2030-06-02 12:00:00+00:00'],
    ['20300602T000000Z', '2030-06-01 12:00:00+00:00'],
])
def test_utc_until(job_template, until, dtend):
    rrule = 'DTSTART:20300601T120000Z RRULE:FREQ=DAILY;INTERVAL=1;UNTIL={}'.format(until)
    s = Schedule(
        name='Some Schedule',
        rrule=rrule,
        unified_job_template=job_template
    )
    s.save()

    assert str(s.next_run) == '2030-06-01 12:00:00+00:00'
    assert str(s.next_run) == str(s.dtstart)
    assert str(s.dtend) == dtend


@pytest.mark.django_db
@pytest.mark.parametrize('dtstart, until', [
    ['DTSTART:20380601T120000Z', '20380601T170000'],  # noon UTC to 5PM UTC
    ['DTSTART;TZID=America/New_York:20380601T120000', '20380601T170000'],  # noon EST to 5PM EST
])
def test_tzinfo_naive_until(job_template, dtstart, until):
    rrule = '{} RRULE:FREQ=HOURLY;INTERVAL=1;UNTIL={}'.format(dtstart, until)  # noqa
    s = Schedule(
        name='Some Schedule',
        rrule=rrule,
        unified_job_template=job_template
    )
    s.save()
    gen = Schedule.rrulestr(s.rrule).xafter(now(), count=20)
    assert len(list(gen)) == 6  # noon, 1PM, 2, 3, 4, 5PM


@pytest.mark.django_db
def test_utc_until_in_the_past(job_template):
    rrule = 'DTSTART:20180601T120000Z RRULE:FREQ=DAILY;INTERVAL=1;UNTIL=20150101T100000Z'
    s = Schedule(
        name='Some Schedule',
        rrule=rrule,
        unified_job_template=job_template
    )
    s.save()

    assert s.next_run is s.dtstart is s.dtend is None


@pytest.mark.django_db
@mock.patch('awx.main.models.schedules.now', lambda: datetime(2030, 3, 5, tzinfo=pytz.utc))
def test_dst_phantom_hour(job_template):
    # The DST period in the United States begins at 02:00 (2 am) local time, so
    # the hour from 2:00:00 to 2:59:59 does not exist in the night of the
    # switch.

    # Three Sundays, starting 2:30AM America/New_York, starting Mar 3, 2030,
    # (which doesn't exist)
    rrule = 'DTSTART;TZID=America/New_York:20300303T023000 RRULE:FREQ=WEEKLY;BYDAY=SU;INTERVAL=1;COUNT=3'
    s = Schedule(
        name='Some Schedule',
        rrule=rrule,
        unified_job_template=job_template
    )
    s.save()

    # 3/10/30 @ 2:30AM is skipped because it _doesn't exist_ <cue twilight zone music>
    assert str(s.next_run) == '2030-03-17 06:30:00+00:00'


@pytest.mark.django_db
@pytest.mark.timeout(3)
def test_beginning_of_time(job_template):
    # ensure that really large generators don't have performance issues
    start = now()
    rrule = 'DTSTART:19700101T000000Z RRULE:FREQ=MINUTELY;INTERVAL=1'
    s = Schedule(
        name='Some Schedule',
        rrule=rrule,
        unified_job_template=job_template
    )
    s.save()
    assert s.next_run > start
    assert (s.next_run - start).total_seconds() < 60


@pytest.mark.django_db
@pytest.mark.parametrize('rrule, tz', [
    ['DTSTART:20300112T210000Z RRULE:FREQ=DAILY;INTERVAL=1', 'UTC'],
    ['DTSTART;TZID=America/New_York:20300112T210000 RRULE:FREQ=DAILY;INTERVAL=1', 'America/New_York']
])
def test_timezone_property(job_template, rrule, tz):
    s = Schedule(
        name='Some Schedule',
        rrule=rrule,
        unified_job_template=job_template
    )
    assert s.timezone == tz


@pytest.mark.django_db
def test_utc_until_property(job_template):
    rrule = 'DTSTART:20380601T120000Z RRULE:FREQ=HOURLY;INTERVAL=1;UNTIL=20380601T170000Z'
    s = Schedule(
        name='Some Schedule',
        rrule=rrule,
        unified_job_template=job_template
    )
    s.save()

    assert s.rrule.endswith('20380601T170000Z')
    assert s.until == '2038-06-01T17:00:00'


@pytest.mark.django_db
def test_localized_until_property(job_template):
    rrule = 'DTSTART;TZID=America/New_York:20380601T120000 RRULE:FREQ=HOURLY;INTERVAL=1;UNTIL=20380601T220000Z'
    s = Schedule(
        name='Some Schedule',
        rrule=rrule,
        unified_job_template=job_template
    )
    s.save()

    assert s.rrule.endswith('20380601T220000Z')
    assert s.until == '2038-06-01T17:00:00'


@pytest.mark.django_db
def test_utc_naive_coercion(job_template):
    rrule = 'DTSTART:20380601T120000Z RRULE:FREQ=HOURLY;INTERVAL=1;UNTIL=20380601T170000'
    s = Schedule(
        name='Some Schedule',
        rrule=rrule,
        unified_job_template=job_template
    )
    s.save()

    assert s.rrule.endswith('20380601T170000Z')
    assert s.until == '2038-06-01T17:00:00'


@pytest.mark.django_db
def test_est_naive_coercion(job_template):
    rrule = 'DTSTART;TZID=America/New_York:20380601T120000 RRULE:FREQ=HOURLY;INTERVAL=1;UNTIL=20380601T170000'
    s = Schedule(
        name='Some Schedule',
        rrule=rrule,
        unified_job_template=job_template
    )
    s.save()

    assert s.rrule.endswith('20380601T220000Z')  # 5PM EDT = 10PM UTC
    assert s.until == '2038-06-01T17:00:00'


@pytest.mark.django_db
def test_empty_until_property(job_template):
    rrule = 'DTSTART;TZID=America/New_York:20380601T120000 RRULE:FREQ=HOURLY;INTERVAL=1'
    s = Schedule(
        name='Some Schedule',
        rrule=rrule,
        unified_job_template=job_template
    )
    s.save()
    assert s.until == ''


@pytest.mark.django_db
def test_duplicate_name_across_templates(job_template):
    # Assert that duplicate name is allowed for different unified job templates.
    rrule = 'DTSTART;TZID=America/New_York:20380601T120000 RRULE:FREQ=HOURLY;INTERVAL=1'
    job_template_2 = JobTemplate.objects.create(name='test-job_template_2')
    s1 = Schedule(
        name='Some Schedule',
        rrule=rrule,
        unified_job_template=job_template
    )
    s2 = Schedule(
        name='Some Schedule',
        rrule=rrule,
        unified_job_template=job_template_2
    )
    s1.save()
    s2.save()

    assert s1.name == s2.name


@pytest.mark.django_db
def test_duplicate_name_within_template(job_template):
    # Assert that duplicate name is not allowed for the same unified job templates.
    rrule = 'DTSTART;TZID=America/New_York:20380601T120000 RRULE:FREQ=HOURLY;INTERVAL=1'
    s1 = Schedule(
        name='Some Schedule',
        rrule=rrule,
        unified_job_template=job_template
    )
    s2 = Schedule(
        name='Some Schedule',
        rrule=rrule,
        unified_job_template=job_template
    )

    s1.save()
    with pytest.raises(IntegrityError) as ierror:
        s2.save()

    assert str(ierror.value) == "UNIQUE constraint failed: main_schedule.unified_job_template_id, main_schedule.name"
