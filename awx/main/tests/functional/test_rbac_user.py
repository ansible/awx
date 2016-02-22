import pytest

from awx.main.migrations import _rbac as rbac
from awx.main.models import Role
from django.apps import apps

@pytest.mark.django_db
def test_user_admin(user_project, project, user):
    joe = user('joe', is_superuser = False)
    admin = user('admin', is_superuser = True)
    sa = Role.singleton('System Administrator')

    # this should happen automatically with our signal
    assert sa.members.filter(id=admin.id).exists() is True
    sa.members.remove(admin)

    assert sa.members.filter(id=joe.id).exists() is False
    assert sa.members.filter(id=admin.id).exists() is False

    migrations = rbac.migrate_users(apps, None)

    # The migration should add the admin back in
    assert sa.members.filter(id=joe.id).exists() is False
    assert sa.members.filter(id=admin.id).exists() is True
    assert len(migrations) == 1
