import pytest

from django.contrib import auth
from django.test import Client

from rest_framework.test import APIRequestFactory

from awx.api.generics import LoggedLoginView
from awx.api.versioning import drf_reverse


@pytest.mark.django_db
def test_invalid_login():
    anon = auth.get_user(Client())
    url = drf_reverse('api:login')
 
    factory = APIRequestFactory()

    data = {'userame': 'invalid', 'password': 'invalid'}

    request = factory.post(url, data)
    request.user = anon

    response = LoggedLoginView.as_view()(request)

    assert response.status_code == 401
