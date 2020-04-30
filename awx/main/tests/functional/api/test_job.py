# Python
import pytest
from unittest import mock
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from crum import impersonate
import datetime

# Django rest framework
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone

# AWX
from awx.api.versioning import reverse
from awx.api.views import RelatedJobsPreventDeleteMixin, UnifiedJobDeletionMixin
from awx.main.models import (
    JobTemplate,
    User,
    Job,
    AdHocCommand,
    ProjectUpdate,
)


@pytest.mark.django_db
def test_job_relaunch_permission_denied_response(
        post, get, inventory, project, credential, net_credential, machine_credential):
    jt = JobTemplate.objects.create(name='testjt', inventory=inventory, project=project, ask_credential_on_launch=True)
    jt.credentials.add(machine_credential)
    jt_user = User.objects.create(username='jobtemplateuser')
    jt.execute_role.members.add(jt_user)
    with impersonate(jt_user):
        job = jt.create_unified_job()

    # User capability is shown for this
    r = get(job.get_absolute_url(), jt_user, expect=200)
    assert r.data['summary_fields']['user_capabilities']['start']

    # Job has prompted credential, launch denied w/ message
    job.launch_config.credentials.add(net_credential)
    r = post(reverse('api:job_relaunch', kwargs={'pk':job.pk}), {}, jt_user, expect=403)
    assert 'launched with prompted fields you do not have access to' in r.data['detail']


@pytest.mark.django_db
def test_job_relaunch_prompts_not_accepted_response(
        post, get, inventory, project, credential, net_credential, machine_credential):
    jt = JobTemplate.objects.create(name='testjt', inventory=inventory, project=project)
    jt.credentials.add(machine_credential)
    jt_user = User.objects.create(username='jobtemplateuser')
    jt.execute_role.members.add(jt_user)
    with impersonate(jt_user):
        job = jt.create_unified_job()

    # User capability is shown for this
    r = get(job.get_absolute_url(), jt_user, expect=200)
    assert r.data['summary_fields']['user_capabilities']['start']

    # Job has prompted credential, launch denied w/ message
    job.launch_config.credentials.add(net_credential)
    r = post(reverse('api:job_relaunch', kwargs={'pk':job.pk}), {}, jt_user, expect=403)


@pytest.mark.django_db
def test_job_relaunch_permission_denied_response_other_user(get, post, inventory, project, alice, bob, survey_spec_factory):
    '''
    Asserts custom permission denied message corresponding to
    awx/main/tests/functional/test_rbac_job.py::TestJobRelaunchAccess::test_other_user_prompts
    '''
    jt = JobTemplate.objects.create(
        name='testjt', inventory=inventory, project=project,
        ask_credential_on_launch=True,
        ask_variables_on_launch=True,
        survey_spec=survey_spec_factory([{'variable': 'secret_key', 'default': '6kQngg3h8lgiSTvIEb21', 'type': 'password'}]),
        survey_enabled=True
    )
    jt.execute_role.members.add(alice, bob)
    with impersonate(bob):
        job = jt.create_unified_job(extra_vars={'job_var': 'foo2', 'secret_key': 'sk4t3Rb01'})

    # User capability is shown for this
    r = get(job.get_absolute_url(), alice, expect=200)
    assert r.data['summary_fields']['user_capabilities']['start']

    # Job has prompted data, launch denied w/ message
    r = post(
        url=reverse('api:job_relaunch', kwargs={'pk':job.pk}),
        data={},
        user=alice,
        expect=403
    )
    assert 'Job was launched with secret prompts provided by another user' in r.data['detail']


@pytest.mark.django_db
def test_job_relaunch_without_creds(post, inventory, project, admin_user):
    jt = JobTemplate.objects.create(
        name='testjt', inventory=inventory,
        project=project
    )
    job = jt.create_unified_job()
    post(
        url=reverse('api:job_relaunch', kwargs={'pk':job.pk}),
        data={},
        user=admin_user,
        expect=201
    )


@pytest.mark.django_db
@pytest.mark.parametrize("status,hosts", [
    ('all', 'host1,host2,host3'),
    ('failed', 'host3'),
])
def test_job_relaunch_on_failed_hosts(post, inventory, project, machine_credential, admin_user, status, hosts):
    h1 = inventory.hosts.create(name='host1')  # no-op
    h2 = inventory.hosts.create(name='host2')  # changed host
    h3 = inventory.hosts.create(name='host3')  # failed host
    jt = JobTemplate.objects.create(
        name='testjt', inventory=inventory,
        project=project
    )
    jt.credentials.add(machine_credential)
    job = jt.create_unified_job(_eager_fields={'status': 'failed'}, limit='host1,host2,host3')
    job.job_events.create(event='playbook_on_stats')
    job.job_host_summaries.create(host=h1, failed=False, ok=1, changed=0, failures=0, host_name=h1.name)
    job.job_host_summaries.create(host=h2, failed=False, ok=0, changed=1, failures=0, host_name=h2.name)
    job.job_host_summaries.create(host=h3, failed=False, ok=0, changed=0, failures=1, host_name=h3.name)

    r = post(
        url=reverse('api:job_relaunch', kwargs={'pk':job.pk}),
        data={'hosts': status},
        user=admin_user,
        expect=201
    )
    assert r.data.get('limit') == hosts


@pytest.mark.django_db
def test_summary_fields_recent_jobs(job_template, admin_user, get):
    jobs = []
    for i in range(13):
        jobs.append(Job.objects.create(
            job_template=job_template,
            status='failed',
            created=timezone.make_aware(datetime.datetime(2017, 3, 21, 9, i)),
            finished=timezone.make_aware(datetime.datetime(2017, 3, 21, 10, i))
        ))
    r = get(
        url = job_template.get_absolute_url(),
        user = admin_user,
        exepect = 200
    )
    recent_jobs = r.data['summary_fields']['recent_jobs']
    assert len(recent_jobs) == 10
    assert recent_jobs == [{
        'id': job.id,
        'status': 'failed',
        'finished': job.finished,
        'canceled_on': None,
        'type': 'job'      
    } for job in jobs[-10:][::-1]]


@pytest.mark.django_db
def test_slice_jt_recent_jobs(slice_job_factory, admin_user, get):
    workflow_job = slice_job_factory(3, spawn=True)
    slice_jt = workflow_job.job_template
    r = get(
        url=slice_jt.get_absolute_url(),
        user=admin_user,
        expect=200
    )
    job_ids = [entry['id'] for entry in r.data['summary_fields']['recent_jobs']]
    # decision is that workflow job should be shown in the related jobs
    # joblets of the workflow job should NOT be shown
    assert job_ids == [workflow_job.pk]


@pytest.mark.django_db
def test_block_unprocessed_events(delete, admin_user, mocker):
    time_of_finish = parse("Thu Feb 28 09:10:20 2013 -0500")
    job = Job.objects.create(
        emitted_events=1,
        status='finished',
        finished=time_of_finish
    )
    request = mock.MagicMock()

    class MockView(UnifiedJobDeletionMixin):
        model = Job

        def get_object(self):
            return job

    view = MockView()

    time_of_request = time_of_finish + relativedelta(seconds=2)
    with mock.patch('awx.api.views.mixin.now', lambda: time_of_request):
        r = view.destroy(request)
        assert r.status_code == 400


@pytest.mark.django_db
def test_block_related_unprocessed_events(mocker, organization, project, delete, admin_user):
    job_template = JobTemplate.objects.create(
        project=project,
        playbook='helloworld.yml'
    )
    time_of_finish = parse("Thu Feb 23 14:17:24 2012 -0500")
    Job.objects.create(
        emitted_events=1,
        status='finished',
        finished=time_of_finish,
        job_template=job_template,
        project=project,
        organization=project.organization
    )
    view = RelatedJobsPreventDeleteMixin()
    time_of_request = time_of_finish + relativedelta(seconds=2)
    with mock.patch('awx.api.views.mixin.now', lambda: time_of_request):
        with pytest.raises(PermissionDenied):
            view.perform_destroy(organization)


@pytest.mark.django_db
def test_disallowed_http_update_methods(put, patch, post, inventory, project, admin_user):
    jt = JobTemplate.objects.create(
        name='test_disallowed_methods', inventory=inventory,
        project=project
    )
    job = jt.create_unified_job()
    post(
        url=reverse('api:job_detail', kwargs={'pk': job.pk}),
        data={},
        user=admin_user,
        expect=405
    )
    put(
        url=reverse('api:job_detail', kwargs={'pk': job.pk}),
        data={},
        user=admin_user,
        expect=405
    )
    patch(
        url=reverse('api:job_detail', kwargs={'pk': job.pk}),
        data={},
        user=admin_user,
        expect=405
    )


class TestControllerNode():
    @pytest.fixture
    def project_update(self, project):
        return ProjectUpdate.objects.create(project=project)

    @pytest.fixture
    def job(self):
        return JobTemplate.objects.create().create_unified_job()

    @pytest.fixture
    def adhoc(self, inventory):
        return AdHocCommand.objects.create(inventory=inventory)

    @pytest.mark.django_db
    def test_field_controller_node_exists(self, sqlite_copy_expert,
                                          admin_user, job, project_update,
                                          inventory_update, adhoc, get, system_job_factory):
        system_job = system_job_factory()

        r = get(reverse('api:unified_job_list') + '?id={}'.format(job.id), admin_user, expect=200)
        assert 'controller_node' in r.data['results'][0]

        r = get(job.get_absolute_url(), admin_user, expect=200)
        assert 'controller_node' in r.data

        r = get(reverse('api:ad_hoc_command_detail', kwargs={'pk': adhoc.pk}), admin_user, expect=200)
        assert 'controller_node' in r.data

        r = get(reverse('api:project_update_detail', kwargs={'pk': project_update.pk}), admin_user, expect=200)
        assert 'controller_node' not in r.data

        r = get(reverse('api:inventory_update_detail', kwargs={'pk': inventory_update.pk}), admin_user, expect=200)
        assert 'controller_node' not in r.data

        r = get(reverse('api:system_job_detail', kwargs={'pk': system_job.pk}), admin_user, expect=200)
        assert 'controller_node' not in r.data
