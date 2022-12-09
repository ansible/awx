import json
import logging
import os
import time

from django.core.management.base import BaseCommand
from django.conf import settings

from awx.main.dispatch import pg_bus_conn

logger = logging.getLogger('awx.main.commands.run_heartbeet')


class Command(BaseCommand):
    help = 'Launch the web server beacon (heartbeet)'

    # def add_arguments(self, parser):
    #    parser.add_argument('--status', dest='status', action='store_true', help='print the internal state of any running broadcast websocket')

    def print_banner(self):
        heartbeet = """
   **********   **********
 ************* *************
*****************************
 ***********HEART***********
  *************************
     *******************
       *************** _._
         *********** /`._ `'.      __
           *******   \  .\| \   _'`  `)
             ***  (``_)  \| ).'` /`- /
              *   `\ `;\_ `\\//`-'` /
                    \ `'.'.| /  __/`
                     `'--v_|/`'`
                         __||-._
                      /'` `-``  `'\\
                     /         .'` )
                     \  BEET  '    )
                      \.          /
                        '.     /'`
                           `) |
                            //
                            '(.
                             `\`.
                               ``"""
        print(heartbeet)

    def construct_payload(self, action='online'):
        payload = {
            'hostname': settings.CLUSTER_HOST_ID,
            'ip': os.environ.get('MY_POD_IP'),
            'action': action,
        }
        return json.dumps(payload)

    def do_hearbeat_loop(self):
        with pg_bus_conn(new_connection=True) as conn:
            while True:
                logger.debug('Sending heartbeat')
                conn.notify('web_heartbeet', self.construct_payload())
                time.sleep(settings.BROADCAST_WEBSOCKET_BEACON_FROM_WEB_RATE_SECONDS)

    # TODO: Send a message with action=offline if we notice a SIGTERM or SIGINT
    # (wsrelay can use this to remove the node quicker)
    def handle(self, *arg, **options):
        self.print_banner()

        # Note: We don't really try any reconnect logic to pg_notify here,
        # just let supervisor restart if we fail.
        self.do_hearbeat_loop()
