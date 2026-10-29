from unittest import mock
import pytest

from awx.main.access import (
    BaseAccess,
    OrganizationAccess,
)
from awx.main.models.credential import Credential, CredentialType


@mock.patch.object(BaseAccess, 'check_license', return_value=None)
@pytest.mark.django_db
def test_organization_access_admin(cl, organization, user):
    '''can_change because I am an admin of that org'''
    a = user('admin', False)
    organization.admin_role.members.add(a)
    organization.member_role.members.add(user('user', False))

    access = OrganizationAccess(a)
    assert access.can_change(organization, None)
    assert access.can_delete(organization)

    org = access.get_queryset()[0]
    assert len(org.admin_role.members.all()) == 1
    assert len(org.member_role.members.all()) == 1


@mock.patch.object(BaseAccess, 'check_license', return_value=None)
@pytest.mark.django_db
def test_organization_access_user(cl, organization, user):
    access = OrganizationAccess(user('user', False))
    organization.member_role.members.add(user('user', False))

    assert not access.can_change(organization, None)
    assert not access.can_delete(organization)

    org = access.get_queryset()[0]
    assert len(org.admin_role.members.all()) == 0
    assert len(org.member_role.members.all()) == 1


@pytest.mark.django_db
@pytest.mark.parametrize('ext_auth', [True, False])
def test_org_resource_role(ext_auth, organization, rando, org_admin):
    with mock.patch('awx.main.access.settings') as settings_mock:
        settings_mock.MANAGE_ORGANIZATION_AUTH = ext_auth
        access = OrganizationAccess(org_admin)

        assert access.can_attach(organization, rando, 'member_role.members') == ext_auth
        organization.member_role.members.add(rando)
        assert access.can_unattach(organization, rando, 'member_role.members') == ext_auth


@pytest.mark.django_db
def test_delete_org_while_workflow_active(workflow_job_template):
    '''
    Delete org while workflow job is active (i.e. changing status)
    '''
    assert workflow_job_template.organization  # sanity check
    wj = workflow_job_template.create_unified_job()  # status should be new
    workflow_job_template.organization.delete()
    wj.refresh_from_db()
    assert wj.status != 'pending'  # sanity check
    wj.status = 'pending'  # status needs to change in order to trigger workflow_job_template.save()
    wj.save(update_fields=['status'])


@pytest.mark.django_db
@pytest.mark.parametrize(
    "obj_perm,subobj_perm,allowed",
    [
        ('admin_role', 'use_role', True),
        ('admin_role', 'read_role', False),
        ('admin_role', 'admin_role', True),
    ],
)
def test_galaxy_credential_role_based_associability(rando, organization, obj_perm, subobj_perm, allowed):
    """Org admin must hold use_role on a galaxy credential to attach it.

    Regression: without the galaxy_credentials branch in
    OrganizationAccess.can_attach the request falls through to
    BaseAccess.can_attach which only requires read access, allowing an
    org admin with mere read_role on a foreign credential to bind it.
    """
    galaxy_ct = CredentialType.defaults['galaxy_api_token']()
    galaxy_ct.save()
    cred = Credential.objects.create(
        credential_type=galaxy_ct,
        name='test-galaxy-cred',
        inputs={'url': 'https://galaxy.example.com/'},
    )

    getattr(organization, obj_perm).members.add(rando)
    getattr(cred, subobj_perm).members.add(rando)

    assert allowed == OrganizationAccess(rando).can_attach(organization, cred, 'galaxy_credentials', None)
