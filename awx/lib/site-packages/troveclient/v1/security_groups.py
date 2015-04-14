# Copyright 2011 OpenStack Foundation
# Copyright 2013 Hewlett-Packard Development Company, L.P.
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


class SecurityGroup(base.Resource):
    """Security Group is a resource used to hold security group information."""

    def __repr__(self):
        return "<SecurityGroup: %s>" % self.name


class SecurityGroups(base.ManagerWithFind):
    """Manage :class:`SecurityGroup` resources."""
    resource_class = SecurityGroup

    def list(self, limit=None, marker=None):
        """Get a list of all security groups.

        :rtype: list of :class:`SecurityGroup`.
        """
        return self._paginated("/security-groups", "security_groups",
                               limit, marker)

    def get(self, security_group):
        """Get a specific security group.

        :rtype: :class:`SecurityGroup`
        """
        return self._get("/security-groups/%s" % base.getid(security_group),
                         "security_group")


class SecurityGroupRule(base.Resource):
    """This resource is used to hold security group rule information."""

    def __repr__(self):
        return ("<SecurityGroupRule: "
                "( Security Group id: %d, "
                "Protocol: %s, From_Port: %d, "
                "To_Port: %d,  CIDR: %s )>"
                % (self.group_id, self.protocol,
                   self.from_port, self.to_port, self.cidr))


class SecurityGroupRules(base.ManagerWithFind):
    """Manage :class:`SecurityGroupRules` resources."""
    resource_class = SecurityGroupRule

    def create(self, group_id, cidr):
        """Create a new security group rule."""
        body = {"security_group_rule": {
            "group_id": group_id,
            "cidr": cidr
        }}
        return self._create("/security-group-rules", body,
                            "security_group_rule", return_raw=True)

    def delete(self, security_group_rule):
        """Delete the specified security group rule.

        :param security_group_rule: The security group rule to delete
        """
        url = "/security-group-rules/%s" % base.getid(security_group_rule)
        resp, body = self.api.client.delete(url)
        common.check_for_exceptions(resp, body, url)

    # Appease the abc gods
    def list(self):
        pass
