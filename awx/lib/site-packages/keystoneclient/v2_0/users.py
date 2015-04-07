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

from six.moves import urllib

from keystoneclient import base


class User(base.Resource):
    """Represents a Keystone user."""
    def __repr__(self):
        return "<User %s>" % self._info

    def delete(self):
        return self.manager.delete(self)

    def list_roles(self, tenant=None):
        return self.manager.list_roles(self.id, base.getid(tenant))


class UserManager(base.ManagerWithFind):
    """Manager class for manipulating Keystone users."""
    resource_class = User

    def __init__(self, client, role_manager):
        super(UserManager, self).__init__(client)
        self.role_manager = role_manager

    def get(self, user):
        return self._get("/users/%s" % base.getid(user), "user")

    def update(self, user, **kwargs):
        """Update user data.

        Supported arguments include ``name``, ``email``, and ``enabled``.
        """
        # FIXME(gabriel): "tenantId" seems to be accepted by the API but
        #                 fails to actually update the default tenant.
        params = {"user": kwargs}
        params['user']['id'] = base.getid(user)
        url = "/users/%s" % base.getid(user)
        return self._update(url, params, "user")

    def update_enabled(self, user, enabled):
        """Update enabled-ness."""
        params = {"user": {"id": base.getid(user),
                           "enabled": enabled}}

        self._update("/users/%s/OS-KSADM/enabled" % base.getid(user), params,
                     "user")

    def update_password(self, user, password):
        """Update password."""
        params = {"user": {"id": base.getid(user),
                           "password": password}}

        return self._update("/users/%s/OS-KSADM/password" % base.getid(user),
                            params, "user", log=False)

    def update_own_password(self, origpasswd, passwd):
        """Update password."""
        params = {"user": {"password": passwd,
                           "original_password": origpasswd}}

        return self._update("/OS-KSCRUD/users/%s" % self.api.user_id, params,
                            response_key="access",
                            method="PATCH",
                            endpoint_filter={'interface': 'public'},
                            log=False)

    def update_tenant(self, user, tenant):
        """Update default tenant."""
        params = {"user": {"id": base.getid(user),
                           "tenantId": base.getid(tenant)}}

        # FIXME(ja): seems like a bad url - default tenant is an attribute
        #            not a subresource!???
        return self._update("/users/%s/OS-KSADM/tenant" % base.getid(user),
                            params, "user")

    def create(self, name, password=None, email=None,
               tenant_id=None, enabled=True):
        """Create a user."""
        params = {"user": {"name": name,
                           "password": password,
                           "tenantId": tenant_id,
                           "email": email,
                           "enabled": enabled}}
        return self._create('/users', params, "user", log=not bool(password))

    def delete(self, user):
        """Delete a user."""
        return self._delete("/users/%s" % base.getid(user))

    def list(self, tenant_id=None, limit=None, marker=None):
        """Get a list of users (optionally limited to a tenant).

        :rtype: list of :class:`User`
        """

        params = {}
        if limit:
            params['limit'] = int(limit)
        if marker:
            params['marker'] = marker

        query = ""
        if params:
            query = "?" + urllib.parse.urlencode(params)

        if not tenant_id:
            return self._list("/users%s" % query, "users")
        else:
            return self._list("/tenants/%s/users%s" % (tenant_id, query),
                              "users")

    def list_roles(self, user, tenant=None):
        return self.role_manager.roles_for_user(base.getid(user),
                                                base.getid(tenant))
