import pytest

# Django
from django.contrib.contenttypes.models import ContentType

# AWX
from awx.main.models import UnifiedJobTemplate, Job, JobTemplate, WorkflowJobTemplate, Project, UnifiedJob


@pytest.mark.django_db
def test_subclass_types(rando):
    assert set(UnifiedJobTemplate._submodels_with_roles()) == set([
        ContentType.objects.get_for_model(JobTemplate).id,
        ContentType.objects.get_for_model(Project).id,
        ContentType.objects.get_for_model(WorkflowJobTemplate).id
    ])


@pytest.mark.django_db
class TestCreateUnifiedJob:
    '''
    Ensure that copying a job template to a job handles many to many field copy
    '''
    def test_many_to_many(self, mocker, job_template_labels):
        jt = job_template_labels
        _get_unified_job_field_names = mocker.patch('awx.main.models.jobs.JobTemplate._get_unified_job_field_names', return_value=['labels'])
        j = jt.create_unified_job()

        _get_unified_job_field_names.assert_called_with()
        assert j.labels.all().count() == 2
        assert j.labels.all()[0] == jt.labels.all()[0]
        assert j.labels.all()[1] == jt.labels.all()[1]

    '''
    Ensure that data is looked for in parameter list before looking at the object
    '''
    def test_many_to_many_kwargs(self, mocker, job_template_labels):
        jt = job_template_labels
        mocked = mocker.MagicMock()
        mocked.__class__.__name__ = 'ManyRelatedManager'
        kwargs = {
            'labels': mocked
        }
        _get_unified_job_field_names = mocker.patch('awx.main.models.jobs.JobTemplate._get_unified_job_field_names', return_value=['labels'])
        jt.create_unified_job(**kwargs)

        _get_unified_job_field_names.assert_called_with()
        mocked.all.assert_called_with()

    '''
    Ensure that extra_credentials m2m field is copied to new relaunched job
    '''
    def test_job_relaunch_copy_vars(self, machine_credential, inventory,
                                    deploy_jobtemplate, post, mocker, net_credential):
        job_with_links = Job.objects.create(name='existing-job', credential=machine_credential, inventory=inventory)
        job_with_links.job_template = deploy_jobtemplate
        job_with_links.limit = "my_server"
        job_with_links.extra_credentials.add(net_credential)
        with mocker.patch('awx.main.models.unified_jobs.UnifiedJobTemplate._get_unified_job_field_names',
                          return_value=['inventory', 'credential', 'limit']):
            second_job = job_with_links.copy_unified_job()

        # Check that job data matches the original variables
        assert second_job.credential == job_with_links.credential
        assert second_job.inventory == job_with_links.inventory
        assert second_job.limit == 'my_server'
        assert net_credential in second_job.extra_credentials.all()


@pytest.mark.django_db
def test_lowest_running_id():
    assert UnifiedJob.lowest_running_id() == 1
    Job.objects.create(status='finished')
    old_job = Job.objects.create(status='finished')
    assert UnifiedJob.lowest_running_id() == old_job.id + 1
    old_running_job = Job.objects.create(status='running')
    Job.objects.create(status='running')
    assert UnifiedJob.lowest_running_id() == old_running_job.id
    Job.objects.create(status='finished')
    assert UnifiedJob.lowest_running_id() == old_running_job.id
