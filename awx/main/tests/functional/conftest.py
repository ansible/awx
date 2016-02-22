import pytest

from django.core.urlresolvers import resolve
from django.utils.six.moves.urllib.parse import urlparse

from awx.main.models.organization import Organization
from awx.main.models.ha import Instance
from django.contrib.auth.models import User

from rest_framework.test import (
    APIRequestFactory,
    force_authenticate,
)

from awx.main.models.credential import Credential
from awx.main.models.projects import Project
from awx.main.models.jobs import JobTemplate
from awx.main.models.ha import Instance
from awx.main.models.inventory import (
    Inventory,
    Group,
)
from awx.main.models.organization import (
    Organization,
    Team,
)

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
def check_jobtemplate(project, inventory, credential):
    return \
        JobTemplate.objects.create(
            job_type='check',
            project=project,
            inventory=inventory,
            credential=credential,
            name='check-job-template'
        )

@pytest.fixture
def deploy_jobtemplate(project, inventory, credential):
    return \
        JobTemplate.objects.create(
            job_type='run',
            project=project,
            inventory=inventory,
            credential=credential,
            name='deploy-job-template'
        )

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
def instance(settings):
    return Instance.objects.create(uuid=settings.SYSTEM_UUID, primary=True, hostname="instance.example.org")

@pytest.fixture
def organization(instance):
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

@pytest.fixture
def post():
    def rf(url, data, user=None, middleware=None, **kwargs):
        view, view_args, view_kwargs = resolve(urlparse(url)[2])
        if 'format' not in kwargs:
            kwargs['format'] = 'json'
        request = APIRequestFactory().post(url, data, **kwargs)
        if middleware:
            middleware.process_request(request)
        if user:
            force_authenticate(request, user=user)
        response = view(request, *view_args, **view_kwargs)
        if middleware:
            middleware.process_response(request, response)
        return response
    return rf

@pytest.fixture
def get():
    def rf(url, user=None, middleware=None, **kwargs):
        view, view_args, view_kwargs = resolve(urlparse(url)[2])
        if 'format' not in kwargs:
            kwargs['format'] = 'json'
        request = APIRequestFactory().get(url, **kwargs)
        if middleware:
            middleware.process_request(request)
        if user:
            force_authenticate(request, user=user)
        response = view(request, *view_args, **view_kwargs)
        if middleware:
            middleware.process_response(request, response)
        return response
    return rf

@pytest.fixture
def put():
    def rf(url, data, user=None, middleware=None, **kwargs):
        view, view_args, view_kwargs = resolve(urlparse(url)[2])
        if 'format' not in kwargs:
            kwargs['format'] = 'json'
        request = APIRequestFactory().put(url, data, **kwargs)
        if middleware:
            middleware.process_request(request)
        if user:
            force_authenticate(request, user=user)
        response = view(request, *view_args, **view_kwargs)
        if middleware:
            middleware.process_response(request, response)
        return response
    return rf

@pytest.fixture
def patch():
    def rf(url, data, user=None, middleware=None, **kwargs):
        view, view_args, view_kwargs = resolve(urlparse(url)[2])
        if 'format' not in kwargs:
            kwargs['format'] = 'json'
        request = APIRequestFactory().patch(url, data, **kwargs)
        if middleware:
            middleware.process_request(request)
        if user:
            force_authenticate(request, user=user)
        response = view(request, *view_args, **view_kwargs)
        if middleware:
            middleware.process_response(request, response)
        return response
    return rf

@pytest.fixture
def delete():
    def rf(url, user=None, middleware=None, **kwargs):
        view, view_args, view_kwargs = resolve(urlparse(url)[2])
        if 'format' not in kwargs:
            kwargs['format'] = 'json'
        request = APIRequestFactory().delete(url, **kwargs)
        if middleware:
            middleware.process_request(request)
        if user:
            force_authenticate(request, user=user)
        response = view(request, *view_args, **view_kwargs)
        if middleware:
            middleware.process_response(request, response)
        return response
    return rf

@pytest.fixture
def head():
    def rf(url, user=None, middleware=None, **kwargs):
        view, view_args, view_kwargs = resolve(urlparse(url)[2])
        if 'format' not in kwargs:
            kwargs['format'] = 'json'
        request = APIRequestFactory().head(url, **kwargs)
        if middleware:
            middleware.process_request(request)
        if user:
            force_authenticate(request, user=user)
        response = view(request, *view_args, **view_kwargs)
        if middleware:
            middleware.process_response(request, response)
        return response
    return rf

@pytest.fixture
def options():
    def rf(url, data, user=None, middleware=None, **kwargs):
        view, view_args, view_kwargs = resolve(urlparse(url)[2])
        if 'format' not in kwargs:
            kwargs['format'] = 'json'
        request = APIRequestFactory().options(url, data, **kwargs)
        if middleware:
            middleware.process_request(request)
        if user:
            force_authenticate(request, user=user)
        response = view(request, *view_args, **view_kwargs)
        if middleware:
            middleware.process_response(request, response)
        return response
    return rf

@pytest.fixture(scope="session", autouse=True)
def celery_memory_broker():
    from django.conf import settings
    settings.BROKER_URL='memory://localhost/'
