
import os
import json
import logging

from django.utils.encoding import smart_str
from django.http.cookie import parse_cookie
from django.core.serializers.json import DjangoJSONEncoder

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.layers import get_channel_layer
from channels.db import database_sync_to_async

from asgiref.sync import async_to_sync

from awx.main.channels import wrap_broadcast_msg, BROADCAST_GROUP


logger = logging.getLogger('awx.main.consumers')
XRF_KEY = '_auth_user_xrf'


class EventConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope['user']
        secret = None
        for k, v in self.scope['headers']:
            if k.decode("utf-8") == 'secret':
                secret = v.decode("utf-8")
                break
        if secret:
            await self.accept()
            await self.channel_layer.group_add(BROADCAST_GROUP, self.channel_name)
        elif user:
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
            await self.send({"close": True})
            await self.close()

    async def disconnect(self, code):
        pass

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

        if 'groups' in data:
            groups = data['groups']
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

                        await self.channel_layer.group_add(
                            name,
                            self.channel_name
                        )
                else:
                    if group_name == BROADCAST_GROUP:
                        logger.warn("Non-priveleged client asked to join broadcast group!")
                        return

                    await self.channel_layer.group_add(
                        group_name,
                        self.channel_name
                    )

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
        BROADCAST_GROUP,
        {
            "type": "internal.message",
            "text": wrap_broadcast_msg(group, payload),
        },
    )

    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": "internal.message",
            "text": payload
        },
    )
