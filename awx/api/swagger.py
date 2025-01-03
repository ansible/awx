import warnings

from rest_framework.permissions import AllowAny
from drf_yasg import openapi
from drf_yasg.inspectors import SwaggerAutoSchema
from drf_yasg.views import get_schema_view


class CustomSwaggerAutoSchema(SwaggerAutoSchema):
    """Custom SwaggerAutoSchema to add swagger_topic to tags."""

    def get_tags(self, operation_keys=None):
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
                'generated for {}.'.format(self.view.__class__.__name__, operation_keys)
            )
        if hasattr(self.view, 'swagger_topic'):
            tags.append(str(self.view.swagger_topic).title())
        elif serializer and hasattr(serializer, 'Meta'):
            tags.append(str(serializer.Meta.model._meta.verbose_name_plural).title())
        elif hasattr(self.view, 'model'):
            tags.append(str(self.view.model._meta.verbose_name_plural).title())
        else:
            tags = ['api']  # Fallback to default value

        if not tags:
            warnings.warn(f'Could not determine tags for {self.view.__class__.__name__}')
        return tags

    def is_deprecated(self):
        """Return `True` if this operation is to be marked as deprecated."""
        return getattr(self.view, 'deprecated', False)


schema_view = get_schema_view(
    openapi.Info(
        title='AWX API',
        default_version='v2',
        description='AWX API Documentation',
        terms_of_service='https://www.google.com/policies/terms/',
        contact=openapi.Contact(email='contact@snippets.local'),
        license=openapi.License(name='Apache License'),
    ),
    public=True,
    permission_classes=[AllowAny],
)
