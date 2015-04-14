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


class Device(base.Resource):
    """Storage is an opaque instance used to hold storage information."""
    def __repr__(self):
        return "<Device: %s>" % self.name


class StorageInfo(base.ManagerWithFind):
    """Manage :class:`Storage` resources."""
    resource_class = Device

    def _list(self, url, response_key):
        resp, body = self.api.client.get(url)
        if not body:
            raise Exception("Call to " + url + " did not return a body.")
        return [self.resource_class(self, res) for res in body[response_key]]

    def index(self):
        """Get a list of all storages.

        :rtype: list of :class:`Storages`.
        """
        return self._list("/mgmt/storage", "devices")

    # Appease the abc gods
    def list(self):
        pass
