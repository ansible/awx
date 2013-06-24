#
# Module to allow connection and socket objects to be transferred
# between processes
#
# multiprocessing/reduction.py
#
# Copyright (c) 2006-2008, R Oudkerk
# Licensed to PSF under a Contributor Agreement.
#

from __future__ import absolute_import

__all__ = []

import os
import sys
import socket
import threading

if sys.version_info[0] == 3:
    from multiprocessing.connection import Client, Listener
else:
    from billiard._connection import Client, Listener  # noqa

from . import current_process
from ._ext import _billiard, win32
from .forking import Popen, duplicate, close, ForkingPickler
from .util import register_after_fork, debug, sub_debug

if not(sys.platform == 'win32' or hasattr(_billiard, 'recvfd')):
    raise ImportError('pickling of connections not supported')


# globals set later
_listener = None
_lock = None
_cache = set()

#
# Platform specific definitions
#

if sys.platform == 'win32':
    # XXX Should this subprocess import be here?
    import _subprocess  # noqa

    def send_handle(conn, handle, destination_pid):
        process_handle = win32.OpenProcess(
            win32.PROCESS_ALL_ACCESS, False, destination_pid
        )
        try:
            new_handle = duplicate(handle, process_handle)
            conn.send(new_handle)
        finally:
            close(process_handle)

    def recv_handle(conn):
        return conn.recv()

else:
    def send_handle(conn, handle, destination_pid):  # noqa
        _billiard.sendfd(conn.fileno(), handle)

    def recv_handle(conn):  # noqa
        return _billiard.recvfd(conn.fileno())

#
# Support for a per-process server thread which caches pickled handles
#


def _reset(obj):
    global _lock, _listener, _cache
    for h in _cache:
        close(h)
    _cache.clear()
    _lock = threading.Lock()
    _listener = None

_reset(None)
register_after_fork(_reset, _reset)


def _get_listener():
    global _listener

    if _listener is None:
        _lock.acquire()
        try:
            if _listener is None:
                debug('starting listener and thread for sending handles')
                _listener = Listener(authkey=current_process().authkey)
                t = threading.Thread(target=_serve)
                t.daemon = True
                t.start()
        finally:
            _lock.release()

    return _listener


def _serve():
    from .util import is_exiting, sub_warning

    while 1:
        try:
            conn = _listener.accept()
            handle_wanted, destination_pid = conn.recv()
            _cache.remove(handle_wanted)
            send_handle(conn, handle_wanted, destination_pid)
            close(handle_wanted)
            conn.close()
        except:
            if not is_exiting():
                sub_warning('thread for sharing handles raised exception',
                            exc_info=True)

#
# Functions to be used for pickling/unpickling objects with handles
#


def reduce_handle(handle):
    if Popen.thread_is_spawning():
        return (None, Popen.duplicate_for_child(handle), True)
    dup_handle = duplicate(handle)
    _cache.add(dup_handle)
    sub_debug('reducing handle %d', handle)
    return (_get_listener().address, dup_handle, False)


def rebuild_handle(pickled_data):
    address, handle, inherited = pickled_data
    if inherited:
        return handle
    sub_debug('rebuilding handle %d', handle)
    conn = Client(address, authkey=current_process().authkey)
    conn.send((handle, os.getpid()))
    new_handle = recv_handle(conn)
    conn.close()
    return new_handle

#
# Register `_billiard.Connection` with `ForkingPickler`
#


def reduce_connection(conn):
    rh = reduce_handle(conn.fileno())
    return rebuild_connection, (rh, conn.readable, conn.writable)


def rebuild_connection(reduced_handle, readable, writable):
    handle = rebuild_handle(reduced_handle)
    return _billiard.Connection(
        handle, readable=readable, writable=writable
    )

ForkingPickler.register(_billiard.Connection, reduce_connection)

#
# Register `socket.socket` with `ForkingPickler`
#


def fromfd(fd, family, type_, proto=0):
    s = socket.fromfd(fd, family, type_, proto)
    if s.__class__ is not socket.socket:
        s = socket.socket(_sock=s)
    return s


def reduce_socket(s):
    reduced_handle = reduce_handle(s.fileno())
    return rebuild_socket, (reduced_handle, s.family, s.type, s.proto)


def rebuild_socket(reduced_handle, family, type_, proto):
    fd = rebuild_handle(reduced_handle)
    _sock = fromfd(fd, family, type_, proto)
    close(fd)
    return _sock
ForkingPickler.register(socket.socket, reduce_socket)

#
# Register `_billiard.PipeConnection` with `ForkingPickler`
#

if sys.platform == 'win32':

    def reduce_pipe_connection(conn):
        rh = reduce_handle(conn.fileno())
        return rebuild_pipe_connection, (rh, conn.readable, conn.writable)

    def rebuild_pipe_connection(reduced_handle, readable, writable):
        handle = rebuild_handle(reduced_handle)
        return _billiard.PipeConnection(
            handle, readable=readable, writable=writable
        )
    ForkingPickler.register(_billiard.PipeConnection, reduce_pipe_connection)
