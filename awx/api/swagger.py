import warnings

from rest_framework.permissions import AllowAny
from rest_framework.schemas import SchemaGenerator, AutoSchema as DRFAuthSchema

from drf_yasg.views import get_schema_view
from drf_yasg import openapi


class SuperUserSchemaGenerator(SchemaGenerator):
    def has_view_permissions(self, path, method, view):
        #
        # Generate the Swagger schema as if you were a superuser and
        # permissions didn't matter; this short-circuits the schema path
        # discovery to include _all_ potential paths in the API.
        #
        return True


class AutoSchema(DRFAuthSchema):
    def get_link(self, path, method, base_url):
        link = super(AutoSchema, self).get_link(path, method, base_url)
        try:
            serializer = self.view.get_serializer()
        except Exception:
            serializer = None
            warnings.warn(
                '{}.get_serializer() raised an exception during '
                'schema generation. Serializer fields will not be '
                'generated for {} {}.'.format(self.view.__class__.__name__, method, path)
            )

        link.__dict__['deprecated'] = getattr(self.view, 'deprecated', False)

        # auto-generate a topic/tag for the serializer based on its model
        if hasattr(self.view, 'swagger_topic'):
            link.__dict__['topic'] = str(self.view.swagger_topic).title()
        elif serializer and hasattr(serializer, 'Meta'):
            link.__dict__['topic'] = str(serializer.Meta.model._meta.verbose_name_plural).title()
        elif hasattr(self.view, 'model'):
            link.__dict__['topic'] = str(self.view.model._meta.verbose_name_plural).title()
        else:
            warnings.warn('Could not determine a Swagger tag for path {}'.format(path))
        return link

    def get_description(self, path, method):
        setattr(self.view.request, 'swagger_method', method)
        description = super(AutoSchema, self).get_description(path, method)
        return description


schema_view = get_schema_view(
    openapi.Info(
        title="Snippets API",
        default_version='v1',
        description="Test description",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[AllowAny],
)
