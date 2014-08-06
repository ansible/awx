__version__ = (0, 3, 5)

import logging
import gevent

log = logging.getLogger(__name__)


def socketio_manage(environ, namespaces, request=None, error_handler=None,
                    json_loads=None, json_dumps=None):
    """Main SocketIO management function, call from within your Framework of
    choice's view.

    The ``environ`` variable is the WSGI ``environ``.  It is used to extract
    Socket object from the underlying server (as the 'socketio' key), and will
    be attached to both the ``Socket`` and ``Namespace`` objects.

    The ``namespaces`` parameter is a dictionary of the namespace string
    representation as key, and the BaseNamespace namespace class descendant as
    a value.  The empty string ('') namespace is the global namespace.  You can
    use Socket.GLOBAL_NS to be more explicit. So it would look like:

    .. code-block:: python

      namespaces={'': GlobalNamespace,
                  '/chat': ChatNamespace}

    The ``request`` object is not required, but will probably be useful to pass
    framework-specific things into your Socket and Namespace functions. It will
    simply be attached to the Socket and Namespace object (accessible through
    ``self.request`` in both cases), and it is not accessed in any case by the
    ``gevent-socketio`` library.

    Pass in an ``error_handler`` if you want to override the default
    error_handler (which is :func:`socketio.virtsocket.default_error_handler`.
    The callable you pass in should have the same signature as the default
    error handler.

    The ``json_loads`` and ``json_dumps`` are overrides for the default
    ``json.loads`` and ``json.dumps`` function calls.  Override these at
    the top-most level here.  This will affect all sockets created by this
    socketio manager, and all namespaces inside.

    This function will block the current "view" or "controller" in your
    framework to do the recv/send on the socket, and dispatch incoming messages
    to your namespaces.

    This is a simple example using Pyramid:

    .. code-block:: python

      def my_view(request):
          socketio_manage(request.environ, {'': GlobalNamespace}, request)

    NOTE: You must understand that this function is going to be called
    *only once* per socket opening, *even though* you are using a long
    polling mechanism.  The subsequent calls (for long polling) will
    be hooked directly at the server-level, to interact with the
    active ``Socket`` instance.  This means you will *not* get access
    to the future ``request`` or ``environ`` objects.  This is of
    particular importance regarding sessions (like Beaker).  The
    session will be opened once at the opening of the Socket, and not
    closed until the socket is closed.  You are responsible for
    opening and closing the cookie-based session yourself if you want
    to keep its data in sync with the rest of your GET/POST calls.
    """
    socket = environ['socketio']
    socket._set_environ(environ)
    socket._set_namespaces(namespaces)

    if request:
        socket._set_request(request)

    if error_handler:
        socket._set_error_handler(error_handler)

    if json_loads:
        socket._set_json_loads(json_loads)
    if json_dumps:
        socket._set_json_dumps(json_dumps)

    receiver_loop = socket._spawn_receiver_loop()

    gevent.joinall([receiver_loop])

    # TODO: double check, what happens to the WSGI request here ? it vanishes ?
    return
