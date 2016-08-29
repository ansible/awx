import json

from channels import Group
from channels.sessions import channel_session


def discard_groups(message):
    if 'groups' in message.channel_session:
        for group in message.channel_session['groups']:
            print("removing from group: {}".format(group))
            Group(group).discard(message.reply_channel)

@channel_session
def ws_disconnect(message):
    discard_groups(message)

@channel_session
def ws_receive(message):
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
                    print("listening to group: {}".format(name))
                    current_groups.append(name)
                    Group(name).add(message.reply_channel)
            else:
                print("listening to group: {}".format(group_name))
                current_groups.append(group_name)
                Group(group_name).add(message.reply_channel)
        message.channel_session['groups'] = current_groups


def emit_channel_notification(group, payload):
    print("sending message to group {}".format(group))
    Group(group).send({"text": json.dumps(payload)})
