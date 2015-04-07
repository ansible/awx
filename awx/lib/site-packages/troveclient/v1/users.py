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
from troveclient.v1 import databases


class User(base.Resource):
    """A database user."""
    def __repr__(self):
        return "<User: %s>" % self.name


class Users(base.ManagerWithFind):
    """Manage :class:`Users` resources."""
    resource_class = User

    def create(self, instance, users):
        """Create users with permissions to the specified databases."""
        body = {"users": users}
        url = "/instances/%s/users" % base.getid(instance)
        resp, body = self.api.client.post(url, body=body)
        common.check_for_exceptions(resp, body, url)

    def delete(self, instance, username, hostname=None):
        """Delete an existing user in the specified instance."""
        user = common.quote_user_host(username, hostname)
        url = "/instances/%s/users/%s" % (base.getid(instance), user)
        resp, body = self.api.client.delete(url)
        common.check_for_exceptions(resp, body, url)

    def list(self, instance, limit=None, marker=None):
        """Get a list of all Users from the instance's Database.

        :rtype: list of :class:`User`.
        """
        url = "/instances/%s/users" % base.getid(instance)
        return self._paginated(url, "users", limit, marker)

    def get(self, instance, username, hostname=None):
        """Get a single User from the instance's Database.

        :rtype: :class:`User`.
        """
        user = common.quote_user_host(username, hostname)
        url = "/instances/%s/users/%s" % (base.getid(instance), user)
        return self._get(url, "user")

    def update_attributes(self, instance, username, newuserattr=None,
                          hostname=None):
        """Update attributes of a single User in an instance.

        :rtype: :class:`User`.
        """
        if not newuserattr:
            raise Exception("No updates specified for user %s" % username)
        instance_id = base.getid(instance)
        user = common.quote_user_host(username, hostname)
        user_dict = {}
        user_dict['user'] = newuserattr
        url = "/instances/%s/users/%s" % (instance_id, user)
        resp, body = self.api.client.put(url, body=user_dict)
        common.check_for_exceptions(resp, body, url)

    def list_access(self, instance, username, hostname=None):
        """Show all databases the given user has access to."""
        instance_id = base.getid(instance)
        user = common.quote_user_host(username, hostname)
        url = "/instances/%(instance_id)s/users/%(user)s/databases"
        local_vars = locals()
        resp, body = self.api.client.get(url % local_vars)
        common.check_for_exceptions(resp, body, url)
        if not body:
            raise Exception("Call to %s did not return to a body" % url)
        return [databases.Database(self, db) for db in body['databases']]

    def grant(self, instance, username, databases, hostname=None):
        """Allow an existing user permissions to access a database."""
        instance_id = base.getid(instance)
        user = common.quote_user_host(username, hostname)
        url = "/instances/%(instance_id)s/users/%(user)s/databases"
        dbs = {'databases': [{'name': db} for db in databases]}
        local_vars = locals()
        resp, body = self.api.client.put(url % local_vars, body=dbs)
        common.check_for_exceptions(resp, body, url)

    def revoke(self, instance, username, database, hostname=None):
        """Revoke from an existing user access permissions to a database."""
        instance_id = base.getid(instance)
        user = common.quote_user_host(username, hostname)
        url = ("/instances/%(instance_id)s/users/%(user)s/"
               "databases/%(database)s")
        local_vars = locals()
        resp, body = self.api.client.delete(url % local_vars)
        common.check_for_exceptions(resp, body, url)

    def change_passwords(self, instance, users):
        """Change the password for one or more users."""
        instance_id = base.getid(instance)
        user_dict = {"users": users}
        url = "/instances/%s/users" % instance_id
        resp, body = self.api.client.put(url, body=user_dict)
        common.check_for_exceptions(resp, body, url)
