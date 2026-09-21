# Copyright (c) 2026 Ansible, Inc.
# All Rights Reserved.

"""
Tests for the deprecation header mechanism (ANSTRAT-2346).

Validates that deprecated API endpoints emit the correct HTTP response headers:
- X-Deprecated: true
- X-Deprecated-Detail: <description>
- Link: <url>; rel="deprecation"

Also validates that the OpenAPI schema includes x-deprecated-detail and x-deprecated-link extensions.
"""

import pytest
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory

from awx.api.deprecation import mark_deprecated, deprecated


class TestMarkDeprecatedUtility:
    """Test the mark_deprecated() utility function."""

    def test_mark_deprecated_adds_required_headers(self):
        """X-Deprecated, X-Deprecated-Detail, and Link headers are added."""
        response = Response({"data": "test"})
        result = mark_deprecated(
            response,
            link="https://docs.example.com/deprecations",
            detail="This endpoint is deprecated.",
        )

        assert result['X-Deprecated'] == 'true'
        assert result['X-Deprecated-Detail'] == "This endpoint is deprecated."
        assert 'https://docs.example.com/deprecations' in result['Link']
        assert 'rel="deprecation"' in result['Link']
        assert 'type="text/html"' in result['Link']

    def test_mark_deprecated_appends_to_existing_link(self):
        """Link header is appended to existing Link header."""
        response = Response({"data": "test"})
        response['Link'] = '<https://example.com/other>; rel="alternate"'

        mark_deprecated(
            response,
            link="https://docs.example.com/deprecations",
            detail="This endpoint is deprecated.",
        )

        link_header = response['Link']
        assert '<https://example.com/other>; rel="alternate"' in link_header
        assert '<https://docs.example.com/deprecations>; rel="deprecation"' in link_header
        assert ', ' in link_header

    def test_mark_deprecated_returns_response(self):
        """Function returns the response for chaining convenience."""
        response = Response({"data": "test"})
        result = mark_deprecated(
            response,
            link="https://docs.example.com/deprecations",
            detail="This endpoint is deprecated.",
        )

        assert result is response

    def test_mark_deprecated_accumulates_details_with_spaces(self):
        """Multiple calls accumulate details as space-separated sentences."""
        response = Response({"data": "test"})
        mark_deprecated(
            response,
            link="https://docs.example.com/deprecations",
            detail="The /api/v2/roles/ endpoint is deprecated.",
        )
        mark_deprecated(
            response,
            link="https://docs.example.com/deprecations",
            detail="The legacy_filter parameter is deprecated.",
        )

        assert response['X-Deprecated-Detail'] == ("The /api/v2/roles/ endpoint is deprecated. " "The legacy_filter parameter is deprecated.")

    def test_mark_deprecated_requires_detail(self):
        """detail parameter is required (not optional)."""
        response = Response({"data": "test"})
        with pytest.raises(TypeError):
            mark_deprecated(response, link="https://docs.example.com/deprecations")


class TestDeprecatedDecorator:
    """Test the @deprecated decorator."""

    def test_decorator_adds_headers(self):
        """Decorator adds deprecation headers to response."""

        class TestView:
            @deprecated(
                link="https://docs.example.com/deprecations",
                detail="This endpoint is deprecated.",
            )
            def get(self, request):
                return Response({"data": "test"})

        factory = APIRequestFactory()
        request = factory.get('/test/')
        view = TestView()
        response = view.get(request)

        assert response['X-Deprecated'] == 'true'
        assert response['X-Deprecated-Detail'] == "This endpoint is deprecated."
        assert 'https://docs.example.com/deprecations' in response['Link']

    def test_decorator_preserves_response_data(self):
        """Decorator doesn't modify the response body."""

        class TestView:
            @deprecated(
                link="https://docs.example.com/deprecations",
                detail="This endpoint is deprecated.",
            )
            def get(self, request):
                return Response({"count": 5, "results": [1, 2, 3]})

        factory = APIRequestFactory()
        request = factory.get('/test/')
        view = TestView()
        response = view.get(request)

        assert response.data == {"count": 5, "results": [1, 2, 3]}
        assert response['X-Deprecated'] == 'true'


class TestDeprecatedViewAttribute:
    """Test the deprecated = True view attribute with finalize_response."""

    @pytest.mark.django_db
    def test_deprecated_view_emits_headers(self, get, admin_user):
        """Views with deprecated = True emit deprecation headers."""
        url = '/api/v2/roles/'
        response = get(url, user=admin_user, expect=200)

        assert response['X-Deprecated'] == 'true'
        assert 'X-Deprecated-Detail' in response
        assert 'Link' in response
        assert 'rel="deprecation"' in response['Link']

        # Legacy Warning header should still be present during transition
        assert 'Warning' in response
        assert '299' in response['Warning']

    @pytest.mark.django_db
    def test_non_deprecated_view_no_headers(self, get, admin_user):
        """Non-deprecated views don't emit deprecation headers."""
        url = '/api/v2/users/'
        response = get(url, user=admin_user, expect=200)

        assert 'X-Deprecated' not in response
        assert 'X-Deprecated-Detail' not in response


class TestOpenAPISchemaExtensions:
    """Test that OpenAPI schema includes x-deprecated-detail and x-deprecated-link extensions."""

    @pytest.mark.django_db
    def test_deprecated_operation_has_extensions(self, get, admin_user):
        """Deprecated operations with deprecation dict include extensions in the schema."""
        url = '/api/v2/schema/'
        response = get(url, user=admin_user, expect=200)
        schema = response.data

        # Dashboard has both deprecated=True and a deprecation dict
        dashboard_path = schema['paths'].get('/api/v2/dashboard/')
        assert dashboard_path is not None, "Dashboard endpoint should exist in schema"

        get_op = dashboard_path.get('get')
        assert get_op is not None, "GET operation should exist"
        assert get_op.get('deprecated') is True, "Operation should be marked deprecated"

        assert 'x-deprecated-detail' in get_op, "x-deprecated-detail extension should be present"
        assert isinstance(get_op['x-deprecated-detail'], str)
        assert len(get_op['x-deprecated-detail']) > 0

        assert 'x-deprecated-link' in get_op, "x-deprecated-link extension should be present"
        assert isinstance(get_op['x-deprecated-link'], str)

    @pytest.mark.django_db
    def test_non_deprecated_operation_no_extensions(self, get, admin_user):
        """Non-deprecated operations don't have deprecation extensions."""
        url = '/api/v2/schema/'
        response = get(url, user=admin_user, expect=200)
        schema = response.data

        users_path = schema['paths'].get('/api/v2/users/')
        assert users_path is not None, "Users endpoint should exist in schema"

        get_op = users_path.get('get')
        assert get_op is not None, "GET operation should exist"

        assert get_op.get('deprecated') is not True
        assert 'x-deprecated-detail' not in get_op
        assert 'x-deprecated-link' not in get_op
