# Copyright (c) 2014 eBay Software Foundation
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


class Cluster(base.Resource):
    """A Cluster is an opaque cluster used to store Database clusters."""
    def __repr__(self):
        return "<Cluster: %s>" % self.name

    def delete(self):
        """Delete the cluster."""
        self.manager.delete(self)


class Clusters(base.ManagerWithFind):
    """Manage :class:`Cluster` resources."""
    resource_class = Cluster

    def create(self, name, datastore, datastore_version, instances=None):
        """Create (boot) a new cluster."""
        body = {"cluster": {
            "name": name
        }}
        datastore_obj = {
            "type": datastore,
            "version": datastore_version
        }
        body["cluster"]["datastore"] = datastore_obj
        if instances:
            body["cluster"]["instances"] = instances

        return self._create("/clusters", body, "cluster")

    def list(self, limit=None, marker=None):
        """Get a list of all clusters.

        :rtype: list of :class:`Cluster`.
        """
        return self._paginated("/clusters", "clusters", limit, marker)

    def get(self, cluster):
        """Get a specific cluster.

        :rtype: :class:`Cluster`
        """
        return self._get("/clusters/%s" % base.getid(cluster),
                         "cluster")

    def delete(self, cluster):
        """Delete the specified cluster.

        :param cluster: The cluster to delete
        """
        url = "/clusters/%s" % base.getid(cluster)
        resp, body = self.api.client.delete(url)
        common.check_for_exceptions(resp, body, url)

    def add_shard(self, cluster):
        """Adds a shard to the specified cluster.

        :param cluster: The cluster to add a shard to
        """
        url = "/clusters/%s" % base.getid(cluster)
        body = {"add_shard": {}}
        resp, body = self.api.client.post(url, body=body)
        common.check_for_exceptions(resp, body, url)
        if body:
            return self.resource_class(self, body, loaded=True)
        return body


class ClusterStatus(object):

    ACTIVE = "ACTIVE"
    BUILD = "BUILD"
    FAILED = "FAILED"
    SHUTDOWN = "SHUTDOWN"
