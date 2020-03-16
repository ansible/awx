import itertools
import pytest

# CRUM
from crum import impersonate

# Django
from django.contrib.contenttypes.models import ContentType

# AWX
from awx.main.models import (
    UnifiedJobTemplate, Job, JobTemplate, WorkflowJobTemplate,
    WorkflowApprovalTemplate, Project, WorkflowJob, Schedule,
    Credential
)
from awx.api.versioning import reverse


@pytest.mark.django_db
def test_subclass_types(rando):
    assert set(UnifiedJobTemplate._submodels_with_roles()) == set([
        ContentType.objects.get_for_model(JobTemplate).id,
        ContentType.objects.get_for_model(Project).id,
        ContentType.objects.get_for_model(WorkflowJobTemplate).id,
        ContentType.objects.get_for_model(WorkflowApprovalTemplate).id

    ])


@pytest.mark.django_db
def test_soft_unique_together(post, project, admin_user):
    """This tests that SOFT_UNIQUE_TOGETHER restrictions are applied correctly.
    """
    jt1 = JobTemplate.objects.create(
        name='foo_jt',
        project=project
    )
    assert jt1.organization == project.organization
    r = post(
        url=reverse('api:job_template_list'),
        data=dict(
            name='foo_jt',  # same as first
            project=project.id,
            ask_inventory_on_launch=True,
            playbook='helloworld.yml'
        ),
        user=admin_user,
        expect=400
    )
    assert 'combination already exists' in str(r.data)


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
        second_job = job_with_links.copy_unified_job()

        # Check that job data matches the original variables
        assert [c.pk for c in second_job.credentials.all()] == [
            machine_credential.pk,
            net_credential.pk
        ]
        assert second_job.inventory == job_with_links.inventory
        assert second_job.limit == 'my_server'
        assert net_credential in second_job.credentials.all()

    def test_job_relaunch_modifed_jt(self, jt_linked):
        # Replace all credentials with a new one of same type
        new_creds = []
        for cred in jt_linked.credentials.all():
            new_creds.append(Credential.objects.create(
                name=str(cred.name) + '_new',
                credential_type=cred.credential_type,
                inputs=cred.inputs
            ))
        job = jt_linked.create_unified_job()
        jt_linked.credentials.clear()
        jt_linked.credentials.add(*new_creds)
        relaunched_job = job.copy_unified_job()
        assert set(relaunched_job.credentials.all()) == set(new_creds)


@pytest.mark.django_db
class TestMetaVars:
    '''
    Extension of unit tests with same class name
    '''

    def test_deleted_user(self, admin_user):
        job = Job.objects.create(
            name='job',
            created_by=admin_user
        )
        job.save()

        user_vars = ['_'.join(x) for x in itertools.product(
            ['tower', 'awx'],
            ['user_name', 'user_id', 'user_email', 'user_first_name', 'user_last_name']
        )]

        for key in user_vars:
            assert key in job.awx_meta_vars()

        # deleted user is hard to simulate as this test occurs within one transaction
        job = Job.objects.get(pk=job.id)
        job.created_by_id = 999999999
        for key in user_vars:
            assert key not in job.awx_meta_vars()

    def test_workflow_job_metavars(self, admin_user, job_template):
        workflow_job = WorkflowJob.objects.create(
            name='workflow-job',
            created_by=admin_user
        )
        node = workflow_job.workflow_nodes.create(unified_job_template=job_template)
        job_kv = node.get_job_kwargs()
        job = node.unified_job_template.create_unified_job(**job_kv)

        workflow_job.workflow_nodes.create(job=job)
        data = job.awx_meta_vars()
        assert data['awx_user_id'] == admin_user.id
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
        assert 'awx_user_name' not in data

    def test_scheduled_workflow_job_node_metavars(self, workflow_job_template):
        schedule = Schedule.objects.create(
            name='job-schedule',
            rrule='DTSTART:20171129T155939z\nFREQ=MONTHLY',
            unified_job_template=workflow_job_template
        )

        workflow_job = WorkflowJob.objects.create(
            name='workflow-job',
            workflow_job_template=workflow_job_template,
            schedule=schedule
        )

        job = Job.objects.create(
            launch_type='workflow'
        )
        workflow_job.workflow_nodes.create(job=job)
        assert job.awx_meta_vars() == {
            'awx_job_id': job.id,
            'tower_job_id': job.id,
            'awx_job_launch_type': 'workflow',
            'tower_job_launch_type': 'workflow',
            'awx_workflow_job_name': 'workflow-job',
            'tower_workflow_job_name': 'workflow-job',
            'awx_workflow_job_id': workflow_job.id,
            'tower_workflow_job_id': workflow_job.id,
            'awx_parent_job_schedule_id': schedule.id,
            'tower_parent_job_schedule_id': schedule.id,
            'awx_parent_job_schedule_name': 'job-schedule',
            'tower_parent_job_schedule_name': 'job-schedule',
            
        }


@pytest.mark.django_db
def test_event_processing_not_finished():
    job = Job.objects.create(emitted_events=2, status='finished')
    job.event_class.objects.create(job=job)
    assert not job.event_processing_finished


@pytest.mark.django_db
def test_event_model_undefined():
    wj = WorkflowJob.objects.create(name='foobar', status='finished')
    assert wj.event_processing_finished


@pytest.mark.django_db
class TestUpdateParentInstance:

    def test_template_modified_by_not_changed_on_launch(self, job_template, alice):
        # jobs are launched as a particular user, user not saved as JT modified_by
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

    def check_update(self, project, status):
        pu_check = project.project_updates.create(
            job_type='check', status='new', launch_type='manual'
        )
        pu_check.status = 'running'
        pu_check.save()
        # these should always be updated for a running check job
        assert project.current_job == pu_check
        assert project.status == 'running'

        pu_check.status = status
        pu_check.save()
        return pu_check

    def run_update(self, project, status):
        pu_run = project.project_updates.create(
            job_type='run', status='new', launch_type='sync'
        )
        pu_run.status = 'running'
        pu_run.save()

        pu_run.status = status
        pu_run.save()
        return pu_run

    def test_project_update_fails_project(self, project):
        # This is the normal server auto-update on create behavior
        assert project.status == 'never updated'
        pu_check = self.check_update(project, status='failed')

        assert project.last_job == pu_check
        assert project.status == 'failed'

    def test_project_sync_with_skip_update(self, project):
        # syncs may be permitted to change project status
        # only if prior status is "never updated"
        assert project.status == 'never updated'
        pu_run = self.run_update(project, status='successful')

        assert project.last_job == pu_run
        assert project.status == 'successful'

    def test_project_sync_does_not_fail_project(self, project):
        # Accurate normal server behavior, creating a project auto-updates
        # have to create update, otherwise will fight with last_job logic
        assert project.status == 'never updated'
        pu_check = self.check_update(project, status='successful')
        assert project.status == 'successful'

        self.run_update(project, status='failed')
        assert project.last_job == pu_check
        assert project.status == 'successful'


@pytest.mark.django_db
class TestTaskImpact:
    @pytest.fixture
    def job_host_limit(self, job_template, inventory):
        def r(hosts, forks):
            for i in range(hosts):
                inventory.hosts.create(name='foo' + str(i))
            job = Job.objects.create(
                name='fake-job',
                launch_type='workflow',
                job_template=job_template,
                inventory=inventory,
                forks=forks
            )
            return job
        return r

    def test_limit_task_impact(self, job_host_limit, run_computed_fields_right_away):
        job = job_host_limit(5, 2)
        job.inventory.update_computed_fields()
        assert job.inventory.total_hosts == 5
        assert job.task_impact == 2 + 1  # forks becomes constraint

    def test_host_task_impact(self, job_host_limit, run_computed_fields_right_away):
        job = job_host_limit(3, 5)
        job.inventory.update_computed_fields()
        assert job.task_impact == 3 + 1  # hosts becomes constraint

    def test_shard_task_impact(self, slice_job_factory, run_computed_fields_right_away):
        # factory creates on host per slice
        workflow_job = slice_job_factory(3, jt_kwargs={'forks': 50}, spawn=True)
        # arrange the jobs by their number
        jobs = [None for i in range(3)]
        for node in workflow_job.workflow_nodes.all():
            jobs[node.job.job_slice_number - 1] = node.job
        # Even distribution - all jobs run on 1 host
        assert [
            len(jobs[0].inventory.get_script_data(slice_number=i + 1, slice_count=3)['all']['hosts'])
            for i in range(3)
        ] == [1, 1, 1]
        jobs[0].inventory.update_computed_fields()
        assert [job.task_impact for job in jobs] == [2, 2, 2]  # plus one base task impact
        # Uneven distribution - first job takes the extra host
        jobs[0].inventory.hosts.create(name='remainder_foo')
        assert [
            len(jobs[0].inventory.get_script_data(slice_number=i + 1, slice_count=3)['all']['hosts'])
            for i in range(3)
        ] == [2, 1, 1]
        jobs[0].inventory.update_computed_fields()
        assert [job.task_impact for job in jobs] == [3, 2, 2]
