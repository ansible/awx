# Copyright 2011 OpenStack Foundation
# Copyright 2013 Mirantis, Inc.
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


class Datastore(base.Resource):

    def __repr__(self):
        return "<Datastore: %s>" % self.name


class DatastoreVersion(base.Resource):

    def __repr__(self):
        return "<DatastoreVersion: %s>" % self.name

    def update(self, visibility=None):
        """Change something in a datastore version."""
        self.manager.update(self.datastore, self.id, visibility)


class DatastoreVersionMember(base.Resource):

    def __repr__(self):
        return "<DatastoreVersionMember: %s>" % self.id


class Datastores(base.ManagerWithFind):
    """Manage :class:`Datastore` resources."""
    resource_class = Datastore

    def __repr__(self):
        return "<Datastore Manager at %s>" % id(self)

    def list(self, limit=None, marker=None):
        """Get a list of all datastores.

        :rtype: list of :class:`Datastore`.
        """
        return self._paginated("/datastores", "datastores", limit, marker)

    def get(self, datastore):
        """Get a specific datastore.

        :rtype: :class:`Datastore`
        """
        return self._get("/datastores/%s" % base.getid(datastore),
                         "datastore")


class DatastoreVersions(base.ManagerWithFind):
    """Manage :class:`DatastoreVersion` resources."""
    resource_class = DatastoreVersion

    def __repr__(self):
        return "<DatastoreVersions Manager at %s>" % id(self)

    def list(self, datastore, limit=None, marker=None):
        """Get a list of all datastore versions.

        :rtype: list of :class:`DatastoreVersion`.
        """
        return self._paginated("/datastores/%s/versions" % datastore,
                               "versions", limit, marker)

    def get(self, datastore, datastore_version):
        """Get a specific datastore version.

        :rtype: :class:`DatastoreVersion`
        """
        return self._get("/datastores/%s/versions/%s" %
                         (datastore, base.getid(datastore_version)),
                         "version")

    def get_by_uuid(self, datastore_version):
        """Get a specific datastore version.

        :rtype: :class:`DatastoreVersion`
        """
        return self._get("/datastores/versions/%s" %
                         base.getid(datastore_version),
                         "version")

    def update(self, datastore, datastore_version, visibility):
        """Update a specific datastore version."""
        body = {
            "datastore_version": {
            }
        }
        if visibility is not None:
            body["datastore_version"]["visibility"] = visibility

        url = ("/mgmt/datastores/%s/versions/%s" %
               (datastore, datastore_version))
        return self._update(url, body=body)


class DatastoreVersionMembers(base.ManagerWithFind):
    """Manage :class:`DatastoreVersionMember` resources."""
    resource_class = DatastoreVersionMember

    def __repr__(self):
        return "<DatastoreVersionMembers Manager at %s>" % id(self)

    def add(self, datastore, datastore_version, tenant):
        """Add a member to a datastore version."""
        body = {"member": tenant}
        return self._create("/mgmt/datastores/%s/versions/%s/members" %
                            (datastore, datastore_version),
                            body, "datastore_version_member")

    def delete(self, datastore, datastore_version, member_id):
        """Delete a member from a datastore version."""
        return self._delete("/mgmt/datastores/%s/versions/%s/members/%s" %
                            (datastore, datastore_version, member_id))

    def list(self, datastore, datastore_version, limit=None, marker=None):
        """List members of datastore version."""
        return self._list("/mgmt/datastores/%s/versions/%s/members" %
                          (datastore, datastore_version),
                          "datastore_version_members", limit, marker)

    def get(self, datastore, datastore_version, member_id):
        """Get a datastore version member."""
        return self._get("/mgmt/datastores/%s/versions/%s/members/%s" %
                         (datastore, datastore_version, member_id),
                         "datastore_version_member")

    def get_by_tenant(self, datastore, tenant, limit=None, marker=None):
        """List members by tenant id."""
        return self._list("/mgmt/datastores/%s/versions/members/%s" %
                          (datastore, tenant), "datastore_version_members",
                          limit, marker)
