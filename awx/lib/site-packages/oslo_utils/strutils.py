# Copyright 2011 OpenStack Foundation.
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
System-level utilities and helper functions.
"""

import math
import re
import unicodedata

import six

from oslo_utils._i18n import _
from oslo_utils import encodeutils


UNIT_PREFIX_EXPONENT = {
    'k': 1,
    'K': 1,
    'Ki': 1,
    'M': 2,
    'Mi': 2,
    'G': 3,
    'Gi': 3,
    'T': 4,
    'Ti': 4,
}
UNIT_SYSTEM_INFO = {
    'IEC': (1024, re.compile(r'(^[-+]?\d*\.?\d+)([KMGT]i?)?(b|bit|B)$')),
    'SI': (1000, re.compile(r'(^[-+]?\d*\.?\d+)([kMGT])?(b|bit|B)$')),
}

TRUE_STRINGS = ('1', 't', 'true', 'on', 'y', 'yes')
FALSE_STRINGS = ('0', 'f', 'false', 'off', 'n', 'no')

SLUGIFY_STRIP_RE = re.compile(r"[^\w\s-]")
SLUGIFY_HYPHENATE_RE = re.compile(r"[-\s]+")


# NOTE(flaper87): The following globals are used by `mask_password`
_SANITIZE_KEYS = ['adminPass', 'admin_pass', 'password', 'admin_password',
                  'auth_token', 'new_pass', 'auth_password', 'secret_uuid']

# NOTE(ldbragst): Let's build a list of regex objects using the list of
# _SANITIZE_KEYS we already have. This way, we only have to add the new key
# to the list of _SANITIZE_KEYS and we can generate regular expressions
# for XML and JSON automatically.
_SANITIZE_PATTERNS_2 = {}
_SANITIZE_PATTERNS_1 = {}

# NOTE(amrith): Some regular expressions have only one parameter, some
# have two parameters. Use different lists of patterns here.
_FORMAT_PATTERNS_1 = [r'(%(key)s\s*[=]\s*)[^\s^\'^\"]+']
_FORMAT_PATTERNS_2 = [r'(%(key)s\s*[=]\s*[\"\'])[^\"\']*([\"\'])',
                      r'(%(key)s\s+[\"\'])[^\"\']*([\"\'])',
                      r'([-]{2}%(key)s\s+)[^\'^\"^=^\s]+([\s]*)',
                      r'(<%(key)s>)[^<]*(</%(key)s>)',
                      r'([\"\']%(key)s[\"\']\s*:\s*[\"\'])[^\"\']*([\"\'])',
                      r'([\'"][^"\']*%(key)s[\'"]\s*:\s*u?[\'"])[^\"\']*'
                      '([\'"])',
                      r'([\'"][^\'"]*%(key)s[\'"]\s*,\s*\'--?[A-z]+\'\s*,\s*u?'
                      '[\'"])[^\"\']*([\'"])',
                      r'(%(key)s\s*--?[A-z]+\s*)\S+(\s*)']

# NOTE(dhellmann): Keep a separate list of patterns by key so we only
# need to apply the substitutions for keys we find using a quick "in"
# test.
for key in _SANITIZE_KEYS:
    _SANITIZE_PATTERNS_1[key] = []
    _SANITIZE_PATTERNS_2[key] = []

    for pattern in _FORMAT_PATTERNS_2:
        reg_ex = re.compile(pattern % {'key': key}, re.DOTALL)
        _SANITIZE_PATTERNS_2[key].append(reg_ex)

    for pattern in _FORMAT_PATTERNS_1:
        reg_ex = re.compile(pattern % {'key': key}, re.DOTALL)
        _SANITIZE_PATTERNS_1[key].append(reg_ex)


def int_from_bool_as_string(subject):
    """Interpret a string as a boolean and return either 1 or 0.

    Any string value in:

        ('True', 'true', 'On', 'on', '1')

    is interpreted as a boolean True.

    Useful for JSON-decoded stuff and config file parsing
    """
    return int(bool_from_string(subject))


def bool_from_string(subject, strict=False, default=False):
    """Interpret a string as a boolean.

    A case-insensitive match is performed such that strings matching 't',
    'true', 'on', 'y', 'yes', or '1' are considered True and, when
    `strict=False`, anything else returns the value specified by 'default'.

    Useful for JSON-decoded stuff and config file parsing.

    If `strict=True`, unrecognized values, including None, will raise a
    ValueError which is useful when parsing values passed in from an API call.
    Strings yielding False are 'f', 'false', 'off', 'n', 'no', or '0'.
    """
    if not isinstance(subject, six.string_types):
        subject = six.text_type(subject)

    lowered = subject.strip().lower()

    if lowered in TRUE_STRINGS:
        return True
    elif lowered in FALSE_STRINGS:
        return False
    elif strict:
        acceptable = ', '.join(
            "'%s'" % s for s in sorted(TRUE_STRINGS + FALSE_STRINGS))
        msg = _("Unrecognized value '%(val)s', acceptable values are:"
                " %(acceptable)s") % {'val': subject,
                                      'acceptable': acceptable}
        raise ValueError(msg)
    else:
        return default


def string_to_bytes(text, unit_system='IEC', return_int=False):
    """Converts a string into an float representation of bytes.

    The units supported for IEC ::

        Kb(it), Kib(it), Mb(it), Mib(it), Gb(it), Gib(it), Tb(it), Tib(it)
        KB, KiB, MB, MiB, GB, GiB, TB, TiB

    The units supported for SI ::

        kb(it), Mb(it), Gb(it), Tb(it)
        kB, MB, GB, TB

    Note that the SI unit system does not support capital letter 'K'

    :param text: String input for bytes size conversion.
    :param unit_system: Unit system for byte size conversion.
    :param return_int: If True, returns integer representation of text
                       in bytes. (default: decimal)
    :returns: Numerical representation of text in bytes.
    :raises ValueError: If text has an invalid value.

    """
    try:
        base, reg_ex = UNIT_SYSTEM_INFO[unit_system]
    except KeyError:
        msg = _('Invalid unit system: "%s"') % unit_system
        raise ValueError(msg)
    match = reg_ex.match(text)
    if match:
        magnitude = float(match.group(1))
        unit_prefix = match.group(2)
        if match.group(3) in ['b', 'bit']:
            magnitude /= 8
    else:
        msg = _('Invalid string format: %s') % text
        raise ValueError(msg)
    if not unit_prefix:
        res = magnitude
    else:
        res = magnitude * pow(base, UNIT_PREFIX_EXPONENT[unit_prefix])
    if return_int:
        return int(math.ceil(res))
    return res


def to_slug(value, incoming=None, errors="strict"):
    """Normalize string.

    Convert to lowercase, remove non-word characters, and convert spaces
    to hyphens.

    Inspired by Django's `slugify` filter.

    :param value: Text to slugify
    :param incoming: Text's current encoding
    :param errors: Errors handling policy. See here for valid
        values http://docs.python.org/2/library/codecs.html
    :returns: slugified unicode representation of `value`
    :raises TypeError: If text is not an instance of str
    """
    value = encodeutils.safe_decode(value, incoming, errors)
    # NOTE(aababilov): no need to use safe_(encode|decode) here:
    # encodings are always "ascii", error handling is always "ignore"
    # and types are always known (first: unicode; second: str)
    value = unicodedata.normalize("NFKD", value).encode(
        "ascii", "ignore").decode("ascii")
    value = SLUGIFY_STRIP_RE.sub("", value).strip().lower()
    return SLUGIFY_HYPHENATE_RE.sub("-", value)


def mask_password(message, secret="***"):
    """Replace password with 'secret' in message.

    :param message: The string which includes security information.
    :param secret: value with which to replace passwords.
    :returns: The unicode value of message with the password fields masked.

    For example:

    >>> mask_password("'adminPass' : 'aaaaa'")
    "'adminPass' : '***'"
    >>> mask_password("'admin_pass' : 'aaaaa'")
    "'admin_pass' : '***'"
    >>> mask_password('"password" : "aaaaa"')
    '"password" : "***"'
    >>> mask_password("'original_password' : 'aaaaa'")
    "'original_password' : '***'"
    >>> mask_password("u'original_password' :   u'aaaaa'")
    "u'original_password' :   u'***'"
    """

    try:
        message = six.text_type(message)
    except UnicodeDecodeError:
        # NOTE(jecarey): Temporary fix to handle cases where message is a
        # byte string. A better solution will be provided in Kilo.
        pass

    substitute1 = r'\g<1>' + secret
    substitute2 = r'\g<1>' + secret + r'\g<2>'

    # NOTE(ldbragst): Check to see if anything in message contains any key
    # specified in _SANITIZE_KEYS, if not then just return the message since
    # we don't have to mask any passwords.
    for key in _SANITIZE_KEYS:
        if key in message:
            for pattern in _SANITIZE_PATTERNS_2[key]:
                message = re.sub(pattern, substitute2, message)
            for pattern in _SANITIZE_PATTERNS_1[key]:
                message = re.sub(pattern, substitute1, message)

    return message


def is_int_like(val):
    """Check if a value looks like an integer with base 10.

    :param val: Value to verify
    :type val: string
    :returns: bool
    """
    try:
        return six.text_type(int(val)) == six.text_type(val)
    except (TypeError, ValueError):
        return False
