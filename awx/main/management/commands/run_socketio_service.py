# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import os
import logging
import urllib
import weakref
from optparse import make_option
from threading import Thread

# Django
from django.conf import settings
from django.core.management.base import NoArgsCommand

# AWX
import awx
from awx.main.models import * # noqa
from awx.main.socket import Socket

# socketio
from socketio import socketio_manage
from socketio.server import SocketIOServer
from socketio.namespace import BaseNamespace

logger = logging.getLogger('awx.main.commands.run_socketio_service')

class SocketSession(object):
    def __init__(self, session_id, token_key, socket):
        self.socket = weakref.ref(socket)
        self.session_id = session_id
        self.token_key = token_key
        self._valid = True

    def is_valid(self):
        return bool(self._valid)

    def invalidate(self):
        self._valid = False

    def is_db_token_valid(self):
        auth_token = AuthToken.objects.filter(key=self.token_key, reason='')
        if not auth_token.exists():
            return False
        auth_token = auth_token[0]
        return bool(not auth_token.is_expired())

class SocketSessionManager(object):

    def __init__(self):
        self.SESSIONS_MAX = 1000
        self.socket_sessions = []
        self.socket_session_token_key_map = {}

    def _prune(self):
        if len(self.socket_sessions) > self.SESSIONS_MAX:
            session = self.socket_sessions[0]
            entries = self.socket_session_token_key_map[session.token_key]
            del entries[session.session_id]
            if len(entries) == 0:
                del self.socket_session_token_key_map[session.token_key]
            self.socket_sessions.pop(0)

    '''
    Returns an dict of sessions <session_id, session>
    '''
    def lookup(self, token_key=None):
        if not token_key:
            raise ValueError("token_key required")
        return self.socket_session_token_key_map.get(token_key, None)

    def add_session(self, session):
        self.socket_sessions.append(session)
        entries = self.socket_session_token_key_map.get(session.token_key, None)
        if not entries:
            entries = {}
            self.socket_session_token_key_map[session.token_key] = entries
        entries[session.session_id] = session
        self._prune()
        return session

class SocketController(object):

    def __init__(self, SocketSessionManager):
        self.server = None
        self.SocketSessionManager = SocketSessionManager

    def add_session(self, session):
        return self.SocketSessionManager.add_session(session)

    def broadcast_packet(self, packet):
        # Broadcast message to everyone at endpoint
        # Loop over the 'raw' list of sockets (don't trust our list)
        for session_id, socket in list(self.server.sockets.iteritems()):
            socket_session = socket.session.get('socket_session', None)
            if socket_session and socket_session.is_valid():
                try:
                    socket.send_packet(packet)
                except Exception, e:
                    logger.error("Error sending client packet to %s: %s" % (str(session_id), str(packet)))
                    logger.error("Error was: " + str(e))

    def send_packet(self, packet, token_key):
        if not token_key:
            raise ValueError("token_key is required")
        socket_sessions = self.SocketSessionManager.lookup(token_key=token_key)
        # We may not find the socket_session if the user disconnected
        # (it's actually more compliciated than that because of our prune logic)
        if not socket_sessions:
            return None
        for session_id, socket_session in socket_sessions.iteritems():
            logger.warn("Maybe sending packet to %s" % session_id)
            if socket_session and socket_session.is_valid():
                logger.warn("Sending packet to %s" % session_id)
                socket = socket_session.socket()
                if socket:
                    try:
                        socket.send_packet(packet)
                    except Exception, e:
                        logger.error("Error sending client packet to %s: %s" % (str(socket_session.session_id), str(packet)))
                        logger.error("Error was: " + str(e))

    def set_server(self, server):
        self.server = server
        return server

socketController = SocketController(SocketSessionManager())

#
# Socket session is attached to self.session['socket_session']
# self.session and self.socket.session point to the same dict
# 
class TowerBaseNamespace(BaseNamespace):

    def get_allowed_methods(self):
        return ['recv_disconnect']
    
    def get_initial_acl(self):
        request_token = self._get_request_token()
        if request_token:
            # (1) This is the first time the socket has been seen (first 
            # namespace joined).
            # (2) This socket has already been seen (already joined and maybe 
            # left a namespace)
            #
            # Note: Assume that the user token is valid if the session is found
            socket_session = self.session.get('socket_session', None)
            if not socket_session:
                socket_session = SocketSession(self.socket.sessid, request_token, self.socket)
                if socket_session.is_db_token_valid():
                    self.session['socket_session'] = socket_session
                    socketController.add_session(socket_session)
                else:
                    socket_session.invalidate()

            return set(['recv_connect'] + self.get_allowed_methods())
        else:
            logger.warn("Authentication Failure validating user")
            self.emit("connect_failed", "Authentication failed")
        return set(['recv_connect'])

    def _get_request_token(self):
        if 'QUERY_STRING' not in self.environ:
            return False

        try:
            k, v = self.environ['QUERY_STRING'].split("=")
            if k == "Token":
                token_actual = urllib.unquote_plus(v).decode().replace("\"","")
                return token_actual
        except Exception, e:
            logger.error("Exception validating user: " + str(e))
            return False
        return False

    def recv_connect(self):
        socket_session = self.session.get('socket_session', None)
        if socket_session and not socket_session.is_valid():
            self.disconnect(silent=False)

class TestNamespace(TowerBaseNamespace):

    def recv_connect(self):
        logger.info("Received client connect for test namespace from %s" % str(self.environ['REMOTE_ADDR']))
        self.emit('test', "If you see this then you attempted to connect to the test socket endpoint")
        super(TestNamespace, self).recv_connect()

class JobNamespace(TowerBaseNamespace):

    def recv_connect(self):
        logger.info("Received client connect for job namespace from %s" % str(self.environ['REMOTE_ADDR']))
        super(JobNamespace, self).recv_connect()

class JobEventNamespace(TowerBaseNamespace):

    def recv_connect(self):
        logger.info("Received client connect for job event namespace from %s" % str(self.environ['REMOTE_ADDR']))
        super(JobEventNamespace, self).recv_connect()

class AdHocCommandEventNamespace(TowerBaseNamespace):

    def recv_connect(self):
        logger.info("Received client connect for ad hoc command event namespace from %s" % str(self.environ['REMOTE_ADDR']))
        super(AdHocCommandEventNamespace, self).recv_connect()

class ScheduleNamespace(TowerBaseNamespace):

    def get_allowed_methods(self):
        parent_allowed = super(ScheduleNamespace, self).get_allowed_methods()
        return parent_allowed + ["schedule_changed"]

    def recv_connect(self):
        logger.info("Received client connect for schedule namespace from %s" % str(self.environ['REMOTE_ADDR']))
        super(ScheduleNamespace, self).recv_connect()

# Catch-all namespace.
# Deliver 'global' events over this namespace
class ControlNamespace(TowerBaseNamespace):

    def recv_connect(self):
        logger.warn("Received client connect for control namespace from %s" % str(self.environ['REMOTE_ADDR']))
        super(ControlNamespace, self).recv_connect()

class TowerSocket(object):

    def __call__(self, environ, start_response):
        path = environ['PATH_INFO'].strip('/') or 'index.html'
        if path.startswith('socket.io'):
            socketio_manage(environ, {'/socket.io/test': TestNamespace,
                                      '/socket.io/jobs': JobNamespace,
                                      '/socket.io/job_events': JobEventNamespace,
                                      '/socket.io/ad_hoc_command_events': AdHocCommandEventNamespace,
                                      '/socket.io/schedules': ScheduleNamespace,
                                      '/socket.io/control': ControlNamespace})
        else:
            logger.warn("Invalid connect path received: " + path)
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

            if 'token_key' in message:
                # Best practice not to send the token over the socket
                socketController.send_packet(packet, message.pop('token_key'))
            else:
                socketController.broadcast_packet(packet)

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

    def handle_noargs(self, **options):
        socketio_listen_port = settings.SOCKETIO_LISTEN_PORT

        try:
            if os.path.exists('/etc/tower/tower.cert') and os.path.exists('/etc/tower/tower.key'):
                logger.info('Listening on port https://0.0.0.0:' + str(socketio_listen_port))
                server = SocketIOServer(('0.0.0.0', socketio_listen_port), TowerSocket(), resource='socket.io',
                                        keyfile='/etc/tower/tower.key', certfile='/etc/tower/tower.cert')
            else:
                logger.info('Listening on port http://0.0.0.0:' + str(socketio_listen_port))
                server = SocketIOServer(('0.0.0.0', socketio_listen_port), TowerSocket(), resource='socket.io')

            socketController.set_server(server)
            handler_thread = Thread(target=notification_handler, args=(server,))
            handler_thread.daemon = True
            handler_thread.start()

            server.serve_forever()
        except KeyboardInterrupt:
            pass
