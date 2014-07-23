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
"""
Softlayer driver
"""

import time

from libcloud.common.base import ConnectionUserAndKey
from libcloud.common.xmlrpc import XMLRPCResponse, XMLRPCConnection
from libcloud.common.types import InvalidCredsError, LibcloudError
from libcloud.compute.types import Provider, NodeState
from libcloud.compute.base import NodeDriver, Node, NodeLocation, NodeSize, \
    NodeImage

DEFAULT_DOMAIN = 'example.com'
DEFAULT_CPU_SIZE = 1
DEFAULT_RAM_SIZE = 2048
DEFAULT_DISK_SIZE = 100

DATACENTERS = {
    'hou02': {'country': 'US'},
    'sea01': {'country': 'US', 'name': 'Seattle - West Coast U.S.'},
    'wdc01': {'country': 'US', 'name': 'Washington, DC - East Coast U.S.'},
    'dal01': {'country': 'US'},
    'dal02': {'country': 'US'},
    'dal04': {'country': 'US'},
    'dal05': {'country': 'US', 'name': 'Dallas - Central U.S.'},
    'dal06': {'country': 'US'},
    'dal07': {'country': 'US'},
    'sjc01': {'country': 'US', 'name': 'San Jose - West Coast U.S.'},
    'sng01': {'country': 'SG', 'name': 'Singapore - Southeast Asia'},
    'ams01': {'country': 'NL', 'name': 'Amsterdam - Western Europe'},
}

NODE_STATE_MAP = {
    'RUNNING': NodeState.RUNNING,
    'HALTED': NodeState.UNKNOWN,
    'PAUSED': NodeState.UNKNOWN,
    'INITIATING': NodeState.PENDING
}

SL_BASE_TEMPLATES = [
    {
        'name': '1 CPU, 1GB ram, 25GB',
        'ram': 1024,
        'disk': 25,
        'cpus': 1,
    }, {
        'name': '1 CPU, 1GB ram, 100GB',
        'ram': 1024,
        'disk': 100,
        'cpus': 1,
    }, {
        'name': '1 CPU, 2GB ram, 100GB',
        'ram': 2 * 1024,
        'disk': 100,
        'cpus': 1,
    }, {
        'name': '1 CPU, 4GB ram, 100GB',
        'ram': 4 * 1024,
        'disk': 100,
        'cpus': 1,
    }, {
        'name': '2 CPU, 2GB ram, 100GB',
        'ram': 2 * 1024,
        'disk': 100,
        'cpus': 2,
    }, {
        'name': '2 CPU, 4GB ram, 100GB',
        'ram': 4 * 1024,
        'disk': 100,
        'cpus': 2,
    }, {
        'name': '2 CPU, 8GB ram, 100GB',
        'ram': 8 * 1024,
        'disk': 100,
        'cpus': 2,
    }, {
        'name': '4 CPU, 4GB ram, 100GB',
        'ram': 4 * 1024,
        'disk': 100,
        'cpus': 4,
    }, {
        'name': '4 CPU, 8GB ram, 100GB',
        'ram': 8 * 1024,
        'disk': 100,
        'cpus': 4,
    }, {
        'name': '6 CPU, 4GB ram, 100GB',
        'ram': 4 * 1024,
        'disk': 100,
        'cpus': 6,
    }, {
        'name': '6 CPU, 8GB ram, 100GB',
        'ram': 8 * 1024,
        'disk': 100,
        'cpus': 6,
    }, {
        'name': '8 CPU, 8GB ram, 100GB',
        'ram': 8 * 1024,
        'disk': 100,
        'cpus': 8,
    }, {
        'name': '8 CPU, 16GB ram, 100GB',
        'ram': 16 * 1024,
        'disk': 100,
        'cpus': 8,
    }]

SL_TEMPLATES = {}
for i, template in enumerate(SL_BASE_TEMPLATES):
    # Add local disk templates
    local = template.copy()
    local['local_disk'] = True
    SL_TEMPLATES[i] = local


class SoftLayerException(LibcloudError):
    """
    Exception class for SoftLayer driver
    """
    pass


class SoftLayerResponse(XMLRPCResponse):
    defaultExceptionCls = SoftLayerException
    exceptions = {
        'SoftLayer_Account': InvalidCredsError,
    }


class SoftLayerConnection(XMLRPCConnection, ConnectionUserAndKey):
    responseCls = SoftLayerResponse
    host = 'api.softlayer.com'
    endpoint = '/xmlrpc/v3'

    def request(self, service, method, *args, **kwargs):
        headers = {}
        headers.update(self._get_auth_headers())
        headers.update(self._get_init_params(service, kwargs.get('id')))
        headers.update(
            self._get_object_mask(service, kwargs.get('object_mask')))
        headers.update(
            self._get_object_mask(service, kwargs.get('object_mask')))

        args = ({'headers': headers}, ) + args
        endpoint = '%s/%s' % (self.endpoint, service)

        return super(SoftLayerConnection, self).request(method, *args,
                                                        **{'endpoint':
                                                            endpoint})

    def _get_auth_headers(self):
        return {
            'authenticate': {
                'username': self.user_id,
                'apiKey': self.key
            }
        }

    def _get_init_params(self, service, id):
        if id is not None:
            return {
                '%sInitParameters' % service: {'id': id}
            }
        else:
            return {}

    def _get_object_mask(self, service, mask):
        if mask is not None:
            return {
                '%sObjectMask' % service: {'mask': mask}
            }
        else:
            return {}


class SoftLayerNodeDriver(NodeDriver):
    """
    SoftLayer node driver

    Extra node attributes:
        - password: root password
        - hourlyRecurringFee: hourly price (if applicable)
        - recurringFee      : flat rate    (if applicable)
        - recurringMonths   : The number of months in which the recurringFee
         will be incurred.
    """
    connectionCls = SoftLayerConnection
    name = 'SoftLayer'
    website = 'http://www.softlayer.com/'
    type = Provider.SOFTLAYER

    features = {'create_node': ['generates_password']}

    def _to_node(self, host):
        try:
            password = \
                host['operatingSystem']['passwords'][0]['password']
        except (IndexError, KeyError):
            password = None

        hourlyRecurringFee = host.get('billingItem', {}).get(
            'hourlyRecurringFee', 0)
        recurringFee = host.get('billingItem', {}).get('recurringFee', 0)
        recurringMonths = host.get('billingItem', {}).get('recurringMonths', 0)
        createDate = host.get('createDate', None)

        # When machine is launching it gets state halted
        # we change this to pending
        state = NODE_STATE_MAP.get(host['powerState']['keyName'],
                                   NodeState.UNKNOWN)

        if not password and state == NodeState.UNKNOWN:
            state = NODE_STATE_MAP['INITIATING']

        public_ips = []
        private_ips = []

        if 'primaryIpAddress' in host:
            public_ips.append(host['primaryIpAddress'])

        if 'primaryBackendIpAddress' in host:
            private_ips.append(host['primaryBackendIpAddress'])

        image = host.get('operatingSystem', {}).get('softwareLicense', {}) \
                    .get('softwareDescription', {}) \
                    .get('longDescription', None)

        return Node(
            id=host['id'],
            name=host['fullyQualifiedDomainName'],
            state=state,
            public_ips=public_ips,
            private_ips=private_ips,
            driver=self,
            extra={
                'hostname': host['hostname'],
                'fullyQualifiedDomainName': host['fullyQualifiedDomainName'],
                'password': password,
                'maxCpu': host.get('maxCpu', None),
                'datacenter': host.get('datacenter', {}).get('longName', None),
                'maxMemory': host.get('maxMemory', None),
                'image': image,
                'hourlyRecurringFee': hourlyRecurringFee,
                'recurringFee': recurringFee,
                'recurringMonths': recurringMonths,
                'created': createDate,
            }
        )

    def destroy_node(self, node):
        self.connection.request(
            'SoftLayer_Virtual_Guest', 'deleteObject', id=node.id
        )
        return True

    def reboot_node(self, node):
        self.connection.request(
            'SoftLayer_Virtual_Guest', 'rebootSoft', id=node.id
        )
        return True

    def ex_stop_node(self, node):
        self.connection.request(
            'SoftLayer_Virtual_Guest', 'powerOff', id=node.id
        )
        return True

    def ex_start_node(self, node):
        self.connection.request(
            'SoftLayer_Virtual_Guest', 'powerOn', id=node.id
        )
        return True

    def _get_order_information(self, node_id, timeout=1200, check_interval=5):
        mask = {
            'billingItem': '',
            'powerState': '',
            'operatingSystem': {'passwords': ''},
            'provisionDate': '',
        }

        for i in range(0, timeout, check_interval):
            res = self.connection.request(
                'SoftLayer_Virtual_Guest',
                'getObject',
                id=node_id,
                object_mask=mask
            ).object

            if res.get('provisionDate', None):
                return res

            time.sleep(check_interval)

        raise SoftLayerException('Timeout on getting node details')

    def create_node(self, **kwargs):
        """Create a new SoftLayer node

        @inherits: :class:`NodeDriver.create_node`

        :keyword    ex_domain: e.g. libcloud.org
        :type       ex_domain: ``str``
        :keyword    ex_cpus: e.g. 2
        :type       ex_cpus: ``int``
        :keyword    ex_disk: e.g. 100
        :type       ex_disk: ``int``
        :keyword    ex_ram: e.g. 2048
        :type       ex_ram: ``int``
        :keyword    ex_bandwidth: e.g. 100
        :type       ex_bandwidth: ``int``
        :keyword    ex_local_disk: e.g. True
        :type       ex_local_disk: ``bool``
        :keyword    ex_datacenter: e.g. Dal05
        :type       ex_datacenter: ``str``
        :keyword    ex_os: e.g. UBUNTU_LATEST
        :type       ex_os: ``str``
        """
        name = kwargs['name']
        os = 'DEBIAN_LATEST'
        if 'ex_os' in kwargs:
            os = kwargs['ex_os']
        elif 'image' in kwargs:
            os = kwargs['image'].id

        size = kwargs.get('size', NodeSize(id=123, name='Custom', ram=None,
                                           disk=None, bandwidth=None,
                                           price=None,
                                           driver=self.connection.driver))
        ex_size_data = SL_TEMPLATES.get(int(size.id)) or {}
        # plan keys are ints
        cpu_count = kwargs.get('ex_cpus') or ex_size_data.get('cpus') or \
            DEFAULT_CPU_SIZE
        ram = kwargs.get('ex_ram') or ex_size_data.get('ram') or \
            DEFAULT_RAM_SIZE
        bandwidth = kwargs.get('ex_bandwidth') or size.bandwidth or 10
        hourly = 'true' if kwargs.get('ex_hourly', True) else 'false'

        local_disk = 'true'
        if ex_size_data.get('local_disk') is False:
            local_disk = 'false'

        if kwargs.get('ex_local_disk') is False:
            local_disk = 'false'

        disk_size = DEFAULT_DISK_SIZE
        if size.disk:
            disk_size = size.disk
        if kwargs.get('ex_disk'):
            disk_size = kwargs.get('ex_disk')

        datacenter = ''
        if 'ex_datacenter' in kwargs:
            datacenter = kwargs['ex_datacenter']
        elif 'location' in kwargs:
            datacenter = kwargs['location'].id

        domain = kwargs.get('ex_domain')
        if domain is None:
            if name.find('.') != -1:
                domain = name[name.find('.') + 1:]
        if domain is None:
            # TODO: domain is a required argument for the Sofylayer API, but it
            # it shouldn't be.
            domain = DEFAULT_DOMAIN

        newCCI = {
            'hostname': name,
            'domain': domain,
            'startCpus': cpu_count,
            'maxMemory': ram,
            'networkComponents': [{'maxSpeed': bandwidth}],
            'hourlyBillingFlag': hourly,
            'operatingSystemReferenceCode': os,
            'localDiskFlag': local_disk,
            'blockDevices': [
                {
                    'device': '0',
                    'diskImage': {
                        'capacity': disk_size,
                    }
                }
            ]

        }

        if datacenter:
            newCCI['datacenter'] = {'name': datacenter}

        res = self.connection.request(
            'SoftLayer_Virtual_Guest', 'createObject', newCCI
        ).object

        node_id = res['id']
        raw_node = self._get_order_information(node_id)

        return self._to_node(raw_node)

    def _to_image(self, img):
        return NodeImage(
            id=img['template']['operatingSystemReferenceCode'],
            name=img['itemPrice']['item']['description'],
            driver=self.connection.driver
        )

    def list_images(self, location=None):
        result = self.connection.request(
            'SoftLayer_Virtual_Guest', 'getCreateObjectOptions'
        ).object
        return [self._to_image(i) for i in result['operatingSystems']]

    def _to_size(self, id, size):
        return NodeSize(
            id=id,
            name=size['name'],
            ram=size['ram'],
            disk=size['disk'],
            bandwidth=size.get('bandwidth'),
            price=None,
            driver=self.connection.driver,
        )

    def list_sizes(self, location=None):
        return [self._to_size(id, s) for id, s in SL_TEMPLATES.items()]

    def _to_loc(self, loc):
        country = 'UNKNOWN'
        loc_id = loc['template']['datacenter']['name']
        name = loc_id

        if loc_id in DATACENTERS:
            country = DATACENTERS[loc_id]['country']
            name = DATACENTERS[loc_id].get('name', loc_id)
        return NodeLocation(id=loc_id, name=name,
                            country=country, driver=self)

    def list_locations(self):
        res = self.connection.request(
            'SoftLayer_Virtual_Guest', 'getCreateObjectOptions'
        ).object
        return [self._to_loc(l) for l in res['datacenters']]

    def list_nodes(self):
        mask = {
            'virtualGuests': {
                'powerState': '',
                'hostname': '',
                'maxMemory': '',
                'datacenter': '',
                'operatingSystem': {'passwords': ''},
                'billingItem': '',
            },
        }
        res = self.connection.request(
            "SoftLayer_Account",
            "getVirtualGuests",
            object_mask=mask
        ).object
        return [self._to_node(h) for h in res]
