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

from .exceptions import UnexpectedFrame
from .utils import get_errno, set_cloexec

_UNAVAIL = errno.EAGAIN, errno.EINTR

AMQP_PORT = 5672

EMPTY_BUFFER = bytes()

# Yes, Advanced Message Queuing Protocol Protocol is redundant
AMQP_PROTOCOL_HEADER = 'AMQP\x01\x01\x00\x09'.encode('latin_1')

# Match things like: [fe80::1]:5432, from RFC 2732
IPV6_LITERAL = re.compile(r'\[([\.0-9a-f:]+)\](?::(\d+))?')


class _AbstractTransport(object):
    """Common superclass for TCP and SSL transports"""
    connected = False

    def __init__(self, host, connect_timeout):
        self.connected = True
        msg = None
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
                try:
                    set_cloexec(self.sock, True)
                except NotImplementedError:
                    pass
                self.sock.settimeout(connect_timeout)
                self.sock.connect(sa)
            except socket.error as exc:
                msg = exc
                self.sock.close()
                self.sock = None
                last_err = msg
                continue
            break

        if not self.sock:
            # Didn't connect, return the most recent error message
            raise socket.error(last_err)

        try:
            self.sock.settimeout(None)
            self.sock.setsockopt(SOL_TCP, socket.TCP_NODELAY, 1)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

            self._setup_transport()

            self._write(AMQP_PROTOCOL_HEADER)
        except (OSError, IOError, socket.error) as exc:
            if get_errno(exc) not in _UNAVAIL:
                self.connected = False
            raise

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
        self.connected = False

    def read_frame(self, unpack=unpack):
        read = self._read
        try:
            frame_type, channel, size = unpack('>BHI', read(7, True))
            payload = read(size)
            ch = ord(read(1))
        except socket.timeout:
            raise
        except (OSError, IOError, socket.error) as exc:
            if get_errno(exc) not in _UNAVAIL:
                self.connected = False
            raise
        if ch == 206:  # '\xce'
            return frame_type, channel, payload
        else:
            raise UnexpectedFrame(
                'Received 0x{0:02x} while expecting 0xce'.format(ch))

    def write_frame(self, frame_type, channel, payload):
        size = len(payload)
        try:
            self._write(pack(
                '>BHI%dsB' % size,
                frame_type, channel, size, payload, 0xce,
            ))
        except socket.timeout:
            raise
        except (OSError, IOError, socket.error) as exc:
            if get_errno(exc) not in _UNAVAIL:
                self.connected = False
            raise


class SSLTransport(_AbstractTransport):
    """Transport that works over SSL"""

    def __init__(self, host, connect_timeout, ssl):
        if isinstance(ssl, dict):
            self.sslopts = ssl
        self._read_buffer = EMPTY_BUFFER
        super(SSLTransport, self).__init__(host, connect_timeout)

    def _setup_transport(self):
        """Wrap the socket in an SSL object, either the
        new Python 2.6 version, or the older Python 2.5 and
        lower version."""
        if HAVE_PY26_SSL:
            if hasattr(self, 'sslopts'):
                self.sock = ssl.wrap_socket(self.sock, **self.sslopts)
            else:
                self.sock = ssl.wrap_socket(self.sock)
            self.sock.do_handshake()
        else:
            self.sock = socket.ssl(self.sock)
        self._quick_recv = self.sock.read

    def _shutdown_transport(self):
        """Unwrap a Python 2.6 SSL socket, so we can call shutdown()"""
        if HAVE_PY26_SSL and self.sock is not None:
            try:
                unwrap = self.sock.unwrap
            except AttributeError:
                return
            self.sock = unwrap()

    def _read(self, n, initial=False,
              _errnos=(errno.ENOENT, errno.EAGAIN, errno.EINTR)):
        # According to SSL_read(3), it can at most return 16kb of data.
        # Thus, we use an internal read buffer like TCPTransport._read
        # to get the exact number of bytes wanted.
        recv = self._quick_recv
        rbuf = self._read_buffer
        try:
            while len(rbuf) < n:
                try:
                    s = recv(131072)  # see note above
                except socket.error as exc:
                    # ssl.sock.read may cause ENOENT if the
                    # operation couldn't be performed (Issue celery#1414).
                    if not initial and exc.errno in _errnos:
                        continue
                    raise
                if not s:
                    raise IOError('Socket closed')
                rbuf += s
        except:
            self._read_buffer = rbuf
            raise
        result, self._read_buffer = rbuf[:n], rbuf[n:]
        return result

    def _write(self, s):
        """Write a string out to the SSL socket fully."""
        write = self.sock.write
        while s:
            n = write(s)
            if not n:
                raise IOError('Socket closed')
            s = s[n:]


class TCPTransport(_AbstractTransport):
    """Transport that deals directly with TCP socket."""

    def _setup_transport(self):
        """Setup to _write() directly to the socket, and
        do our own buffered reads."""
        self._write = self.sock.sendall
        self._read_buffer = EMPTY_BUFFER
        self._quick_recv = self.sock.recv

    def _read(self, n, initial=False, _errnos=(errno.EAGAIN, errno.EINTR)):
        """Read exactly n bytes from the socket"""
        recv = self._quick_recv
        rbuf = self._read_buffer
        try:
            while len(rbuf) < n:
                try:
                    s = recv(131072)
                except socket.error as exc:
                    if not initial and exc.errno in _errnos:
                        continue
                    raise
                if not s:
                    raise IOError('Socket closed')
                rbuf += s
        except:
            self._read_buffer = rbuf
            raise

        result, self._read_buffer = rbuf[:n], rbuf[n:]
        return result


def create_transport(host, connect_timeout, ssl=False):
    """Given a few parameters from the Connection constructor,
    select and create a subclass of _AbstractTransport."""
    if ssl:
        return SSLTransport(host, connect_timeout, ssl)
    else:
        return TCPTransport(host, connect_timeout)
