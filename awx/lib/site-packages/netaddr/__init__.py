#-----------------------------------------------------------------------------
#   Copyright (c) 2008-2015, David P. D. Moss. All rights reserved.
#
#   Released under the BSD license. See the LICENSE file for details.
#-----------------------------------------------------------------------------
"""A Python library for manipulating IP and EUI network addresses."""

#: Version info (major, minor, maintenance, status)
VERSION = (0, 7, 14)
STATUS = ''
__version__ = '%d.%d.%d' % VERSION[0:3] + STATUS

import sys as _sys

if _sys.version_info[0:2] < (2, 4):
    raise RuntimeError('Python 2.4.x or higher is required!')

from netaddr.core import AddrConversionError, AddrFormatError, \
    NotRegisteredError, ZEROFILL, Z, INET_PTON, P, NOHOST, N

from netaddr.ip import IPAddress, IPNetwork, IPRange, all_matching_cidrs, \
    cidr_abbrev_to_verbose, cidr_exclude, cidr_merge, iprange_to_cidrs, \
    iter_iprange, iter_unique_ips, largest_matching_cidr, \
    smallest_matching_cidr, spanning_cidr

from netaddr.ip.sets import IPSet

from netaddr.ip.glob import IPGlob, cidr_to_glob, glob_to_cidrs, \
    glob_to_iprange, glob_to_iptuple, iprange_to_globs, valid_glob

from netaddr.ip.nmap import valid_nmap_range, iter_nmap_range

from netaddr.ip.rfc1924 import base85_to_ipv6, ipv6_to_base85

from netaddr.eui import EUI, IAB, OUI

from netaddr.strategy.ipv4 import valid_str as valid_ipv4

from netaddr.strategy.ipv6 import valid_str as valid_ipv6, ipv6_compact, \
    ipv6_full, ipv6_verbose

from netaddr.strategy.eui48 import mac_eui48, mac_unix, mac_unix_expanded, \
        mac_cisco, mac_bare, mac_pgsql, valid_str as valid_mac

__all__ = [
    #   Constants.
    'ZEROFILL', 'Z', 'INET_PTON', 'P', 'NOHOST', 'N',

    #   Custom Exceptions.
    'AddrConversionError', 'AddrFormatError', 'NotRegisteredError',

    #   IP classes.
    'IPAddress', 'IPNetwork', 'IPRange', 'IPSet',

    #   IPv6 dialect classes.
    'ipv6_compact', 'ipv6_full', 'ipv6_verbose',

    #   IP functions and generators.
    'all_matching_cidrs', 'cidr_abbrev_to_verbose', 'cidr_exclude',
    'cidr_merge', 'iprange_to_cidrs', 'iter_iprange', 'iter_unique_ips',
    'largest_matching_cidr', 'smallest_matching_cidr', 'spanning_cidr',

    #   IP globbing class.
    'IPGlob',

    #   IP globbing functions.
    'cidr_to_glob', 'glob_to_cidrs', 'glob_to_iprange', 'glob_to_iptuple',
    'iprange_to_globs',

    #   IEEE EUI classes.
    'EUI', 'IAB', 'OUI',

    #   EUI-48 (MAC) dialect classes.
    'mac_bare', 'mac_cisco', 'mac_eui48', 'mac_pgsql', 'mac_unix',
    'mac_unix_expanded',

    #   Validation functions.
    'valid_ipv4', 'valid_ipv6', 'valid_glob', 'valid_mac',

    #   nmap-style range functions.
    'valid_nmap_range', 'iter_nmap_range',

    #   RFC 1924 functions.
    'base85_to_ipv6', 'ipv6_to_base85',
]
