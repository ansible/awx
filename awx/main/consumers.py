
import os
import json
import logging
import codecs
import datetime
import hmac

from django.utils.encoding import force_bytes
from django.utils.encoding import smart_str
from django.http.cookie import parse_cookie
from django.core.serializers.json import DjangoJSONEncoder
from django.conf import settings
from django.utils.encoding import force_bytes

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.layers import get_channel_layer
from channels.db import database_sync_to_async

from asgiref.sync import async_to_sync

from awx.main.channels import wrap_broadcast_msg


logger = logging.getLogger('awx.main.consumers')
XRF_KEY = '_auth_user_xrf'
BROADCAST_GROUP = 'broadcast-group_send'


class WebsocketSecretAuthHelper:
    """
    Middlewareish for websockets to verify node websocket broadcast interconnect.

    Note: The "ish" is due to the channels routing interface. Routing occurs 
    _after_ authentication; making it hard to apply this auth to _only_ a subset of
    websocket endpoints.
    """

    @classmethod
    def construct_secret(cls):
        nonce_serialized = "{}".format(int((datetime.datetime.utcnow()-datetime.datetime.fromtimestamp(0)).total_seconds()))
        payload_dict = {
            'secret': settings.BROADCAST_WEBSOCKETS_SECRET,
            'nonce': nonce_serialized
        }
        payload_serialized = json.dumps(payload_dict)

        secret_serialized = hmac.new(force_bytes(settings.BROADCAST_WEBSOCKETS_SECRET),
                                     msg=force_bytes(payload_serialized),
                                     digestmod='sha256').hexdigest()

        return 'HMAC-SHA256 {}:{}'.format(nonce_serialized, secret_serialized)


    @classmethod
    def verify_secret(cls, s, nonce_tolerance=300):
        hex_decoder = codecs.getdecoder("hex_codec")

        try:
            (prefix, payload) = s.split(' ')
            if prefix != 'HMAC-SHA256':
                raise ValueError('Unsupported encryption algorithm')
            (nonce_parsed, secret_parsed) = payload.split(':')
        except Exception:
            raise ValueError("Failed to parse secret")

        try:
            payload_expected = {
                'secret': settings.BROADCAST_WEBSOCKETS_SECRET,
                'nonce': nonce_parsed,
            }
            payload_serialized = json.dumps(payload_expected)
        except Exception:
            raise ValueError("Failed to create hash to compare to secret.")

        secret_serialized = hmac.new(force_bytes(settings.BROADCAST_WEBSOCKETS_SECRET),
                                     msg=force_bytes(payload_serialized),
                                     digestmod='sha256').hexdigest()

        if secret_serialized != secret_parsed:
            raise ValueError("Invalid secret")

        # Avoid timing attack and check the nonce after all the heavy lifting
        now = datetime.datetime.utcnow()
        nonce_parsed = datetime.datetime.fromtimestamp(int(nonce_parsed))
        if (now-nonce_parsed).total_seconds() > nonce_tolerance:
            raise ValueError("Potential replay attack or machine(s) time out of sync.")

        return True

    @classmethod
    def is_authorized(cls, scope):
        secret = ''
        for k, v in scope['headers']:
            if k.decode("utf-8") == 'secret':
                secret = v.decode("utf-8")
                break
        WebsocketSecretAuthHelper.verify_secret(secret)


class BroadcastConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        try:
            WebsocketSecretAuthHelper.is_authorized(self.scope)
        except Exception:
            await self.close()
            return

        # TODO: log ip of connected client
        logger.info("Client connected")
        await self.accept()
        await self.channel_layer.group_add(BROADCAST_GROUP, self.channel_name)

    async def disconnect(self, code):
        # TODO: log ip of disconnected client
        logger.info("Client disconnected")

    async def internal_message(self, event):
        await self.send(event['text'])


class EventConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope['user']
        if user and not user.is_anonymous:
            await self.accept()
            await self.send_json({"accept": True, "user": user.id})
            # store the valid CSRF token from the cookie so we can compare it later
            # on ws_receive
            cookie_token = self.scope['cookies'].get('csrftoken')
            if cookie_token:
                self.scope['session'][XRF_KEY] = cookie_token
        else:
            logger.error("Request user is not authenticated to use websocket.")
            # TODO: Carry over from channels 1 implementation
            # We should never .accept() the client and close without sending a close message
            await self.accept()
            await self.send_json({"close": True})
            await self.close()

    @database_sync_to_async
    def user_can_see_object_id(self, user_access):
        return user_access.get_queryset().filter(pk=oid).exists()

    async def receive_json(self, data):
        from awx.main.access import consumer_access
        user = self.scope['user']
        xrftoken = data.get('xrftoken')
        if (
            not xrftoken or
            XRF_KEY not in self.scope["session"] or
            xrftoken != self.scope["session"][XRF_KEY]
        ):
            logger.error(
            "access denied to channel, XRF mismatch for {}".format(user.username)
            )
            await self.send_json({"error": "access denied to channel"})
            return

        if 'groups' in data:
            groups = data['groups']
            new_groups = set()
            current_groups = set(self.scope['session'].pop('groups') if 'groups' in self.scope['session'] else [])
            for group_name,v in groups.items():
                if type(v) is list:
                    for oid in v:
                        name = '{}-{}'.format(group_name, oid)
                        access_cls = consumer_access(group_name)
                        if access_cls is not None:
                            user_access = access_cls(user)
                            if not self.user_can_see_object_id(user_access):
                                await self.send_json({"error": "access denied to channel {0} for resource id {1}".format(group_name, oid)})
                                continue

                        new_groups.add(name)
                else:
                    if group_name == BROADCAST_GROUP:
                        logger.warn("Non-priveleged client asked to join broadcast group!")
                        return

                    new_groups.add(name)

            old_groups = current_groups - new_groups
            for group_name in old_groups:
                await self.channel_layer.group_discard(
                    group_name,
                    self.channel_name,
                )

            new_groups_exclusive = new_groups - current_groups
            for group_name in new_groups_exclusive:
                await self.channel_layer.group_add(
                    group_name,
                    self.channel_name
                )
            logger.debug(f"Channel {self.channel_name} left groups {old_groups} and joined {new_groups_exclusive}")
            self.scope['session']['groups'] = new_groups

    async def internal_message(self, event):
        await self.send(event['text'])


def emit_channel_notification(group, payload):
    try:
        payload = json.dumps(payload, cls=DjangoJSONEncoder)
    except ValueError:
        logger.error("Invalid payload emitting channel {} on topic: {}".format(group, payload))
        return

    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": "internal.message",
            "text": payload
        },
    )

    async_to_sync(channel_layer.group_send)(
        BROADCAST_GROUP,
        {
            "type": "internal.message",
            "text": wrap_broadcast_msg(group, payload),
        },
    )

