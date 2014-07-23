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
Gandi driver base classes
"""

import time
import hashlib
import sys

from libcloud.utils.py3 import b

from libcloud.common.base import ConnectionKey
from libcloud.common.xmlrpc import XMLRPCResponse, XMLRPCConnection

# Global constants

DEFAULT_TIMEOUT = 600   # operation pooling max seconds
DEFAULT_INTERVAL = 20   # seconds between 2 operation.info


class GandiException(Exception):
    """
    Exception class for Gandi driver
    """
    def __str__(self):
        return '(%u) %s' % (self.args[0], self.args[1])

    def __repr__(self):
        return '<GandiException code %u "%s">' % (self.args[0], self.args[1])


class GandiResponse(XMLRPCResponse):
    """
    A Base Gandi Response class to derive from.
    """


class GandiConnection(XMLRPCConnection, ConnectionKey):
    """
    Connection class for the Gandi driver
    """

    responseCls = GandiResponse
    host = 'rpc.gandi.net'
    endpoint = '/xmlrpc/'

    def __init__(self, key, secure=True):
        # Note: Method resolution order in this case is
        # XMLRPCConnection -> Connection and Connection doesn't take key as the
        # first argument so we specify a keyword argument instead.
        # Previously it was GandiConnection -> ConnectionKey so it worked fine.
        super(GandiConnection, self).__init__(key=key, secure=secure)
        self.driver = BaseGandiDriver

    def request(self, method, *args):
        args = (self.key, ) + args
        return super(GandiConnection, self).request(method, *args)


class BaseGandiDriver(object):
    """
    Gandi base driver

    """
    connectionCls = GandiConnection
    name = 'Gandi'

    # Specific methods for gandi
    def _wait_operation(self, id, timeout=DEFAULT_TIMEOUT,
                        check_interval=DEFAULT_INTERVAL):
        """ Wait for an operation to succeed"""

        for i in range(0, timeout, check_interval):
            try:
                op = self.connection.request('operation.info', int(id)).object

                if op['step'] == 'DONE':
                    return True
                if op['step'] in ['ERROR', 'CANCEL']:
                    return False
            except (KeyError, IndexError):
                pass
            except Exception:
                e = sys.exc_info()[1]
                raise GandiException(1002, e)

            time.sleep(check_interval)
        return False


class BaseObject(object):
    """Base class for objects not conventional"""

    uuid_prefix = ''

    def __init__(self, id, state, driver):
        self.id = str(id) if id else None
        self.state = state
        self.driver = driver
        self.uuid = self.get_uuid()

    def get_uuid(self):
        """Unique hash for this object

        :return: ``str``

        The hash is a function of an SHA1 hash of prefix, the object's ID and
        its driver which means that it should be unique between all
        interfaces.
        TODO : to review
        >>> from libcloud.compute.drivers.dummy import DummyNodeDriver
        >>> driver = DummyNodeDriver(0)
        >>> vif = driver.create_interface()
        >>> vif.get_uuid()
        'd3748461511d8b9b0e0bfa0d4d3383a619a2bb9f'

        Note, for example, that this example will always produce the
        same UUID!
        """
        hashstring = '%s:%s:%s' % \
            (self.uuid_prefix, self.id, self.driver.type)
        return hashlib.sha1(b(hashstring)).hexdigest()


class IPAddress(BaseObject):
    """
    Provide a common interface for ip addresses
    """

    uuid_prefix = 'inet:'

    def __init__(self, id, state, inet, driver, version=4, extra=None):
        super(IPAddress, self).__init__(id, state, driver)
        self.inet = inet
        self.version = version
        self.extra = extra or {}

    def __repr__(self):
        return (('<IPAddress: id=%s, address=%s, state=%s, driver=%s ...>')
                % (self.id, self.inet, self.state, self.driver.name))


class NetworkInterface(BaseObject):
    """
    Provide a common interface for network interfaces
    """

    uuid_prefix = 'if:'

    def __init__(self, id, state, mac_address, driver,
                 ips=None, node_id=None, extra=None):
        super(NetworkInterface, self).__init__(id, state, driver)
        self.mac = mac_address
        self.ips = ips or {}
        self.node_id = node_id
        self.extra = extra or {}

    def __repr__(self):
        return (('<Interface: id=%s, mac=%s, state=%s, driver=%s ...>')
                % (self.id, self.mac, self.state, self.driver.name))


class Disk(BaseObject):
    """
    Gandi disk component
    """
    def __init__(self, id, state, name, driver, size, extra=None):
        super(Disk, self).__init__(id, state, driver)
        self.name = name
        self.size = size
        self.extra = extra or {}

    def __repr__(self):
        return (
            ('<Disk: id=%s, name=%s, state=%s, size=%s, driver=%s ...>')
            % (self.id, self.name, self.state, self.size, self.driver.name))
