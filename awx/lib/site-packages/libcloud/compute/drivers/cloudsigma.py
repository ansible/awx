# -*- coding: utf-8 -*-
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
Drivers for CloudSigma API v1.0 and v2.0.
"""

import re
import time
import copy
import base64

try:
    import simplejson as json
except:
    import json

from libcloud.utils.py3 import b
from libcloud.utils.py3 import httplib

from libcloud.utils.misc import str2dicts, str2list, dict2str
from libcloud.common.base import ConnectionUserAndKey, JsonResponse, Response
from libcloud.common.types import InvalidCredsError, ProviderError
from libcloud.common.cloudsigma import INSTANCE_TYPES
from libcloud.common.cloudsigma import API_ENDPOINTS_1_0
from libcloud.common.cloudsigma import API_ENDPOINTS_2_0
from libcloud.common.cloudsigma import DEFAULT_API_VERSION, DEFAULT_REGION
from libcloud.compute.types import NodeState, Provider
from libcloud.compute.base import NodeDriver, NodeSize, Node
from libcloud.compute.base import NodeImage
from libcloud.compute.base import is_private_subnet
from libcloud.utils.iso8601 import parse_date
from libcloud.utils.misc import get_secure_random_string

__all__ = [
    'CloudSigmaNodeDriver',
    'CloudSigma_1_0_NodeDriver',
    'CloudSigma_2_0_NodeDriver',
    'CloudSigmaError',

    'CloudSigmaNodeSize',
    'CloudSigmaDrive',
    'CloudSigmaTag',
    'CloudSigmaSubscription',
    'CloudSigmaFirewallPolicy',
    'CloudSigmaFirewallPolicyRule'
]


class CloudSigmaNodeDriver(NodeDriver):
    name = 'CloudSigma'
    website = 'http://www.cloudsigma.com/'

    def __new__(cls, key, secret=None, secure=True, host=None, port=None,
                api_version=DEFAULT_API_VERSION, **kwargs):
        if cls is CloudSigmaNodeDriver:
            if api_version == '1.0':
                cls = CloudSigma_1_0_NodeDriver
            elif api_version == '2.0':
                cls = CloudSigma_2_0_NodeDriver
            else:
                raise NotImplementedError('Unsupported API version: %s' %
                                          (api_version))
        return super(CloudSigmaNodeDriver, cls).__new__(cls)


class CloudSigmaException(Exception):
    def __str__(self):
        return self.args[0]

    def __repr__(self):
        return "<CloudSigmaException '%s'>" % (self.args[0])


class CloudSigmaInsufficientFundsException(Exception):
    def __repr__(self):
        return "<CloudSigmaInsufficientFundsException '%s'>" % (self.args[0])


class CloudSigmaNodeSize(NodeSize):
    def __init__(self, id, name, cpu, ram, disk, bandwidth, price, driver):
        self.id = id
        self.name = name
        self.cpu = cpu
        self.ram = ram
        self.disk = disk
        self.bandwidth = bandwidth
        self.price = price
        self.driver = driver

    def __repr__(self):
        return (('<NodeSize: id=%s, name=%s, cpu=%s, ram=%s disk=%s '
                 'bandwidth=%s price=%s driver=%s ...>')
                % (self.id, self.name, self.cpu, self.ram, self.disk,
                   self.bandwidth, self.price, self.driver.name))


class CloudSigma_1_0_Response(Response):
    def success(self):
        if self.status == httplib.UNAUTHORIZED:
            raise InvalidCredsError()

        return self.status >= 200 and self.status <= 299

    def parse_body(self):
        if not self.body:
            return self.body

        return str2dicts(self.body)

    def parse_error(self):
        return 'Error: %s' % (self.body.replace('errors:', '').strip())


class CloudSigma_1_0_Connection(ConnectionUserAndKey):
    host = API_ENDPOINTS_1_0[DEFAULT_REGION]['host']
    responseCls = CloudSigma_1_0_Response

    def add_default_headers(self, headers):
        headers['Accept'] = 'application/json'
        headers['Content-Type'] = 'application/json'

        headers['Authorization'] = 'Basic %s' % (base64.b64encode(
            b('%s:%s' % (self.user_id, self.key))).decode('utf-8'))
        return headers


class CloudSigma_1_0_NodeDriver(CloudSigmaNodeDriver):
    type = Provider.CLOUDSIGMA
    name = 'CloudSigma (API v1.0)'
    website = 'http://www.cloudsigma.com/'
    connectionCls = CloudSigma_1_0_Connection

    IMAGING_TIMEOUT = 20 * 60  # Default timeout (in seconds) for the drive
    # imaging process

    NODE_STATE_MAP = {
        'active': NodeState.RUNNING,
        'stopped': NodeState.TERMINATED,
        'dead': NodeState.TERMINATED,
        'dumped': NodeState.TERMINATED,
    }

    def __init__(self, key, secret=None, secure=True, host=None, port=None,
                 region=DEFAULT_REGION, **kwargs):
        if region not in API_ENDPOINTS_1_0:
            raise ValueError('Invalid region: %s' % (region))

        self._host_argument_set = host is not None
        self.api_name = 'cloudsigma_%s' % (region)
        super(CloudSigma_1_0_NodeDriver, self).__init__(key=key, secret=secret,
                                                        secure=secure,
                                                        host=host,
                                                        port=port,
                                                        region=region,
                                                        **kwargs)

    def reboot_node(self, node):
        """
        Reboot a node.

        Because Cloudsigma API does not provide native reboot call,
        it's emulated using stop and start.

        @inherits: :class:`NodeDriver.reboot_node`
        """
        node = self._get_node(node.id)
        state = node.state

        if state == NodeState.RUNNING:
            stopped = self.ex_stop_node(node)
        else:
            stopped = True

        if not stopped:
            raise CloudSigmaException(
                'Could not stop node with id %s' % (node.id))

        success = self.ex_start_node(node)

        return success

    def destroy_node(self, node):
        """
        Destroy a node (all the drives associated with it are NOT destroyed).

        If a node is still running, it's stopped before it's destroyed.

        @inherits: :class:`NodeDriver.destroy_node`
        """
        node = self._get_node(node.id)
        state = node.state

        # Node cannot be destroyed while running so it must be stopped first
        if state == NodeState.RUNNING:
            stopped = self.ex_stop_node(node)
        else:
            stopped = True

        if not stopped:
            raise CloudSigmaException(
                'Could not stop node with id %s' % (node.id))

        response = self.connection.request(
            action='/servers/%s/destroy' % (node.id),
            method='POST')
        return response.status == 204

    def list_images(self, location=None):
        """
        Return a list of available standard images (this call might take up
        to 15 seconds to return).

        @inherits: :class:`NodeDriver.list_images`
        """
        response = self.connection.request(
            action='/drives/standard/info').object

        images = []
        for value in response:
            if value.get('type'):
                if value['type'] == 'disk':
                    image = NodeImage(id=value['drive'], name=value['name'],
                                      driver=self.connection.driver,
                                      extra={'size': value['size']})
                    images.append(image)

        return images

    def list_sizes(self, location=None):
        sizes = []
        for value in INSTANCE_TYPES:
            key = value['id']
            size = CloudSigmaNodeSize(id=value['id'], name=value['name'],
                                      cpu=value['cpu'], ram=value['memory'],
                                      disk=value['disk'],
                                      bandwidth=value['bandwidth'],
                                      price=self._get_size_price(size_id=key),
                                      driver=self.connection.driver)
            sizes.append(size)

        return sizes

    def list_nodes(self):
        response = self.connection.request(action='/servers/info').object

        nodes = []
        for data in response:
            node = self._to_node(data)
            if node:
                nodes.append(node)
        return nodes

    def create_node(self, **kwargs):
        """
        Creates a CloudSigma instance

        @inherits: :class:`NodeDriver.create_node`

        :keyword    name: String with a name for this new node (required)
        :type       name: ``str``

        :keyword    smp: Number of virtual processors or None to calculate
        based on the cpu speed
        :type       smp: ``int``

        :keyword    nic_model: e1000, rtl8139 or virtio (is not specified,
        e1000 is used)
        :type       nic_model: ``str``

        :keyword    vnc_password: If not set, VNC access is disabled.
        :type       vnc_password: ``bool``

        :keyword    drive_type: Drive type (ssd|hdd). Defaults to hdd.
        :type       drive_type: ``str``
        """
        size = kwargs['size']
        image = kwargs['image']
        smp = kwargs.get('smp', 'auto')
        nic_model = kwargs.get('nic_model', 'e1000')
        vnc_password = kwargs.get('vnc_password', None)
        drive_type = kwargs.get('drive_type', 'hdd')

        if nic_model not in ['e1000', 'rtl8139', 'virtio']:
            raise CloudSigmaException('Invalid NIC model specified')

        if drive_type not in ['hdd', 'ssd']:
            raise CloudSigmaException('Invalid drive type "%s". Valid types'
                                      ' are: hdd, ssd' % (drive_type))

        drive_data = {}
        drive_data.update({'name': kwargs['name'],
                           'size': '%sG' % (kwargs['size'].disk),
                           'driveType': drive_type})

        response = self.connection.request(
            action='/drives/%s/clone' % image.id,
            data=dict2str(drive_data),
            method='POST').object

        if not response:
            raise CloudSigmaException('Drive creation failed')

        drive_uuid = response[0]['drive']

        response = self.connection.request(
            action='/drives/%s/info' % (drive_uuid)).object
        imaging_start = time.time()
        while 'imaging' in response[0]:
            response = self.connection.request(
                action='/drives/%s/info' % (drive_uuid)).object
            elapsed_time = time.time() - imaging_start
            timed_out = elapsed_time >= self.IMAGING_TIMEOUT
            if 'imaging' in response[0] and timed_out:
                raise CloudSigmaException('Drive imaging timed out')
            time.sleep(1)

        node_data = {}
        node_data.update(
            {'name': kwargs['name'], 'cpu': size.cpu, 'mem': size.ram,
             'ide:0:0': drive_uuid, 'boot': 'ide:0:0', 'smp': smp})
        node_data.update({'nic:0:model': nic_model, 'nic:0:dhcp': 'auto'})

        if vnc_password:
            node_data.update({'vnc:ip': 'auto', 'vnc:password': vnc_password})

        response = self.connection.request(action='/servers/create',
                                           data=dict2str(node_data),
                                           method='POST').object

        if not isinstance(response, list):
            response = [response]

        node = self._to_node(response[0])
        if node is None:
            # Insufficient funds, destroy created drive
            self.ex_drive_destroy(drive_uuid)
            raise CloudSigmaInsufficientFundsException(
                'Insufficient funds, node creation failed')

        # Start the node after it has been created
        started = self.ex_start_node(node)

        if started:
            node.state = NodeState.RUNNING

        return node

    def ex_destroy_node_and_drives(self, node):
        """
        Destroy a node and all the drives associated with it.

        :param      node: Node which should be used
        :type       node: :class:`libcloud.compute.base.Node`

        :rtype: ``bool``
        """
        node = self._get_node_info(node)

        drive_uuids = []
        for key, value in node.items():
            if (key.startswith('ide:') or key.startswith(
                'scsi') or key.startswith('block')) and\
                not (key.endswith(':bytes') or
                     key.endswith(':requests') or key.endswith('media')):
                drive_uuids.append(value)

        node_destroyed = self.destroy_node(self._to_node(node))

        if not node_destroyed:
            return False

        for drive_uuid in drive_uuids:
            self.ex_drive_destroy(drive_uuid)

        return True

    def ex_static_ip_list(self):
        """
        Return a list of available static IP addresses.

        :rtype: ``list`` of ``str``
        """
        response = self.connection.request(action='/resources/ip/list',
                                           method='GET')

        if response.status != 200:
            raise CloudSigmaException('Could not retrieve IP list')

        ips = str2list(response.body)
        return ips

    def ex_drives_list(self):
        """
        Return a list of all the available drives.

        :rtype: ``list`` of ``dict``
        """
        response = self.connection.request(action='/drives/info', method='GET')

        result = str2dicts(response.body)
        return result

    def ex_static_ip_create(self):
        """
        Create a new static IP address.p

        :rtype: ``list`` of ``dict``
        """
        response = self.connection.request(action='/resources/ip/create',
                                           method='GET')

        result = str2dicts(response.body)
        return result

    def ex_static_ip_destroy(self, ip_address):
        """
        Destroy a static IP address.

        :param      ip_address: IP address which should be used
        :type       ip_address: ``str``

        :rtype: ``bool``
        """
        response = self.connection.request(
            action='/resources/ip/%s/destroy' % (ip_address), method='GET')

        return response.status == 204

    def ex_drive_destroy(self, drive_uuid):
        """
        Destroy a drive with a specified uuid.
        If the drive is currently mounted an exception is thrown.

        :param      drive_uuid: Drive uuid which should be used
        :type       drive_uuid: ``str``

        :rtype: ``bool``
        """
        response = self.connection.request(
            action='/drives/%s/destroy' % (drive_uuid), method='POST')

        return response.status == 204

    def ex_set_node_configuration(self, node, **kwargs):
        """
        Update a node configuration.
        Changing most of the parameters requires node to be stopped.

        :param      node: Node which should be used
        :type       node: :class:`libcloud.compute.base.Node`

        :param      kwargs: keyword arguments
        :type       kwargs: ``dict``

        :rtype: ``bool``
        """
        valid_keys = ('^name$', '^parent$', '^cpu$', '^smp$', '^mem$',
                      '^boot$', '^nic:0:model$', '^nic:0:dhcp',
                      '^nic:1:model$', '^nic:1:vlan$', '^nic:1:mac$',
                      '^vnc:ip$', '^vnc:password$', '^vnc:tls',
                      '^ide:[0-1]:[0-1](:media)?$', '^scsi:0:[0-7](:media)?$',
                      '^block:[0-7](:media)?$')

        invalid_keys = []
        keys = list(kwargs.keys())
        for key in keys:
            matches = False
            for regex in valid_keys:
                if re.match(regex, key):
                    matches = True
                    break
            if not matches:
                invalid_keys.append(key)

        if invalid_keys:
            raise CloudSigmaException(
                'Invalid configuration key specified: %s' %
                (',' .join(invalid_keys)))

        response = self.connection.request(
            action='/servers/%s/set' % (node.id),
            data=dict2str(kwargs),
            method='POST')

        return (response.status == 200 and response.body != '')

    def ex_start_node(self, node):
        """
        Start a node.

        :param      node: Node which should be used
        :type       node: :class:`libcloud.compute.base.Node`

        :rtype: ``bool``
        """
        response = self.connection.request(
            action='/servers/%s/start' % (node.id),
            method='POST')

        return response.status == 200

    def ex_stop_node(self, node):
        """
        Stop (shutdown) a node.

        :param      node: Node which should be used
        :type       node: :class:`libcloud.compute.base.Node`

        :rtype: ``bool``
        """
        response = self.connection.request(
            action='/servers/%s/stop' % (node.id),
            method='POST')
        return response.status == 204

    def ex_shutdown_node(self, node):
        """
        Stop (shutdown) a node.

        @inherits: :class:`CloudSigmaBaseNodeDriver.ex_stop_node`
        """
        return self.ex_stop_node(node)

    def ex_destroy_drive(self, drive_uuid):
        """
        Destroy a drive.

        :param      drive_uuid: Drive uuid which should be used
        :type       drive_uuid: ``str``

        :rtype: ``bool``
        """
        response = self.connection.request(
            action='/drives/%s/destroy' % (drive_uuid),
            method='POST')
        return response.status == 204

    def _ex_connection_class_kwargs(self):
        """
        Return the host value based on the user supplied region.
        """
        kwargs = {}
        if not self._host_argument_set:
            kwargs['host'] = API_ENDPOINTS_1_0[self.region]['host']

        return kwargs

    def _to_node(self, data):
        if data:
            try:
                state = self.NODE_STATE_MAP[data['status']]
            except KeyError:
                state = NodeState.UNKNOWN

            if 'server' not in data:
                # Response does not contain server UUID if the server
                # creation failed because of insufficient funds.
                return None

            public_ips = []
            if 'nic:0:dhcp' in data:
                if isinstance(data['nic:0:dhcp'], list):
                    public_ips = data['nic:0:dhcp']
                else:
                    public_ips = [data['nic:0:dhcp']]

            extra = {}
            extra_keys = [('cpu', 'int'), ('smp', 'auto'), ('mem', 'int'),
                          ('status', 'str')]
            for key, value_type in extra_keys:
                if key in data:
                    value = data[key]

                    if value_type == 'int':
                        value = int(value)
                    elif value_type == 'auto':
                        try:
                            value = int(value)
                        except ValueError:
                            pass

                    extra.update({key: value})

            if 'vnc:ip' in data and 'vnc:password' in data:
                extra.update({'vnc_ip': data['vnc:ip'],
                              'vnc_password': data['vnc:password']})

            node = Node(id=data['server'], name=data['name'], state=state,
                        public_ips=public_ips, private_ips=None,
                        driver=self.connection.driver,
                        extra=extra)

            return node
        return None

    def _get_node(self, node_id):
        nodes = self.list_nodes()
        node = [node for node in nodes if node.id == node.id]

        if not node:
            raise CloudSigmaException(
                'Node with id %s does not exist' % (node_id))

        return node[0]

    def _get_node_info(self, node):
        response = self.connection.request(
            action='/servers/%s/info' % (node.id))

        result = str2dicts(response.body)
        return result[0]


class CloudSigmaZrhConnection(CloudSigma_1_0_Connection):
    """
    Connection class for the CloudSigma driver for the Zurich end-point
    """
    host = API_ENDPOINTS_1_0['zrh']['host']


class CloudSigmaZrhNodeDriver(CloudSigma_1_0_NodeDriver):
    """
    CloudSigma node driver for the Zurich end-point
    """
    connectionCls = CloudSigmaZrhConnection
    api_name = 'cloudsigma_zrh'


class CloudSigmaLvsConnection(CloudSigma_1_0_Connection):
    """
    Connection class for the CloudSigma driver for the Las Vegas end-point
    """
    host = API_ENDPOINTS_1_0['lvs']['host']


class CloudSigmaLvsNodeDriver(CloudSigma_1_0_NodeDriver):
    """
    CloudSigma node driver for the Las Vegas end-point
    """
    connectionCls = CloudSigmaLvsConnection
    api_name = 'cloudsigma_lvs'


class CloudSigmaError(ProviderError):
    """
    Represents CloudSigma API error.
    """

    def __init__(self, http_code, error_type, error_msg, error_point, driver):
        """
        :param http_code: HTTP status code.
        :type http_code: ``int``

        :param error_type: Type of error (validation / notexist / backend /
                           permissions  database / concurrency / billing /
                           payment)
        :type error_type: ``str``

        :param error_msg: A description of the error that occurred.
        :type error_msg: ``str``

        :param error_point: Point at which the error occurred. Can be None.
        :type error_point: ``str`` or ``None``
        """
        super(CloudSigmaError, self).__init__(http_code=http_code,
                                              value=error_msg, driver=driver)
        self.error_type = error_type
        self.error_msg = error_msg
        self.error_point = error_point


class CloudSigmaSubscription(object):
    """
    Represents CloudSigma subscription.
    """

    def __init__(self, id, resource, amount, period, status, price, start_time,
                 end_time, auto_renew, subscribed_object=None):
        """
        :param id: Subscription ID.
        :type id: ``str``

        :param resource: Resource (e.g vlan, ip, etc.).
        :type resource: ``str``

        :param period: Subscription period.
        :type period: ``str``

        :param status: Subscription status (active / inactive).
        :type status: ``str``

        :param price: Subscription price.
        :type price: ``str``

        :param start_time: Start time for this subscription.
        :type start_time: ``datetime.datetime``

        :param end_time: End time for this subscription.
        :type end_time: ``datetime.datetime``

        :param auto_renew: True if the subscription is auto renewed.
        :type auto_renew: ``bool``

        :param subscribed_object: Optional UUID of the subscribed object.
        :type subscribed_object: ``str``
        """
        self.id = id
        self.resource = resource
        self.amount = amount
        self.period = period
        self.status = status
        self.price = price
        self.start_time = start_time
        self.end_time = end_time
        self.auto_renew = auto_renew
        self.subscribed_object = subscribed_object

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return ('<CloudSigmaSubscription id=%s, resource=%s, amount=%s, '
                'period=%s, object_uuid=%s>' %
                (self.id, self.resource, self.amount, self.period,
                 self.subscribed_object))


class CloudSigmaTag(object):
    """
    Represents a CloudSigma tag object.
    """

    def __init__(self, id, name, resources=None):
        """
        :param id: Tag ID.
        :type id: ``str``

        :param name: Tag name.
        :type name: ``str``

        :param resource: IDs of resources which are associated with this tag.
        :type resources: ``list`` of ``str``
        """
        self.id = id
        self.name = name
        self.resources = resources if resources else []

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return ('<CloudSigmaTag id=%s, name=%s, resources=%s>' %
                (self.id, self.name, repr(self.resources)))


class CloudSigmaDrive(NodeImage):
    """
    Represents a CloudSigma drive.
    """

    def __init__(self, id, name, size, media, status, driver, extra=None):
        """
        :param id: Drive ID.
        :type id: ``str``

        :param name: Drive name.
        :type name: ``str``

        :param size: Drive size (in bytes).
        :type size: ``int``

        :param media: Drive media (cdrom / disk).
        :type media: ``str``

        :param status: Drive status (unmounted / mounted).
        :type status: ``str``
        """
        super(CloudSigmaDrive, self).__init__(id=id, name=name, driver=driver,
                                              extra=extra)
        self.size = size
        self.media = media
        self.status = status

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return (('<CloudSigmaSize id=%s, name=%s size=%s, media=%s, '
                'status=%s>') %
                (self.id, self.name, self.size, self.media, self.status))


class CloudSigmaFirewallPolicy(object):
    """
    Represents a CloudSigma firewall policy.
    """

    def __init__(self, id, name, rules):
        """
        :param id: Policy ID.
        :type id: ``str``

        :param name: Policy name.
        :type name: ``str``

        :param rules: Rules associated with this policy.
        :type rules: ``list`` of :class:`.CloudSigmaFirewallPolicyRule` objects
        """
        self.id = id
        self.name = name
        self.rules = rules if rules else []

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return (('<CloudSigmaFirewallPolicy id=%s, name=%s rules=%s>') %
                (self.id, self.name, repr(self.rules)))


class CloudSigmaFirewallPolicyRule(object):
    """
    Represents a CloudSigma firewall policy rule.
    """

    def __init__(self, action, direction, ip_proto=None, src_ip=None,
                 src_port=None, dst_ip=None, dst_port=None, comment=None):
        """
        :param action: Action (drop / accept).
        :type action: ``str``

        :param direction: Rule direction (in / out / both)>
        :type direction: ``str``

        :param ip_proto: IP protocol (tcp / udp).
        :type ip_proto: ``str``.

        :param src_ip: Source IP in CIDR notation.
        :type src_ip: ``str``

        :param src_port: Source port or a port range.
        :type src_port: ``str``

        :param dst_ip: Destination IP in CIDR notation.
        :type dst_ip: ``str``

        :param src_port: Destination port or a port range.
        :type src_port: ``str``

        :param comment: Comment associated with the policy.
        :type comment: ``str``
        """
        self.action = action
        self.direction = direction
        self.ip_proto = ip_proto
        self.src_ip = src_ip
        self.src_port = src_port
        self.dst_ip = dst_ip
        self.dst_port = dst_port
        self.comment = comment

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return (('<CloudSigmaFirewallPolicyRule action=%s, direction=%s>') %
                (self.action, self.direction))


class CloudSigma_2_0_Response(JsonResponse):
    success_status_codes = [
        httplib.OK,
        httplib.ACCEPTED,
        httplib.NO_CONTENT,
        httplib.CREATED
    ]

    def success(self):
        return self.status in self.success_status_codes

    def parse_error(self):
        if int(self.status) == httplib.UNAUTHORIZED:
            raise InvalidCredsError('Invalid credentials')

        body = self.parse_body()
        errors = self._parse_errors_from_body(body=body)

        if errors:
            # Throw first error
            raise errors[0]

        return body

    def _parse_errors_from_body(self, body):
        """
        Parse errors from the response body.

        :return: List of error objects.
        :rtype: ``list`` of :class:`.CloudSigmaError` objects
        """
        errors = []

        if not isinstance(body, list):
            return None

        for item in body:
            if 'error_type' not in item:
                # Unrecognized error
                continue

            error = CloudSigmaError(http_code=self.status,
                                    error_type=item['error_type'],
                                    error_msg=item['error_message'],
                                    error_point=item['error_point'],
                                    driver=self.connection.driver)
            errors.append(error)

        return errors


class CloudSigma_2_0_Connection(ConnectionUserAndKey):
    host = API_ENDPOINTS_2_0[DEFAULT_REGION]['host']
    responseCls = CloudSigma_2_0_Response
    api_prefix = '/api/2.0'

    def add_default_headers(self, headers):
        headers['Accept'] = 'application/json'
        headers['Content-Type'] = 'application/json'

        headers['Authorization'] = 'Basic %s' % (base64.b64encode(
            b('%s:%s' % (self.user_id, self.key))).decode('utf-8'))
        return headers

    def encode_data(self, data):
        data = json.dumps(data)
        return data

    def request(self, action, params=None, data=None, headers=None,
                method='GET', raw=False):
        params = params or {}
        action = self.api_prefix + action

        if method == 'GET':
            params['limit'] = 0  # we want all the items back

        return super(CloudSigma_2_0_Connection, self).request(action=action,
                                                              params=params,
                                                              data=data,
                                                              headers=headers,
                                                              method=method,
                                                              raw=raw)


class CloudSigma_2_0_NodeDriver(CloudSigmaNodeDriver):
    """
    Driver for CloudSigma API v2.0.
    """
    name = 'CloudSigma (API v2.0)'
    api_name = 'cloudsigma_zrh'
    website = 'http://www.cloudsigma.com/'
    connectionCls = CloudSigma_2_0_Connection

    # Default drive transition timeout in seconds
    DRIVE_TRANSITION_TIMEOUT = 500

    # How long to sleep between different polling periods while waiting for
    # drive transition
    DRIVE_TRANSITION_SLEEP_INTERVAL = 5

    NODE_STATE_MAP = {
        'starting': NodeState.PENDING,
        'stopping': NodeState.PENDING,
        'unavailable': NodeState.PENDING,
        'running': NodeState.RUNNING,
        'stopped': NodeState.STOPPED,
        'paused': NodeState.STOPPED
    }

    def __init__(self, key, secret, secure=True, host=None, port=None,
                 region=DEFAULT_REGION, **kwargs):
        if region not in API_ENDPOINTS_2_0:
            raise ValueError('Invalid region: %s' % (region))

        if not secure:
            # CloudSigma drive uses Basic Auth authentication and we don't want
            # to allow user to accidentally send credentials over the wire in
            # plain-text
            raise ValueError('CloudSigma driver only supports a '
                             'secure connection')

        self._host_argument_set = host is not None
        super(CloudSigma_2_0_NodeDriver, self).__init__(key=key, secret=secret,
                                                        secure=secure,
                                                        host=host, port=port,
                                                        region=region,
                                                        **kwargs)

    def list_nodes(self, ex_tag=None):
        """
        List available nodes.

        :param ex_tag: If specified, only return servers tagged with the
                       provided tag.
        :type ex_tag: :class:`CloudSigmaTag`
        """
        if ex_tag:
            action = '/tags/%s/servers/detail/' % (ex_tag.id)
        else:
            action = '/servers/detail/'

        response = self.connection.request(action=action, method='GET').object
        nodes = [self._to_node(data=item) for item in response['objects']]
        return nodes

    def list_sizes(self):
        """
        List available sizes.
        """
        sizes = []
        for value in INSTANCE_TYPES:
            key = value['id']
            size = CloudSigmaNodeSize(id=value['id'], name=value['name'],
                                      cpu=value['cpu'], ram=value['memory'],
                                      disk=value['disk'],
                                      bandwidth=value['bandwidth'],
                                      price=self._get_size_price(size_id=key),
                                      driver=self.connection.driver)
            sizes.append(size)

        return sizes

    def list_images(self):
        """
        Return a list of available pre-installed library drives.

        Note: If you want to list all the available library drives (both
        pre-installed and installation CDs), use :meth:`ex_list_library_drives`
        method.
        """
        response = self.connection.request(action='/libdrives/').object
        images = [self._to_image(data=item) for item in response['objects']]

        # We filter out non pre-installed library drives by default because
        # they can't be used directly following a default Libcloud server
        # creation flow.
        images = [image for image in images if
                  image.extra['image_type'] == 'preinst']
        return images

    def create_node(self, name, size, image, ex_metadata=None,
                    ex_vnc_password=None, ex_avoid=None, ex_vlan=None):
        """
        Create a new server.

        Server creation consists multiple steps depending on the type of the
        image used.

        1. Installation CD:

            1. Create a server and attach installation cd
            2. Start a server

        2. Pre-installed image:

            1. Clone provided library drive so we can use it
            2. Resize cloned drive to the desired size
            3. Create a server and attach cloned drive
            4. Start a server

        :param ex_metadata: Key / value pairs to associate with the
                            created node. (optional)
        :type ex_metadata: ``dict``

        :param ex_vnc_password: Password to use for VNC access. If not
                                provided, random password is generated.
        :type ex_vnc_password: ``str``

        :param ex_avoid: A list of server UUIDs to avoid when starting this
                         node. (optional)
        :type ex_avoid: ``list``

        :param ex_vlan: Optional UUID of a VLAN network to use. If specified,
                        server will have two nics assigned - 1 with a public ip
                        and 1 with the provided VLAN.
        :type ex_vlan: ``str``
        """
        is_installation_cd = self._is_installation_cd(image=image)

        if ex_vnc_password:
            vnc_password = ex_vnc_password
        else:
            # VNC password is not provided, generate a random one.
            vnc_password = get_secure_random_string(size=12)

        drive_name = '%s-drive' % (name)

        # size is specified in GB
        drive_size = (size.disk * 1024 * 1024 * 1024)

        if not is_installation_cd:
            # 1. Clone library drive so we can use it
            drive = self.ex_clone_drive(drive=image, name=drive_name)

            # Wait for drive clone to finish
            drive = self._wait_for_drive_state_transition(drive=drive,
                                                          state='unmounted')

            # 2. Resize drive to the desired disk size if the desired disk size
            # is larger than the cloned drive size.
            if drive_size > drive.size:
                drive = self.ex_resize_drive(drive=drive, size=drive_size)

            # Wait for drive resize to finish
            drive = self._wait_for_drive_state_transition(drive=drive,
                                                          state='unmounted')
        else:
            # No need to clone installation CDs
            drive = image

        # 3. Create server and attach cloned drive
        # ide 0:0
        data = {}
        data['name'] = name
        data['cpu'] = size.cpu
        data['mem'] = (size.ram * 1024 * 1024)
        data['vnc_password'] = vnc_password

        if ex_metadata:
            data['meta'] = ex_metadata

        # Assign 1 public interface (DHCP) to the node
        nic = {
            'boot_order': None,
            'ip_v4_conf': {
                'conf': 'dhcp',
            },
            'ip_v6_conf': None
        }

        nics = [nic]

        if ex_vlan:
            # Assign another interface for VLAN
            nic = {
                'boot_order': None,
                'ip_v4_conf': None,
                'ip_v6_conf': None,
                'vlan': ex_vlan
            }
            nics.append(nic)

        # Need to use IDE for installation CDs
        if is_installation_cd:
            device_type = 'ide'
        else:
            device_type = 'virtio'

        drive = {
            'boot_order': 1,
            'dev_channel': '0:0',
            'device': device_type,
            'drive': drive.id
        }

        drives = [drive]

        data['nics'] = nics
        data['drives'] = drives

        action = '/servers/'
        response = self.connection.request(action=action, method='POST',
                                           data=data)
        node = self._to_node(response.object['objects'][0])

        # 4. Start server
        self.ex_start_node(node=node, ex_avoid=ex_avoid)

        return node

    def destroy_node(self, node):
        """
        Destroy the node and all the associated drives.

        :return: ``True`` on success, ``False`` otherwise.
        :rtype: ``bool``
        """
        action = '/servers/%s/' % (node.id)
        params = {'recurse': 'all_drives'}
        response = self.connection.request(action=action, method='DELETE',
                                           params=params)
        return response.status == httplib.NO_CONTENT

    # Server extension methods

    def ex_edit_node(self, node, params):
        """
        Edit a node.

        :param node: Node to edit.
        :type node: :class:`libcloud.compute.base.Node`

        :param params: Node parameters to update.
        :type params: ``dict``

        :return Edited node.
        :rtype: :class:`libcloud.compute.base.Node`
        """
        data = {}

        # name, cpu, mem and vnc_password attributes must always be present so
        # we just copy them from the to-be-edited node
        data['name'] = node.name
        data['cpu'] = node.extra['cpu']
        data['mem'] = node.extra['mem']
        data['vnc_password'] = node.extra['vnc_password']

        nics = copy.deepcopy(node.extra.get('nics', []))

        data['nics'] = nics

        data.update(params)

        action = '/servers/%s/' % (node.id)
        response = self.connection.request(action=action, method='PUT',
                                           data=data).object
        node = self._to_node(data=response)
        return node

    def ex_start_node(self, node, ex_avoid=None):
        """
        Start a node.

        :param node: Node to start.
        :type node: :class:`libcloud.compute.base.Node`

        :param ex_avoid: A list of other server uuids to avoid when
                         starting this node. If provided, node will
                         attempt to be started on a different
                         physical infrastructure from other servers
                         specified using this argument. (optional)
        :type ex_avoid: ``list``
        """
        params = {}

        if ex_avoid:
            params['avoid'] = ','.join(ex_avoid)

        path = '/servers/%s/action/' % (node.id)
        response = self._perform_action(path=path, action='start',
                                        params=params,
                                        method='POST')
        return response.status == httplib.ACCEPTED

    def ex_stop_node(self, node):
        """
        Stop a node.
        """
        path = '/servers/%s/action/' % (node.id)
        response = self._perform_action(path=path, action='stop',
                                        method='POST')
        return response.status == httplib.ACCEPTED

    def ex_clone_node(self, node, name=None, random_vnc_password=None):
        """
        Clone the provided node.

        :param name: Optional name for the cloned node.
        :type name: ``str``
        :param random_vnc_password: If True, a new random VNC password will be
                                    generated for the cloned node. Otherwise
                                    password from the cloned node will be
                                    reused.
        :type random_vnc_password: ``bool``

        :return: Cloned node.
        :rtype: :class:`libcloud.compute.base.Node`
        """
        data = {}

        data['name'] = name
        data['random_vnc_password'] = random_vnc_password

        path = '/servers/%s/action/' % (node.id)
        response = self._perform_action(path=path, action='clone',
                                        method='POST', data=data).object
        node = self._to_node(data=response)
        return node

    def ex_open_vnc_tunnel(self, node):
        """
        Open a VNC tunnel to the provided node and return the VNC url.

        :param node: Node to open the VNC tunnel to.
        :type node: :class:`libcloud.compute.base.Node`

        :return: URL of the opened VNC tunnel.
        :rtype: ``str``
        """
        path = '/servers/%s/action/' % (node.id)
        response = self._perform_action(path=path, action='open_vnc',
                                        method='POST').object
        vnc_url = response['vnc_url']
        return vnc_url

    def ex_close_vnc_tunnel(self, node):
        """
        Close a VNC server to the provided node.

        :param node: Node to close the VNC tunnel to.
        :type node: :class:`libcloud.compute.base.Node`

        :return: ``True`` on success, ``False`` otherwise.
        :rtype: ``bool``
        """
        path = '/servers/%s/action/' % (node.id)
        response = self._perform_action(path=path, action='close_vnc',
                                        method='POST')
        return response.status == httplib.ACCEPTED

    # Drive extension methods

    def ex_list_library_drives(self):
        """
        Return a list of all the available library drives (pre-installed and
        installation CDs).

        :rtype: ``list`` of :class:`.CloudSigmaDrive` objects
        """
        response = self.connection.request(action='/libdrives/').object
        drives = [self._to_drive(data=item) for item in response['objects']]
        return drives

    def ex_list_user_drives(self):
        """
        Return a list of all the available user's drives.

        :rtype: ``list`` of :class:`.CloudSigmaDrive` objects
        """
        response = self.connection.request(action='/drives/detail/').object
        drives = [self._to_drive(data=item) for item in response['objects']]
        return drives

    def ex_create_drive(self, name, size, media='disk', ex_avoid=None):
        """
        Create a new drive.

        :param name: Drive name.
        :type name: ``str``

        :param size: Drive size in bytes.
        :type size: ``int``

        :param media: Drive media type (cdrom, disk).
        :type media: ``str``

        :param ex_avoid: A list of other drive uuids to avoid when
                         creating this drive. If provided, drive will
                         attempt to be created on a different
                         physical infrastructure from other drives
                         specified using this argument. (optional)
        :type ex_avoid: ``list``

        :return: Created drive object.
        :rtype: :class:`.CloudSigmaDrive`
        """
        params = {}
        data = {
            'name': name,
            'size': size,
            'media': media
        }

        if ex_avoid:
            params['avoid'] = ','.join(ex_avoid)

        action = '/drives/'
        response = self.connection.request(action=action, method='POST',
                                           params=params, data=data).object
        drive = self._to_drive(data=response['objects'][0])
        return drive

    def ex_clone_drive(self, drive, name=None, ex_avoid=None):
        """
        Clone a library or a standard drive.

        :param drive: Drive to clone.
        :type drive: :class:`libcloud.compute.base.NodeImage` or
                     :class:`.CloudSigmaDrive`

        :param name: Optional name for the cloned drive.
        :type name: ``str``

        :param ex_avoid: A list of other drive uuids to avoid when
                         creating this drive. If provided, drive will
                         attempt to be created on a different
                         physical infrastructure from other drives
                         specified using this argument. (optional)
        :type ex_avoid: ``list``

        :return: New cloned drive.
        :rtype: :class:`.CloudSigmaDrive`
        """
        params = {}
        data = {}

        if ex_avoid:
            params['avoid'] = ','.join(ex_avoid)

        if name:
            data['name'] = name

        path = '/drives/%s/action/' % (drive.id)
        response = self._perform_action(path=path, action='clone',
                                        params=params, data=data,
                                        method='POST')
        drive = self._to_drive(data=response.object['objects'][0])
        return drive

    def ex_resize_drive(self, drive, size):
        """
        Resize a drive.

        :param drive: Drive to resize.

        :param size: New drive size in bytes.
        :type size: ``int``

        :return: Drive object which is being resized.
        :rtype: :class:`.CloudSigmaDrive`
        """
        path = '/drives/%s/action/' % (drive.id)
        data = {'name': drive.name, 'size': size, 'media': 'disk'}
        response = self._perform_action(path=path, action='resize',
                                        method='POST', data=data)

        drive = self._to_drive(data=response.object['objects'][0])
        return drive

    def ex_attach_drive(self, node):
        """
        Attach a drive to the provided node.
        """
        # TODO
        pass

    def ex_get_drive(self, drive_id):
        """
        Retrieve information about a single drive.

        :param drive_id: ID of the drive to retrieve.
        :type drive_id: ``str``

        :return: Drive object.
        :rtype: :class:`.CloudSigmaDrive`
        """
        action = '/drives/%s/' % (drive_id)
        response = self.connection.request(action=action).object
        drive = self._to_drive(data=response)
        return drive

    # Firewall policies extension methods

    def ex_list_firewall_policies(self):
        """
        List firewall policies.

        :rtype: ``list`` of :class:`.CloudSigmaFirewallPolicy`
        """
        action = '/fwpolicies/detail/'
        response = self.connection.request(action=action, method='GET').object
        policies = [self._to_firewall_policy(data=item) for item
                    in response['objects']]
        return policies

    def ex_create_firewall_policy(self, name, rules=None):
        """
        Create a firewall policy.

        :param name: Policy name.
        :type name: ``str``

        :param rules: List of firewall policy rules to associate with this
                      policy. (optional)
        :type rules: ``list`` of ``dict``

        :return: Created firewall policy object.
        :rtype: :class:`.CloudSigmaFirewallPolicy`
        """
        data = {}
        obj = {}
        obj['name'] = name

        if rules:
            obj['rules'] = rules

        data['objects'] = [obj]

        action = '/fwpolicies/'
        response = self.connection.request(action=action, method='POST',
                                           data=data).object
        policy = self._to_firewall_policy(data=response['objects'][0])
        return policy

    def ex_attach_firewall_policy(self, policy, node, nic_mac=None):
        """
        Attach firewall policy to a public NIC interface on the server.

        :param policy: Firewall policy to attach.
        :type policy: :class:`.CloudSigmaFirewallPolicy`

        :param node: Node to attach policy to.
        :type node: :class:`libcloud.compute.base.Node`

        :param nic_mac: Optional MAC address of the NIC to add the policy to.
                        If not specified, first public interface is used
                        instead.
        :type nic_mac: ``str``

        :return: Node object to which the policy was attached to.
        :rtype: :class:`libcloud.compute.base.Node`
        """
        nics = copy.deepcopy(node.extra.get('nics', []))

        if nic_mac:
            nic = [n for n in nics if n['mac'] == nic_mac]
        else:
            nic = nics

        if len(nic) == 0:
            raise ValueError('Cannot find the NIC interface to attach '
                             'a policy to')

        nic = nic[0]
        nic['firewall_policy'] = policy.id

        params = {'nics': nics}
        node = self.ex_edit_node(node=node, params=params)
        return node

    def ex_delete_firewall_policy(self, policy):
        """
        Delete a firewall policy.

        :param policy: Policy to delete to.
        :type policy: :class:`.CloudSigmaFirewallPolicy`

        :return: ``True`` on success, ``False`` otherwise.
        :rtype: ``bool``
        """
        action = '/fwpolicies/%s/' % (policy.id)
        response = self.connection.request(action=action, method='DELETE')
        return response.status == httplib.NO_CONTENT

    # Availability groups extension methods

    def ex_list_servers_availability_groups(self):
        """
        Return which running servers share the same physical compute host.

        :return: A list of server UUIDs which share the same physical compute
                 host. Servers which share the same host will be stored under
                 the same list index.
        :rtype: ``list`` of ``list``
        """
        action = '/servers/availability_groups/'
        response = self.connection.request(action=action, method='GET')
        return response.object

    def ex_list_drives_availability_groups(self):
        """
        Return which drives share the same physical storage host.

        :return: A list of drive UUIDs which share the same physical storage
                 host. Drives which share the same host will be stored under
                 the same list index.
        :rtype: ``list`` of ``list``
        """
        action = '/drives/availability_groups/'
        response = self.connection.request(action=action, method='GET')
        return response.object

    # Tag extension methods

    def ex_list_tags(self):
        """
        List all the available tags.

        :rtype: ``list`` of :class:`.CloudSigmaTag` objects
        """
        action = '/tags/detail/'
        response = self.connection.request(action=action, method='GET').object
        tags = [self._to_tag(data=item) for item in response['objects']]

        return tags

    def ex_get_tag(self, tag_id):
        """
        Retrieve a single tag.

        :param tag_id: ID of the tag to retrieve.
        :type tag_id: ``str``

        :rtype: ``list`` of :class:`.CloudSigmaTag` objects
        """
        action = '/tags/%s/' % (tag_id)
        response = self.connection.request(action=action, method='GET').object
        tag = self._to_tag(data=response)
        return tag

    def ex_create_tag(self, name, resource_uuids=None):
        """
        Create a tag.

        :param name: Tag name.
        :type name: ``str``

        :param resource_uuids: Optional list of resource UUIDs to assign this
                               tag go.
        :type resource_uuids: ``list`` of ``str``

        :return: Created tag object.
        :rtype: :class:`.CloudSigmaTag`
        """
        data = {}
        data['objects'] = [
            {
                'name': name
            }
        ]

        if resource_uuids:
            data['resources'] = resource_uuids

        action = '/tags/'
        response = self.connection.request(action=action, method='POST',
                                           data=data).object
        tag = self._to_tag(data=response['objects'][0])
        return tag

    def ex_tag_resource(self, resource, tag):
        """
        Associate tag with the provided resource.

        :param resource: Resource to associate a tag with.
        :type resource: :class:`libcloud.compute.base.Node` or
                        :class:`.CloudSigmaDrive`

        :param tag: Tag to associate with the resources.
        :type tag: :class:`.CloudSigmaTag`

        :return: Updated tag object.
        :rtype: :class:`.CloudSigmaTag`
        """
        if not hasattr(resource, 'id'):
            raise ValueError('Resource doesn\'t have id attribute')

        return self.ex_tag_resources(resources=[resource], tag=tag)

    def ex_tag_resources(self, resources, tag):
        """
        Associate tag with the provided resources.

        :param resources: Resources to associate a tag with.
        :type resources: ``list`` of :class:`libcloud.compute.base.Node` or
                        :class:`.CloudSigmaDrive`

        :param tag: Tag to associate with the resources.
        :type tag: :class:`.CloudSigmaTag`

        :return: Updated tag object.
        :rtype: :class:`.CloudSigmaTag`
        """

        resources = tag.resources[:]

        for resource in resources:
            if not hasattr(resource, 'id'):
                raise ValueError('Resource doesn\'t have id attribute')

            resources.append(resource.id)

        resources = list(set(resources))

        data = {
            'name': tag.name,
            'resources': resources
        }

        action = '/tags/%s/' % (tag.id)
        response = self.connection.request(action=action, method='PUT',
                                           data=data).object
        tag = self._to_tag(data=response)
        return tag

    def ex_delete_tag(self, tag):
        """
        Delete a tag.

        :param tag: Tag to delete.
        :type tag: :class:`.CloudSigmaTag`

        :return: ``True`` on success, ``False`` otherwise.
        :rtype: ``bool``
        """
        action = '/tags/%s/' % (tag.id)
        response = self.connection.request(action=action, method='DELETE')
        return response.status == httplib.NO_CONTENT

    # Account extension methods

    def ex_get_balance(self):
        """
        Retrueve account balance information.

        :return: Dictionary with two items ("balance" and "currency").
        :rtype: ``dict``
        """
        action = '/balance/'
        response = self.connection.request(action=action, method='GET')
        return response.object

    def ex_get_pricing(self):
        """
        Retrive pricing information that are applicable to the cloud.

        :return: Dictionary with pricing information.
        :rtype: ``dict``
        """
        action = '/pricing/'
        response = self.connection.request(action=action, method='GET')
        return response.object

    def ex_get_usage(self):
        """
        Retrieve account current usage information.

        :return: Dictionary with two items ("balance" and "usage").
        :rtype: ``dict``
        """
        action = '/currentusage/'
        response = self.connection.request(action=action, method='GET')
        return response.object

    def ex_list_subscriptions(self, status='all', resources=None):
        """
        List subscriptions for this account.

        :param status: Only return subscriptions with the provided status
                       (optional).
        :type status: ``str``
        :param resources: Only return subscriptions for the provided resources
                          (optional).
        :type resources: ``list``

        :rtype: ``list``
        """
        params = {}

        if status:
            params['status'] = status

        if resources:
            params['resource'] = ','.join(resources)

        response = self.connection.request(action='/subscriptions/',
                                           params=params).object
        subscriptions = self._to_subscriptions(data=response)
        return subscriptions

    def ex_toggle_subscription_auto_renew(self, subscription):
        """
        Toggle subscription auto renew status.

        :param subscription: Subscription to toggle the auto renew flag for.
        :type subscription: :class:`.CloudSigmaSubscription`

        :return: ``True`` on success, ``False`` otherwise.
        :rtype: ``bool``
        """
        path = '/subscriptions/%s/action/' % (subscription.id)
        response = self._perform_action(path=path, action='auto_renew',
                                        method='POST')
        return response.status == httplib.OK

    def ex_create_subscription(self, amount, period, resource,
                               auto_renew=False):
        """
        Create a new subscription.

        :param amount: Subscription amount. For example, in dssd case this
                       would be disk size in gigabytes.
        :type amount: ``int``

        :param period: Subscription period. For example: 30 days, 1 week, 1
                                            month, ...
        :type period: ``str``

        :param resource: Resource the purchase the subscription for.
        :type resource: ``str``

        :param auto_renew: True to automatically renew the subscription.
        :type auto_renew: ``bool``
        """
        data = [
            {
                'amount': amount,
                'period': period,
                'auto_renew': auto_renew,
                'resource': resource
            }
        ]

        response = self.connection.request(action='/subscriptions/',
                                           data=data, method='POST')
        data = response.object['objects'][0]
        subscription = self._to_subscription(data=data)
        return subscription

    # Misc extension methods

    def ex_list_capabilities(self):
        """
        Retrieve all the basic and sensible limits of the API.

        :rtype: ``dict``
        """
        action = '/capabilities/'
        response = self.connection.request(action=action,
                                           method='GET')
        capabilities = response.object
        return capabilities

    def _parse_ips_from_nic(self, nic):
        """
        Parse private and public IP addresses from the provided network
        interface object.

        :param nic: NIC object.
        :type nic: ``dict``

        :return: (public_ips, private_ips) tuple.
        :rtype: ``tuple``
        """
        public_ips, private_ips = [], []

        ipv4_conf = nic['ip_v4_conf']
        ipv6_conf = nic['ip_v6_conf']

        ipv4 = ipv4_conf['ip'] if ipv4_conf else None
        ipv6 = ipv6_conf['ip'] if ipv6_conf else None

        ips = []

        if ipv4:
            ips.append(ipv4)

        if ipv6:
            ips.append(ipv6)

        runtime = nic['runtime']

        ip_v4 = runtime['ip_v4'] if nic['runtime'] else None
        ip_v6 = runtime['ip_v6'] if nic['runtime'] else None

        ipv4 = ip_v4['uuid'] if ip_v4 else None
        ipv6 = ip_v4['uuid'] if ip_v6 else None

        if ipv4:
            ips.append(ipv4)

        if ipv6:
            ips.append(ipv6)

        ips = set(ips)

        for ip in ips:
            if is_private_subnet(ip):
                private_ips.append(ip)
            else:
                public_ips.append(ip)

        return public_ips, private_ips

    def _to_node(self, data):
        extra_keys = ['cpu', 'mem', 'nics', 'vnc_password', 'meta']

        id = data['uuid']
        name = data['name']
        state = self.NODE_STATE_MAP.get(data['status'], NodeState.UNKNOWN)

        public_ips = []
        private_ips = []
        extra = self._extract_values(obj=data, keys=extra_keys)

        for nic in data['nics']:
            _public_ips, _private_ips = self._parse_ips_from_nic(nic=nic)

            public_ips.extend(_public_ips)
            private_ips.extend(_private_ips)

        node = Node(id=id, name=name, state=state, public_ips=public_ips,
                    private_ips=private_ips, driver=self, extra=extra)
        return node

    def _to_image(self, data):
        extra_keys = ['description', 'arch', 'image_type', 'os', 'licenses',
                      'media', 'meta']

        id = data['uuid']
        name = data['name']
        extra = self._extract_values(obj=data, keys=extra_keys)

        image = NodeImage(id=id, name=name, driver=self, extra=extra)
        return image

    def _to_drive(self, data):
        id = data['uuid']
        name = data['name']
        size = data['size']
        media = data['media']
        status = data['status']
        extra = {}

        drive = CloudSigmaDrive(id=id, name=name, size=size, media=media,
                                status=status, driver=self, extra=extra)

        return drive

    def _to_tag(self, data):
        resources = data['resources']
        resources = [resource['uuid'] for resource in resources]

        tag = CloudSigmaTag(id=data['uuid'], name=data['name'],
                            resources=resources)
        return tag

    def _to_subscriptions(self, data):
        subscriptions = []

        for item in data['objects']:
            subscription = self._to_subscription(data=item)
            subscriptions.append(subscription)

        return subscriptions

    def _to_subscription(self, data):
        start_time = parse_date(data['start_time'])
        end_time = parse_date(data['end_time'])
        obj_uuid = data['subscribed_object']

        subscription = CloudSigmaSubscription(id=data['id'],
                                              resource=data['resource'],
                                              amount=int(data['amount']),
                                              period=data['period'],
                                              status=data['status'],
                                              price=data['price'],
                                              start_time=start_time,
                                              end_time=end_time,
                                              auto_renew=data['auto_renew'],
                                              subscribed_object=obj_uuid)
        return subscription

    def _to_firewall_policy(self, data):
        rules = []

        for item in data.get('rules', []):
            rule = CloudSigmaFirewallPolicyRule(action=item['action'],
                                                direction=item['direction'],
                                                ip_proto=item['ip_proto'],
                                                src_ip=item['src_ip'],
                                                src_port=item['src_port'],
                                                dst_ip=item['dst_ip'],
                                                dst_port=item['dst_port'],
                                                comment=item['comment'])
            rules.append(rule)

        policy = CloudSigmaFirewallPolicy(id=data['uuid'], name=data['name'],
                                          rules=rules)
        return policy

    def _perform_action(self, path, action, method='POST', params=None,
                        data=None):
        """
        Perform API action and return response object.
        """
        if params:
            params = params.copy()
        else:
            params = {}

        params['do'] = action
        response = self.connection.request(action=path, method=method,
                                           params=params, data=data)
        return response

    def _is_installation_cd(self, image):
        """
        Detect if the provided image is an installation CD.

        :rtype: ``bool``
        """
        if isinstance(image, CloudSigmaDrive) and image.media == 'cdrom':
            return True

        return False

    def _extract_values(self, obj, keys):
        """
        Extract values from a dictionary and return a new dictionary with
        extracted values.

        :param obj: Dictionary to extract values from.
        :type obj: ``dict``

        :param keys: Keys to extract.
        :type keys: ``list``

        :return: Dictionary with extracted values.
        :rtype: ``dict``
        """
        result = {}

        for key in keys:
            result[key] = obj[key]

        return result

    def _wait_for_drive_state_transition(self, drive, state,
                                         timeout=DRIVE_TRANSITION_TIMEOUT):
        """
        Wait for a drive to transition to the provided state.

        Note: This function blocks and periodically calls "GET drive" endpoint
        to check if the drive has already transitioned to the desired state.

        :param drive: Drive to wait for.
        :type drive: :class:`.CloudSigmaDrive`

        :param state: Desired drive state.
        :type state: ``str``

        :param timeout: How long to wait for the transition (in seconds) before
                        timing out.
        :type timeout: ``int``

        :return: Drive object.
        :rtype: :class:`.CloudSigmaDrive`
        """

        start_time = time.time()

        while drive.status != state:
            drive = self.ex_get_drive(drive_id=drive.id)

            if drive.status == state:
                break

            current_time = time.time()
            delta = (current_time - start_time)

            if delta >= timeout:
                msg = ('Timed out while waiting for drive transition '
                       '(timeout=%s seconds)' % (timeout))
                raise Exception(msg)

            time.sleep(self.DRIVE_TRANSITION_SLEEP_INTERVAL)

        return drive

    def _ex_connection_class_kwargs(self):
        """
        Return the host value based on the user supplied region.
        """
        kwargs = {}

        if not self._host_argument_set:
            kwargs['host'] = API_ENDPOINTS_2_0[self.region]['host']

        return kwargs
