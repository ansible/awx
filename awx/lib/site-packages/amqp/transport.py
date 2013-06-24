"""
Read/Write AMQP frames over network transports.

2009-01-14 Barry Pederson <bp@barryp.org>

"""
# Copyright (C) 2009 Barry Pederson <bp@barryp.org>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
from __future__ import absolute_import

import errno
import re
import socket

# Jython does not have this attribute
try:
    from socket import SOL_TCP
except ImportError:  # pragma: no cover
    from socket import IPPROTO_TCP as SOL_TCP  # noqa

#
# See if Python 2.6+ SSL support is available
#
try:
    import ssl
    HAVE_PY26_SSL = True
except:
    HAVE_PY26_SSL = False

try:
    bytes
except:
    # Python 2.5 and lower
    bytes = str

from struct import pack, unpack

from .exceptions import AMQPError

AMQP_PORT = 5672

# Yes, Advanced Message Queuing Protocol Protocol is redundant
AMQP_PROTOCOL_HEADER = 'AMQP\x01\x01\x00\x09'.encode('latin_1')

# Match things like: [fe80::1]:5432, from RFC 2732
IPV6_LITERAL = re.compile(r'\[([\.0-9a-f:]+)\](?::(\d+))?')


class _AbstractTransport(object):
    """Common superclass for TCP and SSL transports"""

    def __init__(self, host, connect_timeout):
        msg = 'socket.getaddrinfo() for %s returned an empty list' % host
        port = AMQP_PORT

        m = IPV6_LITERAL.match(host)
        if m:
            host = m.group(1)
            if m.group(2):
                port = int(m.group(2))
        else:
            if ':' in host:
                host, port = host.rsplit(':', 1)
                port = int(port)

        self.sock = None
        last_err = None
        for res in socket.getaddrinfo(host, port, 0,
                                      socket.SOCK_STREAM, SOL_TCP):
            af, socktype, proto, canonname, sa = res
            try:
                self.sock = socket.socket(af, socktype, proto)
                self.sock.settimeout(connect_timeout)
                self.sock.connect(sa)
            except socket.error, msg:
                self.sock.close()
                self.sock = None
                last_err = msg
                continue
            break

        if not self.sock:
            # Didn't connect, return the most recent error message
            raise socket.error(last_err)

        self.sock.settimeout(None)
        self.sock.setsockopt(SOL_TCP, socket.TCP_NODELAY, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

        self._setup_transport()

        self._write(AMQP_PROTOCOL_HEADER)

    def __del__(self):
        try:
            self.close()
        except socket.error:
            pass
        finally:
            self.sock = None

    def _read(self, n, initial=False):
        """Read exactly n bytes from the peer"""
        raise NotImplementedError('Must be overriden in subclass')

    def _setup_transport(self):
        """Do any additional initialization of the class (used
        by the subclasses)."""
        pass

    def _shutdown_transport(self):
        """Do any preliminary work in shutting down the connection."""
        pass

    def _write(self, s):
        """Completely write a string to the peer."""
        raise NotImplementedError('Must be overriden in subclass')

    def close(self):
        if self.sock is not None:
            self._shutdown_transport()
            # Call shutdown first to make sure that pending messages
            # reach the AMQP broker if the program exits after
            # calling this method.
            self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()
            self.sock = None

    def read_frame(self):
        """Read an AMQP frame."""
        frame_type, channel, size = unpack('>BHI', self._read(7, True))
        payload = self._read(size)
        ch = ord(self._read(1))
        if ch == 206:  # '\xce'
            return frame_type, channel, payload
        else:
            raise AMQPError(
                'Framing Error, received 0x%02x while expecting 0xce' % ch)

    def write_frame(self, frame_type, channel, payload):
        """Write out an AMQP frame."""
        size = len(payload)
        self._write(
            pack('>BHI%dsB' % size, frame_type, channel, size, payload, 0xce),
        )


class SSLTransport(_AbstractTransport):
    """Transport that works over SSL"""

    def __init__(self, host, connect_timeout, ssl):
        if isinstance(ssl, dict):
            self.sslopts = ssl
        self.sslobj = None
        super(SSLTransport, self).__init__(host, connect_timeout)

    def _setup_transport(self):
        """Wrap the socket in an SSL object, either the
        new Python 2.6 version, or the older Python 2.5 and
        lower version."""
        if HAVE_PY26_SSL:
            if hasattr(self, 'sslopts'):
                self.sslobj = ssl.wrap_socket(self.sock, **self.sslopts)
            else:
                self.sslobj = ssl.wrap_socket(self.sock)
            self.sslobj.do_handshake()
        else:
            self.sslobj = socket.ssl(self.sock)

    def _shutdown_transport(self):
        """Unwrap a Python 2.6 SSL socket, so we can call shutdown()"""
        if HAVE_PY26_SSL and (self.sslobj is not None):
            self.sock = self.sslobj.unwrap()
            self.sslobj = None

    def _read(self, n, initial=False):
        """It seems that SSL Objects read() method may not supply as much
        as you're asking for, at least with extremely large messages.
        somewhere > 16K - found this in the test_channel.py test_large
        unittest."""
        result = ''

        while len(result) < n:
            try:
                s = self.sslobj.read(n - len(result))
            except socket.error, exc:
                if not initial and exc.errno in (errno.EAGAIN, errno.EINTR):
                    continue
                raise
            if not s:
                raise IOError('Socket closed')
            result += s

        return result

    def _write(self, s):
        """Write a string out to the SSL socket fully."""
        while s:
            n = self.sslobj.write(s)
            if not n:
                raise IOError('Socket closed')
            s = s[n:]


class TCPTransport(_AbstractTransport):
    """Transport that deals directly with TCP socket."""

    def _setup_transport(self):
        """Setup to _write() directly to the socket, and
        do our own buffered reads."""
        self._write = self.sock.sendall
        self._read_buffer = bytes()

    def _read(self, n, initial=False):
        """Read exactly n bytes from the socket"""
        while len(self._read_buffer) < n:
            try:
                s = self.sock.recv(65536)
            except socket.error, exc:
                if not initial and exc.errno in (errno.EAGAIN, errno.EINTR):
                    continue
                raise
            if not s:
                raise IOError('Socket closed')
            self._read_buffer += s

        result = self._read_buffer[:n]
        self._read_buffer = self._read_buffer[n:]

        return result


def create_transport(host, connect_timeout, ssl=False):
    """Given a few parameters from the Connection constructor,
    select and create a subclass of _AbstractTransport."""
    if ssl:
        return SSLTransport(host, connect_timeout, ssl)
    else:
        return TCPTransport(host, connect_timeout)
