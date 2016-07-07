import pytest

from awx.main.access import CredentialAccess
from awx.main.models.credential import Credential
from awx.main.models.jobs import JobTemplate
from awx.main.models.inventory import InventorySource
from awx.main.migrations import _rbac as rbac
from django.apps import apps
from django.contrib.auth.models import User

@pytest.mark.django_db
def test_credential_migration_user(credential, user, permissions):
    u = user('user', False)
    credential.deprecated_user = u
    credential.save()

    rbac.migrate_credential(apps, None)

    assert u in credential.admin_role

@pytest.mark.django_db
def test_two_teams_same_cred_name(organization_factory):
    objects = organization_factory("test",
                                   teams=["team1", "team2"])

    cred1 = Credential.objects.create(name="test", kind="net", deprecated_team=objects.teams.team1)
    cred2 = Credential.objects.create(name="test", kind="net", deprecated_team=objects.teams.team2)

    rbac.migrate_credential(apps, None)

    assert objects.teams.team1.member_role in cred1.admin_role.parents.all()
    assert objects.teams.team2.member_role in cred2.admin_role.parents.all()

@pytest.mark.django_db
def test_credential_use_role(credential, user, permissions):
    u = user('user', False)
    credential.use_role.members.add(u)
    assert u in credential.use_role

@pytest.mark.django_db
def test_credential_migration_team_member(credential, team, user, permissions):
    u = user('user', False)
    team.member_role.members.add(u)
    credential.deprecated_team = team
    credential.save()


    # No permissions pre-migration (this happens automatically so we patch this)
    team.admin_role.children.remove(credential.admin_role)
    team.member_role.children.remove(credential.use_role)
    assert u not in credential.admin_role

    rbac.migrate_credential(apps, None)

    # Admin permissions post migration
    assert u in credential.admin_role

@pytest.mark.django_db
def test_credential_migration_team_admin(credential, team, user, permissions):
    u = user('user', False)
    team.member_role.members.add(u)
    credential.deprecated_team = team
    credential.save()

    assert u not in credential.use_role

    # Usage permissions post migration
    rbac.migrate_credential(apps, None)
    assert u in credential.use_role

def test_credential_access_superuser():
    u = User(username='admin', is_superuser=True)
    access = CredentialAccess(u)
    credential = Credential()

    assert access.can_add(None)
    assert access.can_change(credential, None)
    assert access.can_delete(credential)

@pytest.mark.django_db
def test_credential_access_auditor(credential, organization_factory):
    objects = organization_factory("org_cred_auditor",
                                   users=["user1"],
                                   roles=['org_cred_auditor.auditor_role:user1'])
    credential.organization = objects.organization
    credential.save()

    access = CredentialAccess(objects.users.user1)
    assert access.can_read(credential)

@pytest.mark.django_db
def test_credential_access_admin(user, team, credential):
    u = user('org-admin', False)
    team.organization.admin_role.members.add(u)

    access = CredentialAccess(u)

    assert access.can_add({'user': u.pk})
    assert not access.can_change(credential, {'user': u.pk})

    # unowned credential is superuser only
    assert not access.can_delete(credential)

    # credential is now part of a team
    # that is part of an organization
    # that I am an admin for
    credential.admin_role.parents.add(team.admin_role)
    credential.save()

    cred = Credential.objects.create(kind='aws', name='test-cred')
    cred.deprecated_team = team
    cred.save()

    # should have can_change access as org-admin
    assert access.can_change(credential, {'description': 'New description.'})

@pytest.mark.django_db
def test_org_credential_access_member(alice, org_credential, credential):
    org_credential.admin_role.members.add(alice)
    credential.admin_role.members.add(alice)

    access = CredentialAccess(alice)

    # Alice should be able to PATCH if organization is not changed
    assert access.can_change(org_credential, {
        'description': 'New description.',
        'organization': org_credential.organization.pk})
    assert access.can_change(org_credential, {
        'description': 'New description.'})
    assert access.can_change(credential, {
        'description': 'New description.',
        'organization': None})

@pytest.mark.django_db
def test_credential_access_org_permissions(
        org_admin, org_member, organization, org_credential, credential):
    credential.admin_role.members.add(org_admin)
    credential.admin_role.members.add(org_member)
    org_credential.admin_role.members.add(org_member)

    access = CredentialAccess(org_admin)
    member_access = CredentialAccess(org_member)

    # Org admin can move their own credential into their org
    assert access.can_change(credential, {'organization': organization.pk})
    # Org member can not
    assert not member_access.can_change(credential, {
        'organization': organization.pk})

    # Org admin can remove a credential from their org
    assert access.can_change(org_credential, {'organization': None})
    # Org member can not
    assert not member_access.can_change(org_credential, {'organization': None})
    assert not member_access.can_change(org_credential, {
        'user': org_member.pk, 'organization': None})

@pytest.mark.django_db
def test_cred_job_template_xfail(user, deploy_jobtemplate):
    ' Personal credential migration '
    a = user('admin', False)
    org = deploy_jobtemplate.project.organization
    org.admin_role.members.add(a)

    cred = deploy_jobtemplate.credential
    cred.deprecated_user = user('john', False)
    cred.save()

    access = CredentialAccess(a)
    rbac.migrate_credential(apps, None)
    assert not access.can_change(cred, {'organization': org.pk})

@pytest.mark.django_db
def test_cred_job_template(user, team, deploy_jobtemplate):
    ' Team credential migration => org credential '
    a = user('admin', False)
    org = deploy_jobtemplate.project.organization
    org.admin_role.members.add(a)

    cred = deploy_jobtemplate.credential
    cred.deprecated_team = team
    cred.save()

    access = CredentialAccess(a)
    rbac.migrate_credential(apps, None)

    cred.refresh_from_db()

    assert access.can_change(cred, {'organization': org.pk})

    org.admin_role.members.remove(a)
    assert not access.can_change(cred, {'organization': org.pk})

@pytest.mark.django_db
def test_cred_multi_job_template_single_org_xfail(user, deploy_jobtemplate):
    a = user('admin', False)
    org = deploy_jobtemplate.project.organization
    org.admin_role.members.add(a)

    cred = deploy_jobtemplate.credential
    cred.deprecated_user = user('john', False)
    cred.save()

    access = CredentialAccess(a)
    rbac.migrate_credential(apps, None)
    cred.refresh_from_db()

    assert not access.can_change(cred, {'organization': org.pk})

@pytest.mark.django_db
def test_cred_multi_job_template_single_org(user, team, deploy_jobtemplate):
    a = user('admin', False)
    org = deploy_jobtemplate.project.organization
    org.admin_role.members.add(a)

    cred = deploy_jobtemplate.credential
    cred.deprecated_team = team
    cred.save()

    access = CredentialAccess(a)
    rbac.migrate_credential(apps, None)
    cred.refresh_from_db()

    assert access.can_change(cred, {'organization': org.pk})

    org.admin_role.members.remove(a)
    assert not access.can_change(cred, {'organization': org.pk})

@pytest.mark.django_db
def test_single_cred_multi_job_template_multi_org(user, organizations, credential, team):
    orgs = organizations(2)
    credential.deprecated_team = team
    credential.save()

    jts = []
    for org in orgs:
        inv = org.inventories.create(name="inv-%d" % org.pk)
        jt = JobTemplate.objects.create(
            inventory=inv,
            credential=credential,
            name="test-jt-org-%d" % org.pk,
            job_type='check',
        )
        jts.append(jt)

    a = user('admin', False)
    orgs[0].admin_role.members.add(a)
    orgs[1].admin_role.members.add(a)

    access = CredentialAccess(a)
    rbac.migrate_credential(apps, None)

    for jt in jts:
        jt.refresh_from_db()
    credential.refresh_from_db()

    assert jts[0].credential != jts[1].credential
    assert access.can_change(jts[0].credential, {'organization': org.pk})
    assert access.can_change(jts[1].credential, {'organization': org.pk})

    orgs[0].admin_role.members.remove(a)
    assert not access.can_change(jts[0].credential, {'organization': org.pk})

@pytest.mark.django_db
def test_cred_inventory_source(user, inventory, credential):
    u = user('member', False)
    inventory.organization.member_role.members.add(u)

    InventorySource.objects.create(
        name="test-inv-src",
        credential=credential,
        inventory=inventory,
    )

    assert u not in credential.use_role

    rbac.migrate_credential(apps, None)
    assert u not in credential.use_role

@pytest.mark.django_db
def test_cred_project(user, credential, project):
    u = user('member', False)
    project.organization.member_role.members.add(u)
    project.credential = credential
    project.save()

    assert u not in credential.use_role

    rbac.migrate_credential(apps, None)
    assert u not in credential.use_role

@pytest.mark.django_db
def test_cred_no_org(user, credential):
    su = user('su', True)
    access = CredentialAccess(su)
    assert access.can_change(credential, {'user': su.pk})

@pytest.mark.django_db
def test_cred_team(user, team, credential):
    u = user('a', False)
    team.member_role.members.add(u)
    credential.deprecated_team = team
    credential.save()

    assert u not in credential.use_role

    rbac.migrate_credential(apps, None)
    assert u in credential.use_role
