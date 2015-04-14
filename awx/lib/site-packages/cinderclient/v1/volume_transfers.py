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
Volume transfer interface (1.1 extension).
"""

from cinderclient import base


class VolumeTransfer(base.Resource):
    """Transfer a volume from one tenant to another"""
    def __repr__(self):
        return "<VolumeTransfer: %s>" % self.id

    def delete(self):
        """Delete this volume transfer."""
        return self.manager.delete(self)


class VolumeTransferManager(base.ManagerWithFind):
    """Manage :class:`VolumeTransfer` resources."""
    resource_class = VolumeTransfer

    def create(self, volume_id, name=None):
        """Creates a volume transfer.

        :param volume_id: The ID of the volume to transfer.
        :param name: The name of the transfer.
        :rtype: :class:`VolumeTransfer`
        """
        body = {'transfer': {'volume_id': volume_id,
                             'name': name}}
        return self._create('/os-volume-transfer', body, 'transfer')

    def accept(self, transfer_id, auth_key):
        """Accept a volume transfer.

        :param transfer_id: The ID of the transfer to accept.
        :param auth_key: The auth_key of the transfer.
        :rtype: :class:`VolumeTransfer`
        """
        body = {'accept': {'auth_key': auth_key}}
        return self._create('/os-volume-transfer/%s/accept' % transfer_id,
                            body, 'transfer')

    def get(self, transfer_id):
        """Show details of a volume transfer.

        :param transfer_id: The ID of the volume transfer to display.
        :rtype: :class:`VolumeTransfer`
        """
        return self._get("/os-volume-transfer/%s" % transfer_id, "transfer")

    def list(self, detailed=True, search_opts=None):
        """Get a list of all volume transfer.

        :rtype: list of :class:`VolumeTransfer`
        """
        if detailed is True:
            return self._list("/os-volume-transfer/detail", "transfers")
        else:
            return self._list("/os-volume-transfer", "transfers")

    def delete(self, transfer_id):
        """Delete a volume transfer.

        :param transfer_id: The :class:`VolumeTransfer` to delete.
        """
        self._delete("/os-volume-transfer/%s" % base.getid(transfer_id))
