# Copyright 2011 OpenStack Foundation
# Copyright 2013 Rackspace Hosting
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
from troveclient.v1 import clusters
from troveclient.v1 import configurations
from troveclient.v1 import flavors
from troveclient.v1 import instances


class RootHistory(base.Resource):
    def __repr__(self):
        return ("<Root History: Instance %s enabled at %s by %s>"
                % (self.id, self.created, self.user))


class Management(base.ManagerWithFind):
    """Manage :class:`Instances` resources."""
    resource_class = instances.Instance

    # Appease the abc gods
    def list(self):
        pass

    def show(self, instance):
        """Get details of one instance.

        :rtype: :class:`Instance`.
        """

        return self._get("/mgmt/instances/%s" % base.getid(instance),
                         'instance')

    def index(self, deleted=None, limit=None, marker=None):
        """Show an overview of all local instances.

        Optionally, filter by deleted status.

        :rtype: list of :class:`Instance`.
        """
        form = ''
        if deleted is not None:
            if deleted:
                form = "?deleted=true"
            else:
                form = "?deleted=false"

        url = "/mgmt/instances%s" % form
        return self._paginated(url, "instances", limit, marker)

    def root_enabled_history(self, instance):
        """Get root access history of one instance."""
        url = "/mgmt/instances/%s/root" % base.getid(instance)
        resp, body = self.api.client.get(url)
        if not body:
            raise Exception("Call to " + url + " did not return a body.")
        return RootHistory(self, body['root_history'])

    def _action(self, instance_id, body):
        """Perform a server "action" -- reboot/rebuild/resize/etc."""
        url = "/mgmt/instances/%s/action" % instance_id
        resp, body = self.api.client.post(url, body=body)
        common.check_for_exceptions(resp, body, url)

    def stop(self, instance_id):
        body = {'stop': {}}
        self._action(instance_id, body)

    def reboot(self, instance_id):
        """Reboot the underlying OS.

        :param instance_id: The :class:`Instance` (or its ID) to share onto.
        """
        body = {'reboot': {}}
        self._action(instance_id, body)

    def migrate(self, instance_id, host=None):
        """Migrate the instance.

        :param instance_id: The :class:`Instance` (or its ID) to share onto.
        """
        if host:
            body = {'migrate': {'host': host}}
        else:
            body = {'migrate': {}}
        self._action(instance_id, body)

    def update(self, instance_id):
        """Update the guest agent via apt-get."""
        body = {'update': {}}
        self._action(instance_id, body)

    def reset_task_status(self, instance_id):
        """Set the task status to NONE."""
        body = {'reset-task-status': {}}
        self._action(instance_id, body)


class MgmtClusters(base.ManagerWithFind):
    """Manage :class:`Cluster` resources."""
    resource_class = clusters.Cluster

    # Appease the abc gods
    def list(self):
        pass

    def show(self, cluster):
        """Get details of one cluster."""
        return self._get("/mgmt/clusters/%s" % base.getid(cluster), 'cluster')

    def index(self, deleted=None, limit=None, marker=None):
        """Show an overview of all local clusters.

        Optionally, filter by deleted status.

        :rtype: list of :class:`Cluster`.
        """
        form = ''
        if deleted is not None:
            if deleted:
                form = "?deleted=true"
            else:
                form = "?deleted=false"

        url = "/mgmt/clusters%s" % form
        return self._paginated(url, "clusters", limit, marker)

    def _action(self, cluster_id, body):
        """Perform a cluster action, e.g. reset-task."""
        url = "/mgmt/clusters/%s/action" % cluster_id
        resp, body = self.api.client.post(url, body=body)
        common.check_for_exceptions(resp, body, url)

    def reset_task(self, cluster_id):
        """Reset the current cluster task to NONE."""
        body = {'reset-task': {}}
        self._action(cluster_id, body)


class MgmtFlavors(base.ManagerWithFind):
    """Manage :class:`Flavor` resources."""
    resource_class = flavors.Flavor

    def __repr__(self):
        return "<Flavors Manager at %s>" % id(self)

    # Appease the abc gods
    def list(self):
        pass

    def create(self, name, ram, disk, vcpus,
               flavorid="auto", ephemeral=None, swap=None, rxtx_factor=None,
               service_type=None):
        """Create a new flavor."""
        body = {"flavor": {
            "flavor_id": flavorid,
            "name": name,
            "ram": ram,
            "disk": disk,
            "vcpu": vcpus,
            "ephemeral": 0,
            "swap": 0,
            "rxtx_factor": "1.0",
            "is_public": "True"
        }}
        if ephemeral:
            body["flavor"]["ephemeral"] = ephemeral
        if swap:
            body["flavor"]["swap"] = swap
        if rxtx_factor:
            body["flavor"]["rxtx_factor"] = rxtx_factor
        if service_type:
            body["flavor"]["service_type"] = service_type

        return self._create("/mgmt/flavors", body, "flavor")


class MgmtConfigurationParameters(configurations.ConfigurationParameters):
    def create(self, version, name, restart_required, data_type,
               max_size=None, min_size=None):
        """Mgmt call to create a new configuration parameter."""
        body = {
            "configuration-parameter": {
                "name": name,
                "restart_required": int(restart_required),
                "data_type": data_type,
            }
        }
        if max_size is not None:
            body["configuration-parameter"]["max_size"] = max_size
        if min_size is not None:
            body["configuration-parameter"]["min_size"] = min_size

        url = "/mgmt/datastores/versions/%s/parameters" % version
        resp, body = self.api.client.post(url, body=body)
        common.check_for_exceptions(resp, body, url)

    def list_all_parameter_by_version(self, version):
        """List all configuration parameters deleted or not."""
        return self._list("/mgmt/datastores/versions/%s/parameters" %
                          version, "configuration-parameters")

    def get_any_parameter_by_version(self, version, key):
        """Get any configuration parameter deleted or not."""
        return self._get("/mgmt/datastores/versions/%s/parameters/%s" %
                         (version, key))

    def modify(self, version, name, restart_required, data_type,
               max_size=None, min_size=None):
        """Mgmt call to modify an existing configuration parameter."""
        body = {
            "configuration-parameter": {
                "name": name,
                "restart_required": int(restart_required),
                "data_type": data_type,
            }
        }
        if max_size is not None:
            body["configuration-parameter"]["max_size"] = max_size
        if min_size is not None:
            body["configuration-parameter"]["min_size"] = min_size
        output = {
            'version': version,
            'parameter_name': name
        }
        url = ("/mgmt/datastores/versions/%(version)s/"
               "parameters/%(parameter_name)s" % output)
        resp, body = self.api.client.put(url, body=body)
        common.check_for_exceptions(resp, body, url)

    def delete(self, version, name):
        """Mgmt call to delete a configuration parameter."""
        output = {
            'version_id': version,
            'parameter_name': name
        }
        url = ("/mgmt/datastores/versions/%(version_id)s/"
               "parameters/%(parameter_name)s" % output)
        resp, body = self.api.client.delete(url)
        common.check_for_exceptions(resp, body, url)
