import sys
import traceback

from socket import error

from gevent.pywsgi import WSGIServer

from socketio.handler import SocketIOHandler
from socketio.policyserver import FlashPolicyServer
from socketio.virtsocket import Socket

__all__ = ['SocketIOServer']


class SocketIOServer(WSGIServer):
    """A WSGI Server with a resource that acts like an SocketIO."""

    def __init__(self, *args, **kwargs):
        """
        This is just like the standard WSGIServer __init__, except with a
        few additional ``kwargs``:

        :param resource: The URL which has to be identified as a socket.io request.  Defaults to the /socket.io/ URL.
        :param transports: Optional list of transports to allow. List of
            strings, each string should be one of
            handler.SocketIOHandler.handler_types.
        :param policy_server: Boolean describing whether or not to use the
            Flash policy server.  Default True.
        :param policy_listener : A tuple containing (host, port) for the 
            policy server.  This is optional and used only if policy server 
            is set to true.  The default value is 0.0.0.0:843
        """
        self.sockets = {}
        if 'namespace' in kwargs:
            print("DEPRECATION WARNING: use resource instead of namespace")
            self.resource = kwargs.pop('namespace', 'socket.io')
        else:
            self.resource = kwargs.pop('resource', 'socket.io')

        self.transports = kwargs.pop('transports', None)

        if kwargs.pop('policy_server', True):
            policylistener = kwargs.pop('policy_listener', (args[0][0], 10843))
            self.policy_server = FlashPolicyServer(policylistener)
        else:
            self.policy_server = None

        kwargs['handler_class'] = SocketIOHandler
        super(SocketIOServer, self).__init__(*args, **kwargs)

    def start_accepting(self):
        if self.policy_server is not None:
            try:
                self.policy_server.start()
            except error, ex:
                sys.stderr.write(
                    'FAILED to start flash policy server: %s\n' % (ex, ))
            except Exception:
                traceback.print_exc()
                sys.stderr.write('FAILED to start flash policy server.\n\n')
        super(SocketIOServer, self).start_accepting()

    def kill(self):
        if self.policy_server is not None:
            self.policy_server.kill()
        super(SocketIOServer, self).kill()

    def handle(self, socket, address):
        handler = self.handler_class(socket, address, self)
        handler.handle()

    def get_socket(self, sessid=''):
        """Return an existing or new client Socket."""

        socket = self.sockets.get(sessid)

        if socket is None:
            socket = Socket(self)
            self.sockets[socket.sessid] = socket
        else:
            socket.incr_hits()

        return socket
