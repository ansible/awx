import pytest

from django.core.urlresolvers import reverse
from django.test.client import RequestFactory

from awx.main.models.jobs import JobTemplate
from awx.main.models import Role
from awx.api.serializers import JobTemplateSerializer
from awx.main.access import access_registry


# This file covers special-cases of displays of user_capabilities
# general functionality should be covered fully by unit tests, see:
#   awx/main/tests/unit/api/test_serializers.py :: 
#           TestJobTemplateSerializerGetSummaryFields.test_copy_edit_standard
#   awx/main/tests/unit/test_access.py ::
#           test_user_capabilities_method

class FakeView(object):
    pass

@pytest.fixture
def jt_copy_edit(job_template_factory, project):
    objects = job_template_factory(
        'copy-edit-job-template',
        project=project)
    return objects.job_template


@pytest.mark.django_db
def test_inventory_group_host_can_add(inventory, alice, options):
    inventory.admin_role.members.add(alice)

    response = options(reverse('api:inventory_hosts_list', args=[inventory.pk]), alice)
    assert 'POST' in response.data['actions']
    response = options(reverse('api:inventory_groups_list', args=[inventory.pk]), alice)
    assert 'POST' in response.data['actions']

@pytest.mark.django_db
def test_inventory_group_host_can_not_add(inventory, bob, options):
    inventory.read_role.members.add(bob)

    response = options(reverse('api:inventory_hosts_list', args=[inventory.pk]), bob)
    assert 'POST' not in response.data['actions']
    response = options(reverse('api:inventory_groups_list', args=[inventory.pk]), bob)
    assert 'POST' not in response.data['actions']

@pytest.mark.django_db
def test_user_list_can_add(org_member, org_admin, options):
    response = options(reverse('api:user_list'), org_admin)
    assert 'POST' in response.data['actions']

@pytest.mark.django_db
def test_user_list_can_not_add(org_member, org_admin, options):
    response = options(reverse('api:user_list'), org_member)
    assert 'POST' not in response.data['actions']


def fake_context(user):
    request = RequestFactory().get('/api/v1/resource/42/')
    request.user = user
    fake_view = FakeView()
    fake_view.request = request
    context = {}
    context['view'] = fake_view
    context['request'] = request
    return context

# Test protection against limited set of validation problems

@pytest.mark.django_db
def test_bad_data_copy_edit(admin_user, project):
    """
    If a required resource (inventory here) was deleted, copying not allowed
    because doing so would caues a validation error
    """

    jt_res = JobTemplate.objects.create(
        job_type='run',
        project=project,
        inventory=None,  ask_inventory_on_launch=False, # not allowed
        credential=None, ask_credential_on_launch=True,
        name='deploy-job-template'
    )
    serializer = JobTemplateSerializer(jt_res)
    serializer.context = fake_context(admin_user)
    response = serializer.to_representation(jt_res)
    assert not response['summary_fields']['user_capabilities']['copy']
    assert response['summary_fields']['user_capabilities']['edit']

# Tests for correspondence between view info and intended access

@pytest.mark.django_db
def test_sys_admin_copy_edit(jt_copy_edit, admin_user):
    "Absent a validation error, system admins can do everything"
    serializer = JobTemplateSerializer(jt_copy_edit)
    serializer.context = fake_context(admin_user)
    response = serializer.to_representation(jt_copy_edit)
    assert response['summary_fields']['user_capabilities']['copy']
    assert response['summary_fields']['user_capabilities']['edit']

@pytest.mark.django_db
def test_org_admin_copy_edit(jt_copy_edit, org_admin):
    "Organization admins SHOULD be able to copy a JT firmly in their org"
    serializer = JobTemplateSerializer(jt_copy_edit)
    serializer.context = fake_context(org_admin)
    response = serializer.to_representation(jt_copy_edit)
    assert response['summary_fields']['user_capabilities']['copy']
    assert response['summary_fields']['user_capabilities']['edit']

@pytest.mark.django_db
def test_org_admin_foreign_cred_no_copy_edit(jt_copy_edit, org_admin, machine_credential):
    """
    Organization admins without access to the 3 related resources:
    SHOULD NOT be able to copy JT
    SHOULD be able to edit that job template, for nonsensitive changes
    """

    # Attach credential to JT that org admin can not use
    jt_copy_edit.credential = machine_credential
    jt_copy_edit.save()

    serializer = JobTemplateSerializer(jt_copy_edit)
    serializer.context = fake_context(org_admin)
    response = serializer.to_representation(jt_copy_edit)
    assert not response['summary_fields']['user_capabilities']['copy']
    assert response['summary_fields']['user_capabilities']['edit']

@pytest.mark.django_db
def test_jt_admin_copy_edit(jt_copy_edit, rando):
    """
    JT admins wihout access to associated resources SHOULD NOT be able to copy
    SHOULD be able to make nonsensitive changes"""

    # random user given JT admin access only
    jt_copy_edit.admin_role.members.add(rando)
    jt_copy_edit.save()

    serializer = JobTemplateSerializer(jt_copy_edit)
    serializer.context = fake_context(rando)
    response = serializer.to_representation(jt_copy_edit)
    assert not response['summary_fields']['user_capabilities']['copy']
    assert response['summary_fields']['user_capabilities']['edit']

@pytest.mark.django_db
def test_proj_jt_admin_copy_edit(jt_copy_edit, rando):
    "JT admins with access to associated resources SHOULD be able to copy"

    # random user given JT and project admin abilities
    jt_copy_edit.admin_role.members.add(rando)
    jt_copy_edit.save()
    jt_copy_edit.project.admin_role.members.add(rando)
    jt_copy_edit.project.save()

    serializer = JobTemplateSerializer(jt_copy_edit)
    serializer.context = fake_context(rando)
    response = serializer.to_representation(jt_copy_edit)
    assert response['summary_fields']['user_capabilities']['copy']
    assert response['summary_fields']['user_capabilities']['edit']


@pytest.mark.django_db
class TestAccessListCapabilities:
    @pytest.fixture
    def mock_access_method(self, mocker):
        "Mocking this requires extra work because of the logging statement"
        mock_method = mocker.MagicMock()
        mock_method.return_value = 'foobar'
        mock_method.__name__ = 'bars'
        return mock_method

    def _assert_one_in_list(self, data, sublist='direct_access'):
        assert len(data['results']) == 1
        assert len(data['results'][0]['summary_fields'][sublist]) == 1
    
    def test_access_list_direct_access_capability(self, inventory, rando, get, mocker, mock_access_method):
        """Test that the access_list serializer shows the exact output of the
        RoleAccess.can_attach method in the direct_access list"""
        inventory.admin_role.members.add(rando)
        with mocker.patch.object(access_registry[Role][0], 'can_unattach', mock_access_method):
            response = get(reverse('api:inventory_access_list', args=(inventory.id,)), rando)
        self._assert_one_in_list(response.data)
        direct_access_list = response.data['results'][0]['summary_fields']['direct_access']
        assert direct_access_list[0]['role']['user_capabilities']['unattach'] == 'foobar'

    def test_access_list_indirect_access_capability(self, inventory, admin_user, get, mocker, mock_access_method):
        """Test the display of unattach access for a singleton permission"""
        with mocker.patch.object(access_registry[Role][0], 'can_unattach', mock_access_method):
            response = get(reverse('api:inventory_access_list', args=(inventory.id,)), admin_user)
        self._assert_one_in_list(response.data, sublist='indirect_access')
        indirect_access_list = response.data['results'][0]['summary_fields']['indirect_access']
        assert indirect_access_list[0]['role']['user_capabilities']['unattach'] == 'foobar'

    def test_access_list_team_direct_access_capability(self, inventory, team, team_member, get, mocker, mock_access_method):
        """Test the display of unattach access for team-based permissions
        this happens in a difference place in the serializer code from the user permission"""
        team.member_role.children.add(inventory.admin_role)
        with mocker.patch.object(access_registry[Role][0], 'can_unattach', mock_access_method):
            response = get(reverse('api:inventory_access_list', args=(inventory.id,)), team_member)
        self._assert_one_in_list(response.data)
        direct_access_list = response.data['results'][0]['summary_fields']['direct_access']
        assert direct_access_list[0]['role']['user_capabilities']['unattach'] == 'foobar'


@pytest.mark.django_db
def test_team_roles_unattach(mocker):
    pass

@pytest.mark.django_db
def test_user_roles_unattach(mocker):
    pass

