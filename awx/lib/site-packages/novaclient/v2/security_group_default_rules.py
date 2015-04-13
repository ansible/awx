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
Security group default rules interface.
"""

from novaclient import base
from novaclient import exceptions
from novaclient.i18n import _


class SecurityGroupDefaultRule(base.Resource):
    def __str__(self):
        return str(self.id)

    def delete(self):
        self.manager.delete(self)


class SecurityGroupDefaultRuleManager(base.Manager):
    resource_class = SecurityGroupDefaultRule

    def create(self, ip_protocol=None, from_port=None, to_port=None,
               cidr=None):
        """
        Create a security group default rule

        :param ip_protocol: IP protocol, one of 'tcp', 'udp' or 'icmp'
        :param from_port: Source port
        :param to_port: Destination port
        :param cidr: Destination IP address(es) in CIDR notation
        """

        try:
            from_port = int(from_port)
        except (TypeError, ValueError):
            raise exceptions.CommandError(_("From port must be an integer."))
        try:
            to_port = int(to_port)
        except (TypeError, ValueError):
            raise exceptions.CommandError(_("To port must be an integer."))
        if ip_protocol.upper() not in ['TCP', 'UDP', 'ICMP']:
            raise exceptions.CommandError(_("IP protocol must be 'tcp', 'udp'"
                                            ", or 'icmp'."))

        body = {"security_group_default_rule": {
            "ip_protocol": ip_protocol,
            "from_port": from_port,
            "to_port": to_port,
            "cidr": cidr}}

        return self._create('/os-security-group-default-rules', body,
                            'security_group_default_rule')

    def delete(self, rule):
        """
        Delete a security group default rule

        :param rule: The security group default rule to delete (ID or Class)
        """
        self._delete('/os-security-group-default-rules/%s' % base.getid(rule))

    def list(self):
        """
        Get a list of all security group default rules

        :rtype: list of :class:`SecurityGroupDefaultRule`
        """

        return self._list('/os-security-group-default-rules',
                          'security_group_default_rules')
