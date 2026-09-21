# Copyright (c) 2026 Ansible, Inc.
# All Rights Reserved.

"""
Tests for the deprecation header mechanism (ANSTRAT-2346).

Validates that deprecated API endpoints emit the correct HTTP response headers:
- X-Deprecated: true
- X-Deprecated-Detail: <description>
- Link: <url>; rel="deprecation"
"""

from rest_framework.response import Response
from rest_framework.test import APIRequestFactory

from awx.api.deprecation import mark_deprecated, deprecated
from awx.api.schema import postprocess_inject_deprecation_headers


class TestMarkDeprecatedUtility:
    """Test the mark_deprecated() utility function."""

    def test_mark_deprecated_adds_required_headers(self):
        """X-Deprecated, X-Deprecated-Detail, and Link headers are added."""
        response = Response({"data": "test"})
        mark_deprecated(
            response,
            detail="This endpoint is deprecated.",
            link="https://docs.example.com/deprecations",
        )

        assert response['X-Deprecated'] == 'true'
        assert response['X-Deprecated-Detail'] == "This endpoint is deprecated."
        assert 'https://docs.example.com/deprecations' in response['Link']
        assert 'rel="deprecation"' in response['Link']

    def test_mark_deprecated_first_link_wins(self):
        """First link wins when mark_deprecated called multiple times."""
        response = Response({"data": "test"})

        mark_deprecated(
            response,
            detail="This endpoint is deprecated.",
            link="https://docs.example.com/deprecations",
        )
        mark_deprecated(
            response,
            detail="Another deprecation.",
            link="https://docs.example.com/other-link",
        )

        link_header = response['Link']
        assert '<https://docs.example.com/deprecations>; rel="deprecation"' in link_header
        assert '<https://docs.example.com/other-link>' not in link_header

    def test_mark_deprecated_accumulates_details_with_spaces(self):
        """Multiple calls accumulate details as space-separated sentences."""
        response = Response({"data": "test"})
        mark_deprecated(
            response,
            detail="The /api/v2/roles/ endpoint is deprecated.",
            link="https://docs.example.com/deprecations",
        )
        mark_deprecated(
            response,
            detail="The legacy_filter parameter is deprecated.",
            link="https://docs.example.com/deprecations",
        )

        assert response['X-Deprecated-Detail'] == ("The /api/v2/roles/ endpoint is deprecated. " "The legacy_filter parameter is deprecated.")

    def test_mark_deprecated_deduplicates_details(self):
        """Duplicate details are ignored."""
        response = Response({"data": "test"})
        mark_deprecated(
            response,
            detail="This endpoint is deprecated.",
            link="https://docs.example.com/deprecations",
        )
        mark_deprecated(
            response,
            detail="This endpoint is deprecated.",
            link="https://docs.example.com/deprecations",
        )

        assert response['X-Deprecated-Detail'] == "This endpoint is deprecated."


class TestDeprecatedDecorator:
    """Test the @deprecated decorator."""

    def test_decorator_adds_headers(self):
        """Decorator adds deprecation headers to response."""

        class TestView:
            @deprecated(
                detail="This endpoint is deprecated.",
                link="https://docs.example.com/deprecations",
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
                detail="This endpoint is deprecated.",
                link="https://docs.example.com/deprecations",
            )
            def get(self, request):
                return Response({"count": 5, "results": [1, 2, 3]})

        factory = APIRequestFactory()
        request = factory.get('/test/')
        view = TestView()
        response = view.get(request)

        assert response.data == {"count": 5, "results": [1, 2, 3]}
        assert response['X-Deprecated'] == 'true'


# Integration tests for deprecation headers are in awx/main/tests/functional/api/


class TestPostprocessInjectDeprecationHeaders:
    """Unit tests for the postprocessing hook."""

    def test_injects_headers_on_deprecated_operations(self):
        schema = {
            "paths": {
                "/api/v2/roles/": {
                    "get": {
                        "deprecated": True,
                        "responses": {"200": {"description": "OK"}},
                    }
                }
            }
        }
        result = postprocess_inject_deprecation_headers(schema, None, None, None)
        headers = result["paths"]["/api/v2/roles/"]["get"]["responses"]["200"]["headers"]
        assert "X-Deprecated" in headers
        assert "X-Deprecated-Detail" in headers
        assert "Link" in headers

    def test_skips_non_deprecated_operations(self):
        schema = {
            "paths": {
                "/api/v2/users/": {
                    "get": {
                        "responses": {"200": {"description": "OK"}},
                    }
                }
            }
        }
        result = postprocess_inject_deprecation_headers(schema, None, None, None)
        assert "headers" not in result["paths"]["/api/v2/users/"]["get"]["responses"]["200"]

    def test_preserves_existing_headers(self):
        schema = {
            "paths": {
                "/api/v2/roles/": {
                    "get": {
                        "deprecated": True,
                        "responses": {
                            "200": {
                                "description": "OK",
                                "headers": {"X-Custom": {"schema": {"type": "string"}}},
                            }
                        },
                    }
                }
            }
        }
        result = postprocess_inject_deprecation_headers(schema, None, None, None)
        headers = result["paths"]["/api/v2/roles/"]["get"]["responses"]["200"]["headers"]
        assert "X-Custom" in headers
        assert "X-Deprecated" in headers
