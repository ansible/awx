# Copyright (c) 2013 OpenStack Foundation
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

"""
service interface
"""
from cinderclient import base


class Service(base.Resource):

    def __repr__(self):
        return "<Service: %s>" % self.service


class ServiceManager(base.ManagerWithFind):
    resource_class = Service

    def list(self, host=None, binary=None):
        """
        Describes service list for host.

        :param host: destination host name.
        :param binary: service binary.
        """
        url = "/os-services"
        filters = []
        if host:
            filters.append("host=%s" % host)
        if binary:
            filters.append("binary=%s" % binary)
        if filters:
            url = "%s?%s" % (url, "&".join(filters))
        return self._list(url, "services")

    def enable(self, host, binary):
        """Enable the service specified by hostname and binary."""
        body = {"host": host, "binary": binary}
        result = self._update("/os-services/enable", body)
        return self.resource_class(self, result)

    def disable(self, host, binary):
        """Disable the service specified by hostname and binary."""
        body = {"host": host, "binary": binary}
        result = self._update("/os-services/disable", body)
        return self.resource_class(self, result)

    def disable_log_reason(self, host, binary, reason):
        """Disable the service with reason."""
        body = {"host": host, "binary": binary, "disabled_reason": reason}
        result = self._update("/os-services/disable-log-reason", body)
        return self.resource_class(self, result)
