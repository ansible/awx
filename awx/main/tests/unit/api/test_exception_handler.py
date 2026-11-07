# -*- coding: utf-8 -*-
from unittest import mock

from django.http import Http404

from rest_framework.test import APIRequestFactory

from awx.api.views import api_exception_handler


def _make_context(request_path, environ=None):
    """Build a minimal DRF exception-handler context dict.

    ``request_path`` is the current value of ``request.path`` (which,
    after named-URL rewriting, is the PK-based path).
    ``environ`` is merged into the WSGI environ of the underlying
    Django request so callers can inject ``awx.named_url_rewritten``.
    """
    factory = APIRequestFactory()
    django_request = factory.get(request_path)
    if environ:
        django_request.environ.update(environ)

    # Wrap in a DRF request just like DRF does before calling
    # the exception handler — api_exception_handler accesses
    # context['request']._request.
    from rest_framework.request import Request

    drf_request = Request(django_request)

    view = mock.MagicMock(spec=[])  # empty spec: not UnifiedJobStdout
    return {
        'view': view,
        'request': drf_request,
    }


class TestApiExceptionHandlerHttp404NamedUrl:
    """Verify the Http404-to-NotFound guard for named-URL-rewritten requests.

    The guard must:
    * Convert Http404 → DRF NotFound (standardised JSON body) and revert
      ``req.path`` to the original named URL when the request was rewritten
      by the NamedUrlRewriteMiddleware  (REJECT: prevents oracle).
    * Leave Http404 untouched when no named-URL rewrite happened, so
      normal 404s still flow through DRF's default handling  (PERMIT).
    """

    def test_http404_with_named_url_rewritten_returns_not_found(self):
        """Http404 + awx.named_url_rewritten  →  path reverted,
        response is a standard DRF 404 with 'Not found.' detail."""
        original_named_path = '/api/v2/organizations/SecretOrg/'
        rewritten_pk_path = '/api/v2/organizations/42/'

        ctx = _make_context(
            rewritten_pk_path,
            environ={'awx.named_url_rewritten': original_named_path},
        )

        exc = Http404('No Organization matches the given query.')
        response = api_exception_handler(exc, ctx)

        # The response must be a standard DRF 404.
        assert response is not None
        assert response.status_code == 404
        assert str(response.data['detail']) == 'Not found.'

        # req.path must have been reverted to the original named URL
        # so the PK-based path is never leaked in any renderer.
        django_req = ctx['request']._request
        assert django_req.path == original_named_path

    def test_http404_without_named_url_rewritten_passes_through(self):
        """Http404 with no named-URL rewrite  →  normal DRF 404,
        path unchanged (the guard does not interfere)."""
        plain_path = '/api/v2/organizations/99999/'

        ctx = _make_context(plain_path)

        exc = Http404('No Organization matches the given query.')
        response = api_exception_handler(exc, ctx)

        # DRF's own exception_handler converts Http404 → NotFound,
        # so we still get a 404 response.
        assert response is not None
        assert response.status_code == 404

        # The path must NOT have been changed — no rewrite happened.
        django_req = ctx['request']._request
        assert django_req.path == plain_path
