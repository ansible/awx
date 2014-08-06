# Copyright (c) 2010-2012 OpenStack, LLC.
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
"""Miscellaneous utility functions for use with Swift."""
import hashlib
import hmac
import logging
import time

import six

TRUE_VALUES = set(('true', '1', 'yes', 'on', 't', 'y'))


def config_true_value(value):
    """
    Returns True if the value is either True or a string in TRUE_VALUES.
    Returns False otherwise.
    This function come from swift.common.utils.config_true_value()
    """
    return value is True or \
        (isinstance(value, six.string_types) and value.lower() in TRUE_VALUES)


def prt_bytes(bytes, human_flag):
    """
    convert a number > 1024 to printable format, either in 4 char -h format as
    with ls -lh or return as 12 char right justified string
    """

    if human_flag:
        suffix = ''
        mods = list('KMGTPEZY')
        temp = float(bytes)
        if temp > 0:
            while (temp > 1023):
                try:
                    suffix = mods.pop(0)
                except IndexError:
                    break
                temp /= 1024.0
            if suffix != '':
                if temp >= 10:
                    bytes = '%3d%s' % (temp, suffix)
                else:
                    bytes = '%.1f%s' % (temp, suffix)
        if suffix == '':    # must be < 1024
            bytes = '%4s' % bytes
    else:
        bytes = '%12s' % bytes

    return(bytes)


def generate_temp_url(path, seconds, key, method):
    """ Generates a temporary URL that gives unauthenticated access to the
    Swift object.

    :param path: The full path to the Swift object. Example:
    /v1/AUTH_account/c/o.
    :param seconds: The amount of time in seconds the temporary URL will
    be valid for.
    :param key: The secret temporary URL key set on the Swift cluster.
    To set a key, run 'swift post -m
    "Temp-URL-Key:b3968d0207b54ece87cccc06515a89d4"'
    :param method: A HTTP method, typically either GET or PUT, to allow for
    this temporary URL.
    :raises: ValueError if seconds is not a positive integer
    :raises: TypeError if seconds is not an integer
    :return: the path portion of a temporary URL
    """
    if seconds < 0:
        raise ValueError('seconds must be a positive integer')
    try:
        expiration = int(time.time() + seconds)
    except TypeError:
        raise TypeError('seconds must be an integer')

    standard_methods = ['GET', 'PUT', 'HEAD', 'POST', 'DELETE']
    if method.upper() not in standard_methods:
        logger = logging.getLogger("swiftclient")
        logger.warning('Non default HTTP method %s for tempurl specified, '
                       'possibly an error', method.upper())

    hmac_body = '\n'.join([method.upper(), str(expiration), path])

    # Encode to UTF-8 for py3 compatibility
    sig = hmac.new(key.encode(),
                   hmac_body.encode(),
                   hashlib.sha1).hexdigest()

    return ('{path}?temp_url_sig='
            '{sig}&temp_url_expires={exp}'.format(
                path=path,
                sig=sig,
                exp=expiration)
            )


class LengthWrapper(object):

    def __init__(self, readable, length):
        self._length = self._remaining = length
        self._readable = readable

    def __len__(self):
        return self._length

    def read(self, *args, **kwargs):
        if self._remaining <= 0:
            return ''
        chunk = self._readable.read(
            *args, **kwargs)[:self._remaining]
        self._remaining -= len(chunk)
        return chunk
