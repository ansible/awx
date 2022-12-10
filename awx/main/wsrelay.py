import json
import logging
import asyncio

import aiohttp
from aiohttp import client_exceptions
from asgiref.sync import sync_to_async

from channels.layers import get_channel_layer
from channels.db import database_sync_to_async

from django.conf import settings
from django.apps import apps

import psycopg

from awx.main.analytics.broadcast_websocket import (
    RelayWebsocketStats,
    RelayWebsocketStatsManager,
)
import awx.main.analytics.subsystem_metrics as s_metrics

logger = logging.getLogger('awx.main.wsrelay')


def wrap_broadcast_msg(group, message: str):
    # TODO: Maybe wrap as "group","message" so that we don't need to
    # encode/decode as json.
    return dict(group=group, message=message)


def get_local_host():
    Instance = apps.get_model('main', 'Instance')
    return Instance.objects.my_hostname()


class WebsocketRelayConnection:
    def __init__(
        self,
        name,
        stats: RelayWebsocketStats,
        remote_host: str,
        remote_port: int = settings.BROADCAST_WEBSOCKET_PORT,
        protocol: str = settings.BROADCAST_WEBSOCKET_PROTOCOL,
        verify_ssl: bool = settings.BROADCAST_WEBSOCKET_VERIFY_CERT,
    ):
        self.name = name
        self.event_loop = asyncio.get_event_loop()
        self.stats = stats
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.protocol = protocol
        self.verify_ssl = verify_ssl
        self.channel_layer = None
        self.subsystem_metrics = s_metrics.Metrics(instance_name=name)
        self.producers = dict()

    async def run_loop(self, websocket: aiohttp.ClientWebSocketResponse):
        raise RuntimeError("Implement me")

    async def connect(self, attempt):
        from awx.main.consumers import WebsocketSecretAuthHelper  # noqa

        logger.debug(f"Connection from {self.name} to {self.remote_host} attempt number {attempt}.")

        '''
        Can not put get_channel_layer() in the init code because it is in the init
        path of channel layers i.e. RedisChannelLayer() calls our init code.
        '''
        if not self.channel_layer:
            self.channel_layer = get_channel_layer()

        try:
            if attempt > 0:
                await asyncio.sleep(settings.BROADCAST_WEBSOCKET_RECONNECT_RETRY_RATE_SECONDS)
        except asyncio.CancelledError:
            logger.warning(f"Connection from {self.name} to {self.remote_host} cancelled")
            raise

        uri = f"{self.protocol}://{self.remote_host}:{self.remote_port}/websocket/relay/"
        timeout = aiohttp.ClientTimeout(total=10)

        secret_val = WebsocketSecretAuthHelper.construct_secret()
        try:
            async with aiohttp.ClientSession(headers={'secret': secret_val}, timeout=timeout) as session:
                async with session.ws_connect(uri, ssl=self.verify_ssl, heartbeat=20) as websocket:
                    logger.info(f"Connection from {self.name} to {self.remote_host} established.")
                    self.stats.record_connection_established()
                    attempt = 0
                    await self.run_connection(websocket)
        except asyncio.CancelledError:
            # TODO: Check if connected and disconnect
            # Possibly use run_until_complete() if disconnect is async
            logger.warning(f"Connection from {self.name} to {self.remote_host} cancelled.")
            self.stats.record_connection_lost()
            raise
        except client_exceptions.ClientConnectorError as e:
            logger.warning(f"Connection from {self.name} to {self.remote_host} failed: '{e}'.", exc_info=True)
        except asyncio.TimeoutError:
            logger.warning(f"Connection from {self.name} to {self.remote_host} timed out.")
        except Exception as e:
            # Early on, this is our canary. I'm not sure what exceptions we can really encounter.
            logger.warning(f"Connection from {self.name} to {self.remote_host} failed for unknown reason: '{e}'.", exc_info=True)
        else:
            logger.warning(f"Connection from {self.name} to {self.remote_host} list.")

        self.stats.record_connection_lost()
        self.start(attempt=attempt + 1)

    def start(self, attempt=0):
        self.async_task = self.event_loop.create_task(self.connect(attempt=attempt))

        return self.async_task

    def cancel(self):
        self.async_task.cancel()

    async def run_connection(self, websocket: aiohttp.ClientWebSocketResponse):
        async for msg in websocket:
            self.stats.record_message_received()

            if msg.type == aiohttp.WSMsgType.ERROR:
                break
            elif msg.type == aiohttp.WSMsgType.TEXT:
                try:
                    payload = json.loads(msg.data)
                except json.JSONDecodeError:
                    logmsg = "Failed to decode broadcast message"
                    if logger.isEnabledFor(logging.DEBUG):
                        logmsg = "{} {}".format(logmsg, payload)
                    logger.warning(logmsg)
                    continue

            if payload.get("type") == "consumer.subscribe":
                for group in payload['groups']:
                    name = f"{self.remote_host}-{group}"
                    origin_channel = payload['origin_channel']
                    if not self.producers.get(name):
                        producer = self.event_loop.create_task(self.run_producer(name, websocket, group))

                        self.producers[name] = {"task": producer, "subscriptions": {origin_channel}}
                        logger.debug(f"Producer {name} started.")
                    else:
                        self.producers[name]["subscriptions"].add(origin_channel)
                        logger.debug(f"Connection from {self.name} to {self.remote_host} added subscription to {group}.")

            if payload.get("type") == "consumer.unsubscribe":
                for group in payload['groups']:
                    name = f"{self.remote_host}-{group}"
                    origin_channel = payload['origin_channel']
                    try:
                        self.producers[name]["subscriptions"].remove(origin_channel)
                        logger.debug(f"Unsubscribed {origin_channel} from {name}")
                    except KeyError:
                        logger.warning(f"Producer {name} not found.")

    async def run_producer(self, name, websocket, group):
        try:
            logger.info(f"Starting producer for {name}")

            consumer_channel = await self.channel_layer.new_channel()
            await self.channel_layer.group_add(group, consumer_channel)

            while True:
                try:
                    msg = await asyncio.wait_for(self.channel_layer.receive(consumer_channel), timeout=10)
                    if not msg.get("needs_relay"):
                        # This is added in by emit_channel_notification(). It prevents us from looping
                        # in the event that we are sharing a redis with a web instance. We'll see the
                        # message once (it'll have needs_relay=True), we'll delete that, and then forward
                        # the message along. The web instance will add it back to the same channels group,
                        # but it won't have needs_relay=True, so we'll ignore it.
                        continue
                    del msg["needs_relay"]
                except asyncio.TimeoutError:
                    current_subscriptions = self.producers[name]["subscriptions"]
                    if len(current_subscriptions) == 0:
                        logger.info(f"Producer {name} has no subscribers, shutting down.")
                        return

                    continue

                await websocket.send_json(wrap_broadcast_msg(group, msg))
        except Exception:
            # Note, this is very intentional and important since we do not otherwise
            # ever check the result of this future. Without this line you will not see an error if
            # something goes wrong in here.
            logger.exception(f"Event relay producer {name} crashed")
        finally:
            await self.channel_layer.group_discard(group, consumer_channel)
            del self.producers[name]


class WebSocketRelayManager(object):
    def __init__(self):

        self.local_hostname = get_local_host()
        self.relay_connections = dict()
        # hostname -> ip
        self.known_hosts: Dict[str, str] = dict()

    async def pg_consumer(self, conn):
        try:
            await conn.execute("LISTEN web_heartbeet")
            async for notif in conn.notifies():
                if notif is not None and notif.channel == "web_heartbeet":
                    try:
                        payload = json.loads(notif.payload)
                    except json.JSONDecodeError:
                        logmsg = "Failed to decode message from pg_notify channel `web_heartbeet`"
                        if logger.isEnabledFor(logging.DEBUG):
                            logmsg = "{} {}".format(logmsg, payload)
                        logger.warning(logmsg)
                        continue

                    # Skip if the message comes from the same host we are running on
                    # In this case, we'll be sharing a redis, no need to relay.
                    if payload.get("hostname") == self.local_hostname:
                        continue

                    if payload.get("action") == "online":
                        hostname = payload["hostname"]
                        ip = payload["ip"]
                        if ip is None:
                            # If we don't get an IP, just try the hostname, maybe it resolves
                            ip = hostname
                        self.known_hosts[hostname] = ip
                        logger.debug(f"Web host {hostname} ({ip}) online heartbeat received.")
                    elif payload.get("action") == "offline":
                        hostname = payload["hostname"]
                        del self.known_hosts[hostname]
                        logger.debug(f"Web host {hostname} ({ip}) offline heartbeat received.")
        except Exception as e:
            # This catch-all is the same as the one above. asyncio will NOT log exceptions anywhere, so we need to do so ourselves.
            logger.exception(f"pg_consumer exception")

    async def run(self):
        event_loop = asyncio.get_running_loop()

        stats_mgr = RelayWebsocketStatsManager(event_loop, self.local_hostname)
        stats_mgr.start()

        # Set up a pg_notify consumer for allowing web nodes to "provision" and "deprovision" themselves gracefully.
        database_conf = settings.DATABASES['default']
        async_conn = await psycopg.AsyncConnection.connect(
            dbname=database_conf['NAME'],
            host=database_conf['HOST'],
            user=database_conf['USER'],
            password=database_conf['PASSWORD'],
            port=database_conf['PORT'],
            **database_conf.get("OPTIONS", {}),
        )
        await async_conn.set_autocommit(True)
        event_loop.create_task(self.pg_consumer(async_conn))

        # Establishes a websocket connection to /websocket/relay on all API servers
        while True:
            logger.info("Current known hosts: {}".format(self.known_hosts))
            future_remote_hosts = self.known_hosts.keys()
            current_remote_hosts = self.relay_connections.keys()
            deleted_remote_hosts = set(current_remote_hosts) - set(future_remote_hosts)
            new_remote_hosts = set(future_remote_hosts) - set(current_remote_hosts)

            remote_addresses = {k: v.remote_host for k, v in self.relay_connections.items()}
            for hostname, address in self.known_hosts.items():
                if hostname in self.relay_connections and address != remote_addresses[hostname]:
                    deleted_remote_hosts.add(hostname)
                    new_remote_hosts.add(hostname)

            if deleted_remote_hosts:
                logger.info(f"Removing {deleted_remote_hosts} from websocket broadcast list")

            if new_remote_hosts:
                logger.info(f"Adding {new_remote_hosts} to websocket broadcast list")

            for h in deleted_remote_hosts:
                self.relay_connections[h].cancel()
                del self.relay_connections[h]
                stats_mgr.delete_remote_host_stats(h)

            for h in new_remote_hosts:
                stats = stats_mgr.new_remote_host_stats(h)
                logger.debug(f"Starting relay connection to {h}")
                relay_connection = WebsocketRelayConnection(name=self.local_hostname, stats=stats, remote_host=self.known_hosts[h])
                relay_connection.start()
                self.relay_connections[h] = relay_connection

            # for host, conn in self.relay_connections.items():
            #     logger.info(f"Current producers for {host}: {conn.producers}")

            await asyncio.sleep(settings.BROADCAST_WEBSOCKET_NEW_INSTANCE_POLL_RATE_SECONDS)
