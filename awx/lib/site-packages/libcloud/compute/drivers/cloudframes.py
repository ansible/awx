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
CloudFrames Driver

"""

# (name, ram, disk, bandwidth, price, vcpus)
SIZES = [
    ('512mb_1core_10gb', 512, 10, 512, 0.025, 1),
    ('1024mb_1core_20gb', 1024, 20, 512, 0.05, 1),
    ('2048mb_2core_50gb', 2048, 50, 1024, 0.10, 2),
    ('4096mb_2core_100gb', 4096, 100, 2048, 0.20, 2),
    ('8192mb_4core_200gb', 8192, 200, 2048, 0.40, 4),
    ('16384mb_4core_400gb', 16384, 400, 4096, 0.80, 4),
]

import base64
import random

from libcloud.utils.py3 import urlparse, b
from libcloud.common.base import ConnectionKey
from libcloud.common.xmlrpc import XMLRPCResponse, XMLRPCConnection
from libcloud.common.types import ProviderError
from libcloud.compute.base import NodeImage, NodeSize, Node, NodeLocation
from libcloud.compute.base import NodeDriver
from libcloud.compute.types import Provider, NodeState


class CloudFramesException(ProviderError):
    pass


class CloudFramesComponent(object):
    """
    Represents a node in the cloudapi path.
    """

    def __init__(self, cloudFramesConnection, name):
        self.cloudFramesConnection = cloudFramesConnection
        self.name = name

    def __getattr__(self, key):
        return self.method(key)

    def method(self, methodname):
        def foo(*args, **kwargs):
            async = kwargs.get('async', False)
            args = list(args)
            args.append('')                                 # jobguid
            args.append({'wait': False} if async else {})   # executionparams
            response = self.cloudFramesConnection.request(
                'cloud_api_%s.%s' % (self.name, methodname), *args)
            if not response.success():
                response.parse_error()
            if async:
                return response.parse_body()['jobguid']
            else:
                return response.parse_body()['result']
        return foo


class CloudFramesNodeSize(NodeSize):

    def __init__(self, id, name, ram, disk, bandwidth, price, driver,
                 vcpus=None):
        super(CloudFramesNodeSize, self).__init__(
            id, name, ram, disk, bandwidth, price, driver)
        self.vcpus = vcpus


class CloudFramesNode(Node):

    def list_snapshots(self):
        return self.driver.ex_list_snapshots(self)

    def snapshot(self, label='', description=''):
        return self.driver.ex_snapshot_node(self, label, description)

    def rollback(self, snapshot):
        return self.driver.ex_rollback_node(self, snapshot)


class CloudFramesSnapshot(object):

    def __init__(self, id, timestamp, label, description, driver):
        self.id = id
        self.timestamp = timestamp
        self.label = label
        self.description = description
        self.driver = driver

    def destroy(self):
        self.driver.ex_destroy_snapshot(self)


class CloudFramesConnection(XMLRPCConnection, ConnectionKey):
    """
    Cloudapi connection class
    """

    repsonseCls = XMLRPCResponse
    base_url = None

    def __init__(self, key=None, secret=None, secure=True,
                 host=None, port=None, url=None, timeout=None):
        """
        :param    key:    The username to connect with to the cloudapi
        :type     key:    ``str``

        :param    secret: The password to connect with to the cloudapi
        :type     secret: ``str``

        :param    secure: Should always be false at the moment
        :type     secure: ``bool``

        :param    host:   The hostname of the cloudapi
        :type     host:   ``str``

        :param    port:   The port on which to connect to the cloudapi
        :type     port:   ``int``

        :param    url:    Url to the cloudapi (can replace all above)
        :type     url:    ``str``
        """

        super(CloudFramesConnection, self).__init__(key=key, secure=secure,
                                                    host=host, port=port,
                                                    url=url, timeout=timeout)
        self._auth = base64.b64encode(
            b('%s:%s' % (key, secret))).decode('utf-8')
        self.endpoint = url

    def __getattr__(self, key):
        return CloudFramesComponent(self, key)

    def add_default_headers(self, headers):
        headers['Authorization'] = 'Basic %s' % self._auth
        return headers


class CloudFramesNodeDriver(NodeDriver):
    """
    CloudFrames node driver
    """

    connectionCls = CloudFramesConnection

    name = 'CloudFrames'
    api_name = 'cloudframes'
    website = 'http://www.cloudframes.net/'
    type = Provider.CLOUDFRAMES

    NODE_STATE_MAP = {
        'CONFIGURED': NodeState.PENDING,
        'CREATED': NodeState.PENDING,
        'DELETING': NodeState.PENDING,
        'HALTED': NodeState.TERMINATED,
        'IMAGEONLY': NodeState.UNKNOWN,
        'ISCSIEXPOSED': NodeState.PENDING,
        'MOVING': NodeState.PENDING,
        'OVERLOADED': NodeState.UNKNOWN,
        'PAUSED': NodeState.TERMINATED,
        'RUNNING': NodeState.RUNNING,
        'STARTING': NodeState.PENDING,
        'STOPPING': NodeState.PENDING,
        'SYNCING': NodeState.PENDING,
        'TODELETE': NodeState.PENDING,
    }

    # subclassed internal methods
    def __init__(self, key=None, secret=None, secure=True,
                 host=None, port=None, url=None, **kwargs):
        if not port:
            port = 443 if secure else 80
        if url:
            if not url.endswith('/'):
                url += '/'
            scheme, netloc, _, _, _, _ = urlparse.urlparse(url)
            secure = (scheme == 'https')
            if '@' in netloc:
                auth, hostport = netloc.rsplit('@', 1)
                if ':' in auth:
                    key, secret = auth.split(':', 1)
                else:
                    key = auth
            else:
                hostport = netloc
            if ':' in hostport:
                host, port = hostport.split(':')
            else:
                host = hostport
                hostport = '%s:%s' % (host, port)
            url = url.replace(netloc, hostport)
        else:
            url = '%s://%s:%s/appserver/xmlrpc/' % (
                'https' if secure else 'http', host, port)

        if secure:
            raise NotImplementedError(
                'The cloudapi only supports unsecure connections')

        if key is None or secret is None:
            raise NotImplementedError(
                'Unauthenticated support to the cloudapi is not supported')

        # connection url
        self._url = url

        # cached attributes
        self.__cloudspaceguid = None
        self.__languid = None
        self.__locations = []

        super(CloudFramesNodeDriver, self).__init__(
            key, secret, secure, host, port, **kwargs)

    def _ex_connection_class_kwargs(self):
        return {'url': self._url}

    # internal methods
    @property
    def _cloudspaceguid(self):
        if not self.__cloudspaceguid:
            self.__cloudspaceguid = self.connection.cloudspace.find(
                '', '', 'cloud', '')[0]
        return self.__cloudspaceguid

    @property
    def _languid(self):
        if not self.__languid:
            self.__languid = self.connection.lan.find(
                '', '', 'public_virtual', '', '', '', '', '', '', '', '', '',
                '', '', '', '', '')[0]
        return self.__languid

    def _get_machine_data(self, guid):
        """
        Looks up some basic data related to the given machine guid.
        """
        try:
            d = self.connection.machine.list('', '', '', guid, '')[0]
        except IndexError:
            raise CloudFramesException('VM no longer exists', 404, self)
        d['public_ips'] = []
        d['private_ips'] = []
        d['size'] = None
        d['image'] = None
        return d

    def _machine_find(self, template=False, machinetype=None,
                      machinerole=None):
        # the cloudframes xmlrpc api requires you to pass all args and kwargs
        # as positional arguments, you can't use keywords arguments
        if not machinetype:
            guids = []
            for machinetype in ['VIRTUALSERVER', 'VIRTUALDESKTOP']:
                guids += self.connection.machine.find(
                    '', '', '', '', '', '', '', '', '', '', '', '', '', '', '',
                    '', '', machinetype, template, '', '', '', '', '', '', '',
                    '', '', '', '', '', '', '')
        else:
            guids = self.connection.machine.find(
                '', '', '', '', '', '', '', '', '', '', '', '', '', '', '',
                '', '', machinetype, '', '', '', '', '', '', '', '',
                machinerole, '', '', '', '', '', '')
        return guids

    def _to_image(self, image_dict):
        return NodeImage(id=image_dict['guid'],
                         name=image_dict['name'],
                         driver=self.connection.driver)

    def _to_size(self, id, name, ram, disk, bandwidth, price, vcpus):
        return CloudFramesNodeSize(
            id, name, ram, disk, bandwidth, price, self, vcpus)

    def _to_location(self, location_dict):
        return NodeLocation(id=location_dict['guid'],
                            name=location_dict['name'],
                            country=None,
                            driver=self)

    def _to_node(self, node_dict):
        # only return nodes which can be worked with
        # (ignore cloudframes internal autotests and deleted nodes)
        if node_dict['status'] == 'CONFIGURED':
            return None
        return CloudFramesNode(id=node_dict['guid'],
                               name=node_dict['name'],
                               state=self.NODE_STATE_MAP.get(
                                   node_dict['status'], NodeState.UNKNOWN),
                               public_ips=node_dict['public_ips'],
                               private_ips=node_dict['private_ips'],
                               driver=self.connection.driver,
                               size=node_dict['size'],
                               image=node_dict['image'],
                               extra={})

    def _to_snapshot(self, snapshot_dict):
        return CloudFramesSnapshot(id=snapshot_dict['guid'],
                                   timestamp=snapshot_dict['timestamp'],
                                   label=snapshot_dict['backuplabel'],
                                   description=snapshot_dict['description'],
                                   driver=self)

    # subclassed public methods, and provider specific public methods
    def list_images(self, location=None):
        image_ids = self._machine_find(template=True)
        image_list = []
        for image_id in image_ids:
            image_list.append(self._to_image(self._get_machine_data(image_id)))
        return image_list

    def list_sizes(self, location=None):
        sizes = []
        for id in range(len(SIZES)):
            sizes.append(self._to_size(id, *SIZES[id]))
        return sizes

    def list_locations(self, ex_use_cached=True):
        if not self.__locations or not ex_use_cached:
            self.__locations = []
            for location_id in self._machine_find(machinetype='PHYSICAL',
                                                  machinerole='COMPUTENODE'):
                self.__locations.append(
                    self._to_location(self._get_machine_data(location_id)))
        return self.__locations

    def list_nodes(self):
        node_ids = self._machine_find()
        node_list = []
        for node_id in node_ids:
            node = self._to_node(self._get_machine_data(node_id))
            if node:
                node_list.append(node)
        return node_list

    def create_node(self, **kwargs):
        """
        Creates a new node, by cloning the template provided.

        If no location object is passed, a random location will be used.


        :param   image:           The template to be cloned (required)
        :type    image:           ``list`` of :class:`NodeImage`

        :param   name:            The name for the new node (required)
        :type    name:            ``str``

        :param   size:            The size of the new node (required)
        :type    size:            ``list`` of :class:`NodeSize`

        :param   location:        The location to create the new node
        :type    location:        ``list`` of :class:`NodeLocation`

        :param   default_gateway: The default gateway to be used
        :type    default_gateway: ``str``

        :param   extra:           Additional requirements (extra disks fi.)
        :type    extra:           ``dict``


        :returns: ``list`` of :class:`Node` -- The newly created Node object

        :raises: CloudFramesException
        """

        additionalinfo = kwargs.get('extra', {})
        additionalinfo.update({
            'memory': kwargs['size'].ram,
            'cpu': kwargs['size'].vcpus,
        })
        guid = self.connection.machine.createFromTemplate(
            self._cloudspaceguid, kwargs['image'].id, kwargs['name'],
            [{'languid': self._languid}], kwargs['name'],
            kwargs.get('location', random.choice(self.list_locations())).id,
            kwargs.get('default_gateway', ''), None, additionalinfo)
        if not self.connection.machine.start(guid):
            raise CloudFramesException(
                'failed to start machine after creation', 500, self)
        return self._to_node(self._get_machine_data(guid))

    def destroy_node(self, node):
        return self.connection.machine.delete(node.id, False)

    def reboot_node(self, node, ex_clean=True):
        return self.connection.machine.reboot(node.id, ex_clean)

    def ex_snapshot_node(self, node, label='', description=''):
        guid = self.connection.machine.snapshot(
            node.id, label, description, False, False, 'PAUSED')
        for snapshot in self.ex_list_snapshots(node):
            if snapshot.id == guid:
                return snapshot
        else:
            raise CloudFramesException('Snapshot creation failed', 500, self)

    def ex_rollback_node(self, node, snapshot):
        if not node.state == NodeState.TERMINATED:
            self.connection.machine.stop(node.id, False, 930)
        success = self.connection.machine.rollback(node.id, snapshot.id)
        self.connection.machine.start(node.id)
        return success

    def ex_list_snapshots(self, node):
        return [self._to_snapshot(snapshot_dict) for snapshot_dict in
                self.connection.machine.listSnapshots(node.id, False, '', '')]

    def ex_destroy_snapshot(self, node, snapshot):
        return self.connection.machine.delete(snapshot.id, False)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
