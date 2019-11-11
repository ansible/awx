import json
import logging

#from channels.auth import channel_session_user_from_http, channel_session_user

from django.utils.encoding import smart_str
from django.http.cookie import parse_cookie
from django.core.serializers.json import DjangoJSONEncoder
from channels.consumer import SyncConsumer
from channels.generic.websocket import JsonWebsocketConsumer
from channels.layers import get_channel_layer

#from awx.main.middleware import XRFMiddlewareStack


from asgiref.sync import async_to_sync


logger = logging.getLogger('awx.main.consumers')
#XRF_KEY = XRFMiddlewareStack.XRF_KEY
XRF_KEY = '_auth_user_xrf'


class EventConsumer(JsonWebsocketConsumer):
    def connect(self):
        user = self.scope['user']
        if user:
            self.accept()
            self.send_json({"accept": True, "user": user.id})
            # store the valid CSRF token from the cookie so we can compare it later
            # on ws_receive
            cookie_token = self.scope['cookies'].get('csrftoken')
            if cookie_token:
                self.scope['session'][XRF_KEY] = cookie_token
        else:
            logger.error("Request user is not authenticated to use websocket.")
            self.accept()
            self.send({"close": True})
            self.close()

    def disconnect(self, code):
        pass

    def receive_json(self, data):
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
            self.send_json({"error": "access denied to channel"})

        if 'groups' in data:
            groups = data['groups']
            for group_name,v in groups.items():
                if type(v) is list:
                    for oid in v:
                        name = '{}-{}'.format(group_name, oid)
                        '''
                        access_cls = consumer_access(group_name)
                        if access_cls is not None:
                            user_access = access_cls(user)
                            if not user_access.get_queryset().filter(pk=oid).exists():
                                self.send({"text": json.dumps(
                                    {"error": "access denied to channel {0} for resource id {1}".format(group_name, oid)})})
                                continue
                        '''
                        async_to_sync(self.channel_layer.group_add)(
                            name,
                            self.channel_name
                        )
                else:
                    async_to_sync(self.channel_layer.group_add)(
                        group_name,
                        self.channel_name
                    )


    def internal_message(self, event):
        self.send(event['text'])


'''
@channel_session_user
def ws_receive(message):
    from awx.main.access import consumer_access
    user = message.user
    raw_data = message.content['text']
    data = json.loads(raw_data)

    xrftoken = data.get('xrftoken')
    if (
        not xrftoken or
        XRF_KEY not in message.channel_session or
        xrftoken != message.channel_session[XRF_KEY]
    ):
        logger.error(
            "access denied to channel, XRF mismatch for {}".format(user.username)
        )
        message.reply_channel.send({
            "text": json.dumps({"error": "access denied to channel"})
        })
        return

    if 'groups' in data:
        discard_groups(message)
        groups = data['groups']
        for group_name,v in groups.items():
            if type(v) is list:
                for oid in v:
                    name = '{}-{}'.format(group_name, oid)
                    access_cls = consumer_access(group_name)
                    if access_cls is not None:
                        user_access = access_cls(user)
                        if not user_access.get_queryset().filter(pk=oid).exists():
                            message.reply_channel.send({"text": json.dumps(
                                {"error": "access denied to channel {0} for resource id {1}".format(group_name, oid)})})
                            continue
                    async_to_sync(self.channel_layer.group_add)(
                        name,
                        self.channel_name
                    )
            else:
                async_to_sync(self.channel_layer.group_add)(
                    group_name,
                    self.channel_name
                )
'''

def emit_channel_notification(group, payload):
    channel_layer = get_channel_layer()
    try:
        async_to_sync(channel_layer.group_send)(
            group,
            {
                "type": "internal.message",
                "text": json.dumps(payload, cls=DjangoJSONEncoder)
            },
        )
    except ValueError:
        logger.error("Invalid payload emitting channel {} on topic: {}".format(group, payload))
