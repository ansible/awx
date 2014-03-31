# Copyright 2012 OpenStack Foundation
# Copyright 2013 IBM Corp.
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
from novaclient.v1_1 import flavor_access


class FlavorAccess(flavor_access.FlavorAccess):
    pass


class FlavorAccessManager(flavor_access.FlavorAccessManager):
    """
    Manage :class:`FlavorAccess` resources.
    """
    resource_class = FlavorAccess

    def _list_by_flavor(self, flavor):
        return self._list('/flavors/%s/flavor-access' % base.getid(flavor),
                          'flavor_access')

    def add_tenant_access(self, flavor, tenant):
        """Add a tenant to the given flavor access list."""
        info = {'tenant_id': tenant}
        return self._action('add_tenant_access', flavor, info)

    def remove_tenant_access(self, flavor, tenant):
        """Remove a tenant from the given flavor access list."""
        info = {'tenant_id': tenant}
        return self._action('remove_tenant_access', flavor, info)
