# Deprecation Headers Implementation - Controller POC

This document describes the proof-of-concept implementation of the API deprecation header mechanism in AWX/Controller, based on the [Controller POC](file:///Users/smichel/Work/handbook/AWX-Controller-Deprecation-Header-POC.md) for ANSTRAT-2346.

## Overview

The deprecation header mechanism provides runtime signaling to API consumers when they use deprecated endpoints, parameters, or behaviors.

**Headers Emitted:**
- `X-Deprecated: true` - Boolean signal
- `X-Deprecated-Detail: <text>` - Description and migration guidance
- `Link: <url>; rel="deprecation"` - Changelog URL
- `Warning: 299 - "<text>"` - Legacy header (kept for backward compatibility)

## Implementation Components

### 1. Deprecation Utilities (`awx/api/deprecation.py`)

Provides two mechanisms for emitting deprecation headers:

#### Decorator (for endpoint-level deprecation)

Use when the entire endpoint is deprecated:

```python
from awx.api.deprecation import deprecated

@deprecated(
    link="https://docs.ansible.com/aap/latest/changelog#deprecations",
    detail="Use /api/v2/role_definitions/ instead"
)
class RolesViewSet(ModelViewSet):
    def list(self, request):
        return Response({"data": "..."})
```

#### Utility Function (for conditional deprecation)

Use when deprecation depends on runtime conditions (parameter used, behavior taken, etc.):

```python
from awx.api.deprecation import mark_deprecated

def list(self, request):
    response = Response({"data": "..."})
    
    if request.query_params.get("legacy_filter"):
        mark_deprecated(
            response,
            detail="Parameter 'legacy_filter' is deprecated; use 'host_filter' instead"
        )
    
    return response
```

### 2. View Attribute Mechanism (`awx/api/generics.py`)

The existing `deprecated = True` view attribute now emits the new headers automatically via `finalize_response()`:

```python
class RoleList(ListAPIView):
    deprecated = True
    deprecation_detail = "Use /api/v2/role_definitions/ instead"
    deprecation_link = "https://docs.ansible.com/aap/latest/changelog#deprecations"
    model = models.Role
    serializer_class = serializers.RoleSerializer
```

View attributes:
- `deprecated` (bool): Mark the view as deprecated
- `deprecation_detail` (str, optional): Custom detail message
- `deprecation_link` (str, optional): Custom changelog URL (default: Tower release notes)

### 3. OpenAPI Schema Annotations

The OpenAPI schema should mark deprecated operations with `deprecated: true` for documentation and tooling purposes. The Controller POC uses view-level headers without requiring additional OpenAPI extensions.

```yaml
paths:
  /api/v2/roles/:
    get:
      deprecated: true
      summary: List Roles (Deprecated)
      description: |
        **This endpoint is deprecated.** Use `/api/v2/role_definitions/` instead.
```

### 4. Validation Script (`scripts/validate-deprecation-annotations.py`)

Simple validation script that reports deprecated operations in the OpenAPI spec:

```bash
# Generate schema
make genschema

# Check for deprecated operations
python3 scripts/validate-deprecation-annotations.py --spec-paths "schema.json"
```

## Headers Emitted

When a client requests a deprecated endpoint, the response includes:

```http
HTTP/1.1 200 OK
Content-Type: application/json
X-Deprecated: true
X-Deprecated-Detail: Use /api/v2/role_definitions/ instead
Link: <https://docs.ansible.com/aap/latest/changelog#deprecations>; rel="deprecation"
Warning: 299 - "This resource has been deprecated and will be removed in a future release."

{"count": 12, "results": [...]}
```

**Note:** The `Warning: 299` header is retained for backward compatibility during the transition period.

## PoC Scenarios

### Scenario A: Endpoint-Level Deprecation

```python
class RoleList(ListAPIView):
    deprecated = True
    deprecation_detail = "Use /api/v2/role_definitions/ instead"
    # ...
```

### Scenario B: Parameter-Level Deprecation

```python
def list(self, request):
    queryset = self.filter_queryset(self.get_queryset())
    page = self.paginate_queryset(queryset)
    serializer = self.get_serializer(page, many=True)
    response = self.get_paginated_response(serializer.data)
    
    if 'legacy_filter' in request.query_params:
        mark_deprecated(
            response,
            detail="Parameter 'legacy_filter' is deprecated; use 'host_filter' instead"
        )
    
    return response
```

### Scenario C: Multiple Deprecations

If both the endpoint and a parameter are deprecated, the details are accumulated:

```python
@deprecated(
    link="https://docs.ansible.com/aap/latest/changelog#deprecations",
    detail="Endpoint /api/v2/roles/ is deprecated; use /api/v2/role_definitions/"
)
class RolesViewSet(ModelViewSet):
    def list(self, request):
        # ... build response ...
        
        if 'legacy_filter' in request.query_params:
            mark_deprecated(
                response,
                detail="Parameter 'legacy_filter' is deprecated"
            )
        
        return response
```

Response headers:
```
X-Deprecated: true
X-Deprecated-Detail: Endpoint /api/v2/roles/ is deprecated; use /api/v2/role_definitions/, Parameter 'legacy_filter' is deprecated
```

## Client-Side Expectations

Consumers should:

1. **Log warnings** when `X-Deprecated: true` is present
2. **Follow the `Link` header** to find migration guidance
3. **Not break** on unknown headers (standard HTTP behavior)

### Example: Python Client

```python
response = requests.get(f"{base_url}/api/v2/roles/")

if response.headers.get("X-Deprecated") == "true":
    detail = response.headers.get("X-Deprecated-Detail", "")
    link = response.links.get("deprecation", {}).get("url", "N/A")
    
    msg = f"{response.url} is deprecated."
    if detail:
        msg += f" {detail}."
    msg += f" See: {link}"
    
    warnings.warn(msg, DeprecationWarning)
```

## Testing

### Unit Tests

Tests are in `awx/main/tests/unit/api/test_deprecation_headers.py`:

```bash
pytest awx/main/tests/unit/api/test_deprecation_headers.py
```

### Manual Testing

1. Generate the OpenAPI schema:
   ```bash
   make genschema
   ```

2. Verify a deprecated endpoint is marked:
   ```bash
   cat schema.json | jq '.paths."/api/v2/roles/".get.deprecated'
   # Should output: true
   ```

3. Test the runtime headers:
   ```bash
   curl -i -u admin:password https://localhost:8043/api/v2/roles/
   ```
   
   Should include:
   ```
   X-Deprecated: true
   X-Deprecated-Detail: <message>
   Link: <https://...>; rel="deprecation"
   Warning: 299 - "<message>"
   ```

## Migration from Warning: 299

Existing deprecated views continue to work without changes. The old `Warning: 299` header is still emitted alongside the new headers during the transition period.

To fully adopt the new mechanism:

1. ✅ Set `deprecated = True` (already done for existing deprecated views)
2. ✅ Headers are automatically emitted (implemented in `finalize_response`)
3. ✅ Set `deprecation_detail` attribute for better messages (optional but recommended)
4. ⬜ Update changelog to document the deprecation
5. ⬜ Add CI validation step (future work)

## References

- **Controller POC**: [/Users/smichel/Work/handbook/AWX-Controller-Deprecation-Header-POC.md](file:///Users/smichel/Work/handbook/AWX-Controller-Deprecation-Header-POC.md)
- **Parent Initiative**: [ANSTRAT-2346](https://redhat.atlassian.net/browse/ANSTRAT-2346)
- **Jira Story**: [AAP-86438](https://redhat.atlassian.net/browse/AAP-86438) (Implement deprecation header mechanism)

## Backward Compatibility

✅ **Non-breaking**: All changes are backward compatible
- New headers are purely informational
- Existing clients ignore unknown headers per HTTP/1.1 (RFC 9110)
- No client updates required before deployment
- Response bodies and status codes unchanged
- Legacy `Warning: 299` header maintained for transition period
