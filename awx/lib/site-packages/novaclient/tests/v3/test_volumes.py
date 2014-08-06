# Copyright 2013 IBM Corp.
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

from novaclient.tests import utils
from novaclient.tests.v3 import fakes


class VolumesTest(utils.TestCase):
    def setUp(self):
        super(VolumesTest, self).setUp()
        self.cs = self._get_fake_client()

    def _get_fake_client(self):
        return fakes.FakeClient()

    def test_attach_server_volume(self):
        self.cs.volumes.attach_server_volume(
            server=1234,
            volume_id='15e59938-07d5-11e1-90e3-e3dffe0c5983',
            device='/dev/vdb'
        )
        self.cs.assert_called('POST', '/servers/1234/action')

    def test_attach_server_volume_disk_bus_device_type(self):
        volume_id = '15e59938-07d5-11e1-90e3-e3dffe0c5983'
        device = '/dev/vdb'
        disk_bus = 'ide'
        device_type = 'cdrom'
        self.cs.volumes.attach_server_volume(server=1234,
                                             volume_id=volume_id,
                                             device=device,
                                             disk_bus=disk_bus,
                                             device_type=device_type)
        body_params = {'volume_id': volume_id,
                       'device': device,
                       'disk_bus': disk_bus,
                       'device_type': device_type}
        body = {'attach': body_params}
        self.cs.assert_called('POST', '/servers/1234/action', body)

    def test_update_server_volume(self):
        vol_id = '15e59938-07d5-11e1-90e3-e3dffe0c5983'
        self.cs.volumes.update_server_volume(
            server=1234,
            old_volume_id='Work',
            new_volume_id=vol_id
        )
        self.cs.assert_called('POST', '/servers/1234/action')

    def test_delete_server_volume(self):
        self.cs.volumes.delete_server_volume(1234, 'Work')
        self.cs.assert_called('POST', '/servers/1234/action')
