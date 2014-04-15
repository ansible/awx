import gevent
import re
import logging
import inspect

log = logging.getLogger(__name__)

# regex to check the event name contains only alpha numerical characters
allowed_event_name_regex = re.compile(r'^[A-Za-z][A-Za-z0-9_ ]*$')


class BaseNamespace(object):
    """The **Namespace** is the primary interface a developer will use
    to create a gevent-socketio-based application.

    You should create your own subclass of this class, optionally using one
    of the :mod:`socketio.mixins` provided (or your own), and define methods
    such as:

    .. code-block:: python
      :linenos:

      def on_my_event(self, my_first_arg, my_second_arg):
          print "This is the my_first_arg object", my_first_arg
          print "This is the my_second_arg object", my_second_arg

      def on_my_second_event(self, whatever):
          print "This holds the first arg that was passed", whatever

    We can also access the full packet directly by making an event handler
    that accepts a single argument named 'packet':

    .. code-block:: python
      :linenos:

      def on_third_event(self, packet):
          print "The full packet", packet
          print "See the BaseNamespace::call_method() method for details"
    """
    def __init__(self, environ, ns_name, request=None):
        self.environ = environ
        self.socket = environ['socketio']
        self.session = self.socket.session  # easily accessible session
        self.request = request
        self.ns_name = ns_name
        self.allowed_methods = None  # be careful, None means all methods
                                     # are allowed while an empty list
                                     # means totally closed.
        self.jobs = []

        self.reset_acl()

        # Init the mixins if specified after.
        super(BaseNamespace, self).__init__()

    def is_method_allowed(self, method_name):
        """ACL system: this checks if you have access to that method_name,
        according to the set ACLs"""
        if self.allowed_methods is None:
            return True
        else:
            return method_name in self.allowed_methods

    def add_acl_method(self, method_name):
        """ACL system: make the method_name accessible to the current socket"""

        if isinstance(self.allowed_methods, set):
            self.allowed_methods.add(method_name)
        else:
            self.allowed_methods = set([method_name])

    def del_acl_method(self, method_name):
        """ACL system: ensure the user will not have access to that method."""
        if self.allowed_methods is None:
            raise ValueError(
                "Trying to delete an ACL method, but none were"
                + " defined yet! Or: No ACL restrictions yet, why would you"
                + " delete one?"
            )

        self.allowed_methods.remove(method_name)

    def lift_acl_restrictions(self):
        """ACL system: This removes restrictions on the Namespace's methods, so
        that all the ``on_*()`` and ``recv_*()`` can be accessed.
        """
        self.allowed_methods = None

    def get_initial_acl(self):
        """ACL system: If you define this function, you must return
        all the 'event' names that you want your User (the established
        virtual Socket) to have access to.

        If you do not define this function, the user will have free
        access to all of the ``on_*()`` and ``recv_*()`` functions,
        etc.. methods.

        Return something like: ``['on_connect', 'on_public_method']``

        You can later modify this list dynamically (inside
        ``on_connect()`` for example) using:

        .. code-block:: python

           self.add_acl_method('on_secure_method')

        ``self.request`` is available in here, if you're already ready to
        do some auth. check.

        The ACLs are checked by the :meth:`process_packet` and/or
        :meth:`process_event` default implementations, before calling
        the class's methods.

        **Beware**, returning ``None`` leaves the namespace completely
        accessible.
        """
        return None

    def reset_acl(self):
        """Resets ACL to its initial value (calling
        :meth:`get_initial_acl`` and applying that again).
        """
        self.allowed_methods = self.get_initial_acl()

    def process_packet(self, packet):
        """If you override this, NONE of the functions in this class
        will be called.  It is responsible for dispatching to
        :meth:`process_event` (which in turn calls ``on_*()`` and
        ``recv_*()`` methods).

        If the packet arrived here, it is because it belongs to this endpoint.

        For each packet arriving, the only possible path of execution, that is,
        the only methods that *can* be called are the following:

        * recv_connect()
        * recv_message()
        * recv_json()
        * recv_error()
        * recv_disconnect()
        * on_*()
        """
        packet_type = packet['type']

        if packet_type == 'event':
            return self.process_event(packet)
        elif packet_type == 'message':
            return self.call_method_with_acl('recv_message', packet,
                                             packet['data'])
        elif packet_type == 'json':
            return self.call_method_with_acl('recv_json', packet,
                                             packet['data'])
        elif packet_type == 'connect':
            self.socket.send_packet(packet)
            return self.call_method_with_acl('recv_connect', packet)
        elif packet_type == 'error':
            return self.call_method_with_acl('recv_error', packet)
        elif packet_type == 'ack':
            callback = self.socket._pop_ack_callback(packet['ackId'])
            if not callback:
                print "ERROR: No such callback for ackId %s" % packet['ackId']
                return
            try:
                return callback(*(packet['args']))
            except TypeError, e:
                print "ERROR: Call to callback function failed", packet
        elif packet_type == 'disconnect':
            # Force a disconnect on the namespace.
            return self.call_method_with_acl('recv_disconnect', packet)
        else:
            print "Unprocessed packet", packet
        # TODO: manage the other packet types: disconnect

    def process_event(self, packet):
        """This function dispatches ``event`` messages to the correct
        functions. You should override this method only if you are not
        satisfied with the automatic dispatching to
        ``on_``-prefixed methods.  You could then implement your own dispatch.
        See the source code for inspiration.

        To process events that have callbacks on the client side, you
        must define your event with a single parameter: ``packet``.
        In this case, it will be the full ``packet`` object and you
        can inspect its ``ack`` and ``id`` keys to define if and how
        you reply.  A correct reply to an event with a callback would
        look like this:

        .. code-block:: python

          def on_my_callback(self, packet):
              if 'ack' in packet':
                  self.emit('go_back', 'param1', id=packet['id'])
        """
        args = packet['args']
        name = packet['name']
        if not allowed_event_name_regex.match(name):
            self.error("unallowed_event_name",
                       "name must only contains alpha numerical characters")
            return

        method_name = 'on_' + name.replace(' ', '_')
        # This means the args, passed as a list, will be expanded to
        # the method arg and if you passed a dict, it will be a dict
        # as the first parameter.

        return self.call_method_with_acl(method_name, packet, *args)

    def call_method_with_acl(self, method_name, packet, *args):
        """You should always use this function to call the methods,
        as it checks if the user is allowed according to the ACLs.

        If you override :meth:`process_packet` or
        :meth:`process_event`, you should definitely want to use this
        instead of ``getattr(self, 'my_method')()``
        """
        if not self.is_method_allowed(method_name):
            self.error('method_access_denied',
                       'You do not have access to method "%s"' % method_name)
            return

        return self.call_method(method_name, packet, *args)

    def call_method(self, method_name, packet, *args):
        """This function is used to implement the two behaviors on dispatched
        ``on_*()`` and ``recv_*()`` method calls.

        Those are the two behaviors:

        * If there is only one parameter on the dispatched method and
          it is equal to ``packet``, then pass in the packet as the
          sole parameter.

        * Otherwise, pass in the arguments as specified by the
          different ``recv_*()`` methods args specs, or the
          :meth:`process_event` documentation.
        """
        method = getattr(self, method_name, None)
        if method is None:
            self.error('no_such_method',
                       'The method "%s" was not found' % method_name)
            return

        specs = inspect.getargspec(method)
        func_args = specs.args
        if not len(func_args) or func_args[0] != 'self':
            self.error("invalid_method_args",
                "The server-side method is invalid, as it doesn't "
                "have 'self' as its first argument")
            return
        if len(func_args) == 2 and func_args[1] == 'packet':
            return method(packet)
        else:
            return method(*args)

    def initialize(self):
        """This is called right after ``__init__``, on the initial
        creation of a namespace so you may handle any setup job you
        need.

        Namespaces are created only when some packets arrive that ask
        for the namespace.  They are not created altogether when a new
        :class:`~socketio.virtsocket.Socket` connection is established,
        so you can have many many namespaces assigned (when calling
        :func:`~socketio.socketio_manage`) without clogging the
        memory.

        If you override this method, you probably want to only
        initialize the variables you're going to use in the events of
        this namespace, say, with some default values, but not perform
        any operation that assumes authentication/authorization.
        """
        pass

    def recv_message(self, data):
        """This is more of a backwards compatibility hack. This will be
        called for messages sent with the original send() call on the client
        side. This is NOT the 'message' event, which you will catch with
        'on_message()'. The data arriving here is a simple string, with no
        other info.

        If you want to handle those messages, you should override this method.
        """
        return data

    def recv_json(self, data):
        """This is more of a backwards compatibility hack. This will be
        called for JSON packets sent with the original json() call on the
        JavaScript side. This is NOT the 'json' event, which you will catch
        with 'on_json()'. The data arriving here is a python dict, with no
        event name.

        If you want to handle those messages, you should override this method.
        """
        return data

    def recv_disconnect(self):
        """Override this function if you want to do something when you get a
        *force disconnect* packet.

        By default, this function calls the :meth:`disconnect` clean-up
        function.  You probably want to call it yourself also, and put
        your clean-up routines in :meth:`disconnect` rather than here,
        because that :meth:`disconnect` function gets called
        automatically upon disconnection.  This function is a
        pre-handle for when you get the `disconnect packet`.
        """
        self.disconnect(silent=True)

    def recv_connect(self):
        """Called the first time a client connection is open on a
        Namespace. This *does not* fire on the global namespace.

        This allows you to do boilerplate stuff for
        the namespace like connecting to rooms, broadcasting events
        to others, doing authorization work, and tweaking the ACLs to open
        up the rest of the namespace (if it was closed at the
        beginning by having :meth:`get_initial_acl` return only
        ['recv_connect'])

        Also see the different :ref:`mixins <mixins_module>` (like
        `RoomsMixin`, `BroadcastMixin`).
        """
        pass

    def recv_error(self, packet):
        """Override this function to handle the errors we get from the client.

        :param packet: the full packet.
        """
        pass

    def error(self, error_name, error_message, msg_id=None, quiet=False):
        """Use this to use the configured ``error_handler`` yield an
        error message to your application.

        :param error_name: is a short string, to associate messages to recovery
                           methods
        :param error_message: is some human-readable text, describing the error
        :param msg_id: is used to associate with a request
        :param quiet: specific to error_handlers. The default doesn't send a
                      message to the user, but shows a debug message on the
                      developer console.
        """
        self.socket.error(error_name, error_message, endpoint=self.ns_name,
                          msg_id=msg_id, quiet=quiet)

    def send(self, message, json=False, callback=None):
        """Use send to send a simple string message.

        If ``json`` is True, the message will be encoded as a JSON object
        on the wire, and decoded on the other side.

        This is mostly for backwards compatibility.  ``emit()`` is more fun.

        :param callback: This is a callback function that will be
                         called automatically by the client upon
                         reception.  It does not verify that the
                         listener over there was completed with
                         success.  It just tells you that the browser
                         got a hold of the packet.
        :type callback: callable
        """
        pkt = dict(type="message", data=message, endpoint=self.ns_name)
        if json:
            pkt['type'] = "json"

        if callback:
            # By passing ack=True, we use the old behavior of being returned
            # an 'ack' packet, automatically triggered by the client-side
            # with no user-code being run.  The emit() version of the
            # callback is more useful I think :)  So migrate your code.
            pkt['ack'] = True
            pkt['id'] = msgid = self.socket._get_next_msgid()
            self.socket._save_ack_callback(msgid, callback)

        self.socket.send_packet(pkt)

    def emit(self, event, *args, **kwargs):
        """Use this to send a structured event, with a name and arguments, to
        the client.

        By default, it uses this namespace's endpoint. You can send messages on
        other endpoints with something like:

            ``self.socket['/other_endpoint'].emit()``.

        However, it is possible that the ``'/other_endpoint'`` was not
        initialized yet, and that would yield a ``KeyError``.

        The only supported ``kwargs`` is ``callback``.  All other parameters
        must be passed positionally.

        :param event: The name of the event to trigger on the other end.
        :param callback: Pass in the callback keyword argument to define a
                         call-back that will be called when the client acks.

                         This callback is slightly different from the one from
                         ``send()``, as this callback will receive parameters
                         from the explicit call of the ``ack()`` function
                         passed to the listener on the client side.

                         The remote listener will need to explicitly ack (by
                         calling its last argument, a function which is
                         usually called 'ack') with some parameters indicating
                         success or error.  The 'ack' packet coming back here
                         will then trigger the callback function with the
                         returned values.
        :type callback: callable
        """
        callback = kwargs.pop('callback', None)

        if kwargs:
            raise ValueError(
                "emit() only supports positional argument, to stay "
                "compatible with the Socket.IO protocol. You can "
                "however pass in a dictionary as the first argument")
        pkt = dict(type="event", name=event, args=args,
                   endpoint=self.ns_name)

        if callback:
            # By passing 'data', we indicate that we *want* an explicit ack
            # by the client code, not an automatic as with send().
            pkt['ack'] = 'data'
            pkt['id'] = msgid = self.socket._get_next_msgid()
            self.socket._save_ack_callback(msgid, callback)

        self.socket.send_packet(pkt)

    def spawn(self, fn, *args, **kwargs):
        """Spawn a new process, attached to this Namespace.

        It will be monitored by the "watcher" process in the Socket. If the
        socket disconnects, all these greenlets are going to be killed, after
        calling BaseNamespace.disconnect()
        """
        # self.log.debug("Spawning sub-Namespace Greenlet: %s" % fn.__name__)
        new = gevent.spawn(fn, *args, **kwargs)
        self.jobs.append(new)
        return new

    def disconnect(self, silent=False):
        """Send a 'disconnect' packet, so that the user knows it has been
        disconnected (booted actually).  This will trigger an onDisconnect()
        call on the client side.

        Over here, we will kill all ``spawn``ed processes and remove the
        namespace from the Socket object.

        :param silent: do not actually send the packet (if they asked for a
                       disconnect for example), but just kill all jobs spawned
                       by this Namespace, and remove it from the Socket.
        """
        if not silent:
            packet = {"type": "disconnect",
                      "endpoint": self.ns_name}
            self.socket.send_packet(packet)
        self.socket.remove_namespace(self.ns_name)
        self.kill_local_jobs()

    def kill_local_jobs(self):
        """Kills all the jobs spawned with BaseNamespace.spawn() on a namespace
        object.

        This will be called automatically if the ``watcher`` process detects
        that the Socket was closed.
        """
        gevent.killall(self.jobs)
        self.jobs = []
