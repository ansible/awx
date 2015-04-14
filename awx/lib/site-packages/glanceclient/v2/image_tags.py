# Copyright 2013 OpenStack Foundation
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

import warlock

from glanceclient.common import utils
from glanceclient.v2 import schemas


class Controller(object):
    def __init__(self, http_client, schema_client):
        self.http_client = http_client
        self.schema_client = schema_client

    @utils.memoized_property
    def model(self):
        schema = self.schema_client.get('image')
        return warlock.model_factory(schema.raw(), schemas.SchemaBasedModel)

    def update(self, image_id, tag_value):
        """
        Update an image with the given tag.

        :param image_id:    image to be updated with the given tag.
        :param tag_value:   value of the tag.
        """
        url = '/v2/images/%s/tags/%s' % (image_id, tag_value)
        self.http_client.put(url)

    def delete(self, image_id, tag_value):
        """
        Delete the tag associated with the given image.

        :param image_id:    Image whose tag to be deleted.
        :param tag_value:   tag value to be deleted.
        """
        url = '/v2/images/%s/tags/%s' % (image_id, tag_value)
        self.http_client.delete(url)
