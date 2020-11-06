import pytest

from awx.api.versioning import reverse
from django.test.client import RequestFactory

from awx.main.models import Role, Group, UnifiedJobTemplate, JobTemplate, WorkflowJobTemplate
from awx.main.access import access_registry, WorkflowJobTemplateAccess
from awx.main.utils import prefetch_page_capabilities
from awx.api.serializers import JobTemplateSerializer, UnifiedJobTemplateSerializer

# This file covers special-cases of displays of user_capabilities
# general functionality should be covered fully by unit tests, see:
#   awx/main/tests/unit/api/serializers/test_job_template_serializers.py ::
#           TestJobTemplateSerializerGetSummaryFields.test_copy_edit_standard
#   awx/main/tests/unit/test_access.py ::
#           test_user_capabilities_method


@pytest.mark.django_db
class TestOptionsRBAC:
    """
    Several endpoints are relied-upon by the UI to list POST as an
    allowed action or not depending on whether the user has permission
    to create a resource.
    """

    def test_inventory_group_host_can_add(self, inventory, alice, options):
        inventory.admin_role.members.add(alice)

        response = options(reverse('api:inventory_hosts_list', kwargs={'pk': inventory.pk}), alice)
        assert 'POST' in response.data['actions']
        response = options(reverse('api:inventory_groups_list', kwargs={'pk': inventory.pk}), alice)
        assert 'POST' in response.data['actions']

    def test_inventory_group_host_can_not_add(self, inventory, bob, options):
        inventory.read_role.members.add(bob)

        response = options(reverse('api:inventory_hosts_list', kwargs={'pk': inventory.pk}), bob)
        assert 'POST' not in response.data['actions']
        response = options(reverse('api:inventory_groups_list', kwargs={'pk': inventory.pk}), bob)
        assert 'POST' not in response.data['actions']

    def test_user_list_can_add(self, org_member, org_admin, options):
        response = options(reverse('api:user_list'), org_admin)
        assert 'POST' in response.data['actions']

    def test_user_list_can_not_add(self, org_member, org_admin, options):
        response = options(reverse('api:user_list'), org_member)
        assert 'POST' not in response.data['actions']


@pytest.mark.django_db
class TestJobTemplateCopyEdit:
    """
    Tests contain scenarios that were raised as issues in the past,
    which resulted from failed copy/edit actions even though the buttons
    to do these actions were displayed.
    """

    @pytest.fixture
    def jt_copy_edit(self, job_template_factory, project):
        objects = job_template_factory(
            'copy-edit-job-template',
            project=project)
        return objects.job_template

    def fake_context(self, user):
        request = RequestFactory().get('/api/v2/resource/42/')
        request.user = user

        class FakeView(object):
            pass

        fake_view = FakeView()
        fake_view.request = request
        fake_view.kwargs = {'pk': '42'}
        context = {}
        context['view'] = fake_view
        context['request'] = request
        return context

    def test_validation_bad_data_copy_edit(self, admin_user, project):
        """
        If a required resource (inventory here) was deleted, copying not allowed
        because doing so would caues a validation error
        """

        jt_res = JobTemplate.objects.create(
            job_type='run',
            project=project,
            inventory=None,  ask_inventory_on_launch=False, # not allowed
            ask_credential_on_launch=True, name='deploy-job-template'
        )
        serializer = JobTemplateSerializer(jt_res, context=self.fake_context(admin_user))
        response = serializer.to_representation(jt_res)
        assert not response['summary_fields']['user_capabilities']['copy']
        assert response['summary_fields']['user_capabilities']['edit']

    def test_sys_admin_copy_edit(self, jt_copy_edit, admin_user):
        "Absent a validation error, system admins can do everything"
        serializer = JobTemplateSerializer(jt_copy_edit, context=self.fake_context(admin_user))
        response = serializer.to_representation(jt_copy_edit)
        assert response['summary_fields']['user_capabilities']['copy']
        assert response['summary_fields']['user_capabilities']['edit']

    def test_org_admin_copy_edit(self, jt_copy_edit, org_admin):
        "Organization admins SHOULD be able to copy a JT firmly in their org"
        serializer = JobTemplateSerializer(jt_copy_edit, context=self.fake_context(org_admin))
        response = serializer.to_representation(jt_copy_edit)
        assert response['summary_fields']['user_capabilities']['copy']
        assert response['summary_fields']['user_capabilities']['edit']

    def test_jt_admin_copy_edit(self, jt_copy_edit, rando):
        """
        JT admins wihout access to associated resources SHOULD NOT be able to copy
        SHOULD be able to make nonsensitive changes"""

        # random user given JT admin access only
        jt_copy_edit.admin_role.members.add(rando)
        jt_copy_edit.save()

        serializer = JobTemplateSerializer(jt_copy_edit, context=self.fake_context(rando))
        response = serializer.to_representation(jt_copy_edit)
        assert not response['summary_fields']['user_capabilities']['copy']
        assert response['summary_fields']['user_capabilities']['edit']

    def test_proj_jt_admin_copy_edit(self, jt_copy_edit, rando):
        "JT admins with access to associated resources SHOULD be able to copy"

        # random user given JT and project admin abilities
        jt_copy_edit.admin_role.members.add(rando)
        jt_copy_edit.save()
        jt_copy_edit.project.admin_role.members.add(rando)
        jt_copy_edit.project.save()

        serializer = JobTemplateSerializer(jt_copy_edit, context=self.fake_context(rando))
        response = serializer.to_representation(jt_copy_edit)
        assert response['summary_fields']['user_capabilities']['copy']
        assert response['summary_fields']['user_capabilities']['edit']


@pytest.fixture
def mock_access_method(mocker):
    mock_method = mocker.MagicMock()
    mock_method.return_value = 'foobar'
    mock_method.__name__ = 'bars' # Required for a logging statement
    return mock_method


@pytest.mark.django_db
class TestAccessListCapabilities:
    """
    Test that the access_list serializer shows the exact output of the RoleAccess.can_attach
     - looks at /api/v2/inventories/N/access_list/
     - test for types: direct, indirect, and team access
    """

    extra_kwargs = dict(skip_sub_obj_read_check=False, data={})

    def _assert_one_in_list(self, data, sublist='direct_access'):
        "Establish that exactly 1 type of access exists so we know the entry is the right one"
        assert len(data['results']) == 1
        assert len(data['results'][0]['summary_fields'][sublist]) == 1

    def test_access_list_direct_access_capability(
            self, inventory, rando, get, mocker, mock_access_method):
        inventory.admin_role.members.add(rando)

        with mocker.patch.object(access_registry[Role], 'can_unattach', mock_access_method):
            response = get(reverse('api:inventory_access_list', kwargs={'pk': inventory.id}), rando)

        mock_access_method.assert_called_once_with(inventory.admin_role, rando, 'members', **self.extra_kwargs)
        self._assert_one_in_list(response.data)
        direct_access_list = response.data['results'][0]['summary_fields']['direct_access']
        assert direct_access_list[0]['role']['user_capabilities']['unattach'] == 'foobar'

    def test_access_list_indirect_access_capability(
            self, inventory, organization, org_admin, get, mocker, mock_access_method):
        with mocker.patch.object(access_registry[Role], 'can_unattach', mock_access_method):
            response = get(reverse('api:inventory_access_list', kwargs={'pk': inventory.id}), org_admin)

        mock_access_method.assert_called_once_with(organization.admin_role, org_admin, 'members', **self.extra_kwargs)
        self._assert_one_in_list(response.data, sublist='indirect_access')
        indirect_access_list = response.data['results'][0]['summary_fields']['indirect_access']
        assert indirect_access_list[0]['role']['user_capabilities']['unattach'] == 'foobar'

    def test_access_list_team_direct_access_capability(
            self, inventory, team, team_member, get, mocker, mock_access_method):
        team.member_role.children.add(inventory.admin_role)

        with mocker.patch.object(access_registry[Role], 'can_unattach', mock_access_method):
            response = get(reverse('api:inventory_access_list', kwargs={'pk': inventory.id}), team_member)

        mock_access_method.assert_called_once_with(inventory.admin_role, team.member_role, 'parents', **self.extra_kwargs)
        self._assert_one_in_list(response.data)
        direct_access_list = response.data['results'][0]['summary_fields']['direct_access']
        assert direct_access_list[0]['role']['user_capabilities']['unattach'] == 'foobar'


@pytest.mark.django_db
def test_team_roles_unattach(mocker, team, team_member, inventory, mock_access_method, get):
    team.member_role.children.add(inventory.admin_role)

    with mocker.patch.object(access_registry[Role], 'can_unattach', mock_access_method):
        response = get(reverse('api:team_roles_list', kwargs={'pk': team.id}), team_member)

    # Did we assess whether team_member can remove team's permission to the inventory?
    mock_access_method.assert_called_once_with(
        inventory.admin_role, team.member_role, 'parents', skip_sub_obj_read_check=True, data={})
    assert response.data['results'][0]['summary_fields']['user_capabilities']['unattach'] == 'foobar'


@pytest.mark.django_db
def test_user_roles_unattach(mocker, organization, alice, bob, mock_access_method, get):
    # Add to same organization so that alice and bob can see each other
    organization.member_role.members.add(alice)
    organization.member_role.members.add(bob)

    with mocker.patch.object(access_registry[Role], 'can_unattach', mock_access_method):
        response = get(reverse('api:user_roles_list', kwargs={'pk': alice.id}), bob)

    # Did we assess whether bob can remove alice's permission to the inventory?
    mock_access_method.assert_called_once_with(
        organization.member_role, alice, 'members', skip_sub_obj_read_check=True, data={})
    assert response.data['results'][0]['summary_fields']['user_capabilities']['unattach'] == 'foobar'


@pytest.mark.django_db
def test_team_roles_unattach_functional(team, team_member, inventory, get):
    team.member_role.children.add(inventory.admin_role)
    response = get(reverse('api:team_roles_list', kwargs={'pk': team.id}), team_member)
    # Team member should be able to remove access to inventory, becauase
    # the inventory admin_role grants that ability
    assert response.data['results'][0]['summary_fields']['user_capabilities']['unattach']


@pytest.mark.django_db
def test_user_roles_unattach_functional(organization, alice, bob, get):
    organization.member_role.members.add(alice)
    organization.member_role.members.add(bob)
    response = get(reverse('api:user_roles_list', kwargs={'pk': alice.id}), bob)
    # Org members cannot revoke the membership of other members
    assert not response.data['results'][0]['summary_fields']['user_capabilities']['unattach']


@pytest.mark.django_db
def test_prefetch_jt_capabilities(job_template, rando):
    job_template.execute_role.members.add(rando)
    qs = JobTemplate.objects.all()
    mapping = prefetch_page_capabilities(JobTemplate, qs, ['admin', 'execute'], rando)
    assert mapping[job_template.id] == {'edit': False, 'start': True}


@pytest.mark.django_db
def test_prefetch_ujt_job_template_capabilities(alice, bob, job_template):
    job_template.execute_role.members.add(alice)
    qs = UnifiedJobTemplate.objects.all()
    mapping = prefetch_page_capabilities(UnifiedJobTemplate, qs, ['admin', 'execute'], alice)
    assert mapping[job_template.id] == {'edit': False, 'start': True}
    qs = UnifiedJobTemplate.objects.all()
    mapping = prefetch_page_capabilities(UnifiedJobTemplate, qs, ['admin', 'execute'], bob)
    assert mapping[job_template.id] == {'edit': False, 'start': False}


@pytest.mark.django_db
def test_prefetch_ujt_project_capabilities(alice, project, job_template, mocker):
    project.update_role.members.add(alice)
    qs = UnifiedJobTemplate.objects.all()

    class MockObj:
        pass

    view = MockObj()
    view.request = MockObj()
    view.request.user = alice
    view.request.method = 'GET'
    view.kwargs = {}

    list_serializer = UnifiedJobTemplateSerializer(qs, many=True, context={'view': view})

    # Project form of UJT serializer does not fill in or reference the prefetch dict
    list_serializer.child.to_representation(project)
    assert 'capability_map' not in list_serializer.child.context


@pytest.mark.django_db
def test_prefetch_group_capabilities(group, rando):
    group.inventory.adhoc_role.members.add(rando)
    qs = Group.objects.all()
    mapping = prefetch_page_capabilities(Group, qs, ['inventory.admin', 'inventory.adhoc'], rando)
    assert mapping[group.id] == {'edit': False, 'adhoc': True}


@pytest.mark.django_db
def test_prefetch_jt_copy_capability(job_template, project, inventory, rando):
    job_template.project = project
    job_template.inventory = inventory
    job_template.save()

    qs = JobTemplate.objects.all()
    mapping = prefetch_page_capabilities(JobTemplate, qs, [{'copy': [
        'project.use', 'inventory.use',
    ]}], rando)
    assert mapping[job_template.id] == {'copy': False}

    project.use_role.members.add(rando)
    inventory.use_role.members.add(rando)

    mapping = prefetch_page_capabilities(JobTemplate, qs, [{'copy': [
        'project.use', 'inventory.use',
    ]}], rando)
    assert mapping[job_template.id] == {'copy': True}


@pytest.mark.django_db
def test_workflow_orphaned_capabilities(rando):
    wfjt = WorkflowJobTemplate.objects.create(name='test', organization=None)
    wfjt.admin_role.members.add(rando)
    access = WorkflowJobTemplateAccess(rando)
    assert not access.get_user_capabilities(
        wfjt, method_list=['edit', 'copy'],
        capabilities_cache={'copy': True}
    )['copy']


@pytest.mark.django_db
def test_manual_projects_no_update(manual_project, get, admin_user):
    response = get(reverse('api:project_detail', kwargs={'pk': manual_project.pk}), admin_user, expect=200)
    assert not response.data['summary_fields']['user_capabilities']['start']
    assert not response.data['summary_fields']['user_capabilities']['schedule']
