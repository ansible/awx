import pytest

from awx.api.versioning import reverse

from awx.main.models import JobTemplate


RRULE_EXAMPLE = 'DTSTART:20151117T050000Z RRULE:FREQ=DAILY;INTERVAL=1;COUNT=1'


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
