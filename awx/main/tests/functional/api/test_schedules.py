import pytest

from awx.api.versioning import reverse


@pytest.mark.django_db
def test_non_job_extra_vars_prohibited(post, project, admin_user):
    rrule = 'DTSTART:20151117T050000Z RRULE:FREQ=DAILY;INTERVAL=1;COUNT=1'
    url = reverse('api:project_schedules_list', kwargs={'pk': project.id})
    r = post(url, {'name': 'test sch', 'rrule': rrule, 'extra_data': '{"a": 5}'},
             admin_user, expect=400)
    assert 'cannot accept extra variables' in r.data['extra_data'][0]
