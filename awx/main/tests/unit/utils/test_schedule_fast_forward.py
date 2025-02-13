import pytest
import datetime
import dateutil

from django.utils.timezone import now

from awx.main.models.schedules import _fast_forward_rrule, Schedule
from dateutil.rrule import HOURLY, MINUTELY, MONTHLY

REF_DT = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)


@pytest.mark.parametrize(
    'rrulestr',
    [
        pytest.param('DTSTART;TZID=America/New_York:20201118T200000 RRULE:FREQ=MINUTELY;INTERVAL=5', id='every-5-min'),
        pytest.param('DTSTART;TZID=America/New_York:20201118T200000 RRULE:FREQ=HOURLY;INTERVAL=5', id='every-5-hours'),
        pytest.param('DTSTART;TZID=America/New_York:20201118T200000 RRULE:FREQ=YEARLY;INTERVAL=5', id='every-5-years'),
        pytest.param(
            'DTSTART;TZID=America/New_York:20201118T200000 RRULE:FREQ=MINUTELY;INTERVAL=5;WKST=SU;BYMONTH=2,3;BYMONTHDAY=18;BYHOUR=5;BYMINUTE=35;BYSECOND=0',
            id='every-5-minutes-at-5:35:00-am-on-the-18th-day-of-feb-or-march-with-week-starting-on-sundays',
        ),
        pytest.param(
            'DTSTART;TZID=America/New_York:20201118T200000 RRULE:FREQ=HOURLY;INTERVAL=5;WKST=SU;BYMONTH=2,3;BYHOUR=5',
            id='every-5-hours-at-5-am-in-feb-or-march-with-week-starting-on-sundays',
        ),
    ],
)
def test_fast_forwarded_rrule_matches_original_occurrence(rrulestr):
    '''
    Assert that the resulting fast forwarded date is included in the original rrule
    occurrence list
    '''
    rruleset = Schedule.rrulestr(rrulestr, ref_dt=REF_DT)

    gen = rruleset.xafter(REF_DT, count=200)
    occurrences = [i for i in gen]

    orig_rruleset = dateutil.rrule.rrulestr(rrulestr, forceset=True)
    gen = orig_rruleset.xafter(REF_DT, count=200)
    orig_occurrences = [i for i in gen]

    assert occurrences == orig_occurrences


@pytest.mark.parametrize(
    'ref_dt',
    [
        pytest.param(datetime.datetime(2024, 12, 1, 0, 0, tzinfo=datetime.timezone.utc), id='ref-dt-out-of-dst'),
        pytest.param(datetime.datetime(2024, 6, 1, 0, 0, tzinfo=datetime.timezone.utc), id='ref-dt-in-dst'),
    ],
)
@pytest.mark.parametrize(
    'rrulestr',
    [
        pytest.param('DTSTART;TZID=America/New_York:20240118T200000 RRULE:FREQ=MINUTELY;INTERVAL=10', id='rrule-out-of-dst'),
        pytest.param('DTSTART;TZID=America/New_York:20240318T000000 RRULE:FREQ=MINUTELY;INTERVAL=10', id='rrule-in-dst'),
        pytest.param(
            'DTSTART;TZID=Europe/Lisbon:20230703T005800 RRULE:INTERVAL=10;FREQ=MINUTELY;BYHOUR=9,10,11,12,13,14,15,16,17,18,19,20,21', id='rrule-in-dst-by-hour'
        ),
    ],
)
def test_fast_forward_across_dst(rrulestr, ref_dt):
    '''
    Ensure fast forward works across daylight savings boundaries
    "in dst" means between March and November
    "out of dst" means between November and March the following year

    Assert that the resulting fast forwarded date is included in the original rrule
    occurrence list
    '''
    rruleset = Schedule.rrulestr(rrulestr, ref_dt=ref_dt)

    gen = rruleset.xafter(ref_dt, count=200)
    occurrences = [i for i in gen]

    orig_rruleset = dateutil.rrule.rrulestr(rrulestr, forceset=True)
    gen = orig_rruleset.xafter(ref_dt, count=200)
    orig_occurrences = [i for i in gen]

    assert occurrences == orig_occurrences


def test_fast_forward_rrule_hours():
    '''
    Generate an rrule for each hour of the day

    Assert that the resulting fast forwarded date is included in the original rrule
    occurrence list
    '''
    rrulestr_prefix = 'DTSTART;TZID=America/New_York:20201118T200000 RRULE:FREQ=HOURLY;'
    for interval in range(1, 24):
        rrulestr = f"{rrulestr_prefix}INTERVAL={interval}"
        rruleset = Schedule.rrulestr(rrulestr, ref_dt=REF_DT)

        gen = rruleset.xafter(REF_DT, count=200)
        occurrences = [i for i in gen]

        orig_rruleset = dateutil.rrule.rrulestr(rrulestr, forceset=True)
        gen = orig_rruleset.xafter(REF_DT, count=200)
        orig_occurrences = [i for i in gen]

        assert occurrences == orig_occurrences


def test_multiple_rrules():
    '''
    Create an rruleset that contains multiple rrules and an exrule
    rruleA: freq HOURLY interval 5, dtstart should be fast forwarded
    rruleB: freq HOURLY interval 7, dtstart should be fast forwarded
    rruleC: freq MONTHLY interval 1, dtstart should not be fast forwarded
    exruleA: freq HOURLY interval 5, dtstart should be fast forwarded
    '''
    rrulestr = '''DTSTART;TZID=America/New_York:20201118T200000
                RRULE:FREQ=HOURLY;INTERVAL=5
                RRULE:FREQ=HOURLY;INTERVAL=7
                RRULE:FREQ=MONTHLY
                EXRULE:FREQ=HOURLY;INTERVAL=5;BYDAY=MO,TU,WE'''
    rruleset = Schedule.rrulestr(rrulestr, ref_dt=REF_DT)

    rruleA, rruleB, rruleC = rruleset._rrule
    exruleA = rruleset._exrule[0]

    # assert that each rrule has its own dtstart
    assert rruleA._dtstart != rruleB._dtstart
    assert rruleA._dtstart != rruleC._dtstart

    assert exruleA._dtstart == rruleA._dtstart

    # the new dtstart should be within INTERVAL amount of hours from REF_DT
    assert (REF_DT - rruleA._dtstart) < datetime.timedelta(hours=6)
    assert (REF_DT - rruleB._dtstart) < datetime.timedelta(hours=8)
    assert (REF_DT - exruleA._dtstart) < datetime.timedelta(hours=6)

    # the freq=monthly rrule's dtstart should not have changed
    dateutil_rruleset = dateutil.rrule.rrulestr(rrulestr, forceset=True)
    assert rruleC._dtstart == dateutil_rruleset._rrule[2]._dtstart

    gen = rruleset.xafter(REF_DT, count=200)
    occurrences = [i for i in gen]

    orig_rruleset = dateutil.rrule.rrulestr(rrulestr, forceset=True)
    gen = orig_rruleset.xafter(REF_DT, count=200)
    orig_occurrences = [i for i in gen]

    assert occurrences == orig_occurrences


def test_future_date_does_not_fast_forward():
    dtstart = now() + datetime.timedelta(days=30)
    rrule = dateutil.rrule.rrule(freq=HOURLY, interval=7, dtstart=dtstart)
    new_rrule = _fast_forward_rrule(rrule, ref_dt=REF_DT)
    assert new_rrule == rrule


def test_rrule_with_count_does_not_fast_forward():
    rrule = dateutil.rrule.rrule(freq=MINUTELY, interval=5, count=1, dtstart=REF_DT)

    assert rrule == _fast_forward_rrule(rrule, ref_dt=REF_DT)


@pytest.mark.parametrize(
    ('freq', 'interval'),
    [
        pytest.param(MINUTELY, 15.5555, id="freq-MINUTELY-interval-15.5555"),
        pytest.param(MONTHLY, 1, id="freq-MONTHLY-interval-1"),
    ],
)
def test_does_not_fast_forward(freq, interval):
    '''
    Assert a couple of rrules that should not be fast forwarded
    '''
    dtstart = REF_DT - datetime.timedelta(days=30)
    rrule = dateutil.rrule.rrule(freq=freq, interval=interval, dtstart=dtstart)

    assert rrule == _fast_forward_rrule(rrule, ref_dt=REF_DT)
