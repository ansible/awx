# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.
import logging
import asyncio

from django.core.management.base import BaseCommand

from awx.main.wsbroadcast import BroadcastWebsocketManager


logger = logging.getLogger('awx.main.wsbroadcast')


class Command(BaseCommand):
    help = 'Launch the websocket broadcaster'

    def handle(self, *arg, **options):
        try:
            broadcast_websocket_mgr = BroadcastWebsocketManager()
            task = broadcast_websocket_mgr.start()

            loop = asyncio.get_event_loop()
            loop.run_until_complete(task)
        except KeyboardInterrupt:
            logger.debug('Terminating Websocket Broadcaster')
