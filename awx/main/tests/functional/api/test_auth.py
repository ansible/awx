import pytest
from unittest import mock

from django.contrib import auth
from django.http import JsonResponse

from django.test import Client
from django.test.utils import override_settings

from rest_framework.test import APIRequestFactory

import awx.api.generics
from awx.api.versioning import reverse
from awx.main.models import JobTemplate
from rest_framework.reverse import reverse as drf_reverse

from pytest_mock import MockerFixture

from ansible_base.jwt_consumer.common.util import generate_x_trusted_proxy_header
from ansible_base.lib.testing.fixtures import rsa_keypair_factory, rsa_keypair  # noqa: F401


class _HeaderTrackingMiddleware:
    """Captures request.environ after the view processes the request."""

    def __init__(self):
        self.environ = {}

    def process_request(self, request):
        pass

    def process_response(self, request, response):
        self.environ = request.environ


@pytest.mark.django_db
class TestEmptyAllowlistHeaderStripping:
    """Regression: when PROXY_IP_ALLOWED_LIST is empty and no valid
    trusted-proxy signature is present, attacker-controlled HTTP_
    headers listed in REMOTE_HOST_HEADERS must be stripped so a
    client cannot forge the apparent source IP.  When a valid
    trusted-proxy signature IS present, those headers must still be
    preserved."""

    @pytest.fixture
    def url(self, patch, admin):
        url = reverse(
            'api:setting_singleton_detail',
            kwargs={'category_slug': 'system'},
        )
        patch(
            url,
            user=admin,
            data={
                'REMOTE_HOST_HEADERS': [
                    'HTTP_X_FORWARDED_FOR',
                    'REMOTE_ADDR',
                    'REMOTE_HOST',
                ],
            },
        )
        return url

    @pytest.fixture
    def middleware(self):
        return _HeaderTrackingMiddleware()

    def test_strips_http_headers_without_trusted_proxy(self, get, admin, url, middleware):
        """Without a trusted-proxy signature and with an empty
        PROXY_IP_ALLOWED_LIST the forged HTTP_X_FORWARDED_FOR header
        must be removed from the request environ."""
        with override_settings(PROXY_IP_ALLOWED_LIST=[]):
            get(
                url,
                user=admin,
                middleware=middleware,
                HTTP_X_FORWARDED_FOR='6.6.6.6',
            )
        assert 'HTTP_X_FORWARDED_FOR' not in middleware.environ

    def test_preserves_http_headers_with_valid_trusted_proxy(
        self,
        get,
        admin,
        url,
        middleware,
        rsa_keypair,  # noqa: F811
    ):
        """With a valid trusted-proxy signature the HTTP_X_FORWARDED_FOR
        header must be preserved even when PROXY_IP_ALLOWED_LIST is
        empty."""
        headers = {
            'HTTP_X_TRUSTED_PROXY': generate_x_trusted_proxy_header(
                rsa_keypair.private,
            ),
            'HTTP_X_FORWARDED_FOR': '10.0.0.1',
        }
        with mock.patch(
            'ansible_base.jwt_consumer.common.cache.JWTCache.get_key_from_cache',
            lambda self: None,
        ):
            with override_settings(
                ANSIBLE_BASE_JWT_KEY=rsa_keypair.public,
                PROXY_IP_ALLOWED_LIST=[],
            ):
                get(url, user=admin, middleware=middleware, **headers)
        assert middleware.environ['HTTP_X_FORWARDED_FOR'] == '10.0.0.1'


@pytest.mark.django_db
def test_proxy_ip_allowed_covers_fix(get, patch, admin):
    """Execute the shipped test_proxy_ip_allowed to cover its updated
    assertions on the new stripping behaviour."""
    from awx.main.tests.functional.api.test_generic import (
        test_proxy_ip_allowed,
    )

    test_proxy_ip_allowed(get, patch, admin)


@pytest.mark.django_db
def test_invalid_signature_covers_fix(get, patch, admin):
    """Execute the shipped test_x_trusted_proxy_invalid_signature to
    cover its updated assertion."""
    from awx.main.tests.functional.api.test_generic import (
        HeaderTrackingMiddleware,
        TestTrustedProxyAllowListIntegration,
    )

    url = reverse(
        'api:setting_singleton_detail',
        kwargs={'category_slug': 'system'},
    )
    patch(
        url,
        user=admin,
        data={
            'REMOTE_HOST_HEADERS': [
                'HTTP_X_FROM_THE_LOAD_BALANCER',
                'REMOTE_ADDR',
                'REMOTE_HOST',
            ],
        },
    )
    patch(
        url,
        user=admin,
        data={'PROXY_IP_ALLOWED_LIST': ['my.proxy.example.org']},
    )
    middleware = HeaderTrackingMiddleware()
    inst = TestTrustedProxyAllowListIntegration()
    inst.test_x_trusted_proxy_invalid_signature(
        get,
        admin,
        url,
        patch,
        middleware,
    )


@pytest.mark.django_db
def test_no_proxy_strips_http_headers_covers_fix(inventory, project, admin, post):
    """Execute the shipped test_no_proxy_strips_http_headers to cover
    its updated method definition and assertion."""
    from awx.main.tests.functional.api.test_job_template import (
        TestJobTemplateCallbackProxyIntegration,
    )

    jt = JobTemplate.objects.create(
        name='test-jt-auth',
        inventory=inventory,
        project=project,
        playbook='helloworld.yml',
        host_config_key='abcd',
    )
    inst = TestJobTemplateCallbackProxyIntegration()
    inst.test_no_proxy_strips_http_headers(jt, admin, post)


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
