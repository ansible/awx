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
                '{}.get_serializer() raised an exception during '
                'schema generation. Serializer fields will not be '
                'generated for this view.'.format(self.view.__class__.__name__)
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
