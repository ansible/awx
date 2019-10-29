# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

import logging
from slackclient import SlackClient

from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _

from awx.main.notifications.base import AWXBaseEmailBackend
from awx.main.notifications.custom_notification_base import CustomNotificationBase

logger = logging.getLogger('awx.main.notifications.slack_backend')
WEBSOCKET_TIMEOUT = 30


class SlackBackend(AWXBaseEmailBackend, CustomNotificationBase):

    init_parameters = {"token": {"label": "Token", "type": "password"},
                       "channels": {"label": "Destination Channels", "type": "list"}}
    recipient_parameter = "channels"
    sender_parameter = None

    def __init__(self, token, hex_color="", fail_silently=False, **kwargs):
        super(SlackBackend, self).__init__(fail_silently=fail_silently)
        self.token = token
        self.color = None
        if hex_color.startswith("#") and (len(hex_color) == 4 or len(hex_color) == 7):
            self.color = hex_color

    def send_messages(self, messages):
        connection = SlackClient(self.token)
        sent_messages = 0
        for m in messages:
            try:
                for r in m.recipients():
                    if r.startswith('#'):
                        r = r[1:]
                    if self.color:
                        ret = connection.api_call("chat.postMessage",
                                                  channel=r,
                                                  as_user=True,
                                                  attachments=[{
                                                      "color": self.color,
                                                      "text": m.subject
                                                  }])
                    else:
                        ret = connection.api_call("chat.postMessage",
                                                  channel=r,
                                                  as_user=True,
                                                  text=m.subject)
                    logger.debug(ret)
                    if ret['ok']:
                        sent_messages += 1
                    else:
                        raise RuntimeError("Slack Notification unable to send {}: {} ({})".format(r, m.subject, ret['error']))
            except Exception as e:
                logger.error(smart_text(_("Exception sending messages: {}").format(e)))
                if not self.fail_silently:
                    raise
        return sent_messages
