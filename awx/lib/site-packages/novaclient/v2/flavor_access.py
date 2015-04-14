# Copyright 2012 OpenStack Foundation
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

"""Flavor access interface."""

from novaclient import base
from novaclient.i18n import _


class FlavorAccess(base.Resource):
    def __repr__(self):
        return ("<FlavorAccess flavor id: %s, tenant id: %s>" %
                (self.flavor_id, self.tenant_id))


class FlavorAccessManager(base.ManagerWithFind):
    """
    Manage :class:`FlavorAccess` resources.
    """
    resource_class = FlavorAccess

    def list(self, **kwargs):
        if kwargs.get('flavor'):
            return self._list_by_flavor(kwargs['flavor'])
        elif kwargs.get('tenant'):
            return self._list_by_tenant(kwargs['tenant'])
        else:
            raise NotImplementedError(_('Unknown list options.'))

    def _list_by_flavor(self, flavor):
        return self._list('/flavors/%s/os-flavor-access' % base.getid(flavor),
                          'flavor_access')

    def _list_by_tenant(self, tenant):
        """Print flavor list shared with the given tenant."""
        # TODO(uni): need to figure out a proper URI for list_by_tenant
        # since current API already provided current tenant_id information
        raise NotImplementedError(_('Sorry, query by tenant not supported.'))

    def add_tenant_access(self, flavor, tenant):
        """Add a tenant to the given flavor access list."""
        info = {'tenant': tenant}
        return self._action('addTenantAccess', flavor, info)

    def remove_tenant_access(self, flavor, tenant):
        """Remove a tenant from the given flavor access list."""
        info = {'tenant': tenant}
        return self._action('removeTenantAccess', flavor, info)

    def _action(self, action, flavor, info, **kwargs):
        """Perform a flavor action."""
        body = {action: info}
        self.run_hooks('modify_body_for_action', body, **kwargs)
        url = '/flavors/%s/action' % base.getid(flavor)
        _resp, body = self.api.client.post(url, body=body)

        return [self.resource_class(self, res)
                for res in body['flavor_access']]
