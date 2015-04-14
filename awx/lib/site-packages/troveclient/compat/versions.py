# Copyright (c) 2011 OpenStack Foundation
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

from troveclient.compat import base


class Version(base.Resource):
    """Version is an opaque instance used to hold version information."""
    def __repr__(self):
        return "<Version: %s>" % self.id


class Versions(base.ManagerWithFind):
    """Manage :class:`Versions` information."""

    resource_class = Version

    def index(self, url):
        """Get a list of all versions.

        :rtype: list of :class:`Versions`.
        """
        resp, body = self.api.client.request(url, "GET")
        return [self.resource_class(self, res) for res in body['versions']]
