import pytest

from awx.main.access import InstanceGroupAccess, NotificationTemplateAccess, ProjectAccess
from awx.main.models.credential import Credential, CredentialType

from ansible_base.rbac.models import RoleDefinition


@pytest.mark.django_db
def test_instance_group_object_role_delete(rando, instance_group, setup_managed_roles):
    """Basic functionality of IG object-level admin role function AAP-25506"""
    rd = RoleDefinition.objects.get(name='InstanceGroup Admin')
    rd.give_permission(rando, instance_group)
    access = InstanceGroupAccess(rando)
    assert access.can_delete(instance_group)


@pytest.mark.django_db
def test_notification_template_object_role_change(rando, notification_template, setup_managed_roles):
    """Basic functionality of NT object-level admin role function AAP-25493"""
    rd = RoleDefinition.objects.get(name='NotificationTemplate Admin')
    rd.give_permission(rando, notification_template)
    access = NotificationTemplateAccess(rando)
    assert access.can_change(notification_template, {'name': 'new name'})


@pytest.mark.django_db
def test_organization_auditor_role(rando, setup_managed_roles, organization, inventory, project, jt_linked):
    obj_list = (inventory, project, jt_linked)
    for obj in obj_list:
        assert obj.organization == organization, obj  # sanity

    assert [rando.has_obj_perm(obj, 'view') for obj in obj_list] == [False for i in range(3)], obj_list

    rd = RoleDefinition.objects.get(name='Organization Audit')
    rd.give_permission(rando, organization)

    codename_set = set(rd.permissions.values_list('codename', flat=True))
    assert not ({'view_inventory', 'view_jobtemplate', 'audit_organization'} - codename_set)  # sanity

    assert [obj in type(obj).access_qs(rando) for obj in obj_list] == [True for i in range(3)], obj_list
    assert [rando.has_obj_perm(obj, 'view') for obj in obj_list] == [True for i in range(3)], obj_list


@pytest.mark.django_db
def test_project_can_add_signature_validation_credential_rbac(organization, user):
    """Regression: can_add must enforce use_role on signature_validation_credential.

    Before the fix, a project admin could bind any credential as
    signature_validation_credential on project create without use_role.
    After the fix, can_add returns False unless the user holds use_role
    on the signature_validation_credential.
    """
    project_admin = user('proj-admin', False)
    organization.project_admin_role.members.add(project_admin)

    ct = CredentialType.defaults['gpg_public_key']()
    ct.save()
    sig_cred = Credential.objects.create(
        credential_type=ct,
        name='sig-val-cred',
        inputs={'gpg_public_key': 'FAKE-KEY'},
    )

    access = ProjectAccess(project_admin)

    # Without use_role on the credential, can_add must reject
    assert not access.can_add(
        {
            'organization': organization.id,
            'signature_validation_credential': sig_cred.id,
        }
    )

    # With use_role on the credential, can_add must permit
    sig_cred.use_role.members.add(project_admin)
    assert access.can_add(
        {
            'organization': organization.id,
            'signature_validation_credential': sig_cred.id,
        }
    )


@pytest.mark.django_db
def test_project_can_change_signature_validation_credential_rbac(organization, project, user):
    """Regression: can_change must enforce use_role on signature_validation_credential.

    Before the fix, a project admin could set any credential as
    signature_validation_credential via PATCH without use_role.
    After the fix, can_change returns False unless the user holds use_role
    on the signature_validation_credential.
    """
    project_admin = user('proj-admin', False)
    organization.project_admin_role.members.add(project_admin)

    ct = CredentialType.defaults['gpg_public_key']()
    ct.save()
    sig_cred = Credential.objects.create(
        credential_type=ct,
        name='sig-val-cred',
        inputs={'gpg_public_key': 'FAKE-KEY'},
    )

    access = ProjectAccess(project_admin)

    # Without use_role on the credential, can_change must reject
    assert not access.can_change(
        project,
        {
            'signature_validation_credential': sig_cred.id,
        },
    )

    # With use_role on the credential, can_change must permit
    sig_cred.use_role.members.add(project_admin)
    assert access.can_change(
        project,
        {
            'signature_validation_credential': sig_cred.id,
        },
    )
