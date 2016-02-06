import pytest

from awx.main.models.organization import Organization
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
    def rf(_cls, _user, _url, pk=None, kwargs={}, middleware=None):
        view = _cls.as_view()
        request = APIRequestFactory().post(_url, kwargs, format='json')
        if middleware:
            middleware.process_request(request)
        force_authenticate(request, user=_user)
        response = view(request, pk=pk)
        if middleware:
            middleware.process_response(request, response)
        return response
    return rf

@pytest.fixture
def get():
    def rf(_cls, _user, _url, pk=None, middleware=None):
        view = _cls.as_view()
        request = APIRequestFactory().get(_url, format='json')
        if middleware:
            middleware.process_request(request)
        force_authenticate(request, user=_user)
        response = view(request, pk=pk)
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
