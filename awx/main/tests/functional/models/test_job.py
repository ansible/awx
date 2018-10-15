import pytest
import six

from awx.main.models import JobTemplate, Job, JobHostSummary, WorkflowJob
from crum import impersonate


@pytest.mark.django_db
def test_awx_virtualenv_from_settings(inventory, project, machine_credential):
    jt = JobTemplate.objects.create(
        name='my-jt',
        inventory=inventory,
        project=project,
        playbook='helloworld.yml'
    )
    jt.credentials.add(machine_credential)
    job = jt.create_unified_job()
    assert job.ansible_virtualenv_path == '/venv/ansible'


@pytest.mark.django_db
def test_awx_custom_virtualenv(inventory, project, machine_credential):
    jt = JobTemplate.objects.create(
        name='my-jt',
        inventory=inventory,
        project=project,
        playbook='helloworld.yml'
    )
    jt.credentials.add(machine_credential)
    job = jt.create_unified_job()

    job.project.organization.custom_virtualenv = '/venv/fancy-org'
    job.project.organization.save()
    assert job.ansible_virtualenv_path == '/venv/fancy-org'

    job.project.custom_virtualenv = '/venv/fancy-proj'
    job.project.save()
    assert job.ansible_virtualenv_path == '/venv/fancy-proj'

    job.job_template.custom_virtualenv = '/venv/fancy-jt'
    job.job_template.save()
    assert job.ansible_virtualenv_path == '/venv/fancy-jt'


@pytest.mark.django_db
def test_awx_custom_virtualenv_without_jt(project):
    project.custom_virtualenv = '/venv/fancy-proj'
    project.save()
    job = Job(project=project)
    job.save()

    job = Job.objects.get(pk=job.id)
    assert job.ansible_virtualenv_path == '/venv/fancy-proj'


@pytest.mark.django_db
def test_update_parent_instance(job_template, alice):
    # jobs are launched as a particular user, user not saved as modified_by
    with impersonate(alice):
        assert job_template.current_job is None
        assert job_template.status == 'never updated'
        assert job_template.modified_by is None
        job = job_template.jobs.create(status='new')
        job.status = 'pending'
        job.save()
        assert job_template.current_job == job
        assert job_template.status == 'pending'
        assert job_template.modified_by is None


@pytest.mark.django_db
def test_job_host_summary_representation(host):
    job = Job.objects.create(name='foo')
    jhs = JobHostSummary.objects.create(
        host=host, job=job,
        changed=1, dark=2, failures=3, ok=4, processed=5, skipped=6
    )
    assert 'single-host changed=1 dark=2 failures=3 ok=4 processed=5 skipped=6' == six.text_type(jhs)

    # Representation should be robust to deleted related items
    jhs = JobHostSummary.objects.get(pk=jhs.id)
    host.delete()
    assert 'N/A changed=1 dark=2 failures=3 ok=4 processed=5 skipped=6' == six.text_type(jhs)


@pytest.mark.django_db
class TestSlicingModels:

    def test_slice_workflow_spawn(self, slice_jt_factory):
        slice_jt = slice_jt_factory(3)
        job = slice_jt.create_unified_job()
        assert isinstance(job, WorkflowJob)
        assert job.job_template == slice_jt
        assert job.unified_job_template == slice_jt
        assert job.workflow_nodes.count() == 3

    def test_slices_with_JT_and_prompts(self, slice_job_factory):
        job = slice_job_factory(3, jt_kwargs={'ask_limit_on_launch': True}, prompts={'limit': 'foobar'}, spawn=True)
        assert job.launch_config.prompts_dict() == {'limit': 'foobar'}
        for node in job.workflow_nodes.all():
            assert node.limit is None  # data not saved in node prompts
            job = node.job
            assert job.limit == 'foobar'
