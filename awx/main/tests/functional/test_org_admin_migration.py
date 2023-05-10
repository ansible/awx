import pytest

from django.apps import apps

from awx.main.models import InstanceGroup
from awx.main.migrations import _OrgAdmin_to_use_ig as orgadmin


@pytest.mark.django_db
def test_migrate_admin_role(org_admin, organization):
    instance_group = InstanceGroup.objects.create(name='test')
    organization.admin_role.members.add(org_admin)
    organization.instance_groups.add(instance_group)
    orgadmin.migrate_org_admin_to_use(apps, None)
    assert org_admin in instance_group.use_role.members.all()
    assert instance_group.use_role.members.count() == 1
