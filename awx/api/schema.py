import json
import os
import warnings

from rest_framework.permissions import IsAuthenticated
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)


def filter_credential_type_schema(
    result,
    generator,  # NOSONAR
    request,  # NOSONAR
    public,  # NOSONAR
):
    """
    Postprocessing hook to filter CredentialType kind enum values.

    For CredentialTypeRequest and PatchedCredentialTypeRequest schemas (POST/PUT/PATCH),
    filter the 'kind' enum to only show 'cloud' and 'net' values.

    This ensures the OpenAPI schema accurately reflects that only 'cloud' and 'net'
    credential types can be created or modified via the API, matching the validation
    in CredentialTypeSerializer.validate().

    Args:
        result: The OpenAPI schema dict to be modified
        generator, request, public: Required by drf-spectacular interface (unused)

    Returns:
        The modified OpenAPI schema dict
    """
    schemas = result.get('components', {}).get('schemas', {})

    # Filter CredentialTypeRequest (POST/PUT) - field is required
    if 'CredentialTypeRequest' in schemas:
        kind_prop = schemas['CredentialTypeRequest'].get('properties', {}).get('kind', {})
        if 'enum' in kind_prop:
            # Filter to only cloud and net (no None - field is required)
            kind_prop['enum'] = ['cloud', 'net']
            kind_prop['description'] = "* `cloud` - Cloud\\n* `net` - Network"

    # Filter PatchedCredentialTypeRequest (PATCH) - field is optional
    if 'PatchedCredentialTypeRequest' in schemas:
        kind_prop = schemas['PatchedCredentialTypeRequest'].get('properties', {}).get('kind', {})
        if 'enum' in kind_prop:
            # Filter to only cloud and net (None allowed - field can be omitted in PATCH)
            kind_prop['enum'] = ['cloud', 'net', None]
            kind_prop['description'] = "* `cloud` - Cloud\\n* `net` - Network"

    return result


def inject_ai_descriptions(
    result,
    generator,  # NOSONAR
    request,  # NOSONAR
    public,  # NOSONAR
):
    """
    Inject x-ai-description into operations from the overlay file.

    Many endpoints have human-readable AI descriptions that were added
    downstream but not backported as @extend_schema_if_available decorators.
    This hook merges them from a JSON file keyed by operationId.
    """
    overlay_path = os.path.join(os.path.dirname(__file__), 'openapi_ai_descriptions.json')
    try:
        with open(overlay_path) as f:
            descriptions = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return result

    for path_item in result.get('paths', {}).values():
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue
            op_id = operation.get('operationId')
            if op_id and op_id in descriptions and 'x-ai-description' not in operation:
                operation['x-ai-description'] = descriptions[op_id]

    return result


def inject_clean_text_pattern_components(
    result,
    generator,  # NOSONAR
    request,  # NOSONAR
    public,  # NOSONAR
):
    """Declare CleanText pattern fields on CredentialType.inputs in OpenAPI.

    Models ``inputs`` to match runtime credential-type catalogs: ``fields[]``
    items are ``CleanTextNestedStringField`` (optional pattern / patternDescription /
    flags; no normalize). ``required`` lists field ids; ``metadata`` is optional
    and only present on some types. Other keys (e.g. ``dependencies``) remain
    allowed via ``additionalProperties``.
    """
    try:
        from ansible_base.api_documentation.clean_text_schema_hooks import (
            inject_clean_text_pattern_components as _dab_inject,
        )
    except ImportError:  # pragma: no cover - older DAB without shared schemas
        return result

    result = _dab_inject(result, generator, request, public)
    schemas = result.get('components', {}).get('schemas', {})
    field_item_ref = {'$ref': '#/components/schemas/CleanTextNestedStringField'}
    for schema_name in (
        'CredentialType',
        'CredentialTypeRequest',
        'PatchedCredentialTypeRequest',
    ):
        schema = schemas.get(schema_name)
        if not isinstance(schema, dict):
            continue
        props = schema.setdefault('properties', {})
        existing = props.get('inputs') if isinstance(props.get('inputs'), dict) else {}
        base_description = existing.get('description') or ('Enter inputs using either JSON or YAML syntax. Refer to the documentation for example syntax.')
        note = (
            'When ENHANCED_INPUT_VALIDATION_ENABLED is on, non-secret string '
            'entries in fields[] may include optional pattern, patternDescription, '
            'and flags (Tier 2). Secret and non-string fields omit them. '
            'Requiredness is expressed via inputs.required, not per-field required.'
        )
        description = base_description if note in base_description else f'{base_description} {note}'.strip()
        props['inputs'] = {
            'type': 'object',
            'description': description,
            'properties': {
                'fields': {
                    'type': 'array',
                    'description': 'Input field catalog. Dynamic per credential type.',
                    'items': field_item_ref,
                },
                'required': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'Optional list of field ids that are required.',
                },
                'metadata': {
                    'type': 'array',
                    'description': ('Optional. Present only on some external-secret credential types; same item shape as fields[].'),
                    'items': field_item_ref,
                },
            },
            'additionalProperties': True,
        }
        if 'default' in existing:
            props['inputs']['default'] = existing['default']
    return result


class CustomAutoSchema(AutoSchema):
    """Custom AutoSchema to add swagger_topic to tags and handle deprecated endpoints."""

    def get_tags(self):
        tags = []
        try:
            if hasattr(self.view, 'get_serializer'):
                serializer = self.view.get_serializer()
            else:
                serializer = None
        except Exception:
            serializer = None
            warnings.warn(
                '{}.get_serializer() raised an exception during schema generation. Serializer fields will not be generated for this view.'.format(
                    self.view.__class__.__name__
                )
            )

        if hasattr(self.view, 'swagger_topic'):
            tags.append(str(self.view.swagger_topic).title())
        elif serializer and hasattr(serializer, 'Meta') and hasattr(serializer.Meta, 'model'):
            tags.append(str(serializer.Meta.model._meta.verbose_name_plural).title())
        elif hasattr(self.view, 'model'):
            tags.append(str(self.view.model._meta.verbose_name_plural).title())
        else:
            tags = super().get_tags()  # Use default drf-spectacular behavior

        if not tags:
            warnings.warn(f'Could not determine tags for {self.view.__class__.__name__}')
            tags = ['api']  # Fallback to default value

        return tags

    def is_deprecated(self):
        """Return `True` if this operation is to be marked as deprecated."""
        return getattr(self.view, 'deprecated', False)


class AuthenticatedSpectacularAPIView(SpectacularAPIView):
    """SpectacularAPIView that requires authentication."""

    permission_classes = [IsAuthenticated]


class AuthenticatedSpectacularSwaggerView(SpectacularSwaggerView):
    """SpectacularSwaggerView that requires authentication."""

    permission_classes = [IsAuthenticated]


class AuthenticatedSpectacularRedocView(SpectacularRedocView):
    """SpectacularRedocView that requires authentication."""

    permission_classes = [IsAuthenticated]


# Schema view (returns OpenAPI schema JSON/YAML)
schema_view = AuthenticatedSpectacularAPIView.as_view()

# Swagger UI view
swagger_ui_view = AuthenticatedSpectacularSwaggerView.as_view(url_name='api:schema-json')

# ReDoc UI view
redoc_view = AuthenticatedSpectacularRedocView.as_view(url_name='api:schema-json')
