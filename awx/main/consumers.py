import json
import logging
import urllib

from channels import Group, channel_layers
from channels.sessions import channel_session
from channels.handler import AsgiRequest

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder

from django.contrib.auth.models import User
from awx.main.models.organization import AuthToken


logger = logging.getLogger('awx.main.consumers')


def discard_groups(message):
    if 'groups' in message.channel_session:
        for group in message.channel_session['groups']:
            Group(group).discard(message.reply_channel)


@channel_session
def ws_connect(message):
    connect_text = {'accept':False, 'user':None}

    message.content['method'] = 'FAKE'
    request = AsgiRequest(message)
    token = request.COOKIES.get('token', None)
    if token is not None:
        token = urllib.unquote(token).strip('"')
        try:
            auth_token = AuthToken.objects.get(key=token)
            if auth_token.in_valid_tokens:
                message.channel_session['user_id'] = auth_token.user_id
                connect_text['accept'] = True
                connect_text['user'] = auth_token.user_id
        except AuthToken.DoesNotExist:
            logger.error("auth_token provided was invalid.")
    message.reply_channel.send({"text": json.dumps(connect_text)})


@channel_session
def ws_disconnect(message):
    discard_groups(message)


@channel_session
def ws_receive(message):
    from awx.main.access import consumer_access
    channel_layer_settings = channel_layers.configs[message.channel_layer.alias]
    max_retries = channel_layer_settings.get('RECEIVE_MAX_RETRY', settings.CHANNEL_LAYER_RECEIVE_MAX_RETRY)

    user_id = message.channel_session.get('user_id', None)
    if user_id is None:
        retries = message.content.get('connect_retries', 0) + 1
        message.content['connect_retries'] = retries
        message.reply_channel.send({"text": json.dumps({"error": "no valid user"})})
        retries_left = max_retries - retries
        if retries_left > 0:
            message.channel_layer.send(message.channel.name, message.content)
        else:
            logger.error("No valid user found for websocket.")
        return None

    user = User.objects.get(pk=user_id)
    raw_data = message.content['text']
    data = json.loads(raw_data)

    if 'groups' in data:
        discard_groups(message)
        groups = data['groups']
        current_groups = set(message.channel_session.pop('groups') if 'groups' in message.channel_session else [])
        for group_name,v in groups.items():
            if type(v) is list:
                for oid in v:
                    name = '{}-{}'.format(group_name, oid)
                    access_cls = consumer_access(group_name)
                    if access_cls is not None:
                        user_access = access_cls(user)
                        if not user_access.get_queryset().filter(pk=oid).exists():
                            message.reply_channel.send({"text": json.dumps({"error": "access denied to channel {0} for resource id {1}".format(group_name, oid)})})
                            continue
                    current_groups.add(name)
                    Group(name).add(message.reply_channel)
            else:
                current_groups.add(group_name)
                Group(group_name).add(message.reply_channel)
        message.channel_session['groups'] = list(current_groups)


def emit_channel_notification(group, payload):
    try:
        Group(group).send({"text": json.dumps(payload, cls=DjangoJSONEncoder)})
    except ValueError:
        logger.error("Invalid payload emitting channel {} on topic: {}".format(group, payload))
