# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

import logging

import requests

from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger('awx.main.notifications.hipchat_backend')

class HipChatBackend(BaseEmailBackend):

    init_parameters = {"token": {"label": "Token", "type": "password"},
                       "channels": {"label": "Destination Channels", "type": "list"},
                       "color": {"label": "Notification Color", "type": "string"},
                       "api_url": {"label": "API Url (e.g: https://mycompany.hipchat.com)", "type": "string"},
                       "notify": {"label": "Notify channel", "type": "bool"},
                       "message_from": {"label": "Label to be shown with notification", "type": "string"}}
    recipient_parameter = "channels"
    sender_parameter = "message_from"

    def __init__(self, token, color, api_url, notify, fail_silently=False, **kwargs):
        super(HipChatBackend, self).__init__(fail_silently=fail_silently)
        self.token = token
        self.color = color
        self.api_url = api_url
        self.notify = notify
        
    def send_messages(self, messages):
        sent_messages = 0

        for m in messages:
            for rcp in m.recipients():
                r = requests.post("{}/v2/room/{}/notification".format(self.api_url, rcp),
                                  params={"auth_token": self.token},
                                  json={"color": self.color,
                                        "message": m.body,
                                        "notify": self.notify,
                                        "from": m.from_email,
                                        "message_format": "text"})
                if r.status_code != 204:
                    logger.error("Error sending messages: {}".format(r.text))
                    if not self.fail_silently:
                        raise Exception("Error sending message to hipchat: {}".format(r.text))
                sent_messages += 1
        return sent_messages
