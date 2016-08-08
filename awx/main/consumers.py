from channels import Group
from channels.sessions import channel_session


@channel_session
def job_event_connect(message):
    job_id = message.content['path'].strip('/')
    message.channel_session['job_id'] = job_id
    Group("job_events-%s" % job_id).add(message.reply_channel)

def emit_channel_notification(event, payload):
    Group(event).send(payload)

