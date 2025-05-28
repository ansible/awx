import pytest

from django.contrib import auth
from django.http import JsonResponse

from django.test import Client

from rest_framework.test import APIRequestFactory

import awx.api.generics
from rest_framework.reverse import reverse as drf_reverse

from pytest_mock import MockerFixture


@pytest.mark.django_db
def test_invalid_login():
    anon = auth.get_user(Client())
    url = drf_reverse('api:login')

    factory = APIRequestFactory()

    data = {'userame': 'invalid', 'password': 'invalid'}

    request = factory.post(url, data)
    request.user = anon

    response = awx.api.generics.LoggedLoginView.as_view()(request)

    assert response.status_code == 401


@pytest.mark.django_db
def test_invalid_post(mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch):
    url = drf_reverse('api:login')
    factory = APIRequestFactory()
    request = factory.post(url)

    is_proxied_request_mock = mocker.Mock(
        autospec=True,
        name='is_proxied_request',
        return_value=True,
    )
    monkeypatch.setattr(awx.api.generics, 'is_proxied_request', is_proxied_request_mock)
    response = awx.api.generics.LoggedLoginView.as_view()(request)

    assert isinstance(response, JsonResponse)
    assert b'Please log in via Platform Authentication.' in response.content
    assert response.status_code == 401
