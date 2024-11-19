import pytest
import datetime
import dateutil

from django.utils.timezone import now

from awx.main.models.schedules import fast_forward_rrule, Schedule
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


def test_fast_forward_rrule_all_hours():
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
    '''
    Create an rruleset that contains multiple rrules and an exrule
    - freq HOURLY interval 5, dtstart should be fast forwarded
    - freq HOURLY interval 7, dtstart should be fast forwarded
    - freq MONTHLY interval 1, dtstart should not be fast forwarded
    - exrule freq HOURLY interval 5, dtstart should be fast forwarded
    '''
    rrulestr = '''DTSTART;TZID=America/New_York:20201118T200000
                RRULE:FREQ=HOURLY;INTERVAL=5
                RRULE:FREQ=HOURLY;INTERVAL=7
                RRULE:FREQ=MONTHLY
                EXRULE:FREQ=HOURLY;INTERVAL=5;BYDAY=MO,TU,WE'''
    rruleset = Schedule.rrulestr(rrulestr)
    n = now()

    # assert that each rrule has its own dtstart
    assert rruleset._rrule[0]._dtstart != rruleset._rrule[1]._dtstart != rruleset._rrule[2]._dtstart != rruleset._exrule[0]._dtstart

    # the new dtstart should be within INTERVAL amount of hours from now()
    assert n - rruleset._rrule[0]._dtstart < datetime.timedelta(hours=6)
    assert n - rruleset._rrule[1]._dtstart < datetime.timedelta(hours=8)
    assert n - rruleset._exrule[0]._dtstart < datetime.timedelta(hours=6)

    # the freq=monthly rrule's dtstart should not have changed
    dateutil_rruleset = dateutil.rrule.rrulestr(rrulestr, forceset=True)
    assert rruleset._rrule[2]._dtstart == dateutil_rruleset._rrule[2]._dtstart

    gen = rruleset.xafter(n, count=200)
    occurrences = [i for i in gen]

    orig_rruleset = dateutil.rrule.rrulestr(rrulestr, forceset=True)
    gen = orig_rruleset.xafter(n, count=200)
    orig_occurrences = [i for i in gen]

    assert occurrences == orig_occurrences


def test_future_data_not_fast_forwarded():
    dtstart = now() + datetime.timedelta(days=30)
    rrule = dateutil.rrule.rrule(freq=HOURLY, interval=7, dtstart=dtstart)
    new_rrule = fast_forward_rrule(rrule)
    assert new_rrule == rrule


@pytest.mark.parametrize(
    'freq, interval, error',
    [
        (MINUTELY, 15.5555, "interval is a fraction of a second"),
        (MONTHLY, 1, "frequency must be HOURLY or MINUTELY"),
    ],
)
def test_error_fast_forward_rrule(freq, interval, error):
    '''
    Assert a couple of error states if attempting to fast forward a date that does
    not need to be fast forwarded
    '''
    dtstart = now() - datetime.timedelta(days=30)
    rrule = dateutil.rrule.rrule(freq=freq, interval=interval, dtstart=dtstart)
    if error:
        with pytest.raises(Exception) as e_info:
            fast_forward_rrule(rrule)

        assert error in e_info.value.args[0]
