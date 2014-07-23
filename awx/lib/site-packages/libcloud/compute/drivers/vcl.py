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
VCL driver
"""

import time

from libcloud.common.base import ConnectionUserAndKey
from libcloud.common.xmlrpc import XMLRPCResponse, XMLRPCConnection
from libcloud.common.types import InvalidCredsError, LibcloudError
from libcloud.compute.types import Provider, NodeState
from libcloud.compute.base import NodeDriver, Node
from libcloud.compute.base import NodeSize, NodeImage


class VCLResponse(XMLRPCResponse):
    exceptions = {
        'VCL_Account': InvalidCredsError,
    }


class VCLConnection(XMLRPCConnection, ConnectionUserAndKey):
    endpoint = '/index.php?mode=xmlrpccall'

    def add_default_headers(self, headers):
        headers['X-APIVERSION'] = '2'
        headers['X-User'] = self.user_id
        headers['X-Pass'] = self.key
        return headers


class VCLNodeDriver(NodeDriver):
    """
    VCL node driver

    :keyword   host: The VCL host to which you make requests(required)
    :type      host: ``str``
    """

    NODE_STATE_MAP = {
        'ready': NodeState.RUNNING,
        'failed': NodeState.TERMINATED,
        'timedout': NodeState.TERMINATED,
        'loading': NodeState.PENDING,
        'time': NodeState.PENDING,
        'future': NodeState.PENDING,
        'error': NodeState.UNKNOWN,
        'notready': NodeState.PENDING,
        'notavailable': NodeState.TERMINATED,
        'success': NodeState.PENDING
    }

    connectionCls = VCLConnection
    name = 'VCL'
    website = 'http://incubator.apache.org/vcl/'
    type = Provider.VCL

    def __init__(self, key, secret, secure=True, host=None, port=None, *args,
                 **kwargs):
        """
        :param    key:    API key or username to used (required)
        :type     key:    ``str``

        :param    secret: Secret password to be used (required)
        :type     secret: ``str``

        :param    secure: Weither to use HTTPS or HTTP.
        :type     secure: ``bool``

        :param    host: Override hostname used for connections. (required)
        :type     host: ``str``

        :param    port: Override port used for connections.
        :type     port: ``int``

        :rtype: ``None``
        """
        if not host:
            raise Exception('When instantiating VCL driver directly ' +
                            'you also need to provide host')

        super(VCLNodeDriver, self).__init__(key, secret, secure=True,
                                            host=None, port=None, *args,
                                            **kwargs)

    def _vcl_request(self, method, *args):
        res = self.connection.request(
            method,
            *args
        ).object
        if(res['status'] == 'error'):
            raise LibcloudError(res['errormsg'], driver=self)
        return res

    def create_node(self, **kwargs):
        """Create a new VCL reservation
        size and name ignored, image is the id from list_image

        @inherits: :class:`NodeDriver.create_node`

        :keyword    image: image is the id from list_image
        :type       image: ``str``

        :keyword    start: start time as unix timestamp
        :type       start: ``str``

        :keyword    length: length of time in minutes
        :type       length: ``str``
        """

        image = kwargs["image"]
        start = kwargs.get('start', int(time.time()))
        length = kwargs.get('length', '60')

        res = self._vcl_request(
            "XMLRPCaddRequest",
            image.id,
            start,
            length
        )

        return Node(
            id=res['requestid'],
            name=image.name,
            state=self.NODE_STATE_MAP[res['status']],
            public_ips=[],
            private_ips=[],
            driver=self,
            image=image.name
        )

    def destroy_node(self, node):
        """
        End VCL reservation for the node passed in.
        Throws error if request fails.

        :param  node: The node to be destroyed
        :type   node: :class:`Node`

        :rtype: ``bool``
        """
        try:
            self._vcl_request(
                'XMLRPCendRequest',
                node.id
            )
        except LibcloudError:
            return False
        return True

    def _to_image(self, img):
        return NodeImage(
            id=img['id'],
            name=img['name'],
            driver=self.connection.driver
        )

    def list_images(self, location=None):
        """
        List images available to the user provided credentials

        @inherits: :class:`NodeDriver.list_images`
        """
        res = self.connection.request(
            "XMLRPCgetImages"
        ).object
        return [self._to_image(i) for i in res]

    def list_sizes(self, location=None):
        """
        VCL does not choosing sizes for node creation.
        Size of images are statically set by administrators.

        @inherits: :class:`NodeDriver.list_sizes`
        """
        return [NodeSize(
            't1.micro',
            'none',
            '512',
            0, 0, 0, self)
        ]

    def _to_connect_data(self, request_id, ipaddr):
        res = self._vcl_request(
            "XMLRPCgetRequestConnectData",
            request_id,
            ipaddr
        )
        return res

    def _to_status(self, requestid, imagename, ipaddr):
        res = self._vcl_request(
            "XMLRPCgetRequestStatus",
            requestid
        )

        public_ips = []
        extra = []
        if(res['status'] == 'ready'):
            cdata = self._to_connect_data(requestid, ipaddr)
            public_ips = [cdata['serverIP']]
            extra = {
                'user': cdata['user'],
                'pass': cdata['password']
            }
        return Node(
            id=requestid,
            name=imagename,
            state=self.NODE_STATE_MAP[res['status']],
            public_ips=public_ips,
            private_ips=[],
            driver=self,
            image=imagename,
            extra=extra
        )

    def _to_nodes(self, res, ipaddr):
        return [self._to_status(
            h['requestid'],
            h['imagename'],
            ipaddr
        ) for h in res]

    def list_nodes(self, ipaddr):
        """
        List nodes

        :param  ipaddr: IP address which should be used
        :type   ipaddr: ``str``

        :rtype: ``list`` of :class:`Node`
        """
        res = self._vcl_request(
            "XMLRPCgetRequestIds"
        )
        return self._to_nodes(res['requests'], ipaddr)

    def ex_update_node_access(self, node, ipaddr):
        """
        Update the remote ip accessing the node.

        :param node: the reservation node to update
        :type  node: :class:`Node`

        :param ipaddr: the ipaddr used to access the node
        :type  ipaddr: ``str``

        :return: node with updated information
        :rtype: :class:`Node`
        """
        return self._to_status(node.id, node.image, ipaddr)

    def ex_extend_request_time(self, node, minutes):
        """
        Time in minutes to extend the requested node's reservation time

        :param node: the reservation node to update
        :type  node: :class:`Node`

        :param minutes: the number of mintes to update
        :type  minutes: ``str``

        :return: true on success, throws error on failure
        :rtype: ``bool``
        """
        return self._vcl_request(
            "XMLRPCextendRequest",
            node.id,
            minutes
        )

    def ex_get_request_end_time(self, node):
        """
        Get the ending time of the node reservation.

        :param node: the reservation node to update
        :type  node: :class:`Node`

        :return: unix timestamp
        :rtype: ``int``
        """
        res = self._vcl_request(
            "XMLRPCgetRequestIds"
        )
        time = 0
        for i in res['requests']:
                if i['requestid'] == node.id:
                        time = i['end']
        return time
