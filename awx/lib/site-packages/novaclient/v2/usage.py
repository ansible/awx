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
Usage interface.
"""

from novaclient import base


class Usage(base.Resource):
    """
    Usage contains information about a tenant's physical resource usage
    """
    def __repr__(self):
        return "<ComputeUsage>"


class UsageManager(base.ManagerWithFind):
    """
    Manage :class:`Usage` resources.
    """
    resource_class = Usage

    def list(self, start, end, detailed=False):
        """
        Get usage for all tenants

        :param start: :class:`datetime.datetime` Start date
        :param end: :class:`datetime.datetime` End date
        :param detailed: Whether to include information about each
                         instance whose usage is part of the report
        :rtype: list of :class:`Usage`.
        """
        return self._list(
            "/os-simple-tenant-usage?start=%s&end=%s&detailed=%s" %
            (start.isoformat(), end.isoformat(), int(bool(detailed))),
            "tenant_usages")

    def get(self, tenant_id, start, end):
        """
        Get usage for a specific tenant.

        :param tenant_id: Tenant ID to fetch usage for
        :param start: :class:`datetime.datetime` Start date
        :param end: :class:`datetime.datetime` End date
        :rtype: :class:`Usage`
        """
        return self._get("/os-simple-tenant-usage/%s?start=%s&end=%s" %
                         (tenant_id, start.isoformat(), end.isoformat()),
                         "tenant_usage")
