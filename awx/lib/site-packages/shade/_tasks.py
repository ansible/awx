# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.

from shade import task_manager


class UserList(task_manager.Task):
    def main(self, client):
        return client.keystone_client.users.list()


class UserCreate(task_manager.Task):
    def main(self, client):
        return client.keystone_client.users.create(**self.args)


class FlavorList(task_manager.Task):
    def main(self, client):
        return client.nova_client.flavors.list()


class ServerList(task_manager.Task):
    def main(self, client):
        return client.nova_client.servers.list(**self.args)


class ServerGet(task_manager.Task):
    def main(self, client):
        return client.nova_client.servers.get(**self.args)


class ServerCreate(task_manager.Task):
    def main(self, client):
        return client.nova_client.servers.create(**self.args)


class ServerDelete(task_manager.Task):
    def main(self, client):
        return client.nova_client.servers.delete(**self.args)


class ServerRebuild(task_manager.Task):
    def main(self, client):
        return client.nova_client.servers.rebuild(**self.args)


class KeypairList(task_manager.Task):
    def main(self, client):
        return client.nova_client.keypairs.list()


class KeypairCreate(task_manager.Task):
    def main(self, client):
        return client.nova_client.keypairs.create(**self.args)


class KeypairDelete(task_manager.Task):
    def main(self, client):
        return client.nova_client.keypairs.delete(**self.args)


class NovaUrlGet(task_manager.Task):
    def main(self, client):
        return client.nova_client.client.get(**self.args)


class NetworkList(task_manager.Task):
    def main(self, client):
        return client.neutron_client.list_networks()


class NetworkCreate(task_manager.Task):
    def main(self, client):
        return client.neutron_client.create_network(**self.args)


class NetworkDelete(task_manager.Task):
    def main(self, client):
        return client.neutron_client.delete_network(**self.args)


class RouterList(task_manager.Task):
    def main(self, client):
        return client.neutron_client.list_routers()


class RouterCreate(task_manager.Task):
    def main(self, client):
        return client.neutron_client.create_router(**self.args)


class RouterUpdate(task_manager.Task):
    def main(self, client):
        return client.neutron_client.update_router(**self.args)


class RouterDelete(task_manager.Task):
    def main(self, client):
        client.neutron_client.delete_router(**self.args)


class GlanceImageList(task_manager.Task):
    def main(self, client):
        return client.glance_client.images.list()


class NovaImageList(task_manager.Task):
    def main(self, client):
        return client.nova_client.images.list()


class ImageSnapshotCreate(task_manager.Task):
    def main(self, client):
        return client.nova_client.servers.create_image(**self.args)


class ImageCreate(task_manager.Task):
    def main(self, client):
        return client.glance_client.images.create(**self.args)


class ImageDelete(task_manager.Task):
    def main(self, client):
        return client.glance_client.images.delete(**self.args)


class ImageTaskCreate(task_manager.Task):
    def main(self, client):
        return client.glance_client.tasks.create(**self.args)


class ImageTaskGet(task_manager.Task):
    def main(self, client):
        return client.glance_client.tasks.get(**self.args)


class ImageUpdate(task_manager.Task):
    def main(self, client):
        client.glance_client.images.update(**self.args)


class VolumeCreate(task_manager.Task):
    def main(self, client):
        return client.cinder_client.volumes.create(**self.args)


class VolumeDelete(task_manager.Task):
    def main(self, client):
        return client.cinder_client.volumes.delete(**self.args)


class VolumeList(task_manager.Task):
    def main(self, client):
        return client.cinder_client.volumes.list()


class VolumeDetach(task_manager.Task):
    def main(self, client):
        client.nova_client.volumes.delete_server_volume(**self.args)


class VolumeAttach(task_manager.Task):
    def main(self, client):
        client.nova_client.volumes.create_server_volume(**self.args)


class SecurityGroupList(task_manager.Task):
    def main(self, client):
        return client.nova_client.security_groups.list()


# TODO: Do this with neutron instead of nova if possible
class FloatingIPList(task_manager.Task):
    def main(self, client):
        return client.nova_client.floating_ips.list()


class FloatingIPCreate(task_manager.Task):
    def main(self, client):
        return client.nova_client.floating_ips.create(**self.args)


class FloatingIPDelete(task_manager.Task):
    def main(self, client):
        return client.nova_client.floating_ips.delete(**self.args)


class FloatingIPAttach(task_manager.Task):
    def main(self, client):
        return client.nova_client.servers.add_floating_ip(**self.args)


class ContainerGet(task_manager.Task):
    def main(self, client):
        return client.swift_client.head_container(**self.args)


class ContainerCreate(task_manager.Task):
    def main(self, client):
        client.swift_client.put_container(**self.args)


class ContainerDelete(task_manager.Task):
    def main(self, client):
        client.swift_client.delete_container(**self.args)


class ContainerUpdate(task_manager.Task):
    def main(self, client):
        client.swift_client.post_container(**self.args)


class ObjectCreate(task_manager.Task):
    def main(self, client):
        client.swift_client.put_object(**self.args)


class ObjectUpdate(task_manager.Task):
    def main(self, client):
        client.swift_client.post_object(**self.args)


class ObjectMetadata(task_manager.Task):
    def main(self, client):
        return client.swift_client.head_object(**self.args)
