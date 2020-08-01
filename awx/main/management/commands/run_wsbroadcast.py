# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.
import logging
import asyncio
import datetime
import re
import redis
import time
from datetime import datetime as dt

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Q
from django.db.migrations.executor import MigrationExecutor

from awx.main.analytics.broadcast_websocket import (
    BroadcastWebsocketStatsManager,
    safe_name,
)
from awx.main.wsbroadcast import BroadcastWebsocketManager


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
        host_stats = [('hostname', 'state', 'start time', 'duration (sec)')]
        for h in hostnames:
            connection_color = '91'    # red
            h_safe = safe_name(h)
            prefix = f'awx_{h_safe}'
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
                    connection_duration = int((dt.now() - connection_started).total_seconds())

            connection_state = f'\033[{connection_color}m{connection_state}\033[0m'

            host_stats.append((h, connection_state, str(connection_started), str(connection_duration)))

        return host_stats

    @classmethod
    def get_connection_stats(cls, me, hostnames, data):
        host_stats = [('hostname', 'total', 'per minute')]
        for h in hostnames:
            h_safe = safe_name(h)
            prefix = f'awx_{h_safe}'
            messages_total = data.get(f'{prefix}_messages_received', '0')
            messages_per_minute = data.get(f'{prefix}_messages_received_per_minute', '0')

            host_stats.append((h, str(int(messages_total)), str(int(messages_per_minute))))

        return host_stats

    def handle(self, *arg, **options):
        # it's necessary to delay this import in case
        # database migrations are still running
        from awx.main.models.ha import Instance

        executor = MigrationExecutor(connection)
        migrating = bool(executor.migration_plan(executor.loader.graph.leaf_nodes()))
        registered = False

        if not migrating:
            try:
                Instance.objects.me()
                registered = True
            except RuntimeError:
                pass

        if migrating or not registered:
            # In containerized deployments, migrations happen in the task container,
            # and the services running there don't start until migrations are
            # finished.
            # *This* service runs in the web container, and it's possible that it can
            # start _before_ migrations are finished, thus causing issues with the ORM
            # queries it makes (specifically, conf.settings queries).
            # This block is meant to serve as a sort of bail-out for the situation
            # where migrations aren't yet finished (similar to the migration
            # detection middleware that the uwsgi processes have) or when instance
            # registration isn't done yet
            logger.error('AWX is currently installing/upgrading.  Trying again in 5s...')
            time.sleep(5)
            return

        if options.get('status'):
            try:
                stats_all = BroadcastWebsocketStatsManager.get_stats_sync()
            except redis.exceptions.ConnectionError as e:
                print(f"Unable to get Broadcast Websocket Status. Failed to connect to redis {e}")
                return

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
            hostnames = [i.hostname for i in Instance.objects.exclude(Q(hostname=me.hostname) | Q(rampart_groups__controller__isnull=False))]

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
