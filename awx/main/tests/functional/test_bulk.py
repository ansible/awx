import pytest

from uuid import uuid4

from awx.api.versioning import reverse

from awx.main.models.jobs import JobTemplate
from awx.main.models import Organization, Inventory, WorkflowJob, ExecutionEnvironment, Host
from awx.main.scheduler import TaskManager


@pytest.mark.django_db
@pytest.mark.parametrize('num_hosts, num_queries', [(9, 15), (99, 20), (999, 30)])
def test_bulk_host_create_num_queries(organization, inventory, post, get, user, num_hosts, num_queries, django_assert_max_num_queries):
    '''
    If I am a...
      org admin
      inventory admin at org level
      admin of a particular inventory
      superuser

    Bulk Host create should take under a certain number of queries
    '''
    inventory.organization = organization
    inventory_admin = user('inventory_admin', False)
    org_admin = user('org_admin', False)
    org_inv_admin = user('org_admin', False)
    superuser = user('admin', True)
    for u in [org_admin, org_inv_admin, inventory_admin]:
        organization.member_role.members.add(u)
    organization.admin_role.members.add(org_admin)
    organization.inventory_admin_role.members.add(org_inv_admin)
    inventory.admin_role.members.add(inventory_admin)

    for u in [org_admin, inventory_admin, org_inv_admin, superuser]:
        hosts = [{'name': uuid4()} for i in range(num_hosts)]
        with django_assert_max_num_queries(num_queries):
            bulk_host_create_response = post(reverse('api:bulk_host_create'), {'inventory': inventory.id, 'hosts': hosts}, u, expect=201).data
            assert len(bulk_host_create_response['hosts']) == len(hosts), f"unexpected number of hosts created for user {u}"


@pytest.mark.django_db
def test_bulk_host_create_rbac(organization, inventory, post, get, user):
    '''
    If I am a...
      org admin
      inventory admin at org level
      admin of a particular invenotry
          ... I can bulk add hosts

    Everyone else cannot
    '''
    inventory.organization = organization
    inventory_admin = user('inventory_admin', False)
    org_admin = user('org_admin', False)
    org_inv_admin = user('org_admin', False)
    auditor = user('auditor', False)
    member = user('member', False)
    use_inv_member = user('member', False)
    for u in [org_admin, org_inv_admin, auditor, member, inventory_admin, use_inv_member]:
        organization.member_role.members.add(u)
    organization.admin_role.members.add(org_admin)
    organization.inventory_admin_role.members.add(org_inv_admin)
    inventory.admin_role.members.add(inventory_admin)
    inventory.use_role.members.add(use_inv_member)
    organization.auditor_role.members.add(auditor)

    for indx, u in enumerate([org_admin, inventory_admin, org_inv_admin]):
        bulk_host_create_response = post(
            reverse('api:bulk_host_create'), {'inventory': inventory.id, 'hosts': [{'name': f'foobar-{indx}'}]}, u, expect=201
        ).data
        assert len(bulk_host_create_response['hosts']) == 1, f"unexpected number of hosts created for user {u}"
        assert Host.objects.filter(inventory__id=inventory.id)[0].name == 'foobar-0'

    for indx, u in enumerate([member, auditor, use_inv_member]):
        bulk_host_create_response = post(
            reverse('api:bulk_host_create'), {'inventory': inventory.id, 'hosts': [{'name': f'foobar2-{indx}'}]}, u, expect=400
        ).data
        assert bulk_host_create_response['__all__'][0] == f'Inventory with id {inventory.id} not found or lack permissions to add hosts.'


@pytest.mark.django_db
@pytest.mark.parametrize('num_jobs, num_queries', [(9, 30), (99, 35)])
def test_bulk_job_launch_queries(job_template, organization, inventory, project, post, get, user, num_jobs, num_queries, django_assert_max_num_queries):
    '''
    if I have access to the unified job template
             ... I can launch the bulk job
             ... and the number of queries should NOT scale with the number of jobs
    '''
    normal_user = user('normal_user', False)
    org_admin = user('org_admin', False)
    jt = JobTemplate.objects.create(name='my-jt', ask_inventory_on_launch=True, project=project, playbook='helloworld.yml')
    organization.member_role.members.add(normal_user)
    organization.admin_role.members.add(org_admin)
    jt.execute_role.members.add(normal_user)
    inventory.use_role.members.add(normal_user)
    jt.save()
    inventory.save()
    jobs = [{'unified_job_template': jt.id, 'inventory': inventory.id} for _ in range(num_jobs)]

    # This is not working, we need to figure that out if we want to include tests for more jobs
    # with mock.patch('awx.api.serializers.settings.BULK_JOB_MAX_LAUNCH', num_jobs + 1):
    with django_assert_max_num_queries(num_queries):
        bulk_job_launch_response = post(reverse('api:bulk_job_launch'), {'name': 'Bulk Job Launch', 'jobs': jobs}, normal_user, expect=201).data

    # Run task manager so the workflow job nodes actually spawn
    TaskManager().schedule()

    for u in (org_admin, normal_user):
        bulk_job = get(bulk_job_launch_response['url'], u, expect=200).data
        assert organization.id == bulk_job['summary_fields']['organization']['id']
        resp = get(bulk_job_launch_response['related']['workflow_nodes'], u)
        assert resp.data['count'] == num_jobs
        for item in resp.data['results']:
            assert item["unified_job_template"] == jt.id
            assert item["inventory"] == inventory.id


@pytest.mark.django_db
def test_bulk_job_launch_no_access_to_job_template(job_template, organization, inventory, project, credential, post, get, user):
    '''
    if I don't have access to the unified job templare
             ... I can't launch the bulk job
    '''
    normal_user = user('normal_user', False)
    jt = JobTemplate.objects.create(name='my-jt', inventory=inventory, project=project, playbook='helloworld.yml')
    jt.save()
    organization.member_role.members.add(normal_user)
    bulk_job_launch_response = post(
        reverse('api:bulk_job_launch'), {'name': 'Bulk Job Launch', 'jobs': [{'unified_job_template': jt.id}]}, normal_user, expect=400
    ).data
    assert bulk_job_launch_response['__all__'][0] == f'Unified Job Templates {{{jt.id}}} not found or you don\'t have permissions to access it'


@pytest.mark.django_db
def test_bulk_job_launch_no_org_assigned(job_template, organization, inventory, project, credential, post, get, user):
    '''
    if I am not part of any organization...
             ... I can't launch the bulk job
    '''
    normal_user = user('normal_user', False)
    jt = JobTemplate.objects.create(name='my-jt', inventory=inventory, project=project, playbook='helloworld.yml')
    jt.save()
    jt.execute_role.members.add(normal_user)
    bulk_job_launch_response = post(
        reverse('api:bulk_job_launch'), {'name': 'Bulk Job Launch', 'jobs': [{'unified_job_template': jt.id}]}, normal_user, expect=400
    ).data
    assert bulk_job_launch_response['__all__'][0] == 'User not part of any organization, please assign an organization to assign to the bulk job'


@pytest.mark.django_db
def test_bulk_job_launch_multiple_org_assigned(job_template, organization, inventory, project, credential, post, get, user):
    '''
    if I am part of multiple organization...
        and if I do not provide org at the launch time
             ... I can't launch the bulk job
    '''
    normal_user = user('normal_user', False)
    org1 = Organization.objects.create(name='foo1')
    org2 = Organization.objects.create(name='foo2')
    org1.member_role.members.add(normal_user)
    org2.member_role.members.add(normal_user)
    jt = JobTemplate.objects.create(name='my-jt', inventory=inventory, project=project, playbook='helloworld.yml')
    jt.save()
    jt.execute_role.members.add(normal_user)
    bulk_job_launch_response = post(
        reverse('api:bulk_job_launch'), {'name': 'Bulk Job Launch', 'jobs': [{'unified_job_template': jt.id}]}, normal_user, expect=400
    ).data
    assert bulk_job_launch_response['__all__'][0] == 'User has permission to multiple Organizations, please set one of them in the request'


@pytest.mark.django_db
def test_bulk_job_launch_specific_org(job_template, organization, inventory, project, credential, post, get, user):
    '''
    if I am part of multiple organization...
        and if I provide org at the launch time
             ... I can launch the bulk job
    '''
    normal_user = user('normal_user', False)
    org1 = Organization.objects.create(name='foo1')
    org2 = Organization.objects.create(name='foo2')
    org1.member_role.members.add(normal_user)
    org2.member_role.members.add(normal_user)
    jt = JobTemplate.objects.create(name='my-jt', inventory=inventory, project=project, playbook='helloworld.yml')
    jt.save()
    jt.execute_role.members.add(normal_user)
    bulk_job_launch_response = post(
        reverse('api:bulk_job_launch'), {'name': 'Bulk Job Launch', 'jobs': [{'unified_job_template': jt.id}], 'organization': org1.id}, normal_user, expect=201
    ).data
    bulk_job_id = bulk_job_launch_response['id']
    bulk_job_obj = WorkflowJob.objects.filter(id=bulk_job_id, is_bulk_job=True).first()
    assert org1.id == bulk_job_obj.organization.id


@pytest.mark.django_db
def test_bulk_job_launch_inventory_no_access(job_template, organization, inventory, project, credential, post, get, user):
    '''
    if I don't have access to the inventory...
        and if I try to use it at the launch time
             ... I can't launch the bulk job
    '''
    normal_user = user('normal_user', False)
    org1 = Organization.objects.create(name='foo1')
    org2 = Organization.objects.create(name='foo2')
    jt = JobTemplate.objects.create(name='my-jt', inventory=inventory, project=project, playbook='helloworld.yml')
    jt.save()
    org1.member_role.members.add(normal_user)
    inv = Inventory.objects.create(name='inv1', organization=org2)
    jt.execute_role.members.add(normal_user)
    bulk_job_launch_response = post(
        reverse('api:bulk_job_launch'), {'name': 'Bulk Job Launch', 'jobs': [{'unified_job_template': jt.id, 'inventory': inv.id}]}, normal_user, expect=400
    ).data
    assert bulk_job_launch_response['__all__'][0] == f'Inventories {{{inv.id}}} not found or you don\'t have permissions to access it'


@pytest.mark.django_db
def test_bulk_job_inventory_prompt(job_template, organization, inventory, project, credential, post, get, user):
    '''
    Job template has an inventory set as prompt_on_launch
        and if I provide the inventory as a parameter in bulk job
        ... job uses that inventory
    '''
    normal_user = user('normal_user', False)
    org1 = Organization.objects.create(name='foo1')
    jt = JobTemplate.objects.create(name='my-jt', ask_inventory_on_launch=True, project=project, playbook='helloworld.yml')
    jt.save()
    org1.member_role.members.add(normal_user)
    inv = Inventory.objects.create(name='inv1', organization=org1)
    jt.execute_role.members.add(normal_user)
    inv.use_role.members.add(normal_user)
    bulk_job_launch_response = post(
        reverse('api:bulk_job_launch'), {'name': 'Bulk Job Launch', 'jobs': [{'unified_job_template': jt.id, 'inventory': inv.id}]}, normal_user, expect=201
    ).data
    bulk_job_id = bulk_job_launch_response['id']
    node = WorkflowJob.objects.get(id=bulk_job_id).workflow_job_nodes.all().order_by('created')
    assert inv.id == node[0].inventory.id


@pytest.mark.django_db
def test_bulk_job_set_all_prompt(job_template, organization, inventory, project, credentialtype_ssh, post, get, user):
    '''
    Job template has many fields set as prompt_on_launch
        and if I provide all those fields as a parameter in bulk job
        ... job uses them
    '''
    normal_user = user('normal_user', False)
    jt = JobTemplate.objects.create(
        name='my-jt',
        ask_inventory_on_launch=True,
        ask_diff_mode_on_launch=True,
        ask_job_type_on_launch=True,
        ask_verbosity_on_launch=True,
        ask_execution_environment_on_launch=True,
        ask_forks_on_launch=True,
        ask_job_slice_count_on_launch=True,
        ask_timeout_on_launch=True,
        ask_variables_on_launch=True,
        ask_scm_branch_on_launch=True,
        ask_limit_on_launch=True,
        ask_skip_tags_on_launch=True,
        ask_tags_on_launch=True,
        project=project,
        playbook='helloworld.yml',
    )
    jt.save()
    organization.member_role.members.add(normal_user)
    inv = Inventory.objects.create(name='inv1', organization=organization)
    ee = ExecutionEnvironment.objects.create(name='test-ee', image='quay.io/foo/bar')
    jt.execute_role.members.add(normal_user)
    inv.use_role.members.add(normal_user)
    bulk_job_launch_response = post(
        reverse('api:bulk_job_launch'),
        {
            'name': 'Bulk Job Launch',
            'jobs': [
                {
                    'unified_job_template': jt.id,
                    'inventory': inv.id,
                    'diff_mode': True,
                    'job_type': 'check',
                    'verbosity': 3,
                    'execution_environment': ee.id,
                    'forks': 1,
                    'job_slice_count': 1,
                    'timeout': 200,
                    'extra_data': {'prompted_key': 'prompted_val'},
                    'scm_branch': 'non_dev',
                    'limit': 'kansas',
                    'skip_tags': 'foobar',
                    'job_tags': 'untagged',
                }
            ],
        },
        normal_user,
        expect=201,
    ).data
    bulk_job_id = bulk_job_launch_response['id']
    node = WorkflowJob.objects.get(id=bulk_job_id).workflow_job_nodes.all().order_by('created')
    assert node[0].inventory.id == inv.id
    assert node[0].diff_mode == True
    assert node[0].job_type == 'check'
    assert node[0].verbosity == 3
    assert node[0].execution_environment.id == ee.id
    assert node[0].forks == 1
    assert node[0].job_slice_count == 1
    assert node[0].timeout == 200
    assert node[0].extra_data == {'prompted_key': 'prompted_val'}
    assert node[0].scm_branch == 'non_dev'
    assert node[0].limit == 'kansas'
    assert node[0].skip_tags == 'foobar'
    assert node[0].job_tags == 'untagged'
