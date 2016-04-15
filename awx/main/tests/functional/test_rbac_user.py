import pytest

from django.apps import apps
from django.contrib.auth.models import User

from awx.main.migrations import _rbac as rbac
from awx.main.access import UserAccess
from awx.main.models import Role

@pytest.mark.django_db
def test_user_admin(user_project, project, user):
    username = unicode("\xc3\xb4", "utf-8")

    joe = user(username, is_superuser = False)
    admin = user('admin', is_superuser = True)
    sa = Role.singleton('System Administrator')

    # this should happen automatically with our signal
    assert sa.members.filter(id=admin.id).exists() is True
    sa.members.remove(admin)

    assert sa.members.filter(id=joe.id).exists() is False
    assert sa.members.filter(id=admin.id).exists() is False

    rbac.migrate_users(apps, None)

    # The migration should add the admin back in
    assert sa.members.filter(id=joe.id).exists() is False
    assert sa.members.filter(id=admin.id).exists() is True

@pytest.mark.django_db
def test_user_queryset(user):
    u = user('pete', False)

    access = UserAccess(u)
    qs = access.get_queryset()
    assert qs.count() == 1

@pytest.mark.django_db
def test_user_accessible_objects(user, organization):
    admin = user('admin', False)
    u = user('john', False)
    assert User.accessible_objects(admin, {'read':True}).count() == 1

    organization.member_role.members.add(u)
    organization.admin_role.members.add(admin)
    assert User.accessible_objects(admin, {'read':True}).count() == 2

    organization.member_role.members.remove(u)
    assert User.accessible_objects(admin, {'read':True}).count() == 1

@pytest.mark.django_db
def test_org_user_admin(user, organization):
    admin = user('orgadmin')
    member = user('orgmember')

    organization.member_role.members.add(member)
    assert admin not in member.admin_role

    organization.admin_role.members.add(admin)
    assert admin in member.admin_role

    organization.admin_role.members.remove(admin)
    assert admin not in member.admin_role

@pytest.mark.django_db
def test_org_user_removed(user, organization):
    admin = user('orgadmin')
    member = user('orgmember')

    organization.admin_role.members.add(admin)
    organization.member_role.members.add(member)

    assert admin in member.admin_role

    organization.member_role.members.remove(member)
    assert admin not in member.admin_role
