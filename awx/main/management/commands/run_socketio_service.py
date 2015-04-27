# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import os
import logging
import urllib
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

valid_sockets = []

class TowerBaseNamespace(BaseNamespace):

    def get_allowed_methods(self):
        return ['recv_disconnect']
    
    def get_initial_acl(self):
        global valid_sockets
        v_user = self.valid_user()
        self.is_valid_connection = False
        if v_user:
            if self.socket.sessid not in valid_sockets:
                valid_sockets.append(self.socket.sessid)
                self.is_valid_connection = True
                if len(valid_sockets) > 1000:
                    valid_sockets = valid_sockets[1:]
            return set(['recv_connect'] + self.get_allowed_methods())
        else:
            logger.warn("Authentication Failure validating user")
            self.emit("connect_failed", "Authentication failed")
        return set(['recv_connect'])

    def valid_user(self):
        if 'QUERY_STRING' not in self.environ:
            return False
        else:
            try:
                k, v = self.environ['QUERY_STRING'].split("=")
                if k == "Token":
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
                logger.error("Exception validating user: " + str(e))
                return False

    def recv_connect(self):
        if not self.is_valid_connection:
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

class TowerSocket(object):

    def __call__(self, environ, start_response):
        path = environ['PATH_INFO'].strip('/') or 'index.html'
        if path.startswith('socket.io'):
            socketio_manage(environ, {'/socket.io/test': TestNamespace,
                                      '/socket.io/jobs': JobNamespace,
                                      '/socket.io/job_events': JobEventNamespace,
                                      '/socket.io/ad_hoc_command_events': AdHocCommandEventNamespace,
                                      '/socket.io/schedules': ScheduleNamespace})
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
            for session_id, socket in list(server.sockets.iteritems()):
                if session_id in valid_sockets:
                    try:
                        socket.send_packet(packet)
                    except Exception, e:
                        logger.error("Error sending client packet to %s: %s" % (str(session_id), str(packet)))
                        logger.error("Error was: " + str(e))

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

            handler_thread = Thread(target=notification_handler, args=(server,))
            handler_thread.daemon = True
            handler_thread.start()

            server.serve_forever()
        except KeyboardInterrupt:
            pass
