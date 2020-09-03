# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

import logging
import requests
import json

from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _

from awx.main.notifications.base import AWXBaseEmailBackend
from awx.main.notifications.custom_notification_base import CustomNotificationBase

logger = logging.getLogger('awx.main.notifications.rocketchat_backend')


class RocketChatBackend(AWXBaseEmailBackend, CustomNotificationBase):

    init_parameters = {"rocketchat_url": {"label": "Target URL", "type": "string"},
                       "rocketchat_no_verify_ssl": {"label": "Verify SSL", "type": "bool"}}
    recipient_parameter = "rocketchat_url"
    sender_parameter = None


    def __init__(self, rocketchat_no_verify_ssl=False, rocketchat_username=None, rocketchat_icon_url=None, fail_silently=False, **kwargs):
        super(RocketChatBackend, self).__init__(fail_silently=fail_silently)
        self.rocketchat_no_verify_ssl = rocketchat_no_verify_ssl
        self.rocketchat_username = rocketchat_username
        self.rocketchat_icon_url = rocketchat_icon_url

    def format_body(self, body):
        return body

    def send_messages(self, messages):
        sent_messages = 0
        for m in messages:
            payload = {"text": m.subject}
            for opt, optval in {'rocketchat_icon_url': 'icon_url',
                                'rocketchat_username': 'username'}.items():
                optvalue = getattr(self, opt)
                if optvalue is not None:
                    payload[optval] = optvalue.strip()

            r = requests.post("{}".format(m.recipients()[0]),
                              data=json.dumps(payload), verify=(not self.rocketchat_no_verify_ssl))

            if r.status_code >= 400:
                logger.error(smart_text(
                    _("Error sending notification rocket.chat: {}").format(r.status_code)))
                if not self.fail_silently:
                    raise Exception(smart_text(
                        _("Error sending notification rocket.chat: {}").format(r.status_code)))
            sent_messages += 1
        return sent_messages
