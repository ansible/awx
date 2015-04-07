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

import six
from six.moves import urllib

from keystoneclient import auth
from keystoneclient import base
from keystoneclient import exceptions


class Tenant(base.Resource):
    """Represents a Keystone tenant

    Attributes:
        * id: a uuid that identifies the tenant
        * name: tenant name
        * description: tenant description
        * enabled: boolean to indicate if tenant is enabled

    """
    def __repr__(self):
        return "<Tenant %s>" % self._info

    def delete(self):
        return self.manager.delete(self)

    def update(self, name=None, description=None, enabled=None):
        # Preserve the existing settings; keystone legacy resets these?
        new_name = name if name else self.name
        if description is not None:
            new_description = description
        else:
            new_description = self.description
        new_enabled = enabled if enabled is not None else self.enabled

        try:
            retval = self.manager.update(self.id, tenant_name=new_name,
                                         description=new_description,
                                         enabled=new_enabled)
            self = retval
        except Exception:
            retval = None
        return retval

    def add_user(self, user, role):
        return self.manager.role_manager.add_user_role(base.getid(user),
                                                       base.getid(role),
                                                       self.id)

    def remove_user(self, user, role):
        return self.manager.role_manager.remove_user_role(base.getid(user),
                                                          base.getid(role),
                                                          self.id)

    def list_users(self):
        return self.manager.list_users(self.id)


class TenantManager(base.ManagerWithFind):
    """Manager class for manipulating Keystone tenants."""
    resource_class = Tenant

    def __init__(self, client, role_manager, user_manager):
        super(TenantManager, self).__init__(client)
        self.role_manager = role_manager
        self.user_manager = user_manager

    def get(self, tenant_id):
        return self._get("/tenants/%s" % tenant_id, "tenant")

    def create(self, tenant_name, description=None, enabled=True, **kwargs):
        """Create a new tenant."""
        params = {"tenant": {"name": tenant_name,
                             "description": description,
                             "enabled": enabled}}

        # Allow Extras Passthru and ensure we don't clobber primary arguments.
        for k, v in six.iteritems(kwargs):
            if k not in params['tenant']:
                params['tenant'][k] = v

        return self._create('/tenants', params, "tenant")

    def list(self, limit=None, marker=None):
        """Get a list of tenants.

        :param integer limit: maximum number to return. (optional)
        :param string marker: use when specifying a limit and making
                              multiple calls for querying. (optional)

        :rtype: list of :class:`Tenant`

        """

        params = {}
        if limit:
            params['limit'] = limit
        if marker:
            params['marker'] = marker

        query = ""
        if params:
            query = "?" + urllib.parse.urlencode(params)

        # NOTE(jamielennox): try doing a regular admin query first. If there is
        # no endpoint that can satisfy the request (eg an unscoped token) then
        # issue it against the auth_url.
        try:
            tenant_list = self._list('/tenants%s' % query, 'tenants')
        except exceptions.EndpointNotFound:
            endpoint_filter = {'interface': auth.AUTH_INTERFACE}
            tenant_list = self._list('/tenants%s' % query, 'tenants',
                                     endpoint_filter=endpoint_filter)

        return tenant_list

    def update(self, tenant_id, tenant_name=None, description=None,
               enabled=None, **kwargs):
        """Update a tenant with a new name and description."""
        body = {"tenant": {'id': tenant_id}}
        if tenant_name is not None:
            body['tenant']['name'] = tenant_name
        if enabled is not None:
            body['tenant']['enabled'] = enabled
        if description is not None:
            body['tenant']['description'] = description

        # Allow Extras Passthru and ensure we don't clobber primary arguments.
        for k, v in six.iteritems(kwargs):
            if k not in body['tenant']:
                body['tenant'][k] = v

        # Keystone's API uses a POST rather than a PUT here.
        return self._create("/tenants/%s" % tenant_id, body, "tenant")

    def delete(self, tenant):
        """Delete a tenant."""
        return self._delete("/tenants/%s" % (base.getid(tenant)))

    def list_users(self, tenant):
        """List users for a tenant."""
        return self.user_manager.list(base.getid(tenant))

    def add_user(self, tenant, user, role):
        """Add a user to a tenant with the given role."""
        return self.role_manager.add_user_role(base.getid(user),
                                               base.getid(role),
                                               base.getid(tenant))

    def remove_user(self, tenant, user, role):
        """Remove the specified role from the user on the tenant."""
        return self.role_manager.remove_user_role(base.getid(user),
                                                  base.getid(role),
                                                  base.getid(tenant))
