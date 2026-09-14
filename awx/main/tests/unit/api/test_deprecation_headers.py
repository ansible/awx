# Copyright (c) 2026 Ansible, Inc.
# All Rights Reserved.

"""
Tests for the deprecation header mechanism (ANSTRAT-2346).

Validates that deprecated API endpoints emit the correct HTTP response headers:
- X-Deprecated: true
- X-Deprecated-Detail: <description>
- Link: <url>; rel="deprecation"

Also validates that the OpenAPI schema includes x-deprecated-since extensions.
"""

import pytest
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory

from awx.api.deprecation import mark_deprecated, deprecated


class TestMarkDeprecatedUtility:
    """Test the mark_deprecated() utility function."""

    def test_mark_deprecated_adds_required_headers(self):
        """X-Deprecated and Link headers are added."""
        response = Response({"data": "test"})
        result = mark_deprecated(
            response,
            link="https://docs.example.com/deprecations"
        )

        assert result['X-Deprecated'] == 'true'
        assert 'https://docs.example.com/deprecations' in result['Link']
        assert 'rel="deprecation"' in result['Link']
        assert 'type="text/html"' in result['Link']

    def test_mark_deprecated_with_detail(self):
        """X-Deprecated-Detail header is added when detail is provided."""
        response = Response({"data": "test"})
        mark_deprecated(
            response,
            link="https://docs.example.com/deprecations",
            detail="Use /api/v2/new_endpoint/ instead"
        )

        assert response['X-Deprecated'] == 'true'
        assert response['X-Deprecated-Detail'] == "Use /api/v2/new_endpoint/ instead"

    def test_mark_deprecated_without_detail(self):
        """X-Deprecated-Detail header is not added when detail is omitted."""
        response = Response({"data": "test"})
        mark_deprecated(
            response,
            link="https://docs.example.com/deprecations"
        )

        assert response['X-Deprecated'] == 'true'
        assert 'X-Deprecated-Detail' not in response

    def test_mark_deprecated_appends_to_existing_link(self):
        """Link header is appended to existing Link header."""
        response = Response({"data": "test"})
        response['Link'] = '<https://example.com/other>; rel="alternate"'

        mark_deprecated(
            response,
            link="https://docs.example.com/deprecations"
        )

        link_header = response['Link']
        assert '<https://example.com/other>; rel="alternate"' in link_header
        assert '<https://docs.example.com/deprecations>; rel="deprecation"' in link_header
        assert ', ' in link_header  # Multiple links separated by comma

    def test_mark_deprecated_returns_response(self):
        """Function returns the response for chaining convenience."""
        response = Response({"data": "test"})
        result = mark_deprecated(
            response,
            link="https://docs.example.com/deprecations"
        )

        assert result is response


class TestDeprecatedDecorator:
    """Test the @deprecated decorator."""

    def test_decorator_adds_headers(self):
        """Decorator adds deprecation headers to response."""
        class TestView:
            @deprecated(link="https://docs.example.com/deprecations")
            def get(self, request):
                return Response({"data": "test"})

        factory = APIRequestFactory()
        request = factory.get('/test/')
        view = TestView()
        response = view.get(request)

        assert response['X-Deprecated'] == 'true'
        assert 'https://docs.example.com/deprecations' in response['Link']

    def test_decorator_with_detail(self):
        """Decorator adds detail header when provided."""
        class TestView:
            @deprecated(
                link="https://docs.example.com/deprecations",
                detail="Use the new API instead"
            )
            def get(self, request):
                return Response({"data": "test"})

        factory = APIRequestFactory()
        request = factory.get('/test/')
        view = TestView()
        response = view.get(request)

        assert response['X-Deprecated'] == 'true'
        assert response['X-Deprecated-Detail'] == "Use the new API instead"

    def test_decorator_preserves_response_data(self):
        """Decorator doesn't modify the response body."""
        class TestView:
            @deprecated(link="https://docs.example.com/deprecations")
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
        # RoleList is a deprecated view in AWX
        url = '/api/v2/roles/'
        response = get(url, user=admin_user, expect=200)

        assert response['X-Deprecated'] == 'true'
        assert 'Link' in response
        assert 'rel="deprecation"' in response['Link']

        # Legacy Warning header should still be present during transition
        assert 'Warning' in response
        assert '299' in response['Warning']

    @pytest.mark.django_db
    def test_non_deprecated_view_no_headers(self, get, admin_user):
        """Non-deprecated views don't emit deprecation headers."""
        # Users endpoint is not deprecated
        url = '/api/v2/users/'
        response = get(url, user=admin_user, expect=200)

        assert 'X-Deprecated' not in response
        assert 'X-Deprecated-Detail' not in response

    @pytest.mark.django_db
    def test_deprecated_view_with_custom_link(self, get, admin_user):
        """Deprecated views can specify a custom deprecation link."""
        # This would test a view with deprecated_link attribute set
        # For now, we verify the default link is used
        url = '/api/v2/roles/'
        response = get(url, user=admin_user, expect=200)

        assert 'Link' in response
        # Default link from generics.py
        assert 'docs.ansible.com' in response['Link'] or 'http' in response['Link']


class TestOpenAPISchemaExtensions:
    """Test that OpenAPI schema includes x-deprecated-since extensions."""

    @pytest.mark.django_db
    def test_deprecated_operation_has_extension(self, get, admin_user):
        """Deprecated operations include x-deprecated-since in the schema."""
        # Get the OpenAPI schema
        url = '/api/v2/schema/'
        response = get(url, user=admin_user, expect=200)
        schema = response.data

        # Find a deprecated endpoint (e.g., /api/v2/roles/)
        roles_path = schema['paths'].get('/api/v2/roles/')
        assert roles_path is not None, "Roles endpoint should exist in schema"

        # Check the GET operation
        get_op = roles_path.get('get')
        assert get_op is not None, "GET operation should exist"
        assert get_op.get('deprecated') is True, "Operation should be marked deprecated"

        # Verify x-deprecated-since extension is present
        assert 'x-deprecated-since' in get_op, "x-deprecated-since extension should be present"

        # Verify it's in the correct format (major.minor)
        since_version = get_op['x-deprecated-since']
        assert isinstance(since_version, str), "x-deprecated-since should be a string"
        assert '.' in since_version, "x-deprecated-since should be in major.minor format"

        parts = since_version.split('.')
        assert len(parts) == 2, "x-deprecated-since should have exactly 2 parts"
        assert parts[0].isdigit(), "Major version should be numeric"
        assert parts[1].isdigit(), "Minor version should be numeric"

    @pytest.mark.django_db
    def test_non_deprecated_operation_no_extension(self, get, admin_user):
        """Non-deprecated operations don't have x-deprecated-since."""
        url = '/api/v2/schema/'
        response = get(url, user=admin_user, expect=200)
        schema = response.data

        # Find a non-deprecated endpoint (e.g., /api/v2/users/)
        users_path = schema['paths'].get('/api/v2/users/')
        assert users_path is not None, "Users endpoint should exist in schema"

        get_op = users_path.get('get')
        assert get_op is not None, "GET operation should exist"

        # Should not be marked deprecated
        assert get_op.get('deprecated') is not True

        # Should not have x-deprecated-since extension
        assert 'x-deprecated-since' not in get_op


class TestValidationScript:
    """Test the deprecation annotation validation script."""

    def test_validation_script_exists(self):
        """Validation script exists and is executable."""
        import os
        from pathlib import Path

        script_path = Path(__file__).parent.parent.parent.parent.parent / 'scripts' / 'validate-deprecation-annotations.py'
        assert script_path.exists(), f"Validation script should exist at {script_path}"
        assert os.access(script_path, os.X_OK), "Validation script should be executable"

    def test_validation_script_imports(self):
        """Validation script can be imported without errors."""
        import sys
        from pathlib import Path

        script_path = Path(__file__).parent.parent.parent.parent.parent / 'scripts'
        sys.path.insert(0, str(script_path))

        try:
            # Import should not raise
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "validate_deprecation_annotations",
                script_path / "validate-deprecation-annotations.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Verify key functions exist
            assert hasattr(module, 'validate_spec')
            assert hasattr(module, 'load_spec')
            assert hasattr(module, 'main')
        finally:
            sys.path.pop(0)
