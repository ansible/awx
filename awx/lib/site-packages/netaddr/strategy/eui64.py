#-----------------------------------------------------------------------------
#   Copyright (c) 2008-2015, David P. D. Moss. All rights reserved.
#
#   Released under the BSD license. See the LICENSE file for details.
#-----------------------------------------------------------------------------
"""
IEEE 64-bit EUI (Extended Unique Indentifier) logic.
"""
import struct as _struct
import re as _re

#   This is a fake constant that doesn't really exist. Here for completeness.
AF_EUI64 = 64

from netaddr.core import AddrFormatError
from netaddr.compat import _is_str
from netaddr.strategy import \
    valid_words  as _valid_words, \
    int_to_words as _int_to_words, \
    words_to_int as _words_to_int, \
    valid_bits   as _valid_bits, \
    bits_to_int  as _bits_to_int, \
    int_to_bits  as _int_to_bits, \
    valid_bin    as _valid_bin, \
    int_to_bin   as _int_to_bin, \
    bin_to_int   as _bin_to_int

#: The width (in bits) of this address type.
width = 64

#: The individual word size (in bits) of this address type.
word_size = 8

#: The format string to be used when converting words to string values.
word_fmt = '%.2X'

#: The separator character used between each word.
word_sep = '-'

#: The AF_* constant value of this address type.
family = AF_EUI64

#: A friendly string name address type.
family_name = 'EUI-64'

#: The version of this address type.
version = 64

#: The number base to be used when interpreting word values as integers.
word_base = 16

#: The maximum integer value that can be represented by this address type.
max_int = 2 ** width - 1

#: The number of words in this address type.
num_words = width // word_size

#: The maximum integer value for an individual word in this address type.
max_word = 2 ** word_size - 1

#: Compiled regular expression for detecting value EUI-64 identifiers.
RE_EUI64_FORMATS = [
    _re.compile('^' + ':'.join(['([0-9A-F]{1,2})'] * 8) + '$', _re.IGNORECASE),
    _re.compile('^' + '-'.join(['([0-9A-F]{1,2})'] * 8) + '$', _re.IGNORECASE),
    _re.compile('^(' + '[0-9A-F]' * 16 + ')$', _re.IGNORECASE),
]


def _get_match_result(address, formats):
    for regexp in formats:
        match = regexp.findall(address)
        if match:
            return match[0]

def valid_str(addr):
    """
    :param addr: An IEEE EUI-64 indentifier in string form.

    :return: ``True`` if EUI-64 indentifier is valid, ``False`` otherwise.
    """
    try:
        if _get_match_result(addr, RE_EUI64_FORMATS):
            return True
    except TypeError:
        pass

    return False


def str_to_int(addr):
    """
    :param addr: An IEEE EUI-64 indentifier in string form.

    :return: An unsigned integer that is equivalent to value represented
        by EUI-64 string identifier.
    """
    words = []

    try:
        words = _get_match_result(addr, RE_EUI64_FORMATS)
        if not words:
            raise TypeError
    except TypeError:
        raise AddrFormatError('invalid IEEE EUI-64 identifier: %r!' % addr)

    if _is_str(words):
        return int(words, 16)
    if len(words) != num_words:
        raise AddrFormatError('bad word count for EUI-64 identifier: %r!' \
            % addr)

    return int(''.join(['%.2x' % int(w, 16) for w in words]), 16)


def int_to_str(int_val, dialect=None):
    """
    :param int_val: An unsigned integer.

    :param dialect: (optional) a Python class defining formatting options
        (Please Note - not currently in use).

    :return: An IEEE EUI-64 identifier that is equivalent to unsigned integer.
    """
    words = int_to_words(int_val)
    tokens = [word_fmt % i for i in words]
    addr = word_sep.join(tokens)
    return addr


def int_to_packed(int_val):
    """
    :param int_val: the integer to be packed.

    :return: a packed string that is equivalent to value represented by an
    unsigned integer.
    """
    words = int_to_words(int_val)
    return _struct.pack('>8B', *words)


def packed_to_int(packed_int):
    """
    :param packed_int: a packed string containing an unsigned integer.
        It is assumed that string is packed in network byte order.

    :return: An unsigned integer equivalent to value of network address
        represented by packed binary string.
    """
    words = list(_struct.unpack('>8B', packed_int))

    int_val = 0
    for i, num in enumerate(reversed(words)):
        word = num
        word = word << 8 * i
        int_val = int_val | word

    return int_val


def valid_words(words, dialect=None):
    return _valid_words(words, word_size, num_words)


def int_to_words(int_val, dialect=None):
    return _int_to_words(int_val, word_size, num_words)


def words_to_int(words, dialect=None):
    return _words_to_int(words, word_size, num_words)


def valid_bits(bits, dialect=None):
    return _valid_bits(bits, width, word_sep)


def bits_to_int(bits, dialect=None):
    return _bits_to_int(bits, width, word_sep)


def int_to_bits(int_val, dialect=None):
    return _int_to_bits(int_val, word_size, num_words, word_sep)


def valid_bin(bin_val):
    return _valid_bin(bin_val, width)


def int_to_bin(int_val):
    return _int_to_bin(int_val, width)


def bin_to_int(bin_val):
    return _bin_to_int(bin_val, width)
