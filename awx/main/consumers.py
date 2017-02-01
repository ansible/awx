import json
import logging

from channels import Group
from channels.sessions import channel_session
from channels.auth import channel_session_user, http_session_user, transfer_user

from django.core.serializers.json import DjangoJSONEncoder


logger = logging.getLogger('awx.main.consumers')


def discard_groups(message):
    if 'groups' in message.channel_session:
        for group in message.channel_session['groups']:
            Group(group).discard(message.reply_channel)


@http_session_user
@channel_session
def ws_connect(message):
    if message.http_session:
        # our backend is not set on the http_session so we need to update the session before
        # calling transfer_user. This is why we are doing this manually instead of using the
        # all-in-one helper decorator.
        message.http_session.update({'_auth_user_backend':'django.contrib.auth.backends.ModelBackend'})
        transfer_user(message.http_session, message.channel_session)
        message.reply_channel.send({"text": json.dumps({"accept": True, "user": message.user.id})})
    else:
        message.reply_channel.send({"text": json.dumps({"accept": False, "user": None})})


@channel_session_user
def ws_disconnect(message):
    discard_groups(message)


@channel_session_user
def ws_receive(message):
    from awx.main.access import consumer_access

    user = message.user
    if user.id is None:
        logger.error("No valid user found for websocket.")
        message.reply_channel.send({"text": json.dumps({"error": "no valid user"})})
        return None

    raw_data = message.content['text']
    data = json.loads(raw_data)

    if 'groups' in data:
        discard_groups(message)
        groups = data['groups']
        current_groups = message.channel_session.pop('groups') if 'groups' in message.channel_session else []
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
                    current_groups.append(name)
                    Group(name).add(message.reply_channel)
            else:
                current_groups.append(group_name)
                Group(group_name).add(message.reply_channel)
        message.channel_session['groups'] = current_groups


def emit_channel_notification(group, payload):
    Group(group).send({"text": json.dumps(payload, cls=DjangoJSONEncoder)})
