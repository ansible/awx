import pytest
import mock

# Django
from django.contrib.contenttypes.models import ContentType

# AWX
from awx.main.models import UnifiedJobTemplate, Job, JobTemplate, WorkflowJobTemplate, Project, WorkflowJob, Schedule
from awx.main.models.ha import InstanceGroup


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
        _get_unified_job_field_names = mocker.patch('awx.main.models.jobs.JobTemplate._get_unified_job_field_names', return_value=['labels'])
        jt.create_unified_job()

        _get_unified_job_field_names.assert_called_with()

    '''
    Ensure that credentials m2m field is copied to new relaunched job
    '''
    def test_job_relaunch_copy_vars(self, machine_credential, inventory,
                                    deploy_jobtemplate, post, mocker, net_credential):
        job_with_links = Job(name='existing-job', inventory=inventory)
        job_with_links.job_template = deploy_jobtemplate
        job_with_links.limit = "my_server"
        job_with_links.save()
        job_with_links.credentials.add(machine_credential)
        job_with_links.credentials.add(net_credential)
        with mocker.patch('awx.main.models.unified_jobs.UnifiedJobTemplate._get_unified_job_field_names',
                          return_value=['inventory', 'credential', 'limit']):
            second_job = job_with_links.copy_unified_job()

        # Check that job data matches the original variables
        assert second_job.credential == job_with_links.credential
        assert second_job.inventory == job_with_links.inventory
        assert second_job.limit == 'my_server'
        assert net_credential in second_job.credentials.all()


@pytest.mark.django_db
class TestIsolatedRuns:

    def test_low_capacity_isolated_instance_selected(self):
        ig = InstanceGroup.objects.create(name='tower')
        iso_ig = InstanceGroup.objects.create(name='thepentagon', controller=ig)
        iso_ig.instances.create(hostname='iso1', capacity=50)
        i2 = iso_ig.instances.create(hostname='iso2', capacity=200)
        job = Job.objects.create(
            instance_group=iso_ig,
            celery_task_id='something',
        )

        mock_async = mock.MagicMock()
        success_callback = mock.MagicMock()
        error_callback = mock.MagicMock()

        class MockTaskClass:
            apply_async = mock_async

        with mock.patch.object(job, '_get_task_class') as task_class:
            task_class.return_value = MockTaskClass
            job.start_celery_task([], error_callback, success_callback, 'thepentagon')
        mock_async.assert_called_with([job.id, 'iso2'], [], 
                                      link_error=error_callback, 
                                      link=success_callback, 
                                      queue='thepentagon',
                                      task_id='something')

        i2.capacity = 20
        i2.save()

        with mock.patch.object(job, '_get_task_class') as task_class:
            task_class.return_value = MockTaskClass
            job.start_celery_task([], error_callback, success_callback, 'thepentagon')
        mock_async.assert_called_with([job.id, 'iso1'], [], 
                                      link_error=error_callback, 
                                      link=success_callback, 
                                      queue='thepentagon',
                                      task_id='something')


@pytest.mark.django_db
class TestMetaVars:
    '''
    Extension of unit tests with same class name
    '''

    def test_workflow_job_metavars(self, admin_user):
        workflow_job = WorkflowJob.objects.create(
            name='workflow-job',
            created_by=admin_user
        )
        job = Job.objects.create(
            name='fake-job',
            launch_type='workflow'
        )
        workflow_job.workflow_nodes.create(job=job)
        data = job.awx_meta_vars()
        assert data['awx_user_name'] == admin_user.username
        assert data['awx_workflow_job_id'] == workflow_job.pk

    def test_scheduled_job_metavars(self, job_template, admin_user):
        schedule = Schedule.objects.create(
            name='job-schedule',
            rrule='DTSTART:20171129T155939z\nFREQ=MONTHLY',
            unified_job_template=job_template
        )
        job = Job.objects.create(
            name='fake-job',
            launch_type='workflow',
            schedule=schedule,
            job_template=job_template
        )
        data = job.awx_meta_vars()
        assert data['awx_schedule_id'] == schedule.pk


@pytest.mark.django_db
def test_event_processing_not_finished():
    job = Job.objects.create(emitted_events=2, status='finished')
    job.event_class.objects.create(job=job)
    assert not job.event_processing_finished


@pytest.mark.django_db
def test_event_model_undefined():
    wj = WorkflowJob.objects.create(name='foobar', status='finished')
    assert wj.event_processing_finished
