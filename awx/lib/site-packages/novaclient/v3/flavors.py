# Copyright 2010 Jacob Kaplan-Moss
# Copyright 2013 IBM Corp.
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

"""
Flavor interface.
"""

from novaclient import base
from novaclient import utils
from novaclient.v1_1 import flavors


class Flavor(base.Resource):
    """
    A flavor is an available hardware configuration for a server.
    """
    HUMAN_ID = True

    def __repr__(self):
        return "<Flavor: %s>" % self.name

    @property
    def is_public(self):
        """
        Provide a user-friendly accessor to flavor-access:is_public
        """
        return self._info.get("flavor-access:is_public", 'N/A')

    def get_keys(self):
        """
        Get extra specs from a flavor.

        :param flavor: The :class:`Flavor` to get extra specs from
        """
        _resp, body = self.manager.api.client.get(
                            "/flavors/%s/flavor-extra-specs" %
                            base.getid(self))
        return body["extra_specs"]

    def set_keys(self, metadata):
        """
        Set extra specs on a flavor.

        :param flavor: The :class:`Flavor` to set extra spec on
        :param metadata: A dict of key/value pairs to be set
        """
        utils.validate_flavor_metadata_keys(metadata.keys())

        body = {'extra_specs': metadata}
        return self.manager._create(
                            "/flavors/%s/flavor-extra-specs" %
                            base.getid(self), body, "extra_specs",
                            return_raw=True)

    def unset_keys(self, keys):
        """
        Unset extra specs on a flavor.

        :param flavor: The :class:`Flavor` to unset extra spec on
        :param keys: A list of keys to be unset
        """
        for k in keys:
            return self.manager._delete(
                            "/flavors/%s/flavor-extra-specs/%s" % (
                            base.getid(self), k))

    def delete(self):
        """
        Delete this flavor.
        """
        self.manager.delete(self)


class FlavorManager(flavors.FlavorManager):
    resource_class = Flavor

    def _build_body(self, name, ram, vcpus, disk, id, swap,
                    ephemeral, rxtx_factor, is_public):
        return {
            "flavor": {
                "name": name,
                "ram": ram,
                "vcpus": vcpus,
                "disk": disk,
                "id": id,
                "swap": swap,
                "ephemeral": ephemeral,
                "rxtx_factor": rxtx_factor,
                "flavor-access:is_public": is_public,
            }
        }
