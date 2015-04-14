#-----------------------------------------------------------------------------
#   Copyright (c) 2008-2015, David P. D. Moss. All rights reserved.
#
#   Released under the BSD license. See the LICENSE file for details.
#-----------------------------------------------------------------------------
"""
Routines for dealing with nmap-style IPv4 address ranges.

Based on nmap's Target Specification :-

    http://nmap.org/book/man-target-specification.html
"""

from netaddr.core import AddrFormatError
from netaddr.ip import IPAddress
from netaddr.compat import _iter_range, _is_str


def _nmap_octet_target_values(spec):
    #   Generates sequence of values for an individual octet as defined in the
    #   nmap Target Specification.
    values = set()

    for element in spec.split(','):
        if '-' in element:
            left, right = element.split('-', 1)
            if not left:
                left = 0
            if not right:
                right = 255
            low = int(left)
            high = int(right)
            if not ((0 <= low <= 255) and (0 <= high <= 255)):
                raise ValueError('octet value overflow for spec %s!' % spec)
            if low > high:
                raise ValueError('left side of hyphen must be <= right %r' % element)
            for octet in _iter_range(low, high + 1):
                values.add(octet)
        else:
            octet = int(element)
            if not (0 <= octet <= 255):
                raise ValueError('octet value overflow for spec %s!' % spec)
            values.add(octet)

    return sorted(values)


def _generate_nmap_octet_ranges(nmap_target_spec):
    #   Generate 4 lists containing all octets defined by a given nmap Target
    #   specification.
    if not _is_str(nmap_target_spec):
        raise TypeError('string expected, not %s' % type(nmap_target_spec))

    if not nmap_target_spec:
        raise ValueError('nmap target specification cannot be blank!')

    tokens = nmap_target_spec.split('.')

    if len(tokens) != 4:
        raise AddrFormatError('invalid nmap range: %s' % nmap_target_spec)

    return (_nmap_octet_target_values(tokens[0]),
            _nmap_octet_target_values(tokens[1]),
            _nmap_octet_target_values(tokens[2]),
            _nmap_octet_target_values(tokens[3]))


def valid_nmap_range(nmap_target_spec):
    """
    :param nmap_target_spec: an nmap-style IP range target specification.

    :return: ``True`` if IP range target spec is valid, ``False`` otherwise.
    """
    try:
        _generate_nmap_octet_ranges(nmap_target_spec)
        return True
    except (TypeError, ValueError, AddrFormatError):
        pass
    return False


def iter_nmap_range(nmap_target_spec):
    """
    The nmap security tool supports a custom type of IPv4 range using multiple
    hyphenated octets. This generator provides iterators yielding IP addresses
    according to this rule set.

    :param nmap_target_spec: an nmap-style IP range target specification.

    :return: an iterator producing IPAddress objects for each IP in the range.
    """
    octet_ranges = _generate_nmap_octet_ranges(nmap_target_spec)
    for w in octet_ranges[0]:
        for x in octet_ranges[1]:
            for y in octet_ranges[2]:
                for z in octet_ranges[3]:
                    yield IPAddress("%d.%d.%d.%d" % (w, x, y, z), 4)

