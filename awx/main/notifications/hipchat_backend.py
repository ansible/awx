# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

import logging

import requests

from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _
from awx.main.notifications.base import AWXBaseEmailBackend

logger = logging.getLogger('awx.main.notifications.hipchat_backend')


class HipChatBackend(AWXBaseEmailBackend):

    init_parameters = {"token": {"label": "Token", "type": "password"},
                       "rooms": {"label": "Destination Rooms", "type": "list"},
                       "color": {"label": "Notification Color", "type": "string"},
                       "api_url": {"label": "API Url (e.g: https://mycompany.hipchat.com)", "type": "string"},
                       "notify": {"label": "Notify room", "type": "bool"},
                       "message_from": {"label": "Label to be shown with notification", "type": "string"}}
    recipient_parameter = "rooms"
    sender_parameter = "message_from"

    def __init__(self, token, color, api_url, notify, fail_silently=False, **kwargs):
        super(HipChatBackend, self).__init__(fail_silently=fail_silently)
        self.token = token
        if color is not None:
            self.color = color.lower()
        self.api_url = api_url
        self.notify = notify
        
    def send_messages(self, messages):
        sent_messages = 0

        for m in messages:
            for rcp in m.recipients():
                r = requests.post("{}/v2/room/{}/notification".format(self.api_url, rcp),
                                  params={"auth_token": self.token},
                                  verify=False,
                                  json={"color": self.color,
                                        "message": m.subject,
                                        "notify": self.notify,
                                        "from": m.from_email,
                                        "message_format": "text"})
                if r.status_code != 204:
                    logger.error(smart_text(_("Error sending messages: {}").format(r.text)))
                    if not self.fail_silently:
                        raise Exception(smart_text(_("Error sending message to hipchat: {}").format(r.text)))
                sent_messages += 1
        return sent_messages
