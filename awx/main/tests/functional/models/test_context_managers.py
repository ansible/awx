import pytest

# AWX context managers for testing
from awx.main.models.rbac import batch_role_ancestor_rebuilding
from awx.main.signals import (
    disable_activity_stream,
    disable_computed_fields,
    update_inventory_computed_fields
)

# AWX models
from awx.main.models.organization import Organization
from awx.main.models import ActivityStream, Job
from awx.main.tests.functional import immediate_on_commit


@pytest.mark.django_db
def test_rbac_batch_rebuilding(rando, organization):
    with batch_role_ancestor_rebuilding():
        organization.admin_role.members.add(rando)
        inventory = organization.inventories.create(name='test-inventory')
        assert rando not in inventory.admin_role
    assert rando in inventory.admin_role


@pytest.mark.django_db
def test_disable_activity_stream():
    with disable_activity_stream():
        Organization.objects.create(name='test-organization')
    assert ActivityStream.objects.filter(organization__isnull=False).count() == 0


@pytest.mark.django_db
class TestComputedFields:

    def test_computed_fields_normal_use(self, mocker, inventory):
        job = Job.objects.create(name='fake-job', inventory=inventory)
        with immediate_on_commit():
            with mocker.patch.object(update_inventory_computed_fields, 'delay'):
                job.delete()
                update_inventory_computed_fields.delay.assert_called_once_with(inventory.id)

    def test_disable_computed_fields(self, mocker, inventory):
        job = Job.objects.create(name='fake-job', inventory=inventory)
        with disable_computed_fields():
            with mocker.patch.object(update_inventory_computed_fields, 'delay'):
                job.delete()
                update_inventory_computed_fields.delay.assert_not_called()

