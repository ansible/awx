import datetime
import pytest

from django.utils.encoding import smart_str
from django.utils.timezone import now

from awx.api.versioning import reverse
from awx.main.models import JobTemplate, Schedule
from awx.main.utils.encryption import decrypt_value, get_encryption_key


RRULE_EXAMPLE = 'DTSTART:20151117T050000Z RRULE:FREQ=DAILY;INTERVAL=1;COUNT=1'


def get_rrule(tz=None):
    parts = ['DTSTART']
    if tz:
        parts.append(';TZID={}'.format(tz))
    parts.append(':20300308T050000')
    if tz is None:
        parts.append('Z')
    parts.append(' RRULE:FREQ=DAILY;INTERVAL=1;COUNT=5')
    return ''.join(parts)


@pytest.mark.django_db
def test_non_job_extra_vars_prohibited(post, project, admin_user):
    url = reverse('api:project_schedules_list', kwargs={'pk': project.id})
    r = post(url, {'name': 'test sch', 'rrule': RRULE_EXAMPLE, 'extra_data': '{"a": 5}'}, admin_user, expect=400)
    assert 'not allowed on launch' in str(r.data['extra_data'][0])


@pytest.mark.django_db
def test_wfjt_schedule_accepted(post, workflow_job_template, admin_user):
    url = reverse('api:workflow_job_template_schedules_list', kwargs={'pk': workflow_job_template.id})
    post(url, {'name': 'test sch', 'rrule': RRULE_EXAMPLE}, admin_user, expect=201)


@pytest.mark.django_db
def test_wfjt_unprompted_inventory_rejected(post, workflow_job_template, inventory, admin_user):
    r = post(
        url=reverse('api:workflow_job_template_schedules_list', kwargs={'pk': workflow_job_template.id}),
        data={'name': 'test sch', 'rrule': RRULE_EXAMPLE, 'inventory': inventory.pk},
        user=admin_user,
        expect=400,
    )
    assert r.data['inventory'] == ['Field is not configured to prompt on launch.']


@pytest.mark.django_db
def test_wfjt_unprompted_inventory_accepted(post, workflow_job_template, inventory, admin_user):
    workflow_job_template.ask_inventory_on_launch = True
    workflow_job_template.save()
    r = post(
        url=reverse('api:workflow_job_template_schedules_list', kwargs={'pk': workflow_job_template.id}),
        data={'name': 'test sch', 'rrule': RRULE_EXAMPLE, 'inventory': inventory.pk},
        user=admin_user,
        expect=201,
    )
    assert Schedule.objects.get(pk=r.data['id']).inventory == inventory


@pytest.mark.django_db
def test_valid_survey_answer(post, admin_user, project, inventory, survey_spec_factory):
    job_template = JobTemplate.objects.create(name='test-jt', project=project, playbook='helloworld.yml', inventory=inventory)
    job_template.ask_variables_on_launch = False
    job_template.survey_enabled = True
    job_template.survey_spec = survey_spec_factory('var1')
    assert job_template.survey_spec['spec'][0]['type'] == 'integer'
    job_template.save()
    url = reverse('api:job_template_schedules_list', kwargs={'pk': job_template.id})
    post(url, {'name': 'test sch', 'rrule': RRULE_EXAMPLE, 'extra_data': '{"var1": 54}'}, admin_user, expect=201)


@pytest.mark.django_db
def test_encrypted_survey_answer(post, patch, admin_user, project, inventory, survey_spec_factory):
    job_template = JobTemplate.objects.create(
        name='test-jt',
        project=project,
        playbook='helloworld.yml',
        inventory=inventory,
        ask_variables_on_launch=False,
        survey_enabled=True,
        survey_spec=survey_spec_factory([{'variable': 'var1', 'type': 'password'}]),
    )

    # test encrypted-on-create
    url = reverse('api:job_template_schedules_list', kwargs={'pk': job_template.id})
    r = post(url, {'name': 'test sch', 'rrule': RRULE_EXAMPLE, 'extra_data': '{"var1": "foo"}'}, admin_user, expect=201)
    assert r.data['extra_data']['var1'] == "$encrypted$"
    schedule = Schedule.objects.get(pk=r.data['id'])
    assert schedule.extra_data['var1'].startswith('$encrypted$')
    assert decrypt_value(get_encryption_key('value', pk=None), schedule.extra_data['var1']) == 'foo'

    # test a no-op change
    r = patch(schedule.get_absolute_url(), data={'extra_data': {'var1': '$encrypted$'}}, user=admin_user, expect=200)
    assert r.data['extra_data']['var1'] == '$encrypted$'
    schedule.refresh_from_db()
    assert decrypt_value(get_encryption_key('value', pk=None), schedule.extra_data['var1']) == 'foo'

    # change to a different value
    r = patch(schedule.get_absolute_url(), data={'extra_data': {'var1': 'bar'}}, user=admin_user, expect=200)
    assert r.data['extra_data']['var1'] == '$encrypted$'
    schedule.refresh_from_db()
    assert decrypt_value(get_encryption_key('value', pk=None), schedule.extra_data['var1']) == 'bar'


@pytest.mark.django_db
@pytest.mark.parametrize(
    'rrule, error',
    [
        ("", "This field may not be blank"),
        ("DTSTART:NONSENSE", "Valid DTSTART required in rrule"),
        ("DTSTART:20300308T050000 RRULE:FREQ=DAILY;INTERVAL=1", "DTSTART cannot be a naive datetime"),
        ("DTSTART:20300308T050000Z DTSTART:20310308T050000", "Multiple DTSTART is not supported"),
        ("DTSTART:20300308T050000Z", "One or more rule required in rrule"),
        ("DTSTART:20300308T050000Z RRULE:FREQ=MONTHLY;INTERVAL=1; EXDATE:20220401", "EXDATE not allowed in rrule"),
        ("DTSTART:20300308T050000Z RRULE:FREQ=MONTHLY;INTERVAL=1; RDATE:20220401", "RDATE not allowed in rrule"),
        ("DTSTART:20300308T050000Z RRULE:FREQ=SECONDLY;INTERVAL=5;COUNT=6", "SECONDLY is not supported"),
        # Individual rule test
        ("DTSTART:20300308T050000Z RRULE:NONSENSE", "INTERVAL required in rrule"),
        ("DTSTART:20300308T050000Z RRULE:FREQ=YEARLY;INTERVAL=1;BYDAY=5MO", "BYDAY with numeric prefix not supported"),  # noqa
        ("DTSTART:20030925T104941Z RRULE:FREQ=DAILY;INTERVAL=10;COUNT=500;UNTIL=20040925T104941Z", "RRULE may not contain both COUNT and UNTIL"),  # noqa
        ("DTSTART:20300308T050000Z RRULE:FREQ=DAILY;INTERVAL=1;COUNT=2000", "COUNT > 999 is unsupported"),  # noqa
        # Individual rule test with multiple rules
        ## Bad Rule:  RRULE:NONSENSE
        ("DTSTART:20300308T050000Z RRULE:NONSENSE RRULE:INTERVAL=1;FREQ=DAILY EXRULE:FREQ=WEEKLY;INTERVAL=1;BYDAY=SU", "INTERVAL required in rrule"),
        ## Bad Rule:  RRULE:FREQ=YEARLY;INTERVAL=1;BYDAY=5MO
        (
            "DTSTART:20300308T050000Z RRULE:INTERVAL=1;FREQ=DAILY EXRULE:FREQ=WEEKLY;INTERVAL=1;BYDAY=SU RRULE:FREQ=YEARLY;INTERVAL=1;BYDAY=5MO",
            "BYDAY with numeric prefix not supported",
        ),  # noqa
        ## Bad Rule:  RRULE:FREQ=DAILY;INTERVAL=10;COUNT=500;UNTIL=20040925T104941Z
        (
            "DTSTART:20030925T104941Z RRULE:INTERVAL=1;FREQ=DAILY EXRULE:FREQ=WEEKLY;INTERVAL=1;BYDAY=SU RRULE:FREQ=DAILY;INTERVAL=10;COUNT=500;UNTIL=20040925T104941Z",
            "RRULE may not contain both COUNT and UNTIL",
        ),  # noqa
        ## Bad Rule:  RRULE:FREQ=DAILY;INTERVAL=1;COUNT=2000
        (
            "DTSTART:20300308T050000Z RRULE:INTERVAL=1;FREQ=DAILY EXRULE:FREQ=WEEKLY;INTERVAL=1;BYDAY=SU RRULE:FREQ=DAILY;INTERVAL=1;COUNT=2000",
            "COUNT > 999 is unsupported",
        ),  # noqa
        # Multiple errors, first condition should be returned
        ("DTSTART:NONSENSE RRULE:NONSENSE RRULE:FREQ=MONTHLY;INTERVAL=1;BYMONTHDAY=3,4", "Valid DTSTART required in rrule"),
        # Parsing Tests
        ("DTSTART;TZID=US-Eastern:19961105T090000 RRULE:FREQ=MINUTELY;INTERVAL=10;COUNT=5", "A valid TZID must be provided"),  # noqa
        ("DTSTART:20300308T050000Z RRULE:FREQ=REGULARLY;INTERVAL=1", "rrule parsing failed validation: invalid 'FREQ': REGULARLY"),  # noqa
        ("DTSTART;TZID=America/New_York:20300308T050000Z RRULE:FREQ=DAILY;INTERVAL=1", "rrule parsing failed validation"),
    ],
)
def test_invalid_rrules(post, admin_user, project, inventory, rrule, error):
    job_template = JobTemplate.objects.create(name='test-jt', project=project, playbook='helloworld.yml', inventory=inventory)
    url = reverse('api:job_template_schedules_list', kwargs={'pk': job_template.id})
    resp = post(
        url,
        {
            'name': 'Some Schedule',
            'rrule': rrule,
        },
        admin_user,
        expect=400,
    )
    assert error in smart_str(resp.content)


def test_multiple_invalid_rrules(post, admin_user, project, inventory):
    job_template = JobTemplate.objects.create(name='test-jt', project=project, playbook='helloworld.yml', inventory=inventory)
    url = reverse('api:job_template_schedules_list', kwargs={'pk': job_template.id})
    resp = post(
        url,
        {
            'name': 'Some Schedule',
            'rrule': "EXRULE:FREQ=SECONDLY DTSTART;TZID=US-Eastern:19961105T090000 RRULE:FREQ=MINUTELY;INTERVAL=10;COUNT=5;UNTIL=20220101 DTSTART;TZID=US-Eastern:19961105T090000",
        },
        admin_user,
        expect=400,
    )
    expected_result = {
        "rrule": [
            "Multiple DTSTART is not supported.",
            "INTERVAL required in rrule: RULE:FREQ=SECONDLY",
            "RRULE may not contain both COUNT and UNTIL: RULE:FREQ=MINUTELY;INTERVAL=10;COUNT=5;UNTIL=20220101",
            "rrule parsing failed validation: 'NoneType' object has no attribute 'group'",
        ]
    }
    assert expected_result == resp.data


@pytest.mark.django_db
def test_normal_users_can_preview_schedules(post, alice):
    url = reverse('api:schedule_rrule')
    post(url, {'rrule': get_rrule()}, alice, expect=200)


@pytest.mark.django_db
def test_utc_preview(post, admin_user):
    url = reverse('api:schedule_rrule')
    r = post(url, {'rrule': get_rrule()}, admin_user, expect=200)
    assert r.data['utc'] == r.data['local']
    assert list(map(str, r.data['utc'])) == [
        '2030-03-08 05:00:00+00:00',
        '2030-03-09 05:00:00+00:00',
        '2030-03-10 05:00:00+00:00',
        '2030-03-11 05:00:00+00:00',
        '2030-03-12 05:00:00+00:00',
    ]


@pytest.mark.django_db
def test_nyc_with_dst(post, admin_user):
    url = reverse('api:schedule_rrule')
    r = post(url, {'rrule': get_rrule('America/New_York')}, admin_user, expect=200)

    # March 10, 2030 is when DST takes effect in NYC
    assert list(map(str, r.data['local'])) == [
        '2030-03-08 05:00:00-05:00',
        '2030-03-09 05:00:00-05:00',
        '2030-03-10 05:00:00-04:00',
        '2030-03-11 05:00:00-04:00',
        '2030-03-12 05:00:00-04:00',
    ]
    assert list(map(str, r.data['utc'])) == [
        '2030-03-08 10:00:00+00:00',
        '2030-03-09 10:00:00+00:00',
        '2030-03-10 09:00:00+00:00',
        '2030-03-11 09:00:00+00:00',
        '2030-03-12 09:00:00+00:00',
    ]


@pytest.mark.django_db
def test_phoenix_without_dst(post, admin_user):
    # The state of Arizona (aside from a few Native American territories) does
    # not observe DST
    url = reverse('api:schedule_rrule')
    r = post(url, {'rrule': get_rrule('America/Phoenix')}, admin_user, expect=200)

    # March 10, 2030 is when DST takes effect in NYC
    assert list(map(str, r.data['local'])) == [
        '2030-03-08 05:00:00-07:00',
        '2030-03-09 05:00:00-07:00',
        '2030-03-10 05:00:00-07:00',
        '2030-03-11 05:00:00-07:00',
        '2030-03-12 05:00:00-07:00',
    ]
    assert list(map(str, r.data['utc'])) == [
        '2030-03-08 12:00:00+00:00',
        '2030-03-09 12:00:00+00:00',
        '2030-03-10 12:00:00+00:00',
        '2030-03-11 12:00:00+00:00',
        '2030-03-12 12:00:00+00:00',
    ]


@pytest.mark.django_db
def test_interval_by_local_day(post, admin_user):
    url = reverse('api:schedule_rrule')
    rrule = 'DTSTART;TZID=America/New_York:20300112T210000 RRULE:FREQ=MONTHLY;INTERVAL=1;BYDAY=SA;BYSETPOS=1;COUNT=4'
    r = post(url, {'rrule': rrule}, admin_user, expect=200)

    # March 10, 2030 is when DST takes effect in NYC
    assert list(map(str, r.data['local'])) == [
        '2030-02-02 21:00:00-05:00',
        '2030-03-02 21:00:00-05:00',
        '2030-04-06 21:00:00-04:00',
        '2030-05-04 21:00:00-04:00',
    ]

    assert list(map(str, r.data['utc'])) == [
        '2030-02-03 02:00:00+00:00',
        '2030-03-03 02:00:00+00:00',
        '2030-04-07 01:00:00+00:00',
        '2030-05-05 01:00:00+00:00',
    ]


@pytest.mark.django_db
def test_weekday_timezone_boundary(post, admin_user):
    url = reverse('api:schedule_rrule')
    rrule = 'DTSTART;TZID=America/New_York:20300101T210000 RRULE:FREQ=WEEKLY;BYDAY=TU;INTERVAL=1;COUNT=3'
    r = post(url, {'rrule': rrule}, admin_user, expect=200)

    assert list(map(str, r.data['local'])) == [
        '2030-01-01 21:00:00-05:00',
        '2030-01-08 21:00:00-05:00',
        '2030-01-15 21:00:00-05:00',
    ]

    assert list(map(str, r.data['utc'])) == [
        '2030-01-02 02:00:00+00:00',
        '2030-01-09 02:00:00+00:00',
        '2030-01-16 02:00:00+00:00',
    ]


@pytest.mark.django_db
def test_first_monthly_weekday_timezone_boundary(post, admin_user):
    url = reverse('api:schedule_rrule')
    rrule = 'DTSTART;TZID=America/New_York:20300101T210000 RRULE:FREQ=MONTHLY;BYDAY=SU;BYSETPOS=1;INTERVAL=1;COUNT=3'
    r = post(url, {'rrule': rrule}, admin_user, expect=200)

    assert list(map(str, r.data['local'])) == [
        '2030-01-06 21:00:00-05:00',
        '2030-02-03 21:00:00-05:00',
        '2030-03-03 21:00:00-05:00',
    ]

    assert list(map(str, r.data['utc'])) == [
        '2030-01-07 02:00:00+00:00',
        '2030-02-04 02:00:00+00:00',
        '2030-03-04 02:00:00+00:00',
    ]


@pytest.mark.django_db
def test_annual_timezone_boundary(post, admin_user):
    url = reverse('api:schedule_rrule')
    rrule = 'DTSTART;TZID=America/New_York:20301231T230000 RRULE:FREQ=YEARLY;INTERVAL=1;COUNT=3'
    r = post(url, {'rrule': rrule}, admin_user, expect=200)

    assert list(map(str, r.data['local'])) == [
        '2030-12-31 23:00:00-05:00',
        '2031-12-31 23:00:00-05:00',
        '2032-12-31 23:00:00-05:00',
    ]

    assert list(map(str, r.data['utc'])) == [
        '2031-01-01 04:00:00+00:00',
        '2032-01-01 04:00:00+00:00',
        '2033-01-01 04:00:00+00:00',
    ]


def test_dst_phantom_hour(post, admin_user):
    # The DST period in the United States begins at 02:00 (2 am) local time, so
    # the hour from 2:00:00 to 2:59:59 does not exist in the night of the
    # switch.

    # Three Sundays, starting 2:30AM America/New_York, starting Mar 3, 2030,
    # should _not_ include Mar 10, 2030 @ 2:30AM (because it doesn't exist)
    url = reverse('api:schedule_rrule')
    rrule = 'DTSTART;TZID=America/New_York:20300303T023000 RRULE:FREQ=WEEKLY;BYDAY=SU;INTERVAL=1;COUNT=3'
    r = post(url, {'rrule': rrule}, admin_user, expect=200)

    assert list(map(str, r.data['local'])) == [
        '2030-03-03 02:30:00-05:00',
        '2030-03-17 02:30:00-04:00',  # Skip 3/10 because 3/10 @ 2:30AM isn't a real date
    ]

    assert list(map(str, r.data['utc'])) == [
        '2030-03-03 07:30:00+00:00',
        '2030-03-17 06:30:00+00:00',  # Skip 3/10 because 3/10 @ 2:30AM isn't a real date
    ]


@pytest.mark.django_db
def test_months_with_31_days(post, admin_user):
    url = reverse('api:schedule_rrule')
    rrule = 'DTSTART;TZID=America/New_York:20300101T000000 RRULE:FREQ=MONTHLY;INTERVAL=1;BYMONTHDAY=31;COUNT=7'
    r = post(url, {'rrule': rrule}, admin_user, expect=200)

    # 30 days have September, April, June, and November...
    assert list(map(str, r.data['local'])) == [
        '2030-01-31 00:00:00-05:00',
        '2030-03-31 00:00:00-04:00',
        '2030-05-31 00:00:00-04:00',
        '2030-07-31 00:00:00-04:00',
        '2030-08-31 00:00:00-04:00',
        '2030-10-31 00:00:00-04:00',
        '2030-12-31 00:00:00-05:00',
    ]


@pytest.mark.django_db
@pytest.mark.timeout(3)
@pytest.mark.parametrize(
    'freq, delta, total_seconds',
    (
        ('MINUTELY', 1, 60),
        ('MINUTELY', 15, 15 * 60),
        ('HOURLY', 1, 3600),
        ('HOURLY', 2, 3600 * 2),
    ),
)
def test_really_old_dtstart(post, admin_user, freq, delta, total_seconds):
    url = reverse('api:schedule_rrule')
    # every <interval>, at the :30 second mark
    rrule = f'DTSTART;TZID=America/New_York:20051231T000030 RRULE:FREQ={freq};INTERVAL={delta}'
    start = now()
    next_ten = post(url, {'rrule': rrule}, admin_user, expect=200).data['utc']

    assert len(next_ten) == 10

    # the first date is *in the future*
    assert next_ten[0] >= start

    # ...but *no more than* <interval> into the future
    assert now() + datetime.timedelta(**{'minutes' if freq == 'MINUTELY' else 'hours': delta})

    # every date in the list is <interval> greater than the last
    for i, x in enumerate(next_ten):
        if i == 0:
            continue
        assert x.second == 30
        delta = x - next_ten[i - 1]
        assert delta.total_seconds() == total_seconds


def test_dst_rollback_duplicates(post, admin_user):
    # From Nov 2 -> Nov 3, 2030, daylight savings ends and we "roll back" an hour.
    # Make sure we don't "double count" duplicate times in the "rolled back"
    # hour.

    url = reverse('api:schedule_rrule')
    rrule = 'DTSTART;TZID=America/New_York:20301102T233000 RRULE:FREQ=HOURLY;INTERVAL=1;COUNT=5'
    r = post(url, {'rrule': rrule}, admin_user, expect=200)

    assert list(map(str, r.data['local'])) == [
        '2030-11-02 23:30:00-04:00',
        '2030-11-03 00:30:00-04:00',
        '2030-11-03 01:30:00-04:00',
        '2030-11-03 02:30:00-05:00',
        '2030-11-03 03:30:00-05:00',
    ]


@pytest.mark.parametrize(
    'rrule, expected_result',
    (
        pytest.param(
            'DTSTART;TZID=America/New_York:20300302T150000 RRULE:INTERVAL=1;FREQ=DAILY;UNTIL=20300304T1500 EXRULE:FREQ=WEEKLY;INTERVAL=1;BYDAY=SU',
            ['2030-03-02 15:00:00-05:00', '2030-03-04 15:00:00-05:00'],
            id="Every day except sundays",
        ),
        pytest.param(
            'DTSTART;TZID=US/Eastern:20300428T170000 RRULE:INTERVAL=1;FREQ=DAILY;COUNT=4 EXRULE:INTERVAL=1;FREQ=DAILY;BYMONTH=4;BYMONTHDAY=30',
            ['2030-04-28 17:00:00-04:00', '2030-04-29 17:00:00-04:00', '2030-05-01 17:00:00-04:00'],
            id="Every day except April 30th",
        ),
        pytest.param(
            'DTSTART;TZID=America/New_York:20300313T164500 RRULE:INTERVAL=5;FREQ=MINUTELY EXRULE:FREQ=MINUTELY;INTERVAL=5;BYDAY=WE;BYHOUR=17,18',
            [
                '2030-03-13 16:45:00-04:00',
                '2030-03-13 16:50:00-04:00',
                '2030-03-13 16:55:00-04:00',
                '2030-03-13 19:00:00-04:00',
                '2030-03-13 19:05:00-04:00',
                '2030-03-13 19:10:00-04:00',
                '2030-03-13 19:15:00-04:00',
                '2030-03-13 19:20:00-04:00',
                '2030-03-13 19:25:00-04:00',
                '2030-03-13 19:30:00-04:00',
            ],
            id="Every 5 minutes but not Wednesdays from 5-7pm",
        ),
        pytest.param(
            'DTSTART;TZID=America/New_York:20300426T100100 RRULE:INTERVAL=15;FREQ=MINUTELY;BYDAY=MO,TU,WE,TH,FR;BYHOUR=10,11 EXRULE:INTERVAL=15;FREQ=MINUTELY;BYDAY=MO,TU,WE,TH,FR;BYHOUR=11;BYMINUTE=3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,34,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59',
            [
                '2030-04-26 10:01:00-04:00',
                '2030-04-26 10:16:00-04:00',
                '2030-04-26 10:31:00-04:00',
                '2030-04-26 10:46:00-04:00',
                '2030-04-26 11:01:00-04:00',
                '2030-04-29 10:01:00-04:00',
                '2030-04-29 10:16:00-04:00',
                '2030-04-29 10:31:00-04:00',
                '2030-04-29 10:46:00-04:00',
                '2030-04-29 11:01:00-04:00',
            ],
            id="Every 15 minutes Monday - Friday from 10:01am to 11:02pm (inclusive)",
        ),
        pytest.param(
            'DTSTART:20301219T130551Z RRULE:FREQ=MONTHLY;INTERVAL=1;BYDAY=SA;BYMONTHDAY=12,13,14,15,16,17,18',
            [
                '2031-01-18 13:05:51+00:00',
                '2031-02-15 13:05:51+00:00',
                '2031-03-15 13:05:51+00:00',
                '2031-04-12 13:05:51+00:00',
                '2031-05-17 13:05:51+00:00',
                '2031-06-14 13:05:51+00:00',
                '2031-07-12 13:05:51+00:00',
                '2031-08-16 13:05:51+00:00',
                '2031-09-13 13:05:51+00:00',
                '2031-10-18 13:05:51+00:00',
            ],
            id="Any Saturday whose month day is between 12 and 18",
        ),
    ),
)
def test_complex_schedule(post, admin_user, rrule, expected_result):
    # Every day except Sunday, 2022-05-01 is a Sunday

    url = reverse('api:schedule_rrule')
    r = post(url, {'rrule': rrule}, admin_user, expect=200)

    assert list(map(str, r.data['local'])) == expected_result


@pytest.mark.django_db
def test_zoneinfo(get, admin_user):
    url = reverse('api:schedule_zoneinfo')
    r = get(url, admin_user, expect=200)
    assert {'name': 'America/New_York'} in r.data


@pytest.mark.django_db
def test_normal_user_can_create_jt_schedule(options, post, project, inventory, alice):
    jt = JobTemplate.objects.create(name='test-jt', project=project, playbook='helloworld.yml', inventory=inventory)
    jt.save()
    url = reverse('api:schedule_list')

    # can't create a schedule on the JT because we don't have execute rights
    params = {
        'name': 'My Example Schedule',
        'rrule': RRULE_EXAMPLE,
        'unified_job_template': jt.id,
    }
    assert 'POST' not in options(url, user=alice).data['actions'].keys()
    post(url, params, alice, expect=403)

    # now we can, because we're allowed to execute the JT
    jt.execute_role.members.add(alice)
    assert 'POST' in options(url, user=alice).data['actions'].keys()
    post(url, params, alice, expect=201)


@pytest.mark.django_db
def test_normal_user_can_create_project_schedule(options, post, project, alice):
    url = reverse('api:schedule_list')

    # can't create a schedule on the project because we don't have update rights
    params = {
        'name': 'My Example Schedule',
        'rrule': RRULE_EXAMPLE,
        'unified_job_template': project.id,
    }
    assert 'POST' not in options(url, user=alice).data['actions'].keys()
    post(url, params, alice, expect=403)

    # use role does *not* grant the ability to schedule
    project.use_role.members.add(alice)
    assert 'POST' not in options(url, user=alice).data['actions'].keys()
    post(url, params, alice, expect=403)

    # now we can, because we're allowed to update project
    project.update_role.members.add(alice)
    assert 'POST' in options(url, user=alice).data['actions'].keys()
    post(url, params, alice, expect=201)


@pytest.mark.django_db
def test_normal_user_can_create_inventory_update_schedule(options, post, inventory_source, alice):
    url = reverse('api:schedule_list')

    # can't create a schedule on the project because we don't have update rights
    params = {
        'name': 'My Example Schedule',
        'rrule': RRULE_EXAMPLE,
        'unified_job_template': inventory_source.id,
    }
    assert 'POST' not in options(url, user=alice).data['actions'].keys()
    post(url, params, alice, expect=403)

    # use role does *not* grant the ability to schedule
    inventory_source.inventory.use_role.members.add(alice)
    assert 'POST' not in options(url, user=alice).data['actions'].keys()
    post(url, params, alice, expect=403)

    # now we can, because we're allowed to update project
    inventory_source.inventory.update_role.members.add(alice)
    assert 'POST' in options(url, user=alice).data['actions'].keys()
    post(url, params, alice, expect=201)
