# Copyright 2010-2013 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Utilities for memcache encryption and integrity check.

Data should be serialized before entering these functions. Encryption
has a dependency on the pycrypto. If pycrypto is not available,
CryptoUnavailableError will be raised.

This module will not be called unless signing or encryption is enabled
in the config. It will always validate signatures, and will decrypt
data if encryption is enabled. It is not valid to mix protection
modes.

"""

import base64
import functools
import hashlib
import hmac
import math
import os
import sys

import six

# make sure pycrypto is available
try:
    from Crypto.Cipher import AES
except ImportError:
    AES = None

HASH_FUNCTION = hashlib.sha384
DIGEST_LENGTH = HASH_FUNCTION().digest_size
DIGEST_SPLIT = DIGEST_LENGTH // 3
DIGEST_LENGTH_B64 = 4 * int(math.ceil(DIGEST_LENGTH / 3.0))


class InvalidMacError(Exception):
    """raise when unable to verify MACed data.

    This usually indicates that data had been expectedly modified in memcache.

    """
    pass


class DecryptError(Exception):
    """raise when unable to decrypt encrypted data.

    """
    pass


class CryptoUnavailableError(Exception):
    """raise when Python Crypto module is not available.

    """
    pass


def assert_crypto_availability(f):
    """Ensure Crypto module is available."""

    @functools.wraps(f)
    def wrapper(*args, **kwds):
        if AES is None:
            raise CryptoUnavailableError()
        return f(*args, **kwds)
    return wrapper


if sys.version_info >= (3, 3):
    constant_time_compare = hmac.compare_digest
else:
    def constant_time_compare(first, second):
        """Returns True if both string inputs are equal, otherwise False.

        This function should take a constant amount of time regardless of
        how many characters in the strings match.

        """
        if len(first) != len(second):
            return False
        result = 0
        if six.PY3 and isinstance(first, bytes) and isinstance(second, bytes):
            for x, y in zip(first, second):
                result |= x ^ y
        else:
            for x, y in zip(first, second):
                result |= ord(x) ^ ord(y)
        return result == 0


def derive_keys(token, secret, strategy):
    """Derives keys for MAC and ENCRYPTION from the user-provided
    secret. The resulting keys should be passed to the protect and
    unprotect functions.

    As suggested by NIST Special Publication 800-108, this uses the
    first 128 bits from the sha384 KDF for the obscured cache key
    value, the second 128 bits for the message authentication key and
    the remaining 128 bits for the encryption key.

    This approach is faster than computing a separate hmac as the KDF
    for each desired key.
    """
    digest = hmac.new(secret, token + strategy, HASH_FUNCTION).digest()
    return {'CACHE_KEY': digest[:DIGEST_SPLIT],
            'MAC': digest[DIGEST_SPLIT: 2 * DIGEST_SPLIT],
            'ENCRYPTION': digest[2 * DIGEST_SPLIT:],
            'strategy': strategy}


def sign_data(key, data):
    """Sign the data using the defined function and the derived key."""
    mac = hmac.new(key, data, HASH_FUNCTION).digest()
    return base64.b64encode(mac)


@assert_crypto_availability
def encrypt_data(key, data):
    """Encrypt the data with the given secret key.

    Padding is n bytes of the value n, where 1 <= n <= blocksize.
    """
    iv = os.urandom(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padding = 16 - len(data) % 16
    return iv + cipher.encrypt(data + six.int2byte(padding) * padding)


@assert_crypto_availability
def decrypt_data(key, data):
    """Decrypt the data with the given secret key."""
    iv = data[:16]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    try:
        result = cipher.decrypt(data[16:])
    except Exception:
        raise DecryptError('Encrypted data appears to be corrupted.')

    # Strip the last n padding bytes where n is the last value in
    # the plaintext
    return result[:-1 * six.byte2int([result[-1]])]


def protect_data(keys, data):
    """Given keys and serialized data, returns an appropriately
    protected string suitable for storage in the cache.

    """
    if keys['strategy'] == b'ENCRYPT':
        data = encrypt_data(keys['ENCRYPTION'], data)

    encoded_data = base64.b64encode(data)

    signature = sign_data(keys['MAC'], encoded_data)
    return signature + encoded_data


def unprotect_data(keys, signed_data):
    """Given keys and cached string data, verifies the signature,
    decrypts if necessary, and returns the original serialized data.

    """
    # cache backends return None when no data is found. We don't mind
    # that this particular special value is unsigned.
    if signed_data is None:
        return None

    # First we calculate the signature
    provided_mac = signed_data[:DIGEST_LENGTH_B64]
    calculated_mac = sign_data(
        keys['MAC'],
        signed_data[DIGEST_LENGTH_B64:])

    # Then verify that it matches the provided value
    if not constant_time_compare(provided_mac, calculated_mac):
        raise InvalidMacError('Invalid MAC; data appears to be corrupted.')

    data = base64.b64decode(signed_data[DIGEST_LENGTH_B64:])

    # then if necessary decrypt the data
    if keys['strategy'] == b'ENCRYPT':
        data = decrypt_data(keys['ENCRYPTION'], data)

    return data


def get_cache_key(keys):
    """Given keys generated by derive_keys(), returns a base64
    encoded value suitable for use as a cache key in memcached.

    """
    return base64.b64encode(keys['CACHE_KEY'])
