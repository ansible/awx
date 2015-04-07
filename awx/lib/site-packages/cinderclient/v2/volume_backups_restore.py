# Copyright (C) 2013 Hewlett-Packard Development Company, L.P.
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

"""Volume Backups Restore interface (1.1 extension).

This is part of the Volume Backups interface.
"""

from cinderclient import base


class VolumeBackupsRestore(base.Resource):
    """A Volume Backups Restore represents a restore operation."""
    def __repr__(self):
        return "<VolumeBackupsRestore: %s>" % self.volume_id


class VolumeBackupRestoreManager(base.Manager):
    """Manage :class:`VolumeBackupsRestore` resources."""
    resource_class = VolumeBackupsRestore

    def restore(self, backup_id, volume_id=None):
        """Restore a backup to a volume.

        :param backup_id: The ID of the backup to restore.
        :param volume_id: The ID of the volume to restore the backup to.
        :rtype: :class:`Restore`
        """
        body = {'restore': {'volume_id': volume_id}}
        return self._create("/backups/%s/restore" % backup_id,
                            body, "restore")
