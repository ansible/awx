import pytest
import mock

from django.core.urlresolvers import resolve
from django.utils.six.moves.urllib.parse import urlparse

from awx.main.models.organization import Organization
from awx.main.models.projects import Project
from awx.main.models.ha import Instance
from django.contrib.auth.models import User
from rest_framework.test import (
    APIRequestFactory,
    force_authenticate,
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

@pytest.fixture
def instance(settings):
    return Instance.objects.create(uuid=settings.SYSTEM_UUID, primary=True, hostname="instance.example.org")

@pytest.fixture
def organization(instance):
    return Organization.objects.create(name="test-org", description="test-org-desc")

@pytest.fixture
@mock.patch.object(Project, "update", lambda self, **kwargs: None)
def project(instance):
    return Project.objects.create(name="test-proj",
                                  description="test-proj-desc",
                                  scm_type="git",
                                  scm_url="https://github.com/jlaska/ansible-playbooks")
