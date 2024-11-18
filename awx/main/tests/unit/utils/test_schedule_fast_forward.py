import pytest
import datetime
import dateutil

from django.utils.timezone import now

from awx.main.models.schedules import fast_forward_date, Schedule
from dateutil.rrule import HOURLY, MINUTELY, MONTHLY


@pytest.mark.parametrize(
    'rrulestr',
    [
        'DTSTART;TZID=America/New_York:20201118T200000 RRULE:FREQ=MINUTELY;INTERVAL=5',
        'DTSTART;TZID=America/New_York:20201118T200000 RRULE:FREQ=HOURLY;INTERVAL=5',
        'DTSTART;TZID=America/New_York:20201118T200000 RRULE:FREQ=YEARLY;INTERVAL=5',
        'DTSTART;TZID=America/New_York:20201118T200000 RRULE:FREQ=MINUTELY;INTERVAL=5;WKST=SU;BYMONTH=2,3;BYMONTHDAY=18;BYHOUR=5;BYMINUTE=35;BYSECOND=0',
        'DTSTART;TZID=America/New_York:20201118T200000 RRULE:FREQ=HOURLY;INTERVAL=5;WKST=SU;BYMONTH=2,3;BYHOUR=5',
    ],
)
def test_fast_forwarded_rrule_matches_original_occurrence(rrulestr):
    '''
    Assert that the resulting fast forwarded date is included in the original rrule
    occurrence list
    '''
    rruleset = Schedule.rrulestr(rrulestr)
    n = now()
    gen = rruleset.xafter(n, count=200)
    occurrences = [i for i in gen]

    orig_rruleset = dateutil.rrule.rrulestr(rrulestr, forceset=True)
    gen = orig_rruleset.xafter(n, count=200)
    orig_occurrences = [i for i in gen]

    assert occurrences == orig_occurrences


def test_fast_forward_date_all_hours():
    '''
    Generate an rrule for each hour of the day

    Assert that the resulting fast forwarded date is included in the original rrule
    occurrence list
    '''
    rrulestr_prefix = 'DTSTART;TZID=America/New_York:20201118T200000 RRULE:FREQ=HOURLY;'
    for interval in range(1, 24):
        rrulestr = f"{rrulestr_prefix}INTERVAL={interval}"
        rruleset = Schedule.rrulestr(rrulestr)
        n = now()
        gen = rruleset.xafter(n, count=200)
        occurrences = [i for i in gen]

        orig_rruleset = dateutil.rrule.rrulestr(rrulestr, forceset=True)
        gen = orig_rruleset.xafter(n, count=200)
        orig_occurrences = [i for i in gen]

        assert occurrences == orig_occurrences


def test_multiple_rrule():
    rrulestr = 'DTSTART;TZID=America/New_York:20201118T200000 RRULE:FREQ=HOURLY;INTERVAL=5 RRULE:FREQ=HOURLY;INTERVAL=7'
    rruleset = Schedule.rrulestr(rrulestr)
    n = now()

    # assert that each rule has its own dtstart
    assert rruleset._rrule[0]._dtstart != rruleset._rrule[1]._dtstart

    # the new dtstart should be within INTERVAL amount of hours from now()
    assert n - rruleset._rrule[0]._dtstart < datetime.timedelta(hours=6)
    assert n - rruleset._rrule[1]._dtstart < datetime.timedelta(hours=8)

    gen = rruleset.xafter(n, count=200)
    occurrences = [i for i in gen]

    orig_rruleset = dateutil.rrule.rrulestr(rrulestr, forceset=True)
    gen = orig_rruleset.xafter(n, count=200)
    orig_occurrences = [i for i in gen]

    assert occurrences == orig_occurrences


@pytest.mark.parametrize(
    'freq, interval, error',
    [
        (MINUTELY, 15.5555, "interval is a fraction of a second"),
        (MONTHLY, 1, "frequency must be HOURLY or MINUTELY"),
    ],
)
def test_error_fast_forward_date(freq, interval, error):
    dtstart = now() - datetime.timedelta(days=30)
    rule = dateutil.rrule.rrule(freq=freq, interval=interval, dtstart=dtstart)
    if error:
        with pytest.raises(Exception) as e_info:
            fast_forward_date(rule)

        assert error in e_info.value.args[0]
