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

import os
import mimetypes

from libcloud.utils.py3 import PY3
from libcloud.utils.py3 import httplib
from libcloud.utils.py3 import next
from libcloud.utils.py3 import b

if PY3:
    from io import FileIO as file

CHUNK_SIZE = 8096

__all__ = [
    'read_in_chunks',
    'exhaust_iterator',
    'guess_file_mime_type'
]


def read_in_chunks(iterator, chunk_size=None, fill_size=False,
                   yield_empty=False):
    """
    Return a generator which yields data in chunks.

    :param terator: An object which implements an iterator interface
                     or a File like object with read method.
    :type iterator: :class:`object` which implements iterator interface.

    :param chunk_size: Optional chunk size (defaults to CHUNK_SIZE)
    :type chunk_size: ``int``

    :param fill_size: If True, make sure chunks are exactly chunk_size in
                      length (except for last chunk).
    :type fill_size: ``bool``

    :param yield_empty: If true and iterator returned no data, yield empty
                        bytes object before raising StopIteration.
    :type yield_empty: ``bool``

    TODO: At some point in the future we could use byte arrays here if version
    >= Python 3. This should speed things up a bit and reduce memory usage.
    """
    chunk_size = chunk_size or CHUNK_SIZE

    if isinstance(iterator, (file, httplib.HTTPResponse)):
        get_data = iterator.read
        args = (chunk_size, )
    else:
        get_data = next
        args = (iterator, )

    data = b('')
    empty = False

    while not empty or len(data) > 0:
        if not empty:
            try:
                chunk = b(get_data(*args))
                if len(chunk) > 0:
                    data += chunk
                else:
                    empty = True
            except StopIteration:
                empty = True

        if len(data) == 0:
            if empty and yield_empty:
                yield b('')

            raise StopIteration

        if fill_size:
            if empty or len(data) >= chunk_size:
                yield data[:chunk_size]
                data = data[chunk_size:]
        else:
            yield data
            data = b('')


def exhaust_iterator(iterator):
    """
    Exhaust an iterator and return all data returned by it.

    :type iterator: :class:`object` which implements iterator interface.
    :param response: An object which implements an iterator interface
                     or a File like object with read method.

    :rtype ``str``
    :return Data returned by the iterator.
    """
    data = b('')

    try:
        chunk = b(next(iterator))
    except StopIteration:
        chunk = b('')

    while len(chunk) > 0:
        data += chunk

        try:
            chunk = b(next(iterator))
        except StopIteration:
            chunk = b('')

    return data


def guess_file_mime_type(file_path):
    filename = os.path.basename(file_path)
    (mimetype, encoding) = mimetypes.guess_type(filename)
    return mimetype, encoding
