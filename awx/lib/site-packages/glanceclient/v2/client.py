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


from glanceclient.common import http
from glanceclient.common import utils
from glanceclient.v2 import image_members
from glanceclient.v2 import image_tags
from glanceclient.v2 import images
from glanceclient.v2 import metadefs
from glanceclient.v2 import schemas
from glanceclient.v2 import tasks


class Client(object):
    """Client for the OpenStack Images v2 API.

    :param string endpoint: A user-supplied endpoint URL for the glance
                            service.
    :param string token: Token for authentication.
    :param integer timeout: Allows customization of the timeout for client
                            http requests. (optional)
    """

    def __init__(self, endpoint, *args, **kwargs):
        endpoint, version = utils.strip_version(endpoint)
        self.version = version or 2.0
        self.http_client = http.HTTPClient(endpoint, *args, **kwargs)

        self.schemas = schemas.Controller(self.http_client)

        self.images = images.Controller(self.http_client, self.schemas)
        self.image_tags = image_tags.Controller(self.http_client,
                                                self.schemas)
        self.image_members = image_members.Controller(self.http_client,
                                                      self.schemas)

        self.tasks = tasks.Controller(self.http_client, self.schemas)

        self.metadefs_resource_type = (
            metadefs.ResourceTypeController(self.http_client, self.schemas))

        self.metadefs_property = (
            metadefs.PropertyController(self.http_client, self.schemas))

        self.metadefs_object = (
            metadefs.ObjectController(self.http_client, self.schemas))

        self.metadefs_namespace = (
            metadefs.NamespaceController(self.http_client, self.schemas))
