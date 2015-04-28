# Copyright (c) 2014, Ansible, Inc.
# All Rights Reserved.

import os

import zmq

from django.conf import settings


class Socket(object):
    """An abstraction class implemented for a dumb OS socket.

    Intended to allow alteration of backend details in a single, consistent
    way throughout the Tower application.
    """
    def __init__(self, bucket, rw, debug=0, logger=None, nowait=False):
        """Instantiate a Socket object, which uses ZeroMQ to actually perform
        passing a message back and forth.

        Designed to be used as a context manager:

            with Socket('callbacks', 'w') as socket:
                socket.publish({'message': 'foo bar baz'})

        If listening for messages through a socket, the `listen` method
        is a simple generator:

            with Socket('callbacks', 'r') as socket:
                for message in socket.listen():
                    [...]
        """
        self._bucket = bucket
        self._rw = {
            'r': zmq.REP,
            'w': zmq.REQ,
        }[rw.lower()]

        self._connection_pid = None
        self._context = None
        self._socket = None

        self._debug = debug
        self._logger = logger
        self._nowait = nowait

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args, **kwargs):
        self.close()

    @property
    def is_connected(self):
        if self._socket:
            return True
        return False

    @property
    def port(self):
        return {
            'callbacks': os.environ.get('CALLBACK_CONSUMER_PORT',
                                        settings.CALLBACK_CONSUMER_PORT),
            'task_commands': settings.TASK_COMMAND_PORT,
            'websocket': settings.SOCKETIO_NOTIFICATION_PORT,
            'fact_cache': settings.FACT_CACHE_PORT,
        }[self._bucket]

    def connect(self):
        """Connect to ZeroMQ."""

        # Make sure that we are clearing everything out if there is
        # a problem; PID crossover can cause bad news.
        active_pid = os.getpid()
        if self._connection_pid is None:
            self._connection_pid = active_pid
        if self._connection_pid != active_pid:
            self._context = None
            self._socket = None
            self._connection_pid = active_pid

        # If the port is an integer, convert it into tcp://
        port = self.port
        if isinstance(port, int):
            port = 'tcp://127.0.0.1:%d' % port

        # If the port is None, then this is an intentional dummy;
        # honor this. (For testing.)
        if not port:
            return

        # Okay, create the connection.
        if self._context is None:
            self._context = zmq.Context()
            self._socket = self._context.socket(self._rw)
            if self._nowait:
                self._socket.setsockopt(zmq.RCVTIMEO, 2000)
                self._socket.setsockopt(zmq.LINGER, 1000)
            if self._rw == zmq.REQ:
                self._socket.connect(port)
            else:
                self._socket.bind(port)

    def close(self):
        """Disconnect and tear down."""
        if self._socket:
            self._socket.close()
        self._socket = None
        self._context = None

    def publish(self, message):
        """Publish a message over the socket."""

        # If the port is None, no-op.
        if self.port is None:
            return

        # If we are not connected, whine.
        if not self.is_connected:
            raise RuntimeError('Cannot publish a message when not connected '
                               'to the socket.')

        # If we are in the wrong mode, whine.
        if self._rw != zmq.REQ:
            raise RuntimeError('This socket is not opened for writing.')

        # If we are in debug mode; provide the PID.
        if self._debug:
            message.update({'pid': os.getpid(),
                            'connection_pid': self._connection_pid})

        # Send the message.
        for retry in xrange(4):
            try:
                self._socket.send_json(message)
                self._socket.recv()
                break
            except Exception as ex:
                if self._logger:
                    self._logger.error('Publish Exception: %r; retry=%d',
                                       ex, retry, exc_info=True)
                if retry >= 3:
                    raise

    def listen(self):
        """Retrieve a single message from the subcription channel
        and return it.
        """
        # If the port is None, no-op.
        if self.port is None:
            raise StopIteration

        # If we are not connected, whine.
        if not self.is_connected:
            raise RuntimeError('Cannot publish a message when not connected '
                               'to the socket.')

        # If we are in the wrong mode, whine.
        if self._rw != zmq.REP:
            raise RuntimeError('This socket is not opened for reading.')

        # Actually listen to the socket.
        while True:
            try:
                message = self._socket.recv_json()
                yield message
            finally:
                self._socket.send('1')
