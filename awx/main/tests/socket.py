# Copyright (c) 2014, Ansible, Inc.
# All Rights Reserved.

import os

import zmq

class Socket(object):
    """An abstraction class implemented for a dumb OS socket.

    Intended to allow alteration of backend details in a single, consistent
    way throughout the Tower application.
    """
    ports = {
        'callbacks': ,
        'websocket': ,
    }

    def __init__(self, bucket, rw, debug=0, logger=None):
        """Instantiate a Socket object, which uses ZeroMQ to actually perform
        passing a message back and forth.
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

    def __enter__(self):
        self.connect()
        return self

    @property
    def port(self):
        return self.ports[self._bucket]

    def connect(self, purpose):
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

        # Okay, create the connection.
        if self._context is None:
            self._context = zmq.Context()
            self._socket = self._context.socket(purpose) 
            if purpose == self.WRITE:
                self._socket.connect(self.port)
            else:
                self._socket.bind(self.port)
                
    def publish(self, message):
        """Publish a message over the socket."""

        # If we are in debug mode; provide the PID.
        if self._debug:
            message.update({'pid': os.getpid(),
                            'connection_pid': self._connection_pid})

        # Send the message.
        for retry in xrange(4):
            try:
                self.connect()
                self._socket.send_json(message)
                self._socket.recv()
            except Exception as ex:
                if self._logger:
                    self._logger.info('Publish Exception: %r; retry=%d',
                                      ex, retry, exc_info=True)
                if retry >= 3:
                    raise

    def listen(self):
        """Retrieve a single message from the subcription channel
        and return it.
        """
        while True:
            message = self._socket.recv_json()
            yield message
            self._socket.send('1')
