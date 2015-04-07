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


class Flavor(base.Resource):
    """A Flavor is an Instance type, specifying other things, like RAM size."""

    def __repr__(self):
        return "<Flavor: %s>" % self.name


class Flavors(base.ManagerWithFind):
    """Manage :class:`Flavor` resources."""
    resource_class = Flavor

    def list(self):
        """Get a list of all flavors.
        :rtype: list of :class:`Flavor`.
        """
        return self._list("/flavors", "flavors")

    def list_datastore_version_associated_flavors(self, datastore,
                                                  version_id):
        """Get a list of all flavors for the specified datastore type
        and datastore version .
        :rtype: list of :class:`Flavor`.
        """
        return self._list("/datastores/%s/versions/%s/flavors" %
                         (datastore, version_id),
                          "flavors")

    def get(self, flavor):
        """Get a specific flavor.

        :rtype: :class:`Flavor`
        """
        return self._get("/flavors/%s" % base.getid(flavor),
                         "flavor")
