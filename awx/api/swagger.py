import json
import warnings

from coreapi.document import Object, Link

from rest_framework import exceptions
from rest_framework.permissions import AllowAny
from rest_framework.renderers import CoreJSONRenderer
from rest_framework.response import Response
from rest_framework.schemas import SchemaGenerator, AutoSchema as DRFAuthSchema
from rest_framework.views import APIView

from rest_framework_swagger import renderers


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
            warnings.warn('{}.get_serializer() raised an exception during '
                          'schema generation. Serializer fields will not be '
                          'generated for {} {}.'
                          .format(self.view.__class__.__name__, method, path))

        link.__dict__['deprecated'] = getattr(self.view, 'deprecated', False)

        # auto-generate a topic/tag for the serializer based on its model
        if hasattr(self.view, 'swagger_topic'):
            link.__dict__['topic'] = str(self.view.swagger_topic).title()
        elif serializer and hasattr(serializer, 'Meta'):
            link.__dict__['topic'] = str(
                serializer.Meta.model._meta.verbose_name_plural
            ).title()
        elif hasattr(self.view, 'model'):
            link.__dict__['topic'] = str(self.view.model._meta.verbose_name_plural).title()
        else:
            warnings.warn('Could not determine a Swagger tag for path {}'.format(path))
        return link

    def get_description(self, path, method):
        setattr(self.view.request, 'swagger_method', method)
        description = super(AutoSchema, self).get_description(path, method)
        return description


class SwaggerSchemaView(APIView):
    _ignore_model_permissions = True
    exclude_from_schema = True
    permission_classes = [AllowAny]
    renderer_classes = [
        CoreJSONRenderer,
        renderers.OpenAPIRenderer,
        renderers.SwaggerUIRenderer
    ]

    def get(self, request):
        generator = SuperUserSchemaGenerator(
            title='Ansible Tower API',
            patterns=None,
            urlconf=None
        )
        schema = generator.get_schema(request=request)
        # python core-api doesn't support the deprecation yet, so track it
        # ourselves and return it in a response header
        _deprecated = []

        # By default, DRF OpenAPI serialization places all endpoints in
        # a single node based on their root path (/api).  Instead, we want to
        # group them by topic/tag so that they're categorized in the rendered
        # output
        document = schema._data.pop('api')
        for path, node in document.items():
            if isinstance(node, Object):
                for action in node.values():
                    topic = getattr(action, 'topic', None)
                    if topic:
                        schema._data.setdefault(topic, Object())
                        schema._data[topic]._data[path] = node

                    if isinstance(action, Object):
                        for link in action.links.values():
                            if link.deprecated:
                                _deprecated.append(link.url)
            elif isinstance(node, Link):
                topic = getattr(node, 'topic', None)
                if topic:
                    schema._data.setdefault(topic, Object())
                    schema._data[topic]._data[path] = node

        if not schema:
            raise exceptions.ValidationError(
                'The schema generator did not return a schema Document'
            )

        return Response(
            schema,
            headers={'X-Deprecated-Paths': json.dumps(_deprecated)}
        )
