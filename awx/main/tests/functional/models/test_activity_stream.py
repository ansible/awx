import pytest
import mock

import json

# AWX models
from awx.main.models import (
    ActivityStream,
    Organization,
    JobTemplate,
    Credential,
    CredentialType,
    Inventory,
    InventorySource
)

# other AWX
from awx.main.utils import model_to_dict
from awx.api.serializers import InventorySourceSerializer

# Django
from django.contrib.auth.models import AnonymousUser

# Django-CRUM
from crum import impersonate


model_serializer_mapping = {
    InventorySource: InventorySourceSerializer
}


class TestImplicitRolesOmitted:
    '''
    Test that there is exactly 1 "create" entry in the activity stream for
    common items in the system.
    These tests will fail if `rbac_activity_stream` creates
    false-positive entries.
    '''

    @pytest.mark.django_db
    def test_activity_stream_create_organization(self):
        Organization.objects.create(name='test-organization2')
        qs = ActivityStream.objects.filter(organization__isnull=False)
        assert qs.count() == 1
        assert qs[0].operation == 'create'

    @pytest.mark.django_db
    def test_activity_stream_delete_organization(self):
        org = Organization.objects.create(name='gYSlNSOFEW')
        org.delete()
        qs = ActivityStream.objects.filter(changes__icontains='gYSlNSOFEW')
        assert qs.count() == 2
        assert qs[1].operation == 'delete'

    @pytest.mark.django_db
    def test_activity_stream_create_JT(self, project, inventory, credential):
        JobTemplate.objects.create(
            name='test-jt',
            project=project,
            inventory=inventory,
            credential=credential
        )
        qs = ActivityStream.objects.filter(job_template__isnull=False)
        assert qs.count() == 1
        assert qs[0].operation == 'create'

    @pytest.mark.django_db
    def test_activity_stream_create_inventory(self, organization):
        organization.inventories.create(name='test-inv')
        qs = ActivityStream.objects.filter(inventory__isnull=False)
        assert qs.count() == 1
        assert qs[0].operation == 'create'

    @pytest.mark.django_db
    def test_activity_stream_create_credential(self, organization):
        organization.inventories.create(name='test-inv')
        qs = ActivityStream.objects.filter(inventory__isnull=False)
        assert qs.count() == 1
        assert qs[0].operation == 'create'


class TestRolesAssociationEntries:
    '''
    Test that non-implicit role associations have a corresponding
    activity stream entry.
    These tests will fail if `rbac_activity_stream` skipping logic
    finds a false-negative.
    '''

    @pytest.mark.django_db
    def test_non_implicit_associations_are_recorded(self, project):
        org2 = Organization.objects.create(name='test-organization2')
        project.admin_role.parents.add(org2.admin_role)
        assert ActivityStream.objects.filter(
            role=org2.admin_role,
            organization=org2,
            project=project
        ).count() == 1

    @pytest.mark.django_db
    def test_model_associations_are_recorded(self, organization):
        proj1 = organization.projects.create(name='proj1')
        proj2 = organization.projects.create(name='proj2')
        proj2.use_role.parents.add(proj1.admin_role)
        assert ActivityStream.objects.filter(role=proj1.admin_role, project=proj2).count() == 1



@pytest.fixture
def somecloud_type():
    return CredentialType.objects.create(
        kind='cloud',
        name='SomeCloud',
        managed_by_tower=False,
        inputs={
            'fields': [{
                'id': 'api_token',
                'label': 'API Token',
                'type': 'string',
                'secret': True
            }]
        },
        injectors={
            'env': {
                'MY_CLOUD_API_TOKEN': '{{api_token.foo()}}'
            }
        }
    )


@pytest.mark.django_db
class TestCredentialModels:
    '''
    Assure that core elements of activity stream feature are working
    '''

    def test_create_credential_type(self, somecloud_type):
        assert ActivityStream.objects.filter(credential_type=somecloud_type).count() == 1
        entry = ActivityStream.objects.filter(credential_type=somecloud_type)[0]
        assert entry.operation == 'create'

    def test_credential_hidden_information(self, somecloud_type):
        cred = Credential.objects.create(
            credential_type=somecloud_type,
            inputs = {'api_token': 'ABC123'}
        )
        entry = ActivityStream.objects.filter(credential=cred)[0]
        assert entry.operation == 'create'
        assert json.loads(entry.changes)['inputs'] == 'hidden'


@pytest.mark.django_db
class TestUserModels:

    def test_user_hidden_information(self, alice):
        entry = ActivityStream.objects.filter(user=alice)[0]
        assert entry.operation == 'create'
        assert json.loads(entry.changes)['password'] == 'hidden'


@pytest.mark.django_db
def test_missing_related_on_delete(inventory_source):
    old_is = InventorySource.objects.get(name=inventory_source.name)
    inventory_source.inventory.delete()
    d = model_to_dict(old_is, serializer_mapping=model_serializer_mapping)
    assert d['inventory'] == '<missing inventory source>-{}'.format(old_is.inventory_id)


@pytest.mark.django_db
def test_activity_stream_actor(admin_user):
    with impersonate(admin_user):
        o = Organization.objects.create(name='test organization')
    entry = o.activitystream_set.get(operation='create')
    assert entry.actor == admin_user


@pytest.mark.django_db
def test_annon_user_action():
    with mock.patch('awx.main.signals.get_current_user') as u_mock:
        u_mock.return_value = AnonymousUser()
        inv = Inventory.objects.create(name='ainventory')
    entry = inv.activitystream_set.filter(operation='create').first()
    assert not entry.actor
