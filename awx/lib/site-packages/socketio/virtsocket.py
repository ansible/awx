"""Virtual Socket implementation, unifies all the Transports into one
single interface, and abstracts the work of the long-polling methods.

This module also has the ``default_error_handler`` implementation.
You can define your own so that the error messages are logged or sent
in a different way

:copyright: 2012, Alexandre Bourget <alexandre.bourget@savoirfairelinux.com>
:moduleauthor: Alexandre Bourget <alexandre.bourget@savoirfairelinux.com>

"""
import random
import weakref
import logging

import gevent
from gevent.queue import Queue
from gevent.event import Event

from socketio import packet
from socketio.defaultjson import default_json_loads, default_json_dumps


log = logging.getLogger(__name__)


def default_error_handler(socket, error_name, error_message, endpoint,
                          msg_id, quiet):
    """This is the default error handler, you can override this when
    calling :func:`socketio.socketio_manage`.

    It basically sends an event through the socket with the 'error' name.

    See documentation for :meth:`Socket.error`.

    :param quiet: if quiet, this handler will not send a packet to the
                  user, but only log for the server developer.
    """
    pkt = dict(type='event', name='error',
               args=[error_name, error_message],
               endpoint=endpoint)
    if msg_id:
        pkt['id'] = msg_id

    # Send an error event through the Socket
    if not quiet:
        socket.send_packet(pkt)
        
    # Log that error somewhere for debugging...
    log.error(u"default_error_handler: {}, {} (endpoint={}, msg_id={})".format(
        error_name, error_message, endpoint, msg_id
    ))


class Socket(object):
    """
    Virtual Socket implementation, checks heartbeats, writes to local queues
    for message passing, holds the Namespace objects, dispatches de packets
    to the underlying namespaces.

    This is the abstraction on top of the different transports. It's like
    if you used a WebSocket only...
    """

    STATE_CONNECTING = "CONNECTING"
    STATE_CONNECTED = "CONNECTED"
    STATE_DISCONNECTING = "DISCONNECTING"
    STATE_DISCONNECTED = "DISCONNECTED"

    GLOBAL_NS = ''
    """Use this to be explicit when specifying a Global Namespace (an endpoint
    with no name, not '/chat' or anything."""

    json_loads = staticmethod(default_json_loads)
    json_dumps = staticmethod(default_json_dumps)

    def __init__(self, server, config, error_handler=None):
        self.server = weakref.proxy(server)
        self.sessid = str(random.random())[2:]
        self.session = {}  # the session dict, for general developer usage
        self.client_queue = Queue()  # queue for messages to client
        self.server_queue = Queue()  # queue for messages to server
        self.hits = 0
        self.heartbeats = 0
        self.timeout = Event()
        self.wsgi_app_greenlet = None
        self.state = "NEW"
        self.connection_established = False
        self.ack_callbacks = {}
        self.ack_counter = 0
        self.request = None
        self.environ = None
        self.namespaces = {}
        self.active_ns = {}  # Namespace sessions that were instantiated
        self.jobs = []
        self.error_handler = default_error_handler
        self.config = config
        if error_handler is not None:
            self.error_handler = error_handler

    def _set_namespaces(self, namespaces):
        """This is a mapping (dict) of the different '/namespaces' to their
        BaseNamespace object derivative.

        This is called by socketio_manage()."""
        self.namespaces = namespaces

    def _set_request(self, request):
        """Saves the request object for future use by the different Namespaces.

        This is called by socketio_manage().
        """
        self.request = request

    def _set_environ(self, environ):
        """Save the WSGI environ, for future use.

        This is called by socketio_manage().
        """
        self.environ = environ

    def _set_error_handler(self, error_handler):
        """Changes the default error_handler function to the one specified

        This is called by socketio_manage().
        """
        self.error_handler = error_handler

    def _set_json_loads(self, json_loads):
        """Change the default JSON decoder.

        This should be a callable that accepts a single string, and returns
        a well-formed object.
        """
        self.json_loads = json_loads

    def _set_json_dumps(self, json_dumps):
        """Change the default JSON decoder.

        This should be a callable that accepts a single string, and returns
        a well-formed object.
        """
        self.json_dumps = json_dumps

    def _get_next_msgid(self):
        """This retrieves the next value for the 'id' field when sending
        an 'event' or 'message' or 'json' that asks the remote client
        to 'ack' back, so that we trigger the local callback.
        """
        self.ack_counter += 1
        return self.ack_counter

    def _save_ack_callback(self, msgid, callback):
        """Keep a reference of the callback on this socket."""
        if msgid in self.ack_callbacks:
            return False
        self.ack_callbacks[msgid] = callback

    def _pop_ack_callback(self, msgid):
        """Fetch the callback for a given msgid, if it exists, otherwise,
        return None"""
        if msgid not in self.ack_callbacks:
            return None
        return self.ack_callbacks.pop(msgid)

    def __str__(self):
        result = ['sessid=%r' % self.sessid]
        if self.state == self.STATE_CONNECTED:
            result.append('connected')
        if self.client_queue.qsize():
            result.append('client_queue[%s]' % self.client_queue.qsize())
        if self.server_queue.qsize():
            result.append('server_queue[%s]' % self.server_queue.qsize())
        if self.hits:
            result.append('hits=%s' % self.hits)
        if self.heartbeats:
            result.append('heartbeats=%s' % self.heartbeats)

        return ' '.join(result)

    def __getitem__(self, key):
        """This will get the nested Namespace using its '/chat' reference.

        Using this, you can go from one Namespace to the other (to emit, add
        ACLs, etc..) with:

          adminnamespace.socket['/chat'].add_acl_method('kick-ban')

        """
        return self.active_ns[key]

    def __hasitem__(self, key):
        """Verifies if the namespace is active (was initialized)"""
        return key in self.active_ns

    @property
    def connected(self):
        """Returns whether the state is CONNECTED or not."""
        return self.state == self.STATE_CONNECTED

    def incr_hits(self):
        self.hits += 1

    def heartbeat(self):
        """This makes the heart beat for another X seconds.  Call this when
        you get a heartbeat packet in.

        This clear the heartbeat disconnect timeout (resets for X seconds).
        """
        self.timeout.set()

    def kill(self, detach=False):
        """This function must/will be called when a socket is to be completely
        shut down, closed by connection timeout, connection error or explicit
        disconnection from the client.

        It will call all of the Namespace's
        :meth:`~socketio.namespace.BaseNamespace.disconnect` methods
        so that you can shut-down things properly.

        """
        # Clear out the callbacks
        self.ack_callbacks = {}
        if self.connected:
            self.state = self.STATE_DISCONNECTING
            self.server_queue.put_nowait(None)
            self.client_queue.put_nowait(None)
            if len(self.active_ns) > 0:
                log.debug("Calling disconnect() on %s" % self)
                self.disconnect()

        if detach:
            self.detach()

        gevent.killall(self.jobs)

    def detach(self):
        """Detach this socket from the server. This should be done in
        conjunction with kill(), once all the jobs are dead, detach the
        socket for garbage collection."""

        log.debug("Removing %s from server sockets" % self)
        if self.sessid in self.server.sockets:
            self.server.sockets.pop(self.sessid)

    def put_server_msg(self, msg):
        """Writes to the server's pipe, to end up in in the Namespaces"""
        self.heartbeat()
        self.server_queue.put_nowait(msg)

    def put_client_msg(self, msg):
        """Writes to the client's pipe, to end up in the browser"""
        self.client_queue.put_nowait(msg)

    def get_client_msg(self, **kwargs):
        """Grab a message to send it to the browser"""
        return self.client_queue.get(**kwargs)

    def get_server_msg(self, **kwargs):
        """Grab a message, to process it by the server and dispatch calls
        """
        return self.server_queue.get(**kwargs)

    def get_multiple_client_msgs(self, **kwargs):
        """Get multiple messages, in case we're going through the various
        XHR-polling methods, on which we can pack more than one message if the
        rate is high, and encode the payload for the HTTP channel."""
        client_queue = self.client_queue
        msgs = [client_queue.get(**kwargs)]
        while client_queue.qsize():
            msgs.append(client_queue.get())
        return msgs

    def error(self, error_name, error_message, endpoint=None, msg_id=None,
              quiet=False):
        """Send an error to the user, using the custom or default
        ErrorHandler configured on the [TODO: Revise this] Socket/Handler
        object.

        :param error_name: is a simple string, for easy association on
                           the client side

        :param error_message: is a human readable message, the user
                              will eventually see

        :param endpoint: set this if you have a message specific to an
                         end point

        :param msg_id: set this if your error is relative to a
                       specific message

        :param quiet: way to make the error handler quiet. Specific to
                      the handler.  The default handler will only log,
                      with quiet.
        """
        handler = self.error_handler
        return handler(
            self, error_name, error_message, endpoint, msg_id, quiet)

    # User facing low-level function
    def disconnect(self, silent=False):
        """Calling this method will call the
        :meth:`~socketio.namespace.BaseNamespace.disconnect` method on
        all the active Namespaces that were open, killing all their
        jobs and sending 'disconnect' packets for each of them.

        Normally, the Global namespace (endpoint = '') has special meaning,
        as it represents the whole connection,

        :param silent: when True, pass on the ``silent`` flag to the Namespace
                       :meth:`~socketio.namespace.BaseNamespace.disconnect`
                       calls.
        """
        for ns_name, ns in list(self.active_ns.iteritems()):
            ns.recv_disconnect()

    def remove_namespace(self, namespace):
        """This removes a Namespace object from the socket.

        This is usually called by
        :meth:`~socketio.namespace.BaseNamespace.disconnect`.

        """
        if namespace in self.active_ns:
            del self.active_ns[namespace]

        if len(self.active_ns) == 0 and self.connected:
            self.kill(detach=True)

    def send_packet(self, pkt):
        """Low-level interface to queue a packet on the wire (encoded as wire
        protocol"""
        self.put_client_msg(packet.encode(pkt, self.json_dumps))

    def spawn(self, fn, *args, **kwargs):
        """Spawn a new Greenlet, attached to this Socket instance.

        It will be monitored by the "watcher" method
        """

        log.debug("Spawning sub-Socket Greenlet: %s" % fn.__name__)
        job = gevent.spawn(fn, *args, **kwargs)
        self.jobs.append(job)
        return job

    def _receiver_loop(self):
        """This is the loop that takes messages from the queue for the server
        to consume, decodes them and dispatches them.

        It is the main loop for a socket.  We join on this process before
        returning control to the web framework.

        This process is not tracked by the socket itself, it is not going
        to be killed by the ``gevent.killall(socket.jobs)``, so it must
        exit gracefully itself.
        """

        while True:
            rawdata = self.get_server_msg()

            if not rawdata:
                continue  # or close the connection ?
            try:
                pkt = packet.decode(rawdata, self.json_loads)
            except (ValueError, KeyError, Exception), e:
                self.error('invalid_packet',
                    "There was a decoding error when dealing with packet "
                    "with event: %s... (%s)" % (rawdata[:20], e))
                continue

            if pkt['type'] == 'heartbeat':
                # This is already dealth with in put_server_msg() when
                # any incoming raw data arrives.
                continue

            if pkt['type'] == 'disconnect' and pkt['endpoint'] == '':
                # On global namespace, we kill everything.
                self.kill(detach=True)
                continue

            endpoint = pkt['endpoint']

            if endpoint not in self.namespaces:
                self.error("no_such_namespace",
                    "The endpoint you tried to connect to "
                    "doesn't exist: %s" % endpoint, endpoint=endpoint)
                continue
            elif endpoint in self.active_ns:
                pkt_ns = self.active_ns[endpoint]
            else:
                new_ns_class = self.namespaces[endpoint]
                pkt_ns = new_ns_class(self.environ, endpoint,
                                        request=self.request)
                # This calls initialize() on all the classes and mixins, etc..
                # in the order of the MRO
                for cls in type(pkt_ns).__mro__:
                    if hasattr(cls, 'initialize'):
                        cls.initialize(pkt_ns)  # use this instead of __init__,
                                                # for less confusion

                self.active_ns[endpoint] = pkt_ns

            retval = pkt_ns.process_packet(pkt)

            # Has the client requested an 'ack' with the reply parameters ?
            if pkt.get('ack') == "data" and pkt.get('id'):
                if type(retval) is tuple:
                    args = list(retval)
                else:
                    args = [retval]
                returning_ack = dict(type='ack', ackId=pkt['id'],
                                     args=args,
                                     endpoint=pkt.get('endpoint', ''))
                self.send_packet(returning_ack)

            # Now, are we still connected ?
            if not self.connected:
                self.kill(detach=True)  # ?? what,s the best clean-up
                                        # when its not a
                                        # user-initiated disconnect
                return

    def _spawn_receiver_loop(self):
        """Spawns the reader loop.  This is called internall by
        socketio_manage().
        """
        job = gevent.spawn(self._receiver_loop)
        self.jobs.append(job)
        return job

    def _watcher(self):
        """Watch out if we've been disconnected, in that case, kill
        all the jobs.

        """
        while True:
            gevent.sleep(1.0)
            if not self.connected:
                for ns_name, ns in list(self.active_ns.iteritems()):
                    ns.recv_disconnect()
                # Killing Socket-level jobs
                gevent.killall(self.jobs)
                break

    def _spawn_watcher(self):
        """This one is not waited for with joinall(socket.jobs), as it
        is an external watcher, to clean up when everything is done."""
        job = gevent.spawn(self._watcher)
        return job

    def _heartbeat(self):
        """Start the heartbeat Greenlet to check connection health."""
        interval = self.config['heartbeat_interval']
        while self.connected:
            gevent.sleep(interval)
            # TODO: this process could use a timeout object like the disconnect
            #       timeout thing, and ONLY send packets when none are sent!
            #       We would do that by calling timeout.set() for a "sending"
            #       timeout.  If we're sending 100 messages a second, there is
            #       no need to push some heartbeats in there also.
            self.put_client_msg("2::")

    def _heartbeat_timeout(self):
        timeout = float(self.config['heartbeat_timeout'])
        while True:
            self.timeout.clear()
            gevent.sleep(0)
            wait_res = self.timeout.wait(timeout=timeout)
            if not wait_res:
                if self.connected:
                    log.debug("heartbeat timed out, killing socket")
                    self.kill(detach=True)
                return


    def _spawn_heartbeat(self):
        """This functions returns a list of jobs"""
        self.spawn(self._heartbeat)
        self.spawn(self._heartbeat_timeout)
