# Copyright (c) 2013 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""Volume Type interface."""

from cinderclient import base


class VolumeType(base.Resource):
    """A Volume Type is the type of volume to be created."""
    def __repr__(self):
        return "<VolumeType: %s>" % self.name

    def get_keys(self):
        """Get extra specs from a volume type.

        :param vol_type: The :class:`VolumeType` to get extra specs from
        """
        _resp, body = self.manager.api.client.get(
            "/types/%s/extra_specs" %
            base.getid(self))
        return body["extra_specs"]

    def set_keys(self, metadata):
        """Set extra specs on a volume type.

        :param type : The :class:`VolumeType` to set extra spec on
        :param metadata: A dict of key/value pairs to be set
        """
        body = {'extra_specs': metadata}
        return self.manager._create(
            "/types/%s/extra_specs" % base.getid(self),
            body,
            "extra_specs",
            return_raw=True)

    def unset_keys(self, keys):
        """Unset extra specs on a volue type.

        :param type_id: The :class:`VolumeType` to unset extra spec on
        :param keys: A list of keys to be unset
        """

        # NOTE(jdg): This wasn't actually doing all of the keys before
        # the return in the loop resulted in ony ONE key being unset.
        # since on success the return was NONE, we'll only interrupt the loop
        # and return if there's an error
        for k in keys:
            resp = self.manager._delete(
                "/types/%s/extra_specs/%s" % (
                base.getid(self), k))
            if resp is not None:
                return resp


class VolumeTypeManager(base.ManagerWithFind):
    """Manage :class:`VolumeType` resources."""
    resource_class = VolumeType

    def list(self, search_opts=None):
        """Lists all volume types.

        :rtype: list of :class:`VolumeType`.
        """
        return self._list("/types", "volume_types")

    def get(self, volume_type):
        """Get a specific volume type.

        :param volume_type: The ID of the :class:`VolumeType` to get.
        :rtype: :class:`VolumeType`
        """
        return self._get("/types/%s" % base.getid(volume_type), "volume_type")

    def delete(self, volume_type):
        """Deletes a specific volume_type.

        :param volume_type: The name or ID of the :class:`VolumeType` to get.
        """
        self._delete("/types/%s" % base.getid(volume_type))

    def create(self, name):
        """Creates a volume type.

        :param name: Descriptive name of the volume type
        :rtype: :class:`VolumeType`
        """

        body = {
            "volume_type": {
                "name": name,
            }
        }

        return self._create("/types", body, "volume_type")
