import json
import logging

from channels import Group
from channels.auth import channel_session_user_from_http, channel_session_user

from django.core.serializers.json import DjangoJSONEncoder


logger = logging.getLogger('awx.main.consumers')


def discard_groups(message):
    if 'groups' in message.channel_session:
        for group in message.channel_session['groups']:
            Group(group).discard(message.reply_channel)


@channel_session_user_from_http
def ws_connect(message):
    message.reply_channel.send({"accept": True})
    message.content['method'] = 'FAKE'
    if message.user.is_authenticated():
        message.reply_channel.send(
            {"text": json.dumps({"accept": True, "user": message.user.id})}
        )
    else:
        logger.error("Request user is not authenticated to use websocket.")
        message.reply_channel.send({"close": True})
    return None


@channel_session_user
def ws_disconnect(message):
    discard_groups(message)


@channel_session_user
def ws_receive(message):
    from awx.main.access import consumer_access
    user = message.user
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
                            message.reply_channel.send({"text": json.dumps(
                                {"error": "access denied to channel {0} for resource id {1}".format(group_name, oid)})})
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
