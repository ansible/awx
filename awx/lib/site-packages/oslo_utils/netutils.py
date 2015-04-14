# Copyright 2012 OpenStack Foundation.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Network-related utilities and helper functions.
"""

import logging
import os
import socket

import netaddr
import netifaces
from six.moves.urllib import parse

from oslo_utils._i18n import _
from oslo_utils._i18n import _LI
from oslo_utils._i18n import _LW

LOG = logging.getLogger(__name__)
_IS_IPV6_ENABLED = None


def parse_host_port(address, default_port=None):
    """Interpret a string as a host:port pair.

    An IPv6 address MUST be escaped if accompanied by a port,
    because otherwise ambiguity ensues: 2001:db8:85a3::8a2e:370:7334
    means both [2001:db8:85a3::8a2e:370:7334] and
    [2001:db8:85a3::8a2e:370]:7334.

    >>> parse_host_port('server01:80')
    ('server01', 80)
    >>> parse_host_port('server01')
    ('server01', None)
    >>> parse_host_port('server01', default_port=1234)
    ('server01', 1234)
    >>> parse_host_port('[::1]:80')
    ('::1', 80)
    >>> parse_host_port('[::1]')
    ('::1', None)
    >>> parse_host_port('[::1]', default_port=1234)
    ('::1', 1234)
    >>> parse_host_port('2001:db8:85a3::8a2e:370:7334', default_port=1234)
    ('2001:db8:85a3::8a2e:370:7334', 1234)
    >>> parse_host_port(None)
    (None, None)
    """
    if not address:
        return (None, None)

    if address[0] == '[':
        # Escaped ipv6
        _host, _port = address[1:].split(']')
        host = _host
        if ':' in _port:
            port = _port.split(':')[1]
        else:
            port = default_port
    else:
        if address.count(':') == 1:
            host, port = address.split(':')
        else:
            # 0 means ipv4, >1 means ipv6.
            # We prohibit unescaped ipv6 addresses with port.
            host = address
            port = default_port

    return (host, None if port is None else int(port))


def is_valid_ipv4(address):
    """Verify that address represents a valid IPv4 address.

    :param address: Value to verify
    :type address: string
    :returns: bool
    """
    try:
        return netaddr.valid_ipv4(address)
    except Exception:
        return False


def is_valid_ipv6(address):
    """Verify that address represents a valid IPv6 address.

    :param address: Value to verify
    :type address: string
    :returns: bool
    """
    try:
        return netaddr.valid_ipv6(address)
    except Exception:
        return False


def get_ipv6_addr_by_EUI64(prefix, mac):
    """Calculate IPv6 address using EUI-64 specification.

    This method calculates the IPv6 address using the EUI-64
    addressing scheme as explained in rfc2373.

    :param prefix: IPv6 prefix.
    :param mac: IEEE 802 48-bit MAC address.
    :returns: IPv6 address on success.
    :raises ValueError, TypeError: For any invalid input.
    """
    # Check if the prefix is an IPv4 address
    if netaddr.valid_ipv4(prefix):
        msg = _("Unable to generate IP address by EUI64 for IPv4 prefix")
        raise ValueError(msg)
    try:
        eui64 = int(netaddr.EUI(mac).eui64())
        prefix = netaddr.IPNetwork(prefix)
        return netaddr.IPAddress(prefix.first + eui64 ^ (1 << 57))
    except (ValueError, netaddr.AddrFormatError):
        raise ValueError(_('Bad prefix or mac format for generating IPv6 '
                           'address by EUI-64: %(prefix)s, %(mac)s:')
                         % {'prefix': prefix, 'mac': mac})
    except TypeError:
        raise TypeError(_('Bad prefix type for generating IPv6 address by '
                          'EUI-64: %s') % prefix)


def is_ipv6_enabled():
    """Check if IPv6 support is enabled on the platform.

    This api will look into the proc entries of the platform to figure
    out the status of IPv6 support on the platform.

    :returns: True if the platform has IPv6 support, False otherwise.

    """

    global _IS_IPV6_ENABLED

    if _IS_IPV6_ENABLED is None:
        disabled_ipv6_path = "/proc/sys/net/ipv6/conf/default/disable_ipv6"
        if os.path.exists(disabled_ipv6_path):
            with open(disabled_ipv6_path, 'r') as f:
                disabled = f.read().strip()
            _IS_IPV6_ENABLED = disabled == "0"
        else:
            _IS_IPV6_ENABLED = False
    return _IS_IPV6_ENABLED


def is_valid_ip(address):
    """Verify that address represents a valid IP address.

    :param address: Value to verify
    :type address: string
    :returns: bool
    """
    return is_valid_ipv4(address) or is_valid_ipv6(address)


def is_valid_port(port):
    """Verify that port represents a valid port number."""
    try:
        val = int(port)
    except (ValueError, TypeError):
        return False

    return (val > 0 and val <= 65535)


def get_my_ipv4():
    """Returns the actual ipv4 of the local machine.

    This code figures out what source address would be used if some traffic
    were to be sent out to some well known address on the Internet. In this
    case, IP from RFC5737 is used, but the specific address does not
    matter much. No traffic is actually sent.
    """
    try:
        csock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        csock.connect(('192.0.2.0', 80))
        (addr, port) = csock.getsockname()
        csock.close()
        return addr
    except socket.error:
        return _get_my_ipv4_address()


def _get_my_ipv4_address():
    """Figure out the best ipv4
    """
    LOCALHOST = '127.0.0.1'
    gtw = netifaces.gateways()
    try:
        interface = gtw['default'][netifaces.AF_INET][1]
    except (KeyError, IndexError):
        LOG.info(_LI('Could not determine default network interface, '
                     'using 127.0.0.1 for IPv4 address'))
        return LOCALHOST

    try:
        return netifaces.ifaddresses(interface)[netifaces.AF_INET][0]['addr']
    except (KeyError, IndexError):
        LOG.info(_LI('Could not determine IPv4 address for interface %s, '
                     'using 127.0.0.1'),
                 interface)
    except Exception as e:
        LOG.info(_LI('Could not determine IPv4 address for '
                     'interface %(interface)s: %(error)s'),
                 {'interface': interface, 'error': e})
    return LOCALHOST


class _ModifiedSplitResult(parse.SplitResult):
    """Split results class for urlsplit."""

    # NOTE(dims): The functions below are needed for Python 2.6.x.
    # We can remove these when we drop support for 2.6.x.
    @property
    def hostname(self):
        netloc = self.netloc.split('@', 1)[-1]
        host, port = parse_host_port(netloc)
        return host

    @property
    def port(self):
        netloc = self.netloc.split('@', 1)[-1]
        host, port = parse_host_port(netloc)
        return port

    def params(self, collapse=True):
        """Extracts the query parameters from the split urls components.

        This method will provide back as a dictionary the query parameter
        names and values that were provided in the url.

        :param collapse: Boolean, turn on or off collapsing of query values
        with the same name. Since a url can contain the same query parameter
        name with different values it may or may not be useful for users to
        care that this has happened. This parameter when True uses the
        last value that was given for a given name, while if False it will
        retain all values provided by associating the query parameter name with
        a list of values instead of a single (non-list) value.
        """
        if self.query:
            if collapse:
                return dict(parse.parse_qsl(self.query))
            else:
                params = {}
                for (key, value) in parse.parse_qsl(self.query):
                    if key in params:
                        if isinstance(params[key], list):
                            params[key].append(value)
                        else:
                            params[key] = [params[key], value]
                    else:
                        params[key] = value
                return params
        else:
            return {}


def urlsplit(url, scheme='', allow_fragments=True):
    """Parse a URL using urlparse.urlsplit(), splitting query and fragments.
    This function papers over Python issue9374_ when needed.

    .. _issue9374: http://bugs.python.org/issue9374

    The parameters are the same as urlparse.urlsplit.
    """
    scheme, netloc, path, query, fragment = parse.urlsplit(
        url, scheme, allow_fragments)
    if allow_fragments and '#' in path:
        path, fragment = path.split('#', 1)
    if '?' in path:
        path, query = path.split('?', 1)
    return _ModifiedSplitResult(scheme, netloc,
                                path, query, fragment)


def set_tcp_keepalive(sock, tcp_keepalive=True,
                      tcp_keepidle=None,
                      tcp_keepalive_interval=None,
                      tcp_keepalive_count=None):
    """Set values for tcp keepalive parameters

    This function configures tcp keepalive parameters if users wish to do
    so.

    :param tcp_keepalive: Boolean, turn on or off tcp_keepalive. If users are
      not sure, this should be True, and default values will be used.

    :param tcp_keepidle: time to wait before starting to send keepalive probes
    :param tcp_keepalive_interval: time between successive probes, once the
      initial wait time is over
    :param tcp_keepalive_count: number of probes to send before the connection
      is killed
    """

    # NOTE(praneshp): Despite keepalive being a tcp concept, the level is
    # still SOL_SOCKET. This is a quirk.
    if isinstance(tcp_keepalive, bool):
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, tcp_keepalive)
    else:
        raise TypeError("tcp_keepalive must be a boolean")

    if not tcp_keepalive:
        return

    # These options aren't available in the OS X version of eventlet,
    # Idle + Count * Interval effectively gives you the total timeout.
    if tcp_keepidle is not None:
        if hasattr(socket, 'TCP_KEEPIDLE'):
            sock.setsockopt(socket.IPPROTO_TCP,
                            socket.TCP_KEEPIDLE,
                            tcp_keepidle)
        else:
            LOG.warning(_LW('tcp_keepidle not available on your system'))
    if tcp_keepalive_interval is not None:
        if hasattr(socket, 'TCP_KEEPINTVL'):
            sock.setsockopt(socket.IPPROTO_TCP,
                            socket.TCP_KEEPINTVL,
                            tcp_keepalive_interval)
        else:
            LOG.warning(_LW('tcp_keepintvl not available on your system'))
    if tcp_keepalive_count is not None:
        if hasattr(socket, 'TCP_KEEPCNT'):
            sock.setsockopt(socket.IPPROTO_TCP,
                            socket.TCP_KEEPCNT,
                            tcp_keepalive_count)
        else:
            LOG.warning(_LW('tcp_keepcnt not available on your system'))
