"""
kombu.transport.zookeeper
=========================

Zookeeper transport.

:copyright: (c) 2010 - 2012 by Mahendra M.
:license: BSD, see LICENSE for more details.

**Synopsis**

- Connects to a zookeeper node as <server>:<port>/<vhost>
  The <vhost> becomes the base for all the other znodes. So we can use
  it like a vhost
- A queue is a znode under the <vhost> path
- Creates a new sequential node under the queue and writes the message to it
- If priority is used, we will use it in the node name, so that higher
  priority messages are picked up first
- Keep consuming messages from the top of the queue, till we
  are able to delete a particular message. If deletion raises a
  NoNode exception, we try again with the next message

**References**

- https://zookeeper.apache.org/doc/trunk/recipes.html#sc_recipes_Queues
- http://bit.ly/cZHf9g

**Limitations**

- A queue cannot handle more than 2^32 messages. This is an internal
  limitation with zookeeper. This has to be handled internally in this
  module.

"""
from __future__ import absolute_import

from Queue import Empty

import socket

from anyjson import loads, dumps

from kombu.exceptions import StdConnectionError, StdChannelError
from . import virtual

try:
    import kazoo

    KZ_CONNECTION_ERRORS = (
        kazoo.zkclient.SystemErrorException,
        kazoo.zkclient.ConnectionLossException,
        kazoo.zkclient.MarshallingErrorException,
        kazoo.zkclient.UnimplementedException,
        kazoo.zkclient.OperationTimeoutException,
        kazoo.zkclient.NoAuthException,
        kazoo.zkclient.InvalidACLException,
        kazoo.zkclient.AuthFailedException,
        kazoo.zkclient.SessionExpiredException,
    )

    KZ_CHANNEL_ERRORS = (
        kazoo.zkclient.RuntimeInconsistencyException,
        kazoo.zkclient.DataInconsistencyException,
        kazoo.zkclient.BadArgumentsException,
        kazoo.zkclient.MarshallingErrorException,
        kazoo.zkclient.UnimplementedException,
        kazoo.zkclient.OperationTimeoutException,
        kazoo.zkclient.ApiErrorException,
        kazoo.zkclient.NoNodeException,
        kazoo.zkclient.NoAuthException,
        kazoo.zkclient.NodeExistsException,
        kazoo.zkclient.NoChildrenForEphemeralsException,
        kazoo.zkclient.NotEmptyException,
        kazoo.zkclient.SessionExpiredException,
        kazoo.zkclient.InvalidCallbackException,
    )
except ImportError:
    kazoo = None                                    # noqa
    KZ_CONNECTION_ERRORS = KZ_CHANNEL_ERRORS = ()   # noqa

DEFAULT_PORT = 2181

__author__ = 'Mahendra M <mahendra.m@gmail.com>'


class Channel(virtual.Channel):

    _client = None

    def _get_queue(self, queue):
        return '/%s' % (queue, )

    def _put(self, queue, message, **kwargs):
        try:
            priority = message['properties']['delivery_info']['priority']
        except KeyError:
            priority = 0

        msg_id = '%s/msg-%02d' % (self._get_queue(queue), priority % 10)
        self.client.create(msg_id, dumps(message), sequence=True)

    def _get_msg(self, queue, msgs):
        msgs.sort()  # this is a bad hack, but required

        for msg_id in msgs:
            msg_id = '%s/%s' % (queue, msg_id)
            try:
                message, headers = self.client.get(msg_id)
                self.client.delete(msg_id)
            except kazoo.zkclient.NoNodeException:
                pass  # Someone has got this message
            else:
                return loads(message)

        raise Empty()

    def _get(self, queue):
        queue = self._get_queue(queue)
        msgs = self.client.get_children(queue)
        return self._get_msg(queue, msgs)

    def _purge(self, queue):
        failures = 0
        queue = self._get_queue(queue)

        for count, msg_id in enumerate(self.client.get_children(queue)):
            try:
                self.client.delete('%s/%s' % (queue, msg_id))
            except kazoo.zkclient.NoNodeException:
                failures += 1
        return count - failures

    def _delete(self, queue, *args, **kwargs):
        if self._has_queue(queue):
            queue = self._get_queue(queue)
            self._purge(queue)
            self.client.delete(queue)

    def _size(self, queue):
        _, meta = self.client.get(self._get_queue(queue))
        return meta['numChildren']

    def _new_queue(self, queue, **kwargs):
        if not self._has_queue(queue):
            self.client.create(self._get_queue(queue), '')

    def _has_queue(self, queue):
        return self.client.exists(self._get_queue(queue)) is not None

    def _open(self):
        conninfo = self.connection.client
        port = conninfo.port or DEFAULT_PORT
        conn_str = '%s:%s' % (conninfo.hostname, port)
        conn_str += '/' + conninfo.virtual_host[0:-1]

        conn = kazoo.ZooKeeperClient(conn_str)
        conn.connect(timeout=conninfo.connect_timeout)
        return conn

    @property
    def client(self):
        if self._client is None:
            self._client = self._open()
        return self._client


class Transport(virtual.Transport):
    Channel = Channel
    polling_interval = 1
    default_port = DEFAULT_PORT
    connection_errors = (StdConnectionError, ) + KZ_CONNECTION_ERRORS
    channel_errors = (StdChannelError, socket.error) + KZ_CHANNEL_ERRORS
    driver_type = 'zookeeper'
    driver_name = 'kazoo'

    def __init__(self, *args, **kwargs):
        if kazoo is None:
            raise ImportError('The kazoo library is not installed')

        super(Transport, self).__init__(*args, **kwargs)

    def driver_version(self):
        return kazoo.__version__
