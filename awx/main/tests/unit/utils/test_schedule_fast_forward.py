import pytest
import datetime

from django.utils.timezone import now

from awx.main.models.schedules import fast_forward_date
from dateutil.rrule import rrule, HOURLY, MINUTELY, MONTHLY


def test_fast_forward_date_all_hours():
    '''
    Assert that the resulting fast forwarded date is included in the original rrule
    occurrence list
    '''
    for interval in range(1, 24):
        dtstart = now() - datetime.timedelta(days=30)
        rule = rrule(freq=HOURLY, interval=interval, dtstart=dtstart)
        new_datetime = fast_forward_date(rule)

        # get occurrences of the rrule
        gen = rule.xafter(new_datetime - datetime.timedelta(days=1), count=100)
        found_matching_date = False
        for occurrence in gen:
            if occurrence == new_datetime:
                found_matching_date = True
                break

        assert found_matching_date


@pytest.mark.parametrize(
    'freq, interval',
    [
        (MINUTELY, 15),
        (MINUTELY, 120),
        (MINUTELY, 60 * 24 * 3),
        (HOURLY, 7),
        (HOURLY, 24 * 3),
    ],
)
def test_fast_forward_date(freq, interval):
    '''
    Assert that the resulting fast forwarded date is included in the original rrule
    occurrence list
    '''
    dtstart = now() - datetime.timedelta(days=30)
    rule = rrule(freq=freq, interval=interval, dtstart=dtstart)
    new_datetime = fast_forward_date(rule)

    # get occurrences of the rrule
    gen = rule.xafter(new_datetime - datetime.timedelta(days=1), count=100)
    found_matching_date = False
    for occurrence in gen:
        if occurrence == new_datetime:
            found_matching_date = True
            break

    assert found_matching_date


@pytest.mark.parametrize(
    'freq, interval, error',
    [
        (MINUTELY, 15.5555, "interval is a fraction of a second"),
        (MONTHLY, 1, "frequency must be HOURLY or MINUTELY"),
        (HOURLY, 24 * 30, "interval is greater than the fast forward amount"),
    ],
)
def test_error_fast_forward_date(freq, interval, error):
    dtstart = now() - datetime.timedelta(days=30)
    rule = rrule(freq=freq, interval=interval, dtstart=dtstart)
    if error:
        with pytest.raises(Exception) as e_info:
            fast_forward_date(rule)

        assert error in e_info.value.args[0]
