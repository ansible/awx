import pytest
from unittest.mock import patch

from awx.api.versioning import reverse
from django.test.client import RequestFactory
from django.db import connection
from django.test.utils import CaptureQueriesContext

from ansible_base.rbac.models import RoleDefinition
from ansible_base.rbac import permission_registry

from awx.main.models import Role, Group, Inventory, Organization, ExecutionEnvironment, UnifiedJobTemplate, JobTemplate, WorkflowJobTemplate, SystemJobTemplate
from awx.main.access import (
    BaseAccess,
    ORGANIZATION_CAPABILITY_CODENAMES,
    get_object_permissions,
    access_registry,
    WorkflowJobTemplateAccess,
    get_user_capabilities,
    check_user_access,
    prefetch_page_permissions,
)
from awx.api.serializers import (
    InventorySerializer,
    JobTemplateSerializer,
    ProjectSerializer,
    UnifiedJobTemplateSerializer,
    WorkflowJobTemplateSerializer,
    UnifiedJobSerializer,
)

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
        objects = job_template_factory('copy-edit-job-template', project=project)
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
            inventory=None,
            ask_inventory_on_launch=False,  # not allowed
            ask_credential_on_launch=True,
            name='deploy-job-template',
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
        """JT admin permission enables the copy and edit capabilities.

        Copy requests enforce related-resource policies and explain denials.
        """

        # random user given JT admin access only
        jt_copy_edit.admin_role.members.add(rando)
        jt_copy_edit.save()

        serializer = JobTemplateSerializer(jt_copy_edit, context=self.fake_context(rando))
        response = serializer.to_representation(jt_copy_edit)
        assert response['summary_fields']['user_capabilities']['copy']
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
    mock_method.__name__ = 'bars'  # Required for a logging statement
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

    def test_access_list_direct_access_capability(self, inventory, rando, get, mocker, mock_access_method):
        inventory.admin_role.members.add(rando)

        mocker.patch.object(access_registry[Role], 'can_unattach', mock_access_method)
        response = get(reverse('api:inventory_access_list', kwargs={'pk': inventory.id}), rando)

        mock_access_method.assert_called_once_with(inventory.admin_role, rando, 'members', **self.extra_kwargs)
        self._assert_one_in_list(response.data)
        direct_access_list = response.data['results'][0]['summary_fields']['direct_access']
        assert direct_access_list[0]['role']['user_capabilities']['unattach'] == 'foobar'

    def test_access_list_indirect_access_capability(self, inventory, organization, org_admin, get, mocker, mock_access_method):
        mocker.patch.object(access_registry[Role], 'can_unattach', mock_access_method)
        response = get(reverse('api:inventory_access_list', kwargs={'pk': inventory.id}), org_admin)

        mock_access_method.assert_called_once_with(organization.admin_role, org_admin, 'members', **self.extra_kwargs)
        self._assert_one_in_list(response.data, sublist='indirect_access')
        indirect_access_list = response.data['results'][0]['summary_fields']['indirect_access']
        assert indirect_access_list[0]['role']['user_capabilities']['unattach'] == 'foobar'

    def test_access_list_team_direct_access_capability(self, inventory, team, team_member, get, mocker, mock_access_method):
        team.member_role.children.add(inventory.admin_role)

        mocker.patch.object(access_registry[Role], 'can_unattach', mock_access_method)
        response = get(reverse('api:inventory_access_list', kwargs={'pk': inventory.id}), team_member)

        mock_access_method.assert_called_once_with(inventory.admin_role, team.member_role, 'parents', **self.extra_kwargs)
        self._assert_one_in_list(response.data)
        direct_access_list = response.data['results'][0]['summary_fields']['direct_access']
        assert direct_access_list[0]['role']['user_capabilities']['unattach'] == 'foobar'


@pytest.mark.django_db
def test_team_roles_unattach(mocker, team, team_member, inventory, mock_access_method, get):
    team.member_role.children.add(inventory.admin_role)

    mocker.patch.object(access_registry[Role], 'can_unattach', mock_access_method)
    response = get(reverse('api:team_roles_list', kwargs={'pk': team.id}), team_member)

    # Did we assess whether team_member can remove team's permission to the inventory?
    mock_access_method.assert_called_once_with(inventory.admin_role, team.member_role, 'parents', skip_sub_obj_read_check=True, data={})
    assert response.data['results'][0]['summary_fields']['user_capabilities']['unattach'] == 'foobar'


@pytest.mark.django_db
def test_user_roles_unattach(mocker, organization, alice, bob, mock_access_method, get):
    # Add to same organization so that alice and bob can see each other
    organization.member_role.members.add(alice)
    organization.member_role.members.add(bob)

    mocker.patch.object(access_registry[Role], 'can_unattach', mock_access_method)
    response = get(reverse('api:user_roles_list', kwargs={'pk': alice.id}), bob)

    # Did we assess whether bob can remove alice's permission to the inventory?
    mock_access_method.assert_called_once_with(organization.member_role, alice, 'members', skip_sub_obj_read_check=True, data={})
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
    mapping = prefetch_page_permissions(qs, rando)
    assert 'execute_jobtemplate' in mapping.grants[JobTemplate][job_template.pk]
    assert 'change_jobtemplate' not in mapping.grants[JobTemplate][job_template.pk]


@pytest.mark.django_db
def test_prefetch_ujt_job_template_capabilities(alice, bob, job_template):
    job_template.execute_role.members.add(alice)
    qs = UnifiedJobTemplate.objects.all()
    mapping = prefetch_page_permissions(qs, alice)
    assert 'execute_jobtemplate' in mapping.grants[JobTemplate][job_template.pk]
    assert 'change_jobtemplate' not in mapping.grants[JobTemplate][job_template.pk]
    qs = UnifiedJobTemplate.objects.all()
    mapping = prefetch_page_permissions(qs, bob)
    assert mapping.grants[JobTemplate][job_template.pk] == set()


@pytest.mark.django_db
def test_prefetch_ujt_project_capabilities(alice, project, job_template, mocker):
    project.update_role.members.add(alice)
    system_template = SystemJobTemplate.objects.create(name='No capabilities')
    qs = UnifiedJobTemplate.objects.all()
    prefetch = mocker.patch('awx.api.serializers.prefetch_page_permissions', wraps=prefetch_page_permissions)

    class MockObj:
        pass

    view = MockObj()
    view.request = MockObj()
    view.request.user = alice
    view.request.method = 'GET'
    view.kwargs = {}

    list_serializer = UnifiedJobTemplateSerializer(qs, many=True, context={'view': view})

    # A child without capabilities does not trigger the lazy prefetch.
    list_serializer.child.to_representation(system_template)
    prefetch.assert_not_called()

    # Capable children share the page snapshot, using each object's concrete model.
    list_serializer.child.to_representation(project)
    list_serializer.child.to_representation(job_template)
    prefetch.assert_called_once_with(qs, alice)
    assert 'update_project' in list_serializer._prefetched_page_permissions.grants[type(project)][project.pk]


@pytest.mark.django_db
def test_prefetch_group_capabilities(group, rando):
    group.inventory.adhoc_role.members.add(rando)
    qs = Group.objects.all()
    mapping = prefetch_page_permissions(qs, rando)
    assert 'adhoc_inventory' in mapping.grants[Inventory][group.inventory_id]
    assert 'change_inventory' not in mapping.grants[Inventory][group.inventory_id]


@pytest.mark.django_db
def test_prefetch_jt_copy_capability(job_template, project, inventory, rando, django_assert_num_queries):
    job_template.read_role.members.add(rando)
    ee_org = Organization.objects.create(name='EE organization')
    ee_org.read_role.members.add(rando)
    job_template.execution_environment = ExecutionEnvironment.objects.create(name='EE', image='example.com/ee', organization=ee_org)
    job_template.project = project
    job_template.inventory = inventory
    job_template.save()

    qs = JobTemplate.objects.select_related('project', 'inventory')
    mapping = prefetch_page_permissions(qs, rando)
    page_template = next(obj for obj in qs if obj.pk == job_template.pk)
    # Copy is an option for a visible source; related policies are checked on POST.
    with django_assert_num_queries(0):
        assert get_user_capabilities(rando, page_template, prefetched_permissions=mapping, method_list=['copy'])['copy']


@pytest.mark.django_db
def test_workflow_orphaned_capabilities(rando):
    wfjt = WorkflowJobTemplate.objects.create(name='test', organization=None)
    wfjt.admin_role.members.add(rando)
    access = WorkflowJobTemplateAccess(rando)
    assert not access.get_user_capabilities(wfjt, method_list=['edit', 'copy'])['copy']


@pytest.mark.django_db
def test_manual_projects_no_update(manual_project, get, admin_user):
    response = get(reverse('api:project_detail', kwargs={'pk': manual_project.pk}), admin_user, expect=200)
    assert not response.data['summary_fields']['user_capabilities']['start']
    assert not response.data['summary_fields']['user_capabilities']['schedule']


@pytest.mark.django_db
def test_inventory_list_capabilities_query_count(get, alice, organization):
    """A full page must distinguish change/delete without per-inventory queries."""
    expected = {}
    for index, permissions in enumerate(
        (['view_inventory'], ['view_inventory', 'change_inventory'], ['view_inventory', 'change_inventory', 'delete_inventory'])
    ):
        role = RoleDefinition.objects.create_from_permissions(
            name=f'inventory-capabilities-{index}',
            permissions=permissions,
            content_type=permission_registry.content_type_model.objects.get_for_model(Inventory),
        )
        for number in range(9):
            inventory = Inventory.objects.create(name=f'capabilities-{index}-{number}', organization=organization)
            role.give_permission(alice, inventory)
            expected[inventory.pk] = {'edit': index > 0, 'delete': index == 2, 'adhoc': False, 'copy': True}

    url = reverse('api:inventory_list')
    # Warm permission metadata, as in a running API process.
    get(url, alice, data={'page_size': 1}, expect=200)
    counts = []
    for page_size in (1, 25):
        with CaptureQueriesContext(connection) as queries:
            response = get(url, alice, data={'page_size': page_size}, expect=200)
        assert len(response.data['results']) == page_size
        for item in response.data['results']:
            assert item['summary_fields']['user_capabilities'] == expected[item['id']]
        counts.append(len(queries))
    assert counts[1] == counts[0], counts
    assert counts[1] <= 8, counts


@pytest.mark.django_db
def test_page_permissions_are_bound_to_actor_and_objects(inventory, alice, bob):
    inventory.admin_role.members.add(alice)
    alice_permissions = prefetch_page_permissions([inventory], alice)
    bob_permissions = prefetch_page_permissions([inventory], bob)
    assert alice_permissions.actor is alice
    assert alice_permissions.grants[Inventory].keys() == {inventory.pk}
    assert bob_permissions.grants[Inventory][inventory.pk] == set()

    assert get_user_capabilities(alice, inventory, prefetched_permissions=alice_permissions, method_list=['edit']) == {'edit': True}
    assert get_user_capabilities(bob, inventory, prefetched_permissions=bob_permissions, method_list=['edit']) == {'edit': False}
    with pytest.raises(ValueError, match='different actor'):
        get_user_capabilities(bob, inventory, prefetched_permissions=alice_permissions, method_list=['edit'])
    assert not bob.has_obj_perm(inventory, 'change')


@pytest.mark.django_db
def test_page_snapshot_does_not_cache_authorization(inventory, alice, organization):
    snapshot = prefetch_page_permissions([inventory], alice)
    inventory.admin_role.members.add(alice)
    assert alice.has_obj_perm(inventory, 'change')
    assert check_user_access(alice, Inventory, 'change', inventory, {})

    # An object created after prefetch is outside the snapshot. Its creator's
    # new grant must be visible immediately, including during rendering.
    new_inventory = Inventory.objects.create(name='created after prefetch', organization=organization)
    new_inventory.admin_role.members.add(alice)
    assert check_user_access(alice, Inventory, 'change', new_inventory, {})
    assert get_user_capabilities(alice, new_inventory, prefetched_permissions=snapshot, method_list=['edit']) == {'edit': True}

    granted_snapshot = prefetch_page_permissions([inventory], alice)
    assert get_user_capabilities(alice, inventory, prefetched_permissions=granted_snapshot, method_list=['edit']) == {'edit': True}
    inventory.admin_role.members.remove(alice)
    assert not alice.has_obj_perm(inventory, 'change')
    assert not check_user_access(alice, Inventory, 'change', inventory, {})
    assert get_user_capabilities(alice, inventory, method_list=['edit']) == {'edit': False}


@pytest.mark.django_db
@pytest.mark.parametrize('rendering', ['list', 'no_capabilities', 'no_summary_fields', 'detail', 'empty_list', 'superuser'])
def test_permission_prefetch_only_when_rendering_list_capabilities(get, inventory, alice, admin_user, mocker, rendering):
    inventory.read_role.members.add(alice)
    prefetch = mocker.patch('awx.api.serializers.prefetch_page_permissions', wraps=prefetch_page_permissions)
    url = reverse('api:inventory_list')
    params = {}
    if rendering == 'no_capabilities':
        mocker.patch.object(InventorySerializer, 'show_capabilities', [])
    elif rendering == 'no_summary_fields':
        mocker.patch.object(InventorySerializer.Meta, 'fields', ('id',))
    elif rendering == 'detail':
        url = reverse('api:inventory_detail', kwargs={'pk': inventory.pk})
    elif rendering == 'empty_list':
        params['id'] = 0

    response = get(url, admin_user if rendering == 'superuser' else alice, data=params, expect=200)
    if rendering == 'empty_list':
        assert response.data['results'] == []
    else:
        item = response.data if rendering == 'detail' else response.data['results'][0]
        if rendering == 'no_summary_fields':
            assert 'summary_fields' not in item
        elif rendering == 'no_capabilities':
            assert 'user_capabilities' not in item['summary_fields']
        else:
            allowed = rendering == 'superuser'
            assert item['summary_fields']['user_capabilities'] == {**dict.fromkeys(['edit', 'delete', 'adhoc'], allowed), 'copy': True}
    if rendering == 'list':
        prefetch.assert_called_once()
        page, actor = prefetch.call_args.args
        assert [obj.pk for obj in page] == [inventory.pk]
        assert actor.pk == alice.pk
    else:
        prefetch.assert_not_called()


@pytest.mark.django_db
def test_capabilities_resolved_without_permissions_do_not_prefetch(get, manual_project, alice, mocker):
    manual_project.read_role.members.add(alice)
    mocker.patch.object(ProjectSerializer, 'show_capabilities', ['start', 'schedule'])
    prefetch = mocker.patch('awx.api.serializers.prefetch_page_permissions', wraps=prefetch_page_permissions)

    response = get(reverse('api:project_list'), alice, expect=200)

    assert len(response.data['results']) == 1
    assert response.data['results'][0]['summary_fields']['user_capabilities'] == {'start': False, 'schedule': False}
    prefetch.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize('jobs', [False, True], ids=['templates', 'jobs'])
def test_prefetch_permissions_for_mixed_page(job_template, workflow_job_template, alice, bob, jobs, django_assert_num_queries):
    job_template.execute_role.members.add(alice)
    workflow_job_template.read_role.members.add(alice)
    outside_page = JobTemplate.objects.create(name='Not on the page')
    outside_page.admin_role.members.add(alice)
    page = [job_template, workflow_job_template]
    if jobs:
        page = [template.create_unified_job() for template in page]

    with django_assert_num_queries(0):
        snapshot = prefetch_page_permissions(page, alice)
    with django_assert_num_queries(1):
        snapshot.grants[JobTemplate][job_template.pk]
    with django_assert_num_queries(0):
        snapshot.grants[JobTemplate][job_template.pk]
    with django_assert_num_queries(1):
        snapshot.grants[WorkflowJobTemplate][workflow_job_template.pk]
    assert snapshot.actor is alice
    assert snapshot.grants[JobTemplate].keys() == {job_template.pk}
    assert snapshot.grants[WorkflowJobTemplate].keys() == {workflow_job_template.pk}
    assert 'execute_jobtemplate' in snapshot.grants[JobTemplate][job_template.pk]
    assert 'change_jobtemplate' not in snapshot.grants[JobTemplate][job_template.pk]
    assert 'view_workflowjobtemplate' in snapshot.grants[WorkflowJobTemplate][workflow_job_template.pk]
    assert 'execute_workflowjobtemplate' not in snapshot.grants[WorkflowJobTemplate][workflow_job_template.pk]
    assert all(not grants for by_pk in prefetch_page_permissions(page, bob).grants.values() for grants in by_pk.values())


@pytest.mark.django_db
def test_organization_prefetch_filters_codenames(organization, alice, django_assert_num_queries, mocker):
    organization.admin_role.members.add(alice)
    snapshot = prefetch_page_permissions([organization], alice)
    with django_assert_num_queries(1) as queries:
        grants = snapshot.grants[Organization][organization.pk]
    assert {'change_organization', 'add_workflowjobtemplate'} <= grants
    assert grants <= ORGANIZATION_CAPABILITY_CODENAMES
    assert 'view_organization' not in grants
    assert '"codename" IN' in queries.captured_queries[0]['sql']

    access = BaseAccess(alice, prefetched_permissions=snapshot)
    live_check = mocker.spy(alice, 'has_obj_perm')
    assert access.has_permission_with_prefetch(organization, 'change')
    live_check.assert_not_called()
    # A permission outside the filter requires a live check.
    assert access.has_permission_with_prefetch(organization, 'view')
    live_check.assert_called_once_with(organization, 'view_organization')


@pytest.mark.django_db
@pytest.mark.parametrize('jobs', [False, True], ids=['templates', 'jobs'])
def test_unified_list_capabilities_query_count(get, alice, organization, project, inventory, jobs):
    """Compare mixed pages of the same model composition, with and without capabilities."""
    project.use_role.members.add(alice)
    inventory.use_role.members.add(alice)
    private_org = Organization.objects.create(name='Private execution environments')
    ee = ExecutionEnvironment.objects.create(name='Private EE', image='example.com/ee', organization=private_org)
    expected = {}
    roles = {}
    for model in (JobTemplate, WorkflowJobTemplate):
        name = model._meta.model_name
        for allowed in (False, True):
            permissions = [f'view_{name}']
            if allowed:
                permissions.append(f'execute_{name}')
                if model is WorkflowJobTemplate:
                    permissions.append(f'change_{name}')
            roles[model, allowed] = RoleDefinition.objects.create_from_permissions(
                name=f'{name}-{allowed}',
                permissions=permissions,
                content_type=permission_registry.content_type_model.objects.get_for_model(model),
            )
    for index in range(12):
        for model in (JobTemplate, WorkflowJobTemplate):
            allowed = (index % 2 == 0) == (model is JobTemplate)
            fields = {'project': project, 'inventory': inventory, 'playbook': 'helloworld.yml', 'execution_environment': ee} if model is JobTemplate else {}
            template = model.objects.create(name=f'page-{index}-{model.__name__}', organization=organization, **fields)
            roles[model, allowed].give_permission(alice, template)
            if jobs:
                obj = template.create_unified_job()
                expected[obj.pk] = {'start': allowed, 'delete': False}
            else:
                expected[template.pk] = {
                    'edit': allowed and model is WorkflowJobTemplate,
                    'delete': allowed and model is WorkflowJobTemplate,
                    'start': allowed,
                    'schedule': allowed,
                    'copy': True,
                }

    url = reverse('api:unified_job_list' if jobs else 'api:unified_job_template_list')
    params = {'order_by': 'id', 'id__in': ','.join(str(pk) for pk in expected)}
    get(url, alice, data={**params, 'page_size': 24}, expect=200)
    counts = []
    permission_counts = []
    baseline_counts = []
    prefetch_calls = []
    expected_models = {JobTemplate, WorkflowJobTemplate} | ({Organization} if jobs else set())

    def measured_prefetch(user, model, ids, **kwargs):
        assert kwargs == ({'codenames': ORGANIZATION_CAPABILITY_CODENAMES} if model is Organization else {})
        with CaptureQueriesContext(connection) as queries:
            grants = get_object_permissions(user, model, ids, **kwargs)
        prefetch_calls.append((model, len(queries)))
        return grants

    for page_size in (2, 24):
        prefetch_calls.clear()
        with patch('awx.main.access.get_object_permissions', side_effect=measured_prefetch), CaptureQueriesContext(connection) as queries:
            response = get(url, alice, data={**params, 'page_size': page_size}, expect=200)
        assert len(response.data['results']) == page_size
        assert {item['type'] for item in response.data['results']} == ({'job', 'workflow_job'} if jobs else {'job_template', 'workflow_job_template'})
        for item in response.data['results']:
            assert item['summary_fields']['user_capabilities'] == expected[item['id']]
        assert len(prefetch_calls) == len(expected_models)
        assert {model for model, count in prefetch_calls} == expected_models
        assert all(count == 1 for model, count in prefetch_calls)
        counts.append(len(queries))
        permission_counts.append(sum('dab_rbac_roleevaluation' in q['sql'].lower() for q in queries))
        with patch.object(UnifiedJobSerializer if jobs else JobTemplateSerializer, 'show_capabilities', []):
            with patch.object(WorkflowJobTemplateSerializer, 'show_capabilities', []):
                with CaptureQueriesContext(connection) as baseline_queries:
                    get(url, alice, data={**params, 'page_size': page_size}, expect=200)
        baseline_counts.append(len(baseline_queries))
    assert 0 < permission_counts[0] == permission_counts[1] <= len(expected_models) + 2, permission_counts
    # Each workflow job's delete check loads its template's organization.
    # Subtract those relation queries to measure the permission batch overhead.
    capability_overhead = [count - baseline - (size // 2 if jobs else 0) for count, baseline, size in zip(counts, baseline_counts, (2, 24))]
    # One query per needed model, plus at most one timed settings-cache refresh.
    assert max(capability_overhead) <= len(expected_models) + 1, (counts, baseline_counts)


@pytest.mark.django_db
@pytest.mark.parametrize('can_read_ee', [False, True])
def test_copy_capability_defers_ee_policy_with_detailed_denial(get, post, alice, project, inventory, organization, can_read_ee):
    private_org = Organization.objects.create(name='Private EE organization')
    ee = ExecutionEnvironment.objects.create(name='Private EE', image='example.com/ee', organization=private_org)
    template = JobTemplate.objects.create(
        name='Copy with EE', organization=organization, project=project, inventory=inventory, playbook='helloworld.yml', execution_environment=ee
    )
    template.read_role.members.add(alice)
    project.use_role.members.add(alice)
    inventory.use_role.members.add(alice)
    if can_read_ee:
        private_org.read_role.members.add(alice)

    response = get(reverse('api:job_template_list'), alice, data={'id': template.pk}, expect=200)
    assert response.data['results'][0]['summary_fields']['user_capabilities']['copy'] is True
    before = JobTemplate.objects.count()
    response = post(reverse('api:job_template_copy', kwargs={'pk': template.pk}), alice, data={'name': 'Copy'}, expect=201 if can_read_ee else 403)
    if can_read_ee:
        assert response.data['execution_environment'] == ee.pk
        assert JobTemplate.objects.count() == before + 1
    else:
        assert response.data == {'execution_environment': ['You do not have read access to the execution environment.']}
        assert JobTemplate.objects.count() == before


@pytest.mark.django_db
@pytest.mark.parametrize('model,denied_field', [(JobTemplate, 'inventory'), (JobTemplate, 'project'), (WorkflowJobTemplate, 'organization')])
def test_template_copy_capability_defers_related_denials(get, post, alice, project, inventory, organization, model, denied_field):
    fields = {'project': project, 'inventory': inventory, 'playbook': 'helloworld.yml'} if model is JobTemplate else {}
    template = model.objects.create(name='Copy policy', organization=organization, **fields)
    template.read_role.members.add(alice)
    if denied_field != 'inventory':
        inventory.use_role.members.add(alice)
    if denied_field != 'project':
        project.use_role.members.add(alice)
    response = get(reverse('api:unified_job_template_list'), alice, data={'id': template.pk}, expect=200)
    assert response.data['results'][0]['summary_fields']['user_capabilities']['copy'] is True

    endpoint = 'job_template' if model is JobTemplate else 'workflow_job_template'
    before = model.objects.count()
    response = post(reverse(f'api:{endpoint}_copy', kwargs={'pk': template.pk}), alice, data={'name': 'Copy'}, expect=403)
    expected = {
        'inventory': ['You do not have use permission on Inventory'],
        'project': ['You do not have use permission on Project'],
        'organization': ['You do not have permission to create workflow job templates in this organization.'],
    }
    assert response.data == {denied_field: expected[denied_field]}
    assert model.objects.count() == before


@pytest.mark.django_db
@pytest.mark.parametrize(
    'fixture_name,endpoint,resource_label',
    [
        ('inventory', 'inventory', 'inventories'),
        ('project', 'project', 'projects'),
        ('execution_environment', 'execution_environment', 'execution environments'),
        ('notification_template', 'notification_template', 'notification templates'),
    ],
)
def test_copy_capability_defers_organization_permission(get, post, request, alice, organization, mocker, fixture_name, endpoint, resource_label):
    obj = request.getfixturevalue(fixture_name)
    if isinstance(obj, ExecutionEnvironment):
        obj.organization = organization
        obj.save(update_fields=['organization'])
        organization.read_role.members.add(alice)
    else:
        role = RoleDefinition.objects.create_from_permissions(
            name='Read copy source',
            permissions=[f'view_{obj._meta.model_name}'],
            content_type=permission_registry.content_type_model.objects.get_for_model(type(obj)),
        )
        role.give_permission(alice, obj)
    prefetch = mocker.patch('awx.main.access.get_object_permissions', wraps=get_object_permissions)
    response = get(reverse(f'api:{endpoint}_list'), alice, data={'id': obj.pk}, expect=200)
    assert response.data['results'][0]['summary_fields']['user_capabilities']['copy'] is True
    assert all(call.args[1] is not Organization for call in prefetch.call_args_list)

    before = type(obj).objects.count()
    response = post(reverse(f'api:{endpoint}_copy', kwargs={'pk': obj.pk}), alice, data={'name': 'Copy'}, expect=403)
    assert response.data == {'organization': [f'You do not have permission to create {resource_label} in this organization.']}
    assert type(obj).objects.count() == before


@pytest.mark.django_db
def test_public_execution_environment_copy_denial_explains_missing_organization(get, post, alice, execution_environment):
    response = get(reverse('api:execution_environment_list'), alice, data={'id': execution_environment.pk}, expect=200)
    assert response.data['results'][0]['summary_fields']['user_capabilities']['copy'] is True
    response = post(reverse('api:execution_environment_copy', kwargs={'pk': execution_environment.pk}), alice, data={'name': 'Copy'}, expect=403)
    assert response.data == {'organization': ['You must be a system administrator to create this resource without specifying organization.']}


@pytest.mark.django_db
@pytest.mark.parametrize('denied_field', ['credential', 'default_environment'])
def test_project_copy_capability_defers_related_permission(get, post, alice, project, organization, scm_credential, denied_field):
    project.read_role.members.add(alice)
    organization.project_admin_role.members.add(alice)
    if denied_field == 'credential':
        project.credential = scm_credential
        expected_message = 'You do not have use permission on the credential.'
    else:
        private_org = Organization.objects.create(name='Private environments')
        project.default_environment = ExecutionEnvironment.objects.create(name='Private EE', organization=private_org, image='example.com/ee')
        expected_message = 'You do not have read access to the execution environment.'
    project.save(update_fields=[denied_field])

    response = get(reverse('api:project_list'), alice, data={'id': project.pk}, expect=200)
    assert response.data['results'][0]['summary_fields']['user_capabilities']['copy'] is True
    before = type(project).objects.count()
    response = post(reverse('api:project_copy', kwargs={'pk': project.pk}), alice, data={'name': 'Copy'}, expect=403)
    assert response.data == {denied_field: [expected_message]}
    assert type(project).objects.count() == before


@pytest.mark.django_db
def test_job_delete_capability_matches_authorization(get, delete, alice, job_template, organization):
    job_template.organization = organization
    job_template.save(update_fields=['organization'])
    job_template.read_role.members.add(alice)
    job = job_template.create_unified_job(_eager_fields={'status': 'successful'})
    url = reverse('api:unified_job_list')
    response = get(url, alice, data={'id': job.pk}, expect=200)
    assert response.data['results'][0]['summary_fields']['user_capabilities']['delete'] is False
    delete(reverse('api:job_detail', kwargs={'pk': job.pk}), alice, expect=403)

    role = RoleDefinition.objects.create_from_permissions(
        name='Organization change for job deletion',
        managed=True,
        permissions=['view_organization', 'change_organization'],
        content_type=permission_registry.content_type_model.objects.get_for_model(Organization),
    )
    role.give_permission(alice, job.organization)
    response = get(url, alice, data={'id': job.pk}, expect=200)
    assert response.data['results'][0]['summary_fields']['user_capabilities']['delete'] is True
    delete(reverse('api:job_detail', kwargs={'pk': job.pk}), alice, expect=204)
    assert not type(job).objects.filter(pk=job.pk).exists()


@pytest.mark.django_db
def test_workflow_delete_capability_matches_authorization(get, delete, alice, workflow_job_template):
    workflow_job_template.read_role.members.add(alice)
    organization = workflow_job_template.organization
    role = RoleDefinition.objects.create_from_permissions(
        name='Organization change only',
        managed=True,
        permissions=['view_organization', 'change_organization'],
        content_type=permission_registry.content_type_model.objects.get_for_model(Organization),
    )
    role.give_permission(alice, organization)
    job = workflow_job_template.create_unified_job(_eager_fields={'status': 'successful'})
    assert alice.has_obj_perm(organization, 'change')
    assert not alice.has_obj_perm(organization, 'add_workflowjobtemplate')
    response = get(reverse('api:unified_job_list'), alice, data={'id': job.pk}, expect=200)
    assert response.data['results'][0]['summary_fields']['user_capabilities']['delete'] is False

    delete(reverse('api:workflow_job_detail', kwargs={'pk': job.pk}), alice, expect=403)
    assert type(job).objects.filter(pk=job.pk).exists()

    organization.workflow_admin_role.members.add(alice)
    response = get(reverse('api:unified_job_list'), alice, data={'id': job.pk}, expect=200)
    assert response.data['results'][0]['summary_fields']['user_capabilities']['delete'] is True
    delete(reverse('api:workflow_job_detail', kwargs={'pk': job.pk}), alice, expect=204)
    assert not type(job).objects.filter(pk=job.pk).exists()
