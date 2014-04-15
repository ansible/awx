import os

import gevent
from gevent.pool import Pool

from gunicorn.workers.ggevent import GeventPyWSGIWorker
from socketio.server import SocketIOServer
from socketio.handler import SocketIOHandler


class GeventSocketIOBaseWorker(GeventPyWSGIWorker):
    """ The base gunicorn worker class """
    def run(self):
        self.socket.setblocking(1)
        pool = Pool(self.worker_connections)
        self.server_class.base_env['wsgi.multiprocess'] = \
            self.cfg.workers > 1
        server = self.server_class(
            self.socket, application=self.wsgi,
            spawn=pool, handler_class=self.wsgi_handler,
            namespace=self.namespace, policy_server=self.policy_server)
        server.start()
        try:
            while self.alive:
                self.notify()

                if self.ppid != os.getppid():
                    self.log.info("Parent changed, shutting down: %s", self)
                    break

                gevent.sleep(1.0)

        except KeyboardInterrupt:
            pass

        # try to stop the connections
        try:
            self.notify()
            server.stop(timeout=self.timeout)
        except:
            pass


class GeventSocketIOWorker(GeventSocketIOBaseWorker):
    """
    Default gunicorn worker utilizing gevent

    Uses the namespace 'socket.io' and defaults to the flash policy server
    being disabled.
    """
    server_class = SocketIOServer
    wsgi_handler = SocketIOHandler
    # We need to define a namespace for the server, it would be nice if this
    # was a configuration option, will probably end up how this implemented,
    # for now this is just a proof of concept to make sure this will work
    namespace = 'socket.io'
    policy_server = False  # Don't run the flash policy server
