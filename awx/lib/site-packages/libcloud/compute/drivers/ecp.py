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
Enomaly ECP driver
"""
import time
import base64
import os
import socket
import binascii

from libcloud.utils.py3 import httplib
from libcloud.utils.py3 import b

# JSON is included in the standard library starting with Python 2.6.  For 2.5
# and 2.4, there's a simplejson egg at: http://pypi.python.org/pypi/simplejson
try:
    import simplejson as json
except ImportError:
    import json

from libcloud.common.base import Response, ConnectionUserAndKey
from libcloud.compute.base import NodeDriver, NodeSize, NodeLocation
from libcloud.compute.base import NodeImage, Node
from libcloud.compute.types import Provider, NodeState, InvalidCredsError
from libcloud.utils.networking import is_private_subnet

# Defaults
API_HOST = ''
API_PORT = (80, 443)


class ECPResponse(Response):
    def success(self):
        if self.status == httplib.OK or self.status == httplib.CREATED:
            try:
                j_body = json.loads(self.body)
            except ValueError:
                self.error = "JSON response cannot be decoded."
                return False
            if j_body['errno'] == 0:
                return True
            else:
                self.error = "ECP error: %s" % j_body['message']
                return False
        elif self.status == httplib.UNAUTHORIZED:
            raise InvalidCredsError()
        else:
            self.error = "HTTP Error Code: %s" % self.status
        return False

    def parse_error(self):
        return self.error

    # Interpret the json responses - no error checking required
    def parse_body(self):
        return json.loads(self.body)

    def getheaders(self):
        return self.headers


class ECPConnection(ConnectionUserAndKey):
    """
    Connection class for the Enomaly ECP driver
    """

    responseCls = ECPResponse
    host = API_HOST
    port = API_PORT

    def add_default_headers(self, headers):
        # Authentication
        username = self.user_id
        password = self.key
        base64string = base64.encodestring(
            b('%s:%s' % (username, password)))[:-1]
        authheader = "Basic %s" % base64string
        headers['Authorization'] = authheader

        return headers

    def _encode_multipart_formdata(self, fields):
        """
        Based on Wade Leftwich's function:
        http://code.activestate.com/recipes/146306/
        """
        # use a random boundary that does not appear in the fields
        boundary = ''
        while boundary in ''.join(fields):
            boundary = binascii.hexlify(os.urandom(16)).decode('utf-8')
        L = []
        for i in fields:
            L.append('--' + boundary)
            L.append('Content-Disposition: form-data; name="%s"' % i)
            L.append('')
            L.append(fields[i])
        L.append('--' + boundary + '--')
        L.append('')
        body = '\r\n'.join(L)
        content_type = 'multipart/form-data; boundary=%s' % boundary
        header = {'Content-Type': content_type}
        return header, body


class ECPNodeDriver(NodeDriver):
    """
    Enomaly ECP node driver
    """

    name = "Enomaly Elastic Computing Platform"
    website = 'http://www.enomaly.com/'
    type = Provider.ECP
    connectionCls = ECPConnection

    def list_nodes(self):
        """
        Returns a list of all running Nodes

        :rtype: ``list`` of :class:`Node`
        """

        # Make the call
        res = self.connection.request('/rest/hosting/vm/list').parse_body()

        # Put together a list of node objects
        nodes = []
        for vm in res['vms']:
            node = self._to_node(vm)
            if node is not None:
                nodes.append(node)

        # And return it
        return nodes

    def _to_node(self, vm):
        """
        Turns a (json) dictionary into a Node object.
        This returns only running VMs.
        """

        # Check state
        if not vm['state'] == "running":
            return None

        # IPs
        iplist = [interface['ip'] for interface in vm['interfaces'] if
                  interface['ip'] != '127.0.0.1']

        public_ips = []
        private_ips = []
        for ip in iplist:
            try:
                socket.inet_aton(ip)
            except socket.error:
                # not a valid ip
                continue
            if is_private_subnet(ip):
                private_ips.append(ip)
            else:
                public_ips.append(ip)

        # Create the node object
        n = Node(
            id=vm['uuid'],
            name=vm['name'],
            state=NodeState.RUNNING,
            public_ips=public_ips,
            private_ips=private_ips,
            driver=self,
        )

        return n

    def reboot_node(self, node):
        """
        Shuts down a VM and then starts it again.

        @inherits: :class:`NodeDriver.reboot_node`
        """

        # Turn the VM off
        # Black magic to make the POST requests work
        d = self.connection._encode_multipart_formdata({'action': 'stop'})
        self.connection.request(
            '/rest/hosting/vm/%s' % node.id,
            method='POST',
            headers=d[0],
            data=d[1]
        ).parse_body()

        node.state = NodeState.REBOOTING
        # Wait for it to turn off and then continue (to turn it on again)
        while node.state == NodeState.REBOOTING:
            # Check if it's off.
            response = self.connection.request(
                '/rest/hosting/vm/%s' % node.id
            ).parse_body()
            if response['vm']['state'] == 'off':
                node.state = NodeState.TERMINATED
            else:
                time.sleep(5)

        # Turn the VM back on.
        # Black magic to make the POST requests work
        d = self.connection._encode_multipart_formdata({'action': 'start'})
        self.connection.request(
            '/rest/hosting/vm/%s' % node.id,
            method='POST',
            headers=d[0],
            data=d[1]
        ).parse_body()

        node.state = NodeState.RUNNING
        return True

    def destroy_node(self, node):
        """
        Shuts down and deletes a VM.

        @inherits: :class:`NodeDriver.destroy_node`
        """

        # Shut down first
        # Black magic to make the POST requests work
        d = self.connection._encode_multipart_formdata({'action': 'stop'})
        self.connection.request(
            '/rest/hosting/vm/%s' % node.id,
            method='POST',
            headers=d[0],
            data=d[1]
        ).parse_body()

        # Ensure there was no applicationl level error
        node.state = NodeState.PENDING
        # Wait for the VM to turn off before continuing
        while node.state == NodeState.PENDING:
            # Check if it's off.
            response = self.connection.request(
                '/rest/hosting/vm/%s' % node.id
            ).parse_body()
            if response['vm']['state'] == 'off':
                node.state = NodeState.TERMINATED
            else:
                time.sleep(5)

        # Delete the VM
        # Black magic to make the POST requests work
        d = self.connection._encode_multipart_formdata({'action': 'delete'})
        self.connection.request(
            '/rest/hosting/vm/%s' % (node.id),
            method='POST',
            headers=d[0],
            data=d[1]
        ).parse_body()

        return True

    def list_images(self, location=None):
        """
        Returns a list of all package templates aka appiances aka images.

        @inherits: :class:`NodeDriver.list_images`
        """

        # Make the call
        response = self.connection.request(
            '/rest/hosting/ptemplate/list').parse_body()

        # Turn the response into an array of NodeImage objects
        images = []
        for ptemplate in response['packages']:
            images.append(NodeImage(
                id=ptemplate['uuid'],
                name='%s: %s' % (ptemplate['name'], ptemplate['description']),
                driver=self,)
            )

        return images

    def list_sizes(self, location=None):
        """
        Returns a list of all hardware templates

        @inherits: :class:`NodeDriver.list_sizes`
        """

        # Make the call
        response = self.connection.request(
            '/rest/hosting/htemplate/list').parse_body()

        # Turn the response into an array of NodeSize objects
        sizes = []
        for htemplate in response['templates']:
            sizes.append(NodeSize(
                id=htemplate['uuid'],
                name=htemplate['name'],
                ram=htemplate['memory'],
                disk=0,  # Disk is independent of hardware template.
                bandwidth=0,  # There is no way to keep track of bandwidth.
                price=0,  # The billing system is external.
                driver=self,)
            )

        return sizes

    def list_locations(self):
        """
        This feature does not exist in ECP. Returns hard coded dummy location.

        :rtype: ``list`` of :class:`NodeLocation`
        """
        return [NodeLocation(id=1,
                             name="Cloud",
                             country='',
                             driver=self),
                ]

    def create_node(self, **kwargs):
        """
        Creates a virtual machine.

        :keyword    name:   String with a name for this new node (required)
        :type       name:   ``str``

        :keyword    size:   The size of resources allocated to this node .
                            (required)
        :type       size:   :class:`NodeSize`

        :keyword    image:  OS Image to boot on node. (required)
        :type       image:  :class:`NodeImage`

        :rtype: :class:`Node`
        """

        # Find out what network to put the VM on.
        res = self.connection.request(
            '/rest/hosting/network/list').parse_body()

        # Use the first / default network because there is no way to specific
        # which one
        network = res['networks'][0]['uuid']

        # Prepare to make the VM
        data = {
            'name': str(kwargs['name']),
            'package': str(kwargs['image'].id),
            'hardware': str(kwargs['size'].id),
            'network_uuid': str(network),
            'disk': ''
        }

        # Black magic to make the POST requests work
        d = self.connection._encode_multipart_formdata(data)
        response = self.connection.request(
            '/rest/hosting/vm/',
            method='PUT',
            headers=d[0],
            data=d[1]
        ).parse_body()

        # Create a node object and return it.
        n = Node(
            id=response['machine_id'],
            name=data['name'],
            state=NodeState.PENDING,
            public_ips=[],
            private_ips=[],
            driver=self,
        )

        return n
