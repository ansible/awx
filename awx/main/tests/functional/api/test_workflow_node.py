import pytest

from awx.api.versioning import reverse

from awx.main.models.jobs import JobTemplate


@pytest.mark.django_db
def test_node_rejects_unprompted_fields(inventory, project, workflow_job_template, post, admin_user):
    job_template = JobTemplate.objects.create(
        inventory = inventory,
        project = project,
        playbook = 'helloworld.yml',
        ask_limit_on_launch = False
    )
    url = reverse('api:workflow_job_template_workflow_nodes_list',
                  kwargs={'pk': workflow_job_template.pk, 'version': 'v1'})
    r = post(url, {'unified_job_template': job_template.pk, 'limit': 'webservers'},
             user=admin_user, expect=400)
    assert 'limit' in r.data
    assert 'not configured to prompt on launch' in r.data['limit'][0]


@pytest.mark.django_db
def test_node_accepts_prompted_fields(inventory, project, workflow_job_template, post, admin_user):
    job_template = JobTemplate.objects.create(
        inventory = inventory,
        project = project,
        playbook = 'helloworld.yml',
        ask_limit_on_launch = True
    )
    url = reverse('api:workflow_job_template_workflow_nodes_list',
                  kwargs={'pk': workflow_job_template.pk, 'version': 'v1'})
    post(url, {'unified_job_template': job_template.pk, 'limit': 'webservers'},
         user=admin_user, expect=201)
