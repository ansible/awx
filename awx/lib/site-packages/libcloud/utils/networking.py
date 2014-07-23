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

import socket
import struct

__all__ = [
    'is_private_subnet',
    'is_public_subnet',
    'is_valid_ip_address'
]


def is_private_subnet(ip):
    """
    Utility function to check if an IP address is inside a private subnet.

    :type ip: ``str``
    :param ip: IP address to check

    :return: ``bool`` if the specified IP address is private.
    """
    priv_subnets = [{'subnet': '10.0.0.0', 'mask': '255.0.0.0'},
                    {'subnet': '172.16.0.0', 'mask': '255.240.0.0'},
                    {'subnet': '192.168.0.0', 'mask': '255.255.0.0'}]

    ip = struct.unpack('I', socket.inet_aton(ip))[0]

    for network in priv_subnets:
        subnet = struct.unpack('I', socket.inet_aton(network['subnet']))[0]
        mask = struct.unpack('I', socket.inet_aton(network['mask']))[0]

        if (ip & mask) == (subnet & mask):
            return True

    return False


def is_public_subnet(ip):
    """
    Utility function to check if an IP address is inside a public subnet.

    :type ip: ``str``
    :param ip: IP address to check

    :return: ``bool`` if the specified IP address is public.
    """
    return not is_private_subnet(ip=ip)


def is_valid_ip_address(address, family=socket.AF_INET):
    """
    Check if the provided address is valid IPv4 or IPv6 address.

    :param address: IPv4 or IPv6 ddress to check.
    :type address: ``str``

    :param family: Address family (socket.AF_INTET / socket.AF_INET6).
    :type family: ``int``

    :return: ``bool`` True if the provided address is valid.
    """
    try:
        socket.inet_pton(family, address)
    except socket.error:
        return False

    return True
