from dateutil.relativedelta import relativedelta
from dateutil import rrule
from datetime import datetime
import pytest

from awxkit.rrule import RRule
from awxkit.utils import to_ical


@pytest.mark.parametrize('frequency,expected_rrule',
                         [('YEARLY', 'RRULE:FREQ=YEARLY;INTERVAL=1;WKST=MO;BYMONTH={0.month};'
                                     'BYMONTHDAY={0.day};BYHOUR={0.hour};BYMINUTE={0.minute};BYSECOND={0.second}'),
                          ('MONTHLY', 'RRULE:FREQ=MONTHLY;INTERVAL=1;WKST=MO;BYMONTHDAY={0.day};BYHOUR={0.hour};'
                                      'BYMINUTE={0.minute};BYSECOND={0.second}'),
                          ('WEEKLY', 'RRULE:FREQ=WEEKLY;INTERVAL=1;WKST=MO;BYWEEKDAY={1};BYHOUR={0.hour};'
                                     'BYMINUTE={0.minute};BYSECOND={0.second}'),
                          ('DAILY', 'RRULE:FREQ=DAILY;INTERVAL=1;WKST=MO;BYHOUR={0.hour};'
                                    'BYMINUTE={0.minute};BYSECOND={0.second}'),
                          ('HOURLY', 'RRULE:FREQ=HOURLY;INTERVAL=1;WKST=MO;BYMINUTE={0.minute};BYSECOND={0.second}'),
                          ('MINUTELY', 'RRULE:FREQ=MINUTELY;INTERVAL=1;WKST=MO;BYSECOND={0.second}'),
                          ('SECONDLY', 'RRULE:FREQ=SECONDLY;INTERVAL=1;WKST=MO')],
                          ids=('yearly', 'monthly', 'weekly', 'daily', 'hourly', 'minutely', 'secondly'))
def test_string_frequency(frequency, expected_rrule):
    dtstart = datetime.utcnow()
    rule = RRule(freq=getattr(rrule, frequency), dtstart=dtstart)
    weekday_str = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU'][dtstart.weekday()]
    assert str(rule) == 'DTSTART:{0} {1}'.format(to_ical(dtstart), expected_rrule.format(dtstart, weekday_str))


@pytest.mark.parametrize('frequency,expected_rrule',
                         [(0, 'RRULE:FREQ=YEARLY;INTERVAL=1;WKST=MO;BYMONTH={0.month};'
                              'BYMONTHDAY={0.day};BYHOUR={0.hour};BYMINUTE={0.minute};BYSECOND={0.second}'),
                          (1, 'RRULE:FREQ=MONTHLY;INTERVAL=1;WKST=MO;BYMONTHDAY={0.day};BYHOUR={0.hour};'
                               'BYMINUTE={0.minute};BYSECOND={0.second}'),
                          (2, 'RRULE:FREQ=WEEKLY;INTERVAL=1;WKST=MO;BYWEEKDAY={1};BYHOUR={0.hour};'
                              'BYMINUTE={0.minute};BYSECOND={0.second}'),
                          (3, 'RRULE:FREQ=DAILY;INTERVAL=1;WKST=MO;BYHOUR={0.hour};'
                              'BYMINUTE={0.minute};BYSECOND={0.second}'),
                          (4, 'RRULE:FREQ=HOURLY;INTERVAL=1;WKST=MO;BYMINUTE={0.minute};BYSECOND={0.second}'),
                          (5, 'RRULE:FREQ=MINUTELY;INTERVAL=1;WKST=MO;BYSECOND={0.second}'),
                          (6, 'RRULE:FREQ=SECONDLY;INTERVAL=1;WKST=MO')],
                          ids=('0-yearly', '1-monthly', '2-weekly', '3-daily', '4-hourly', '5-minutely', '6-secondly'))
def test_int_frequency(frequency, expected_rrule):
    dtstart = datetime.utcnow()
    rule = RRule(freq=frequency, dtstart=dtstart)
    weekday_str = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU'][dtstart.weekday()]
    assert str(rule) == 'DTSTART:{0} {1}'.format(to_ical(dtstart), expected_rrule.format(dtstart, weekday_str))


def test_count():
    dtstart = datetime.utcnow()
    rule = RRule(freq=rrule.YEARLY, dtstart=dtstart, count=10)
    expected_rrule = ('RRULE:FREQ=YEARLY;INTERVAL=1;WKST=MO;COUNT=10;BYMONTH={0.month};'
                      'BYMONTHDAY={0.day};BYHOUR={0.hour};BYMINUTE={0.minute};BYSECOND={0.second}')
    assert str(rule) == 'DTSTART:{0} {1}'.format(to_ical(dtstart), expected_rrule.format(dtstart))


def test_until():
    dtstart = datetime.utcnow()
    until = dtstart + relativedelta(years=100)
    rule = RRule(freq=rrule.YEARLY, dtstart=dtstart, until=until)
    expected_rrule = ('RRULE:FREQ=YEARLY;INTERVAL=1;WKST=MO;UNTIL={1};BYMONTH={0.month};'
                      'BYMONTHDAY={0.day};BYHOUR={0.hour};BYMINUTE={0.minute};BYSECOND={0.second}')
    assert str(rule) == 'DTSTART:{0} {1}'.format(to_ical(dtstart), expected_rrule.format(dtstart, to_ical(until)))
