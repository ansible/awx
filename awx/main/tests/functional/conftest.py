import pytest

from awx.main.models.credential import Credential
from awx.main.models.inventory import (
    Inventory,
    Group,
)
from awx.main.models.projects import Project
from awx.main.models.organization import (
    Organization,
    Team,
)
from django.contrib.auth.models import User

@pytest.fixture
def user():
    def u(name, is_superuser=False):
        try:
            user = User.objects.get(username=name)
        except User.DoesNotExist:
            user = User(username=name, is_superuser=is_superuser, password=name)
            user.save()
        return user
    return u

@pytest.fixture
def team(organization):
    return Team.objects.create(organization=organization, name='test-team')

@pytest.fixture
def project(organization):
    prj = Project.objects.create(name="test-project",  description="test-project-desc")
    prj.organizations.add(organization)
    return prj

@pytest.fixture
def user_project(user):
    owner = user('owner')
    return Project.objects.create(name="test-user-project", created_by=owner, description="test-user-project-desc")

@pytest.fixture
def organization():
    return Organization.objects.create(name="test-org", description="test-org-desc")

@pytest.fixture
def credential():
    return Credential.objects.create(kind='aws', name='test-cred')

@pytest.fixture
def inventory(organization):
    return Inventory.objects.create(name="test-inventory", organization=organization)

@pytest.fixture
def group(inventory):
    def g(name):
        return Group.objects.create(inventory=inventory, name=name)
    return g

@pytest.fixture
def permissions():
    return {
        'admin':{'create':True, 'read':True, 'write':True,
                 'update':True, 'delete':True, 'scm_update':True, 'execute':True, 'use':True,},

        'auditor':{'read':True, 'create':False, 'write':False,
                   'update':False, 'delete':False, 'scm_update':False, 'execute':False, 'use':False,},

        'usage':{'read':False, 'create':False, 'write':False,
                 'update':False, 'delete':False, 'scm_update':False, 'execute':False, 'use':True,},
    }

