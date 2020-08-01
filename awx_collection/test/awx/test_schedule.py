from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible.errors import AnsibleError

from awx.main.models import Schedule
from awx.api.serializers import SchedulePreviewSerializer


@pytest.mark.django_db
def test_create_schedule(run_module, job_template, admin_user):
    my_rrule = 'DTSTART;TZID=Zulu:20200416T034507 RRULE:FREQ=MONTHLY;INTERVAL=1'
    result = run_module('tower_schedule', {
        'name': 'foo_schedule',
        'unified_job_template': job_template.name,
        'rrule': my_rrule
    }, admin_user)
    assert not result.get('failed', False), result.get('msg', result)

    schedule = Schedule.objects.filter(name='foo_schedule').first()

    assert result['id'] == schedule.id
    assert result['changed']

    assert schedule.rrule == my_rrule


@pytest.mark.parametrize("freq, kwargs, expect", [
    # Test with a valid start date (no time) (also tests none frequency and count)
    ('none', {'start_date': '2020-04-16'}, 'DTSTART;TZID=America/New_York:20200416T000000 RRULE:FREQ=DAILY;COUNT=1;INTERVAL=1'),
    # Test with a valid start date and time
    ('none', {'start_date': '2020-04-16 03:45:07'}, 'DTSTART;TZID=America/New_York:20200416T034507 RRULE:FREQ=DAILY;COUNT=1;INTERVAL=1'),
    # Test end_on as count (also integration test)
    ('minute', {'start_date': '2020-4-16 03:45:07', 'end_on': '2'}, 'DTSTART;TZID=America/New_York:20200416T034507 RRULE:FREQ=MINUTELY;COUNT=2;INTERVAL=1'),
    # Test end_on as date
    ('minute', {'start_date': '2020-4-16 03:45:07', 'end_on': '2020-4-17 03:45:07'},
        'DTSTART;TZID=America/New_York:20200416T034507 RRULE:FREQ=MINUTELY;UNTIL=20200417T034507;INTERVAL=1'),
    # Test on_days as a single day
    ('week', {'start_date': '2020-4-16 03:45:07', 'on_days': 'saturday'},
        'DTSTART;TZID=America/New_York:20200416T034507 RRULE:FREQ=WEEKLY;BYDAY=SA;INTERVAL=1'),
    # Test on_days as multiple days (with some whitespaces)
    ('week', {'start_date': '2020-4-16 03:45:07', 'on_days': 'saturday,monday , friday'},
        'DTSTART;TZID=America/New_York:20200416T034507 RRULE:FREQ=WEEKLY;BYDAY=MO,FR,SA;INTERVAL=1'),
    # Test valid month_day_number
    ('month', {'start_date': '2020-4-16 03:45:07', 'month_day_number': '18'},
        'DTSTART;TZID=America/New_York:20200416T034507 RRULE:FREQ=MONTHLY;BYMONTHDAY=18;INTERVAL=1'),
    # Test a valid on_the
    ('month', {'start_date': '2020-4-16 03:45:07', 'on_the': 'second sunday'},
        'DTSTART;TZID=America/New_York:20200416T034507 RRULE:FREQ=MONTHLY;BYSETPOS=2;BYDAY=SU;INTERVAL=1'),
    # Test an valid timezone
    ('month', {'start_date': '2020-4-16 03:45:07', 'timezone': 'Zulu'},
        'DTSTART;TZID=Zulu:20200416T034507 RRULE:FREQ=MONTHLY;INTERVAL=1'),
])
def test_rrule_lookup_plugin(collection_import, freq, kwargs, expect):
    LookupModule = collection_import('plugins.lookup.tower_schedule_rrule').LookupModule
    generated_rule = LookupModule.get_rrule(freq, kwargs)
    assert generated_rule == expect
    rrule_checker = SchedulePreviewSerializer()
    # Try to run our generated rrule through the awx validator
    # This will raise its own exception on failure
    rrule_checker.validate_rrule(generated_rule)


@pytest.mark.parametrize("freq", ('none', 'minute', 'hour', 'day', 'week', 'month'))
def test_empty_schedule_rrule(collection_import, freq):
    LookupModule = collection_import('plugins.lookup.tower_schedule_rrule').LookupModule
    if freq == 'day':
        pfreq = 'DAILY'
    elif freq == 'none':
        pfreq = 'DAILY;COUNT=1'
    else:
        pfreq = freq.upper() + 'LY'
    assert LookupModule.get_rrule(freq, {}).endswith(' RRULE:FREQ={0};INTERVAL=1'.format(pfreq))


@pytest.mark.parametrize("freq, kwargs, msg", [
    # Test end_on as junk
    ('minute', {'start_date': '2020-4-16 03:45:07', 'end_on': 'junk'},
        'Parameter end_on must either be an integer or in the format YYYY-MM-DD'),
    # Test on_days as junk
    ('week', {'start_date': '2020-4-16 03:45:07', 'on_days': 'junk'},
        'Parameter on_days must only contain values monday, tuesday, wednesday, thursday, friday, saturday, sunday'),
    # Test combo of both month_day_number and on_the
    ('month', dict(start_date='2020-4-16 03:45:07', on_the='something', month_day_number='else'),
        "Month based frequencies can have month_day_number or on_the but not both"),
    # Test month_day_number as not an integer
    ('month', dict(start_date='2020-4-16 03:45:07', month_day_number='junk'), "month_day_number must be between 1 and 31"),
    # Test month_day_number < 1
    ('month', dict(start_date='2020-4-16 03:45:07', month_day_number='0'), "month_day_number must be between 1 and 31"),
    # Test month_day_number > 31
    ('month', dict(start_date='2020-4-16 03:45:07', month_day_number='32'), "month_day_number must be between 1 and 31"),
    # Test on_the as junk
    ('month', dict(start_date='2020-4-16 03:45:07', on_the='junk'), "on_the parameter must be two words separated by a space"),
    # Test on_the with invalid occurance
    ('month', dict(start_date='2020-4-16 03:45:07', on_the='junk wednesday'), "The first string of the on_the parameter is not valid"),
    # Test on_the with invalid weekday
    ('month', dict(start_date='2020-4-16 03:45:07', on_the='second junk'), "Weekday portion of on_the parameter is not valid"),
    # Test an invalid timezone
    ('month', dict(start_date='2020-4-16 03:45:07', timezone='junk'), 'Timezone parameter is not valid'),
])
def test_rrule_lookup_plugin_failure(collection_import, freq, kwargs, msg):
    LookupModule = collection_import('plugins.lookup.tower_schedule_rrule').LookupModule
    with pytest.raises(AnsibleError) as e:
        assert LookupModule.get_rrule(freq, kwargs)
    assert msg in str(e.value)
