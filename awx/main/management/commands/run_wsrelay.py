# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.
import logging
import asyncio
import requests

from prometheus_client import CollectorRegistry
import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from awx.main.analytics.broadcast_websocket import (
    Metrics,
    MetricsRegistryBridge,
    MetricsManager,
)
from awx.main.analytics.subsystem_metrics import MetricsServer
from awx.main.wsrelay import WebSocketRelayManager


logger = logging.getLogger('awx.main.wsrelay')


class Command(BaseCommand):
    help = 'Launch the websocket broadcaster'

    def add_arguments(self, parser):
        parser.add_argument('--status', dest='status', action='store_true', help='print the internal state of any running broadcast websocket')

    def handle(self, *arg, **options):
        # it's necessary to delay this import in case
        # database migrations are still running
        from awx.main.models.ha import Instance

        if options.get('status'):
            res = requests.get(f"http://localhost:{settings.METRICS_SUBSYSTEM_CONFIG['server'][settings.METRICS_SERVICE_WEBSOCKET_RELAY]['port']}")
            print(res.content.decode("UTF-8"))
            return

        try:
            executor = MigrationExecutor(connection)
            migrating = bool(executor.migration_plan(executor.loader.graph.leaf_nodes()))
            connection.close()  # Because of async nature, main loop will use new connection, so close this
        except Exception as exc:
            logger.warning(f'Error on startup of run_wsrelay (error: {exc}), retry in 10s...')
            time.sleep(10)
            return

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
        if migrating:
            logger.info('AWX is currently migrating, retry in 10s...')
            time.sleep(10)
            return

        try:
            my_hostname = Instance.objects.my_hostname()
            logger.info('Active instance with hostname {} is registered.'.format(my_hostname))
        except RuntimeError as e:
            # the CLUSTER_HOST_ID in the task, and web instance must match and
            # ensure network connectivity between the task and web instance
            logger.info('Unable to return currently active instance: {}, retry in 5s...'.format(e))
            time.sleep(5)
            return

        while True:
            try:
                metrics = Metrics()
                registry = CollectorRegistry()
                MetricsRegistryBridge(metrics, registry, autoregister=True)
                metrics_mgr = MetricsManager(metrics)
                websocket_relay_manager = WebSocketRelayManager(metrics_mgr)

                MetricsServer(settings.METRICS_SERVICE_WEBSOCKET_RELAY, registry).start()

                asyncio.run(websocket_relay_manager.run())
            except KeyboardInterrupt:
                logger.info('Shutting down Websocket Relayer')
                break
            except Exception as e:
                logger.exception('Error in Websocket Relayer, exception: {}. Restarting in 10 seconds'.format(e))
                time.sleep(10)
