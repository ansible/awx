import json
import yaml
import os

from coreapi.compat import force_bytes
from django.conf import settings
from openapi_codec.encode import generate_swagger_object
import pytest

import awx
from awx.api.versioning import drf_reverse


config_dest = os.sep.join([
    os.path.realpath(os.path.dirname(awx.__file__)),
    'api', 'templates', 'swagger'
])
config_file = os.sep.join([config_dest, 'config.yml'])
description_file = os.sep.join([config_dest, 'description.md'])


@pytest.mark.django_db
class TestSwaggerGeneration():
    """
    This class is used to generate a Swagger/OpenAPI document for the awx
    API.  A _prepare fixture generates a JSON blob containing OpenAPI data,
    individual tests have the ability modify the payload.

    Finally, the JSON content is written to a file, `swagger.json`, in the
    current working directory.

    $ py.test test_swagger_generation.py --version 3.3.0

    To customize the `info.description` in the generated OpenAPI document,
    modify the text in `awx.api.templates.swagger.description.md`
    """
    JSON = {}

    @pytest.fixture(autouse=True, scope='function')
    def _prepare(self, get, admin):
        if not self.__class__.JSON:
            url = drf_reverse('api:swagger_view') + '?format=openapi'
            response = get(url, user=admin)
            data = generate_swagger_object(response.data)
            if response.has_header('X-Deprecated-Paths'):
                data['deprecated_paths'] = json.loads(response['X-Deprecated-Paths'])
            data.update(response.accepted_renderer.get_customizations() or {})
            self.__class__.JSON = data

    def test_transform_metadata(self, release):
        """
        This test takes the JSON output from the swagger endpoint and applies
        various transformations to it.
        """
        JSON = self.__class__.JSON
        JSON['info']['version'] = release
        JSON['host'] = None
        JSON['schemes'] = ['https']
        JSON['produces'] = ['application/json']
        JSON['consumes'] = ['application/json']

        # Inject a top-level description into the OpenAPI document
        if os.path.exists(description_file):
            with open(description_file, 'r') as f:
                JSON['info']['description'] = f.read()

        # Write tags in the order we want them sorted
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = yaml.load(f.read())
                for category in config.get('categories', []):
                    tag = {'name': category['name']}
                    if 'description' in category:
                        tag['description'] = category['description']
                    JSON.setdefault('tags', []).append(tag)

        revised_paths = {}
        deprecated_paths = JSON.pop('deprecated_paths', [])
        for path, node in self.__class__.JSON['paths'].items():
            # change {version} in paths to the actual default API version (e.g., v2)
            revised_paths[path.replace(
                '{version}',
                settings.REST_FRAMEWORK['DEFAULT_VERSION']
            )] = node
            for method in node:
                if path in deprecated_paths:
                    node[method]['deprecated'] = True
                if 'description' in node[method]:
                    # Pop off the first line and use that as the summary
                    lines = node[method]['description'].splitlines()
                    node[method]['summary'] = lines.pop(0).strip('#:')
                    node[method]['description'] = '\n'.join(lines)
        self.__class__.JSON['paths'] = revised_paths

    @classmethod
    def teardown_class(cls):
        with open('swagger.json', 'w') as f:
            f.write(force_bytes(json.dumps(cls.JSON)))
