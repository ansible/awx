# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

try:
    import simplejson as json
except ImportError:
    import json  # NOQA

from libcloud.loadbalancer.base import LoadBalancer, Member, Driver, Algorithm
from libcloud.compute.drivers.gce import GCEConnection, GCENodeDriver

# GCE doesn't actually give you a algorithm choice, but this is here simply as
# the closest match.  The actual algorithm is described here:
# https://developers.google.com/compute/docs/load-balancing/#overview
DEFAULT_ALGORITHM = Algorithm.RANDOM


class GCELBDriver(Driver):
    connectionCls = GCEConnection
    apiname = 'googleapis'
    name = 'Google Compute Engine Load Balancer'
    website = 'https://cloud.google.com/'

    _VALUE_TO_ALGORITHM_MAP = {
        'RANDOM': Algorithm.RANDOM
    }

    def __init__(self, *args, **kwargs):

        if kwargs.get('gce_driver'):
            self.gce = kwargs['gce_driver']
        else:
            self.gce = GCENodeDriver(*args, **kwargs)

        self.connection = self.gce.connection

    def _get_node_from_ip(self, ip):
        """
        Return the node object that matches a given public IP address.

        :param  ip: Public IP address to search for
        :type   ip: ``str``

        :return:  Node object that has the given IP, or None if not found.
        :rtype:   :class:`Node` or None
        """
        all_nodes = self.gce.list_nodes(ex_zone='all')
        for node in all_nodes:
            if ip in node.public_ips:
                return node
        return None

    def list_protocols(self):
        """
        Return a list of supported protocols.

        For GCE, this is simply a hardcoded list.

        :rtype: ``list`` of ``str``
        """
        return ['TCP', 'UDP']

    def list_balancers(self, ex_region=None):
        """
        List all loadbalancers

        :keyword  ex_region: The region to return balancers from.  If None,
                             will default to self.region.  If 'all', will
                             return all balancers.
        :type     ex_region: ``str`` or :class:`GCERegion` or ``None``

        :rtype: ``list`` of :class:`LoadBalancer`
        """
        balancers = []
        for fwr in self.gce.ex_list_forwarding_rules(region=ex_region):
            balancers.append(self._forwarding_rule_to_loadbalancer(fwr))
        return balancers

    def create_balancer(self, name, port, protocol, algorithm, members,
                        ex_region=None, ex_healthchecks=None, ex_address=None):
        """
        Create a new load balancer instance.

        For GCE, this means creating a forwarding rule and a matching target
        pool, then adding the members to the target pool.

        :param  name: Name of the new load balancer (required)
        :type   name: ``str``

        :param  port: Port or range of ports the load balancer should listen
                      on, defaults to all ports.  Examples: '80', '5000-5999'
        :type   port: ``str``

        :param  protocol: Load balancer protocol.  Should be 'tcp' or 'udp',
                          defaults to 'tcp'.
        :type   protocol: ``str``

        :param  members: List of Members to attach to balancer.  Can be Member
                         objects or Node objects.  Node objects are preferred
                         for GCE, but Member objects are accepted to comply
                         with the established libcloud API.  Note that the
                         'port' attribute of the members is ignored.
        :type   members: ``list`` of :class:`Member` or :class:`Node`

        :param  algorithm: Load balancing algorithm.  Ignored for GCE which
                           uses a hashing-based algorithm.
        :type   algorithm: :class:`Algorithm` or ``None``

        :keyword  ex_region:  Optional region to create the load balancer in.
                              Defaults to the default region of the GCE Node
                              Driver.
        :type     ex_region:  C{GCERegion} or ``str``

        :keyword  ex_healthchecks: Optional list of healthcheck objects or
                                   names to add to the load balancer.
        :type     ex_healthchecks: ``list`` of :class:`GCEHealthCheck` or
                                   ``str``

        :keyword  ex_address: Optional static address object to be assigned to
                              the load balancer.
        :type     ex_address: C{GCEAddress}

        :return:  LoadBalancer object
        :rtype:   :class:`LoadBalancer`
        """
        node_list = []
        for member in members:
            # Member object
            if hasattr(member, 'ip'):
                if member.extra.get('node'):
                    node_list.append(member.extra['node'])
                else:
                    node_list.append(self._get_node_from_ip(member.ip))
            # Node object
            elif hasattr(member, 'name'):
                node_list.append(member)
            # Assume it's a node name otherwise
            else:
                node_list.append(self.gce.ex_get_node(member, 'all'))

        # Create Target Pool
        tp_name = '%s-tp' % name
        targetpool = self.gce.ex_create_targetpool(
            tp_name, region=ex_region, healthchecks=ex_healthchecks,
            nodes=node_list)

        # Create the Forwarding rule, but if it fails, delete the target pool.
        try:
            forwarding_rule = self.gce.ex_create_forwarding_rule(
                name, targetpool, region=ex_region, protocol=protocol,
                port_range=port, address=ex_address)
        except:
            targetpool.destroy()
            raise

        # Reformat forwarding rule to LoadBalancer object
        return self._forwarding_rule_to_loadbalancer(forwarding_rule)

    def destroy_balancer(self, balancer):
        """
        Destroy a load balancer.

        For GCE, this means destroying the associated forwarding rule, then
        destroying the target pool that was attached to the forwarding rule.

        :param  balancer: LoadBalancer which should be used
        :type   balancer: :class:`LoadBalancer`

        :return:  True if successful
        :rtype:   ``bool``
        """
        destroy = balancer.extra['forwarding_rule'].destroy()
        if destroy:
            tp_destroy = balancer.extra['targetpool'].destroy()
            return tp_destroy
        else:
            return destroy

    def get_balancer(self, balancer_id):
        """
        Return a :class:`LoadBalancer` object.

        :param  balancer_id: Name of load balancer you wish to fetch.  For GCE,
                             this is the name of the associated forwarding
                             rule.
        :param  balancer_id: ``str``

        :rtype: :class:`LoadBalancer`
        """
        fwr = self.gce.ex_get_forwarding_rule(balancer_id)
        return self._forwarding_rule_to_loadbalancer(fwr)

    def balancer_attach_compute_node(self, balancer, node):
        """
        Attach a compute node as a member to the load balancer.

        :param balancer: LoadBalancer which should be used
        :type  balancer: :class:`LoadBalancer`

        :param node: Node to join to the balancer
        :type  node: :class:`Node`

        :return: Member after joining the balancer.
        :rtype: :class:`Member`
        """
        add_node = balancer.extra['targetpool'].add_node(node)
        if add_node:
            return self._node_to_member(node, balancer)

    def balancer_attach_member(self, balancer, member):
        """
        Attach a member to balancer

        :param balancer: LoadBalancer which should be used
        :type  balancer: :class:`LoadBalancer`

        :param member: Member to join to the balancer
        :type member: :class:`Member`

        :return: Member after joining the balancer.
        :rtype: :class:`Member`
        """
        node = member.extra.get('node') or self._get_node_from_ip(member.ip)
        add_node = balancer.extra['targetpool'].add_node(node)
        if add_node:
            return self._node_to_member(node, balancer)

    def balancer_detach_member(self, balancer, member):
        """
        Detach member from balancer

        :param balancer: LoadBalancer which should be used
        :type  balancer: :class:`LoadBalancer`

        :param member: Member which should be used
        :type member: :class:`Member`

        :return: True if member detach was successful, otherwise False
        :rtype: ``bool``
        """
        node = member.extra.get('node') or self._get_node_from_ip(member.ip)
        remove_node = balancer.extra['targetpool'].remove_node(node)
        return remove_node

    def balancer_list_members(self, balancer):
        """
        Return list of members attached to balancer

        :param balancer: LoadBalancer which should be used
        :type  balancer: :class:`LoadBalancer`

        :rtype: ``list`` of :class:`Member`
        """
        return [self._node_to_member(n, balancer) for n in
                balancer.extra['targetpool'].nodes]

    def ex_create_healthcheck(self, *args, **kwargs):
        return self.gce.ex_create_healthcheck(*args, **kwargs)

    def ex_list_healthchecks(self):
        return self.gce.ex_list_healthchecks()

    def ex_balancer_attach_healthcheck(self, balancer, healthcheck):
        """
        Attach a healthcheck to balancer

        :param balancer: LoadBalancer which should be used
        :type  balancer: :class:`LoadBalancer`

        :param healthcheck: Healthcheck to add
        :type  healthcheck: :class:`GCEHealthCheck`

        :return: True if successful
        :rtype:  ``bool``
        """
        return balancer.extra['targetpool'].add_healthcheck(healthcheck)

    def ex_balancer_detach_healthcheck(self, balancer, healthcheck):
        """
        Detach healtcheck from balancer

        :param balancer: LoadBalancer which should be used
        :type  balancer: :class:`LoadBalancer`

        :param healthcheck: Healthcheck to remove
        :type  healthcheck: :class:`GCEHealthCheck`

        :return: True if successful
        :rtype: ``bool``
        """
        return balancer.extra['targetpool'].remove_healthcheck(healthcheck)

    def ex_balancer_list_healthchecks(self, balancer):
        """
        Return list of healthchecks attached to balancer

        :param  balancer: LoadBalancer which should be used
        :type   balancer: :class:`LoadBalancer`

        :rtype: ``list`` of :class:`HealthChecks`
        """
        return balancer.extra['healthchecks']

    def _node_to_member(self, node, balancer):
        """
        Return a Member object based on a Node.

        :param  node: Node object
        :type   node: :class:`Node`

        :keyword  balancer: The balancer the member is attached to.
        :type     balancer: :class:`LoadBalancer`

        :return:  Member object
        :rtype:   :class:`Member`
        """
        # A balancer can have a node as a member, even if the node doesn't
        # exist.  In this case, 'node' is simply a string to where the resource
        # would be found if it was there.
        if hasattr(node, 'name'):
            member_id = node.name
            member_ip = node.public_ips[0]
        else:
            member_id = node
            member_ip = None

        extra = {'node': node}
        return Member(id=member_id, ip=member_ip, port=balancer.port,
                      balancer=balancer, extra=extra)

    def _forwarding_rule_to_loadbalancer(self, forwarding_rule):
        """
        Return a Load Balancer object based on a GCEForwardingRule object.

        :param  forwarding_rule: ForwardingRule object
        :type   forwarding_rule: :class:`GCEForwardingRule`

        :return:  LoadBalancer object
        :rtype:   :class:`LoadBalancer`
        """
        extra = {}
        extra['forwarding_rule'] = forwarding_rule
        extra['targetpool'] = forwarding_rule.targetpool
        extra['healthchecks'] = forwarding_rule.targetpool.healthchecks

        return LoadBalancer(id=forwarding_rule.id,
                            name=forwarding_rule.name, state=None,
                            ip=forwarding_rule.address,
                            port=forwarding_rule.extra['portRange'],
                            driver=self, extra=extra)
