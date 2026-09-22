# Copyright (c) 2026 Ansible, Inc.
# All Rights Reserved.

"""
Deprecation header mechanism for AWX API endpoints.

Based on the Controller POC (ANSTRAT-2346).

Headers emitted:
- X-Deprecated: true - Boolean signal
- X-Deprecated-Detail: <text> - Full-sentence description and migration guidance (always required)
- Link: <url>; rel="deprecation" - Pointer to deprecation details
- Warning: 299 - "<text>" - Legacy header (kept for backward compatibility on /v2/)

Usage:

    # Decorator for endpoint-level deprecation (emits on every response)
    @deprecated(
        link="https://docs.ansible.com/aap/latest/changelog#deprecations",
        detail="The /api/v2/roles/ endpoint is deprecated. Use /api/v2/role_definitions/ instead."
    )
    def list(self, request):
        ...

    # Utility function for conditional deprecation (field/parameter/behavior)
    def list(self, request):
        response = Response(data)
        if request.query_params.get("legacy_filter"):
            mark_deprecated(
                response,
                link="https://docs.ansible.com/aap/latest/changelog#deprecations",
                detail="The legacy_filter parameter is deprecated. Use the host_filter parameter instead."
            )
        return response
"""

from functools import wraps
from django.http import HttpResponse


def mark_deprecated(response: HttpResponse, link: str, detail: str) -> HttpResponse:
    """
    Mark a response as deprecated by adding deprecation headers.

    This utility is used for conditional deprecations where only the view
    knows at runtime whether a deprecated code path was taken (e.g.,
    deprecated parameter used, deprecated field in request, behavioral
    deprecation).

    If called multiple times on the same response, details are accumulated
    as space-separated sentences.

    Args:
        response: HttpResponse object to modify
        link: URL to deprecation details (used in Link header)
        detail: Full-sentence description of what is deprecated, ending with a period

    Returns:
        The modified response object (for chaining)
    """
    response['X-Deprecated'] = 'true'

    existing_detail = response.get('X-Deprecated-Detail', '')
    if existing_detail:
        response['X-Deprecated-Detail'] = f"{existing_detail} {detail}"
    else:
        response['X-Deprecated-Detail'] = detail

    if link:
        deprecation_link = f'<{link}>; rel="deprecation"; type="text/html"'
        existing_link = response.get('Link', '')
        if existing_link:
            response['Link'] = f'{existing_link}, {deprecation_link}'
        else:
            response['Link'] = deprecation_link

    return response


def check_deprecated_fields(request, response, fields, link, detail):
    """
    Emit deprecation headers if any of the given fields are present in request.data.

    Call this from view methods (post/put/patch) for field-level deprecations
    that should only signal when the client sends the deprecated field.

    Args:
        request: DRF request object
        response: HttpResponse object to modify
        fields: Field name (str) or iterable of field names to check
        link: URL to deprecation details
        detail: Full-sentence description of what is deprecated

    Returns:
        The response object (for chaining)
    """
    if isinstance(fields, str):
        fields = (fields,)
    if any(f in request.data for f in fields):
        mark_deprecated(response, link=link, detail=detail)
    return response


def deprecated(link: str, detail: str):
    """
    Decorator to mark an entire view/endpoint as deprecated.

    Emits deprecation headers on every response.

    Args:
        link: URL to deprecation details (used in Link header)
        detail: Full-sentence description of what is deprecated, ending with a period
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
