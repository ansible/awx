# Copyright (C) 2013, Red Hat, Inc.
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
Assisted volume snapshots - to be used by Cinder and not end users.
"""

import json

from novaclient import base


class Snapshot(base.Resource):
    def __repr__(self):
        return "<Snapshot: %s>" % self.id

    def delete(self):
        """
        Delete this snapshot.
        """
        self.manager.delete(self)


class AssistedSnapshotManager(base.Manager):
    resource_class = Snapshot

    def create(self, volume_id, create_info):
        body = {'snapshot': {'volume_id': volume_id,
                             'create_info': create_info}}
        return self._create('/os-assisted-volume-snapshots', body, 'snapshot')

    def delete(self, snapshot, delete_info):
        self._delete("/os-assisted-volume-snapshots/%s?delete_info=%s" % (
            base.getid(snapshot), json.dumps(delete_info)))

manager_class = AssistedSnapshotManager
name = 'assisted_volume_snapshots'
