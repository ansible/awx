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

from __future__ import with_statement

import base64
import warnings

from libcloud.utils.py3 import b
from libcloud.utils.py3 import urlparse

from libcloud.compute.providers import Provider
from libcloud.common.cloudstack import CloudStackDriverMixIn
from libcloud.compute.base import Node, NodeDriver, NodeImage, NodeLocation
from libcloud.compute.base import NodeSize, StorageVolume
from libcloud.compute.base import KeyPair
from libcloud.compute.types import NodeState, LibcloudError
from libcloud.compute.types import KeyPairDoesNotExistError
from libcloud.utils.networking import is_private_subnet


"""
Define the extra dictionary for specific resources
"""
RESOURCE_EXTRA_ATTRIBUTES_MAP = {
    'network': {
        'broadcast_domain_type': {
            'key_name': 'broadcastdomaintype',
            'transform_func': str
        },
        'traffic_type': {
            'key_name': 'traffictype',
            'transform_func': str
        },
        'zone_name': {
            'key_name': 'zonename',
            'transform_func': str
        },
        'network_offering_name': {
            'key_name': 'networkofferingname',
            'transform_func': str
        },
        'network_offeringdisplay_text': {
            'key_name': 'networkofferingdisplaytext',
            'transform_func': str
        },
        'network_offering_availability': {
            'key_name': 'networkofferingavailability',
            'transform_func': str
        },
        'is_system': {
            'key_name': 'issystem',
            'transform_func': str
        },
        'state': {
            'key_name': 'state',
            'transform_func': str
        },
        'dns1': {
            'key_name': 'dns1',
            'transform_func': str
        },
        'dns2': {
            'key_name': 'dns2',
            'transform_func': str
        },
        'type': {
            'key_name': 'type',
            'transform_func': str
        },
        'acl_type': {
            'key_name': 'acltype',
            'transform_func': str
        },
        'subdomain_access': {
            'key_name': 'subdomainaccess',
            'transform_func': str
        },
        'network_domain': {
            'key_name': 'networkdomain',
            'transform_func': str
        },
        'physical_network_id': {
            'key_name': 'physicalnetworkid',
            'transform_func': str
        },
        'can_use_for_deploy': {
            'key_name': 'canusefordeploy',
            'transform_func': str
        },
        'gateway': {
            'key_name': 'gateway',
            'transform_func': str
        },
        'netmask': {
            'key_name': 'netmask',
            'transform_func': str
        },
        'vpc_id': {
            'key_name': 'vpcid',
            'transform_func': str
        },
        'project_id': {
            'key_name': 'projectid',
            'transform_func': str
        }
    },
    'node': {
        'haenable': {
            'key_name': 'haenable',
            'transform_func': str
        },
        'zone_id': {
            'key_name': 'zoneid',
            'transform_func': str
        },
        'zone_name': {
            'key_name': 'zonename',
            'transform_func': str
        },
        'key_name': {
            'key_name': 'keypair',
            'transform_func': str
        },
        'password': {
            'key_name': 'password',
            'transform_func': str
        },
        'image_id': {
            'key_name': 'templateid',
            'transform_func': str
        },
        'image_name': {
            'key_name': 'templatename',
            'transform_func': str
        },
        'template_display_text': {
            'key_name': 'templatdisplaytext',
            'transform_func': str
        },
        'password_enabled': {
            'key_name': 'passwordenabled',
            'transform_func': str
        },
        'size_id': {
            'key_name': 'serviceofferingid',
            'transform_func': str
        },
        'size_name': {
            'key_name': 'serviceofferingname',
            'transform_func': str
        },
        'root_device_id': {
            'key_name': 'rootdeviceid',
            'transform_func': str
        },
        'root_device_type': {
            'key_name': 'rootdevicetype',
            'transform_func': str
        },
        'hypervisor': {
            'key_name': 'hypervisor',
            'transform_func': str
        },
        'project': {
            'key_name': 'project',
            'transform_func': str
        },
        'project_id': {
            'key_name': 'projectid',
            'transform_func': str
        }
    },
    'volume': {
        'created': {
            'key_name': 'created',
            'transform_func': str
        },
        'device_id': {
            'key_name': 'deviceid',
            'transform_func': int
        },
        'instance_id': {
            'key_name': 'serviceofferingid',
            'transform_func': str
        },
        'state': {
            'key_name': 'state',
            'transform_func': str
        },
        'volume_type': {
            'key_name': 'type',
            'transform_func': str
        },
        'zone_id': {
            'key_name': 'zoneid',
            'transform_func': str
        },
        'zone_name': {
            'key_name': 'zonename',
            'transform_func': str
        }
    },
    'project': {
        'account': {'key_name': 'account', 'transform_func': str},
        'cpuavailable': {'key_name': 'cpuavailable', 'transform_func': int},
        'cpulimit': {'key_name': 'cpulimit', 'transform_func': int},
        'cputotal': {'key_name': 'cputotal', 'transform_func': int},
        'domain': {'key_name': 'domain', 'transform_func': str},
        'domainid': {'key_name': 'domainid', 'transform_func': str},
        'ipavailable': {'key_name': 'ipavailable', 'transform_func': int},
        'iplimit': {'key_name': 'iplimit', 'transform_func': int},
        'iptotal': {'key_name': 'iptotal', 'transform_func': int},
        'memoryavailable': {'key_name': 'memoryavailable',
                            'transform_func': int},
        'memorylimit': {'key_name': 'memorylimit', 'transform_func': int},
        'memorytotal': {'key_name': 'memorytotal', 'transform_func': int},
        'networkavailable': {'key_name': 'networkavailable',
                             'transform_func': int},
        'networklimit': {'key_name': 'networklimit', 'transform_func': int},
        'networktotal': {'key_name': 'networktotal', 'transform_func': int},
        'primarystorageavailable': {'key_name': 'primarystorageavailable',
                                    'transform_func': int},
        'primarystoragelimit': {'key_name': 'primarystoragelimit',
                                'transform_func': int},
        'primarystoragetotal': {'key_name': 'primarystoragetotal',
                                'transform_func': int},
        'secondarystorageavailable': {'key_name': 'secondarystorageavailable',
                                      'transform_func': int},
        'secondarystoragelimit': {'key_name': 'secondarystoragelimit',
                                  'transform_func': int},
        'secondarystoragetotal': {'key_name': 'secondarystoragetotal',
                                  'transform_func': int},
        'snapshotavailable': {'key_name': 'snapshotavailable',
                              'transform_func': int},
        'snapshotlimit': {'key_name': 'snapshotlimit', 'transform_func': int},
        'snapshottotal': {'key_name': 'snapshottotal', 'transform_func': int},
        'state': {'key_name': 'state', 'transform_func': str},
        'tags': {'key_name': 'tags', 'transform_func': str},
        'templateavailable': {'key_name': 'templateavailable',
                              'transform_func': int},
        'templatelimit': {'key_name': 'templatelimit', 'transform_func': int},
        'templatetotal': {'key_name': 'templatetotal', 'transform_func': int},
        'vmavailable': {'key_name': 'vmavailable', 'transform_func': int},
        'vmlimit': {'key_name': 'vmlimit', 'transform_func': int},
        'vmrunning': {'key_name': 'vmrunning', 'transform_func': int},
        'vmtotal': {'key_name': 'vmtotal', 'transform_func': int},
        'volumeavailable': {'key_name': 'volumeavailable',
                            'transform_func': int},
        'volumelimit': {'key_name': 'volumelimit', 'transform_func': int},
        'volumetotal': {'key_name': 'volumetotal', 'transform_func': int},
        'vpcavailable': {'key_name': 'vpcavailable', 'transform_func': int},
        'vpclimit': {'key_name': 'vpclimit', 'transform_func': int},
        'vpctotal': {'key_name': 'vpctotal', 'transform_func': int}
    }
}


class CloudStackNode(Node):
    """
    Subclass of Node so we can expose our extension methods.
    """

    def ex_allocate_public_ip(self):
        """
        Allocate a public IP and bind it to this node.
        """
        return self.driver.ex_allocate_public_ip(self)

    def ex_release_public_ip(self, address):
        """
        Release a public IP that this node holds.
        """
        return self.driver.ex_release_public_ip(self, address)

    def ex_create_ip_forwarding_rule(self, address, protocol,
                                     start_port, end_port=None):
        """
        Add a NAT/firewall forwarding rule for a port or ports.
        """
        return self.driver.ex_create_ip_forwarding_rule(node=self,
                                                        address=address,
                                                        protocol=protocol,
                                                        start_port=start_port,
                                                        end_port=end_port)

    def ex_create_port_forwarding_rule(self, address,
                                       private_port, public_port,
                                       protocol,
                                       public_end_port=None,
                                       private_end_port=None,
                                       openfirewall=True):
        """
        Add a port forwarding rule for port or ports.
        """
        return self.driver.ex_create_port_forwarding_rule(
            node=self, address=address, private_port=private_port,
            public_port=public_port, protocol=protocol,
            public_end_port=public_end_port, private_end_port=private_end_port,
            openfirewall=openfirewall)

    def ex_delete_ip_forwarding_rule(self, rule):
        """
        Delete a port forwarding rule.
        """
        return self.driver.ex_delete_ip_forwarding_rule(node=self, rule=rule)

    def ex_delete_port_forwarding_rule(self, rule):
        """
        Delete a NAT/firewall rule.
        """
        return self.driver.ex_delete_port_forwarding_rule(node=self, rule=rule)

    def ex_start(self):
        """
        Starts a stopped virtual machine.
        """
        return self.driver.ex_start(node=self)

    def ex_stop(self):
        """
        Stops a running virtual machine.
        """
        return self.driver.ex_stop(node=self)


class CloudStackAddress(object):
    """
    A public IP address.

    :param      id: UUID of the Public IP
    :type       id: ``str``

    :param      address: The public IP address
    :type       address: ``str``

    :param      associated_network_id: The ID of the network where this address
                                        has been associated with
    :type       associated_network_id: ``str``
    """

    def __init__(self, id, address, driver, associated_network_id=None):
        self.id = id
        self.address = address
        self.driver = driver
        self.associated_network_id = associated_network_id

    def release(self):
        self.driver.ex_release_public_ip(address=self)

    def __str__(self):
        return self.address

    def __eq__(self, other):
        return self.__class__ is other.__class__ and self.id == other.id


class CloudStackIPForwardingRule(object):
    """
    A NAT/firewall forwarding rule.
    """

    def __init__(self, node, id, address, protocol, start_port, end_port=None):
        self.node = node
        self.id = id
        self.address = address
        self.protocol = protocol
        self.start_port = start_port
        self.end_port = end_port

    def delete(self):
        self.node.ex_delete_ip_forwarding_rule(rule=self)

    def __eq__(self, other):
        return self.__class__ is other.__class__ and self.id == other.id


class CloudStackPortForwardingRule(object):
    """
    A Port forwarding rule for Source NAT.
    """

    def __init__(self, node, rule_id, address, protocol, public_port,
                 private_port, public_end_port=None, private_end_port=None):
        """
        A Port forwarding rule for Source NAT.

        @note: This is a non-standard extension API, and only works for EC2.

        :param      node: Node for rule
        :type       node: :class:`Node`

        :param      rule_id: Rule ID
        :type       rule_id: ``int``

        :param      address: External IP address
        :type       address: :class:`CloudStackAddress`

        :param      protocol: TCP/IP Protocol (TCP, UDP)
        :type       protocol: ``str``

        :param      public_port: External port for rule (or start port if
                                 public_end_port is also provided)
        :type       public_port: ``int``

        :param      private_port: Internal node port for rule (or start port if
                                  public_end_port is also provided)
        :type       private_port: ``int``

        :param      public_end_port: End of external port range
        :type       public_end_port: ``int``

        :param      private_end_port: End of internal port range
        :type       private_end_port: ``int``

        :rtype: :class:`CloudStackPortForwardingRule`
        """
        self.node = node
        self.id = rule_id
        self.address = address
        self.protocol = protocol
        self.public_port = public_port
        self.public_end_port = public_end_port
        self.private_port = private_port
        self.private_end_port = private_end_port

    def delete(self):
        self.node.ex_delete_port_forwarding_rule(rule=self)

    def __eq__(self, other):
        return self.__class__ is other.__class__ and self.id == other.id


class CloudStackDiskOffering(object):
    """
    A disk offering within CloudStack.
    """

    def __init__(self, id, name, size, customizable):
        self.id = id
        self.name = name
        self.size = size
        self.customizable = customizable

    def __eq__(self, other):
        return self.__class__ is other.__class__ and self.id == other.id


class CloudStackNetwork(object):
    """
    Class representing a CloudStack Network.
    """

    def __init__(self, displaytext, name, networkofferingid, id, zoneid,
                 driver, extra=None):
        self.displaytext = displaytext
        self.name = name
        self.networkofferingid = networkofferingid
        self.id = id
        self.zoneid = zoneid
        self.driver = driver
        self.extra = extra or {}

    def __repr__(self):
        return (('<CloudStackNetwork: id=%s, displaytext=%s, name=%s, '
                 'networkofferingid=%s, zoneid=%s, driver%s>')
                % (self.id, self.displaytext, self.name,
                   self.networkofferingid, self.zoneid, self.driver.name))


class CloudStackNetworkOffering(object):
    """
    Class representing a CloudStack Network Offering.
    """

    def __init__(self, name, display_text, guest_ip_type, id,
                 service_offering_id, for_vpc, driver, extra=None):
        self.display_text = display_text
        self.name = name
        self.guest_ip_type = guest_ip_type
        self.id = id
        self.service_offering_id = service_offering_id
        self.for_vpc = for_vpc
        self.driver = driver
        self.extra = extra or {}

    def __repr__(self):
        return (('<CloudStackNetworkOffering: id=%s, name=%s, '
                 'display_text=%s, guest_ip_type=%s, service_offering_id=%s, '
                 'for_vpc=%s, driver%s>')
                % (self.id, self.name, self.display_text,
                   self.guest_ip_type, self.service_offering_id, self.for_vpc,
                   self.driver.name))


class CloudStackProject(object):
    """
    Class representing a CloudStack Project.
    """

    def __init__(self, id, name, display_text, driver, extra=None):
        self.id = id
        self.name = name
        self.display_text = display_text
        self.driver = driver
        self.extra = extra or {}

    def __repr__(self):
        return (('<CloudStackProject: id=%s, display_text=%s, name=%s, '
                 'driver=%s>')
                % (self.id, self.display_text, self.name,
                   self.driver.name))


class CloudStackNodeDriver(CloudStackDriverMixIn, NodeDriver):
    """
    Driver for the CloudStack API.

    :cvar host: The host where the API can be reached.
    :cvar path: The path where the API can be reached.
    :cvar async_poll_frequency: How often (in seconds) to poll for async
                                job completion.
    :type async_poll_frequency: ``int``"""

    name = 'CloudStack'
    api_name = 'cloudstack'
    website = 'http://cloudstack.org/'
    type = Provider.CLOUDSTACK

    features = {'create_node': ['generates_password']}

    NODE_STATE_MAP = {
        'Running': NodeState.RUNNING,
        'Starting': NodeState.REBOOTING,
        'Stopped': NodeState.STOPPED,
        'Stopping': NodeState.PENDING,
        'Destroyed': NodeState.TERMINATED,
        'Expunging': NodeState.PENDING,
        'Error': NodeState.TERMINATED
    }

    def __init__(self, key, secret=None, secure=True, host=None,
                 path=None, port=None, url=None, *args, **kwargs):
        """
        :inherits: :class:`NodeDriver.__init__`

        :param    host: The host where the API can be reached. (required)
        :type     host: ``str``

        :param    path: The path where the API can be reached. (required)
        :type     path: ``str``

        :param url: Full URL to the API endpoint. Mutually exclusive with host
                    and path argument.
        :type url: ``str``
        """
        if url:
            parsed = urlparse.urlparse(url)

            path = parsed.path

            scheme = parsed.scheme
            split = parsed.netloc.split(':')

            if len(split) == 1:
                # No port provided, use the default one
                host = parsed.netloc
                port = 443 if scheme == 'https' else 80
            else:
                host = split[0]
                port = int(split[1])
        else:
            host = host if host else self.host
            path = path if path else self.path

        if path is not None:
            self.path = path

        if host is not None:
            self.host = host

        if (self.type == Provider.CLOUDSTACK) and (not host or not path):
            raise Exception('When instantiating CloudStack driver directly '
                            'you also need to provide url or host and path '
                            'argument')

        super(CloudStackNodeDriver, self).__init__(key=key,
                                                   secret=secret,
                                                   secure=secure,
                                                   host=host,
                                                   port=port)

    def list_images(self, location=None):
        args = {
            'templatefilter': 'executable'
        }
        if location is not None:
            args['zoneid'] = location.id
        imgs = self._sync_request(command='listTemplates',
                                  params=args,
                                  method='GET')
        images = []
        for img in imgs.get('template', []):
            images.append(NodeImage(
                id=img['id'],
                name=img['name'],
                driver=self.connection.driver,
                extra={
                    'hypervisor': img['hypervisor'],
                    'format': img['format'],
                    'os': img['ostypename'],
                    'displaytext': img['displaytext']}))
        return images

    def list_locations(self):
        """
        :rtype ``list`` of :class:`NodeLocation`
        """
        locs = self._sync_request('listZones')

        locations = []
        for loc in locs['zone']:
            location = NodeLocation(str(loc['id']), loc['name'], 'Unknown',
                                    self)
            locations.append(location)

        return locations

    def list_nodes(self, project=None):
        """
        @inherits: :class:`NodeDriver.list_nodes`

        :keyword    project: Limit nodes returned to those configured under
                             the defined project.
        :type       project: :class:`.CloudStackProject`

        :rtype: ``list`` of :class:`CloudStackNode`
        """

        args = {}
        if project:
            args['projectid'] = project.id
        vms = self._sync_request('listVirtualMachines', params=args)
        addrs = self._sync_request('listPublicIpAddresses', params=args)

        public_ips_map = {}
        for addr in addrs.get('publicipaddress', []):
            if 'virtualmachineid' not in addr:
                continue
            vm_id = str(addr['virtualmachineid'])
            if vm_id not in public_ips_map:
                public_ips_map[vm_id] = {}
            public_ips_map[vm_id][addr['ipaddress']] = addr['id']

        nodes = []

        for vm in vms.get('virtualmachine', []):
            public_ips = public_ips_map.get(str(vm['id']), {}).keys()
            public_ips = list(public_ips)
            node = self._to_node(data=vm, public_ips=public_ips)

            addresses = public_ips_map.get(vm['id'], {}).items()
            addresses = [CloudStackAddress(node, v, k) for k, v in addresses]
            node.extra['ip_addresses'] = addresses

            rules = []
            for addr in addresses:
                result = self._sync_request('listIpForwardingRules')
                for r in result.get('ipforwardingrule', []):
                    if str(r['virtualmachineid']) == node.id:
                        rule = CloudStackIPForwardingRule(node, r['id'],
                                                          addr,
                                                          r['protocol']
                                                          .upper(),
                                                          r['startport'],
                                                          r['endport'])
                        rules.append(rule)
            node.extra['ip_forwarding_rules'] = rules

            rules = []
            public_ips = self.ex_list_public_ips()
            result = self._sync_request('listPortForwardingRules')
            for r in result.get('portforwardingrule', []):
                if str(r['virtualmachineid']) == node.id:
                    addr = [a for a in public_ips if
                            a.address == r['ipaddress']]
                    rule = CloudStackPortForwardingRule(node, r['id'],
                                                        addr[0],
                                                        r['protocol'].upper(),
                                                        r['publicport'],
                                                        r['privateport'],
                                                        r['publicendport'],
                                                        r['privateendport'])
                    if not addr[0].address in node.public_ips:
                        node.public_ips.append(addr[0].address)
                    rules.append(rule)
            node.extra['port_forwarding_rules'] = rules

            nodes.append(node)

        return nodes

    def list_sizes(self, location=None):
        """
        :rtype ``list`` of :class:`NodeSize`
        """
        szs = self._sync_request(command='listServiceOfferings',
                                 method='GET')
        sizes = []
        for sz in szs['serviceoffering']:
            extra = {'cpu': sz['cpunumber']}
            sizes.append(NodeSize(sz['id'], sz['name'], sz['memory'], 0, 0,
                                  0, self, extra=extra))
        return sizes

    def create_node(self, **kwargs):
        """
        Create a new node

        @inherits: :class:`NodeDriver.create_node`

        :keyword    networks: Optional list of networks to launch the server
                              into.
        :type       networks: ``list`` of :class:`.CloudStackNetwork`

        :keyword    project: Optional project to create the new node under.
        :type       project: :class:`.CloudStackProject`

        :keyword    diskoffering:  Optional disk offering to add to the new
                                   node.
        :type       diskoffering:  :class:`.CloudStackDiskOffering`

        :keyword    ex_keyname:  Name of existing keypair
        :type       ex_keyname:  ``str``

        :keyword    ex_userdata: String containing user data
        :type       ex_userdata: ``str``

        :keyword    ex_security_groups: List of security groups to assign to
                                        the node
        :type       ex_security_groups: ``list`` of ``str``

        :keyword    ex_displayname: String containing instance display name
        :type       ex_displayname: ``str``

        :rtype:     :class:`.CloudStackNode`
        """

        server_params = self._create_args_to_params(None, **kwargs)

        data = self._async_request(command='deployVirtualMachine',
                                   params=server_params,
                                   method='GET')['virtualmachine']
        node = self._to_node(data=data)
        return node

    def _create_args_to_params(self, node, **kwargs):
        server_params = {}

        # TODO: Refactor and use "kwarg_to_server_params" map
        name = kwargs.get('name', None)
        size = kwargs.get('size', None)
        image = kwargs.get('image', None)
        location = kwargs.get('location', None)
        networks = kwargs.get('networks', None)
        project = kwargs.get('project', None)
        diskoffering = kwargs.get('diskoffering', None)
        ex_key_name = kwargs.get('ex_keyname', None)
        ex_user_data = kwargs.get('ex_userdata', None)
        ex_security_groups = kwargs.get('ex_security_groups', None)
        ex_displayname = kwargs.get('ex_displayname', None)

        if name:
            server_params['name'] = name

        if ex_displayname:
            server_params['displayname'] = ex_displayname

        if size:
            server_params['serviceofferingid'] = size.id

        if image:
            server_params['templateid'] = image.id

        if location:
            server_params['zoneid'] = location.id
        else:
            # Use a default location
            server_params['zoneid'] = self.list_locations()[0].id

        if networks:
            networks = ','.join([network.id for network in networks])
            server_params['networkids'] = networks

        if project:
            server_params['projectid'] = project.id

        if diskoffering:
            server_params['diskofferingid'] = diskoffering.id

        if ex_key_name:
            server_params['keypair'] = ex_key_name

        if ex_user_data:
            ex_user_data = base64.b64encode(b(ex_user_data).decode('ascii'))
            server_params['userdata'] = ex_user_data

        if ex_security_groups:
            ex_security_groups = ','.join(ex_security_groups)
            server_params['securitygroupnames'] = ex_security_groups

        return server_params

    def destroy_node(self, node):
        """
        @inherits: :class:`NodeDriver.reboot_node`
        :type node: :class:`CloudStackNode`

        :rtype: ``bool``
        """
        self._async_request(command='destroyVirtualMachine',
                            params={'id': node.id},
                            method='GET')
        return True

    def reboot_node(self, node):
        """
        @inherits: :class:`NodeDriver.reboot_node`
        :type node: :class:`CloudStackNode`

        :rtype: ``bool``
        """
        self._async_request(command='rebootVirtualMachine',
                            params={'id': node.id},
                            method='GET')
        return True

    def ex_start(self, node):
        """
        Starts/Resumes a stopped virtual machine

        :type node: :class:`CloudStackNode`

        :param id: The ID of the virtual machine (required)
        :type  id: ``str``

        :param hostid: destination Host ID to deploy the VM to
                       parameter available for root admin only
        :type  hostid: ``str``

        :rtype ``str``
        """
        res = self._async_request(command='startVirtualMachine',
                                  params={'id': node.id},
                                  method='GET')
        return res['virtualmachine']['state']

    def ex_stop(self, node):
        """
        Stops/Suspends a running virtual machine

        :param node: Node to stop.
        :type node: :class:`CloudStackNode`

        :rtype: ``str``
        """
        res = self._async_request(command='stopVirtualMachine',
                                  params={'id': node.id},
                                  method='GET')
        return res['virtualmachine']['state']

    def ex_list_disk_offerings(self):
        """
        Fetch a list of all available disk offerings.

        :rtype: ``list`` of :class:`CloudStackDiskOffering`
        """

        diskOfferings = []

        diskOfferResponse = self._sync_request(command='listDiskOfferings',
                                               method='GET')
        for diskOfferDict in diskOfferResponse.get('diskoffering', ()):
            diskOfferings.append(
                CloudStackDiskOffering(
                    id=diskOfferDict['id'],
                    name=diskOfferDict['name'],
                    size=diskOfferDict['disksize'],
                    customizable=diskOfferDict['iscustomized']))

        return diskOfferings

    def ex_list_networks(self):
        """
        List the available networks

        :rtype ``list`` of :class:`CloudStackNetwork`
        """

        res = self._sync_request(command='listNetworks',
                                 method='GET')
        nets = res.get('network', [])

        networks = []
        extra_map = RESOURCE_EXTRA_ATTRIBUTES_MAP['network']
        for net in nets:
            extra = self._get_extra_dict(net, extra_map)

            if 'tags' in net:
                extra['tags'] = self._get_resource_tags(net['tags'])

            networks.append(CloudStackNetwork(
                            net['displaytext'],
                            net['name'],
                            net['networkofferingid'],
                            net['id'],
                            net['zoneid'],
                            self,
                            extra=extra))

        return networks

    def ex_list_network_offerings(self):
        """
        List the available network offerings

        :rtype ``list`` of :class:`CloudStackNetworkOffering`
        """
        res = self._sync_request(command='listNetworkOfferings',
                                 method='GET')
        netoffers = res.get('networkoffering', [])

        networkofferings = []

        for netoffer in netoffers:
            networkofferings.append(CloudStackNetworkOffering(
                                    netoffer['name'],
                                    netoffer['displaytext'],
                                    netoffer['guestiptype'],
                                    netoffer['id'],
                                    netoffer['serviceofferingid'],
                                    netoffer['forvpc'],
                                    self))

        return networkofferings

    def ex_create_network(self, display_text, name, network_offering,
                          location, gateway=None, netmask=None,
                          network_domain=None, vpc_id=None, project_id=None):
        """

        Creates a Network, only available in advanced zones.

        :param  display_text: the display text of the network
        :type   display_text: ``str``

        :param  name: the name of the network
        :type   name: ``str``

        :param  network_offering: the network offering id
        :type   network_offering: :class:'CloudStackNetworkOffering`

        :param location: Zone
        :type  location: :class:`NodeLocation`

        :param  gateway: Optional, the Gateway of this network
        :type   gateway: ``str``

        :param  netmask: Optional, the netmask of this network
        :type   netmask: ``str``

        :param  network_domain: Optional, the DNS domain of the network
        :type   network_domain: ``str``

        :param  vpc_id: Optional, the VPC id the network belongs to
        :type   vpc_id: ``str``

        :param  project_id: Optional, the project id the networks belongs to
        :type   project_id: ``str``

        :rtype: :class:`CloudStackNetwork`

        """

        extra_map = RESOURCE_EXTRA_ATTRIBUTES_MAP['network']

        args = {
            'displaytext': display_text,
            'name': name,
            'networkofferingid': network_offering.id,
            'zoneid': location.id,
        }

        if gateway is not None:
            args['gateway'] = gateway

        if netmask is not None:
            args['netmask'] = netmask

        if network_domain is not None:
            args['networkdomain'] = network_domain

        if vpc_id is not None:
            args['vpcid'] = vpc_id

        if project_id is not None:
            args['projectid'] = project_id

        """ Cloudstack allows for duplicate network names,
        this should be handled in the code leveraging libcloud
        As there could be use cases for duplicate names.
        e.g. management from ROOT level"""

        # for net in self.ex_list_networks():
        #    if name == net.name:
        #        raise LibcloudError('This network name already exists')

        result = self._sync_request(command='createNetwork',
                                    params=args,
                                    method='GET')

        result = result['network']
        extra = self._get_extra_dict(result, extra_map)

        network = CloudStackNetwork(display_text,
                                    name,
                                    network_offering.id,
                                    result['id'],
                                    location.id,
                                    self,
                                    extra=extra)

        return network

    def ex_delete_network(self, network, force=None):
        """

        Deletes a Network, only available in advanced zones.

        :param  network: The network
        :type   network: :class: 'CloudStackNetwork'

        :param  force: Force deletion of the network?
        :type   force: ``bool``

        :rtype: ``bool``

        """

        args = {'id': network.id, 'forced': force}

        self._async_request(command='deleteNetwork',
                            params=args,
                            method='GET')
        return True

    def ex_list_projects(self):
        """
        List the available projects

        :rtype ``list`` of :class:`CloudStackProject`
        """

        res = self._sync_request(command='listProjects',
                                 method='GET')
        projs = res.get('project', [])

        projects = []
        extra_map = RESOURCE_EXTRA_ATTRIBUTES_MAP['project']
        for proj in projs:
            extra = self._get_extra_dict(proj, extra_map)

            if 'tags' in proj:
                extra['tags'] = self._get_resource_tags(proj['tags'])

            projects.append(CloudStackProject(
                            id=proj['id'],
                            name=proj['name'],
                            display_text=proj['displaytext'],
                            driver=self,
                            extra=extra))

        return projects

    def create_volume(self, size, name, location=None, snapshot=None):
        """
        Creates a data volume
        Defaults to the first location
        """
        for diskOffering in self.ex_list_disk_offerings():
            if diskOffering.size == size or diskOffering.customizable:
                break
        else:
            raise LibcloudError(
                'Disk offering with size=%s not found' % size)

        if location is None:
            location = self.list_locations()[0]

        params = {'name': name,
                  'diskOfferingId': diskOffering.id,
                  'zoneId': location.id}

        if diskOffering.customizable:
            params['size'] = size

        requestResult = self._async_request(command='createVolume',
                                            params=params,
                                            method='GET')

        volumeResponse = requestResult['volume']

        return StorageVolume(id=volumeResponse['id'],
                             name=name,
                             size=size,
                             driver=self,
                             extra=dict(name=volumeResponse['name']))

    def destroy_volume(self, volume):
        """
        :rtype: ``bool``
        """
        self._sync_request(command='deleteVolume',
                           params={'id': volume.id},
                           method='GET')
        return True

    def attach_volume(self, node, volume, device=None):
        """
        @inherits: :class:`NodeDriver.attach_volume`
        :type node: :class:`CloudStackNode`

        :rtype: ``bool``
        """
        # TODO Add handling for device name
        self._async_request(command='attachVolume',
                            params={'id': volume.id,
                                    'virtualMachineId': node.id},
                            method='GET')
        return True

    def detach_volume(self, volume):
        """
        :rtype: ``bool``
        """
        self._async_request(command='detachVolume',
                            params={'id': volume.id},
                            method='GET')
        return True

    def list_volumes(self, node=None):
        """
        List all volumes

        :param node: Only return volumes for the provided node.
        :type node: :class:`CloudStackNode`

        :rtype: ``list`` of :class:`StorageVolume`
        """
        if node:
            volumes = self._sync_request(command='listVolumes',
                                         params={'virtualmachineid': node.id},
                                         method='GET')
        else:
            volumes = self._sync_request(command='listVolumes',
                                         method='GET')

        list_volumes = []
        extra_map = RESOURCE_EXTRA_ATTRIBUTES_MAP['volume']
        for vol in volumes['volume']:
            extra = self._get_extra_dict(vol, extra_map)

            if 'tags' in vol:
                extra['tags'] = self._get_resource_tags(vol['tags'])

            list_volumes.append(StorageVolume(id=vol['id'],
                                              name=vol['name'],
                                              size=vol['size'],
                                              driver=self,
                                              extra=extra))
        return list_volumes

    def list_key_pairs(self, **kwargs):
        """
        List registered key pairs.

        :param     projectid: list objects by project
        :type      projectid: ``str``

        :param     page: The page to list the keypairs from
        :type      page: ``int``

        :param     keyword: List by keyword
        :type      keyword: ``str``

        :param     listall: If set to false, list only resources
                            belonging to the command's caller;
                            if set to true - list resources that
                            the caller is authorized to see.
                            Default value is false

        :type      listall: ``bool``

        :param     pagesize: The number of results per page
        :type      pagesize: ``int``

        :param     account: List resources by account.
                            Must be used with the domainId parameter
        :type      account: ``str``

        :param     isrecursive: Defaults to false, but if true,
                                lists all resources from
                                the parent specified by the
                                domainId till leaves.
        :type      isrecursive: ``bool``

        :param     fingerprint: A public key fingerprint to look for
        :type      fingerprint: ``str``

        :param     name: A key pair name to look for
        :type      name: ``str``

        :param     domainid: List only resources belonging to
                                     the domain specified
        :type      domainid: ``str``

        :return:   A list of key par objects.
        :rtype:   ``list`` of :class:`libcloud.compute.base.KeyPair`
        """
        extra_args = kwargs.copy()
        res = self._sync_request(command='listSSHKeyPairs',
                                 params=extra_args,
                                 method='GET')
        key_pairs = res.get('sshkeypair', [])
        key_pairs = self._to_key_pairs(data=key_pairs)
        return key_pairs

    def get_key_pair(self, name):
        params = {'name': name}
        res = self._sync_request(command='listSSHKeyPairs',
                                 params=params,
                                 method='GET')
        key_pairs = res.get('sshkeypair', [])

        if len(key_pairs) == 0:
            raise KeyPairDoesNotExistError(name=name, driver=self)

        key_pair = self._to_key_pair(data=key_pairs[0])
        return key_pair

    def create_key_pair(self, name, **kwargs):
        """
        Create a new key pair object.

        :param name: Key pair name.
        :type name: ``str``

        :param     name: Name of the keypair (required)
        :type      name: ``str``

        :param     projectid: An optional project for the ssh key
        :type      projectid: ``str``

        :param     domainid: An optional domainId for the ssh key.
                             If the account parameter is used,
                             domainId must also be used.
        :type      domainid: ``str``

        :param     account: An optional account for the ssh key.
                            Must be used with domainId.
        :type      account: ``str``

        :return:   Created key pair object.
        :rtype:    :class:`libcloud.compute.base.KeyPair`
        """
        extra_args = kwargs.copy()

        params = {'name': name}
        params.update(extra_args)

        res = self._sync_request(command='createSSHKeyPair',
                                 params=params,
                                 method='GET')
        key_pair = self._to_key_pair(data=res['keypair'])
        return key_pair

    def import_key_pair_from_string(self, name, key_material):
        """
        Import a new public key from string.

        :param name: Key pair name.
        :type name: ``str``

        :param key_material: Public key material.
        :type key_material: ``str``

        :return: Imported key pair object.
        :rtype: :class:`libcloud.compute.base.KeyPair`
        """
        res = self._sync_request(command='registerSSHKeyPair',
                                 params={'name': name,
                                         'publickey': key_material},
                                 method='GET')
        key_pair = self._to_key_pair(data=res['keypair'])
        return key_pair

    def delete_key_pair(self, key_pair, **kwargs):
        """
        Delete an existing key pair.

        :param key_pair: Key pair object.
        :type key_pair: :class`libcloud.compute.base.KeyPair`

        :param     projectid: The project associated with keypair
        :type      projectid: ``str``

        :param     domainid: The domain ID associated with the keypair
        :type      domainid: ``str``

        :param     account: The account associated with the keypair.
                            Must be used with the domainId parameter.
        :type      account: ``str``

        :return:   True of False based on success of Keypair deletion
        :rtype:    ``bool``
        """

        extra_args = kwargs.copy()
        params = {'name': key_pair.name}
        params.update(extra_args)

        res = self._sync_request(command='deleteSSHKeyPair',
                                 params=params,
                                 method='GET')
        return res['success'] == 'true'

    def ex_list_public_ips(self):
        """
        Lists all Public IP Addresses.

        :rtype: ``list`` of :class:`CloudStackAddress`
        """
        ips = []

        res = self._sync_request(command='listPublicIpAddresses',
                                 method='GET')

        # Workaround for basic zones
        if not res:
            return ips

        for ip in res['publicipaddress']:
            ips.append(CloudStackAddress(ip['id'],
                                         ip['ipaddress'],
                                         self,
                                         ip['associatednetworkid']))
        return ips

    def ex_allocate_public_ip(self, location=None):
        """
        Allocate a public IP.

        :param location: Zone
        :type  location: :class:`NodeLocation`

        :rtype: :class:`CloudStackAddress`
        """
        if location is None:
            location = self.list_locations()[0]

        addr = self._async_request(command='associateIpAddress',
                                   params={'zoneid': location.id},
                                   method='GET')
        addr = addr['ipaddress']
        addr = CloudStackAddress(addr['id'], addr['ipaddress'], self)
        return addr

    def ex_release_public_ip(self, address):
        """
        Release a public IP.

        :param address: CloudStackAddress which should be used
        :type  address: :class:`CloudStackAddress`

        :rtype: ``bool``
        """
        res = self._async_request(command='disassociateIpAddress',
                                  params={'id': address.id},
                                  method='GET')
        return res['success']

    def ex_list_port_forwarding_rules(self):
        """
        Lists all Port Forwarding Rules

        :rtype: ``list`` of :class:`CloudStackPortForwardingRule`
        """
        rules = []
        result = self._sync_request(command='listPortForwardingRules',
                                    method='GET')
        if result != {}:
            public_ips = self.ex_list_public_ips()
            nodes = self.list_nodes()
            for rule in result['portforwardingrule']:
                node = [n for n in nodes
                        if n.id == str(rule['virtualmachineid'])]
                addr = [a for a in public_ips if
                        a.address == rule['ipaddress']]
                rules.append(CloudStackPortForwardingRule
                             (node[0],
                              rule['id'],
                              addr[0],
                              rule['protocol'],
                              rule['publicport'],
                              rule['privateport'],
                              rule['publicendport'],
                              rule['privateendport']))

        return rules

    def ex_create_port_forwarding_rule(self, node, address,
                                       private_port, public_port,
                                       protocol,
                                       public_end_port=None,
                                       private_end_port=None,
                                       openfirewall=True):
        """
        Creates a Port Forwarding Rule, used for Source NAT

        :param  address: IP address of the Source NAT
        :type   address: :class:`CloudStackAddress`

        :param  private_port: Port of the virtual machine
        :type   private_port: ``int``

        :param  protocol: Protocol of the rule
        :type   protocol: ``str``

        :param  public_port: Public port on the Source NAT address
        :type   public_port: ``int``

        :param  node: The virtual machine
        :type   node: :class:`CloudStackNode`

        :rtype: :class:`CloudStackPortForwardingRule`
        """
        args = {
            'ipaddressid': address.id,
            'protocol': protocol,
            'privateport': int(private_port),
            'publicport': int(public_port),
            'virtualmachineid': node.id,
            'openfirewall': openfirewall
        }
        if public_end_port:
            args['publicendport'] = int(public_end_port)
        if private_end_port:
            args['privateendport'] = int(private_end_port)

        result = self._async_request(command='createPortForwardingRule',
                                     params=args,
                                     method='GET')
        rule = CloudStackPortForwardingRule(node,
                                            result['portforwardingrule']
                                            ['id'],
                                            address,
                                            protocol,
                                            public_port,
                                            private_port,
                                            public_end_port,
                                            private_end_port)
        node.extra['port_forwarding_rules'].append(rule)
        node.public_ips.append(address.address)
        return rule

    def ex_delete_port_forwarding_rule(self, node, rule):
        """
        Remove a Port forwarding rule.

        :param node: Node used in the rule
        :type  node: :class:`CloudStackNode`

        :param rule: Forwarding rule which should be used
        :type  rule: :class:`CloudStackPortForwardingRule`

        :rtype: ``bool``
        """

        node.extra['port_forwarding_rules'].remove(rule)
        node.public_ips.remove(rule.address.address)
        res = self._async_request(command='deletePortForwardingRule',
                                  params={'id': rule.id},
                                  method='GET')
        return res['success']

    def ex_create_ip_forwarding_rule(self, node, address, protocol,
                                     start_port, end_port=None):
        """
        "Add a NAT/firewall forwarding rule.

        :param      node: Node which should be used
        :type       node: :class:`CloudStackNode`

        :param      address: CloudStackAddress which should be used
        :type       address: :class:`CloudStackAddress`

        :param      protocol: Protocol which should be used (TCP or UDP)
        :type       protocol: ``str``

        :param      start_port: Start port which should be used
        :type       start_port: ``int``

        :param      end_port: End port which should be used
        :type       end_port: ``int``

        :rtype:     :class:`CloudStackForwardingRule`
        """

        protocol = protocol.upper()
        if protocol not in ('TCP', 'UDP'):
            return None

        args = {
            'ipaddressid': address.id,
            'protocol': protocol,
            'startport': int(start_port)
        }
        if end_port is not None:
            args['endport'] = int(end_port)

        result = self._async_request(command='createIpForwardingRule',
                                     params=args,
                                     method='GET')
        result = result['ipforwardingrule']
        rule = CloudStackIPForwardingRule(node, result['id'], address,
                                          protocol, start_port, end_port)
        node.extra['ip_forwarding_rules'].append(rule)
        return rule

    def ex_delete_ip_forwarding_rule(self, node, rule):
        """
        Remove a NAT/firewall forwarding rule.

        :param node: Node which should be used
        :type  node: :class:`CloudStackNode`

        :param rule: Forwarding rule which should be used
        :type  rule: :class:`CloudStackForwardingRule`

        :rtype: ``bool``
        """

        node.extra['ip_forwarding_rules'].remove(rule)
        self._async_request(command='deleteIpForwardingRule',
                            params={'id': rule.id},
                            method='GET')
        return True

    def ex_list_keypairs(self, **kwargs):
        """
        List Registered SSH Key Pairs

        :param     projectid: list objects by project
        :type      projectid: ``str``

        :param     page: The page to list the keypairs from
        :type      page: ``int``

        :param     keyword: List by keyword
        :type      keyword: ``str``

        :param     listall: If set to false, list only resources
                            belonging to the command's caller;
                            if set to true - list resources that
                            the caller is authorized to see.
                            Default value is false

        :type      listall: ``bool``

        :param     pagesize: The number of results per page
        :type      pagesize: ``int``

        :param     account: List resources by account.
                            Must be used with the domainId parameter
        :type      account: ``str``

        :param     isrecursive: Defaults to false, but if true,
                                lists all resources from
                                the parent specified by the
                                domainId till leaves.
        :type      isrecursive: ``bool``

        :param     fingerprint: A public key fingerprint to look for
        :type      fingerprint: ``str``

        :param     name: A key pair name to look for
        :type      name: ``str``

        :param     domainid: List only resources belonging to
                                     the domain specified
        :type      domainid: ``str``

        :return:   A list of keypair dictionaries
        :rtype:   ``list`` of ``dict``
        """
        warnings.warn('This method has been deprecated in favor of '
                      'list_key_pairs method')

        key_pairs = self.list_key_pairs(**kwargs)

        result = []

        for key_pair in key_pairs:
            item = {
                'name': key_pair.name,
                'fingerprint': key_pair.fingerprint,
                'privateKey': key_pair.private_key
            }
            result.append(item)

        return result

    def ex_create_keypair(self, name, **kwargs):
        """
        Creates a SSH KeyPair, returns fingerprint and private key

        :param     name: Name of the keypair (required)
        :type      name: ``str``

        :param     projectid: An optional project for the ssh key
        :type      projectid: ``str``

        :param     domainid: An optional domainId for the ssh key.
                             If the account parameter is used,
                             domainId must also be used.
        :type      domainid: ``str``

        :param     account: An optional account for the ssh key.
                            Must be used with domainId.
        :type      account: ``str``

        :return:   A keypair dictionary
        :rtype:    ``dict``
        """
        warnings.warn('This method has been deprecated in favor of '
                      'create_key_pair method')

        key_pair = self.create_key_pair(name=name, **kwargs)

        result = {
            'name': key_pair.name,
            'fingerprint': key_pair.fingerprint,
            'privateKey': key_pair.private_key
        }

        return result

    def ex_import_keypair_from_string(self, name, key_material):
        """
        Imports a new public key where the public key is passed in as a string

        :param     name: The name of the public key to import.
        :type      name: ``str``

        :param     key_material: The contents of a public key file.
        :type      key_material: ``str``

        :rtype: ``dict``
        """
        warnings.warn('This method has been deprecated in favor of '
                      'import_key_pair_from_string method')

        key_pair = self.import_key_pair_from_string(name=name,
                                                    key_material=key_material)
        result = {
            'keyName': key_pair.name,
            'keyFingerprint': key_pair.fingerprint
        }

        return result

    def ex_import_keypair(self, name, keyfile):
        """
        Imports a new public key where the public key is passed via a filename

        :param     name: The name of the public key to import.
        :type      name: ``str``

        :param     keyfile: The filename with path of the public key to import.
        :type      keyfile: ``str``

        :rtype: ``dict``
        """
        warnings.warn('This method has been deprecated in favor of '
                      'import_key_pair_from_file method')

        key_pair = self.import_key_pair_from_file(name=name,
                                                  key_file_path=keyfile)
        result = {
            'keyName': key_pair.name,
            'keyFingerprint': key_pair.fingerprint
        }

        return result

    def ex_delete_keypair(self, keypair, **kwargs):
        """
        Deletes an existing SSH KeyPair

        :param     keypair: Name of the keypair (required)
        :type      keypair: ``str``

        :param     projectid: The project associated with keypair
        :type      projectid: ``str``

        :param     domainid: The domain ID associated with the keypair
        :type      domainid: ``str``

        :param     account: The account associated with the keypair.
                             Must be used with the domainId parameter.
        :type      account: ``str``

        :return:   True of False based on success of Keypair deletion
        :rtype:    ``bool``
        """
        warnings.warn('This method has been deprecated in favor of '
                      'delete_key_pair method')

        key_pair = KeyPair(name=keypair, public_key=None, fingerprint=None,
                           driver=self)

        return self.delete_key_pair(key_pair=key_pair)

    def ex_list_security_groups(self, **kwargs):
        """
        Lists Security Groups

        :param domainid: List only resources belonging to the domain specified
        :type  domainid: ``str``

        :param account: List resources by account. Must be used with
                                                   the domainId parameter.
        :type  account: ``str``

        :param listall: If set to false, list only resources belonging to
                                         the command's caller; if set to true
                                         list resources that the caller is
                                         authorized to see.
                                         Default value is false
        :type  listall: ``bool``

        :param pagesize: Number of entries per page
        :type  pagesize: ``int``

        :param keyword: List by keyword
        :type  keyword: ``str``

        :param tags: List resources by tags (key/value pairs)
        :type  tags: ``dict``

        :param id: list the security group by the id provided
        :type  id: ``str``

        :param securitygroupname: lists security groups by name
        :type  securitygroupname: ``str``

        :param virtualmachineid: lists security groups by virtual machine id
        :type  virtualmachineid: ``str``

        :param projectid: list objects by project
        :type  projectid: ``str``

        :param isrecursive: (boolean) defaults to false, but if true,
                                      lists all resources from the parent
                                      specified by the domainId till leaves.
        :type  isrecursive: ``bool``

        :param page: (integer)
        :type  page: ``int``

        :rtype ``list``
        """
        extra_args = kwargs.copy()
        res = self._sync_request(command='listSecurityGroups',
                                 params=extra_args,
                                 method='GET')

        security_groups = res.get('securitygroup', [])
        return security_groups

    def ex_create_security_group(self, name, **kwargs):
        """
        Creates a new Security Group

        :param name: name of the security group (required)
        :type  name: ``str``

        :param account: An optional account for the security group.
                        Must be used with domainId.
        :type  account: ``str``

        :param domainid: An optional domainId for the security group.
                         If the account parameter is used,
                         domainId must also be used.
        :type  domainid: ``str``

        :param description: The description of the security group
        :type  description: ``str``

        :param projectid: Deploy vm for the project
        :type  projectid: ``str``

        :rtype: ``dict``
        """

        extra_args = kwargs.copy()

        for sg in self.ex_list_security_groups():
            if name in sg['name']:
                raise LibcloudError('This Security Group name already exists')

        params = {'name': name}
        params.update(extra_args)

        return self._sync_request(command='createSecurityGroup',
                                  params=params,
                                  method='GET')['securitygroup']

    def ex_delete_security_group(self, name):
        """
        Deletes a given Security Group

        :param domainid: The domain ID of account owning
                         the security group
        :type  domainid: ``str``

        :param id: The ID of the security group.
                   Mutually exclusive with name parameter
        :type  id: ``str``

        :param name: The ID of the security group.
                     Mutually exclusive with id parameter
        :type name: ``str``

        :param account: The account of the security group.
                        Must be specified with domain ID
        :type  account: ``str``

        :param projectid:  The project of the security group
        :type  projectid:  ``str``

        :rtype: ``bool``
        """

        return self._sync_request(command='deleteSecurityGroup',
                                  params={'name': name},
                                  method='GET')['success']

    def ex_authorize_security_group_ingress(self, securitygroupname,
                                            protocol, cidrlist, startport,
                                            endport=None):
        """
        Creates a new Security Group Ingress rule

        :param domainid: An optional domainId for the security group.
                         If the account parameter is used,
                         domainId must also be used.
        :type domainid: ``str``

        :param startport: Start port for this ingress rule
        :type  startport: ``int``

        :param securitygroupid: The ID of the security group.
                                Mutually exclusive with securityGroupName
                                parameter
        :type  securitygroupid: ``str``

        :param cidrlist: The cidr list associated
        :type  cidrlist: ``list``

        :param usersecuritygrouplist: user to security group mapping
        :type  usersecuritygrouplist: ``dict``

        :param securitygroupname: The name of the security group.
                                  Mutually exclusive with
                                  securityGroupName parameter
        :type  securitygroupname: ``str``

        :param account: An optional account for the security group.
                        Must be used with domainId.
        :type  account: ``str``

        :param icmpcode: Error code for this icmp message
        :type  icmpcode: ``int``

        :param protocol: TCP is default. UDP is the other supported protocol
        :type  protocol: ``str``

        :param icmptype: type of the icmp message being sent
        :type  icmptype: ``int``

        :param projectid: An optional project of the security group
        :type  projectid: ``str``

        :param endport: end port for this ingress rule
        :type  endport: ``int``

        :rtype: ``list``
        """

        protocol = protocol.upper()
        if protocol not in ('TCP', 'ICMP'):
            raise LibcloudError('Only TCP and ICMP are allowed')

        args = {
            'securitygroupname': securitygroupname,
            'protocol': protocol,
            'startport': int(startport),
            'cidrlist': cidrlist
        }
        if endport is None:
            args['endport'] = int(startport)

        return self._async_request(command='authorizeSecurityGroupIngress',
                                   params=args,
                                   method='GET')['securitygroup']

    def ex_revoke_security_group_ingress(self, rule_id):
        """
        Revoke/delete an ingress security rule

        :param id: The ID of the ingress security rule
        :type  id: ``str``

        :rtype: ``bool``
        """

        self._async_request(command='revokeSecurityGroupIngress',
                            params={'id': rule_id},
                            method='GET')
        return True

    def ex_register_iso(self, name, url, location=None, **kwargs):
        """
        Registers an existing ISO by URL.

        :param      name: Name which should be used
        :type       name: ``str``

        :param      url: Url should be used
        :type       url: ``str``

        :param      location: Location which should be used
        :type       location: :class:`NodeLocation`

        :rtype: ``str``
        """
        if location is None:
            location = self.list_locations()[0]

        params = {'name': name,
                  'displaytext': name,
                  'url': url,
                  'zoneid': location.id}
        params['bootable'] = kwargs.pop('bootable', False)
        if params['bootable']:
            os_type_id = kwargs.pop('ostypeid', None)

            if not os_type_id:
                raise LibcloudError('If bootable=True, ostypeid is required!')

            params['ostypeid'] = os_type_id

        return self._sync_request(command='registerIso',
                                  name=name,
                                  displaytext=name,
                                  url=url,
                                  zoneid=location.id,
                                  params=params)

    def ex_limits(self):
        """
        Extra call to get account's resource limits, such as
        the amount of instances, volumes, snapshots and networks.

        CloudStack uses integers as the resource type so we will convert
        them to a more human readable string using the resource map

        A list of the resource type mappings can be found at
        http://goo.gl/17C6Gk

        :return: dict
        :rtype: ``dict``
        """

        result = self._sync_request(command='listResourceLimits',
                                    method='GET')

        limits = {}
        resource_map = {
            0: 'max_instances',
            1: 'max_public_ips',
            2: 'max_volumes',
            3: 'max_snapshots',
            4: 'max_images',
            5: 'max_projects',
            6: 'max_networks',
            7: 'max_vpc',
            8: 'max_cpu',
            9: 'max_memory',
            10: 'max_primary_storage',
            11: 'max_secondary_storage'
        }

        for limit in result.get('resourcelimit', []):
            # We will ignore unknown types
            resource = resource_map.get(int(limit['resourcetype']), None)
            if not resource:
                continue
            limits[resource] = int(limit['max'])

        return limits

    def ex_create_tags(self, resource_ids, resource_type, tags):
        """
        Create tags for a resource (Node/StorageVolume/etc).
        A list of resource types can be found at http://goo.gl/6OKphH

        :param resource_ids: Resource IDs to be tagged. The resource IDs must
                             all be associated with the resource_type.
                             For example, for virtual machines (UserVm) you
                             can only specify a list of virtual machine IDs.
        :type  resource_ids: ``list`` of resource IDs

        :param resource_type: Resource type (eg: UserVm)
        :type  resource_type: ``str``

        :param tags: A dictionary or other mapping of strings to strings,
                     associating tag names with tag values.
        :type  tags: ``dict``

        :rtype: ``bool``
        """
        params = {'resourcetype': resource_type,
                  'resourceids': ','.join(resource_ids)}

        for i, key in enumerate(tags):
            params['tags[%d].key' % i] = key
            params['tags[%d].value' % i] = tags[key]

        self._async_request(command='createTags',
                            params=params,
                            method='GET')
        return True

    def ex_delete_tags(self, resource_ids, resource_type, tag_keys):
        """
        Delete tags from a resource.

        :param resource_ids: Resource IDs to be tagged. The resource IDs must
                             all be associated with the resource_type.
                             For example, for virtual machines (UserVm) you
                             can only specify a list of virtual machine IDs.
        :type  resource_ids: ``list`` of resource IDs

        :param resource_type: Resource type (eg: UserVm)
        :type  resource_type: ``str``

        :param tag_keys: A list of keys to delete. CloudStack only requires
                         the keys from the key/value pair.
        :type  tag_keys: ``list``

        :rtype: ``bool``
        """
        params = {'resourcetype': resource_type,
                  'resourceids': ','.join(resource_ids)}

        for i, key in enumerate(tag_keys):
            params['tags[%s].key' % i] = key

        self._async_request(command='deleteTags',
                            params=params,
                            method='GET')

        return True

    def _to_node(self, data, public_ips=None):
        """
        :param data: Node data object.
        :type data: ``dict``

        :param public_ips: A list of additional IP addresses belonging to
                           this node. (optional)
        :type public_ips: ``list`` or ``None``
        """
        id = data['id']

        if 'name' in data:
            name = data['name']
        elif 'displayname' in data:
            name = data['displayname']
        else:
            name = None

        state = self.NODE_STATE_MAP[data['state']]

        public_ips = public_ips if public_ips else []
        private_ips = []

        for nic in data['nic']:
            if is_private_subnet(nic['ipaddress']):
                private_ips.append(nic['ipaddress'])
            else:
                public_ips.append(nic['ipaddress'])

        security_groups = data.get('securitygroup', [])

        if security_groups:
            security_groups = [sg['name'] for sg in security_groups]

        created = data.get('created', False)

        extra = self._get_extra_dict(data,
                                     RESOURCE_EXTRA_ATTRIBUTES_MAP['node'])

        # Add additional parameters to extra
        extra['security_group'] = security_groups
        extra['ip_addresses'] = []
        extra['ip_forwarding_rules'] = []
        extra['port_forwarding_rules'] = []
        extra['created'] = created

        if 'tags' in data:
            extra['tags'] = self._get_resource_tags(data['tags'])

        node = CloudStackNode(id=id, name=name, state=state,
                              public_ips=public_ips, private_ips=private_ips,
                              driver=self, extra=extra)
        return node

    def _to_key_pairs(self, data):
        key_pairs = [self._to_key_pair(data=item) for item in data]
        return key_pairs

    def _to_key_pair(self, data):
        key_pair = KeyPair(name=data['name'],
                           fingerprint=data['fingerprint'],
                           public_key=data.get('publickey', None),
                           private_key=data.get('privatekey', None),
                           driver=self)
        return key_pair

    def _get_resource_tags(self, tag_set):
        """
        Parse tags from the provided element and return a dictionary with
        key/value pairs.

        :param      tag_set: A list of key/value tag pairs
        :type       tag_set: ``list```

        :rtype: ``dict``
        """
        tags = {}

        for tag in tag_set:
            for key, value in tag.iteritems():
                key = tag['key']
                value = tag['value']
                tags[key] = value

        return tags

    def _get_extra_dict(self, response, mapping):
        """
        Extract attributes from the element based on rules provided in the
        mapping dictionary.

        :param      response: The JSON response to parse the values from.
        :type       response: ``dict``

        :param      mapping: Dictionary with the extra layout
        :type       mapping: ``dict``

        :rtype: ``dict``
        """
        extra = {}
        for attribute, values in mapping.items():
            transform_func = values['transform_func']
            value = response.get(values['key_name'], None)

            if value is not None:
                extra[attribute] = transform_func(value)
            else:
                extra[attribute] = None

        return extra
