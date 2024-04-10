import pytest
from django.apps import apps
from django.test.utils import override_settings

from awx.main.migrations._dab_rbac import setup_managed_role_definitions

from ansible_base.rbac.models import RoleDefinition

INVENTORY_OBJ_PERMISSIONS = ['view_inventory', 'adhoc_inventory', 'use_inventory', 'change_inventory', 'delete_inventory', 'update_inventory']


@pytest.mark.django_db
def test_managed_definitions_precreate():
    with override_settings(
        ANSIBLE_BASE_ROLE_PRECREATE={
            'object_admin': '{cls._meta.model_name}-admin',
            'org_admin': 'organization-admin',
            'org_children': 'organization-{cls._meta.model_name}-admin',
            'special': '{cls._meta.model_name}-{action}',
        }
    ):
        setup_managed_role_definitions(apps, None)
    rd = RoleDefinition.objects.get(name='inventory-admin')
    assert rd.managed is True
    # add permissions do not go in the object-level admin
    assert set(rd.permissions.values_list('codename', flat=True)) == set(INVENTORY_OBJ_PERMISSIONS)

    # test org-level object admin permissions
    rd = RoleDefinition.objects.get(name='organization-inventory-admin')
    assert rd.managed is True
    assert set(rd.permissions.values_list('codename', flat=True)) == set(['add_inventory', 'view_organization'] + INVENTORY_OBJ_PERMISSIONS)


@pytest.mark.django_db
def test_managed_definitions_custom_obj_admin_name():
    with override_settings(
        ANSIBLE_BASE_ROLE_PRECREATE={
            'object_admin': 'foo-{cls._meta.model_name}-foo',
        }
    ):
        setup_managed_role_definitions(apps, None)
    rd = RoleDefinition.objects.get(name='foo-inventory-foo')
    assert rd.managed is True
    # add permissions do not go in the object-level admin
    assert set(rd.permissions.values_list('codename', flat=True)) == set(INVENTORY_OBJ_PERMISSIONS)
