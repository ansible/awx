import sys
import re
import gevent
import urlparse

from gevent.pywsgi import WSGIHandler
from socketio import transports
from geventwebsocket.handler import WebSocketHandler


class SocketIOHandler(WSGIHandler):
    RE_REQUEST_URL = re.compile(r"""
        ^/(?P<resource>[^/]+)
         /(?P<protocol_version>[^/]+)
         /(?P<transport_id>[^/]+)
         /(?P<sessid>[^/]+)/?$
         """, re.X)
    RE_HANDSHAKE_URL = re.compile(r"^/(?P<resource>[^/]+)/1/$", re.X)

    handler_types = {
        'websocket': transports.WebsocketTransport,
        'flashsocket': transports.FlashSocketTransport,
        'htmlfile': transports.HTMLFileTransport,
        'xhr-multipart': transports.XHRMultipartTransport,
        'xhr-polling': transports.XHRPollingTransport,
        'jsonp-polling': transports.JSONPolling,
    }

    def __init__(self, *args, **kwargs):
        self.socketio_connection = False
        self.allowed_paths = None

        super(SocketIOHandler, self).__init__(*args, **kwargs)

        self.transports = self.handler_types.keys()
        if self.server.transports:
            self.transports = self.server.transports
            if not set(self.transports).issubset(set(self.handler_types)):
                raise Exception("transports should be elements of: %s" %
                    (self.handler_types.keys()))

    def _do_handshake(self, tokens):
        if tokens["resource"] != self.server.resource:
            self.log_error("socket.io URL mismatch")
        else:
            socket = self.server.get_socket()
            data = "%s:15:10:%s" % (socket.sessid, ",".join(self.transports))
            self.write_smart(data)

    def write_jsonp_result(self, data, wrapper="0"):
        self.start_response("200 OK", [
            ("Content-Type", "application/javascript"),
        ])
        self.result = ['io.j[%s]("%s");' % (wrapper, data)]

    def write_plain_result(self, data):
        self.start_response("200 OK", [
            ("Access-Control-Allow-Origin", self.environ.get('HTTP_ORIGIN', '*')),
            ("Access-Control-Allow-Credentials", "true"),
            ("Access-Control-Allow-Methods", "POST, GET, OPTIONS"),
            ("Access-Control-Max-Age", 3600),
            ("Content-Type", "text/plain"),
        ])
        self.result = [data]

    def write_smart(self, data):
        args = urlparse.parse_qs(self.environ.get("QUERY_STRING"))

        if "jsonp" in args:
            self.write_jsonp_result(data, args["jsonp"][0])
        else:
            self.write_plain_result(data)

        self.process_result()

    def handle_one_response(self):
        path = self.environ.get('PATH_INFO')

        # Kick non-socket.io requests to our superclass
        if not path.lstrip('/').startswith(self.server.resource):
            return super(SocketIOHandler, self).handle_one_response()

        self.status = None
        self.headers_sent = False
        self.result = None
        self.response_length = 0
        self.response_use_chunked = False
        request_method = self.environ.get("REQUEST_METHOD")
        request_tokens = self.RE_REQUEST_URL.match(path)

        # Parse request URL and QUERY_STRING and do handshake
        if request_tokens:
            request_tokens = request_tokens.groupdict()
        else:
            handshake_tokens = self.RE_HANDSHAKE_URL.match(path)

            if handshake_tokens:
                return self._do_handshake(handshake_tokens.groupdict())
            else:
                # This is no socket.io request. Let the WSGI app handle it.
                return super(SocketIOHandler, self).handle_one_response()

        # Setup the transport and socket
        transport = self.handler_types.get(request_tokens["transport_id"])
        sessid = request_tokens["sessid"]
        socket = self.server.get_socket(sessid)

        # In case this is WebSocket request, switch to the WebSocketHandler
        # FIXME: fix this ugly class change
        if issubclass(transport, (transports.WebsocketTransport,
                                  transports.FlashSocketTransport)):
            self.__class__ = WebSocketHandler
            self.prevent_wsgi_call = True  # thank you
            # TODO: any errors, treat them ??
            self.handle_one_response()

        # Make the socket object available for WSGI apps
        self.environ['socketio'] = socket

        # Create a transport and handle the request likewise
        self.transport = transport(self)

        jobs = self.transport.connect(socket, request_method)
        # Keep track of those jobs (reading, writing and heartbeat jobs) so
        # that we can kill them later with Socket.kill()
        socket.jobs.extend(jobs)

        try:
            # We'll run the WSGI app if it wasn't already done.
            if socket.wsgi_app_greenlet is None:
                # TODO: why don't we spawn a call to handle_one_response here ?
                #       why call directly the WSGI machinery ?
                start_response = lambda status, headers, exc=None: None
                socket.wsgi_app_greenlet = gevent.spawn(self.application,
                                                        self.environ,
                                                        start_response)
        except:
            self.handle_error(*sys.exc_info())

        # TODO DOUBLE-CHECK: do we need to joinall here ?
        gevent.joinall(jobs)

    def handle_bad_request(self):
        self.close_connection = True
        self.start_reponse("400 Bad Request", [
            ('Content-Type', 'text/plain'),
            ('Connection', 'close'),
            ('Content-Length', 0)
        ])
