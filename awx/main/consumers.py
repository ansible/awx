import json
import urlparse

from channels import Group
from channels.sessions import channel_session

from django.contrib.auth.models import User
from awx.main.models.organization import AuthToken


def discard_groups(message):
    if 'groups' in message.channel_session:
        for group in message.channel_session['groups']:
            Group(group).discard(message.reply_channel)


def validate_token(token):
    try:
        auth_token = AuthToken.objects.get(key=token)
        if not auth_token.in_valid_tokens:
            return None
    except AuthToken.DoesNotExist:
        return None
    return auth_token


def user_from_token(auth_token):
    try:
        return User.objects.get(pk=auth_token.user_id)
    except User.DoesNotExist:
        return None


@channel_session
def ws_connect(message):
    token = None
    qs = urlparse.parse_qs(message['query_string'])
    if 'token' in qs:
        if len(qs['token']) > 0:
            token = qs['token'].pop()
    message.channel_session['token'] = token


@channel_session
def ws_disconnect(message):
    discard_groups(message)


@channel_session
def ws_receive(message):
    token = message.channel_session.get('token')

    auth_token = validate_token(token)
    if auth_token is None:
        message.reply_channel.send({"text": json.dumps({"error": "invalid auth token"})})
        return None

    user = user_from_token(auth_token)
    if user is None:
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
                    current_groups.append(name)
                    Group(name).add(message.reply_channel)
            else:
                current_groups.append(group_name)
                Group(group_name).add(message.reply_channel)
        message.channel_session['groups'] = current_groups


def emit_channel_notification(group, payload):
    Group(group).send({"text": json.dumps(payload)})
