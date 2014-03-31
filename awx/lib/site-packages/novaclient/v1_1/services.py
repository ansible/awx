# Copyright 2012 IBM Corp.
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
from novaclient import base


class Service(base.Resource):
    def __repr__(self):
        return "<Service: %s>" % self.binary

    def _add_details(self, info):
        dico = 'resource' in info and info['resource'] or info
        for (k, v) in dico.items():
            setattr(self, k, v)


class ServiceManager(base.ManagerWithFind):
    resource_class = Service

    def list(self, host=None, binary=None):
        """
        Describes cpu/memory/hdd info for host.

        :param host: destination host name.
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

    def _update_body(self, host, binary, disabled_reason=None):
        body = {"host": host,
                "binary": binary}
        if disabled_reason is not None:
            body["disabled_reason"] = disabled_reason
        return body

    def enable(self, host, binary):
        """Enable the service specified by hostname and binary."""
        body = self._update_body(host, binary)
        return self._update("/os-services/enable", body, "service")

    def disable(self, host, binary):
        """Disable the service specified by hostname and binary."""
        body = self._update_body(host, binary)
        return self._update("/os-services/disable", body, "service")

    def disable_log_reason(self, host, binary, reason):
        """Disable the service with reason."""
        body = self._update_body(host, binary, reason)
        return self._update("/os-services/disable-log-reason", body, "service")
