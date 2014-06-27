# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import os
import datetime
import logging
import json
import signal
import time
from optparse import make_option
from threading import Thread

# Django
from django.conf import settings
from django.core.management.base import NoArgsCommand, CommandError
from django.db import transaction, DatabaseError
from django.contrib.auth.models import User
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now, is_aware, make_aware
from django.utils.tzinfo import FixedOffset

# AWX
import awx
from awx.main.models import *

# ZeroMQ
import zmq

# gevent & socketio
import gevent
from socketio import socketio_manage
from socketio.server import SocketIOServer
from socketio.namespace import BaseNamespace

class TestNamespace(BaseNamespace):

    def recv_connect(self):
        print("Received client connect for test namespace from %s" % str(self.environ['REMOTE_ADDR']))
        self.emit('test', "If you see this then you are connected to the test socket endpoint")

class JobNamespace(BaseNamespace):

    def recv_connect(self):
        print("Received client connect for job namespace from %s" % str(self.environ['REMOTE_ADDR']))

class JobEventNamespace(BaseNamespace):

    def recv_connect(self):
        print("Received client connect for job event namespace from %s" % str(self.environ['REMOTE_ADDR']))

class ScheduleNamespace(BaseNamespace):

    def recv_connect(self):
        print("Received client connect for schedule namespace from %s" % str(self.environ['REMOTE_ADDR']))

class TowerSocket(object):

    def __call__(self, environ, start_response):
        path = environ['PATH_INFO'].strip('/') or 'index.html'
        print path
        if path.startswith('socket.io'):
            socketio_manage(environ, {'/socket.io/test': TestNamespace,
                                      '/socket.io/jobs': JobNamespace,
                                      '/socket.io/job_events': JobEventNamespace,
                                      '/socket.io/schedules': ScheduleNamespace})
        else:
            start_response('404 Not Found', [])
            return ['Tower version %s' % awx.__version__]

def notification_handler(bind_port, server):
    handler_context = zmq.Context()
    handler_socket = handler_context.socket(zmq.PULL)
    handler_socket.bind(bind_port)

    while True:
        message = handler_socket.recv_json()
        packet = dict(type='event', name=message['event'], endpoint=message['endpoint'], args=message)
        for session_id, socket in list(server.sockets.iteritems()):
            socket.send_packet(packet)

class Command(NoArgsCommand):
    '''
    SocketIO event emitter Tower service
    Receives notifications from other services destined for UI notification
    '''

    help = 'Launch the SocketIO event emitter service'

    option_list = NoArgsCommand.option_list + (
        make_option('--receive_port', dest='receive_port', type='int', default=5559,
                    help='Port to listen for new events that will be destined for a client'),
        make_option('--socketio_port', dest='socketio_port', type='int', default=8080,
                    help='Port to accept socketio requests from clients'),)

    def init_logging(self):
        log_levels = dict(enumerate([logging.ERROR, logging.INFO,
                                     logging.DEBUG, 0]))
        self.logger = logging.getLogger('awx.main.commands.run_socketio_service')
        self.logger.setLevel(log_levels.get(self.verbosity, 0))
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
        self.logger.propagate = False

    def handle_noargs(self, **options):
        self.verbosity = int(options.get('verbosity', 1))
        self.init_logging()
        socketio_listen_port = settings.SOCKETIO_LISTEN_PORT
        socketio_notification_port = settings.SOCKETIO_NOTIFICATION_PORT

        try:
            if os.path.exists('/etc/awx/awx.cert') and os.path.exists('/etc/awx/awx.key'):
                print 'Listening on port https://0.0.0.0:' + str(socketio_listen_port)
                server = SocketIOServer(('0.0.0.0', socketio_listen_port), TowerSocket(), resource='socket.io',
                                        keyfile='/etc/awx/awx.key', certfile='/etc/awx/awx.cert')
            else:
                print 'Listening on port http://0.0.0.0:' + str(socketio_listen_port)
                server = SocketIOServer(('0.0.0.0', socketio_listen_port), TowerSocket(), resource='socket.io')

            #gevent.spawn(notification_handler, socketio_notification_port, server)
            handler_thread = Thread(target=notification_handler, args = (socketio_notification_port, server,))
            handler_thread.daemon = True
            handler_thread.start()

            server.serve_forever()
        except KeyboardInterrupt:
            pass
