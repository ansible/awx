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

import os
import time
import uuid

import six.moves

from novaclient import client
from novaclient import exceptions
from novaclient.tests.functional import base


def wait_for_delete(test, name, thing, get_func):
    thing.delete()
    for x in six.moves.range(60):
        try:
            thing = get_func(thing.id)
        except exceptions.NotFound:
            break
        time.sleep(1)
    else:
        test.fail('%s %s still not deleted after 60s' % (name, thing.id))


class TestVolumesAPI(base.ClientTestBase):

    def setUp(self):
        super(TestVolumesAPI, self).setUp()
        user = os.environ['OS_USERNAME']
        passwd = os.environ['OS_PASSWORD']
        tenant = os.environ['OS_TENANT_NAME']
        auth_url = os.environ['OS_AUTH_URL']

        self.client = client.Client(2, user, passwd, tenant, auth_url=auth_url)

    def test_volumes_snapshots_types_create_get_list_delete(self):
        # Create a volume
        volume = self.client.volumes.create(1)

        # Make sure we can still list servers after using the volume endpoint
        self.client.servers.list()

        # This cleanup tests volume delete
        self.addCleanup(volume.delete)

        # Wait for the volume to become available
        for x in six.moves.range(60):
            volume = self.client.volumes.get(volume.id)
            if volume.status == 'available':
                break
            elif volume.status == 'error':
                self.fail('Volume %s is in error state' % volume.id)
            time.sleep(1)
        else:
            self.fail('Volume %s not available after 60s' % volume.id)

        # List all volumes
        self.client.volumes.list()

        # Create a volume snapshot
        snapshot = self.client.volume_snapshots.create(volume.id)

        # This cleanup tests volume snapshot delete. The volume
        # can't be deleted until the dependent snapshot is gone
        self.addCleanup(wait_for_delete, self, 'Snapshot', snapshot,
                        self.client.volume_snapshots.get)

        # Wait for the snapshot to become available
        for x in six.moves.range(60):
            snapshot = self.client.volume_snapshots.get(snapshot.id)
            if snapshot.status == 'available':
                break
            elif snapshot.status == 'error':
                self.fail('Snapshot %s is in error state' % snapshot.id)
            time.sleep(1)
        else:
            self.fail('Snapshot %s not available after 60s' % snapshot.id)

        # List snapshots
        self.client.volume_snapshots.list()

        # List servers again to make sure things are still good
        self.client.servers.list()

        # Create a volume type
        # TODO(melwitt): Use a better random name
        name = str(uuid.uuid4())
        volume_type = self.client.volume_types.create(name)

        # This cleanup tests volume type delete
        self.addCleanup(self.client.volume_types.delete, volume_type.id)

        # Get the volume type
        volume_type = self.client.volume_types.get(volume_type.id)

        # List all volume types
        self.client.volume_types.list()

        # One more servers list
        self.client.servers.list()
