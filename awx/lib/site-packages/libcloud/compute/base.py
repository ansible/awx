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
Provides base classes for working with drivers
"""

from __future__ import with_statement

import sys
import time
import hashlib
import os
import socket
import binascii

from libcloud.utils.py3 import b

import libcloud.compute.ssh
from libcloud.pricing import get_size_price
from libcloud.compute.types import NodeState, DeploymentError
from libcloud.compute.ssh import SSHClient
from libcloud.common.base import ConnectionKey
from libcloud.common.base import BaseDriver
from libcloud.common.types import LibcloudError
from libcloud.compute.ssh import have_paramiko

from libcloud.utils.networking import is_private_subnet
from libcloud.utils.networking import is_valid_ip_address

if have_paramiko:
    from paramiko.ssh_exception import SSHException
    SSH_TIMEOUT_EXCEPTION_CLASSES = (SSHException, IOError, socket.gaierror,
                                     socket.error)
else:
    SSH_TIMEOUT_EXCEPTION_CLASSES = (IOError, socket.gaierror, socket.error)

# How long to wait for the node to come online after creating it
NODE_ONLINE_WAIT_TIMEOUT = 10 * 60

# How long to try connecting to a remote SSH server when running a deployment
# script.
SSH_CONNECT_TIMEOUT = 5 * 60


__all__ = [
    'Node',
    'NodeState',
    'NodeSize',
    'NodeImage',
    'NodeLocation',
    'NodeAuthSSHKey',
    'NodeAuthPassword',
    'NodeDriver',

    'StorageVolume',
    'VolumeSnapshot',

    # Deprecated, moved to libcloud.utils.networking
    'is_private_subnet',
    'is_valid_ip_address'
]


class UuidMixin(object):
    """
    Mixin class for get_uuid function.
    """

    def __init__(self):
        self._uuid = None

    def get_uuid(self):
        """
        Unique hash for a node, node image, or node size

        The hash is a function of an SHA1 hash of the node, node image,
        or node size's ID and its driver which means that it should be
        unique between all objects of its type.
        In some subclasses (e.g. GoGridNode) there is no ID
        available so the public IP address is used.  This means that,
        unlike a properly done system UUID, the same UUID may mean a
        different system install at a different time

        >>> from libcloud.compute.drivers.dummy import DummyNodeDriver
        >>> driver = DummyNodeDriver(0)
        >>> node = driver.create_node()
        >>> node.get_uuid()
        'd3748461511d8b9b0e0bfa0d4d3383a619a2bb9f'

        Note, for example, that this example will always produce the
        same UUID!

        :rtype: ``str``
        """
        if not self._uuid:
            self._uuid = hashlib.sha1(b('%s:%s' %
                                      (self.id, self.driver.type))).hexdigest()

        return self._uuid

    @property
    def uuid(self):
        return self.get_uuid()


class Node(UuidMixin):
    """
    Provide a common interface for handling nodes of all types.

    The Node object provides the interface in libcloud through which
    we can manipulate nodes in different cloud providers in the same
    way.  Node objects don't actually do much directly themselves,
    instead the node driver handles the connection to the node.

    You don't normally create a node object yourself; instead you use
    a driver and then have that create the node for you.

    >>> from libcloud.compute.drivers.dummy import DummyNodeDriver
    >>> driver = DummyNodeDriver(0)
    >>> node = driver.create_node()
    >>> node.public_ips[0]
    '127.0.0.3'
    >>> node.name
    'dummy-3'

    You can also get nodes from the driver's list_node function.

    >>> node = driver.list_nodes()[0]
    >>> node.name
    'dummy-1'

    The node keeps a reference to its own driver which means that we
    can work on nodes from different providers without having to know
    which is which.

    >>> driver = DummyNodeDriver(72)
    >>> node2 = driver.create_node()
    >>> node.driver.creds
    0
    >>> node2.driver.creds
    72

    Although Node objects can be subclassed, this isn't normally
    done.  Instead, any driver specific information is stored in the
    "extra" attribute of the node.

    >>> node.extra
    {'foo': 'bar'}
    """

    def __init__(self, id, name, state, public_ips, private_ips,
                 driver, size=None, image=None, extra=None):
        """
        :param id: Node ID.
        :type id: ``str``

        :param name: Node name.
        :type name: ``str``

        :param state: Node state.
        :type state: :class:`libcloud.compute.types.NodeState`

        :param public_ips: Public IP addresses associated with this node.
        :type public_ips: ``list``

        :param private_ips: Private IP addresses associated with this node.
        :type private_ips: ``list``

        :param driver: Driver this node belongs to.
        :type driver: :class:`.NodeDriver`

        :param size: Size of this node. (optional)
        :type size: :class:`.NodeSize`

        :param image: Image of this node. (optional)
        :type size: :class:`.NodeImage`

        :param extra: Optional provider specific attributes associated with
                      this node.
        :type extra: ``dict``

        """
        self.id = str(id) if id else None
        self.name = name
        self.state = state
        self.public_ips = public_ips if public_ips else []
        self.private_ips = private_ips if private_ips else []
        self.driver = driver
        self.size = size
        self.image = image
        self.extra = extra or {}
        UuidMixin.__init__(self)

    def reboot(self):
        """
        Reboot this node

        :return: ``bool``

        This calls the node's driver and reboots the node

        >>> from libcloud.compute.drivers.dummy import DummyNodeDriver
        >>> driver = DummyNodeDriver(0)
        >>> node = driver.create_node()
        >>> node.state == NodeState.RUNNING
        True
        >>> node.state == NodeState.REBOOTING
        False
        >>> node.reboot()
        True
        >>> node.state == NodeState.REBOOTING
        True
        """
        return self.driver.reboot_node(self)

    def destroy(self):
        """
        Destroy this node

        :return: ``bool``

        This calls the node's driver and destroys the node

        >>> from libcloud.compute.drivers.dummy import DummyNodeDriver
        >>> driver = DummyNodeDriver(0)
        >>> from libcloud.compute.types import NodeState
        >>> node = driver.create_node()
        >>> node.state == NodeState.RUNNING
        True
        >>> node.destroy()
        True
        >>> node.state == NodeState.RUNNING
        False

        """
        return self.driver.destroy_node(self)

    def __repr__(self):
        return (('<Node: uuid=%s, name=%s, state=%s, public_ips=%s, '
                 'private_ips=%s, provider=%s ...>')
                % (self.uuid, self.name, self.state, self.public_ips,
                   self.private_ips, self.driver.name))


class NodeSize(UuidMixin):
    """
    A Base NodeSize class to derive from.

    NodeSizes are objects which are typically returned a driver's
    list_sizes function.  They contain a number of different
    parameters which define how big an image is.

    The exact parameters available depends on the provider.

    N.B. Where a parameter is "unlimited" (for example bandwidth in
    Amazon) this will be given as 0.

    >>> from libcloud.compute.drivers.dummy import DummyNodeDriver
    >>> driver = DummyNodeDriver(0)
    >>> size = driver.list_sizes()[0]
    >>> size.ram
    128
    >>> size.bandwidth
    500
    >>> size.price
    4
    """

    def __init__(self, id, name, ram, disk, bandwidth, price,
                 driver, extra=None):
        """
        :param id: Size ID.
        :type  id: ``str``

        :param name: Size name.
        :type  name: ``str``

        :param ram: Amount of memory (in MB) provided by this size.
        :type  ram: ``int``

        :param disk: Amount of disk storage (in GB) provided by this image.
        :type  disk: ``int``

        :param bandwidth: Amount of bandiwdth included with this size.
        :type  bandwidth: ``int``

        :param price: Price (in US dollars) of running this node for an hour.
        :type  price: ``float``

        :param driver: Driver this size belongs to.
        :type  driver: :class:`.NodeDriver`

        :param extra: Optional provider specific attributes associated with
                      this size.
        :type  extra: ``dict``
        """
        self.id = str(id)
        self.name = name
        self.ram = ram
        self.disk = disk
        self.bandwidth = bandwidth
        self.price = price
        self.driver = driver
        self.extra = extra or {}
        UuidMixin.__init__(self)

    def __repr__(self):
        return (('<NodeSize: id=%s, name=%s, ram=%s disk=%s bandwidth=%s '
                 'price=%s driver=%s ...>')
                % (self.id, self.name, self.ram, self.disk, self.bandwidth,
                   self.price, self.driver.name))


class NodeImage(UuidMixin):
    """
    An operating system image.

    NodeImage objects are typically returned by the driver for the
    cloud provider in response to the list_images function

    >>> from libcloud.compute.drivers.dummy import DummyNodeDriver
    >>> driver = DummyNodeDriver(0)
    >>> image = driver.list_images()[0]
    >>> image.name
    'Ubuntu 9.10'

    Apart from name and id, there is no further standard information;
    other parameters are stored in a driver specific "extra" variable

    When creating a node, a node image should be given as an argument
    to the create_node function to decide which OS image to use.

    >>> node = driver.create_node(image=image)
    """

    def __init__(self, id, name, driver, extra=None):
        """
        :param id: Image ID.
        :type id: ``str``

        :param name: Image name.
        :type name: ``str``

        :param driver: Driver this image belongs to.
        :type driver: :class:`.NodeDriver`

        :param extra: Optional provided specific attributes associated with
                      this image.
        :type extra: ``dict``
        """
        self.id = str(id)
        self.name = name
        self.driver = driver
        self.extra = extra or {}
        UuidMixin.__init__(self)

    def __repr__(self):
        return (('<NodeImage: id=%s, name=%s, driver=%s  ...>')
                % (self.id, self.name, self.driver.name))


class NodeLocation(object):
    """
    A physical location where nodes can be.

    >>> from libcloud.compute.drivers.dummy import DummyNodeDriver
    >>> driver = DummyNodeDriver(0)
    >>> location = driver.list_locations()[0]
    >>> location.country
    'US'
    """

    def __init__(self, id, name, country, driver):
        """
        :param id: Location ID.
        :type id: ``str``

        :param name: Location name.
        :type name: ``str``

        :param country: Location country.
        :type country: ``str``

        :param driver: Driver this location belongs to.
        :type driver: :class:`.NodeDriver`
        """
        self.id = str(id)
        self.name = name
        self.country = country
        self.driver = driver

    def __repr__(self):
        return (('<NodeLocation: id=%s, name=%s, country=%s, driver=%s>')
                % (self.id, self.name, self.country, self.driver.name))


class NodeAuthSSHKey(object):
    """
    An SSH key to be installed for authentication to a node.

    This is the actual contents of the users ssh public key which will
    normally be installed as root's public key on the node.

    >>> pubkey = '...' # read from file
    >>> from libcloud.compute.base import NodeAuthSSHKey
    >>> k = NodeAuthSSHKey(pubkey)
    >>> k
    <NodeAuthSSHKey>
    """

    def __init__(self, pubkey):
        """
        :param pubkey: Public key matetiral.
        :type pubkey: ``str``
        """
        self.pubkey = pubkey

    def __repr__(self):
        return '<NodeAuthSSHKey>'


class NodeAuthPassword(object):
    """
    A password to be used for authentication to a node.
    """
    def __init__(self, password, generated=False):
        """
        :param password: Password.
        :type password: ``str``

        :type generated: ``True`` if this password was automatically generated,
                         ``False`` otherwise.
        """
        self.password = password
        self.generated = generated

    def __repr__(self):
        return '<NodeAuthPassword>'


class StorageVolume(UuidMixin):
    """
    A base StorageVolume class to derive from.
    """

    def __init__(self, id, name, size, driver, extra=None):
        """
        :param id: Storage volume ID.
        :type id: ``str``

        :param name: Storage volume name.
        :type name: ``str``

        :param size: Size of this volume (in GB).
        :type size: ``int``

        :param driver: Driver this image belongs to.
        :type driver: :class:`.NodeDriver`

        :param extra: Optional provider specific attributes.
        :type extra: ``dict``
        """
        self.id = id
        self.name = name
        self.size = size
        self.driver = driver
        self.extra = extra
        UuidMixin.__init__(self)

    def list_snapshots(self):
        """
        :rtype: ``list`` of ``VolumeSnapshot``
        """
        return self.driver.list_volume_snapshots(volume=self)

    def attach(self, node, device=None):
        """
        Attach this volume to a node.

        :param node: Node to attach volume to
        :type node: :class:`.Node`

        :param device: Where the device is exposed,
                            e.g. '/dev/sdb (optional)
        :type device: ``str``

        :return: ``True`` if attach was successful, ``False`` otherwise.
        :rtype: ``bool``
        """

        return self.driver.attach_volume(node=node, volume=self, device=device)

    def detach(self):
        """
        Detach this volume from its node

        :return: ``True`` if detach was successful, ``False`` otherwise.
        :rtype: ``bool``
        """

        return self.driver.detach_volume(volume=self)

    def snapshot(self, name):
        """
        Creates a snapshot of this volume.

        :return: Created snapshot.
        :rtype: ``VolumeSnapshot``
        """
        return self.driver.create_volume_snapshot(volume=self, name=name)

    def destroy(self):
        """
        Destroy this storage volume.

        :return: ``True`` if destroy was successful, ``False`` otherwise.
        :rtype: ``bool``
        """

        return self.driver.destroy_volume(volume=self)

    def __repr__(self):
        return '<StorageVolume id=%s size=%s driver=%s>' % (
               self.id, self.size, self.driver.name)


class VolumeSnapshot(object):
    """
    A base VolumeSnapshot class to derive from.
    """
    def __init__(self, id, driver, size=None, extra=None):
        """
        VolumeSnapshot constructor.

        :param      id: Snapshot ID.
        :type       id: ``str``

        :param      size: A snapshot size in GB.
        :type       size: ``int``

        :param      extra: Provider depends parameters for snapshot.
        :type       extra: ``dict``
        """
        self.id = id
        self.driver = driver
        self.size = size
        self.extra = extra or {}

    def destroy(self):
        """
        Destroys this snapshot.

        :rtype: ``bool``
        """
        return self.driver.destroy_volume_snapshot(snapshot=self)

    def __repr__(self):
        return ('<VolumeSnapshot id=%s size=%s driver=%s>' %
                (self.id, self.size, self.driver.name))


class KeyPair(object):
    """
    Represents a SSH key pair.
    """

    def __init__(self, name, public_key, fingerprint, driver, private_key=None,
                 extra=None):
        """
        Constructor.

        :keyword    name: Name of the key pair object.
        :type       name: ``str``

        :keyword    fingerprint: Key fingerprint.
        :type       fingerprint: ``str``

        :keyword    public_key: Public key in OpenSSH format.
        :type       public_key: ``str``

        :keyword    private_key: Private key in PEM format.
        :type       private_key: ``str``

        :keyword    extra: Provider specific attributes associated with this
                           key pair. (optional)
        :type       extra: ``dict``
        """
        self.name = name
        self.fingerprint = fingerprint
        self.public_key = public_key
        self.private_key = private_key
        self.driver = driver
        self.extra = extra or {}

    def __repr__(self):
        return ('<KeyPair name=%s fingerprint=%s driver=%s>' %
                (self.name, self.fingerprint, self.driver.name))


class NodeDriver(BaseDriver):
    """
    A base NodeDriver class to derive from

    This class is always subclassed by a specific driver.  For
    examples of base behavior of most functions (except deploy node)
    see the dummy driver.

    """

    connectionCls = ConnectionKey
    name = None
    type = None
    port = None
    features = {'create_node': []}

    """
    List of available features for a driver.
        - :meth:`libcloud.compute.base.NodeDriver.create_node`
            - ssh_key: Supports :class:`.NodeAuthSSHKey` as an authentication
              method for nodes.
            - password: Supports :class:`.NodeAuthPassword` as an
              authentication
              method for nodes.
            - generates_password: Returns a password attribute on the Node
              object returned from creation.
    """

    NODE_STATE_MAP = {}

    def __init__(self, key, secret=None, secure=True, host=None, port=None,
                 api_version=None, **kwargs):
        super(NodeDriver, self).__init__(key=key, secret=secret, secure=secure,
                                         host=host, port=port,
                                         api_version=api_version, **kwargs)

    def list_nodes(self):
        """
        List all nodes.

        :return:  list of node objects
        :rtype: ``list`` of :class:`.Node`
        """
        raise NotImplementedError(
            'list_nodes not implemented for this driver')

    def list_sizes(self, location=None):
        """
        List sizes on a provider

        :param location: The location at which to list sizes
        :type location: :class:`.NodeLocation`

        :return: list of node size objects
        :rtype: ``list`` of :class:`.NodeSize`
        """
        raise NotImplementedError(
            'list_sizes not implemented for this driver')

    def list_locations(self):
        """
        List data centers for a provider

        :return: list of node location objects
        :rtype: ``list`` of :class:`.NodeLocation`
        """
        raise NotImplementedError(
            'list_locations not implemented for this driver')

    def create_node(self, **kwargs):
        """
        Create a new node instance. This instance will be started
        automatically.

        Not all hosting API's are created equal and to allow libcloud to
        support as many as possible there are some standard supported
        variations of ``create_node``. These are declared using a
        ``features`` API.
        You can inspect ``driver.features['create_node']`` to see what
        variation of the API you are dealing with:

        ``ssh_key``
            You can inject a public key into a new node allows key based SSH
            authentication.
        ``password``
            You can inject a password into a new node for SSH authentication.
            If no password is provided libcloud will generated a password.
            The password will be available as
            ``return_value.extra['password']``.
        ``generates_password``
            The hosting provider will generate a password. It will be returned
            to you via ``return_value.extra['password']``.

        Some drivers allow you to set how you will authenticate with the
        instance that is created. You can inject this initial authentication
        information via the ``auth`` parameter.

        If a driver supports the ``ssh_key`` feature flag for ``created_node``
        you can upload a public key into the new instance::

            >>> from libcloud.compute.drivers.dummy import DummyNodeDriver
            >>> driver = DummyNodeDriver(0)
            >>> auth = NodeAuthSSHKey('pubkey data here')
            >>> node = driver.create_node("test_node", auth=auth)

        If a driver supports the ``password`` feature flag for ``create_node``
        you can set a password::

            >>> driver = DummyNodeDriver(0)
            >>> auth = NodeAuthPassword('mysecretpassword')
            >>> node = driver.create_node("test_node", auth=auth)

        If a driver supports the ``password`` feature and you don't provide the
        ``auth`` argument libcloud will assign a password::

            >>> driver = DummyNodeDriver(0)
            >>> node = driver.create_node("test_node")
            >>> password = node.extra['password']

        A password will also be returned in this way for drivers that declare
        the ``generates_password`` feature, though in that case the password is
        actually provided to the driver API by the hosting provider rather than
        generated by libcloud.

        You can only pass a :class:`.NodeAuthPassword` or
        :class:`.NodeAuthSSHKey` to ``create_node`` via the auth parameter if
        has the corresponding feature flag.

        :param name:   String with a name for this new node (required)
        :type name:   ``str``

        :param size:   The size of resources allocated to this node.
                            (required)
        :type size:   :class:`.NodeSize`

        :param image:  OS Image to boot on node. (required)
        :type image:  :class:`.NodeImage`

        :param location: Which data center to create a node in. If empty,
                              undefined behavior will be selected. (optional)
        :type location: :class:`.NodeLocation`

        :param auth:   Initial authentication information for the node
                            (optional)
        :type auth:   :class:`.NodeAuthSSHKey` or :class:`NodeAuthPassword`

        :return: The newly created node.
        :rtype: :class:`.Node`
        """
        raise NotImplementedError(
            'create_node not implemented for this driver')

    def deploy_node(self, **kwargs):
        """
        Create a new node, and start deployment.

        In order to be able to SSH into a created node access credentials are
        required.

        A user can pass either a :class:`.NodeAuthPassword` or
        :class:`.NodeAuthSSHKey` to the ``auth`` argument. If the
        ``create_node`` implementation supports that kind if credential (as
        declared in ``self.features['create_node']``) then it is passed on to
        ``create_node``. Otherwise it is not passed on to ``create_node`` and
        it is only used for authentication.

        If the ``auth`` parameter is not supplied but the driver declares it
        supports ``generates_password`` then the password returned by
        ``create_node`` will be used to SSH into the server.

        Finally, if the ``ssh_key_file`` is supplied that key will be used to
        SSH into the server.

        This function may raise a :class:`DeploymentException`, if a
        create_node call was successful, but there is a later error (like SSH
        failing or timing out).  This exception includes a Node object which
        you may want to destroy if incomplete deployments are not desirable.

        >>> from libcloud.compute.drivers.dummy import DummyNodeDriver
        >>> from libcloud.compute.deployment import ScriptDeployment
        >>> from libcloud.compute.deployment import MultiStepDeployment
        >>> from libcloud.compute.base import NodeAuthSSHKey
        >>> driver = DummyNodeDriver(0)
        >>> key = NodeAuthSSHKey('...') # read from file
        >>> script = ScriptDeployment("yum -y install emacs strace tcpdump")
        >>> msd = MultiStepDeployment([key, script])
        >>> def d():
        ...     try:
        ...         driver.deploy_node(deploy=msd)
        ...     except NotImplementedError:
        ...         print ("not implemented for dummy driver")
        >>> d()
        not implemented for dummy driver

        Deploy node is typically not overridden in subclasses.  The
        existing implementation should be able to handle most such.

        :param deploy: Deployment to run once machine is online and
                            available to SSH.
        :type deploy: :class:`Deployment`

        :param ssh_username: Optional name of the account which is used
                                  when connecting to
                                  SSH server (default is root)
        :type ssh_username: ``str``

        :param ssh_alternate_usernames: Optional list of ssh usernames to
                                             try to connect with if using the
                                             default one fails
        :type ssh_alternate_usernames: ``list``

        :param ssh_port: Optional SSH server port (default is 22)
        :type ssh_port: ``int``

        :param ssh_timeout: Optional SSH connection timeout in seconds
                                 (default is 10)
        :type ssh_timeout: ``float``

        :param auth:   Initial authentication information for the node
                            (optional)
        :type auth:   :class:`.NodeAuthSSHKey` or :class:`NodeAuthPassword`

        :param ssh_key: A path (or paths) to an SSH private key with which
                             to attempt to authenticate. (optional)
        :type ssh_key: ``str`` or ``list`` of ``str``

        :param timeout: How many seconds to wait before timing out.
                             (default is 600)
        :type timeout: ``int``

        :param max_tries: How many times to retry if a deployment fails
                               before giving up (default is 3)
        :type max_tries: ``int``

        :param ssh_interface: The interface to wait for. Default is
                                   'public_ips', other option is 'private_ips'.
        :type ssh_interface: ``str``
        """
        if not libcloud.compute.ssh.have_paramiko:
            raise RuntimeError('paramiko is not installed. You can install ' +
                               'it using pip: pip install paramiko')

        if 'auth' in kwargs:
            auth = kwargs['auth']
            if not isinstance(auth, (NodeAuthSSHKey, NodeAuthPassword)):
                raise NotImplementedError(
                    'If providing auth, only NodeAuthSSHKey or'
                    'NodeAuthPassword is supported')
        elif 'ssh_key' in kwargs:
            # If an ssh_key is provided we can try deploy_node
            pass
        elif 'create_node' in self.features:
            f = self.features['create_node']
            if 'generates_password' not in f and "password" not in f:
                raise NotImplementedError(
                    'deploy_node not implemented for this driver')
        else:
            raise NotImplementedError(
                'deploy_node not implemented for this driver')

        node = self.create_node(**kwargs)
        max_tries = kwargs.get('max_tries', 3)

        password = None
        if 'auth' in kwargs:
            if isinstance(kwargs['auth'], NodeAuthPassword):
                password = kwargs['auth'].password
        elif 'password' in node.extra:
            password = node.extra['password']

        ssh_interface = kwargs.get('ssh_interface', 'public_ips')

        # Wait until node is up and running and has IP assigned
        try:
            node, ip_addresses = self.wait_until_running(
                nodes=[node],
                wait_period=3,
                timeout=kwargs.get('timeout', NODE_ONLINE_WAIT_TIMEOUT),
                ssh_interface=ssh_interface)[0]
        except Exception:
            e = sys.exc_info()[1]
            raise DeploymentError(node=node, original_exception=e, driver=self)

        ssh_username = kwargs.get('ssh_username', 'root')
        ssh_alternate_usernames = kwargs.get('ssh_alternate_usernames', [])
        ssh_port = kwargs.get('ssh_port', 22)
        ssh_timeout = kwargs.get('ssh_timeout', 10)
        ssh_key_file = kwargs.get('ssh_key', None)
        timeout = kwargs.get('timeout', SSH_CONNECT_TIMEOUT)

        deploy_error = None

        for username in ([ssh_username] + ssh_alternate_usernames):
            try:
                self._connect_and_run_deployment_script(
                    task=kwargs['deploy'], node=node,
                    ssh_hostname=ip_addresses[0], ssh_port=ssh_port,
                    ssh_username=username, ssh_password=password,
                    ssh_key_file=ssh_key_file, ssh_timeout=ssh_timeout,
                    timeout=timeout, max_tries=max_tries)
            except Exception:
                # Try alternate username
                # Todo: Need to fix paramiko so we can catch a more specific
                # exception
                e = sys.exc_info()[1]
                deploy_error = e
            else:
                # Script successfully executed, don't try alternate username
                deploy_error = None
                break

        if deploy_error is not None:
            raise DeploymentError(node=node, original_exception=deploy_error,
                                  driver=self)

        return node

    def reboot_node(self, node):
        """
        Reboot a node.

        :param node: The node to be rebooted
        :type node: :class:`.Node`

        :return: True if the reboot was successful, otherwise False
        :rtype: ``bool``
        """
        raise NotImplementedError(
            'reboot_node not implemented for this driver')

    def destroy_node(self, node):
        """
        Destroy a node.

        Depending upon the provider, this may destroy all data associated with
        the node, including backups.

        :param node: The node to be destroyed
        :type node: :class:`.Node`

        :return: True if the destroy was successful, False otherwise.
        :rtype: ``bool``
        """
        raise NotImplementedError(
            'destroy_node not implemented for this driver')

    ##
    # Volume and snapshot management methods
    ##

    def list_volumes(self):
        """
        List storage volumes.

        :rtype: ``list`` of :class:`.StorageVolume`
        """
        raise NotImplementedError(
            'list_volumes not implemented for this driver')

    def list_volume_snapshots(self, volume):
        """
        List snapshots for a storage volume.

        :rtype: ``list`` of :class:`VolumeSnapshot`
        """
        raise NotImplementedError(
            'list_volume_snapshots not implemented for this driver')

    def create_volume(self, size, name, location=None, snapshot=None):
        """
        Create a new volume.

        :param size: Size of volume in gigabytes (required)
        :type size: ``int``

        :param name: Name of the volume to be created
        :type name: ``str``

        :param location: Which data center to create a volume in. If
                               empty, undefined behavior will be selected.
                               (optional)
        :type location: :class:`.NodeLocation`

        :param snapshot:  Name of snapshot from which to create the new
                               volume.  (optional)
        :type snapshot:  ``str``

        :return: The newly created volume.
        :rtype: :class:`StorageVolume`
        """
        raise NotImplementedError(
            'create_volume not implemented for this driver')

    def create_volume_snapshot(self, volume, name):
        """
        Creates a snapshot of the storage volume.

        :rtype: :class:`VolumeSnapshot`
        """
        raise NotImplementedError(
            'create_volume_snapshot not implemented for this driver')

    def attach_volume(self, node, volume, device=None):
        """
        Attaches volume to node.

        :param node: Node to attach volume to.
        :type node: :class:`.Node`

        :param volume: Volume to attach.
        :type volume: :class:`.StorageVolume`

        :param device: Where the device is exposed, e.g. '/dev/sdb'
        :type device: ``str``

        :rytpe: ``bool``
        """
        raise NotImplementedError('attach not implemented for this driver')

    def detach_volume(self, volume):
        """
        Detaches a volume from a node.

        :param volume: Volume to be detached
        :type volume: :class:`.StorageVolume`

        :rtype: ``bool``
        """

        raise NotImplementedError('detach not implemented for this driver')

    def destroy_volume(self, volume):
        """
        Destroys a storage volume.

        :param volume: Volume to be destroyed
        :type volume: :class:`StorageVolume`

        :rtype: ``bool``
        """

        raise NotImplementedError(
            'destroy_volume not implemented for this driver')

    def destroy_volume_snapshot(self, snapshot):
        """
        Destroys a snapshot.

        :rtype: :class:`bool`
        """
        raise NotImplementedError(
            'destroy_volume_snapshot not implemented for this driver')

    ##
    # Image management methods
    ##

    def list_images(self, location=None):
        """
        List images on a provider.

        :param location: The location at which to list images.
        :type location: :class:`.NodeLocation`

        :return: list of node image objects.
        :rtype: ``list`` of :class:`.NodeImage`
        """
        raise NotImplementedError(
            'list_images not implemented for this driver')

    def create_image(self, node, name, description=None):
        """
        Creates an image from a node object.

        :param node: Node to run the task on.
        :type node: :class:`.Node`

        :param name: name for new image.
        :type name: ``str``

        :param description: description for new image.
        :type name: ``description``

        :rtype: :class:`.NodeImage`:
        :return: NodeImage instance on success.

        """
        raise NotImplementedError(
            'create_image not implemented for this driver')

    def delete_image(self, node_image):
        """
        Deletes a node image from a provider.

        :param node_image: Node image object.
        :type node_image: :class:`.NodeImage`

        :return: ``True`` if delete_image was successful, ``False`` otherwise.
        :rtype: ``bool``
        """

        raise NotImplementedError(
            'delete_image not implemented for this driver')

    def get_image(self, image_id):
        """
        Returns a single node image from a provider.

        :param image_id: Node to run the task on.
        :type image_id: ``str``

        :rtype :class:`.NodeImage`:
        :return: NodeImage instance on success.
        """
        raise NotImplementedError(
            'get_image not implemented for this driver')

    def copy_image(self, source_region, node_image, name, description=None):
        """
        Copies an image from a source region to the current region.

        :param source_region: Region to copy the node from.
        :type source_region: ``str``

        :param node_image: NodeImage to copy.
        :type node_image: :class`.NodeImage`:

        :param name: name for new image.
        :type name: ``str``

        :param description: description for new image.
        :type name: ``str``

        :rtype: :class:`.NodeImage`:
        :return: NodeImage instance on success.
        """
        raise NotImplementedError(
            'copy_image not implemented for this driver')

    ##
    # SSH key pair management methods
    ##

    def list_key_pairs(self):
        """
        List all the available key pair objects.

        :rtype: ``list`` of :class:`.KeyPair` objects
        """
        raise NotImplementedError(
            'list_key_pairs not implemented for this driver')

    def get_key_pair(self, name):
        """
        Retrieve a single key pair.

        :param name: Name of the key pair to retrieve.
        :type name: ``str``

        :rtype: :class:`.KeyPair`
        """
        raise NotImplementedError(
            'get_key_pair not implemented for this driver')

    def create_key_pair(self, name):
        """
        Create a new key pair object.

        :param name: Key pair name.
        :type name: ``str``
        """
        raise NotImplementedError(
            'create_key_pair not implemented for this driver')

    def import_key_pair_from_string(self, name, key_material):
        """
        Import a new public key from string.

        :param name: Key pair name.
        :type name: ``str``

        :param key_material: Public key material.
        :type key_material: ``str``

        :rtype: :class:`.KeyPair` object
        """
        raise NotImplementedError(
            'import_key_pair_from_string not implemented for this driver')

    def import_key_pair_from_file(self, name, key_file_path):
        """
        Import a new public key from string.

        :param name: Key pair name.
        :type name: ``str``

        :param key_file_path: Path to the public key file.
        :type key_file_path: ``str``

        :rtype: :class:`.KeyPair` object
        """
        key_file_path = os.path.expanduser(key_file_path)

        with open(key_file_path, 'r') as fp:
            key_material = fp.read()

        return self.import_key_pair_from_string(name=name,
                                                key_material=key_material)

    def delete_key_pair(self, key_pair):
        """
        Delete an existing key pair.

        :param key_pair: Key pair object.
        :type key_pair: :class`.KeyPair`
        """
        raise NotImplementedError(
            'delete_key_pair not implemented for this driver')

    def wait_until_running(self, nodes, wait_period=3, timeout=600,
                           ssh_interface='public_ips', force_ipv4=True):
        """
        Block until the provided nodes are considered running.

        Node is considered running when it's state is "running" and when it has
        at least one IP address assigned.

        :param nodes: List of nodes to wait for.
        :type nodes: ``list`` of :class:`.Node`

        :param wait_period: How many seconds to wait between each loop
                            iteration. (default is 3)
        :type wait_period: ``int``

        :param timeout: How many seconds to wait before giving up.
                        (default is 600)
        :type timeout: ``int``

        :param ssh_interface: Which attribute on the node to use to obtain
                              an IP address. Valid options: public_ips,
                              private_ips. Default is public_ips.
        :type ssh_interface: ``str``

        :param force_ipv4: Ignore IPv6 addresses (default is True).
        :type force_ipv4: ``bool``

        :return: ``[(Node, ip_addresses)]`` list of tuple of Node instance and
                 list of ip_address on success.
        :rtype: ``list`` of ``tuple``
        """
        def is_supported(address):
            """
            Return True for supported address.
            """
            if force_ipv4 and not is_valid_ip_address(address=address,
                                                      family=socket.AF_INET):
                return False
            return True

        def filter_addresses(addresses):
            """
            Return list of supported addresses.
            """
            return [address for address in addresses if is_supported(address)]

        if ssh_interface not in ['public_ips', 'private_ips']:
            raise ValueError('ssh_interface argument must either be' +
                             'public_ips or private_ips')

        start = time.time()
        end = start + timeout

        uuids = set([node.uuid for node in nodes])

        while time.time() < end:
            all_nodes = self.list_nodes()
            matching_nodes = list([node for node in all_nodes
                                   if node.uuid in uuids])

            if len(matching_nodes) > len(uuids):
                found_uuids = [node.uuid for node in matching_nodes]
                msg = ('Unable to match specified uuids ' +
                       '(%s) with existing nodes. Found ' % (uuids) +
                       'multiple nodes with same uuid: (%s)' % (found_uuids))
                raise LibcloudError(value=msg, driver=self)

            running_nodes = [node for node in matching_nodes
                             if node.state == NodeState.RUNNING]
            addresses = [filter_addresses(getattr(node, ssh_interface))
                         for node in running_nodes]

            if len(running_nodes) == len(uuids) == len(addresses):
                return list(zip(running_nodes, addresses))
            else:
                time.sleep(wait_period)
                continue

        raise LibcloudError(value='Timed out after %s seconds' % (timeout),
                            driver=self)

    def _get_and_check_auth(self, auth):
        """
        Helper function for providers supporting :class:`.NodeAuthPassword` or
        :class:`.NodeAuthSSHKey`

        Validates that only a supported object type is passed to the auth
        parameter and raises an exception if it is not.

        If no :class:`.NodeAuthPassword` object is provided but one is expected
        then a password is automatically generated.
        """

        if isinstance(auth, NodeAuthPassword):
            if 'password' in self.features['create_node']:
                return auth
            raise LibcloudError(
                'Password provided as authentication information, but password'
                'not supported', driver=self)

        if isinstance(auth, NodeAuthSSHKey):
            if 'ssh_key' in self.features['create_node']:
                return auth
            raise LibcloudError(
                'SSH Key provided as authentication information, but SSH Key'
                'not supported', driver=self)

        if 'password' in self.features['create_node']:
            value = os.urandom(16)
            value = binascii.hexlify(value).decode('ascii')
            return NodeAuthPassword(value, generated=True)

        if auth:
            raise LibcloudError(
                '"auth" argument provided, but it was not a NodeAuthPassword'
                'or NodeAuthSSHKey object', driver=self)

    def _wait_until_running(self, node, wait_period=3, timeout=600,
                            ssh_interface='public_ips', force_ipv4=True):
        # This is here for backward compatibility and will be removed in the
        # next major release
        return self.wait_until_running(nodes=[node], wait_period=wait_period,
                                       timeout=timeout,
                                       ssh_interface=ssh_interface,
                                       force_ipv4=force_ipv4)

    def _ssh_client_connect(self, ssh_client, wait_period=1.5, timeout=300):
        """
        Try to connect to the remote SSH server. If a connection times out or
        is refused it is retried up to timeout number of seconds.

        :param ssh_client: A configured SSHClient instance
        :type ssh_client: ``SSHClient``

        :param wait_period: How many seconds to wait between each loop
                            iteration. (default is 1.5)
        :type wait_period: ``int``

        :param timeout: How many seconds to wait before giving up.
                        (default is 300)
        :type timeout: ``int``

        :return: ``SSHClient`` on success
        """
        start = time.time()
        end = start + timeout

        while time.time() < end:
            try:
                ssh_client.connect()
            except SSH_TIMEOUT_EXCEPTION_CLASSES:
                e = sys.exc_info()[1]
                message = str(e).lower()
                expected_msg = 'no such file or directory'

                if isinstance(e, IOError) and expected_msg in message:
                    # Propagate (key) file doesn't exist errors
                    raise e

                # Retry if a connection is refused, timeout occurred,
                # or the connection fails due to failed authentication.
                ssh_client.close()
                time.sleep(wait_period)
                continue
            else:
                return ssh_client

        raise LibcloudError(value='Could not connect to the remote SSH ' +
                            'server. Giving up.', driver=self)

    def _connect_and_run_deployment_script(self, task, node, ssh_hostname,
                                           ssh_port, ssh_username,
                                           ssh_password, ssh_key_file,
                                           ssh_timeout, timeout, max_tries):
        """
        Establish an SSH connection to the node and run the provided deployment
        task.

        :rtype: :class:`.Node`:
        :return: Node instance on success.
        """
        ssh_client = SSHClient(hostname=ssh_hostname,
                               port=ssh_port, username=ssh_username,
                               password=ssh_password,
                               key_files=ssh_key_file,
                               timeout=ssh_timeout)

        ssh_client = self._ssh_client_connect(ssh_client=ssh_client,
                                              timeout=timeout)

        # Execute the deployment task
        node = self._run_deployment_script(task=task, node=node,
                                           ssh_client=ssh_client,
                                           max_tries=max_tries)
        return node

    def _run_deployment_script(self, task, node, ssh_client, max_tries=3):
        """
        Run the deployment script on the provided node. At this point it is
        assumed that SSH connection has already been established.

        :param task: Deployment task to run.
        :type task: :class:`Deployment`

        :param node: Node to run the task on.
        :type node: ``Node``

        :param ssh_client: A configured and connected SSHClient instance.
        :type ssh_client: :class:`SSHClient`

        :param max_tries: How many times to retry if a deployment fails
                          before giving up. (default is 3)
        :type max_tries: ``int``

        :rtype: :class:`.Node`
        :return: ``Node`` Node instance on success.
        """
        tries = 0

        while tries < max_tries:
            try:
                node = task.run(node, ssh_client)
            except Exception:
                tries += 1

                if tries >= max_tries:
                    e = sys.exc_info()[1]
                    raise LibcloudError(value='Failed after %d tries: %s'
                                        % (max_tries, str(e)), driver=self)
            else:
                # Deployment succeeded
                ssh_client.close()
                return node

    def _get_size_price(self, size_id):
        """
        Return pricing information for the provided size id.
        """
        return get_size_price(driver_type='compute',
                              driver_name=self.api_name,
                              size_id=size_id)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
