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


class Database(base.Resource):
    """Wikipedia definition for database.

    "A database is a system intended to organize, store, and retrieve large
    amounts of data easily."
    """
    def __repr__(self):
        return "<Database: %s>" % self.name


class Databases(base.ManagerWithFind):
    """Manage :class:`Databases` resources."""
    resource_class = Database

    def create(self, instance, databases):
        """Create new databases within the specified instance."""
        body = {"databases": databases}
        url = "/instances/%s/databases" % base.getid(instance)
        resp, body = self.api.client.post(url, body=body)
        common.check_for_exceptions(resp, body, url)

    def delete(self, instance, dbname):
        """Delete an existing database in the specified instance."""
        url = "/instances/%s/databases/%s" % (base.getid(instance), dbname)
        resp, body = self.api.client.delete(url)
        common.check_for_exceptions(resp, body, url)

    def list(self, instance, limit=None, marker=None):
        """Get a list of all Databases from the instance.

        :rtype: list of :class:`Database`.
        """
        url = "/instances/%s/databases" % base.getid(instance)
        return self._paginated(url, "databases", limit, marker)

#    def get(self, instance, database):
#        """
#        Get a specific instances.
#
#        :param flavor: The ID of the :class:`Database` to get.
#        :rtype: :class:`Database`
#        """
#        assert isinstance(instance, Instance)
#        assert isinstance(database, (Database, int))
#        instance_id = base.getid(instance)
#        db_id = base.getid(database)
#        url = "/instances/%s/databases/%s" % (instance_id, db_id)
#        return self._get(url, "database")
