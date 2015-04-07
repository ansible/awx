# Copyright (c) 2013 OpenStack Foundation
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

"""Volume snapshot interface (1.1 extension)."""

import six
try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

from cinderclient import base


class Snapshot(base.Resource):
    """A Snapshot is a point-in-time snapshot of an openstack volume."""
    def __repr__(self):
        return "<Snapshot: %s>" % self.id

    def delete(self):
        """Delete this snapshot."""
        self.manager.delete(self)

    def update(self, **kwargs):
        """Update the name or description for this snapshot."""
        self.manager.update(self, **kwargs)

    @property
    def progress(self):
        return self._info.get('os-extended-snapshot-attributes:progress')

    @property
    def project_id(self):
        return self._info.get('os-extended-snapshot-attributes:project_id')

    def reset_state(self, state):
        """Update the snapshot with the provided state."""
        self.manager.reset_state(self, state)

    def set_metadata(self, metadata):
        """Set metadata of this snapshot."""
        return self.manager.set_metadata(self, metadata)

    def delete_metadata(self, keys):
        """Delete metadata of this snapshot."""
        return self.manager.delete_metadata(self, keys)

    def update_all_metadata(self, metadata):
        """Update_all metadata of this snapshot."""
        return self.manager.update_all_metadata(self, metadata)


class SnapshotManager(base.ManagerWithFind):
    """Manage :class:`Snapshot` resources."""
    resource_class = Snapshot

    def create(self, volume_id, force=False,
               name=None, description=None):

        """Creates a snapshot of the given volume.

        :param volume_id: The ID of the volume to snapshot.
        :param force: If force is True, create a snapshot even if the volume is
        attached to an instance. Default is False.
        :param name: Name of the snapshot
        :param description: Description of the snapshot
        :rtype: :class:`Snapshot`
        """
        body = {'snapshot': {'volume_id': volume_id,
                             'force': force,
                             'name': name,
                             'description': description}}
        return self._create('/snapshots', body, 'snapshot')

    def get(self, snapshot_id):
        """Shows snapshot details.

        :param snapshot_id: The ID of the snapshot to get.
        :rtype: :class:`Snapshot`
        """
        return self._get("/snapshots/%s" % snapshot_id, "snapshot")

    def list(self, detailed=True, search_opts=None):
        """Get a list of all snapshots.

        :rtype: list of :class:`Snapshot`
        """

        if search_opts is None:
            search_opts = {}

        qparams = {}

        for opt, val in six.iteritems(search_opts):
            if val:
                qparams[opt] = val

        # Transform the dict to a sequence of two-element tuples in fixed
        # order, then the encoded string will be consistent in Python 2&3.
        if qparams:
            new_qparams = sorted(qparams.items(), key=lambda x: x[0])
            query_string = "?%s" % urlencode(new_qparams)
        else:
            query_string = ""

        detail = ""
        if detailed:
            detail = "/detail"

        return self._list("/snapshots%s%s" % (detail, query_string),
                          "snapshots")

    def delete(self, snapshot):
        """Delete a snapshot.

        :param snapshot: The :class:`Snapshot` to delete.
        """
        self._delete("/snapshots/%s" % base.getid(snapshot))

    def update(self, snapshot, **kwargs):
        """Update the name or description for a snapshot.

        :param snapshot: The :class:`Snapshot` to update.
        """
        if not kwargs:
            return

        body = {"snapshot": kwargs}

        self._update("/snapshots/%s" % base.getid(snapshot), body)

    def reset_state(self, snapshot, state):
        """Update the specified snapshot with the provided state."""
        return self._action('os-reset_status', snapshot, {'status': state})

    def _action(self, action, snapshot, info=None, **kwargs):
        """Perform a snapshot action."""
        body = {action: info}
        self.run_hooks('modify_body_for_action', body, **kwargs)
        url = '/snapshots/%s/action' % base.getid(snapshot)
        return self.api.client.post(url, body=body)

    def update_snapshot_status(self, snapshot, update_dict):
        return self._action('os-update_snapshot_status',
                            base.getid(snapshot), update_dict)

    def set_metadata(self, snapshot, metadata):
        """Update/Set a snapshots metadata.

        :param snapshot: The :class:`Snapshot`.
        :param metadata: A list of keys to be set.
        """
        body = {'metadata': metadata}
        return self._create("/snapshots/%s/metadata" % base.getid(snapshot),
                            body, "metadata")

    def delete_metadata(self, snapshot, keys):
        """Delete specified keys from snapshot metadata.

        :param snapshot: The :class:`Snapshot`.
        :param keys: A list of keys to be removed.
        """
        snapshot_id = base.getid(snapshot)
        for k in keys:
            self._delete("/snapshots/%s/metadata/%s" % (snapshot_id, k))

    def update_all_metadata(self, snapshot, metadata):
        """Update_all snapshot metadata.

        :param snapshot: The :class:`Snapshot`.
        :param metadata: A list of keys to be updated.
        """
        body = {'metadata': metadata}
        return self._update("/snapshots/%s/metadata" % base.getid(snapshot),
                            body)
