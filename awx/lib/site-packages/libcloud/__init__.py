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
libcloud provides a unified interface to the cloud computing resources.

:var __version__: Current version of libcloud
"""

__all__ = ['__version__', 'enable_debug']
__version__ = '0.15.1'

import os

try:
    import paramiko
    have_paramiko = True
except ImportError:
    have_paramiko = False


def enable_debug(fo):
    """
    Enable library wide debugging to a file-like object.

    :param fo: Where to append debugging information
    :type fo: File like object, only write operations are used.
    """
    from libcloud.common.base import (Connection,
                                      LoggingHTTPConnection,
                                      LoggingHTTPSConnection)
    LoggingHTTPSConnection.log = fo
    LoggingHTTPConnection.log = fo
    Connection.conn_classes = (LoggingHTTPConnection,
                               LoggingHTTPSConnection)


def _init_once():
    """
    Utility function that is ran once on Library import.

    This checks for the LIBCLOUD_DEBUG environment variable, which if it exists
    is where we will log debug information about the provider transports.
    """
    path = os.getenv('LIBCLOUD_DEBUG')
    if path:
        fo = open(path, 'a')
        enable_debug(fo)

        if have_paramiko:
            paramiko.common.logging.basicConfig(level=paramiko.common.DEBUG)

_init_once()
