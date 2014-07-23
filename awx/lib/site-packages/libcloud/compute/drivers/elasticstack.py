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
Base driver for the providers based on the ElasticStack platform -
http://www.elasticstack.com.
"""

import re
import time
import base64

from libcloud.utils.py3 import httplib
from libcloud.utils.py3 import b

try:
    import simplejson as json
except ImportError:
    import json

from libcloud.common.base import ConnectionUserAndKey, JsonResponse
from libcloud.common.types import InvalidCredsError
from libcloud.compute.types import NodeState
from libcloud.compute.base import NodeDriver, NodeSize, Node
from libcloud.compute.base import NodeImage
from libcloud.compute.deployment import ScriptDeployment, SSHKeyDeployment
from libcloud.compute.deployment import MultiStepDeployment


NODE_STATE_MAP = {
    'active': NodeState.RUNNING,
    'dead': NodeState.TERMINATED,
    'dumped': NodeState.TERMINATED,
}

# Default timeout (in seconds) for the drive imaging process
IMAGING_TIMEOUT = 10 * 60

# ElasticStack doesn't specify special instance types, so I just specified
# some plans based on the other provider offerings.
#
# Basically for CPU any value between 500Mhz and 20000Mhz should work,
# 256MB to 8192MB for ram and 1GB to 2TB for disk.
INSTANCE_TYPES = {
    'small': {
        'id': 'small',
        'name': 'Small instance',
        'cpu': 2000,
        'memory': 1700,
        'disk': 160,
        'bandwidth': None,
    },
    'medium': {
        'id': 'medium',
        'name': 'Medium instance',
        'cpu': 3000,
        'memory': 4096,
        'disk': 500,
        'bandwidth': None,
    },
    'large': {
        'id': 'large',
        'name': 'Large instance',
        'cpu': 4000,
        'memory': 7680,
        'disk': 850,
        'bandwidth': None,
    },
    'extra-large': {
        'id': 'extra-large',
        'name': 'Extra Large instance',
        'cpu': 8000,
        'memory': 8192,
        'disk': 1690,
        'bandwidth': None,
    },
    'high-cpu-medium': {
        'id': 'high-cpu-medium',
        'name': 'High-CPU Medium instance',
        'cpu': 5000,
        'memory': 1700,
        'disk': 350,
        'bandwidth': None,
    },
    'high-cpu-extra-large': {
        'id': 'high-cpu-extra-large',
        'name': 'High-CPU Extra Large instance',
        'cpu': 20000,
        'memory': 7168,
        'disk': 1690,
        'bandwidth': None,
    },
}


class ElasticStackException(Exception):
    def __str__(self):
        return self.args[0]

    def __repr__(self):
        return "<ElasticStackException '%s'>" % (self.args[0])


class ElasticStackResponse(JsonResponse):
    def success(self):
        if self.status == 401:
            raise InvalidCredsError()

        return self.status >= 200 and self.status <= 299

    def parse_error(self):
        error_header = self.headers.get('x-elastic-error', '')
        return 'X-Elastic-Error: %s (%s)' % (error_header, self.body.strip())


class ElasticStackNodeSize(NodeSize):
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
        return (('<NodeSize: id=%s, name=%s, cpu=%s, ram=%s '
                 'disk=%s bandwidth=%s price=%s driver=%s ...>')
                % (self.id, self.name, self.cpu, self.ram,
                   self.disk, self.bandwidth, self.price, self.driver.name))


class ElasticStackBaseConnection(ConnectionUserAndKey):
    """
    Base connection class for the ElasticStack driver
    """

    host = None
    responseCls = ElasticStackResponse

    def add_default_headers(self, headers):
        headers['Accept'] = 'application/json'
        headers['Content-Type'] = 'application/json'
        headers['Authorization'] = \
            ('Basic %s' % (base64.b64encode(b('%s:%s' % (self.user_id,
                                                         self.key))))
                .decode('utf-8'))
        return headers


class ElasticStackBaseNodeDriver(NodeDriver):
    website = 'http://www.elasticstack.com'
    connectionCls = ElasticStackBaseConnection
    features = {"create_node": ["generates_password"]}

    def reboot_node(self, node):
        # Reboots the node
        response = self.connection.request(
            action='/servers/%s/reset' % (node.id),
            method='POST'
        )
        return response.status == 204

    def destroy_node(self, node):
        # Kills the server immediately
        response = self.connection.request(
            action='/servers/%s/destroy' % (node.id),
            method='POST'
        )
        return response.status == 204

    def list_images(self, location=None):
        # Returns a list of available pre-installed system drive images
        images = []
        for key, value in self._standard_drives.items():
            image = NodeImage(
                id=value['uuid'],
                name=value['description'],
                driver=self.connection.driver,
                extra={
                    'size_gunzipped': value['size_gunzipped']
                }
            )
            images.append(image)

        return images

    def list_sizes(self, location=None):
        sizes = []
        for key, value in INSTANCE_TYPES.items():
            size = ElasticStackNodeSize(
                id=value['id'],
                name=value['name'], cpu=value['cpu'], ram=value['memory'],
                disk=value['disk'], bandwidth=value['bandwidth'],
                price=self._get_size_price(size_id=value['id']),
                driver=self.connection.driver
            )
            sizes.append(size)

        return sizes

    def list_nodes(self):
        # Returns a list of active (running) nodes
        response = self.connection.request(action='/servers/info').object

        nodes = []
        for data in response:
            node = self._to_node(data)
            nodes.append(node)

        return nodes

    def create_node(self, **kwargs):
        """Creates a ElasticStack instance

        @inherits: :class:`NodeDriver.create_node`

        :keyword    name: String with a name for this new node (required)
        :type       name: ``str``

        :keyword    smp: Number of virtual processors or None to calculate
                         based on the cpu speed
        :type       smp: ``int``

        :keyword    nic_model: e1000, rtl8139 or virtio
                               (if not specified, e1000 is used)
        :type       nic_model: ``str``

        :keyword    vnc_password: If set, the same password is also used for
                                  SSH access with user toor,
                                  otherwise VNC access is disabled and
                                  no SSH login is possible.
        :type       vnc_password: ``str``
        """
        size = kwargs['size']
        image = kwargs['image']
        smp = kwargs.get('smp', 'auto')
        nic_model = kwargs.get('nic_model', 'e1000')
        vnc_password = ssh_password = kwargs.get('vnc_password', None)

        if nic_model not in ('e1000', 'rtl8139', 'virtio'):
            raise ElasticStackException('Invalid NIC model specified')

        # check that drive size is not smaller than pre installed image size

        # First we create a drive with the specified size
        drive_data = {}
        drive_data.update({'name': kwargs['name'],
                           'size': '%sG' % (kwargs['size'].disk)})

        response = self.connection.request(action='/drives/create',
                                           data=json.dumps(drive_data),
                                           method='POST').object

        if not response:
            raise ElasticStackException('Drive creation failed')

        drive_uuid = response['drive']

        # Then we image the selected pre-installed system drive onto it
        response = self.connection.request(
            action='/drives/%s/image/%s/gunzip' % (drive_uuid, image.id),
            method='POST'
        )

        if response.status not in (200, 204):
            raise ElasticStackException('Drive imaging failed')

        # We wait until the drive is imaged and then boot up the node
        # (in most cases, the imaging process shouldn't take longer
        # than a few minutes)
        response = self.connection.request(
            action='/drives/%s/info' % (drive_uuid)
        ).object

        imaging_start = time.time()
        while 'imaging' in response:
            response = self.connection.request(
                action='/drives/%s/info' % (drive_uuid)
            ).object

            elapsed_time = time.time() - imaging_start
            if ('imaging' in response and elapsed_time >= IMAGING_TIMEOUT):
                raise ElasticStackException('Drive imaging timed out')

            time.sleep(1)

        node_data = {}
        node_data.update({'name': kwargs['name'],
                          'cpu': size.cpu,
                          'mem': size.ram,
                          'ide:0:0': drive_uuid,
                          'boot': 'ide:0:0',
                          'smp': smp})
        node_data.update({'nic:0:model': nic_model, 'nic:0:dhcp': 'auto'})

        if vnc_password:
            node_data.update({'vnc': 'auto', 'vnc:password': vnc_password})

        response = self.connection.request(
            action='/servers/create', data=json.dumps(node_data),
            method='POST'
        ).object

        if isinstance(response, list):
            nodes = [self._to_node(node, ssh_password) for node in response]
        else:
            nodes = self._to_node(response, ssh_password)

        return nodes

    # Extension methods
    def ex_set_node_configuration(self, node, **kwargs):
        """
        Changes the configuration of the running server

        :param      node: Node which should be used
        :type       node: :class:`Node`

        :param      kwargs: keyword arguments
        :type       kwargs: ``dict``

        :rtype: ``bool``
        """
        valid_keys = ('^name$', '^parent$', '^cpu$', '^smp$', '^mem$',
                      '^boot$', '^nic:0:model$', '^nic:0:dhcp',
                      '^nic:1:model$', '^nic:1:vlan$', '^nic:1:mac$',
                      '^vnc:ip$', '^vnc:password$', '^vnc:tls',
                      '^ide:[0-1]:[0-1](:media)?$',
                      '^scsi:0:[0-7](:media)?$', '^block:[0-7](:media)?$')

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
            raise ElasticStackException(
                'Invalid configuration key specified: %s'
                % (',' .join(invalid_keys))
            )

        response = self.connection.request(
            action='/servers/%s/set' % (node.id), data=json.dumps(kwargs),
            method='POST'
        )

        return (response.status == httplib.OK and response.body != '')

    def deploy_node(self, **kwargs):
        """
        Create a new node, and start deployment.

        @inherits: :class:`NodeDriver.deploy_node`

        :keyword    enable_root: If true, root password will be set to
                                 vnc_password (this will enable SSH access)
                                 and default 'toor' account will be deleted.
        :type       enable_root: ``bool``
        """
        image = kwargs['image']
        vnc_password = kwargs.get('vnc_password', None)
        enable_root = kwargs.get('enable_root', False)

        if not vnc_password:
            raise ValueError('You need to provide vnc_password argument '
                             'if you want to use deployment')

        if (image in self._standard_drives and
                not self._standard_drives[image]['supports_deployment']):
            raise ValueError('Image %s does not support deployment'
                             % (image.id))

        if enable_root:
            script = ("unset HISTFILE;"
                      "echo root:%s | chpasswd;"
                      "sed -i '/^toor.*$/d' /etc/passwd /etc/shadow;"
                      "history -c") % vnc_password
            root_enable_script = ScriptDeployment(script=script,
                                                  delete=True)
            deploy = kwargs.get('deploy', None)
            if deploy:
                if (isinstance(deploy, ScriptDeployment) or
                        isinstance(deploy, SSHKeyDeployment)):
                    deployment = MultiStepDeployment([deploy,
                                                      root_enable_script])
                elif isinstance(deploy, MultiStepDeployment):
                    deployment = deploy
                    deployment.add(root_enable_script)
            else:
                deployment = root_enable_script

            kwargs['deploy'] = deployment

        if not kwargs.get('ssh_username', None):
            kwargs['ssh_username'] = 'toor'

        return super(ElasticStackBaseNodeDriver, self).deploy_node(**kwargs)

    def ex_shutdown_node(self, node):
        """
        Sends the ACPI power-down event

        :param      node: Node which should be used
        :type       node: :class:`Node`

        :rtype: ``bool``
        """
        response = self.connection.request(
            action='/servers/%s/shutdown' % (node.id),
            method='POST'
        )
        return response.status == 204

    def ex_destroy_drive(self, drive_uuid):
        """
        Deletes a drive

        :param      drive_uuid: Drive uuid which should be used
        :type       drive_uuid: ``str``

        :rtype: ``bool``
        """
        response = self.connection.request(
            action='/drives/%s/destroy' % (drive_uuid),
            method='POST'
        )
        return response.status == 204

    # Helper methods
    def _to_node(self, data, ssh_password=None):
        try:
            state = NODE_STATE_MAP[data['status']]
        except KeyError:
            state = NodeState.UNKNOWN

        if isinstance(data['nic:0:dhcp'], list):
            public_ip = data['nic:0:dhcp']
        else:
            public_ip = [data['nic:0:dhcp']]

        extra = {'cpu': data['cpu'],
                 'smp': data['smp'],
                 'mem': data['mem'],
                 'started': data['started']}

        if 'vnc:ip' in data:
            extra['vnc:ip'] = data['vnc:ip']

        if 'vnc:password' in data:
            extra['vnc:password'] = data['vnc:password']

        boot_device = data['boot']

        if isinstance(boot_device, list):
            for device in boot_device:
                extra[device] = data[device]
        else:
            extra[boot_device] = data[boot_device]

        if ssh_password:
            extra.update({'password': ssh_password})

        node = Node(id=data['server'], name=data['name'], state=state,
                    public_ips=public_ip, private_ips=None,
                    driver=self.connection.driver,
                    extra=extra)

        return node
