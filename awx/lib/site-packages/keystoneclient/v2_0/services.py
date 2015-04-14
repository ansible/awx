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


class Service(base.Resource):
    """Represents a Keystone service."""
    def __repr__(self):
        return "<Service %s>" % self._info


class ServiceManager(base.ManagerWithFind):
    """Manager class for manipulating Keystone services."""
    resource_class = Service

    def list(self):
        """List available services."""
        return self._list("/OS-KSADM/services", "OS-KSADM:services")

    def get(self, id):
        """Retrieve a service by id."""
        return self._get("/OS-KSADM/services/%s" % id, "OS-KSADM:service")

    def create(self, name, service_type, description):
        """Create a new service."""
        body = {"OS-KSADM:service": {'name': name,
                                     'type': service_type,
                                     'description': description}}
        return self._create("/OS-KSADM/services", body, "OS-KSADM:service")

    def delete(self, id):
        """Delete a service."""
        return self._delete("/OS-KSADM/services/%s" % id)
