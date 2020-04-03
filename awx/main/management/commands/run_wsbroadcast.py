# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.
import logging
import asyncio
import datetime
import re
from datetime import datetime as dt

from django.core.management.base import BaseCommand

from awx.main.analytics.broadcast_websocket import (
    BroadcastWebsocketStatsManager,
    safe_name,
)
from awx.main.wsbroadcast import BroadcastWebsocketManager
from awx.main.models.ha import Instance


logger = logging.getLogger('awx.main.wsbroadcast')


class Command(BaseCommand):
    help = 'Launch the websocket broadcaster'

    def add_arguments(self, parser):
        parser.add_argument('--status', dest='status', action='store_true',
                            help='print the internal state of any running broadcast websocket')

    @classmethod
    def display_len(cls, s):
        return len(re.sub('\x1b.*?m', '', s))

    @classmethod
    def _format_lines(cls, host_stats, padding=5):
        widths = [0 for i in host_stats[0]]
        for entry in host_stats:
            for i, e in enumerate(entry):
                if Command.display_len(e) > widths[i]:
                    widths[i] = Command.display_len(e)
        paddings = [padding for i in widths]

        lines = []
        for entry in host_stats:
            line = ""
            for pad, width, value in zip(paddings, widths, entry):
                if len(value) > Command.display_len(value):
                    width += len(value) - Command.display_len(value)
                total_width = width + pad
                line += f'{value:{total_width}}'
            lines.append(line)
        return lines

    @classmethod
    def get_connection_status(cls, me, hostnames, data):
        host_stats = [('hostame', 'state', 'start time', 'duration (sec)')]
        for h in hostnames:
            connection_color = '91'    # red
            h = safe_name(h)
            prefix = f'awx_{h}'
            connection_state = data.get(f'{prefix}_connection', 'N/A')
            connection_started = 'N/A'
            connection_duration = 'N/A'
            if connection_state is None:
                connection_state = 'unknown'
            if connection_state == 'connected':
                connection_color = '92' # green
                connection_started = data.get(f'{prefix}_connection_start', 'Error')
                if connection_started != 'Error':
                    connection_started = datetime.datetime.fromtimestamp(connection_started)
                    connection_duration = (dt.now() - connection_started).total_seconds()

            connection_state = f'\033[{connection_color}m{connection_state}\033[0m'

            host_stats.append((h, connection_state, str(connection_started), str(connection_duration)))

        return host_stats

    @classmethod
    def get_connection_stats(cls, me, hostnames, data):
        host_stats = [('hostame', 'total', 'per minute')]
        for h in hostnames:
            h = safe_name(h)
            prefix = f'awx_{h}'
            messages_total = data.get(f'{prefix}_messages_received', 'N/A')
            messages_per_minute = data.get(f'{prefix}_messages_received_per_minute', 'N/A')

            host_stats.append((h, str(int(messages_total)), str(int(messages_per_minute))))

        return host_stats

    def handle(self, *arg, **options):
        if options.get('status'):
            stats_all = BroadcastWebsocketStatsManager.get_stats_sync()
            data = {}
            for family in stats_all:
                if family.type == 'gauge' and len(family.samples) > 1:
                    for sample in family.samples:
                        if sample.value >= 1:
                            data[family.name] = sample.labels[family.name]
                            break
                else:
                    data[family.name] = family.samples[0].value
            me = Instance.objects.me()
            hostnames = [i.hostname for i in Instance.objects.exclude(hostname=me.hostname)]

            host_stats = Command.get_connection_status(me, hostnames, data)
            lines = Command._format_lines(host_stats)

            print(f'Broadcast websocket connection status from "{me.hostname}" to:')
            print('\n'.join(lines))

            host_stats = Command.get_connection_stats(me, hostnames, data)
            lines = Command._format_lines(host_stats)

            print(f'\nBroadcast websocket connection stats from "{me.hostname}" to:')
            print('\n'.join(lines))

            return

        try:
            broadcast_websocket_mgr = BroadcastWebsocketManager()
            task = broadcast_websocket_mgr.start()

            loop = asyncio.get_event_loop()
            loop.run_until_complete(task)
        except KeyboardInterrupt:
            logger.debug('Terminating Websocket Broadcaster')
