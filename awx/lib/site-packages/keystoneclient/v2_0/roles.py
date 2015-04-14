# Copyright 2011 OpenStack Foundation
# Copyright 2011 Nebula, Inc.
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

from keystoneclient import base


class Role(base.Resource):
    """Represents a Keystone role."""
    def __repr__(self):
        return "<Role %s>" % self._info

    def delete(self):
        return self.manager.delete(self)


class RoleManager(base.ManagerWithFind):
    """Manager class for manipulating Keystone roles."""
    resource_class = Role

    def get(self, role):
        return self._get("/OS-KSADM/roles/%s" % base.getid(role), "role")

    def create(self, name):
        """Create a role."""
        params = {"role": {"name": name}}
        return self._create('/OS-KSADM/roles', params, "role")

    def delete(self, role):
        """Delete a role."""
        return self._delete("/OS-KSADM/roles/%s" % base.getid(role))

    def list(self):
        """List all available roles."""
        return self._list("/OS-KSADM/roles", "roles")

    def roles_for_user(self, user, tenant=None):
        user_id = base.getid(user)
        if tenant:
            tenant_id = base.getid(tenant)
            route = "/tenants/%s/users/%s/roles"
            return self._list(route % (tenant_id, user_id), "roles")
        else:
            return self._list("/users/%s/roles" % user_id, "roles")

    def add_user_role(self, user, role, tenant=None):
        """Adds a role to a user.

        If tenant is specified, the role is added just for that tenant,
        otherwise the role is added globally.
        """
        user_id = base.getid(user)
        role_id = base.getid(role)
        if tenant:
            route = "/tenants/%s/users/%s/roles/OS-KSADM/%s"
            params = (base.getid(tenant), user_id, role_id)
            return self._update(route % params, None, "role")
        else:
            route = "/users/%s/roles/OS-KSADM/%s"
            return self._update(route % (user_id, role_id), None, "roles")

    def remove_user_role(self, user, role, tenant=None):
        """Removes a role from a user.

        If tenant is specified, the role is removed just for that tenant,
        otherwise the role is removed from the user's global roles.
        """
        user_id = base.getid(user)
        role_id = base.getid(role)
        if tenant:
            route = "/tenants/%s/users/%s/roles/OS-KSADM/%s"
            params = (base.getid(tenant), user_id, role_id)
            return self._delete(route % params)
        else:
            route = "/users/%s/roles/OS-KSADM/%s"
            return self._delete(route % (user_id, role_id))
