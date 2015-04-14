# Copyright 2012 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import copy
import json
import jsonpatch
import six
import warlock.model as warlock


class SchemaBasedModel(warlock.Model):
    """Glance specific subclass of the warlock Model

    This implementation alters the function of the patch property
    to take into account the schema's core properties. With this version
    undefined properties which are core will generated 'replace'
    operations rather than 'add' since this is what the Glance API
    expects.
    """

    def _make_custom_patch(self, new, original):
        if not self.get('tags'):
            tags_patch = []
        else:
            tags_patch = [{"path": "/tags",
                          "value": self.get('tags'),
                          "op": "replace"}]

        patch_string = jsonpatch.make_patch(original, new).to_string()
        patch = json.loads(patch_string)
        if not patch:
            return json.dumps(tags_patch)
        else:
            return json.dumps(patch + tags_patch)

    @warlock.Model.patch.getter
    def patch(self):
        """Return a jsonpatch object representing the delta."""
        original = copy.deepcopy(self.__dict__['__original__'])
        new = dict(self)
        if self.schema:
            for (name, prop) in six.iteritems(self.schema['properties']):
                if (name not in original and name in new and
                        prop.get('is_base', True)):
                    original[name] = None

        original['tags'] = None
        new['tags'] = None
        return self._make_custom_patch(new, original)


class SchemaProperty(object):
    def __init__(self, name, **kwargs):
        self.name = name
        self.description = kwargs.get('description')


def translate_schema_properties(schema_properties):
    """Parse the properties dictionary of a schema document

    :returns list of SchemaProperty objects
    """
    properties = []
    for (name, prop) in schema_properties.items():
        properties.append(SchemaProperty(name, **prop))
    return properties


class Schema(object):
    def __init__(self, raw_schema):
        self._raw_schema = raw_schema
        self.name = raw_schema['name']
        raw_properties = raw_schema['properties']
        self.properties = translate_schema_properties(raw_properties)

    def is_core_property(self, property_name):
        for prop in self.properties:
            if property_name == prop.name:
                return True
        return False

    def raw(self):
        return copy.deepcopy(self._raw_schema)


class Controller(object):
    def __init__(self, http_client):
        self.http_client = http_client

    def get(self, schema_name):
        uri = '/v2/schemas/%s' % schema_name
        _, raw_schema = self.http_client.get(uri)
        return Schema(raw_schema)
