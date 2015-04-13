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

from novaclient import extension
from novaclient.tests.unit import utils
from novaclient.tests.unit.v2.contrib import fakes
from novaclient.v2.contrib import assisted_volume_snapshots as assisted_snaps


extensions = [
    extension.Extension(assisted_snaps.__name__.split(".")[-1],
                        assisted_snaps),
]
cs = fakes.FakeClient(extensions=extensions)


class AssistedVolumeSnapshotsTestCase(utils.TestCase):

    def test_create_snap(self):
        cs.assisted_volume_snapshots.create('1', {})
        cs.assert_called('POST', '/os-assisted-volume-snapshots')

    def test_delete_snap(self):
        cs.assisted_volume_snapshots.delete('x', {})
        cs.assert_called(
            'DELETE',
            '/os-assisted-volume-snapshots/x?delete_info={}')
