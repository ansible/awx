# Copyright (c) 2026 Ansible, Inc.
# All Rights Reserved.

"""
Deprecation header mechanism for AWX API endpoints.

Based on the Controller POC (ANSTRAT-2346).

Headers emitted:
- X-Deprecated: true - Boolean signal
- X-Deprecated-Detail: <text> - Description and migration guidance
- Link: <url>; rel="deprecation" - Changelog URL
- Warning: 299 - "<text>" - Legacy header (kept for backward compatibility)

Usage:

    # Decorator for endpoint-level deprecation
    @deprecated(
        link="https://docs.ansible.com/aap/latest/changelog#deprecations",
        detail="Use /api/v2/role_definitions/ instead"
    )
    def list(self, request):
        ...

    # Utility function for conditional deprecation
    def list(self, request):
        response = Response(data)
        if request.query_params.get("legacy_filter"):
            mark_deprecated(
                response,
                link="https://docs.ansible.com/aap/latest/changelog#deprecations",
                detail="Parameter 'legacy_filter' is deprecated; use 'host_filter' instead"
            )
        return response
"""

from functools import wraps
from django.http import HttpResponse


def mark_deprecated(response: HttpResponse, link: str, detail: str = "") -> HttpResponse:
    """
    Mark a response as deprecated by adding deprecation headers.

    This utility is used for conditional deprecations where only the view
    knows at runtime whether a deprecated code path was taken (e.g.,
    deprecated parameter used, deprecated field in response, behavioral
    deprecation).

    If called multiple times on the same response, details are accumulated
    with comma-separation.

    Args:
        response: HttpResponse object to modify
        link: URL to changelog fragment (used in Link header)
        detail: Short description of what's deprecated

    Returns:
        The modified response object (for chaining)

    Example:
        response = Response(data)
        if request.query_params.get("legacy_filter"):
            mark_deprecated(
                response,
                detail="Parameter 'legacy_filter' is deprecated"
            )
        return response
    """
    # Set or update X-Deprecated header
    response['X-Deprecated'] = 'true'

    # Append to X-Deprecated-Detail if already present
    existing_detail = response.get('X-Deprecated-Detail', '')
    if existing_detail:
        response['X-Deprecated-Detail'] = f"{existing_detail}, {detail}"
    else:
        response['X-Deprecated-Detail'] = detail

    # Set Link header if provided
    if link:
        response['Link'] = f'<{link}>; rel="deprecation"'

    return response


def deprecated(link: str, detail: str):
    """
    Decorator to mark an entire view/endpoint as deprecated.

    Args:
        link: URL to changelog fragment (used in Link header)
        detail: Short description of what's deprecated and migration path

    Example:
        @deprecated(
            link="https://docs.ansible.com/aap/latest/changelog#deprecations",
            detail="Use /api/v2/role_definitions/ instead"
        )
        class RolesViewSet(ModelViewSet):
            def list(self, request):
                ...
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            response = view_func(*args, **kwargs)

            if isinstance(response, HttpResponse):
                mark_deprecated(response, link=link, detail=detail)

            return response

        return wrapper

    return decorator
