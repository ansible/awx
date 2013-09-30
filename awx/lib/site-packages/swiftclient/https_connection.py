# Copyright (c) 2013 OpenStack, LLC.
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
HTTPS/SSL related functionality
"""

import socket

from httplib import HTTPSConnection

import OpenSSL

try:
    from eventlet.green.OpenSSL.SSL import GreenConnection
    from eventlet.greenio import GreenSocket
    from eventlet.patcher import is_monkey_patched

    def getsockopt(self, *args, **kwargs):
        return self.fd.getsockopt(*args, **kwargs)
    # The above is a workaround for an eventlet bug in getsockopt.
    # TODO(mclaren): Workaround can be removed when this fix lands:
    # https://bitbucket.org/eventlet/eventlet/commits/609f230
    GreenSocket.getsockopt = getsockopt
except ImportError:
    def is_monkey_patched(*args):
        return False


class HTTPSConnectionNoSSLComp(HTTPSConnection):
    """
    Extended HTTPSConnection which uses the OpenSSL library
    for disabling SSL compression.
    Note: This functionality can eventually be replaced
          with native Python 3.3 code.
    """
    def __init__(self, host):
        HTTPSConnection.__init__(self, host)
        self.setcontext()

    def setcontext(self):
        """
        Set up the OpenSSL context.
        """
        self.context = OpenSSL.SSL.Context(OpenSSL.SSL.SSLv23_METHOD)
        # Disable SSL layer compression.
        self.context.set_options(0x20000)  # SSL_OP_NO_COMPRESSION

    def connect(self):
        """
        Connect to an SSL port using the OpenSSL library and apply
        per-connection parameters.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock = OpenSSLConnectionDelegator(self.context, sock)
        self.sock.connect((self.host, self.port))


class OpenSSLConnectionDelegator(object):
    """
    An OpenSSL.SSL.Connection delegator.

    Supplies an additional 'makefile' method which httplib requires
    and is not present in OpenSSL.SSL.Connection.

    Note: Since it is not possible to inherit from OpenSSL.SSL.Connection
    a delegator must be used.
    """
    def __init__(self, *args, **kwargs):
        if is_monkey_patched('socket'):
            # If we are running in a monkey patched environment
            # use eventlet's GreenConnection -- it handles eventlet's
            # non-blocking sockets correctly.
            Connection = GreenConnection
        else:
            Connection = OpenSSL.SSL.Connection
        self.connection = Connection(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self.connection, name)

    def makefile(self, *args, **kwargs):
        return socket._fileobject(self.connection, *args, **kwargs)
