import pytest

from awx.main.access import CredentialAccess
from awx.main.models.credential import Credential
from awx.main.models.jobs import JobTemplate
from awx.main.migrations import _rbac as rbac
from django.apps import apps
from django.contrib.auth.models import User

@pytest.mark.django_db
def test_credential_migration_user(credential, user, permissions):
    u = user('user', False)
    credential.user = u
    credential.save()

    migrated = rbac.migrate_credential(apps, None)

    assert len(migrated) == 1
    assert credential.accessible_by(u, permissions['admin'])

@pytest.mark.django_db
def test_credential_usage_role(credential, user, permissions):
    u = user('user', False)
    credential.usage_role.members.add(u)
    assert credential.accessible_by(u, permissions['usage'])

@pytest.mark.django_db
def test_credential_migration_team_member(credential, team, user, permissions):
    u = user('user', False)
    team.admin_role.members.add(u)
    credential.team = team
    credential.save()


    # No permissions pre-migration (this happens automatically so we patch this)
    team.admin_role.children.remove(credential.owner_role)
    team.member_role.children.remove(credential.usage_role)
    assert not credential.accessible_by(u, permissions['admin'])

    migrated = rbac.migrate_credential(apps, None)

    # Admin permissions post migration
    assert len(migrated) == 1
    assert credential.accessible_by(u, permissions['admin'])

@pytest.mark.django_db
def test_credential_migration_team_admin(credential, team, user, permissions):
    u = user('user', False)
    team.member_role.members.add(u)
    credential.team = team
    credential.save()

    # No permissions pre-migration
    team.admin_role.children.remove(credential.owner_role)
    team.member_role.children.remove(credential.usage_role)
    assert not credential.accessible_by(u, permissions['usage'])

    # Usage permissions post migration
    migrated = rbac.migrate_credential(apps, None)
    assert len(migrated) == 1
    assert credential.accessible_by(u, permissions['usage'])

def test_credential_access_superuser():
    u = User(username='admin', is_superuser=True)
    access = CredentialAccess(u)
    credential = Credential()

    assert access.can_add(None)
    assert access.can_change(credential, None)
    assert access.can_delete(credential)

@pytest.mark.django_db
def test_credential_access_admin(user, team, credential):
    u = user('org-admin', False)
    team.organization.admin_role.members.add(u)

    access = CredentialAccess(u)

    assert access.can_add({'user': u.pk})
    assert access.can_add({'team': team.pk})

    assert not access.can_change(credential, {'user': u.pk})

    # unowned credential can be deleted
    assert access.can_delete(credential)

    # credential is now part of a team
    # that is part of an organization
    # that I am an admin for
    credential.team = team
    credential.save()
    credential.owner_role.rebuild_role_ancestor_list()

    cred = Credential.objects.create(kind='aws', name='test-cred')
    cred.team = team
    cred.save()

    # should have can_change access as org-admin
    assert access.can_change(credential, {'user': u.pk})

@pytest.mark.django_db
def test_cred_job_template(user, deploy_jobtemplate):
    a = user('admin', False)
    org = deploy_jobtemplate.project.organization
    org.admin_role.members.add(a)

    cred = deploy_jobtemplate.credential
    cred.user = user('john', False)
    cred.save()

    access = CredentialAccess(a)
    rbac.migrate_credential(apps, None)
    assert access.can_change(cred, {'organization': org.pk})

    org.admin_role.members.remove(a)
    assert not access.can_change(cred, {'organization': org.pk})

@pytest.mark.django_db
def test_cred_multi_job_template_single_org(user, deploy_jobtemplate):
    a = user('admin', False)
    org = deploy_jobtemplate.project.organization
    org.admin_role.members.add(a)

    cred = deploy_jobtemplate.credential
    cred.user = user('john', False)
    cred.save()

    access = CredentialAccess(a)
    rbac.migrate_credential(apps, None)
    assert access.can_change(cred, {'organization': org.pk})

    org.admin_role.members.remove(a)
    assert not access.can_change(cred, {'organization': org.pk})

@pytest.mark.django_db
def test_single_cred_multi_job_template_multi_org(user, organizations, credential):
    orgs = organizations(2)
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

    assert jts[0].credential != jts[1].credential
    assert access.can_change(jts[0].credential, {'organization': org.pk})
    assert access.can_change(jts[1].credential, {'organization': org.pk})

    orgs[0].admin_role.members.remove(a)
    assert not access.can_change(jts[0].credential, {'organization': org.pk})

@pytest.mark.django_db
def test_cred_single_org():
    pass

@pytest.mark.django_db
def test_cred_created_by_multi_org():
    pass

@pytest.mark.django_db
def test_cred_no_org():
    pass

@pytest.mark.django_db
def test_cred_team():
    pass
