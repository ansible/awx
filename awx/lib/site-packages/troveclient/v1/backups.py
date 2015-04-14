# Copyright 2011 OpenStack Foundation
# Copyright 2013 Rackspace Hosting
# Copyright 2013 Hewlett-Packard Development Company, L.P.
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


class Backup(base.Resource):
    """Backup is a resource used to hold backup information."""
    def __repr__(self):
        return "<Backup: %s>" % self.name


class Backups(base.ManagerWithFind):
    """Manage :class:`Backups` information."""

    resource_class = Backup

    def get(self, backup):
        """Get a specific backup.

        :rtype: :class:`Backups`
        """
        return self._get("/backups/%s" % base.getid(backup),
                         "backup")

    def list(self, limit=None, marker=None, datastore=None):
        """Get a list of all backups.

        :rtype: list of :class:`Backups`.
        """
        query_strings = {}
        if datastore:
            query_strings = {'datastore': datastore}

        return self._paginated("/backups", "backups", limit, marker,
                               query_strings)

    def create(self, name, instance=None, description=None, parent_id=None,
               backup=None,):
        """Create a new backup from the given instance."""
        body = {
            "backup": {
                "name": name
            }
        }

        if instance:
            body['backup']['instance'] = base.getid(instance)
        if backup:
            body["backup"]['backup'] = backup
        if description:
            body['backup']['description'] = description
        if parent_id:
            body['backup']['parent_id'] = parent_id
        return self._create("/backups", body, "backup")

    def delete(self, backup_id):
        """Delete the specified backup.

        :param backup_id: The backup id to delete
        """
        url = "/backups/%s" % backup_id
        resp, body = self.api.client.delete(url)
        common.check_for_exceptions(resp, body, url)
