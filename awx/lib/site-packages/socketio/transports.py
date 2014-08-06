import gevent
import urllib
import urlparse
from geventwebsocket import WebSocketError
from gevent.queue import Empty


class BaseTransport(object):
    """Base class for all transports. Mostly wraps handler class functions."""

    def __init__(self, handler, config, **kwargs):
        """Base transport class.

        :param config: dict Should contain the config keys, like
          ``heartbeat_interval``, ``heartbeat_timeout`` and
          ``close_timeout``.

        """
        self.content_type = ("Content-Type", "text/plain; charset=UTF-8")
        self.headers = [
            ("Access-Control-Allow-Origin", "*"),
            ("Access-Control-Allow-Credentials", "true"),
            ("Access-Control-Allow-Methods", "POST, GET, OPTIONS"),
            ("Access-Control-Max-Age", 3600),
        ]
        self.handler = handler
        self.config = config

    def write(self, data=""):
        # Gevent v 0.13
        if hasattr(self.handler, 'response_headers_list'):
            if 'Content-Length' not in self.handler.response_headers_list:
                self.handler.response_headers.append(('Content-Length', len(data)))
                self.handler.response_headers_list.append('Content-Length')
        elif not hasattr(self.handler, 'provided_content_length') or self.handler.provided_content_length is None:
            # Gevent 1.0bX
            l = len(data)
            self.handler.provided_content_length = l
            self.handler.response_headers.append(('Content-Length', l))

        self.handler.write_smart(data)

    def start_response(self, status, headers, **kwargs):
        if "Content-Type" not in [x[0] for x in headers]:
            headers.append(self.content_type)

        headers.extend(self.headers)
        self.handler.start_response(status, headers, **kwargs)


class XHRPollingTransport(BaseTransport):
    def __init__(self, *args, **kwargs):
        super(XHRPollingTransport, self).__init__(*args, **kwargs)

    def options(self):
        self.start_response("200 OK", ())
        self.write()
        return []

    def get(self, socket):
        socket.heartbeat()

        heartbeat_interval = self.config['heartbeat_interval']
        payload = self.get_messages_payload(socket, timeout=heartbeat_interval)
        if not payload:
            payload = "8::"  # NOOP

        self.start_response("200 OK", [])
        self.write(payload)

    def _request_body(self):
        return self.handler.wsgi_input.readline()

    def post(self, socket):
        for message in self.decode_payload(self._request_body()):
            socket.put_server_msg(message)

        self.start_response("200 OK", [
            ("Connection", "close"),
            ("Content-Type", "text/plain")
        ])
        self.write("1")

    def get_messages_payload(self, socket, timeout=None):
        """This will fetch the messages from the Socket's queue, and if
        there are many messes, pack multiple messages in one payload and return
        """
        try:
            msgs = socket.get_multiple_client_msgs(timeout=timeout)
            data = self.encode_payload(msgs)
        except Empty:
            data = ""
        return data

    def encode_payload(self, messages):
        """Encode list of messages. Expects messages to be unicode.

        ``messages`` - List of raw messages to encode, if necessary

        """
        if not messages or messages[0] is None:
            return ''

        if len(messages) == 1:
            return messages[0].encode('utf-8')

        payload = u''.join([(u'\ufffd%d\ufffd%s' % (len(p), p))
                            for p in messages if p is not None])
        # FIXME: why is it so that we must filter None from here ?  How
        #        is it even possible that a None gets in there ?

        return payload.encode('utf-8')

    def decode_payload(self, payload):
        """This function can extract multiple messages from one HTTP payload.
        Some times, the XHR/JSONP/.. transports can pack more than one message
        on a single packet.  They are encoding following the WebSocket
        semantics, which need to be reproduced here to unwrap the messages.

        The semantics are:

          \ufffd + [length as a string] + \ufffd + [payload as a unicode string]

        This function returns a list of messages, even though there is only
        one.

        Inspired by socket.io/lib/transports/http.js
        """
        payload = payload.decode('utf-8')
        if payload[0] == u"\ufffd":
            ret = []
            while len(payload) != 0:
                len_end = payload.find(u"\ufffd", 1)
                length = int(payload[1:len_end])
                msg_start = len_end + 1
                msg_end = length + msg_start
                message = payload[msg_start:msg_end]
                ret.append(message)
                payload = payload[msg_end:]
            return ret
        return [payload]

    def do_exchange(self, socket, request_method):
        if not socket.connection_established:
            # Runs only the first time we get a Socket opening
            self.start_response("200 OK", [
                ("Connection", "close"),
            ])
            self.write("1::")  # 'connect' packet
            return
        elif request_method in ("GET", "POST", "OPTIONS"):
            return getattr(self, request_method.lower())(socket)
        else:
            raise Exception("No support for the method: " + request_method)


class JSONPolling(XHRPollingTransport):
    def __init__(self, handler, config):
        super(JSONPolling, self).__init__(handler, config)
        self.content_type = ("Content-Type", "text/javascript; charset=UTF-8")

    def _request_body(self):
        data = super(JSONPolling, self)._request_body()
        # resolve %20%3F's, take out wrapping d="...", etc..
        data = urllib.unquote_plus(data)[3:-1] \
                     .replace(r'\"', '"') \
                     .replace(r"\\", "\\")

        # For some reason, in case of multiple messages passed in one
        # query, IE7 sends it escaped, not utf-8 encoded. This dirty
        # hack handled it
        if data[0] == "\\":
            data = data.decode("unicode_escape").encode("utf-8")
        return data

    def write(self, data):
        """Just quote out stuff before sending it out"""
        args = urlparse.parse_qs(self.handler.environ.get("QUERY_STRING"))
        if "i" in args:
            i = args["i"]
        else:
            i = "0"
        # TODO: don't we need to quote this data in here ?
        super(JSONPolling, self).write("io.j[%s]('%s');" % (i, data))


class XHRMultipartTransport(XHRPollingTransport):
    def __init__(self, handler):
        super(JSONPolling, self).__init__(handler)
        self.content_type = (
            "Content-Type",
            "multipart/x-mixed-replace;boundary=\"socketio\""
        )

    def do_exchange(self, socket, request_method):
        if request_method == "GET":
            return self.get(socket)
        elif request_method == "POST":
            return self.post(socket)
        else:
            raise Exception("No support for such method: " + request_method)

    def get(self, socket):
        header = "Content-Type: text/plain; charset=UTF-8\r\n\r\n"

        self.start_response("200 OK", [("Connection", "keep-alive")])
        self.write_multipart("--socketio\r\n")
        self.write_multipart(header)
        self.write_multipart(str(socket.sessid) + "\r\n")
        self.write_multipart("--socketio\r\n")

        def chunk():
            while True:
                payload = self.get_messages_payload(socket)

                if not payload:
                    # That would mean the call to Queue.get() returned Empty,
                    # so it was in fact killed, since we pass no timeout=..
                    return
                    # See below
                else:
                    try:
                        self.write_multipart(header)
                        self.write_multipart(payload)
                        self.write_multipart("--socketio\r\n")
                    except socket.error:
                        # The client might try to reconnect, even with a socket
                        # error, so let's just let it go, and not kill the
                        # socket completely.  Other processes will ensure
                        # we kill everything if the user expires the timeouts.
                        #
                        # WARN: this means that this payload is LOST, unless we
                        # decide to re-inject it into the queue.
                        return

        socket.spawn(chunk)


class WebsocketTransport(BaseTransport):
    def do_exchange(self, socket, request_method):
        websocket = self.handler.environ['wsgi.websocket']
        websocket.send("1::")  # 'connect' packet

        def send_into_ws():
            while True:
                message = socket.get_client_msg()

                if message is None:
                    break
                try:
                    websocket.send(message)
                except (WebSocketError, TypeError):
                    # We can't send a message on the socket
                    # it is dead, let the other sockets know
                    socket.disconnect()

        def read_from_ws():
            while True:
                message = websocket.receive()

                if message is None:
                    break
                else:
                    if message is not None:
                        socket.put_server_msg(message)

        socket.spawn(send_into_ws)
        socket.spawn(read_from_ws)


class FlashSocketTransport(WebsocketTransport):
    pass


class HTMLFileTransport(XHRPollingTransport):
    """Not tested at all!"""

    def __init__(self, handler, config):
        super(HTMLFileTransport, self).__init__(handler, config)
        self.content_type = ("Content-Type", "text/html")

    def write_packed(self, data):
        self.write("<script>_('%s');</script>" % data)

    def write(self, data):
        l = 1024 * 5
        super(HTMLFileTransport, self).write("%d\r\n%s%s\r\n" % (l, data, " " * (l - len(data))))

    def do_exchange(self, socket, request_method):
        return super(HTMLFileTransport, self).do_exchange(socket, request_method)

    def get(self, socket):
        self.start_response("200 OK", [
            ("Connection", "keep-alive"),
            ("Content-Type", "text/html"),
            ("Transfer-Encoding", "chunked"),
        ])
        self.write("<html><body><script>var _ = function (msg) { parent.s._(msg, document); };</script>")
        self.write_packed("1::")  # 'connect' packet


        def chunk():
            while True:
                payload = self.get_messages_payload(socket)

                if not payload:
                    # That would mean the call to Queue.get() returned Empty,
                    # so it was in fact killed, since we pass no timeout=..
                    return
                else:
                    try:
                        self.write_packed(payload)
                    except socket.error:
                        # See comments for XHRMultipart
                        return

        socket.spawn(chunk)
