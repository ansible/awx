import pytest

from awx.api.versioning import reverse

from awx.main.models import JobTemplate


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
    r = post(url, {'name': 'test sch', 'rrule': RRULE_EXAMPLE, 'extra_data': '{"a": 5}'},
             admin_user, expect=400)
    assert 'not allowed on launch' in str(r.data['extra_data'][0])


@pytest.mark.django_db
def test_valid_survey_answer(post, admin_user, project, inventory, survey_spec_factory):
    job_template = JobTemplate.objects.create(
        name='test-jt',
        project=project,
        playbook='helloworld.yml',
        inventory=inventory
    )
    job_template.ask_variables_on_launch = False
    job_template.survey_enabled = True
    job_template.survey_spec = survey_spec_factory('var1')
    assert job_template.survey_spec['spec'][0]['type'] == 'integer'
    job_template.save()
    url = reverse('api:job_template_schedules_list', kwargs={'pk': job_template.id})
    post(url, {'name': 'test sch', 'rrule': RRULE_EXAMPLE, 'extra_data': '{"var1": 54}'},
         admin_user, expect=201)


@pytest.mark.django_db
@pytest.mark.parametrize('rrule, error', [
    ("", "This field may not be blank"),
    ("DTSTART:NONSENSE", "Valid DTSTART required in rrule"),
    ("DTSTART:20300308T050000Z DTSTART:20310308T050000", "Multiple DTSTART is not supported"),
    ("DTSTART:20300308T050000Z", "RRULE required in rrule"),
    ("DTSTART:20300308T050000Z RRULE:NONSENSE", "INTERVAL required in rrule"),
    ("DTSTART:20300308T050000Z RRULE:FREQ=SECONDLY;INTERVAL=5;COUNT=6", "SECONDLY is not supported"),
    ("DTSTART:20300308T050000Z RRULE:FREQ=MONTHLY;INTERVAL=1;BYMONTHDAY=3,4", "Multiple BYMONTHDAYs not supported"),  # noqa
    ("DTSTART:20300308T050000Z RRULE:FREQ=YEARLY;INTERVAL=1;BYMONTH=1,2", "Multiple BYMONTHs not supported"),  # noqa
    ("DTSTART:20300308T050000Z RRULE:FREQ=YEARLY;INTERVAL=1;BYDAY=5MO", "BYDAY with numeric prefix not supported"),  # noqa
    ("DTSTART:20300308T050000Z RRULE:FREQ=YEARLY;INTERVAL=1;BYYEARDAY=100", "BYYEARDAY not supported"),  # noqa
    ("DTSTART:20300308T050000Z RRULE:FREQ=YEARLY;INTERVAL=1;BYWEEKNO=20", "BYWEEKNO not supported"),
    ("DTSTART:20300308T050000Z RRULE:FREQ=DAILY;INTERVAL=1;COUNT=2000", "COUNT > 999 is unsupported"),  # noqa
    ("DTSTART:20300308T050000Z RRULE:FREQ=REGULARLY;INTERVAL=1", "rrule parsing failed validation"),  # noqa
    ("DTSTART;TZID=America/New_York:30200308T050000Z RRULE:FREQ=DAILY;INTERVAL=1", "rrule parsing failed validation"),
    ("DTSTART:20300308T050000 RRULE:FREQ=DAILY;INTERVAL=1", "DTSTART cannot be a naive datetime"),
])
def test_invalid_rrules(post, admin_user, project, inventory, rrule, error):
    job_template = JobTemplate.objects.create(
        name='test-jt',
        project=project,
        playbook='helloworld.yml',
        inventory=inventory
    )
    url = reverse('api:job_template_schedules_list', kwargs={'pk': job_template.id})
    resp = post(url, {
        'name': 'Some Schedule',
        'rrule': rrule,
    }, admin_user, expect=400)
    assert error in resp.content


@pytest.mark.django_db
def test_utc_preview(post, admin_user):
    url = reverse('api:schedule_rrule')
    r = post(url, {'rrule': get_rrule()}, admin_user, expect=200)
    assert r.data['utc'] == r.data['local']
    assert map(str, r.data['utc']) == [
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
    assert map(str, r.data['local']) == [
        '2030-03-08 05:00:00-05:00',
        '2030-03-09 05:00:00-05:00',
        '2030-03-10 05:00:00-04:00',
        '2030-03-11 05:00:00-04:00',
        '2030-03-12 05:00:00-04:00',
    ]
    assert map(str, r.data['utc']) == [
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
    assert map(str, r.data['local']) == [
        '2030-03-08 05:00:00-07:00',
        '2030-03-09 05:00:00-07:00',
        '2030-03-10 05:00:00-07:00',
        '2030-03-11 05:00:00-07:00',
        '2030-03-12 05:00:00-07:00',
    ]
    assert map(str, r.data['utc']) == [
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
    assert map(str, r.data['local']) == [
        '2030-02-02 21:00:00-05:00',
        '2030-03-02 21:00:00-05:00',
        '2030-04-06 21:00:00-04:00',
        '2030-05-04 21:00:00-04:00',
    ]

    assert map(str, r.data['utc']) == [
        '2030-02-03 02:00:00+00:00',
        '2030-03-03 02:00:00+00:00',
        '2030-04-07 01:00:00+00:00',
        '2030-05-05 01:00:00+00:00',
    ]
