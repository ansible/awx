import pytest

# AWX models
from awx.main.models import ActivityStream, Organization, JobTemplate



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

