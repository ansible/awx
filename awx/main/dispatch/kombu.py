from amqp.exceptions import PreconditionFailed
from django.conf import settings
from kombu.connection import Connection as KombuConnection
from kombu.transport import pyamqp

import logging

logger = logging.getLogger('awx.main.dispatch')


__all__ = ['Connection']


class Connection(KombuConnection):

    def __init__(self, *args, **kwargs):
        super(Connection, self).__init__(*args, **kwargs)
        class _Channel(pyamqp.Channel):

            def queue_declare(self, queue, *args, **kwargs):
                kwargs['durable'] = settings.BROKER_DURABILITY
                try:
                    return super(_Channel, self).queue_declare(queue, *args, **kwargs)
                except PreconditionFailed as e:
                    if "inequivalent arg 'durable'" in getattr(e, 'reply_text', None):
                        logger.error(
                            'queue {} durability is not {}, deleting and recreating'.format(

                                queue,
                                kwargs['durable']
                            )
                        )
                        self.queue_delete(queue)
                    return super(_Channel, self).queue_declare(queue, *args, **kwargs)

        class _Connection(pyamqp.Connection):
            Channel = _Channel

        class _Transport(pyamqp.Transport):
            Connection = _Connection

        self.transport_cls = _Transport
