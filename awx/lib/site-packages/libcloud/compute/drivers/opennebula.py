# Copyright 2002-2009, Distributed Systems Architecture Group, Universidad
# Complutense de Madrid (dsa-research.org)
#
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
OpenNebula.org driver.
"""

__docformat__ = 'epytext'

from base64 import b64encode
import hashlib

try:
    from lxml import etree as ET
except ImportError:
    from xml.etree import ElementTree as ET

from libcloud.utils.py3 import httplib
from libcloud.utils.py3 import next
from libcloud.utils.py3 import b

from libcloud.compute.base import NodeState, NodeDriver, Node, NodeLocation
from libcloud.common.base import ConnectionUserAndKey, XmlResponse
from libcloud.compute.base import NodeImage, NodeSize, StorageVolume
from libcloud.common.types import InvalidCredsError
from libcloud.compute.providers import Provider

__all__ = [
    'ACTION',
    'OpenNebulaResponse',
    'OpenNebulaConnection',
    'OpenNebulaNodeSize',
    'OpenNebulaNetwork',
    'OpenNebulaNodeDriver',
    'OpenNebula_1_4_NodeDriver',
    'OpenNebula_2_0_NodeDriver',
    'OpenNebula_3_0_NodeDriver',
    'OpenNebula_3_2_NodeDriver',
    'OpenNebula_3_8_NodeDriver']

API_HOST = ''
API_PORT = (4567, 443)
API_SECURE = True
API_PLAIN_AUTH = False
DEFAULT_API_VERSION = '3.2'


class ACTION(object):
    """
    All actions, except RESUME, only apply when the VM is in the "Running"
    state.
    """

    STOP = 'STOPPED'
    """
    The VM is stopped, and its memory state stored to a checkpoint file. VM
    state, and disk image, are transferred back to the front-end. Resuming
    the VM requires the VM instance to be re-scheduled.
    """

    SUSPEND = 'SUSPENDED'
    """
    The VM is stopped, and its memory state stored to a checkpoint file. The VM
    state, and disk image, are left on the host to be resumed later. Resuming
    the VM does not require the VM to be re-scheduled. Rather, after
    suspending, the VM resources are reserved for later resuming.
    """

    RESUME = 'RESUME'
    """
    The VM is resumed using the saved memory state from the checkpoint file,
    and the VM's disk image. The VM is either started immediately, or
    re-scheduled depending on how it was suspended.
    """

    CANCEL = 'CANCEL'
    """
    The VM is forcibly shutdown, its memory state is deleted. If a persistent
    disk image was used, that disk image is transferred back to the front-end.
    Any non-persistent disk images are deleted.
    """

    SHUTDOWN = 'SHUTDOWN'
    """
    The VM is gracefully shutdown by sending the ACPI signal. If the VM does
    not shutdown, then it is considered to still be running. If successfully,
    shutdown, its memory state is deleted. If a persistent disk image was used,
    that disk image is transferred back to the front-end. Any non-persistent
    disk images are deleted.
    """

    REBOOT = 'REBOOT'
    """
    Introduced in OpenNebula v3.2.

    The VM is gracefully restarted by sending the ACPI signal.
    """

    DONE = 'DONE'
    """
    The VM is forcibly shutdown, its memory state is deleted. If a persistent
    disk image was used, that disk image is transferred back to the front-end.
    Any non-persistent disk images are deleted.
    """


class OpenNebulaResponse(XmlResponse):
    """
    XmlResponse class for the OpenNebula.org driver.
    """

    def success(self):
        """
        Check if response has the appropriate HTTP response code to be a
        success.

        :rtype:  ``bool``
        :return: True is success, else False.
        """
        i = int(self.status)
        return i >= 200 and i <= 299

    def parse_error(self):
        """
        Check if response contains any errors.

        @raise: :class:`InvalidCredsError`

        :rtype:  :class:`ElementTree`
        :return: Contents of HTTP response body.
        """
        if int(self.status) == httplib.UNAUTHORIZED:
            raise InvalidCredsError(self.body)
        return self.body


class OpenNebulaConnection(ConnectionUserAndKey):
    """
    Connection class for the OpenNebula.org driver.
    with plain_auth support
    """

    host = API_HOST
    port = API_PORT
    secure = API_SECURE
    plain_auth = API_PLAIN_AUTH
    responseCls = OpenNebulaResponse

    def __init__(self, *args, **kwargs):
        if 'plain_auth' in kwargs:
            self.plain_auth = kwargs.pop('plain_auth')
        super(OpenNebulaConnection, self).__init__(*args, **kwargs)

    def add_default_headers(self, headers):
        """
        Add headers required by the OpenNebula.org OCCI interface.

        Includes adding Basic HTTP Authorization headers for authenticating
        against the OpenNebula.org OCCI interface.

        :type  headers: ``dict``
        :param headers: Dictionary containing HTTP headers.

        :rtype:  ``dict``
        :return: Dictionary containing updated headers.
        """
        if self.plain_auth:
            passwd = self.key
        else:
            passwd = hashlib.sha1(b(self.key)).hexdigest()
        headers['Authorization'] =\
            ('Basic %s' % b64encode(b('%s:%s' % (self.user_id,
                                                 passwd))).decode('utf-8'))
        return headers


class OpenNebulaNodeSize(NodeSize):
    """
    NodeSize class for the OpenNebula.org driver.
    """

    def __init__(self, id, name, ram, disk, bandwidth, price, driver,
                 cpu=None, vcpu=None):
        super(OpenNebulaNodeSize, self).__init__(id=id, name=name, ram=ram,
                                                 disk=disk,
                                                 bandwidth=bandwidth,
                                                 price=price, driver=driver)
        self.cpu = cpu
        self.vcpu = vcpu

    def __repr__(self):
        return (('<OpenNebulaNodeSize: id=%s, name=%s, ram=%s, disk=%s, '
                 'bandwidth=%s, price=%s, driver=%s, cpu=%s, vcpu=%s ...>')
                % (self.id, self.name, self.ram, self.disk, self.bandwidth,
                   self.price, self.driver.name, self.cpu, self.vcpu))


class OpenNebulaNetwork(object):
    """
    Provide a common interface for handling networks of all types.

    Network objects are analogous to physical switches connecting two or
    more physical nodes together. The Network object provides the interface in
    libcloud through which we can manipulate networks in different cloud
    providers in the same way. Network objects don't actually do much directly
    themselves, instead the network driver handles the connection to the
    network.

    You don't normally create a network object yourself; instead you use
    a driver and then have that create the network for you.

    >>> from libcloud.compute.drivers.dummy import DummyNodeDriver
    >>> driver = DummyNodeDriver()
    >>> network = driver.create_network()
    >>> network = driver.list_networks()[0]
    >>> network.name
    'dummy-1'
    """

    def __init__(self, id, name, address, size, driver, extra=None):
        self.id = str(id)
        self.name = name
        self.address = address
        self.size = size
        self.driver = driver
        self.uuid = self.get_uuid()
        self.extra = extra or {}

    def get_uuid(self):
        """
        Unique hash for this network.

        The hash is a function of an SHA1 hash of the network's ID and
        its driver which means that it should be unique between all
        networks. In some subclasses (e.g. GoGrid) there is no ID
        available so the public IP address is used. This means that,
        unlike a properly done system UUID, the same UUID may mean a
        different system install at a different time

        >>> from libcloud.network.drivers.dummy import DummyNetworkDriver
        >>> driver = DummyNetworkDriver()
        >>> network = driver.create_network()
        >>> network.get_uuid()
        'd3748461511d8b9b0e0bfa0d4d3383a619a2bb9f'

        Note, for example, that this example will always produce the
        same UUID!

        :rtype:  ``str``
        :return: Unique identifier for this instance.
        """
        return hashlib.sha1(b("%s:%s" % (self.id,
                                         self.driver.type))).hexdigest()

    def __repr__(self):
        return (('<OpenNebulaNetwork: uuid=%s, name=%s, address=%s, size=%s, '
                 'provider=%s ...>')
                % (self.uuid, self.name, self.address, self.size,
                   self.driver.name))


class OpenNebulaNodeDriver(NodeDriver):
    """
    OpenNebula.org node driver.
    """

    connectionCls = OpenNebulaConnection
    name = 'OpenNebula'
    website = 'http://opennebula.org/'
    type = Provider.OPENNEBULA

    NODE_STATE_MAP = {
        'INIT': NodeState.PENDING,
        'PENDING': NodeState.PENDING,
        'HOLD': NodeState.PENDING,
        'ACTIVE': NodeState.RUNNING,
        'STOPPED': NodeState.TERMINATED,
        'SUSPENDED': NodeState.PENDING,
        'DONE': NodeState.TERMINATED,
        'FAILED': NodeState.TERMINATED}

    def __new__(cls, key, secret=None, api_version=DEFAULT_API_VERSION,
                **kwargs):
        if cls is OpenNebulaNodeDriver:
            if api_version in ['1.4']:
                cls = OpenNebula_1_4_NodeDriver
            elif api_version in ['2.0', '2.2']:
                cls = OpenNebula_2_0_NodeDriver
            elif api_version in ['3.0']:
                cls = OpenNebula_3_0_NodeDriver
            elif api_version in ['3.2']:
                cls = OpenNebula_3_2_NodeDriver
            elif api_version in ['3.6']:
                cls = OpenNebula_3_6_NodeDriver
            elif api_version in ['3.8']:
                cls = OpenNebula_3_8_NodeDriver
                if 'plain_auth' not in kwargs:
                    kwargs['plain_auth'] = cls.plain_auth
                else:
                    cls.plain_auth = kwargs['plain_auth']
            else:
                raise NotImplementedError(
                    "No OpenNebulaNodeDriver found for API version %s" %
                    (api_version))
            return super(OpenNebulaNodeDriver, cls).__new__(cls)

    def create_node(self, **kwargs):
        """
        Create a new OpenNebula node.

        @inherits: :class:`NodeDriver.create_node`

        :keyword networks: List of virtual networks to which this node should
                           connect. (optional)
        :type    networks: :class:`OpenNebulaNetwork` or
            ``list`` of :class:`OpenNebulaNetwork`
        """
        compute = ET.Element('COMPUTE')

        name = ET.SubElement(compute, 'NAME')
        name.text = kwargs['name']

        instance_type = ET.SubElement(compute, 'INSTANCE_TYPE')
        instance_type.text = kwargs['size'].name

        storage = ET.SubElement(compute, 'STORAGE')
        ET.SubElement(storage,
                      'DISK',
                      {'image': '%s' % (str(kwargs['image'].id))})

        if 'networks' in kwargs:
            if not isinstance(kwargs['networks'], list):
                kwargs['networks'] = [kwargs['networks']]

            networkGroup = ET.SubElement(compute, 'NETWORK')
            for network in kwargs['networks']:
                if network.address:
                    ET.SubElement(networkGroup, 'NIC',
                                  {'network': '%s' % (str(network.id)),
                                   'ip': network.address})
                else:
                    ET.SubElement(networkGroup, 'NIC',
                                  {'network': '%s' % (str(network.id))})

        xml = ET.tostring(compute)
        node = self.connection.request('/compute', method='POST',
                                       data=xml).object

        return self._to_node(node)

    def destroy_node(self, node):
        url = '/compute/%s' % (str(node.id))
        resp = self.connection.request(url, method='DELETE')

        return resp.status == httplib.OK

    def list_nodes(self):
        return self._to_nodes(self.connection.request('/compute').object)

    def list_images(self, location=None):
        return self._to_images(self.connection.request('/storage').object)

    def list_sizes(self, location=None):
        """
        Return list of sizes on a provider.

        @inherits: :class:`NodeDriver.list_sizes`

        :return: List of compute node sizes supported by the cloud provider.
        :rtype:  ``list`` of :class:`OpenNebulaNodeSize`
        """
        return [
            NodeSize(id=1,
                     name='small',
                     ram=None,
                     disk=None,
                     bandwidth=None,
                     price=None,
                     driver=self),
            NodeSize(id=2,
                     name='medium',
                     ram=None,
                     disk=None,
                     bandwidth=None,
                     price=None,
                     driver=self),
            NodeSize(id=3,
                     name='large',
                     ram=None,
                     disk=None,
                     bandwidth=None,
                     price=None,
                     driver=self),
        ]

    def list_locations(self):
        return [NodeLocation(0, '', '', self)]

    def ex_list_networks(self, location=None):
        """
        List virtual networks on a provider.

        :param location: Location from which to request a list of virtual
                         networks. (optional)
        :type  location: :class:`NodeLocation`

        :return: List of virtual networks available to be connected to a
                 compute node.
        :rtype:  ``list`` of :class:`OpenNebulaNetwork`
        """
        return self._to_networks(self.connection.request('/network').object)

    def ex_node_action(self, node, action):
        """
        Build action representation and instruct node to commit action.

        Build action representation from the compute node ID, and the
        action which should be carried out on that compute node. Then
        instruct the node to carry out that action.

        :param node: Compute node instance.
        :type  node: :class:`Node`

        :param action: Action to be carried out on the compute node.
        :type  action: ``str``

        :return: False if an HTTP Bad Request is received, else, True is
                 returned.
        :rtype:  ``bool``
        """
        compute_node_id = str(node.id)

        compute = ET.Element('COMPUTE')

        compute_id = ET.SubElement(compute, 'ID')
        compute_id.text = compute_node_id

        state = ET.SubElement(compute, 'STATE')
        state.text = action

        xml = ET.tostring(compute)

        url = '/compute/%s' % compute_node_id
        resp = self.connection.request(url, method='PUT',
                                       data=xml)

        if resp.status == httplib.BAD_REQUEST:
            return False
        else:
            return True

    def _to_images(self, object):
        """
        Request a list of images and convert that list to a list of NodeImage
        objects.

        Request a list of images from the OpenNebula web interface, and
        issue a request to convert each XML object representation of an image
        to a NodeImage object.

        :rtype:  ``list`` of :class:`NodeImage`
        :return: List of images.
        """
        images = []
        for element in object.findall('DISK'):
            image_id = element.attrib['href'].partition('/storage/')[2]
            image = self.connection.request(
                ('/storage/%s' % (image_id))).object
            images.append(self._to_image(image))

        return images

    def _to_image(self, image):
        """
        Take XML object containing an image description and convert to
        NodeImage object.

        :type  image: :class:`ElementTree`
        :param image: XML representation of an image.

        :rtype:  :class:`NodeImage`
        :return: The newly extracted :class:`NodeImage`.
        """
        return NodeImage(id=image.findtext('ID'),
                         name=image.findtext('NAME'),
                         driver=self.connection.driver,
                         extra={'size': image.findtext('SIZE'),
                                'url': image.findtext('URL')})

    def _to_networks(self, object):
        """
        Request a list of networks and convert that list to a list of
        OpenNebulaNetwork objects.

        Request a list of networks from the OpenNebula web interface, and
        issue a request to convert each XML object representation of a network
        to an OpenNebulaNetwork object.

        :rtype:  ``list`` of :class:`OpenNebulaNetwork`
        :return: List of virtual networks.
        """
        networks = []
        for element in object.findall('NETWORK'):
            network_id = element.attrib['href'].partition('/network/')[2]
            network_element = self.connection.request(
                ('/network/%s' % (network_id))).object
            networks.append(self._to_network(network_element))

        return networks

    def _to_network(self, element):
        """
        Take XML object containing a network description and convert to
        OpenNebulaNetwork object.

        Take XML representation containing a network description and
        convert to OpenNebulaNetwork object.

        :rtype:  :class:`OpenNebulaNetwork`
        :return: The newly extracted :class:`OpenNebulaNetwork`.
        """
        return OpenNebulaNetwork(id=element.findtext('ID'),
                                 name=element.findtext('NAME'),
                                 address=element.findtext('ADDRESS'),
                                 size=element.findtext('SIZE'),
                                 driver=self.connection.driver)

    def _to_nodes(self, object):
        """
        Request a list of compute nodes and convert that list to a list of
        Node objects.

        Request a list of compute nodes from the OpenNebula web interface, and
        issue a request to convert each XML object representation of a node
        to a Node object.

        :rtype:  ``list`` of :class:`Node`
        :return: A list of compute nodes.
        """
        computes = []
        for element in object.findall('COMPUTE'):
            compute_id = element.attrib['href'].partition('/compute/')[2]
            compute = self.connection.request(
                ('/compute/%s' % (compute_id))).object
            computes.append(self._to_node(compute))

        return computes

    def _to_node(self, compute):
        """
        Take XML object containing a compute node description and convert to
        Node object.

        Take XML representation containing a compute node description and
        convert to Node object.

        :type  compute: :class:`ElementTree`
        :param compute: XML representation of a compute node.

        :rtype:  :class:`Node`
        :return: The newly extracted :class:`Node`.
        """
        try:
            state = self.NODE_STATE_MAP[compute.findtext('STATE').upper()]
        except KeyError:
            state = NodeState.UNKNOWN

        return Node(id=compute.findtext('ID'),
                    name=compute.findtext('NAME'),
                    state=state,
                    public_ips=self._extract_networks(compute),
                    private_ips=[],
                    driver=self.connection.driver,
                    image=self._extract_images(compute))

    def _extract_networks(self, compute):
        """
        Extract networks from a compute node XML representation.

        Extract network descriptions from a compute node XML representation,
        converting each network to an OpenNebulaNetwork object.

        :type  compute: :class:`ElementTree`
        :param compute: XML representation of a compute node.

        :rtype:  ``list`` of :class:`OpenNebulaNetwork`s.
        :return: List of virtual networks attached to the compute node.
        """
        networks = list()

        network_list = compute.find('NETWORK')
        for element in network_list.findall('NIC'):
            networks.append(
                OpenNebulaNetwork(id=element.attrib.get('network', None),
                                  name=None,
                                  address=element.attrib.get('ip', None),
                                  size=1,
                                  driver=self.connection.driver))

        return networks

    def _extract_images(self, compute):
        """
        Extract image disks from a compute node XML representation.

        Extract image disk descriptions from a compute node XML representation,
        converting the disks to an NodeImage object.

        :type  compute: :class:`ElementTree`
        :param compute: XML representation of a compute node.

        :rtype:  :class:`NodeImage`.
        :return: First disk attached to a compute node.
        """
        disks = list()

        disk_list = compute.find('STORAGE')
        if disk_list is not None:
            for element in disk_list.findall('DISK'):
                disks.append(
                    NodeImage(id=element.attrib.get('image', None),
                              name=None,
                              driver=self.connection.driver,
                              extra={'dev': element.attrib.get('dev', None)}))

        # @TODO: Return all disks when the Node type accepts multiple
        # attached disks per node.
        if len(disks) > 0:
            return disks[0]
        else:
            return None


class OpenNebula_1_4_NodeDriver(OpenNebulaNodeDriver):
    """
    OpenNebula.org node driver for OpenNebula.org v1.4.
    """

    name = 'OpenNebula (v1.4)'


class OpenNebula_2_0_NodeDriver(OpenNebulaNodeDriver):
    """
    OpenNebula.org node driver for OpenNebula.org v2.0 through OpenNebula.org
    v2.2.
    """

    name = 'OpenNebula (v2.0 - v2.2)'

    def create_node(self, **kwargs):
        """
        Create a new OpenNebula node.

        @inherits: :class:`NodeDriver.create_node`

        :keyword networks: List of virtual networks to which this node should
                           connect. (optional)
        :type    networks: :class:`OpenNebulaNetwork` or ``list``
                           of :class:`OpenNebulaNetwork`

        :keyword context: Custom (key, value) pairs to be injected into
                          compute node XML description. (optional)
        :type    context: ``dict``

        :return: Instance of a newly created node.
        :rtype:  :class:`Node`
        """
        compute = ET.Element('COMPUTE')

        name = ET.SubElement(compute, 'NAME')
        name.text = kwargs['name']

        instance_type = ET.SubElement(compute, 'INSTANCE_TYPE')
        instance_type.text = kwargs['size'].name

        disk = ET.SubElement(compute, 'DISK')
        ET.SubElement(disk,
                      'STORAGE',
                      {'href': '/storage/%s' % (str(kwargs['image'].id))})

        if 'networks' in kwargs:
            if not isinstance(kwargs['networks'], list):
                kwargs['networks'] = [kwargs['networks']]

            for network in kwargs['networks']:
                nic = ET.SubElement(compute, 'NIC')
                ET.SubElement(nic, 'NETWORK',
                              {'href': '/network/%s' % (str(network.id))})
                if network.address:
                    ip_line = ET.SubElement(nic, 'IP')
                    ip_line.text = network.address

        if 'context' in kwargs:
            if isinstance(kwargs['context'], dict):
                contextGroup = ET.SubElement(compute, 'CONTEXT')
                for key, value in list(kwargs['context'].items()):
                    context = ET.SubElement(contextGroup, key.upper())
                    context.text = value

        xml = ET.tostring(compute)
        node = self.connection.request('/compute', method='POST',
                                       data=xml).object

        return self._to_node(node)

    def destroy_node(self, node):
        url = '/compute/%s' % (str(node.id))
        resp = self.connection.request(url, method='DELETE')

        return resp.status == httplib.NO_CONTENT

    def list_sizes(self, location=None):
        """
        Return list of sizes on a provider.

        @inherits: :class:`NodeDriver.list_sizes`

        :return: List of compute node sizes supported by the cloud provider.
        :rtype:  ``list`` of :class:`OpenNebulaNodeSize`
        """
        return [
            OpenNebulaNodeSize(id=1,
                               name='small',
                               ram=1024,
                               cpu=1,
                               disk=None,
                               bandwidth=None,
                               price=None,
                               driver=self),
            OpenNebulaNodeSize(id=2,
                               name='medium',
                               ram=4096,
                               cpu=4,
                               disk=None,
                               bandwidth=None,
                               price=None,
                               driver=self),
            OpenNebulaNodeSize(id=3,
                               name='large',
                               ram=8192,
                               cpu=8,
                               disk=None,
                               bandwidth=None,
                               price=None,
                               driver=self),
            OpenNebulaNodeSize(id=4,
                               name='custom',
                               ram=0,
                               cpu=0,
                               disk=None,
                               bandwidth=None,
                               price=None,
                               driver=self),
        ]

    def _to_images(self, object):
        """
        Request a list of images and convert that list to a list of NodeImage
        objects.

        Request a list of images from the OpenNebula web interface, and
        issue a request to convert each XML object representation of an image
        to a NodeImage object.

        :rtype:  ``list`` of :class:`NodeImage`
        :return: List of images.
        """
        images = []
        for element in object.findall('STORAGE'):
            image_id = element.attrib["href"].partition("/storage/")[2]
            image = self.connection.request(
                ("/storage/%s" % (image_id))).object
            images.append(self._to_image(image))

        return images

    def _to_image(self, image):
        """
        Take XML object containing an image description and convert to
        NodeImage object.

        :type  image: :class:`ElementTree`
        :param image: XML representation of an image.

        :rtype:  :class:`NodeImage`
        :return: The newly extracted :class:`NodeImage`.
        """
        return NodeImage(id=image.findtext('ID'),
                         name=image.findtext('NAME'),
                         driver=self.connection.driver,
                         extra={'description': image.findtext('DESCRIPTION'),
                                'type': image.findtext('TYPE'),
                                'size': image.findtext('SIZE'),
                                'fstype': image.findtext('FSTYPE', None)})

    def _to_node(self, compute):
        """
        Take XML object containing a compute node description and convert to
        Node object.

        Take XML representation containing a compute node description and
        convert to Node object.

        :type  compute: :class:`ElementTree`
        :param compute: XML representation of a compute node.

        :rtype:  :class:`Node`
        :return: The newly extracted :class:`Node`.
        """
        try:
            state = self.NODE_STATE_MAP[compute.findtext('STATE').upper()]
        except KeyError:
            state = NodeState.UNKNOWN

        return Node(id=compute.findtext('ID'),
                    name=compute.findtext('NAME'),
                    state=state,
                    public_ips=self._extract_networks(compute),
                    private_ips=[],
                    driver=self.connection.driver,
                    image=self._extract_images(compute),
                    size=self._extract_size(compute),
                    extra={'context': self._extract_context(compute)})

    def _extract_networks(self, compute):
        """
        Extract networks from a compute node XML representation.

        Extract network descriptions from a compute node XML representation,
        converting each network to an OpenNebulaNetwork object.

        :type  compute: :class:`ElementTree`
        :param compute: XML representation of a compute node.

        :rtype:  ``list`` of :class:`OpenNebulaNetwork`
        :return: List of virtual networks attached to the compute node.
        """
        networks = []

        for element in compute.findall('NIC'):
            network = element.find('NETWORK')
            network_id = network.attrib['href'].partition('/network/')[2]

            networks.append(
                OpenNebulaNetwork(id=network_id,
                                  name=network.attrib.get('name', None),
                                  address=element.findtext('IP'),
                                  size=1,
                                  driver=self.connection.driver,
                                  extra={'mac': element.findtext('MAC')}))

        return networks

    def _extract_images(self, compute):
        """
        Extract image disks from a compute node XML representation.

        Extract image disk descriptions from a compute node XML representation,
        converting the disks to an NodeImage object.

        :type  compute: :class:`ElementTree`
        :param compute: XML representation of a compute node.

        :rtype:  ``list`` of :class:`NodeImage`
        :return: Disks attached to a compute node.
        """
        disks = list()

        for element in compute.findall('DISK'):
            disk = element.find('STORAGE')
            image_id = disk.attrib['href'].partition('/storage/')[2]

            if 'id' in element.attrib:
                disk_id = element.attrib['id']
            else:
                disk_id = None

            disks.append(
                NodeImage(id=image_id,
                          name=disk.attrib.get('name', None),
                          driver=self.connection.driver,
                          extra={'type': element.findtext('TYPE'),
                                 'disk_id': disk_id,
                                 'target': element.findtext('TARGET')}))

        # Return all disks when the Node type accepts multiple attached disks
        # per node.
        if len(disks) > 1:
            return disks
        elif len(disks) == 1:
            return disks[0]
        else:
            return None

    def _extract_size(self, compute):
        """
        Extract size, or node type, from a compute node XML representation.

        Extract node size, or node type, description from a compute node XML
        representation, converting the node size to a NodeSize object.

        :type  compute: :class:`ElementTree`
        :param compute: XML representation of a compute node.

        :rtype:  :class:`OpenNebulaNodeSize`
        :return: Node type of compute node.
        """
        instance_type = compute.find('INSTANCE_TYPE')

        try:
            return next((node_size for node_size in self.list_sizes()
                        if node_size.name == instance_type.text))
        except StopIteration:
            return None

    def _extract_context(self, compute):
        """
        Extract size, or node type, from a compute node XML representation.

        Extract node size, or node type, description from a compute node XML
        representation, converting the node size to a NodeSize object.

        :type  compute: :class:`ElementTree`
        :param compute: XML representation of a compute node.

        :rtype:  ``dict``
        :return: Dictionary containing (key, value) pairs related to
                 compute node context.
        """
        contexts = dict()
        context = compute.find('CONTEXT')

        if context is not None:
            for context_element in list(context):
                contexts[context_element.tag.lower()] = context_element.text

        return contexts


class OpenNebula_3_0_NodeDriver(OpenNebula_2_0_NodeDriver):
    """
    OpenNebula.org node driver for OpenNebula.org v3.0.
    """

    name = 'OpenNebula (v3.0)'

    def ex_node_set_save_name(self, node, name):
        """
        Build action representation and instruct node to commit action.

        Build action representation from the compute node ID, the disk image
        which will be saved, and the name under which the image will be saved
        upon shutting down the compute node.

        :param node: Compute node instance.
        :type  node: :class:`Node`

        :param name: Name under which the image should be saved after shutting
                     down the compute node.
        :type  name: ``str``

        :return: False if an HTTP Bad Request is received, else, True is
                 returned.
        :rtype:  ``bool``
        """
        compute_node_id = str(node.id)

        compute = ET.Element('COMPUTE')

        compute_id = ET.SubElement(compute, 'ID')
        compute_id.text = compute_node_id

        disk = ET.SubElement(compute, 'DISK', {'id': str(node.image.id)})

        ET.SubElement(disk, 'STORAGE',
                      {'href': '/storage/%s' % (str(node.image.id)),
                       'name': node.image.name})

        ET.SubElement(disk, 'SAVE_AS', {'name': str(name)})

        xml = ET.tostring(compute)

        url = '/compute/%s' % compute_node_id
        resp = self.connection.request(url, method='PUT',
                                       data=xml)

        if resp.status == httplib.BAD_REQUEST:
            return False
        else:
            return True

    def _to_network(self, element):
        """
        Take XML object containing a network description and convert to
        OpenNebulaNetwork object.

        Take XML representation containing a network description and
        convert to OpenNebulaNetwork object.

        :return: The newly extracted :class:`OpenNebulaNetwork`.
        :rtype:  :class:`OpenNebulaNetwork`
        """
        return OpenNebulaNetwork(id=element.findtext('ID'),
                                 name=element.findtext('NAME'),
                                 address=element.findtext('ADDRESS'),
                                 size=element.findtext('SIZE'),
                                 driver=self.connection.driver,
                                 extra={'public': element.findtext('PUBLIC')})


class OpenNebula_3_2_NodeDriver(OpenNebula_3_0_NodeDriver):
    """
    OpenNebula.org node driver for OpenNebula.org v3.2.
    """

    name = 'OpenNebula (v3.2)'

    def reboot_node(self, node):
        return self.ex_node_action(node, ACTION.REBOOT)

    def list_sizes(self, location=None):
        """
        Return list of sizes on a provider.

        @inherits: :class:`NodeDriver.list_sizes`

        :return: List of compute node sizes supported by the cloud provider.
        :rtype:  ``list`` of :class:`OpenNebulaNodeSize`
        """
        return self._to_sizes(self.connection.request('/instance_type').object)

    def _to_sizes(self, object):
        """
        Request a list of instance types and convert that list to a list of
        OpenNebulaNodeSize objects.

        Request a list of instance types from the OpenNebula web interface,
        and issue a request to convert each XML object representation of an
        instance type to an OpenNebulaNodeSize object.

        :return: List of instance types.
        :rtype:  ``list`` of :class:`OpenNebulaNodeSize`
        """
        sizes = []
        size_id = 1

        attributes = [('name', str, None), ('ram', int, 'MEMORY'),
                      ('cpu', float, None), ('vcpu', float, None),
                      ('disk', str, None), ('bandwidth', float, None),
                      ('price', float, None)]

        for element in object.findall('INSTANCE_TYPE'):
            size_kwargs = {'id': size_id, 'driver': self}
            values = self._get_attributes_values(attributes=attributes,
                                                 element=element)
            size_kwargs.update(values)

            size = OpenNebulaNodeSize(**size_kwargs)
            sizes.append(size)
            size_id += 1

        return sizes

    def _get_attributes_values(self, attributes, element):
        values = {}

        for attribute_name, attribute_type, alias in attributes:
                key = alias if alias else attribute_name.upper()
                value = element.findtext(key)

                if value is not None:
                    value = attribute_type(value)

                values[attribute_name] = value

        return values


class OpenNebula_3_6_NodeDriver(OpenNebula_3_2_NodeDriver):
    """
    OpenNebula.org node driver for OpenNebula.org v3.6.
    """

    name = 'OpenNebula (v3.6)'

    def create_volume(self, size, name, location=None, snapshot=None):
        storage = ET.Element('STORAGE')

        vol_name = ET.SubElement(storage, 'NAME')
        vol_name.text = name

        vol_type = ET.SubElement(storage, 'TYPE')
        vol_type.text = 'DATABLOCK'

        description = ET.SubElement(storage, 'DESCRIPTION')
        description.text = 'Attached storage'

        public = ET.SubElement(storage, 'PUBLIC')
        public.text = 'NO'

        persistent = ET.SubElement(storage, 'PERSISTENT')
        persistent.text = 'YES'

        fstype = ET.SubElement(storage, 'FSTYPE')
        fstype.text = 'ext3'

        vol_size = ET.SubElement(storage, 'SIZE')
        vol_size.text = str(size)

        xml = ET.tostring(storage)
        volume = self.connection.request('/storage',
                                         {'occixml': xml},
                                         method='POST').object

        return self._to_volume(volume)

    def destroy_volume(self, volume):
        url = '/storage/%s' % (str(volume.id))
        resp = self.connection.request(url, method='DELETE')

        return resp.status == httplib.NO_CONTENT

    def attach_volume(self, node, volume, device):
        action = ET.Element('ACTION')

        perform = ET.SubElement(action, 'PERFORM')
        perform.text = 'ATTACHDISK'

        params = ET.SubElement(action, 'PARAMS')

        ET.SubElement(params,
                      'STORAGE',
                      {'href': '/storage/%s' % (str(volume.id))})

        target = ET.SubElement(params, 'TARGET')
        target.text = device

        xml = ET.tostring(action)

        url = '/compute/%s/action' % node.id

        resp = self.connection.request(url, method='POST', data=xml)
        return resp.status == httplib.ACCEPTED

    def _do_detach_volume(self, node_id, disk_id):
        action = ET.Element('ACTION')

        perform = ET.SubElement(action, 'PERFORM')
        perform.text = 'DETACHDISK'

        params = ET.SubElement(action, 'PARAMS')

        ET.SubElement(params,
                      'DISK',
                      {'id': disk_id})

        xml = ET.tostring(action)

        url = '/compute/%s/action' % node_id

        resp = self.connection.request(url, method='POST', data=xml)
        return resp.status == httplib.ACCEPTED

    def detach_volume(self, volume):
        # We need to find the node using this volume
        for node in self.list_nodes():
            if type(node.image) is not list:
                # This node has only one associated image. It is not the one we
                # are after.
                continue

            for disk in node.image:
                if disk.id == volume.id:
                    # Node found. We can now detach the volume
                    disk_id = disk.extra['disk_id']
                    return self._do_detach_volume(node.id, disk_id)

        return False

    def list_volumes(self):
        return self._to_volumes(self.connection.request('/storage').object)

    def _to_volume(self, storage):
        return StorageVolume(id=storage.findtext('ID'),
                             name=storage.findtext('NAME'),
                             size=int(storage.findtext('SIZE')),
                             driver=self.connection.driver)

    def _to_volumes(self, object):
        volumes = []
        for storage in object.findall('STORAGE'):
            storage_id = storage.attrib['href'].partition('/storage/')[2]

            volumes.append(self._to_volume(
                self.connection.request('/storage/%s' % storage_id).object))

        return volumes


class OpenNebula_3_8_NodeDriver(OpenNebula_3_6_NodeDriver):
    """
    OpenNebula.org node driver for OpenNebula.org v3.8.
    """

    name = 'OpenNebula (v3.8)'
    plain_auth = API_PLAIN_AUTH

    def _to_sizes(self, object):
        """
        Request a list of instance types and convert that list to a list of
        OpenNebulaNodeSize objects.

        Request a list of instance types from the OpenNebula web interface,
        and issue a request to convert each XML object representation of an
        instance type to an OpenNebulaNodeSize object.

        :return: List of instance types.
        :rtype:  ``list`` of :class:`OpenNebulaNodeSize`
        """
        sizes = []
        size_id = 1

        attributes = [('name', str, None), ('ram', int, 'MEMORY'),
                      ('cpu', float, None), ('vcpu', float, None),
                      ('disk', str, None), ('bandwidth', float, None),
                      ('price', float, None)]

        for element in object.findall('INSTANCE_TYPE'):
            element = self.connection.request(
                ('/instance_type/%s') % (element.attrib['name'])).object

            size_kwargs = {'id': size_id, 'driver': self}
            values = self._get_attributes_values(attributes=attributes,
                                                 element=element)
            size_kwargs.update(values)

            size = OpenNebulaNodeSize(**size_kwargs)
            sizes.append(size)
            size_id += 1
        return sizes

    def _ex_connection_class_kwargs(self):
        """
        Set plain_auth as an extra :class:`OpenNebulaConnection_3_8` argument

        :return: ``dict`` of :class:`OpenNebulaConnection_3_8` input arguments
        """

        return {'plain_auth': self.plain_auth}
