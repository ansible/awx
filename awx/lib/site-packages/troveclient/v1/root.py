# Copyright 2011 OpenStack Foundation
# Copyright 2013 Rackspace Hosting
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

from troveclient import base
from troveclient import common
from troveclient.v1 import users


class Root(base.ManagerWithFind):
    """Manager class for Root resource."""
    resource_class = users.User
    url = "/instances/%s/root"

    def create(self, instance):
        """Implements root-enable API.

        Enable the root user and return the root password for the
        specified db instance.
        """
        resp, body = self.api.client.post(self.url % base.getid(instance))
        common.check_for_exceptions(resp, body, self.url)
        return body['user']['name'], body['user']['password']

    def is_root_enabled(self, instance):
        """Return whether root is enabled for the instance."""
        resp, body = self.api.client.get(self.url % base.getid(instance))
        common.check_for_exceptions(resp, body, self.url)
        return self.resource_class(self, body, loaded=True)

    # Appease the abc gods
    def list(self):
        pass
