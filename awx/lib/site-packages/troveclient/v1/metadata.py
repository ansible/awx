# Copyright 2014 Rackspace Hosting
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

import json
from troveclient import base


class MetadataResource(base.Resource):
    def __getitem__(self, item):
        return self.__dict__[item]

    def __contains__(self, item):
        if item in self.__dict__:
                return True
        else:
            return False


class Metadata(base.Manager):

    resource_class = MetadataResource

    def list(self, instance_id):
        return self._get('/instances/%s/metadata' % instance_id, 'metadata')

    def show(self, instance_id, key):
        return self._get('/instances/%s/metadata/%s' % (instance_id, key),
                         'metadata')

    def create(self, instance_id, key, value):
        body = {
            'metadata': {
                'value': self._parse_value(value)
            }
        }
        return self._create(
            '/instances/%s/metadata/%s' % (instance_id, key), body, 'metadata')

    def update(self, instance_id, key, newkey, value):
        body = {
            'metadata': {
                'key': newkey,
                'value': self._parse_value(value)
            }
        }
        return self._update(
            '/instances/%s/metadata/%s' % (instance_id, key), body)

    def edit(self, instance_id, key, value):
        body = {
            'metadata': {
                'value': self._parse_value(value)
            }
        }
        return self._edit(
            '/instances/%s/metadata/%s' % (instance_id, key), body)

    def delete(self, instance_id, key):
        return self._delete('/instances/%s/metadata/%s' % (instance_id, key))

    @staticmethod
    def _parse_value(value):
        """This method is used to parse if a string was passed to any of the
        methods we should first try to deserialize it using json.loads.  This
        is needed to facilitate users passing serialized structures from the
        cli.

        :param value: A value of type dict, list, tuple, int, float, str

        :returns value:
        """
        # NOTE(imsplitbit): if you give _parse_value invalid json you get
        # the string passed back to you.
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except ValueError:
                # the value passed in was a string but not json
                pass

        return value
