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
Volume interface
"""

from novaclient import base


class VolumeManager(base.Manager):
    """
    Manage :class:`Volume` resources.
    """

    def attach_server_volume(self, server, volume_id, device):
        """
        Attach a volume identified by the volume ID to the given server ID

        :param server: The server (or it's ID)
        :param volume_id: The ID of the volume to attach.
        :param device: The device name
        :rtype: :class:`Volume`
        """
        body = {'volume_id': volume_id, 'device': device}
        return self._action('attach', server, body)

    def update_server_volume(self, server, old_volume_id, new_volume_id):
        """
        Update the volume identified by the attachment ID, that is attached to
        the given server ID

        :param server_id: The server (or it's ID)
        :param old_volume_id: The ID of the attachment
        :param new_volume_id: The ID of the new volume to attach
        :rtype: :class:`Volume`
        """
        body = {'new_volume_id': new_volume_id, 'old_volume_id': old_volume_id}
        return self._action('swap_volume_attachment', server, body)

    def delete_server_volume(self, server, volume_id):
        """
        Detach a volume identified by the attachment ID from the given server

        :param server_id: The ID of the server
        :param volume_id: The ID of the attachment
        """
        return self._action('detach', server, {'volume_id': volume_id})

    def _action(self, action, server, info=None, **kwargs):
        """
        Perform a server "action" -- reboot/rebuild/resize/etc.
        """
        body = {action: info}
        self.run_hooks('modify_body_for_action', body, **kwargs)
        url = '/servers/%s/action' % base.getid(server)
        return self.api.client.post(url, body=body)
