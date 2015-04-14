# Copyright 2011 Denali Systems, Inc.
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

"""
Volume snapshot interface (1.1 extension).
"""

from novaclient import base


class Snapshot(base.Resource):
    """
    A Snapshot is a point-in-time snapshot of an openstack volume.
    """
    NAME_ATTR = 'display_name'

    def __repr__(self):
        return "<Snapshot: %s>" % self.id

    def delete(self):
        """
        Delete this snapshot.
        """
        self.manager.delete(self)


class SnapshotManager(base.ManagerWithFind):
    """
    Manage :class:`Snapshot` resources.
    """
    resource_class = Snapshot

    def create(self, volume_id, force=False, display_name=None,
               display_description=None):

        """
        Create a snapshot of the given volume.

        :param volume_id: The ID of the volume to snapshot.
        :param force: If force is True, create a snapshot even if the volume is
        attached to an instance. Default is False.
        :param display_name: Name of the snapshot
        :param display_description: Description of the snapshot
        :rtype: :class:`Snapshot`
        """
        body = {'snapshot': {'volume_id': volume_id,
                             'force': force,
                             'display_name': display_name,
                             'display_description': display_description}}
        return self._create('/snapshots', body, 'snapshot')

    def get(self, snapshot_id):
        """
        Get a snapshot.

        :param snapshot_id: The ID of the snapshot to get.
        :rtype: :class:`Snapshot`
        """
        return self._get("/snapshots/%s" % snapshot_id, "snapshot")

    def list(self, detailed=True):
        """
        Get a list of all snapshots.

        :rtype: list of :class:`Snapshot`
        """
        if detailed is True:
            return self._list("/snapshots/detail", "snapshots")
        else:
            return self._list("/snapshots", "snapshots")

    def delete(self, snapshot):
        """
        Delete a snapshot.

        :param snapshot: The :class:`Snapshot` to delete.
        """
        self._delete("/snapshots/%s" % base.getid(snapshot))
