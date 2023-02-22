import pytest
from unittest import mock

from django.apps import apps
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from awx.main.models.rbac import Role
from awx.main.models import Organization, InstanceGroup
from awx.main.migrations import _OrgAdmin_to_use_ig as orgadmin

@pytest.mark.django_db
def test_migrate_admin_role(org_admin, organization):
    instance_group = InstanceGroup.objects.create(name='test')
    organization.admin_role.members.add(org_admin)
    organization.instance_groups.add(instance_group)
    with mock.patch('django.conf.settings.CONSTRUCTED_INSTANCE_ID_VAR'):
        orgadmin.migrate_org_admin_to_use(apps)
    assert org_admin in instance_group.use_role.members.all()
