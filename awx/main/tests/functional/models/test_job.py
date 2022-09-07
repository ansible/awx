import pytest

from awx.main.models import JobTemplate, Job, JobHostSummary, WorkflowJob, Inventory, Project, Organization


@pytest.mark.django_db
def test_prevent_slicing():
    jt = JobTemplate.objects.create(name='foo', job_slice_count=4)
    job = jt.create_unified_job(_prevent_slicing=True)
    assert job.job_slice_count == 1
    assert job.job_slice_number == 0
    assert isinstance(job, Job)


@pytest.mark.django_db
def test_job_host_summary_representation(host):
    job = Job.objects.create(name='foo')
    jhs = JobHostSummary.objects.create(host=host, job=job, changed=1, dark=2, failures=3, ignored=4, ok=5, processed=6, rescued=7, skipped=8)
    assert 'single-host changed=1 dark=2 failures=3 ignored=4 ok=5 processed=6 rescued=7 skipped=8' == str(jhs)

    # Representation should be robust to deleted related items
    jhs = JobHostSummary.objects.get(pk=jhs.id)
    host.delete()
    assert 'N/A changed=1 dark=2 failures=3 ignored=4 ok=5 processed=6 rescued=7 skipped=8' == str(jhs)


@pytest.mark.django_db
def test_jt_organization_follows_project():
    org1 = Organization.objects.create(name='foo1')
    org2 = Organization.objects.create(name='foo2')
    project1 = Project.objects.create(name='proj1', organization=org1)
    project2 = Project.objects.create(name='proj2', organization=org2)
    jt = JobTemplate.objects.create(name='foo', playbook='helloworld.yml', project=project1)
    assert jt.organization == org1
    jt.project = project2
    jt.save()
    assert JobTemplate.objects.get(pk=jt.id).organization == org2


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

    def test_effective_slice_count(self, job_template, inventory, organization):
        job_template.inventory = inventory
        assert job_template.inventory.hosts.count() == 0
        job_template.job_slice_count = 2
        job_template.inventory.hosts.create(name='foo1')
        assert job_template.get_effective_slice_ct({})
        inventory2 = Inventory.objects.create(organization=organization, name='fooinv')
        [inventory2.hosts.create(name='foo{}'.format(i)) for i in range(3)]
        assert job_template.get_effective_slice_ct({'inventory': inventory2})

    def test_effective_slice_count_prompt(self, job_template, inventory, organization):
        job_template.inventory = inventory
        # Add our prompt fields to the JT to allow overrides
        job_template.ask_job_slice_count_on_launch = True
        job_template.ask_inventory_on_launch = True
        # Set a default value of the slice count to something low
        job_template.job_slice_count = 2
        # Create an inventory with 4 nodes
        inventory2 = Inventory.objects.create(organization=organization, name='fooinv')
        [inventory2.hosts.create(name='foo{}'.format(i)) for i in range(4)]
        # The inventory slice count will be the min of the number of nodes (4) or the job slice (2)
        assert job_template.get_effective_slice_ct({'inventory': inventory2}) == 2
        # Now we are going to pass in an override (like the prompt would) and as long as that is < host count we expect that back
        assert job_template.get_effective_slice_ct({'inventory': inventory2, 'job_slice_count': 3}) == 3
