import json
import logging
import os
import time
import signal
import sys

from django.core.management.base import BaseCommand
from django.conf import settings

from awx.main.dispatch import pg_bus_conn

logger = logging.getLogger('awx.main.commands.run_ws_heartbeat')


class Command(BaseCommand):
    help = 'Launch the web server beacon (ws_heartbeat)'

    def construct_payload(self, action='online'):
        payload = {
            'hostname': settings.CLUSTER_HOST_ID,
            'ip': os.environ.get('MY_POD_IP'),
            'action': action,
        }
        return json.dumps(payload)

    def notify_listener_and_exit(self, *args):
        with pg_bus_conn(new_connection=False) as conn:
            conn.notify('web_ws_heartbeat', self.construct_payload(action='offline'))
        sys.exit(0)

    def do_hearbeat_loop(self):
        while True:
            with pg_bus_conn() as conn:
                logger.debug('Sending heartbeat')
                conn.notify('web_ws_heartbeat', self.construct_payload())
            time.sleep(settings.BROADCAST_WEBSOCKET_BEACON_FROM_WEB_RATE_SECONDS)

    def handle(self, *arg, **options):
        signal.signal(signal.SIGTERM, self.notify_listener_and_exit)
        signal.signal(signal.SIGINT, self.notify_listener_and_exit)

        # Note: We don't really try any reconnect logic to pg_notify here,
        # just let supervisor restart if we fail.
        self.do_hearbeat_loop()
