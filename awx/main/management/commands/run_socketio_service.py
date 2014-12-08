# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import os
import datetime
import logging
import json
import signal
import time
import urllib
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
from awx.main.socket import Socket

# gevent & socketio
import gevent
from socketio import socketio_manage
from socketio.server import SocketIOServer
from socketio.namespace import BaseNamespace

def print_log(message):
    print("[%s] %s" % (now().isoformat(), message))

valid_sockets = []

class TowerBaseNamespace(BaseNamespace):

    def get_allowed_methods(self):
        return []
    
    def get_initial_acl(self):
        global valid_sockets
        print self
        v_user = self.valid_user()
        if v_user:
            if self.socket.sessid not in valid_sockets:
                valid_sockets.append(self.socket.sessid)
                if len(valid_sockets) > 1000:
                    valid_sockets = valid_sockets[1:]
            return set(['recv_connect'] + self.get_allowed_methods())
        return set()

    def valid_user(self):
        if 'HTTP_COOKIE' not in self.environ:
            return False
        else:
            try:
                all_keys = [e.strip() for e in self.environ['HTTP_COOKIE'].split(";")]
                for each_key in all_keys:
                    k, v = each_key.split("=")
                    if k == "token":
                        token_actual = urllib.unquote_plus(v).decode().replace("\"","")
                        auth_token = AuthToken.objects.filter(key=token_actual)
                        if not auth_token.exists():
                            return False
                        auth_token = auth_token[0]
                        if not auth_token.expired:
                            return auth_token.user
                        else:
                            return False
            except Exception, e:
                return False

class TestNamespace(TowerBaseNamespace):

    def recv_connect(self):
        print_log("Received client connect for test namespace from %s" % str(self.environ['REMOTE_ADDR']))
        self.emit('test', "If you see this then you are connected to the test socket endpoint")

class JobNamespace(TowerBaseNamespace):

    def recv_connect(self):
        print_log("Received client connect for job namespace from %s" % str(self.environ['REMOTE_ADDR']))

class JobEventNamespace(TowerBaseNamespace):

    def get_initial_acl(self):
        valid_user = self.valid_user()
        if valid_user is None or valid_user is False:
            return set()
        else:
            user_jobs = get_user_queryset(valid_user, Job).filter(finished__isnull=True)
            visible_jobs = set(['recv_connect'] + ["job_events-%s" % str(j.id) for j in user_jobs])
            print_log("Visible jobs: " + str(visible_jobs))
            return visible_jobs
    
    def recv_connect(self):
        print_log("Received client connect for job event namespace from %s" % str(self.environ['REMOTE_ADDR']))

class ScheduleNamespace(TowerBaseNamespace):

    def get_allowed_methods(self):
        return ["schedule_changed"]

    def recv_connect(self):
        print_log("Received client connect for schedule namespace from %s" % str(self.environ['REMOTE_ADDR']))

class TowerSocket(object):

    def __call__(self, environ, start_response):
        path = environ['PATH_INFO'].strip('/') or 'index.html'
        if path.startswith('socket.io'):
            socketio_manage(environ, {'/socket.io/test': TestNamespace,
                                      '/socket.io/jobs': JobNamespace,
                                      '/socket.io/job_events': JobEventNamespace,
                                      '/socket.io/schedules': ScheduleNamespace})
        else:
            start_response('404 Not Found', [])
            return ['Tower version %s' % awx.__version__]

def notification_handler(server):
    with Socket('websocket', 'r') as websocket:
        for message in websocket.listen():
            packet = {
                'args': message,
                'endpoint': message['endpoint'],
                'name': message['event'],
                'type': 'event',
            }
            for session_id, socket in list(server.sockets.iteritems()):
                if session_id in valid_sockets:
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
            if os.path.exists('/etc/tower/awx.cert') and os.path.exists('/etc/tower/awx.key'):
                print 'Listening on port https://0.0.0.0:' + str(socketio_listen_port)
                server = SocketIOServer(('0.0.0.0', socketio_listen_port), TowerSocket(), resource='socket.io',
                                        keyfile='/etc/tower/awx.key', certfile='/etc/tower/awx.cert')
            else:
                print 'Listening on port http://0.0.0.0:' + str(socketio_listen_port)
                server = SocketIOServer(('0.0.0.0', socketio_listen_port), TowerSocket(), resource='socket.io')

            #gevent.spawn(notification_handler, socketio_notification_port, server)
            handler_thread = Thread(target=notification_handler, args=(server,))
            handler_thread.daemon = True
            handler_thread.start()

            server.serve_forever()
        except KeyboardInterrupt:
            pass
