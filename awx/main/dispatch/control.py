import logging
import socket

from django.conf import settings

from awx.main.dispatch import get_local_queuename
from kombu import Connection, Queue, Exchange, Producer, Consumer

logger = logging.getLogger('awx.main.dispatch')


class Control(object):

    services = ('dispatcher', 'callback_receiver')
    result = None

    def __init__(self, service):
        if service not in self.services:
            raise RuntimeError('{} must be in {}'.format(service, self.services))
        self.service = service
        queuename = get_local_queuename()
        self.queue = Queue(queuename, Exchange(queuename), routing_key=queuename)

    def publish(self, msg, conn, host, **kwargs):
        producer = Producer(
            exchange=self.queue.exchange,
            channel=conn,
            routing_key=get_local_queuename()
        )
        producer.publish(msg, expiration=5, **kwargs)

    def status(self, *args, **kwargs):
        return self.control_with_reply('status', *args, **kwargs)

    def running(self, *args, **kwargs):
        return self.control_with_reply('running', *args, **kwargs)

    def control_with_reply(self, command, host=None, timeout=5):
        host = host or settings.CLUSTER_HOST_ID
        logger.warn('checking {} {} for {}'.format(self.service, command, host))
        reply_queue = Queue(name="amq.rabbitmq.reply-to")
        self.result = None
        with Connection(settings.BROKER_URL) as conn:
            with Consumer(conn, reply_queue, callbacks=[self.process_message], no_ack=True):
                self.publish({'control': command}, conn, host, reply_to='amq.rabbitmq.reply-to')
                try:
                    conn.drain_events(timeout=timeout)
                except socket.timeout:
                    logger.error('{} did not reply within {}s'.format(self.service, timeout))
                    raise
        return self.result

    def control(self, msg, host=None, **kwargs):
        host = host or settings.CLUSTER_HOST_ID
        with Connection(settings.BROKER_URL) as conn:
            self.publish(msg, conn, host)

    def process_message(self, body, message):
        self.result = body
        message.ack()
