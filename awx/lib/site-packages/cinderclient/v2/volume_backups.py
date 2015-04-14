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

"""
Volume Backups interface (1.1 extension).
"""

from cinderclient import base


class VolumeBackup(base.Resource):
    """A volume backup is a block level backup of a volume."""
    def __repr__(self):
        return "<VolumeBackup: %s>" % self.id

    def delete(self):
        """Delete this volume backup."""
        return self.manager.delete(self)


class VolumeBackupManager(base.ManagerWithFind):
    """Manage :class:`VolumeBackup` resources."""
    resource_class = VolumeBackup

    def create(self, volume_id, container=None,
               name=None, description=None):
        """Creates a volume backup.

        :param volume_id: The ID of the volume to backup.
        :param container: The name of the backup service container.
        :param name: The name of the backup.
        :param description: The description of the backup.
        :rtype: :class:`VolumeBackup`
        """
        body = {'backup': {'volume_id': volume_id,
                           'container': container,
                           'name': name,
                           'description': description}}
        return self._create('/backups', body, 'backup')

    def get(self, backup_id):
        """Show volume backup details.

        :param backup_id: The ID of the backup to display.
        :rtype: :class:`VolumeBackup`
        """
        return self._get("/backups/%s" % backup_id, "backup")

    def list(self, detailed=True):
        """Get a list of all volume backups.

        :rtype: list of :class:`VolumeBackup`
        """
        if detailed is True:
            return self._list("/backups/detail", "backups")
        else:
            return self._list("/backups", "backups")

    def delete(self, backup):
        """Delete a volume backup.

        :param backup: The :class:`VolumeBackup` to delete.
        """
        self._delete("/backups/%s" % base.getid(backup))

    def export_record(self, backup_id):
        """Export volume backup metadata record.

        :param backup_id: The ID of the backup to export.
        :rtype: :class:`VolumeBackup`
        """
        resp, body = \
            self.api.client.get("/backups/%s/export_record" % backup_id)
        return body['backup-record']

    def import_record(self, backup_service, backup_url):
        """Export volume backup metadata record.

        :param backup_service: Backup service to use for importing the backup
        :param backup_urlBackup URL for importing the backup metadata
        :rtype: :class:`VolumeBackup`
        """
        body = {'backup-record': {'backup_service': backup_service,
                                  'backup_url': backup_url}}
        self.run_hooks('modify_body_for_update', body, 'backup-record')
        resp, body = self.api.client.post("/backups/import_record", body=body)
        return body['backup']
